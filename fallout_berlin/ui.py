"""
UI/Display System
Handles all terminal UI rendering and display formatting for the game.
"""

import os
import random
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any, TYPE_CHECKING
from colorama import Fore, Style, Back
from fallout_berlin.enhanced_art_system import ArtComposer, BureaucracyRenderer, LightingManager, WeatherEffect
from fallout_berlin.art_master import SceneRenderer
from fallout_berlin.art_berlin import BERLIN_ART

if TYPE_CHECKING:
    from fallout_berlin.game_state import GameState
    from fallout_berlin.location import Location


class SettingsManager:
    """Manages game settings and accessibility options"""
    
    DEFAULT_SETTINGS = {
        "ui": {
            "scanlines": True,
            "flicker": True,
            "glitch_effects": True,
            "radiation_glow": True,
            "theme": "green",
            "compact_hud": True,
            "interface_width": 80
        },
        "accessibility": {
            "disable_animations": False,
            "disable_text_distortion": False
        },
        "retro_terminal": {
            "enabled": False,
            "color": "green",
            "scanlines": True,
            "simplified_graphics": True
        }
    }

    def __init__(self):
        self.settings_path = Path("fallout_berlin/data/settings.json")
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()

    def save_settings(self):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def get(self, category: str, key: str, default: Any = None) -> Any:
        return self.settings.get(category, {}).get(key, default)

    def set(self, category: str, key: str, value: Any):
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
        self.save_settings()


class PipBoyRenderer:
    """Specialized renderer for Pip-Boy styled UI elements"""

    THEMES = {
        "green": (Fore.GREEN, Fore.LIGHTGREEN_EX),
        "amber": (Fore.YELLOW, Fore.LIGHTYELLOW_EX),
        "blue": (Fore.CYAN, Fore.LIGHTCYAN_EX),
        "white": (Fore.WHITE, Fore.LIGHTWHITE_EX),
    }

    @staticmethod
    def apply_theme(text: str, theme: str = "green", scanlines: bool = True, flicker_rate: float = 0.02, radiation_glow: bool = False, settings: Optional[SettingsManager] = None) -> str:
        # Simplified to just apply the core color theme, as effects are now more direct.
        if settings:
            theme = settings.get("ui", "theme", theme)
            if settings.get("retro_terminal", "enabled", False):
                scanlines = settings.get("retro_terminal", "scanlines", True)
            else:
                scanlines = settings.get("ui", "scanlines", True)

        colors = PipBoyRenderer.THEMES.get(theme.lower(), PipBoyRenderer.THEMES["green"])
        primary, _ = colors # Only need primary color
        
        if scanlines:
            lines = text.split('\n')
            for i in range(1, len(lines), 2):
                lines[i] = f"{Back.BLACK}{Style.DIM}{lines[i]}{Style.RESET_ALL}"
            text = '\n'.join(lines)

        # Apply primary color and reset at the end.
        return f"{primary}{text}{Style.RESET_ALL}"


