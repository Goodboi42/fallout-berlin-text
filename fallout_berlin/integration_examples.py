"""
Integration Guide for Enhanced ASCII Art System
Shows how to integrate the advanced art features into Fallout Berlin
"""

from enhanced_art_system import (
    SceneRenderer, Animation, ArtFrame, ArtComposer, 
    AdvancedArtLibrary, ArtEffects, WeatherEffect
)
from colorama import Fore, Style
import time


# ============================================================================
# EXAMPLE 1: Enhanced Location Descriptions
# ============================================================================

def enhanced_look_command(game_engine):
    """
    Replace or enhance the existing look command with rich visuals
    
    Integration Point: In game_engine.py, modify the _handle_look() method
    """
    location = game_engine.location_manager.get_location(game_engine.state.current_location)
    renderer = SceneRenderer(width=80)
    
    # Determine weather and time
    weather = game_engine.state.current_weather if hasattr(game_engine.state, 'current_weather') else None
    time_of_day = game_engine.state.time_of_day if hasattr(game_engine.state, 'time_of_day') else "day"
    
    # Render the scene
    scene = renderer.render_location_scene(
        location.location_id,
        weather=weather,
        time_of_day=time_of_day
    )
    
    print(scene)
    print(f"\n{Fore.CYAN}{location.name}{Style.RESET_ALL}")
    print(location.description)
    
    # Show available exits with styled output
    if location.connections:
        composer = ArtComposer()
        exits_text = "Available exits:\n" + "\n".join([f"  → {direction}" for direction in location.connections.keys()])
        print("\n" + composer.create_border(exits_text, "single", Fore.YELLOW))


# ============================================================================
# EXAMPLE 2: Dynamic Combat Visualization
# ============================================================================

def enhanced_combat_display(combat_manager, player, enemy, last_action=None):
    """
    Enhance combat display with dynamic art
    
    Integration Point: In combat.py or game_engine.py combat methods
    """
    renderer = SceneRenderer()
    
    # Map action types to art
    action_map = {
        "melee": "melee_attack",
        "shoot": "ranged_attack",
        "critical": "critical_hit",
        "kill": "enemy_defeated"
    }
    
    action_art = action_map.get(last_action)
    
    # Render combat scene
    scene = renderer.render_combat_scene(
        player.health,
        enemy.name,
        enemy.health,
        action=action_art
    )
    
    print(scene)
    
    # Add atmospheric effects based on enemy type
    if "radiation" in enemy.name.lower() or "glowing" in enemy.name.lower():
        print(AdvancedArtLibrary.ATMOSPHERE["radiation_glow"])


def show_combat_result(won: bool, xp_gained: int = 0):
    """
    Show combat result with visual flair
    """
    if won:
        print(ArtEffects.quest_complete().replace("QUEST COMPLETED", "ENEMY DEFEATED"))
        if xp_gained > 0:
            print(f"\n{Fore.YELLOW}✦ Gained {xp_gained} XP ✦{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}{'═' * 40}")
        print("YOU WERE DEFEATED")
        print(f"{'═' * 40}{Style.RESET_ALL}\n")


# ============================================================================
# EXAMPLE 3: Animated Transitions
# ============================================================================

def transition_to_location(from_location: str, to_location: str):
    """
    Show animated transition between locations
    
    Integration Point: In _handle_move() method
    """
    print(f"\n{Fore.CYAN}Traveling...{Style.RESET_ALL}\n")
    
    # Simple loading animation
    frames = [
        ArtFrame(" ·      ", Fore.WHITE, 0.15),
        ArtFrame("  ·     ", Fore.WHITE, 0.15),
        ArtFrame("   ·    ", Fore.WHITE, 0.15),
        ArtFrame("    ·   ", Fore.WHITE, 0.15),
        ArtFrame("     ·  ", Fore.WHITE, 0.15),
        ArtFrame("      · ", Fore.WHITE, 0.15),
    ]
    
    travel_animation = Animation(frames, loop=True)
    
    # Play for a short time
    for _ in range(3):
        for frame in travel_animation.frames:
            print(f"\r{frame.render()}", end='', flush=True)
            time.sleep(frame.delay)
    
    print(f"\r{Fore.GREEN}✓ Arrived at {to_location}{Style.RESET_ALL}\n")


