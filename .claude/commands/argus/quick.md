---
description: Quick task — create a chore, implement it, and mark done
argument-hint: "[task description]"
---

You are now running an **Argus quick task**. This is a streamlined workflow for small chores that don't need full spec or story breakdown.

The user's input is: **$ARGUMENTS**

## Instructions

1. Create a chore in the PM tool with a concise title based on the user's description
2. Move the chore to "In Progress"
3. Create a feature branch following Gitflow (`chore/{branch-name}`)
4. Implement the task with atomic commits
5. Run tests to verify nothing is broken
6. Create the PR following the "Create PR Guidelines" below
7. Move the chore to "In QA"
8. Report completion to the user with the PR link and chore ID

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

- Keep it simple — quick tasks should not require multi-step planning
- Follow Gitflow and commit conventions
- If the task turns out to be complex, suggest switching to `/argus:execute` instead
