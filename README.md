# BayanSafe

A disaster preparedness game that teaches players what to do before, during, and after a disaster.

Repository: https://github.com/JayEL-01/BayanSafe

---

## Contents

- [About the project](#about-the-project)
- [Getting started](#getting-started)
- [Working with Git as a team](#working-with-git-as-a-team)
- [Dealing with `__pycache__` files](#dealing-with-__pycache__-files)
- [Troubleshooting](#troubleshooting)
- [Team rules](#team-rules)
- [Cheat sheet](#cheat-sheet)

---

## About the project

BayanSafe is a game about staying safe when disasters happen. Players pick a character, move around the map, and work through stages that build practical safety knowledge.

The story campaign follows the supplied island map as one continuous journey. It starts in San Isidro, follows the roads shown on the map, and ends at Mount Talon. During play, press **M** to see the complete supplied map, your current location, and the next marked story stop; the map's own red dashed roads show the route. Press **Tab** there to switch to the readable place directory. The island is one connected 1,920 × 720 playfield. Rivers block travel except at visible bridge crossings, so players must use the crossings to move between regions. Each disaster region has four story beats. Hazards join at the level shown in the campaign and remain active through later locations, building from three hazards at the North West Plateau to all eight in the Volcano Valleys and finale. At chapter boundaries, named characters reveal what changed through a short, staged dialogue scene; Tarsi provides optional gameplay hints. There are no post-mission replay or stage-selection choices. The finale resolves into one of three outcomes based on campaign performance and the shutdown decision.

| Region level | Location and escalation |
|---:|---|
| Opening | Home Village: the player’s home and the first warning |
| Levels 1–4 | North West Plateau: Earthquake → Landslide → recovery lull → Tsunami |
| Levels 1–4 | Central Town: Flash Fire → Landslide → Typhoon → Flash Flood |
| Levels 1–4 | Harbor: Flash Flood → Typhoon → Severe Flooding → Fire + Tsunami |
| Levels 1–4 | North East Plains: Typhoon → Flash Flood + Severe Flooding → Landslide → Earthquake + Volcanic Eruption |
| Levels 1–4 | Volcano Valleys: Volcanic Eruption → Landslide + Flash Fire → Flash Flood → all eight hazards |
| Finale | Main Control Room: all hazards continue while the player makes the shutdown decision |

The desktop game saves locally. The Flask/PostgreSQL service is separate from the game client. RFID login is for student identification; it does not collect survival items. Physical RFID, LCD, and serial-controller support still depends on the actual reader, board, display, and communication protocol.

At an evacuation point, the player can end the task phase before optional objectives are complete. Villagers then head for the safe zone; the flood escort mission requires both the player and Nanay Luz to arrive before it ends. Endings weigh campaign-wide objective completion, supplies, rescues, damage, and the final shutdown decision. The leaderboard can be filtered by individual hazards and combinations that appear in the campaign.

Mission scoring is transparent and capped: objectives 400, supplies 200, preparation and choices 200, response time 100, and personal/property safety 100; each available rescue can add up to 100 more (maximum two rescue bonuses). A wrong safety-quiz answer subtracts 150 points and does not count as another gameplay attempt.

### Safety content references

The missions are educational scenarios, not live emergency guidance. Always follow current instructions from local authorities and your barangay DRRM office. Content reviewers can check the lessons against [PAGASA storm surge preparedness](https://bagong.pagasa.dost.gov.ph/information/storm-surge), [PHIVOLCS earthquake and tsunami guidance](https://www.phivolcs.dost.gov.ph/primer-on-the-08-june-2026-magnitude-mw-7-8-offshore-sarangani-earthquake/), [PHIVOLCS volcano preparedness](https://www.phivolcs.dost.gov.ph/volcano-preparedness/), [PHIVOLCS landslide preparedness](https://test-wp.phivolcs.dost.gov.ph/landslide-preparedness/), [BFP fire safety for young adults](https://bfp.gov.ph/wp-content/uploads/2024/08/Volume-3-Fire-Safety-for-Young-Adults.pdf), and [flood safety guidance](https://www.ready.gov/floods).

### In-game controls

| Action | Controls |
|---|---|
| Move | WASD or arrow keys |
| Talk / advance dialogue | E, Enter, or Space |
| Use character ability | Q |
| Ask Tarsi for a hint | H |
| Open / close island overview | M |
| Pause / resume | P or Escape |
| Pause menu | R restart current scene, Q leave to title |

Juan can sprint for a short burst (8-second cooldown). Maria can restore up to 35 health (20-second cooldown).

At the start of the journey, players choose a community plan (first-aid pack, route map, or radio plan) and a pace. The plan and pace carry across the continuous story. Relaxed gives more warning time, extra health, and a small speed boost; Challenge makes hazards build sooner. The final recovery scene reflects campaign scores, rescues, injuries, and property damage. NPC rescue objectives and Tarsi's advice reinforce teamwork; restarting the current scene does not remove campaign progress.

Each completed scene advances through an authored story beat tied to the supplied story document. The beat shows who is speaking, what changed because of the player's decisions, and why the journey continues. Press Enter to travel onward or Q to open the optional safety check; there is no replay or stage-selection screen between scenes. The optional overview can be opened during play with **M**.

### Mission preparation controls

| Action | Controls |
|---|---|
| Choose a plan | Left / Right or 1–3 |
| Choose a pace | Up / Down |
| Begin the journey | Enter or click **BEGIN JOURNEY** |
| Leave preparation | Escape |

In a mission, press **Tab** to expand or collapse the objective list. Wrong answers on the end-of-mission safety check reduce that run's score by 150 points.

### Project structure

```
BayanSafe/
├── data/          Characters, 22-story order, supplied map, lessons, and mission definitions
├── database/      Optional PostgreSQL schema and connection helper
├── server/        Optional Flask account, RFID, save, and quiz API
├── src/
│   ├── core/      Game loop, campaign session, and local save handling
│   ├── hazards/   Weather and disaster effects
│   ├── states/    Menus, campaign map, stages, and results
│   └── systems/   Quests and composable disaster hazards
├── README.md
└── .gitignore
```

See [HARDWARE_INTEGRATION.md](HARDWARE_INTEGRATION.md) for the supported USB HID controller mapping and the remaining board/RFID/LCD integration details.

---

## Getting started

### Run the automated checks

From the project folder, run:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The checks validate the 22-stage campaign data, verify every mission can load and render, confirm all six island regions are reachable on foot, walk residents to their evacuation destination, check text bounds and collisions across the primary screens and modal dialogs, and guard scene-transition input handling. They use Pygame's headless display, so no game window or controller is needed.

These steps are for Windows. Do them in order.

### 1. Download the tools

| Tool | Where to get it | Notes |
|---|---|---|
| Visual Studio Code | https://code.visualstudio.com | The code editor |
| Python 3.14 | https://www.python.org/downloads | On the first installer screen, tick **Add python.exe to PATH** |
| Git | https://git-scm.com/download/win | The default options are fine |

Restart VS Code (or your PC) after installing so everything gets picked up.

### 2. Check that everything installed

Open PowerShell and run:

```powershell
python --version
git --version
```

Both should print a version number.

### 3. Install the VS Code extensions

In VS Code, press `Ctrl+Shift+X` and install:

- **Python** and **Pylance** (both by Microsoft), for running code and getting hints
- **GitLens** (optional), to see who changed each line
- **Git Graph** (optional), to see the branch history visually

### 4. Set your Git identity

You only need to do this once. Use your own name and the email on your GitHub account:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 5. Accept the collaborator invitation

The owner will invite you on GitHub. Accept it from your email or at https://github.com/notifications. You can't push until you do.

### 6. Clone the project and switch to `dev`

Pick any folder where you keep your projects, such as Documents or Desktop. Open PowerShell there (or use `cd` to move into it), then run:

```powershell
git clone https://github.com/JayEL-01/BayanSafe.git
cd BayanSafe
git checkout dev
code .
```

This creates a `BayanSafe` folder inside whichever folder you were in.

Check that you're on `dev`. The current branch is the one marked with `*`:

```powershell
git branch
```

If VS Code asks whether you trust the authors of the folder, choose Yes.

### 7. Create a virtual environment

Open a terminal in VS Code (Terminal, then New Terminal) and run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

You should now see `(.venv)` at the start of the terminal line.

<details>
<summary>PowerShell says scripts are disabled</summary>

Run this once, then try activating again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

</details>

### 8. Select the interpreter

Press `Ctrl+Shift+P`, type **Python: Select Interpreter**, and choose the one that shows `.venv`.

### 9. Install the packages

This project uses **pygame-ce** (the community edition of pygame). Make sure the virtual environment is active (you should see `(.venv)` in the terminal), then install it:

```powershell
pip install pygame-ce
```

Install all game and optional backend dependencies in one go:

```powershell
pip install -r requirements.txt
```

A few things to know about pygame-ce:

- In the code you still write `import pygame`. The package name is `pygame-ce`, but the module name is the same as regular pygame.
- **Don't install both `pygame` and `pygame-ce`.** They use the same module name and will conflict. If you already installed regular pygame, remove it first:

  ```powershell
  pip uninstall pygame
  pip install pygame-ce
  ```

- To check that it worked, run:

  ```powershell
  python -c "import pygame; print(pygame.version.ver, pygame.IS_CE)"
  ```

  It should print a version number followed by `True`.

If the install fails, make sure you're using a Python version that pygame-ce supports (check the version with `python --version`) and that `pip` is up to date:

```powershell
python -m pip install --upgrade pip
```

Keep `requirements.txt` as the reviewed dependency list. Avoid replacing it with a full `pip freeze`, which can capture unrelated packages from a developer's environment.

### 10. Run the game

```powershell
python main.py
```

If the main file has a different name or location, use that instead, for example `python src/main.py`. You can also open the file in VS Code and press the Run button at the top right.

### 11. Sign in to GitHub

The first time you push, Git will ask you to sign in. Choose **Sign in with your browser** and approve it. If it asks for a password instead, use a Personal Access Token: GitHub, then Settings, Developer settings, Personal access tokens, Tokens (classic), with the `repo` scope ticked.

---

## Working with Git as a team

> **Work only in `dev`, and never push to `main`.**
> The owner merges `dev` into `main` once it's ready.

### The everyday routine

Run these from inside the project folder:

```powershell
git pull                          # get the latest work from the group
# ...make your changes...
git add .                         # stage them
git commit -m "what I changed"    # save a snapshot on your computer
git push                          # upload it to GitHub
```

After pushing, open the repo on GitHub, switch the branch dropdown from `main` to `dev`, and check that your commit is there.

### What each step does

| Command | What it does |
|---|---|
| `git pull` | Downloads the latest changes |
| `git status` | Shows what changed. Red files aren't staged yet, green ones are |
| `git add .` | Stages all your changes. Use `git add path/to/file` for a single file |
| `git commit -m "message"` | Saves a snapshot on your computer |
| `git push` | Uploads your commits to GitHub |

Two things that trip people up:

- Always include `-m "message"` when committing. If you type just `git commit`, a text editor opens and it looks like Git is stuck.
- A commit only lives on your computer until you push it. If you committed but nothing shows on GitHub, you probably forgot `git push`.

Write commit messages that say what the change does, like `"add emergency contact form"` or `"fix map marker bug"`. Avoid vague ones like `"stuff"` or `"changes"`.

---

## Dealing with `__pycache__` files

Whenever you run the game, Python creates `__pycache__` folders full of `.pyc` files. They're generated automatically and shouldn't be committed. If one gets committed, you'll see errors like this when switching branches:

```
error: The following untracked working tree files would be overwritten by checkout:
        src/states/__pycache__/big_map.cpython-314.pyc
```

### Fixing the error

Delete your local cache folder (Python will recreate it) and try again:

```powershell
Remove-Item -Recurse -Force src/states/__pycache__
git checkout dev
git pull
```

### Preventing it

Make sure there's a `.gitignore` file in the project root containing:

```
__pycache__/
*.pyc
.venv/
```

Then commit it:

```powershell
git add .gitignore
git commit -m "add gitignore"
git push
```

### If `.pyc` files were already committed

Remove them from Git. This doesn't delete them from your computer:

```powershell
git rm -r --cached src/states/__pycache__
git commit -m "remove pycache from repo"
git push
```

If `git status` only lists them as `deleted:`, stage the deletions first:

```powershell
git add src/states/__pycache__
git commit -m "remove pycache from repo"
git push
```

Once that's pushed, everyone should run `git pull`.

---

## Troubleshooting

<details>
<summary>"python" or "git" is not recognized</summary>

Reinstall it (for Python, tick **Add python.exe to PATH**) and restart VS Code.

</details>

<details>
<summary>ModuleNotFoundError: No module named 'pygame'</summary>

The module is called `pygame` in code, but the package to install is `pygame-ce`. Activate the virtual environment and install it:

```powershell
.venv\Scripts\Activate.ps1
pip install pygame-ce
```

If you get strange errors after installing, you may have both `pygame` and `pygame-ce`. Remove both and reinstall only the CE version:

```powershell
pip uninstall pygame pygame-ce
pip install pygame-ce
```

</details>

<details>
<summary>VS Code shows import errors, but the game runs</summary>

Select the `.venv` interpreter: press `Ctrl+Shift+P` and choose **Python: Select Interpreter**.

</details>

<details>
<summary>"Author identity unknown"</summary>

Set your name and email (Getting started, step 4), then commit again.

</details>

<details>
<summary>"nothing added to commit"</summary>

You haven't staged anything yet. Run `git add .` and commit again.

</details>

<details>
<summary>I committed, but nothing shows on GitHub</summary>

Run `git push`. Also check that the branch dropdown on GitHub is set to `dev`.

</details>

<details>
<summary>"Updates were rejected" or "failed to push some refs"</summary>

Someone pushed before you did. Pull their changes, then push again:

```powershell
git pull
git push
```

</details>

<details>
<summary>"Permission denied" or a 403 error</summary>

Either you haven't accepted the invitation yet, or you're signed in to the wrong GitHub account.

</details>

<details>
<summary>"Your local changes would be overwritten"</summary>

Commit your work first, or set it aside for a moment:

```powershell
git stash
git pull
git stash pop
```

</details>

<details>
<summary>Merge conflict (Git says CONFLICT)</summary>

Two people edited the same lines. Open the file and look for the markers `<<<<<<<`, `=======`, and `>>>>>>>`. Keep the code you want, delete the markers, then:

```powershell
git add .
git commit -m "resolve merge conflict"
git push
```

In VS Code you can also click Accept Current, Accept Incoming, or Accept Both above the conflict. To cancel a merge that went wrong, run `git merge --abort`.

</details>

<details>
<summary>I accidentally worked on <code>main</code></summary>

Don't push. Tell the owner, or commit your work, run `git checkout dev`, and redo the changes there.

</details>

<details>
<summary>I want to undo my changes to a file</summary>

If you haven't committed yet:

```powershell
git restore path/to/file
```

</details>

---

## Team rules

- Run `git pull` before you start working and again before you push.
- Commit small and often, with clear messages.
- Let the group know which files you're editing so you don't overwrite each other.
- Never commit passwords, API keys, or `.env` files.
- Never use `git push --force`.
- Never push to `main`.

---

## Cheat sheet

### Everyday commands

| Command | What it does |
|---|---|
| `git pull` | Download the latest changes |
| `git status` | Show changed files and branch status |
| `git add .` | Stage all changes |
| `git commit -m "msg"` | Save a snapshot locally |
| `git push` | Upload commits to GitHub |
| `git branch` | Show the current branch |
| `git checkout dev` | Switch to the `dev` branch |
| `git log --oneline -5` | Show the last 5 commits |
| `git diff` | Show uncommitted changes |
| `git restore file` | Discard changes to a file |

### Getting one file from another branch

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

### Merging branches (owner only)

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
| `git log main..dev --oneline` | Preview commits that `dev` has and `main` doesn't |
# Reference asset pack

The NPC, player, terrain, building, item, and animated effect art in
`assets/images/game_art` is cropped from the BayanSafe reference pack in
`assets/images/bayan_pack`. `tools/prepare_bayan_pack.py` rebuilds the game art
from those source sheets and the exported animation frames in
`assets/images/sprite_frames`. The supplied labeled map remains the in-game
map reference; it is not used as walkable ground art.