class UIManager:
    """Manages all UI display and rendering"""

    BORDER_WIDTH = 80

    @property
    def C_ENEMY(self):
        return self._get_color(Fore.RED)

    @property
    def C_DAMAGE(self):
        return self._get_color(Fore.RED)

    @property
    def C_RADS(self):
        return self._get_color(Fore.LIGHTGREEN_EX)
    @property
    def C_HEAL(self):
        return self._get_color(Fore.GREEN)

    @property
    def C_SUCCESS(self):
        return self._get_color(Fore.GREEN)

    @property
    def C_FRIENDLY(self):
        return self._get_color(Fore.CYAN)

    @property
    def C_QUEST(self):
        return self._get_color(Fore.YELLOW)

    @property
    def C_LOOT(self):
        return self._get_color(Fore.LIGHTYELLOW_EX)

    @property
    def C_DIALOGUE(self):
        return self._get_color(Fore.CYAN)

    C_RESET = Style.RESET_ALL

    @property
    def C_PIP_BOY(self):
        return self._get_color(Fore.GREEN)

    @property
    def C_HEADER(self):
        return self._get_color(Style.BRIGHT + Fore.GREEN)

    def __init__(self, game_state):
        self.state = game_state
        self.settings = SettingsManager()
        self.BORDER_WIDTH = self.settings.get("ui", "interface_width", 80)
        # Use SceneRenderer from art_master as preferred by the redesign
        self.renderer = SceneRenderer(width=self.BORDER_WIDTH)
        self.composer = ArtComposer()

    @staticmethod
    def get_npc_name(npc_id: str) -> str:
        return npc_id.replace("_", " ").title()

    def _get_color(self, color: str) -> str:
        """Return color based on retro mode settings"""
        if self.settings.get("retro_terminal", "enabled", False):
            retro_color_name = self.settings.get("retro_terminal", "color", "green")
            retro_color, _ = PipBoyRenderer.THEMES.get(retro_color_name.lower(), PipBoyRenderer.THEMES["green"])
            return retro_color
        return color

    def clear_screen(self) -> None:
        """Clear the terminal screen"""
        os.system("cls" if os.name == "nt" else "clear")

    def display_location(self, location, weather=None, time_of_day="day", first_visit=False, force_art=False):
        self.clear_screen()

        if first_visit or force_art:
            scene = self.renderer.render_location(
                location.location_id, weather=weather, time_of_day=time_of_day, show_pip_boy=True
            )
            print(scene)

        self.display_header(location.name.upper(), style="double")

        # Display description within a box
        print(f"| {self.C_PIP_BOY}{location.description.ljust(self.BORDER_WIDTH - 4)}{self.C_RESET} |")
        
        tags = self._get_location_tags(location)
        if tags:
            print(f"| {' '.join(tags).ljust(self.BORDER_WIDTH - 4)} |")
        
        print(f"+{'=' * (self.BORDER_WIDTH - 2)}+")

        # Exits, items, hostiles, NPCs in a structured layout
        self._display_location_details(location)

        self._print_player_hud()

    def display_ascii_location(self, location):
        """Displays a simplified ASCII art view of the location."""
        self.clear_screen()
        self.display_header(location.name.upper(), style="double")

        if location.ascii_map:
            # Apply theme to the ascii map
            themed_map = PipBoyRenderer.apply_theme(location.ascii_map, settings=self.settings)
            print(themed_map)
        else:
            self.draw_mini_map(location)

        print(f"| {self.C_PIP_BOY}{location.description.ljust(self.BORDER_WIDTH - 4)}{self.C_RESET} |")
        
        tags = self._get_location_tags(location)
        if tags:
            print(f"| {' '.join(tags).ljust(self.BORDER_WIDTH - 4)} |")
        
        print(f"+{'=' * (self.BORDER_WIDTH - 2)}+")

        self._display_location_details(location)
        self._print_player_hud()

    def _display_location_details(self, location):
        """Helper to display structured location info."""
        details = []
        if location.connections:
            exits = ", ".join([e.capitalize() for e in location.connections.keys()])
            details.append(f"Exits: {exits}")
        if location.items:
            items_str = ", ".join([i.name for i in location.items])
            details.append(f"Items: {self.C_LOOT}{items_str}{self.C_RESET}")
        if location.enemies:
            enemies_str = ", ".join([e.name for e in location.enemies])
            details.append(f"Hostiles: {self.C_ENEMY}{enemies_str}{self.C_RESET}")
        if location.npcs:
            npcs_str = ", ".join([str(npc) for npc in location.npcs])
            details.append(f"NPCs: {self.C_FRIENDLY}{npcs_str}{self.C_RESET}")
        
        for detail in details:
            print(f"| {detail.ljust(self.BORDER_WIDTH - 4)}")
        
        if details:
             print(f"+{'=' * (self.BORDER_WIDTH - 2)}+")


    def _print_border(
        self, title: str, border_color: str, text_color: str, reset: str
    ) -> None:
        """Print a decorative border with title"""
        # Delegating to display_header for consistency
        self.display_header(title, color=border_color, style="single")

    def _get_location_tags(self, location: "Location") -> List[str]:
        """Generate location property tags

        Args:
            location: The location to get tags for

        Returns:
            List of tag strings
        """
        tags = []

        if location.get_property("radiation_level", 0) > 0:
            tags.append(f"{self.C_RADS}[RADIOACTIVE]{self.C_RESET}")
        if location.get_property("hostile", False):
            tags.append(f"{self.C_ENEMY}[DANGER]{self.C_RESET}")
        if not location.get_property("safe", True):
            tags.append(f"{self.C_ENEMY}[UNSAFE]{self.C_RESET}")

        return tags

    def _print_player_hud(self):
        """Redesigned ASCII HUD"""
        if not self.state.player:
            return
        player = self.state.player
        
        hp_bar = self._get_progress_bar(player.hit_points, player.max_hit_points, length=20, bar_type="health")
        rad_bar = self._get_progress_bar(player.radiation, 1000, length=10, bar_type="radiation")
        
        caps = self.state.inventory.caps if hasattr(self.state.inventory, 'caps') else 0
        
        # ASCII icons for status
        status_icon = f"{self.C_PIP_BOY}☺{self.C_RESET}"  # Smiley for normal
        hp_pct = player.hit_points / player.max_hit_points if player.max_hit_points > 0 else 0
        if hp_pct < 0.25 or player.radiation > 600:
            status_icon = f"{self.C_ENEMY}☠{self.C_RESET}"  # Skull for danger
        elif player.get_property("stealth_mode", False):
            status_icon = f"{self.C_FRIENDLY}[ SNEAK ]{self.C_RESET}"

        # ASCII Border
        print(f"{self.C_PIP_BOY}+{'=' * (self.BORDER_WIDTH - 2)}+{self.C_RESET}")
        
        # HUD Content
        hud_line_1 = f" HP: [{hp_bar}] {player.hit_points}/{player.max_hit_points}"
        hud_line_2 = f" RADS: [{rad_bar}] {player.radiation}"
        hud_line_3 = f" CAPS: {caps} {BERLIN_ART.get('caps', '©')}"
        
        # Combine and pad
        info_panel = f"{hud_line_1:<40} | {hud_line_2:<25} | {hud_line_3:<15}"
        
        print(f"{self.C_PIP_BOY}| {status_icon} {info_panel.ljust(self.BORDER_WIDTH - 6)} |{self.C_RESET}")
        
        # Bottom border
        print(f"{self.C_PIP_BOY}+{'=' * (self.BORDER_WIDTH - 2)}+{self.C_RESET}")

    def display_detailed_stats(self):
        """Moved detailed HUD stats here"""
        if not self.state.player:
            return
        player = self.state.player

        self.display_header("STATISTICS", style="single")

        print(f" Level: {player.level} | XP: {self._get_progress_bar(player.experience, player.experience_to_next, 20)}")
        
        wep = player.equipped_weapon.name if player.equipped_weapon else "None"
        arm = player.equipped_armor.name if player.equipped_armor else "None"
        print(f" Weapon: {wep} | Armor: {arm}")
        
        effects = getattr(player, 'active_effects', [])
        if effects:
            active_effects = ', '.join([f"[{e}]" for e in effects])
            print(f" Active Effects: {self.C_QUEST}{active_effects}{self.C_RESET}")
        
        iron_rep = self.state.get_faction_reputation("Iron Ring")
        print(f" Iron Ring Rep: {self.C_FRIENDLY}{iron_rep}{self.C_RESET}")

    def _get_progress_bar(
        self, current: int, total: int, length: int = 20, bar_type: str = "default"
    ) -> str:
        """
        Generate an ASCII progress bar using block characters.
        Style options: 'default', 'health', 'radiation', 'ap'.
        """
        if total <= 0:
            return f"[{Fore.BLACK}{'█' * length}{Style.RESET_ALL}] {current}/{total}" # Show 0/0 for total 0

        color = Fore.WHITE # Default
        if bar_type == "health":
            pct = current / total
            if pct > 0.6:
                color = Fore.GREEN
            elif pct > 0.3:
                color = Fore.YELLOW
            else:
                color = Fore.RED
        elif bar_type == "radiation":
            color = Fore.LIGHTGREEN_EX
        elif bar_type == "ap":
            color = Fore.BLUE

        filled_len = int((current / total) * length)
        
        return f"{color}{'█' * filled_len}{Fore.BLACK}{'█' * (length - filled_len)}{Style.RESET_ALL}"


    def show_inventory(self) -> None:
        """Display the player inventory"""
        if self.state.inventory:
            print(self.state.inventory.display())
        else:
            print("Inventory is empty.")

    def show_stats(self) -> None:
        """Display detailed player stats"""
        if self.state.player:
            print(self.state.player.get_stat_summary())
            
            perks = getattr(self.state.player, "perks", [])
            perk_str = ", ".join(perks) if perks else "None"
            print(f"\nPerks: {Fore.YELLOW}{perk_str}{Style.RESET_ALL}")

            print(f"\nFaction Reputation:")
            for faction, rep in self.state.faction_reputation.items():
                standing = self.state.get_faction_standing(faction)
                print(f"  {faction}: {standing} ({rep})")
        else:
            print("No character loaded.")

    def show_quests(self, quest_display: str) -> None:
        """Display the quest log

        Args:
            quest_display: Formatted quest log string
        """
        print(quest_display)

    def show_help(self, context="exploration"):
        self.display_header(f"HELP: {context.upper()}", style="single")
        
        command_groups = {
            "combat": [
                ("attack (a)", "Attack with equipped weapon"),
                ("vats (v)", "Enter V.A.T.S. targeting mode"),
                ("heal (h)", "Use a Stimpak"),
                ("take cover (c)", "Take cover from attacks"),
                ("flee (f)", "Attempt to escape"),
            ],
            "dialogue": [
                ("1-9", "Select dialogue option"),
                ("look", "Examine the speaker"),
                ("quit/bye", "End conversation (if allowed)"),
            ],
            "trading": [
                ("buy [item]", "Buy an item"),
                ("buy [item] [quantity]", "Buy multiple stackable items"),
                ("sell [item] [quantity]", "Sell loot for caps"),
                ("list", "List goods"),
                ("close", "Leave shop"),
            ],
            "exploration": [
                ("go [dir]", "Move (north, south, east, west, up, down)"),
                ("attack [enemy]", "Engage an enemy in this location"),
                ("i", "Open inventory"),
                ("q", "Open quest log"),
                ("look [obj]", "Examine surroundings or items"),
                ("take [item]", "Pick up an item"),
                ("talk [npc]", "Talk to a character"),
                ("sneak", "Toggle stealth mode"),
            ],
            "management": [
                ("inventory (i)", "Manage items"),
                ("stats", "View character sheet"),
                ("quests (q)", "View quest log"),
                ("craft", "Open crafting menu"),
                ("camp", "Rest and recover"),
                ("radio", "Toggle radio"),
                ("companion", "Manage companion"),
                ("settings", "Change UI and accessibility options"),
            ],
            "system": [
                ("save / load", "Save or load game"),
                ("help", "Show this message"),
                ("quit", "Exit game"),
            ]
        }
        
        def print_commands(title, commands, color):
            print(f"\n{color}--- {title} ---{self.C_RESET}")
            for cmd, desc in commands:
                print(f"  {cmd:<15} - {desc}")

        if context == "combat":
            print_commands("Combat Commands", command_groups["combat"], self.C_ENEMY)
        elif context == "dialogue":
            print_commands("Dialogue Commands", command_groups["dialogue"], self.C_DIALOGUE)
        elif context == "trading":
            print_commands("Trading Commands", command_groups["trading"], self.C_LOOT)
        else: # exploration
            print_commands("Exploration", command_groups["exploration"], self.C_SUCCESS)
            print_commands("Management", command_groups["management"], self.C_QUEST)
            print_commands("System", command_groups["system"], Fore.WHITE)

        print(f"\n{self.C_PIP_BOY}Tip: Bureaucracy checks at restricted zones. Bring forms!{self.C_RESET}")

    def display_dialogue_node(
        self, npc_name: str, node_text: str, options: List[tuple]
    ) -> None:
        """Display a dialogue node with speaker and options"""
        
        # Simple ASCII border for dialogue
        self.display_header(f"DIALOGUE WITH: {npc_name.upper()}", style="single")
        
        # Word wrap for dialogue text
        wrapped_text = self.renderer._word_wrap(node_text, self.BORDER_WIDTH - 4)
        for line in wrapped_text.split('\n'):
            print(f"| {self.C_DIALOGUE}{line.ljust(self.BORDER_WIDTH - 4)}{self.C_RESET} |")
            
        print(f"+{'=' * (self.BORDER_WIDTH - 2)}+")

        if options:
            for i, text in options:
                print(f" > {self.C_QUEST}[{i}]{self.C_RESET} {text}")
        else:
            print(" (Press ENTER to continue)")

    def draw_mini_map(self, location):
        if location.ascii_map:
            print(location.ascii_map)
        else:
            # ASCII-art mini map
            n = "↑" if "north" in location.connections else " "
            s = "↓" if "south" in location.connections else " "
            e = "→" if "east" in location.connections else " "
            w = "←" if "west" in location.connections else " "
            
            print("   +---+")
            print(f"   | {n} |")
            print(f"   |{w} @ {e}|") # @ = player
            print(f"   | {s} |")
            print("   +---+")


    def show_combat_status(
        self,
        player_name: str,
        player_hp: int,
        player_max_hp: int,
        player_ap: int,
        player_max_ap: int,
        player_effects: List[str],
        enemy_name: str,
        enemy_hp: int,
        enemy_max_hp: int,
        enemy_effects: List[str],
        enemy_has_cover: bool,
        action_feedback: Optional[str] = None,
        available_actions: Optional[List[Tuple[str, str]]] = None # (action_key, display_text)
    ) -> None:
        """Display ASCII combat status screen. AP functionality is deprecated and hidden."""
        
        # Delegate full scene rendering to SceneRenderer in art_master
        # Passing 0 for AP to effectively hide/deprecate it in the renderer
        combat_scene = self.renderer.render_combat(
            player_name=player_name,
            player_hp=player_hp,
            player_max_hp=player_max_hp,
            player_ap=0, 
            player_max_ap=0,
            player_effects=player_effects,
            enemy_name=enemy_name,
            enemy_hp=enemy_hp,
            enemy_max_hp=enemy_max_hp,
            enemy_effects=enemy_effects,
            enemy_has_cover=enemy_has_cover,
            action_feedback=action_feedback
        )
        print(combat_scene)

        # Display available actions below the scene
        print(f"\n{self.C_PIP_BOY}+{'=' * (self.BORDER_WIDTH - 2)}+{self.C_RESET}")
        print(f" {self.C_HEADER}ACTIONS:{self.C_RESET}")
        if available_actions:
            for i, (action_key, display_text) in enumerate(available_actions, 1):
                print(f"   [{self.C_QUEST}{action_key[0].upper()}{self.C_RESET}] {display_text}")
        else:
            print(f"   {self.C_PIP_BOY}No actions available.{self.C_RESET}")
        print(f"{self.C_PIP_BOY}+{'=' * (self.BORDER_WIDTH - 2)}+{self.C_RESET}")


    # Consolidated display_header
    def display_header(self, text: str, style: str = "double", color: str = None, stamp: bool = False):
        if color is None:
            color = self.C_PIP_BOY
        border_char = "=" if style == "double" else "-"
        corner = "*" if style == "double" else "+"
        
        title = f" {text.upper()} "
        
        print(f"{color}{corner}{title.center(self.BORDER_WIDTH - 2, border_char)}{corner}{self.C_RESET}")

    # Consolidated display_menu (flexible)
    def display_menu(self, title: str, options: List[str], prompt: str = " > ", numbered: bool = True, allow_cancel: bool = True):
        self.display_header(title, color=Fore.CYAN, style="single")
        
        for i, opt in enumerate(options, 1):
            if numbered:
                print(f"  {self.C_QUEST}[{i}]{self.C_RESET} {opt}")
            else:
                print(f"  {self.C_PIP_BOY}* {opt}{self.C_RESET}")

        if allow_cancel:
            print(f"  {self.C_ENEMY}[C] Cancel{self.C_RESET}")
        
        print(f"\n{prompt}", end="")

    def draw_main_menu(self, title: str, options: List[str], blink_state: bool, prompt: str = " > "):
        self.display_header(title, color=Fore.CYAN, style="single")
        
        for i, opt in enumerate(options, 1):
            if blink_state:
                print(f"  {self.C_QUEST}[{i}]{self.C_RESET} {opt}")
            else:
                # Render empty space to create the "off" blink state
                print(f"  {' ' * (len(str(i)) + 3 + len(opt))}")
        print(f"\n{prompt}", end="")

    # Consolidated radio & terminal
    def display_radio_message(self, message: str):
        self.display_header(f"PIP-BOY RADIO {BERLIN_ART.get('radio', '📻')}", style="single")
        wrapped = self.renderer._word_wrap(message, self.BORDER_WIDTH - 6)
        
        for line in wrapped.split('\n'):
            print(f"| {self.C_PIP_BOY}{line.ljust(self.BORDER_WIDTH - 4)}{self.C_RESET} |")
        
        print(f"+{'~' * (self.BORDER_WIDTH - 2)}+")

    def display_terminal(self, content: str, title: str = "ROBCO INDUSTRIES (TM) TERMLINK"):
        """Displays content in a retro terminal style using BureaucracyRenderer"""
        self.clear_screen()
        
        # Use terminal art if available
        from fallout_berlin.art_master import AdvancedArtLibrary, BureaucracyRenderer
        terminal_art = AdvancedArtLibrary.INTERACTIVE.get("terminal", "")
        if terminal_art:
            print(PipBoyRenderer.apply_theme(terminal_art, settings=self.settings))

        self.display_header(title, style="double", color=self.C_PIP_BOY)
        
        # Apply glitch effect occasionally if enabled
        if self.settings.get("ui", "glitch_effects", True) and random.random() < 0.3:
            content = BureaucracyRenderer.apply_glitch_effect(content, intensity=0.02)
            
        # Apply theme to the whole content block
        themed_content = PipBoyRenderer.apply_theme(content, settings=self.settings)
        print(themed_content)
        print(f"{self.C_PIP_BOY}+{'=' * (self.BORDER_WIDTH - 2)}+{self.C_RESET}")

    def display_document(self, content: str, fields: Optional[Dict[str, str]] = None):
        """Displays a bureaucratic document using BureaucracyRenderer"""
        from fallout_berlin.art_master import BureaucracyRenderer
        form = BureaucracyRenderer.render_form(content, fields)
        print(form)

    # New: Status effects + loading
    def display_status_effects(self):
        effects = getattr(self.state.player, 'active_effects', [])
        if effects:
            effect_str = ', '.join([f"[{e}]" for e in effects])
            print(f"{self.C_QUEST}STATUS: {effect_str}{self.C_RESET}")

    def show_loading(self, message: str = "Processing..."):
        # Simple ASCII loading indicator
        print(f"{self.C_PIP_BOY}[»] {message}{self.C_RESET}")


    def show_settings_menu(self):
        """Interactive settings menu with ASCII design"""
        while True:
            self.clear_screen()
            self.display_header("SYSTEM SETTINGS", color=Fore.YELLOW, style="double")
            
            ui = self.settings.settings["ui"]
            acc = self.settings.settings["accessibility"]
            
            def get_status(enabled):
                return f"[{self.C_SUCCESS}ON{self.C_RESET}]" if enabled else f"[{self.C_ENEMY}OFF{self.C_RESET}]"

            options = [
                f"Scanlines......... {get_status(ui['scanlines'])}",
                f"Flicker........... {get_status(ui['flicker'])}",
                f"Glitch Effects.... {get_status(ui['glitch_effects'])}",
                f"Radiation Glow.... {get_status(ui['radiation_glow'])}",
                f"UI Theme.......... [{self.C_QUEST}{ui['theme'].upper()}{self.C_RESET}]",
                f"Interface Width... [{self.C_QUEST}{ui.get('interface_width', 80)}{self.C_RESET}]",
                f"Text Distortion... {get_status(not acc['disable_text_distortion'])}",
                f"Animations........ {get_status(not acc['disable_animations'])}",
                f"Retro Terminal.... {get_status(self.settings.get('retro_terminal', 'enabled', False))}",
                f"Simplified Graphics.. {get_status(self.settings.get('retro_terminal', 'simplified_graphics', True))}",
            ]

            self.display_menu("OPTIONS", options, allow_cancel=True)
            choice = input("\nChoice (1-10, C to Close): ").strip().upper()

            if choice == 'C':
                break

            if choice == '1':
                self.settings.set("ui", "scanlines", not ui["scanlines"])
            elif choice == '2':
                self.settings.set("ui", "flicker", not ui["flicker"])
            elif choice == '3':
                self.settings.set("ui", "glitch_effects", not ui["glitch_effects"])
            elif choice == '4':
                self.settings.set("ui", "radiation_glow", not ui["radiation_glow"])
            elif choice == '5':
                themes = list(PipBoyRenderer.THEMES.keys())
                current_idx = themes.index(ui["theme"])
                next_theme = themes[(current_idx + 1) % len(themes)]
                self.settings.set("ui", "theme", next_theme)
            elif choice == '6':
                widths = [80, 100, 120]
                current = ui.get("interface_width", 80)
                try:
                    current_idx = widths.index(current)
                except ValueError:
                    current_idx = 0
                next_width = widths[(current_idx + 1) % len(widths)]
                self.settings.set("ui", "interface_width", next_width)
                self.BORDER_WIDTH = next_width
                self.renderer.width = next_width
            elif choice == '7':
                self.settings.set("accessibility", "disable_text_distortion", not acc["disable_text_distortion"])
            elif choice == '8':
                self.settings.set("accessibility", "disable_animations", not acc["disable_animations"])
            elif choice == '9':
                self.settings.set("retro_terminal", "enabled", not self.settings.get("retro_terminal", "enabled", False))
            elif choice == '10':
                self.settings.set("retro_terminal", "simplified_graphics", not self.settings.get("retro_terminal", "simplified_graphics", True))
