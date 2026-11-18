# Code exploration

The goal is a map from each component to its code: where it is, how it starts, how it logs, how it is configured and deployed, and how to find the change that shipped before an incident. Read the code yourself; ask the person only to choose and to confirm.

All commands run with `bash` in the project's machine, with the project's `project_id`. The machine is signed in to the project's CLIs (`gh`, `glab`, `az`, `git`). Never ask for a token, and never print one: do not run `env`, `gh auth token`, or `git config --list` with credentials in it. Only `/tmp` is kept between messages, so clone into `/tmp/onboarding/`.

## 1. List the candidates

Collect repositories from two places:

- The code host, with its integration tools or CLI, bounded:
  - GitHub: `gh repo list <org> --limit 200 --json name,pushedAt,description,primaryLanguage`
  - GitLab: `glab repo list --group <group> --per-page 100` or `glab api "groups/<group>/projects?per_page=100&order_by=last_activity_at&include_subgroups=true"`
  - Azure DevOps: `az repos list --project <project> --query "[].{name:name,url:remoteUrl,size:size}" -o table`
  The first `bash` result shows each CLI's settings, such as the GitHub organization. When it does not, ask.
- The Context Graph: `context_graph_list_entities` with `blueprint: repository`, and the repositories that already have a `team: <domain>` label.

Rank them, and keep the top five to eight:

1. Name or description matches a component or the domain (from Step 3).
2. Pushed to recently (the last 90 days).
3. Named in recent incidents: a link to a commit, pull request or repository in a ticket's resolution notes.

When the code host is not connected, or its connection fails, ask the person for the repository URLs. A public repository clones with plain `git clone`, with no connection.

When an organization has many repositories, search instead of listing: `gh search repos --owner <org> <component> --limit 20`, or the code host's code search for a component's name.

## 2. Ask which to read

One `ask_user_input`: offer the top candidates as options, each with one line of why ("matches component pricer; pushed 3 days ago"). The person can add others in their answer. Read at most four in one pass; offer the rest after.

For a large monorepo, ask first which paths belong to the domain, and read only those.

## 3. Clone shallowly

```bash
mkdir -p /tmp/onboarding && cd /tmp/onboarding
gh repo clone <org>/<repo> <repo> -- --depth 100 --filter=blob:limit=1m --single-branch
# GitLab:       glab repo clone <group>/<repo> <repo> -- --depth 100
# Azure Repos:  git clone --depth 100 <remoteUrl from az repos list> <repo>
```

When you have a `git_clone` tool, clone with it instead of `bash`, and update with `git_pull`.

When the directory exists from an earlier message, update it with `git -C <repo> pull --depth 100` instead of cloning again. If a clone asks for credentials or fails, do not retry with a token: read the files through the integration's own file tools instead, and say what you could not clone.

## 4. Read with bounded commands

Every command limits its output (`head`, `-maxdepth`, `--max-count`). Read in this order, and stop once you can fill the codebase skill:

- **Purpose and docs**: `head -150 README*`; `ls docs/ 2>/dev/null | head -50`
- **Layout**: `find . -maxdepth 3 -type d -not -path '*/.git*' -not -path '*/node_modules*' | head -150`
- **Languages and dependencies**: `ls`, then the manifests: `go.mod`, `package.json`, `pom.xml`, `build.gradle`, `*.csproj`, `requirements*.txt`, `pyproject.toml` (`head -80` each)
- **Entry points**: `rg -l --max-count 1 -g '!**/test*/**' 'func main\(|static void Main|@SpringBootApplication|if __name__ == .__main__.|createServer\(|app.listen\(' | head -20`
- **Routes, consumers and jobs**: `rg -n --max-count 5 '@(Get|Post|Put)Mapping|router\.(get|post)|HandleFunc|@app\.(get|post)|Consumer|Subscribe|@Scheduled|cron' | head -60`
- **Configuration and flags**: `find . -maxdepth 4 \( -name 'appsettings*.json' -o -name 'application*.y*ml' -o -name '*.env.example' -o -name 'config*.y*ml' \) -not -path '*/node_modules/*' | head -30`; `rg -n --max-count 5 -i 'feature.?flag|launchdarkly|unleash|flagd' | head -20`
- **Logging**: the library: `rg -l --max-count 1 'zap\.|logrus|slog|log4j|logback|Serilog|ILogger|winston|pino|logging\.getLogger' | head`; the messages: `rg -n --max-count 3 '\.(Error|Warn|error|warn|LogError|LogWarning)\(' -g '!**/test*/**' | head -60`
- **Data stores**: `rg -n --max-count 3 -i 'connectionstring|jdbc:|sqlserver|postgres|mongodb|redis|DATABASE_URL' -g '!**/test*/**' | head -30` (do not print secret values)
- **Deploys**: `find . -maxdepth 3 \( -name 'Dockerfile*' -o -name 'Chart.yaml' -o -name '*.tf' -o -name 'kustomization.yaml' -o -name 'azure-pipelines*.yml' -o -name '.gitlab-ci.yml' \) | head -30`; `ls .github/workflows 2>/dev/null`
- **Recent change**: `git log --since='60 days ago' --format='%h %ad %an %s' --date=short | head -40`; `git tag --sort=-creatordate | head -10`

From the logging lines, write down the message formats that a log search can match, such as `"payment status changed from {old} to {new} for {paymentId}"`, and the file that writes each one. Check them against the log integration from Step 3 when you can: one query for a message string over the last day.

## 5. Explore in parallel when you can

When you have `invoke_explore`, start one child for each chosen repository, at most four at once, each with the repository's `project_id` and a prompt that names:

- the repository, its clone path under `/tmp/onboarding/`, and the domain's component names;
- the table above as the reading list, with its output limits;
- what to return: the components the repository holds and their paths; language and framework; entry points; configuration and flags; the logging library and three to five message formats with their files; data stores; deploy manifests and pipelines; how a release maps to a commit; and open questions.

Each child returns `findings`, `queries_that_ran` and `open_questions`. Merge them yourself. Without `invoke_explore`, read the repositories one after another.

## 6. Confirm before you write

Show the person a short summary for each repository: the components and paths, the entry points, the log formats, and how it deploys. Ask what is wrong or missing with `ask_user_input` (options: "Looks right", "Some of it is wrong"). Then write:

- `<domain>-codebase` (template in `skill-shapes.md`);
- the "Code" section of each component skill;
- the `team: <domain>` label on each repository (see `context-graph.md`);
- `repository_url` on each service entity.

Mark what came from the code `(from code: <repo>/<path>)`.
