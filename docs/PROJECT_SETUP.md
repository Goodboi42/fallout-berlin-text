# Fallout: Berlin - Project Setup Guide

## Version Control (Git)

This project uses Git for version control. Here's how to use it:

### Initial Setup (Already Done)
- Git repository initialized
- `.gitignore` file created to exclude unnecessary files

### Making Your First Commit

1. **Check what files will be committed:**
   ```bash
   git status
   ```

2. **Add all project files:**
   ```bash
   git add .
   ```

3. **Make your first commit:**
   ```bash
   git commit -m "Initial commit: Fallout Berlin game mechanics"
   ```

### Daily Workflow

**Before starting work:**
```bash
git status  # See what changed
```

**After making changes:**
```bash
git add .                    # Stage all changes
git commit -m "Description"   # Save changes with a message
```

**View commit history:**
```bash
git log
```

### Creating a Backup (Remote Repository)

To save your project online (GitHub, GitLab, etc.):

1. **Create a repository on GitHub/GitLab**
   - Go to GitHub.com and create a new repository
   - Don't initialize with README (we already have files)

2. **Connect your local project:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/fallout-berlin.git
   git branch -M main
   git push -u origin main
   ```

3. **Push future changes:**
   ```bash
   git add .
   git commit -m "Your commit message"
   git push
   ```

### Useful Git Commands

- `git status` - See what files changed
- `git add <file>` - Stage a specific file
- `git add .` - Stage all changes
- `git commit -m "message"` - Save changes
- `git log` - View commit history
- `git diff` - See what changed
- `git restore <file>` - Undo changes to a file

## Project Structure

```
fallout_berlin/
├── __init__.py
├── game_state.py
├── player.py
├── item.py
├── inventory.py
├── location.py
├── dialogue.py
├── quest.py
├── game_engine.py
└── main.py

Documentation:
├── Fallout_Berlin_Worldbuilding.md
├── README.md
├── QUICKSTART.md
├── GAME_MECHANICS.md
└── PROJECT_SETUP.md

Other:
├── .gitignore          # Files to exclude from Git
├── run_game.py         # Game launcher
└── saves/              # Game save files (not in Git)
```

## Best Practices

1. **Commit often** - Save your work frequently
2. **Write clear commit messages** - Describe what you changed
3. **Don't commit save files** - They're in `.gitignore`
4. **Back up to remote** - Use GitHub/GitLab for cloud backup

## Troubleshooting

**If you make a mistake:**
```bash
git restore <file>  # Undo changes to a file
git reset HEAD~1     # Undo last commit (keeps changes)
```

**If you want to see what changed:**
```bash
git diff
```

## Next Steps

1. Make your first commit (see commands above)
2. Optionally set up a GitHub repository for cloud backup
3. Continue developing and commit regularly!
