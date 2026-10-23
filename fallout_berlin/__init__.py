"""
Fallout: Berlin - Text-Based Adventure Game

A narrative-driven text-based RPG set in a post-apocalyptic Berlin.
"""

__version__ = "0.1.0"
__author__ = "Fallout: Berlin Development Team"

# Core game engine
try:
    from fallout_berlin.improved_game_engine import ImprovedGameEngine as GameEngine, main
except ImportError:
    from fallout_berlin.game_engine import ImprovedGameEngine as GameEngine, main

# Manager classes
from fallout_berlin.combat import CombatManager
from fallout_berlin.ui import UIManager

__all__ = [
    'GameEngine',
    'CombatManager',
    'UIManager',
    'main',
]
