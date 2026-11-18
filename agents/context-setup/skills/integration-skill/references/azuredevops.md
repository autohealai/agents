# Azure DevOps

What the Azure DevOps skill must tell agents about this customer's organizations: which repositories matter, which pipelines deploy production, and where the operational wiki pages live. Agents already know `az repos`, `az pipelines` and `git`; record what is true only here.

## Capture

- **Organizations and projects:** each connected organization (the `dev.azure.com/<org>` segment) and the projects that own production services.
- **Repositories** (the skill's `## Repositories` section): for each selected repository, its organization, project and name, what it is (the active service, a library, an infrastructure repo, empty or deprecated), its main language, and where its deploy or production config lives (`deploy/`, `helm/`, `azure-pipelines.yml`).
- **Production deploys:** which pipelines deploy production, how to tell them from CI and pull-request builds (name pattern, branch, stage or environment name), and which repository and branch each one builds.
- **Environments:** the pipeline environments or stages that mean production and staging, and any approval gate on them.
- **Wiki:** the wiki and the paths of the runbook and incident pages (`Ops/Runbooks/Payments`), so agents read the right page instead of crawling the tree.
- **Recurring issues:** pipelines that fail often and why, when the person knows.

## Ask the person

- Which repositories are the services that run in production, and which can agents ignore?
- Which pipeline deploys production for each key service, and which stage or environment is production?
- Where do the runbooks and incident write-ups live in the wiki?
- Which organization or project belongs to which team?

## Explore

Run every command with the connection's config dir prefix that the `bash` result names (`AZURE_CONFIG_DIR=<dir> az ...`). The connection's default organization applies; for another organization pass `--org https://dev.azure.com/<org>` and `--project <project>`.

- Projects: `az devops project list --query "value[].name" -o tsv`.
- Repositories: `az repos list --project <project> --query "[].{name:name,size:size,branch:defaultBranch}" -o table`. Size 0 means an empty repository.
- Pipelines: `az pipelines list --project <project> --query "[].{id:id,name:name,path:path}" -o table`, then `az pipelines runs list --project <project> --top 20 --query "[].{pipeline:definition.name,branch:sourceBranch,result:result,finished:finishTime}" -o table` to see which run on the main branch and how often they fail.
- A pipeline's stages: read its YAML from the repository (`az repos show`, then `git` clone and read `azure-pipelines.yml`), or `az pipelines show --id <id>`.
- Wiki: `az devops wiki list --project <project>`, then `az devops wiki page show --project <project> --wiki <wiki> --path / --recursion-level full`.

## Guardrails

Write the ones agents will hit into the skill.

- For anything without a subcommand use `az devops invoke` (GET only), never `az rest`: with a personal access token connection, `az rest` is unauthenticated.
- `az devops wiki page show` needs `--project`, and the flag is `--recursion-level` (`none`, `oneLevel`, `full`), not `--recursion`.
- A bare `curl` gets no credentials. On Azure DevOps Server (on-premises, not `dev.azure.com` or `*.visualstudio.com`) `az` does not work: use `git` only.
- Shape output with `--query` (JMESPath). If you pipe to `jq`, do not merge stderr (`2>&1`): a warning breaks the JSON.
- Throttling is per organization: on HTTP 429 honour `Retry-After`, and keep `--top` small.

## Pitfalls

- Several organizations can be connected. Each repository row carries its own `organization` and `project`; never put them into `name`.
- The form's `pipelines_production_identification` and the `description` columns of `key_pipelines` and `wiki_runbook_locations` are the person's: propose the production pattern in your reply or in the Pipelines feature's `agent_findings`.
- Many projects: look first at the ones that own production services, not every project.

## Leave out

`az` and `git` mechanics, sign-in, REST api-versions, CLI versus REST enum casing, and live lists of runs or pull requests.
