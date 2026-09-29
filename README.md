# BayanSafe
Disaster Preparedness Game

# BayanSafe: Group Guide to Working on the `dev` Branch

Repo: https://github.com/JayEL-01/BayanSafe

**Golden rule:** work only in `dev`. Never push to `main`. The owner merges `dev` into `main` when it is ready.

---

## Part 1: One-time setup

### 1. Install Git
Download from https://git-scm.com/download/win and install with the default options. Then open **PowerShell** and check:

```powershell
git --version
```

### 2. Set your identity
Use your own name and the email of your GitHub account:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3. Accept the invitation
The owner invites you as a collaborator. Accept it from your email or at https://github.com/notifications. Without this you cannot push.

### 4. Clone the project and switch to `dev`

```powershell
cd C:\CODING
git clone https://github.com/JayEL-01/BayanSafe.git
cd BayanSafe
git checkout dev
```

Check which branch you are on (the one with `*`):

```powershell
git branch
```

### 5. Sign in
The first time you push, Git asks you to sign in. Choose **Sign in with your browser** and approve. If it asks for a password, use a **Personal Access Token** (GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic) > tick `repo`).

---

## Part 2: How to commit and push your changes

Run everything from inside the project folder.

### Step 1: Get the latest work from your group

```powershell
git pull
```

### Step 2: Edit your code
Make your changes in your editor and save the files.

### Step 3: See what changed

```powershell
git status
```

- **Red** files are changed but not staged yet.
- **Green** files are staged and ready to commit.

### Step 4: Stage your changes
Stage everything:

```powershell
git add .
```

Or stage only specific files:

```powershell
git add src/states/main_menu.py
```

### Step 5: Commit (save a snapshot on your computer)

```powershell
git commit -m "describe what you changed"
```

**Always include `-m "message"`.** If you type only `git commit`, a text editor opens and it can look like Git is stuck. Good messages: `"add emergency contact form"`, `"fix map marker bug"`. Bad messages: `"stuff"`, `"changes"`.

### Step 6: Push (upload to GitHub)

```powershell
git push
```

A commit is saved only on your PC until you push. If you commit but do not push, nothing shows on GitHub.

### Step 7: Check on GitHub
Open the repo, switch the branch dropdown from `main` to `dev`, and confirm your commit is listed.

### The whole routine in one block

```powershell
git pull
# ...edit your code...
git add .
git commit -m "what I changed"
git push
```

---

## Part 3: Python `__pycache__` files (important)

When you run the game, Python creates `__pycache__` folders with `.pyc` files. These are auto-generated and **must not be committed**. They cause errors like:

```
error: The following untracked working tree files would be overwritten by checkout:
        src/states/__pycache__/big_map.cpython-314.pyc
```

### Fix the error when switching branches or pulling
Delete the local cache folder (Python recreates it), then retry:

```powershell
Remove-Item -Recurse -Force src/states/__pycache__
git checkout dev
git pull
```

### Stop it for good with a `.gitignore`
Create a file named `.gitignore` in the project root with these lines:

```
__pycache__/
*.pyc
```

Commit it:

```powershell
git add .gitignore
git commit -m "add gitignore"
git push
```

### If `.pyc` files are already committed
Remove them from Git (this does not delete them from your PC):

```powershell
git rm -r --cached src/states/__pycache__
git commit -m "remove pycache from repo"
git push
```

If Git only shows them as `deleted:` in `git status`, stage the deletions with:

```powershell
git add src/states/__pycache__
git commit -m "remove pycache from repo"
git push
```

After that, everyone runs `git pull`.

---

## Part 4: Common problems and fixes

**"Author identity unknown"**
Do Part 1, Step 2, then commit again.

**"nothing added to commit" or "no changes added to commit"**
You forgot `git add .`. Stage your files first, then commit.

**"I committed but nothing shows on GitHub"**
Run `git push`. Also make sure the GitHub branch dropdown is set to `dev`.

**"Updates were rejected" or "failed to push some refs"**
A teammate pushed before you. Run:

```powershell
git pull
git push
```

**"Permission denied" or 403 error**
You have not accepted the invitation, or you are signed in to the wrong GitHub account.

**"Your local changes would be overwritten"**
Commit your work first, or set it aside temporarily:

```powershell
git stash
git pull
git stash pop
```

**Merge conflict (Git says CONFLICT)**
Two people edited the same lines. Open the file, find the markers `<<<<<<<`, `=======`, `>>>>>>>`, keep the correct code, delete the markers, then:

```powershell
git add .
git commit -m "resolve merge conflict"
git push
```

**"I accidentally worked on `main`"**
Do not push. Tell the owner, or commit your work, run `git checkout dev`, and redo your changes there.

**"I want to undo my changes to a file"** (not yet committed)

```powershell
git restore path/to/file
```

---

## Part 5: Team rules

- Run `git pull` before you start and before you push.
- Commit small and often, with clear messages.
- Tell the group which files you are editing to avoid conflicts.
- Never commit passwords, API keys, or `.env` files.
- Never use `git push --force`.
- Never push to `main`.

---

## Quick cheat sheet

| Command | What it does |
|---|---|
| `git pull` | Download the latest changes |
| `git status` | Show changed files and branch status |
| `git add .` | Stage all changes |
| `git commit -m "msg"` | Save a snapshot locally |
| `git push` | Upload commits to GitHub |
| `git branch` | Show current branch |
| `git checkout dev` | Switch to the `dev` branch |
| `git log --oneline -5` | Show the last 5 commits |
| `git diff` | Show uncommitted changes |
| `git restore file` | Discard changes to a file |

### Get one file from another branch

```powershell
git fetch
git checkout origin/dev -- README.md
git commit -m "add README from dev"
git push
```

| Command | What it does |
|---|---|
| `git fetch` | Download the latest info from GitHub |
| `git checkout origin/dev -- path/to/file` | Copy one file from `dev` into your current branch |
| `git checkout origin/dev -- src/states` | Copy a whole folder from `dev` |
| `git show origin/dev:README.md` | Read a file from `dev` without copying it |
| `git ls-tree --name-only origin/dev` | List the files on `dev` |
| `git diff main origin/dev -- file` | Compare a file between `main` and `dev` |

### Merge branches

```powershell
git checkout main
git pull
git merge dev
git push
```

| Command | What it does |
|---|---|
| `git merge dev` | Bring `dev` changes into the current branch |
| `git merge --abort` | Cancel a merge that went wrong |
| `git checkout --ours file` | On conflict, keep the version from your current branch |
| `git checkout --theirs file` | On conflict, keep the version from the branch you merged in |
| `git log main..dev --oneline` | Preview commits `dev` has that `main` doesn't |

### Fix `__pycache__` problems

```powershell
Remove-Item -Recurse -Force src/states/__pycache__
git rm -r --cached src/states/__pycache__
```

Add a `.gitignore` in the project root containing:

```
__pycache__/
*.pyc
```