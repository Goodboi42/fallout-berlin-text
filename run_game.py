#!/usr/bin/env python
"""
Simple launcher script for Fallout: Berlin
Run this file to start the game.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from fallout_berlin.game_engine import main
    main()
except ImportError as e:

    print(f"Import error: {e}")
    print("\nMake sure you're running from the project root directory.")
    print("Try: python run_game.py")
    sys.exit(1)
