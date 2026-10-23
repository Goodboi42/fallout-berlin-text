1
#!/usr/bin/env python3
"""
Interactive Demo of Enhanced ASCII Art System for Fallout Berlin
Run this to see all features in action!
"""

import time
import sys
import colorama
from enhanced_art_system import (
    SceneRenderer, ArtEffects, AdvancedArtLibrary,
    ArtComposer, WeatherEffect, Animation, ArtFrame
)
from colorama import Fore, Style, init

# Initialize colorama
init()


def clear_screen():
    """Clear the screen (works on most terminals)"""
    print("\n" * 50)


def pause(message="Press Enter to continue..."):
    """Pause for user input"""
    try:
        input(f"\n{Fore.CYAN}{message}{Style.RESET_ALL}\n")
    except EOFError:
        time.sleep(2)


def print_section_header(title: str):
    """Print a nice section header"""
    print("\n" + "=" * 80)
    print(f"{Fore.YELLOW}{title.center(80)}{Style.RESET_ALL}")
    print("=" * 80 + "\n")


def demo_title_screen():
    """Demo 1: Enhanced title screen"""
    print_section_header("DEMO 1: Title Screen & Borders")
    
    from art import TITLE
    composer = ArtComposer()
    
    # Show title with border
    print(f"{Fore.GREEN}{TITLE}{Style.RESET_ALL}")
    
    welcome_text = """
FALLOUT: BERLIN

Welcome to the wasteland, survivor.
The year is 2287. Berlin lies in ruins,
divided by old walls and new conflicts.

Your story begins here...
    """
    
    print(composer.create_border(welcome_text.strip(), "double", Fore.CYAN))
    
    pause()


def demo_location_scenes():
    """Demo 2: Location scenes with weather"""
    print_section_header("DEMO 2: Location Scenes with Weather Effects")
    
    renderer = SceneRenderer(width=80)
    
    locations = [
        ("checkpoint_charlie", None, "day"),
        ("fernsehturm", "fog", "dusk"),
        ("brandenburg_gate", "rain", "night"),
        ("wasteland", "radiation_storm", "day"),
    ]
    
    for loc_id, weather, time in locations:
        print(f"\n{Fore.YELLOW}Location: {loc_id.replace('_', ' ').title()}{Style.RESET_ALL}")
        if weather:
            print(f"{Fore.CYAN}Weather: {weather.replace('_', ' ').title()}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Time: {time.title()}{Style.RESET_ALL}\n")
        
        scene = renderer.render_location_scene(loc_id, weather, time)
        print(scene)
        
        time.sleep(2)
    
    pause()


def demo_combat_scenes():
    """Demo 3: Combat visualization"""
    print_section_header("DEMO 3: Dynamic Combat Scenes")
    
    renderer = SceneRenderer()
    
    print(f"{Fore.RED}COMBAT INITIATED!{Style.RESET_ALL}\n")
    time.sleep(1)
    
    # Show combat progression
    combat_sequence = [
        (100, 100, None, "Combat start"),
        (95, 85, "ranged_attack", "Player shoots"),
        (90, 70, "melee_attack", "Enemy attacks"),
        (90, 40, "critical_hit", "Player critical!"),
        (85, 0, "enemy_defeated", "Victory!"),
    ]
    
    for player_hp, enemy_hp, action, description in combat_sequence:
        print(f"{Fore.YELLOW}► {description}{Style.RESET_ALL}\n")
        scene = renderer.render_combat_scene(player_hp, "Raider", enemy_hp, action)
        print(scene)
        time.sleep(2)
    
    pause()


