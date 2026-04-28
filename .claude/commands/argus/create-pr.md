---
description: Create a PR based on the current branch
---

You are now running an **Argus create PR command** on the current branch.

## Instructions

1. Remember the current branch: !`git branch --show-current`
2. Review the diff provided by `git diff develop...HEAD` to understand what was implemented
3. Extract the ticket ID from the current branch name and read it from the PM tool to understand the scope
4. Create or update the PR following the "Create PR Guidelines" below

## Create PR Guidelines

> **Reminder**: Read tool uses `file_path` (not `file`). Bash tool uses `command` (not `cmd`).

When creating the PR, follow these guidelines:

1. Check if `.github/PULL_REQUEST_TEMPLATE.md` exists in the project root
   - If the template DOES exist:
      1. Read the template file, and populate each section using context from the ticket and commits
      2. Populate the `Story:` field based on the PM tool:
         - **Shortcut**: `[{{config.commit_prefix}}-{id}](https://app.shortcut.com/{org}/story/{id})`
         - **Linear**: `[{{config.commit_prefix}}-{id}](https://linear.app/{workspace}/issue/{id})`
         - **GitHub Projects** / **GitHub Issues**: `[#{number}](https://github.com/{owner}/{repo}/issues/{number})` — resolve `{owner}/{repo}` from `config.github_repo` if set, otherwise auto-detect from `git remote get-url origin`
      3. Use the filled template as the body upon creating the PR
   - If the template DOES NOT exist, stop and warn the user
2. Push the branch to remote with the `git push -u origin HEAD` command
3. Determine the title based on the ticket title, following the `[<prefix>-<ticket id>] <ticket title>` format
4. Determine the label based on the ticket type:
   - story → `type : feature`
   - bug → `type : bug`
   - chore → `type : chore`
5. Create the PR using the GitHub CLI: `gh pr create --draft --base develop --assignee @me --label "<label>" --title "<title>" --body "<body>"`


## Constraints

- Do NOT create the PR if the current branch is `main` or `develop`
- Do NOT create the PR if there are uncommitted changes on the current branch
