---
name: Upgrading every repository off an end-of-life version
description: >-
  Move every repository off an end-of-life runtime, toolchain or base image
  without handing owners red pull requests. Prove the playbook on one pilot
  per language family, record each fix as a step, roll out by tier with
  approval, and count a repository done only when production runs it.
---

# Upgrading every repository off an end-of-life version

> Written after the first Debian 12 attempt opened twelve pull requests at
> once and four failed CI: currency on libssl1.1, shipping on glibc,
> load-generator on pip, and email on a package that depends on libssl1.1.
> The tier-1 owners held their green pull requests while the red ones were
> open, and the attempt was withdrawn.

A migration applies one playbook to many repositories. A playbook that has
not been run against our own Dockerfiles is untested. Applied to twelve
repositories at once, an untested playbook costs twelve reviews and four
debugging sessions in four different teams.

## 1. Count what production runs

Start from the running images, not from GitHub. For each repository in scope,
read the image running in `<prod-namespace>` (kubectl) and the base it was built from
(ECR). A merged pull request is not done until its image is the one running.
Some deploys pin a digest in platform-helm, and a merge does not move them.

## 2. One pilot per language family

Group the repositories by how their image is built:

| Family | Here | What breaks first |
|---|---|---|
| Native, links system libraries | currency (C++) | a shared library renamed between releases |
| Compiled, multi-stage | shipping (Rust), checkout (Go) | a builder newer than its runtime stage |
| Interpreted, installs packages | load-generator (Python), frontend (Node) | package manager policy, removed syntax |

Pick one pilot for each family the migration touches. Never a tier-1 service.
Prefer the repository with the most native dependencies. A migration with one
repository left makes that repository its own pilot.

## 3. Make the pilots green, and write each fix down

Open the pilots as draft pull requests with the playbook as written. When CI
is red, fix it on the branch and add a numbered step to
`playbooks/<migration>.md` in <org>/platform-migrations: what failed, the
change, and which other repositories it applies to.

A pilot is green when its image builds, starts, and passes the smoke test.
"It builds" is not green.

## 4. Roll out by tier, with approval

Rolling past the pilots needs the platform lead's approval. Ask with the
pilots green, the steps recorded, and the order stated. Then:

- **Tier-1 first.** These are the services customers reach, so an end-of-life
  image there is the largest exposure. The pilots carried the playbook's risk.
- **Tier-2** once tier-1 has merged.
- **Internal repositories** last.

One wave at a time. A step that breaks in a wave is fixed and recorded before
the next wave opens. Every pull request links the pilot results.

## 5. Blocked is not red

A repository that cannot move because of something it depends on is blocked.
Name the dependency, its owner and what they need to ship, and open a ticket
on their board. Do not open a pull request that cannot go green.

## Reporting status

Every repository in scope is in exactly one state:

| State | Meaning |
|---|---|
| Running | production runs an image on the new version |
| Merged, not running | merged, but the running digest is still the old one |
| In review | pull request open and green; the owner merges |
| Queued | waits for an earlier wave |
| Blocked | waits on a named dependency and its owner |

Give the tier, owner, pull request and CI for each.
