# Fallout: Berlin - Quick Start Guide

## Running the Game

### Option 1: Run as Module
```bash
cd C:\Users\felix.LAPTOP-STLSVUGN
python -m fallout_berlin.game_engine
```

### Option 2: Direct Python Execution
```bash
cd C:\Users\felix.LAPTOP-STLSVUGN
python fallout_berlin\game_engine.py
```

### Option 3: Using main.py
```bash
cd C:\Users\felix.LAPTOP-STLSVUGN
python fallout_berlin\main.py
```

## First Time Setup

1. Make sure you have Python 3.6+ installed
2. Navigate to the project directory
3. Run one of the commands above
4. Choose "New Game" from the menu
5. Follow the character creation prompts

## Gameplay Basics

### Character Creation
- Choose your origin (affects starting skills and items)
- Allocate 5 points to S.P.E.C.I.A.L. stats
- Each stat can be increased from 5 to 10

### Basic Commands
- `go north` or `n` - Move north
- `look` - Examine current location
- `inventory` or `i` - View inventory
- `stats` - View character stats
- `talk trader` - Talk to NPCs
- `quest` - View quest log
- `save` - Save your game
- `help` - Show all commands

### Starting Location
You begin at **Checkpoint Charlie Market**, a neutral trading hub.

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the project root directory:
```bash
cd C:\Users\felix.LAPTOP-STLSVUGN
python -m fallout_berlin.game_engine
```

### Save Files
Save files are stored in the `saves/` directory, which is created automatically.

## Next Steps

- Explore the wasteland
- Complete the "First Steps" quest
- Talk to NPCs to learn about the world
- Build your character's reputation with factions
- Discover new locations

Enjoy your journey through Fallout: Berlin!
