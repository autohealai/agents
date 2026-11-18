# GitHub

What the GitHub skill must tell agents about this customer's organization: which repositories matter, which workflows deploy production, and the labels and teams they use. Agents already know `gh`, `git` and GitHub's search syntax; record what is true only here.

## Capture

- **Host and organizations:** `github.com` or the GitHub Enterprise host, and each organization the connection reaches (`acme`). Every `gh` command names the owner, so state it first.
- **Repositories** (the skill's `## Repositories` section): for each selected repository, its full name (`acme/checkout`), what it is (a service that runs in production, a library, infrastructure, a GitOps repo), its main language, its default branch, and where its deploy or production config lives (`.github/workflows/deploy-prod.yml`, `deploy/helm/checkout/values-prod.yaml`).
- **Production deploys:** which workflow deploys production for each key service, and how to tell its runs from CI: the workflow name (`Deploy production`), the trigger (`push` to `main`, `release`, `workflow_dispatch`) or the GitHub environment (`production`). When another repository or tool deploys (a central `deploy` repo, Argo CD), say which.
- **Environments:** the GitHub environment names that mean production and staging, when the repositories use them.
- **Issue labels:** the exact label names for bugs, incidents and severity (`type: bug`, `sev1`), and what each means to them.
- **Teams and ownership:** the team slugs that own key services (`acme/payments`), and whether `CODEOWNERS` maps paths to teams.
- **Recurring failures:** workflows that fail often and why (a flaky test job, a noisy scan), when the person knows.

## Ask the person

- Which repositories run in production, and which can agents ignore?
- Which workflow deploys production for each key service, and how do you tell a production run from CI?
- Which labels mark incidents or severity, and which team owns which service?

## Explore

Name the owner on every command (the organization the first `bash` result names) and the repository with `-R <org>/<repo>` or `/repos/<org>/<repo>/...`.

- `github_test_connection` first: it says whether the GitHub App or token works and, for an App, which account it is installed on and how many repositories it reaches.
- Repositories: `gh repo list <org> --no-archived --limit 200 --json nameWithOwner,description,primaryLanguage,defaultBranchRef,pushedAt`. `github_list_repositories` returns the same set as full objects, one page at a time.
- Deploy config: list the tree once with `gh api '/repos/<org>/<repo>/git/trees/<branch>?recursive=1' --jq '.tree[].path' | grep -E '\.github/workflows/|helm|deploy|k8s|kustomize|terraform|Dockerfile' | head -50`, then read a file with `gh api -H 'Accept: application/vnd.github.raw' /repos/<org>/<repo>/contents/<path>`.
- Workflows and runs: `gh workflow list -R <org>/<repo>`, then `gh run list -R <org>/<repo> --branch <default> --limit 20 --json workflowName,event,conclusion,createdAt` to see which run on the default branch and how often they fail.
- Environments and deployments: `gh api /repos/<org>/<repo>/environments --jq '.environments[].name'` and `gh api '/repos/<org>/<repo>/deployments?per_page=10' --jq '.[] | {environment, ref, created_at}'`.
- Labels: `gh label list -R <org>/<repo> --limit 100 --json name,description`.
- Teams: `gh api '/orgs/<org>/teams?per_page=100' --jq '.[] | {slug, name, description}'`, and the `CODEOWNERS` file (`.github/CODEOWNERS` or the root) for which team owns which path.

## Guardrails

Write the ones agents will hit into the skill.

- With a GitHub App, `/user`, `/user/orgs` and `gh repo list` without an owner fail with "Resource not accessible by integration". Name the organization; `gh api /installation/repositories` lists what the App reaches.
- Repo commands need the repository: `-R <org>/<repo>` or a `/repos/<org>/<repo>/...` path. The machine has no checked-out repository to infer it from.
- Search (`gh search`, `/search/*`) allows 30 requests a minute. Scope each search with `repo:<org>/<repo>` or `org:<org>` and a date (`created:>2026-11-01`).
- Failed job output: `gh run view <run-id> -R <org>/<repo> --log-failed`. Full logs of many runs use up the rate limit.
- Write label names exactly as the repository spells them, quoted when they hold spaces or colons (`label:"type: bug"`).

## Pitfalls

- Teams need the App's organization Members permission: a 403 on `/orgs/<org>/teams` means it is not granted. Say so in the Teams row's `agent_findings` instead of writing "no teams".
- In `repositories` rows, `name` is `org/repo`. Take `description` from GitHub's repository description, `language` from `primaryLanguage`, and `last_activity` from `pushedAt` as relative time ("3 days ago").
- `actions_workflow_types` and `actions_production_deployment` are the person's: propose the production pattern (workflow, branch, environment) in your reply or in the Actions row's `agent_findings`.
- In `issues_type_labels`, `issues_priority_labels` and `teams`, you add the `label` or `name`; the meaning column is the person's.
- Archived repositories and forks crowd the table: leave them out unless the person names one.
- A repository with no deploy workflow can still deploy from elsewhere (a GitOps repo, Argo CD): ask before you write that it does not deploy.

## Leave out

`gh` and `git` usage, search qualifier syntax, REST and GraphQL mechanics, sign-in and token handling, and live lists of runs, pull requests or issues.
