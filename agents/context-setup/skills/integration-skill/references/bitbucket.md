# Bitbucket

What the Bitbucket skill must tell agents about this customer's Bitbucket Cloud workspace: which repositories matter, which pipelines deploy production, and how pull requests reach production. Agents reach Bitbucket through the `bitbucket_*` tools and `git`; record what is true only here.

## Capture

- **Workspace:** the workspace slug the connection is bound to (`acme`). Every tool works inside it, so state it first.
- **Repositories** (the skill's `## Repositories` section): for each selected repository, its slug (`checkout-api`), what it is (a service that runs in production, a library, infrastructure), its main language, its default branch, and where its deploy or production config lives (`bitbucket-pipelines.yml` step `Deploy to production`, `deploy/helm/values-prod.yaml`).
- **Production deploys:** how to tell a production pipeline run: the branch it targets (`main`, `release/*`), the trigger (`push`, `manual`), the custom pipeline or step name, and the step's `deployment:` environment (`production`).
- **Pull requests:** the destination branch that ships to production, the merge strategy (squash, merge commit), and branch names that mark hotfixes (`hotfix/*`).
- **Projects:** the Bitbucket project keys that group a team's repositories (`PAY`), when the person uses them that way.
- **Recurring failures:** pipeline steps that fail often and why, when the person knows.

## Ask the person

- Which repositories run in production, and which can agents ignore?
- Which pipeline or step deploys production for each key service?
- Which branch do pull requests merge into to ship, and how are they merged?

## Explore

- `bitbucket_test_connection` first, then `bitbucket_list_repositories` with `sort: "-updated_on"`, `pagelen: 50`. Narrow with `query` (`project.key = "PAY"`, `name ~ "checkout"`).
- One repository: `bitbucket_get_repository` gives its `default_branch`, `language` and `description`.
- Deploy config: `bitbucket_get_file_contents` on `bitbucket-pipelines.yml` with `commit` set to the default branch. Its `branches`, `custom` pipelines and `deployment:` keys show which step deploys where. A directory path with a trailing slash (`deploy/`) returns the directory's entries.
- Pipeline runs: `bitbucket_list_pipelines` with `sort: "-created_on"`, `pagelen: 20`: each run's `target_branch`, `trigger_name` and `result`. For a failed run, `bitbucket_list_pipeline_steps`, then `bitbucket_get_pipeline_step_log` on the failed step.
- Pull requests: `bitbucket_list_pull_requests` with `state: "MERGED"`, `pagelen: 20`: destination branches and branch naming.

## Guardrails

Write the ones agents will hit into the skill.

- Bitbucket Cloud only: the tools call `api.bitbucket.org`, so Bitbucket Server and Data Center do not work.
- Tools take the repository slug (`checkout-api`), never `workspace/repo`: the workspace comes from the connection.
- Pipeline and step UUIDs keep their curly braces: `pipeline_uuid: "{4f9c2e1a-...}"`.
- `bitbucket_list_pipelines` filters nothing: sort by `-created_on`, keep `pagelen` small, and pick runs by `target_branch` and `result` in the output.
- `bitbucket_list_commits` filters by `branch` and `path` only; there is no date filter.
- `bitbucket_list_pull_requests` returns only `OPEN` pull requests unless you pass `state`, and `pagelen` is at most 50.
- Pass `commit` (a branch, tag or hash) to `bitbucket_get_file_contents` rather than relying on its default.
- Bitbucket Cloud allows about 1,000 API requests an hour: read the failed step's log, not every step's.

## Pitfalls

- In `repositories` rows, `name` is `workspace/repo` (`acme/checkout-api`), but the tools take the slug alone.
- Bitbucket's `language` is set by hand and is often empty: take it from the pipeline file's image or a root manifest (`go.mod`, `package.json`).
- `pull_requests_review_labels`: the tools return no labels on pull requests. Fill it only from what the person tells you; do not turn title prefixes into labels.
- `pipelines_types`, `pipelines_production_deployment` and `pull_requests_merge_strategy` are the person's: propose what you found in your reply or in the feature row's `agent_findings`.
- A repository access token reaches one repository: when `bitbucket_list_repositories` returns only one, say so rather than writing the workspace as small.

## Leave out

Bitbucket API mechanics, the query language's syntax, pagination, pipeline YAML syntax, and live lists of pipeline runs, commits or pull requests.
