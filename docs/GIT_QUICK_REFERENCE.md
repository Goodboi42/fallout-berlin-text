# Git Quick Reference for Fallout: Berlin

## Your Project is Now Saved! ✅

Your project is now tracked with Git. Here's a quick reference for daily use.

## Essential Commands

### Check Status
```bash
git status
```
Shows what files changed since last commit.

### Save Your Work (Commit)
```bash
git add .                    # Stage all changes
git commit -m "Description"  # Save with a message
```

**Example:**
```bash
git add .
git commit -m "Added new location: Vault 17"
```

### View History
```bash
git log
```
Shows all your commits.

### Undo Changes
```bash
git restore <filename>      # Undo changes to a file
git restore .                # Undo all changes
```

## Daily Workflow

1. **Start working** - Make changes to files
2. **Check status** - `git status` to see what changed
3. **Save changes** - `git add .` then `git commit -m "message"`
4. **Repeat!**

## Good Commit Messages

Write clear, descriptive messages:
- ✅ "Added dialogue system for Vault 17 NPCs"
- ✅ "Fixed inventory weight calculation bug"
- ✅ "Added new quest: The Spree Purification Project"
- ❌ "fix"
- ❌ "changes"
- ❌ "update"

## Backing Up Online (Optional but Recommended)

### Step 1: Create GitHub Account
1. Go to https://github.com
2. Sign up (free)
3. Create a new repository named "fallout-berlin"

### Step 2: Connect Your Project
```bash
git remote add origin https://github.com/YOUR_USERNAME/fallout-berlin.git
git branch -M main
git push -u origin main
```

### Step 3: Push Future Changes
```bash
git add .
git commit -m "Your message"
git push
```

## What's Already Saved

Your first commit includes:
- ✅ All game mechanics (player, inventory, quests, etc.)
- ✅ Worldbuilding document
- ✅ Documentation files
- ✅ Game launcher

## What's NOT Saved (and shouldn't be)

- Game save files (in `saves/` folder)
- Python cache files (`__pycache__/`)
- IDE settings

These are automatically excluded by `.gitignore`.

## Need Help?

- `git help` - General help
- `git help <command>` - Help for specific command
- `git status` - Always safe to run, shows current state

## Remember

- **Commit often** - Don't wait until you're "done"
- **Write clear messages** - Future you will thank you
- **Back up online** - Use GitHub for cloud backup

Your project is safe! 🎉