def demo_animations():
    """Demo 4: Animations"""
    print_section_header("DEMO 4: Animations")
    
    print(f"{Fore.YELLOW}1. Level Up Animation{Style.RESET_ALL}\n")
    level_up = Animation(AdvancedArtLibrary.ANIMATIONS["level_up"], loop=False)
    
    for frame in level_up.frames:
        print(f"\r{ArtComposer.center_text(frame.render(), 80)}", flush=True)
        time.sleep(frame.delay)
    
    print(ArtEffects.level_up_splash())
    time.sleep(2)
    
    print(f"\n{Fore.YELLOW}2. Explosion Sequence{Style.RESET_ALL}\n")
    explosion = ArtEffects.explosion_sequence()
    
    for frame in explosion.frames:
        print(ArtComposer.center_text(frame.render(), 80))
        time.sleep(frame.delay)
    
    time.sleep(1)
    
    print(f"\n{Fore.YELLOW}3. Radiation Pulse{Style.RESET_ALL}\n")
    rad_pulse = Animation(AdvancedArtLibrary.ANIMATIONS["radiation_pulse"], loop=False)
    
    for frame in rad_pulse.frames:
        print(ArtComposer.center_text(frame.render(), 80))
        time.sleep(frame.delay)
    
    pause()


def demo_weather_effects():
    """Demo 5: Weather effects"""
    print_section_header("DEMO 5: Weather & Atmospheric Effects")
    
    effects = [
        ("Rain", lambda: WeatherEffect.generate_rain(70, 8, 0.4)),
        ("Radiation Storm", lambda: WeatherEffect.generate_radiation_storm(70, 8)),
        ("Fog", lambda: WeatherEffect.generate_fog(70, 6)),
    ]
    
    for name, effect_func in effects:
        print(f"\n{Fore.CYAN}{name}:{Style.RESET_ALL}\n")
        print(effect_func())
        time.sleep(2)
    
    pause()


def demo_borders_and_formatting():
    """Demo 6: Border styles and formatting"""
    print_section_header("DEMO 6: Border Styles & Text Formatting")
    
    composer = ArtComposer()
    sample_text = "This is a sample\nmulti-line message\nwith different borders"
    
    styles = [
        ("Double Border", "double", Fore.CYAN),
        ("Single Border", "single", Fore.YELLOW),
        ("Heavy Border", "heavy", Fore.RED),
        ("ASCII Border", "ascii", Fore.GREEN),
    ]
    
    for name, style, color in styles:
        print(f"\n{Fore.WHITE}{name}:{Style.RESET_ALL}\n")
        print(composer.create_border(sample_text, style, color))
        time.sleep(1)
    
    pause()


def demo_interactive_elements():
    """Demo 7: Interactive elements"""
    print_section_header("DEMO 7: Interactive Elements")
    
    composer = ArtComposer()
    
    print(f"{Fore.YELLOW}Terminal:{Style.RESET_ALL}\n")
    print(composer.center_text(AdvancedArtLibrary.INTERACTIVE["terminal"], 80))
    time.sleep(2)
    
    print(f"\n{Fore.YELLOW}Locked Door:{Style.RESET_ALL}\n")
    print(composer.center_text(AdvancedArtLibrary.INTERACTIVE["locked_door"], 80))
    time.sleep(2)
    
    print(f"\n{Fore.YELLOW}Loot Container:{Style.RESET_ALL}\n")
    print(composer.center_text(AdvancedArtLibrary.INTERACTIVE["loot_container"], 80))
    time.sleep(2)
    
    pause()


def demo_status_bars():
    """Demo 8: Status and health bars"""
    print_section_header("DEMO 8: Status Bars & Visual Indicators")
    
    print(f"{Fore.WHITE}Health Bar Examples:{Style.RESET_ALL}\n")
    
    health_levels = [
        ("Full Health", 100),
        ("High Health", 75),
        ("Medium Health", 50),
        ("Low Health", 25),
        ("Critical Health", 10),
    ]
    
    for label, hp in health_levels:
        bar_length = 30
        filled = int(bar_length * (hp / 100))
        
        if hp > 60:
            color = Fore.GREEN
        elif hp > 30:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        
        bar = f"{color}{'█' * filled}{Fore.BLACK}{'█' * (bar_length - filled)}{Style.RESET_ALL}"
        
        print(f"{label}:")
        print(f"[{bar}] {hp}/100\n")
        time.sleep(0.5)
    
    pause()


