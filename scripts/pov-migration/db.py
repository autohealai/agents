"""Database plumbing shared by the investigation and memory steps.

asyncpg is imported lazily, so the skills and label commands run on a laptop without it.
"""

import asyncio
import errno
import json
import os
import socket
import sys
from pathlib import Path

# A held lock fails fast instead of hanging the run; the name shows in pg_stat_activity.
SESSION_SETTINGS = {
    "lock_timeout": "10s",
    "statement_timeout": "5min",
    "application_name": "pov-migration",
}
ITEM_TRIES = 3  # per investigation or memory, for dropped connections and lock waits
NETWORK_ERRNOS = {
    errno.ECONNREFUSED,
    errno.ECONNRESET,
    errno.EHOSTUNREACH,
    errno.ENETUNREACH,
    errno.ETIMEDOUT,
    errno.EPIPE,
}


class RunStopped(Exception):
    """An outside problem stopped the run partway; rerunning the same command continues it."""


async def connect(db_url: str | None):
    import asyncpg

    if db_url:
        return await asyncpg.connect(db_url, server_settings=SESSION_SETTINGS, timeout=30)
    env = os.environ
    needed = [f"POSTGRES_CONFIG__{k}" for k in ("HOST", "USER", "PASSWORD", "DATABASE")]
    if missing := [k for k in needed if k not in env]:
        sys.exit(f"no --db, and the environment lacks {', '.join(missing)}")
    return await asyncpg.connect(
        host=env["POSTGRES_CONFIG__HOST"],
        port=int(env.get("POSTGRES_CONFIG__PORT") or 5432),
        user=env["POSTGRES_CONFIG__USER"],
        password=env["POSTGRES_CONFIG__PASSWORD"],
        database=env["POSTGRES_CONFIG__DATABASE"],
        ssl=env.get("POSTGRES_CONFIG__SSLMODE") or None,
        server_settings=SESSION_SETTINGS,
        timeout=30,
    )


def lost_connection(e: BaseException) -> bool:
    """The database went away, as opposed to rejecting the data. A missing file is not a lost connection."""
    try:
        import asyncpg
    except ImportError:
        return False
    if isinstance(
        e, asyncpg.InterfaceError
    ):  # also raised for client misuse; only this one means "gone"
        return "connection is closed" in str(e)
    if isinstance(
        e, (asyncpg.PostgresConnectionError, ConnectionError, TimeoutError, socket.gaierror)
    ):
        return True
    return type(e) is OSError and e.errno in NETWORK_ERRNOS


def lock_timeout(e: BaseException) -> bool:
    import asyncpg

    return isinstance(e, asyncpg.LockNotAvailableError)


def outside_problem(e: BaseException) -> bool:
    """Not the data's fault: the run stopped, the database went away, or a lock or statement timed out.

    Inside write_item a statement timeout fails only that item; anywhere else it stops the run.
    """
    if isinstance(e, RunStopped) or lost_connection(e):
        return True
    try:
        import asyncpg
    except ImportError:
        return False
    return isinstance(e, (asyncpg.LockNotAvailableError, asyncpg.QueryCanceledError))


class Session:
    """One connection that comes back after a drop, holding the run's claim.

    The claim is a session advisory lock: a second import or undo of the same kind
    against the same database refuses to start (exit 2) instead of racing the first.
    """

    def __init__(self, db_url: str | None, claim: str):
        self.db_url, self.claim, self.conn = db_url, claim, None

    async def _claim(self) -> bool:
        self.conn = await connect(self.db_url)
        if await self.conn.fetchval("select pg_try_advisory_lock(hashtext($1))", self.claim):
            return True
        await self.conn.close()
        return False

    async def _holder(self) -> str:
        conn = await connect(self.db_url)
        try:
            row = await conn.fetchrow(
                """select a.pid, a.application_name, a.client_addr::text as addr, a.backend_start, a.state
                   from pg_locks l join pg_stat_activity a on a.pid = l.pid
                   where l.locktype = 'advisory' and l.granted
                     and l.objid = (hashtext($1)::bigint & 4294967295)::oid limit 1""",
                self.claim,
            )
        finally:
            await conn.close()
        if not row:
            return ""
        return (
            f"  held by pid {row['pid']} ({row['application_name']}, {row['addr']}, since {row['backend_start']:%H:%M}, "
            f"{row['state']}). If that run is dead, end it with: select pg_terminate_backend({row['pid']});"
        )

    async def open(self):
        if not await self._claim():
            print(
                f"STOPPED: another '{self.claim}' run is already going against this database; wait for it"
            )
            print(await self._holder())
            sys.exit(2)
        return self.conn

    async def reopen(self, attempts: int = 6) -> bool:
        """Reconnect and take the claim back. A dropped connection's server side may hold it for a while."""
        for n in range(1, attempts + 1):
            wait = min(60, 2**n)
            print(f"  lost the database connection; reconnecting in {wait}s ({n}/{attempts})")
            await asyncio.sleep(wait)
            try:
                if self.conn and not self.conn.is_closed():
                    await self.conn.close()
            except Exception:
                pass
            try:
                if await self._claim():
                    print("  reconnected")
                    return True
                print("  reconnected, but the old connection still holds the run's claim; waiting")
            except Exception as e:
                if not lost_connection(e):
                    raise
        return False

    async def write_item(self, label: str, write, exists=None) -> str | None:
        """Run one item's all-or-nothing write(conn). Returns None when written, else why it failed.

        exists(conn) tells, after a dropped connection, whether the last try's commit landed anyway.
        Raises RunStopped when the database stays unreachable.
        """
        why, dropped = "", False
        for attempt in range(1, ITEM_TRIES + 1):
            try:
                if dropped and exists and await exists(self.conn):
                    return None
                await write(self.conn)
                return None
            except Exception as e:
                dropped = lost_connection(e)
                if dropped:
                    if not await self.reopen():
                        raise RunStopped("the database stayed unreachable") from e
                    why = "the connection dropped on every try"
                elif lock_timeout(e):
                    print(f"  {label}: waited 10s for a lock ({attempt}/{ITEM_TRIES})")
                    await asyncio.sleep(5)
                    why = "another session kept holding a lock"
                else:
                    return f"{type(e).__name__}: {e}"[:500]  # bad data: this item only
        return f"gave up after {ITEM_TRIES} tries: {why}"

    async def close(self):
        if self.conn and not self.conn.is_closed():
            await self.conn.close()


async def revision(conn) -> str:
    return await conn.fetchval("select version_num from alembic_version limit 1")


async def columns_of(conn, table: str) -> set[str]:
    sql = "select column_name from information_schema.columns where table_schema = 'public' and table_name = $1"
    return {r["column_name"] for r in await conn.fetch(sql, table)}


async def require_columns(conn, needs: dict[str, list[str]], which: str = "source"):
    """Stop with exit 2 when a database lacks a column this tool reads or writes."""
    missing = []
    for table, cols in needs.items():
        have = await columns_of(conn, table)
        missing += [
            f"{table}.{c}" if have else f"{table} (whole table)" for c in cols if c not in have
        ]
    if missing:
        print(f"STOPPED: the {which} database lacks what this step needs:")
        for m in dict.fromkeys(missing):
            print(f"  - {m}")
        print(
            f"  its revision: {await revision(conn)}. Upgrade that install first, or extend the tool."
        )
        sys.exit(2)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
