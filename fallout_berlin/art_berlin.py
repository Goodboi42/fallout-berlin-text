"""
Consolidated Art Assets for Fallout Berlin
This module serves as a bridge for the legacy and redesigned art systems.
"""

from fallout_berlin.art_master import LOCATIONS as MASTER_LOCATIONS
from fallout_berlin.new_art import LOCATION_ART, ENEMY_ART, ITEM_ART

# Consolidated BERLIN_ART dictionary
BERLIN_ART = {
    # UI Icons
    "caps": "©",
    "radio": "📻",
    "player": "👤",
    "health": "❤",
    "armor": "🛡",
    "weapon": "🔫",
}

# Merge all locations
BERLIN_ART.update(MASTER_LOCATIONS)
BERLIN_ART.update(LOCATION_ART)

# Merge enemies
BERLIN_ART.update(ENEMY_ART)

# Merge items
BERLIN_ART.update(ITEM_ART)