# ============================================================================
# EXAMPLE 4: Interactive Terminal Hacking
# ============================================================================

def enhanced_terminal_display():
    """
    Show terminal with enhanced visuals
    
    Integration Point: In _handle_hack() or _play_hacking_minigame()
    """
    terminal_art = AdvancedArtLibrary.INTERACTIVE["terminal"]
    composer = ArtComposer()
    
    # Add border and color
    print(composer.center_text(terminal_art, 80))
    print(f"\n{Fore.GREEN}ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Initializing...{Style.RESET_ALL}")
    
    # Simulate loading
    for i in range(3):
        print(f"{Fore.GREEN}{'.' * (i + 1)}{Style.RESET_ALL}", end='', flush=True)
        time.sleep(0.3)
    
    print(f"\n{Fore.GREEN}[READY]{Style.RESET_ALL}\n")


# ============================================================================
# EXAMPLE 5: Level Up Celebration
# ============================================================================

def show_level_up_sequence(player, new_level: int):
    """
    Show elaborate level up sequence
    
    Integration Point: In player.py level_up() method or wherever XP is processed
    """
    # Play animation
    level_up_anim = Animation(AdvancedArtLibrary.ANIMATIONS["level_up"], loop=False)
    
    print("\n" * 3)
    for frame in level_up_anim.frames:
        print(f"\r{ArtComposer.center_text(frame.render(), 80)}", flush=True)
        time.sleep(frame.delay)
    
    # Show splash
    print(ArtEffects.level_up_splash())
    print(f"\n{Fore.YELLOW}{'═' * 60}")
    print(f"  YOU REACHED LEVEL {new_level}!")
    print(f"{'═' * 60}{Style.RESET_ALL}\n")
    
    # Show stats increase
    print(f"{Fore.GREEN}✦ Health +10")
    print(f"✦ Skill Point +1{Style.RESET_ALL}\n")


# ============================================================================
# EXAMPLE 6: Weather System Integration
# ============================================================================

def display_weather_change(new_weather: str):
    """
    Show weather change with effects
    
    Integration Point: Create a weather system and call this on change
    """
    print(f"\n{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")
    
    if new_weather == "radiation_storm":
        print(WeatherEffect.generate_radiation_storm(60, 5))
        print(f"\n{Fore.GREEN}☢ A RADIATION STORM APPROACHES ☢{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Take cover! High radiation levels detected.{Style.RESET_ALL}")
    
    elif new_weather == "rain":
        print(WeatherEffect.generate_rain(60, 5, intensity=0.4))
        print(f"\n{Fore.BLUE}It begins to rain...{Style.RESET_ALL}")
    
    elif new_weather == "fog":
        print(WeatherEffect.generate_fog(60, 4))
        print(f"\n{Fore.WHITE}Thick fog rolls in, reducing visibility.{Style.RESET_ALL}")
    
    elif new_weather == "clear":
        print(f"\n{Fore.YELLOW}☼ The weather clears up ☼{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}\n")


# ============================================================================
# EXAMPLE 7: NPC Dialogue Enhancement
# ============================================================================

def show_npc_dialogue(npc_name: str, dialogue: str, npc_type: str = "friendly"):
    """
    Enhanced NPC dialogue display
    
    Integration Point: In dialogue.py or where NPC dialogue is shown
    """
    renderer = SceneRenderer()
    
    # Select NPC art based on type
    npc_art_map = {
        "friendly": r"""
              ╱◥█◣
             ┃◢●◤
             ┃ ┃
             ┗━┛
        """,
        "hostile": r"""
              ╱◥█◣
             ┃◢☠◤
             ┃ ┃
             ┗━┛
        """,
        "merchant": r"""
              ╱◥█◣
             ┃◢$◤
             ┃ ┃
             ┗━┛
        """,
    }
    
    npc_art = npc_art_map.get(npc_type, npc_art_map["friendly"])
    scene = renderer.render_dialogue_scene(npc_name, npc_art, dialogue)
    
    print(scene)


