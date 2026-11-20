---
obs2pdf.template: cheatsheet
---
# Git Cheatsheet

## Setup

- `git config --global user.name "Name"` — set your name
- `git config --global user.email "a@b.c"` — set your email
- `git init` — create a repository here
- `git clone <url>` — copy a remote repository

## Everyday

- `git status` — what changed
- `git add <file>` — stage a file
- `git add -p` — stage hunk by hunk
- `git commit -m "msg"` — record staged changes
- `git commit --amend` — fix the last commit

## Inspect

- `git log --oneline --graph` — compact history
- `git diff` — unstaged changes
- `git diff --staged` — staged changes
- `git show <commit>` — one commit in full
- `git blame <file>` — who changed each line

## Branches

- `git branch` — list local branches
- `git switch <name>` — change branch
- `git switch -c <name>` — create and switch
- `git branch -d <name>` — delete a merged branch

## Merge and rebase

- `git merge <name>` — merge into the current branch
- `git rebase <base>` — replay commits onto `<base>`
- `git rebase -i HEAD~3` — edit the last three commits
- `git cherry-pick <commit>` — copy one commit here

## Remotes

- `git remote -v` — list remotes
- `git fetch` — download, don't merge
- `git pull --rebase` — fetch, then rebase
- `git push -u origin <name>` — publish a branch

## Undo

| Situation | Command |
| --- | --- |
| discard file edits | `git restore <file>` |
| unstage a file | `git restore --staged <file>` |
| undo last commit, keep changes | `git reset --soft HEAD~1` |
| invert a pushed commit | `git revert <commit>` |

## Stash

- `git stash` — shelve uncommitted changes
- `git stash list` — show shelved changes
- `git stash pop` — re-apply and drop the latest

## Tags

- `git tag v1.0` — lightweight tag
- `git tag -a v1.0 -m "msg"` — annotated tag
- `git push --tags` — publish tags

## Find things

- `git grep <pattern>` — search tracked files
- `git log -S <text>` — commits adding/removing text
- `git bisect start` — binary-search for a bug

## Handy aliases

```ini
[alias]
  st = status -sb
  lg = log --oneline --graph --decorate
  undo = reset --soft HEAD~1
```

## Ranges

- `HEAD~2` — two commits before `HEAD`
- `main..feature` — on `feature`, not on `main`
- `@{u}` — the upstream of the current branch

## Clean up

- `git clean -n` — preview untracked files to delete
- `git clean -fd` — delete untracked files and folders
- `git branch --merged` — branches safe to delete
- `git fetch --prune` — forget deleted remote branches

## Worktrees

- `git worktree add ../hotfix main` — second checkout
- `git worktree list` — show all checkouts
- `git worktree remove ../hotfix` — drop one

## Submodules

- `git submodule add <url> <dir>` — add a submodule
- `git submodule update --init --recursive` — fetch them all

## Patches

- `git format-patch -1 <commit>` — commit to a patch file
- `git am <file.patch>` — apply it as a commit
- `git apply <file.diff>` — apply without committing

## Commit messages

1. Subject line in the imperative, about 50 characters
2. Blank line
3. Body wrapped at 72 characters: *what* and *why*, not *how*

## Ignore files

```gitignore
build/          # a folder anywhere
*.log           # by extension
!keep.log       # but not this one
/secrets.txt    # only at the top level
```

- `git check-ignore -v <file>` — which rule matches
- `git rm --cached <file>` — stop tracking, keep the file

## Getting help

- `git help <command>` — full manual page
- `git <command> -h` — short usage summary
- `git help -g` — list the concept guides
