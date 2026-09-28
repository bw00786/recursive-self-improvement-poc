# Git

Git is a distributed version control system. A branch is a movable pointer to
a commit, so creating a branch is cheap. Merge combines histories and can
create a merge commit; rebase replays commits onto a new base and produces a
linear history.

Feature branches isolate work in progress from the main branch. A revert
commit undoes a change without rewriting history, which makes revert safer
than reset on shared branches.

Tags mark release points; annotated tags store a message and tagger identity.