# ============================================================================
# EXAMPLE 8: Quest Notifications
# ============================================================================

def show_quest_notification(quest_name: str, notification_type: str):
    """
    Show quest-related notifications with style
    
    Integration Point: In quest.py quest update methods
    """
    composer = ArtComposer()
    
    if notification_type == "new":
        text = f"NEW QUEST\n{quest_name}"
        print(composer.create_border(text, "double", Fore.CYAN))
    
    elif notification_type == "update":
        text = f"QUEST UPDATED\n{quest_name}"
        print(composer.create_border(text, "single", Fore.YELLOW))
    
    elif notification_type == "complete":
        print(ArtEffects.quest_complete())
        print(f"{Fore.GREEN}{quest_name}{Style.RESET_ALL}\n")


# ============================================================================
# EXAMPLE 9: Loot Discovery
# ============================================================================

def show_loot_found(items: list):
    """
    Show loot container opening
    
    Integration Point: In location.py or wherever loot is found
    """
    print("\n" + ArtComposer.center_text(AdvancedArtLibrary.INTERACTIVE["loot_container"], 80))
    print(f"\n{Fore.YELLOW}You found:{Style.RESET_ALL}\n")
    
    for item in items:
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {item}")
    
    print()


# ============================================================================
# EXAMPLE 10: Status Screen Enhancement
# ============================================================================

def show_enhanced_status(player):
    """
    Enhanced status/character screen
    
    Integration Point: Replace or enhance existing status display
    """
    composer = ArtComposer()
    
    # Player info section
    info = f"""
NAME: {player.name}
LEVEL: {player.level}
XP: {player.experience}/{player.experience_to_next_level}
    """
    
    # Stats section with bars
    health_percent = player.health / player.max_health
    health_bar = SceneRenderer()._get_health_bar(health_percent)
    
    stats = f"""
HEALTH: {player.health}/{player.max_health}
{health_bar}

S.P.E.C.I.A.L:
  STR: {player.strength}  ║ PER: {player.perception}
  END: {player.endurance}  ║ CHA: {player.charisma}
  INT: {player.intelligence}  ║ AGI: {player.agility}
  LCK: {player.luck}
    """
    
    # Compose and display
    print(f"\n{Fore.CYAN}{'═' * 60}")
    print(composer.center_text("CHARACTER STATUS", 60))
    print(f"{'═' * 60}{Style.RESET_ALL}\n")
    
    print(composer.create_border(info.strip(), "double", Fore.CYAN))
    print(composer.create_border(stats.strip(), "single", Fore.YELLOW))


# ============================================================================
# QUICK INTEGRATION SNIPPETS
# ============================================================================

"""
QUICK COPY-PASTE SNIPPETS FOR GAME_ENGINE.PY:

1. In __init__, add:
    from enhanced_art_system import SceneRenderer, ArtEffects
    self.scene_renderer = SceneRenderer()

2. In _handle_look, replace location display with:
    scene = self.scene_renderer.render_location_scene(self.state.current_location)
    print(scene)

3. In combat start, add:
    print(self.scene_renderer.render_combat_scene(
        self.state.player.health, enemy.name, enemy.health
    ))

4. In level up code, add:
    from enhanced_art_system import ArtEffects
    print(ArtEffects.level_up_splash())

5. In quest completion, add:
    print(ArtEffects.quest_complete())

6. For hacking minigame, add at start:
    print(AdvancedArtLibrary.INTERACTIVE["terminal"])
"""


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  FALLOUT BERLIN - ENHANCED ASCII ART SYSTEM                   ║
║  Integration Guide & Examples                                 ║
║                                                               ║
║  This file contains practical examples for integrating        ║
║  the enhanced art system into your game.                      ║
║                                                               ║
║  See function docstrings for integration points.              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