def demo_event_notifications():
    """Demo 9: Event notifications"""
    print_section_header("DEMO 9: Event Notifications")
    
    print(f"{Fore.YELLOW}Quest Complete:{Style.RESET_ALL}\n")
    print(ArtEffects.quest_complete())
    print(f"{Fore.GREEN}First Steps - Return to Checkpoint Charlie{Style.RESET_ALL}\n")
    time.sleep(2)
    
    print(f"{Fore.YELLOW}Radiation Exposure:{Style.RESET_ALL}\n")
    print(ArtEffects.radiation_exposure())
    time.sleep(2)
    
    composer = ArtComposer()
    
    print(f"{Fore.YELLOW}New Quest:{Style.RESET_ALL}\n")
    quest_text = "NEW QUEST\n\nThe Lost Bunker\nFind the hidden bunker beneath\nthe Brandenburg Gate"
    print(composer.create_border(quest_text, "double", Fore.CYAN))
    time.sleep(2)
    
    pause()


def demo_atmospheric_elements():
    """Demo 10: Atmospheric elements"""
    print_section_header("DEMO 10: Atmospheric Elements")
    
    print(f"{Fore.WHITE}Dust Particles:{Style.RESET_ALL}")
    print(composer.center_text(AdvancedArtLibrary.ATMOSPHERE["dust_particles"], 80))
    print()
    time.sleep(1)
    
    print(f"{Fore.GREEN}Radiation Glow:{Style.RESET_ALL}")
    print(ArtComposer.center_text(AdvancedArtLibrary.ATMOSPHERE["radiation_glow"], 80))
    print()
    time.sleep(1)
    
    print(f"{Fore.YELLOW}Broken Lights:{Style.RESET_ALL}")
    print(ArtComposer.center_text(AdvancedArtLibrary.ATMOSPHERE["broken_lights"], 80))
    print()
    time.sleep(1)
    
    print(f"{Fore.WHITE}Smoke:{Style.RESET_ALL}")
    print(ArtComposer.center_text(AdvancedArtLibrary.ATMOSPHERE["smoke"], 80))
    print()
    time.sleep(1)
    
    print(f"{Fore.YELLOW}Sparks:{Style.RESET_ALL}")
    print(ArtComposer.center_text(AdvancedArtLibrary.ATMOSPHERE["sparks"], 80))
    print()
    
    pause()


def main_menu():
    """Show main demo menu"""
    composer = ArtComposer()
    
    menu_text = """
ENHANCED ASCII ART SYSTEM DEMO

Select a demo to view:

1.  Title Screen & Borders
2.  Location Scenes with Weather
3.  Dynamic Combat Scenes
4.  Animations
5.  Weather & Atmospheric Effects
6.  Border Styles & Formatting
7.  Interactive Elements
8.  Status Bars
9.  Event Notifications
10. Atmospheric Elements
11. Run All Demos
0.  Exit
    """
    
    print(composer.create_border(menu_text.strip(), "double", Fore.CYAN))
    
    return input(f"\n{Fore.YELLOW}Enter choice: {Style.RESET_ALL}").strip()


def run_demo():
    """Main demo runner"""
    clear_screen()
    
    from art import TITLE
    print(f"{Fore.GREEN}{TITLE}{Style.RESET_ALL}")
    print(ArtComposer.center_text("ENHANCED ASCII ART SYSTEM DEMO", 80))
    print(ArtComposer.center_text("=" * 40, 80))
    print()
    
    demos = {
        "1": ("Title Screen & Borders", demo_title_screen),
        "2": ("Location Scenes", demo_location_scenes),
        "3": ("Combat Scenes", demo_combat_scenes),
        "4": ("Animations", demo_animations),
        "5": ("Weather Effects", demo_weather_effects),
        "6": ("Borders & Formatting", demo_borders_and_formatting),
        "7": ("Interactive Elements", demo_interactive_elements),
        "8": ("Status Bars", demo_status_bars),
        "9": ("Event Notifications", demo_event_notifications),
        "10": ("Atmospheric Elements", demo_atmospheric_elements),
    }
    
    while True:
        choice = main_menu()
        
        if choice == "0":
            print(f"\n{Fore.GREEN}Thanks for viewing the demo!{Style.RESET_ALL}\n")
            break
        
        elif choice == "11":
            # Run all demos
            for name, demo_func in demos.values():
                clear_screen()
                demo_func()
        
        elif choice in demos:
            clear_screen()
            demos[choice][1]()
        
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
            time.sleep(1)


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Demo interrupted.{Style.RESET_ALL}\n")
        sys.exit(0)
