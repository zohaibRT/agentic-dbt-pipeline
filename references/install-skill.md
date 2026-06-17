# Install agentic-dbt-pipeline Skill

Install once — then invoke with: **"Use the agentic-dbt-pipeline skill"** (same pattern as dbt Agent Skills).

## Recommended — npx skills from GitHub

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
npx skills add zohaibRT/agentic-dbt-pipeline
```

Repository: https://github.com/zohaibRT/agentic-dbt-pipeline

## Manual — copy into project

```text
.agents/skills/agentic-dbt-pipeline/
```

Clone this repo and copy the folder contents, or symlink:

```bash
git clone https://github.com/zohaibRT/agentic-dbt-pipeline.git
cp -r agentic-dbt-pipeline .agents/skills/agentic-dbt-pipeline
```

## Verify

```text
.agents/skills/agentic-dbt-pipeline/SKILL.md exists?
.agents/skills/using-dbt-for-analytics-engineering/SKILL.md exists?
```

## Configure per project

Edit [project.config.yml](../project.config.yml) for warehouse, project name, and layer paths.  
Do **not** hardcode GitHub accounts — use `github_repo_name` in the prompt; owner from `gh api user`.

## One-shot prompt

See [ONE_SHOT_PROMPT.md](../ONE_SHOT_PROMPT.md).
