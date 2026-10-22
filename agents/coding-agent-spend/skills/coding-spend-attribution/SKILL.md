---
name: Attributing coding-agent spend
description: >-
  Price coding-agent usage by token type, compare repositories on cost per
  merged PR, find where each repository's tokens go, and benchmark any model,
  effort or settings change on the team's own tasks before proposing it. Use on
  every nightly spend review.
---

# Attributing coding-agent spend

> Written after the Sep 17 report recommended moving checkout to a cheaper
> model because it had the largest bill. checkout had merged 58 PRs that week,
> more than any other repository, and its cost per merged PR was the lowest of
> the seven. The bill itself was 3.6 times too high, because cache reads had
> been priced as fresh input.

A total answers "who spent the most?". It does not answer "who is wasting
tokens?", and it always points at the team that ships the most. Four steps do.

## 1. Price each token type at its own rate

| Token type | Rate |
|---|---|
| `input` | the model's input rate |
| `cacheCreation` | 1.25 times the input rate |
| `cacheRead` | a tenth of the input rate |
| `output` | the model's output rate |

Cache reads are about 90% of the input-side tokens in our coding sessions,
because every turn re-sends the context. Priced as fresh input, they inflate a
repository's bill three to four times, and inflate the repositories with the
longest sessions most.

Check the total against the harness's own figure: `claude_code.cost.usage`
plus Cursor's reported cost. Within 3% is fine. Outside it, say so and stop.
A ranking built on a wrong total is worse than no ranking.

## 2. Divide by what shipped

Cost per merged PR, per repository, over the same seven days. A repository
with fewer than eight merged PRs in the window is reported but not ranked.

A migration or a large refactor merges at the end. When a repository's cost
per PR is high, read what merged before calling it waste.

## 3. Find where the tokens went

Split each repository's input-side tokens by tool and by path, from the
`PostToolUse` hook events platform-config ships to Datadog. A file read early
in a session is carried in context on every later turn, so attribute what it
costs across the session, not only at the read.

Name the largest sink in each repository. Anything above 15% of a
repository's input-side tokens is worth a change.

## 4. Fix the sink, not the model

| Where the tokens go | The fix | Who decides |
|---|---|---|
| Generated or vendored code | ignore rule, plus a CLAUDE.md pointer to the source | the owning team reviews a PR |
| Long tool output (test logs, builds) | a quieter command in CLAUDE.md or a skill | the owning team reviews a PR |
| Reasoning on routine tasks | an effort or model default for that kind of task | platform engineering approves |

A cheaper model is the last lever, not the first. If the model mix is the same
across repositories, the model is not what sets one apart.

## Benchmark before proposing

Every model, effort or settings change is benchmarked before it is proposed.

1. Take 30 to 50 tasks of the affected kind from the last 30 days of the
   team's own sessions, spread across the repositories in proportion to
   their share.
2. Replay each from its starting commit with its original prompt, once per
   setup. Today's setup is always one of them.
3. Define a pass before you run. For test-writing, the tests compile, pass on
   the merged change, and fail with the change reverted.
4. Propose a setup only if it passes within one task of today's setup and
   costs at least 15% less. Report pass rate, cost per task and median time
   for every setup, including the ones you reject.

## What to do

- **A sink in a team's repository:** open a pull request against it for the
  team to review. The merge is theirs.
- **A benchmarked settings change:** open it against
  `<org>/platform-config`. It waits for platform engineering's approval.
- **A re-run of a closed week:** correct the figures, withdraw anything the
  old report proposed that these steps do not support, and propose nothing.
