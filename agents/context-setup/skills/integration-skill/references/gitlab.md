# GitLab

What the GitLab skill must tell agents about this customer's GitLab: which projects matter, which pipelines deploy production, and the labels they use. Agents reach GitLab through the `gitlab_*` tools and `git`; there is no `glab`. Record what is true only here.

## Capture

- **Host and groups:** `gitlab.com` or the self-managed host, and the groups that hold production projects (`acme/platform`), subgroups included.
- **Repositories** (the skill's `## Repositories` section): for each selected project, its full path (`acme/platform/checkout`) and numeric id (`4211`), what it is (a service that runs in production, a library, infrastructure, a shared CI template), its main language, its default branch, and where its deploy or production config lives (`.gitlab-ci.yml` job `deploy-production`, `helm/checkout/values-prod.yaml`).
- **Production deploys:** how to tell a production pipeline: the branch or tag it runs on (`main`, `v*` tags), the stage or job names (`deploy-production`), and the CI `environment:` (`production`).
- **CI layout:** projects whose CI is not `.gitlab-ci.yml` at the root: a custom `ci_config_path`, or an `include:` of a shared template project (`acme/ci-templates`).
- **Labels:** the exact label names for type and severity, scoped labels included (`type::bug`, `severity::1`), and what each means to them.
- **Merge requests:** the target branch that ships to production (`main`, `production`), and the labels or branch names that mark hotfixes and releases.
- **Recurring failures:** pipelines that fail often and why, when the person knows.

## Ask the person

- Which projects run in production, and which can agents ignore?
- Which pipeline, job or environment deploys production for each key service?
- Which labels mark incidents or severity, and which group or project belongs to which team?

## Explore

- `gitlab_test_connection` first: it names the user the token acts as. A group or project access token is a bot user and reaches only its group or project.
- Groups: `gitlab_list_namespaces` with `search`. Projects: `gitlab_list_projects` with `group: "<group path>"`, `include_subgroups: true`, `order_by: "last_activity_at"`, `per_page: 50`.
- One project: `gitlab_get_project` with `id: "<group>/<project>"` gives its numeric id, `default_branch`, `ci_config_path` and `last_activity_at`.
- CI and deploy config: `gitlab_get_file_contents` on `.gitlab-ci.yml` (or the `ci_config_path`). Its jobs' `stage`, `environment:` and `rules` show which job deploys where, and its scripts name the deploy paths (a Helm chart, a Kustomize overlay, a Terraform directory).
- Pipelines: `gitlab_get_pipelines` with `ref: "<default branch>"`, `updated_after` a week ago, `per_page: 20`: how often they run and fail.
- Labels in use: `gitlab_get_issues` and `gitlab_get_merge_requests` with `project_id`, `state: "all"`, `order_by: "updated_at"`, `per_page: 50`; read the `labels` arrays.

## Guardrails

Write the ones agents will hit into the skill.

- Pass `project_id` to `gitlab_get_merge_requests` and `gitlab_get_issues`. Without it GitLab returns only items the token's user created, which for a bot token is nothing.
- `gitlab_list_projects` without `group` lists every project the token can see, on `gitlab.com` all public projects too. Pass `group`, or `membership: true`.
- `project_id` takes the numeric id or the full path (`acme/platform/checkout`); the tool encodes the path. `gitlab_get_project` names the same argument `id`.
- Merge request and issue numbers are IIDs (the `!42` and `#42` in the UI), not global ids. `gitlab_get_merge_request` takes `mr_iid`; `gitlab_get_merge_request_diffs`, `gitlab_list_merge_request_diffs` and `gitlab_mr_discussions` take `merge_request_iid`; `gitlab_get_issue_by_id` takes `issue_iid`.
- Dates: `gitlab_get_pipelines` filters on `updated_after` and `updated_before`, `gitlab_get_commits` on `since` and `until` (ISO 8601). Merge requests and issues have no date filter: sort with `order_by: "updated_at"`, `sort: "desc"` and keep `per_page` small.
- `labels: "bug,production"` matches items that carry all the labels, not any of them.
- `gitlab_get_file_contents` reads one file; a directory path fails.
- No tool lists a pipeline's jobs or reads job logs: agents see a pipeline's status, ref and sha, then read the CI file and the commits.

## Pitfalls

- In `repositories` rows, `name` is the full path with every subgroup (`acme/platform/checkout`), not the project name. `last_activity` comes from `last_activity_at`, as relative time.
- No tool returns a project's languages: take `language` from the CI file's images and build commands, or from a root manifest (`go.mod`, `package.json`, `pyproject.toml`).
- `pipelines_types` and `pipelines_production_deployment` are the person's: propose the production pattern (branch, job, environment) in your reply or in the Pipelines row's `agent_findings`.
- In `issues_type_labels` and `issues_priority_labels`, you add the `label`; the meaning is the person's. Write scoped labels whole (`severity::1`).
- A project that includes a shared template has its deploy jobs in the template project: read that file too before you say where the deploy lives.
- When expected projects are missing, the token may be scoped to one group or project: say so rather than writing them as absent.

## Leave out

GitLab API mechanics, URL encoding, pagination, CI YAML syntax, and live lists of pipelines, merge requests or issues.
