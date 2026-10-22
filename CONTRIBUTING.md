# Contributing to trek-planner

This file describes how a change reaches `main`. It applies to humans and to
Paperclip agents alike. For pull requests it replaces the ACTION_PLAN workflow
described in `CLAUDE.md`.

## 1. Branch

- Branch from `main`. Use a short, descriptive name such as `docs/isd-22-contributing`.
- Never push to `main` or `master`. The pre-push hook rejects it; do not bypass
  it with `--no-verify` and do not change `core.hooksPath`.

## 2. Pull request

- Open a pull request against `main` for every change, however small.
- Say in the description what changed and which issue it belongs to.
- CI runs on every pull request to `main` (`.github/workflows/ci.yml`). Keep it green.
- After this file merges, Roald makes `CI / checks` a required check on `main`, so
  a pull request with red CI cannot be merged.

## 3. Review

- The reviewer reads the pull request and leaves comments or an approval.
- Once a pull request has review comments, never force-push its branch. Add
  commits instead.

## 4. Merge

A pull request is merged only when all three hold:

1. Roald has approved the merge for the pull request's current head commit.
2. CI is green on that head commit.
3. The reviewer has approved.

Only the Engineering Lead merges, and never with `gh pr merge --admin`.

## 5. Commit messages

- Use a short imperative subject line, for example `Add CONTRIBUTING.md and CI workflow`.
- Every commit made by a Paperclip agent ends with the trailer
  `Assisted-by: Paperclip <role>`, for example
  `Assisted-by: Paperclip Senior Developer`.
- Commits made by Roald do not need the trailer.
