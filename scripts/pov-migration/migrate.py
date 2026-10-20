"""Move a customer's data from their POV install to a new install. See README.md for the run order.

The whole migration, as one command (run it twice: it pauses once for the memory review):
  migrate-all             exports, converts, then after --reviewed imports, labels and verifies everything

Or step by step:

Skills (laptop, through the app's API):
  probe                   what the token can reach on the target
  export-skills           old agents DB -> SKILL.md files
  push-skills             commit them to a project's Git repository

Memories (convert anywhere agents-py is importable; database steps in a pod):
  export-memories         memories + their hypothesis + the old agents.md -> bundle
  convert-memories        LLM rewrites each one as Use when / What to do / Avoid when (no database writes)
  review-memories         HTML page to read every converted memory next to its old lesson
  accept-memories         keep a draft that was held for adding details, after reading it
  import-memories / verify-memories / undo-memories

Memory labels (laptop, through the app's API):
  label-memories / verify-labels / unlabel-memories   (unlabel BEFORE undo-memories)

Investigations (in a pod; hidden cold storage):
  export-investigations / import-investigations / verify-investigations / undo-investigations

Exit codes: 0 done; 1 some items failed (the rest went in), memories still need review, or a crash;
2 stopped before writing anything; 3 stopped on an outside problem (rerun the same command to continue).
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
import review  # noqa: E402
import skills  # noqa: E402


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    pipeline.add_commands(sub)
    skills.add_commands(sub)
    memories.add_commands(sub)
    review.add_commands(sub)
    labels.add_commands(sub)
    investigations.add_commands(sub)
    commands = {
        **pipeline.COMMANDS,
        **skills.COMMANDS,
        **memories.COMMANDS,
        **review.COMMANDS,
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
