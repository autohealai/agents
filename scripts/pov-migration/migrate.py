"""Move a customer's data from their POV install to a new install. See README.md.

The whole migration, in one run:
  migrate-all             exports, rewrites the memories, then imports, labels and verifies everything

Or step by step:

Skills (through the app's API):
  probe                   what the token can reach on the target
  export-skills           old agents DB -> SKILL.md files
  push-skills             commit them to a project's Git repository

Memories (convert where agents-py is importable, e.g. an agents-py pod):
  export-memories         memories + their hypothesis + the old agents.md -> bundle
  convert-memories        LLM rewrites each one as Use when / What to do / Avoid when (no database writes)
  import-memories / verify-memories / undo-memories

Memory labels (through the app's API):
  label-memories / verify-labels / unlabel-memories   (unlabel BEFORE undo-memories)

Investigations (hidden history):
  export-investigations / import-investigations / verify-investigations / undo-investigations

Exit codes: 0 done; 1 some items failed (the rest went in) or a crash; 2 stopped before writing
anything; 3 stopped on an outside problem (rerun the same command to continue).
"""

import sys

if sys.version_info < (3, 11):  # noqa: UP036 - a laptop's system Python may be older
    sys.exit(f"needs Python 3.11 or newer; this is {sys.version.split()[0]}")

import argparse  # noqa: E402
import asyncio  # noqa: E402
import inspect  # noqa: E402

import db  # noqa: E402
import investigations  # noqa: E402
import labels  # noqa: E402
import memories  # noqa: E402
import pipeline  # noqa: E402
import skills  # noqa: E402


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    pipeline.add_commands(sub)
    skills.add_commands(sub)
    memories.add_commands(sub)
    labels.add_commands(sub)
    investigations.add_commands(sub)
    commands = {
        **pipeline.COMMANDS,
        **skills.COMMANDS,
        **memories.COMMANDS,
        **labels.COMMANDS,
        **investigations.COMMANDS,
    }

    args = p.parse_args()
    fn = commands[args.cmd]
    try:
        if inspect.iscoroutinefunction(fn):
            asyncio.run(fn(args))
        else:
            fn(args)
    except Exception as e:  # e.g. the database is down when the command starts
        if not db.outside_problem(e):
            raise
        print(
            f"STOPPED: {type(e).__name__}: {e}. Every finished item is saved; rerun the same command to continue."
        )
        sys.exit(3)


if __name__ == "__main__":
    main()
