import json
import os
from typing import Optional, Tuple, List, Dict
from colorama import Fore, Style
from fallout_berlin.player import Player
from fallout_berlin.companion import Companion
from fallout_berlin.ui import UIManager

class CharacterCreator:
    """Handles the character creation process."""

    def __init__(self, ui_manager: UIManager):
        self.ui_manager = ui_manager

    def create_character(self) -> Tuple[Player, Optional[Companion]]:
        """
        Runs the interactive character creation process.
        Returns a tuple of (Player, Companion), where Companion can be None.
        """
        self.ui_manager.display_header("CHARACTER CREATION", style="double", color=Fore.CYAN)

        # Get name
        while True:
            try:
                name = input("What is your name? ").strip()
                if name:
                    break
                print("You must enter a name, Wanderer.")
            except EOFError:
                name = "Wanderer"
                break

        player = Player(name)
        player.perks = []

        # Initialize Survival Stats
        player.hunger = 0
        player.thirst = 0
        player.is_sneaking = False

        companion = None

        # Choose origin
        origins = list(Player.ORIGINS.keys())
        origin_options = []
        for origin_key in origins:
            origin_data = Player.ORIGINS[origin_key]
            origin_options.append(f"{origin_data['name']}\n      {origin_data['description']}")
            
        self.ui_manager.display_menu("CHOOSE YOUR ORIGIN", origin_options)

        while True:
            try:
                choice = input(
                    f"\nEnter your choice (1-{len(origins)}): "
                ).strip()
                if not choice:
                    continue
                choice_num = int(choice)
                if 1 <= choice_num <= len(origins):
                    origin_key = origins[choice_num - 1]
                    player.set_origin(origin_key)
                    origin_data = Player.ORIGINS[origin_key]
                    print(f"\nYou are a {origin_data['name']}.")

                    # Exclusive Companion for Vault Dweller: Pretinho
                    if origin_key == "vault_dweller":
                        companion = Companion("Pretinho", "A sleek black panther with glowing eyes.", 40, 6)
                        print(f"\n{Fore.GREEN}Pretinho the Black Panther joins you! (+2 CHA, +2 PER){Style.RESET_ALL}")
                        player.charisma += 2
                        player.perception += 2
                    break
                else:
                    print(f"Please enter a number between 1 and {len(origins)}.")
            except (ValueError, IndexError):
                print(
                    "Invalid input. Please enter the number corresponding to your choice."
                )
            except EOFError:
                player.set_origin(origins[0])
                break

        # S.P.E.C.I.A.L. point allocation
        self.ui_manager.display_header("S.P.E.C.I.A.L. STATS", style="single", color=Fore.YELLOW)
        print("You have 10 points to distribute among your S.P.E.C.I.A.L. stats.")
        print("Each stat starts at 5. You can increase any stat up to 10.")

        points_remaining = 10
        stats = [
            "strength",
            "perception",
            "endurance",
            "charisma",
            "intelligence",
            "agility",
            "luck",
        ]

        while points_remaining > 0:
            print(f"\nPoints remaining: {points_remaining}")
            
            stat_options = []
            for stat in stats:
                value = getattr(player, stat)
                stat_options.append(f"{stat.capitalize()}: {value}")
            
            self.ui_manager.display_menu("CURRENT STATS", stat_options)

            try:
                stat_input = (
                    input("\nWhich stat would you like to increase? (Name or Number): ")
                    .strip()
                    .lower()
                )
                if not stat_input:
                    continue

                matched_stat = None
                if stat_input.isdigit():
                    idx = int(stat_input) - 1
                    if 0 <= idx < len(stats):
                        matched_stat = stats[idx]
                else:
                    for s in stats:
                        if s.startswith(stat_input):
                            matched_stat = s
                            break

                if matched_stat:
                    current_value = getattr(player, matched_stat)
                    if current_value >= 10:
                        print(
                            f"{matched_stat.capitalize()} is already at maximum (10)."
                        )
                    else:
                        player.set_special(matched_stat, current_value + 1)
                        points_remaining -= 1
                        print(f"[+] {matched_stat.capitalize()} increased.")
                else:
                    print(
                        "Invalid stat. Type the name (e.g., 'Strength') or the number."
                    )
            except EOFError:
                break

        print("\n" + player.get_stat_summary())
        
        # Perk Selection
        self._select_starting_perks(player)

        try:
            input("\nCharacter creation complete. Press Enter to begin your journey...")
        except EOFError:
            pass
            
        return player, companion

    def _select_starting_perks(self, player: Player):
        """Allow the player to select 3 starting perks based on their S.P.E.C.I.A.L."""
        self.ui_manager.display_header("STARTING PERKS", style="double", color=Fore.MAGENTA)
        print("You can choose 3 starting perks to define your character.")
        
        perks_db = self._load_perks()
        chosen_perks = []
        
        while len(chosen_perks) < 3:
            eligible_perks = self._get_eligible_perks(player, perks_db, chosen_perks)
            
            if not eligible_perks:
                print(f"{Fore.YELLOW}No more eligible perks found for your stats.{Style.RESET_ALL}")
                break
                
            perk_options = [f"{p.get('name', 'Unknown')} ({p.get('req_text', 'None')})\n      {p.get('desc', 'No description')}" for p in eligible_perks]
            
            self.ui_manager.display_menu(f"CHOOSE STARTING PERK {len(chosen_perks) + 1}/3", perk_options)
            
            try:
                choice = input(f"\nEnter your choice (1-{len(eligible_perks)}): ").strip()
                if not choice:
                    continue
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(eligible_perks):
                    selected_perk = eligible_perks[choice_num - 1]
                    player.perks.append(selected_perk)
                    chosen_perks.append(selected_perk["name"])
                    print(f"\n{Fore.GREEN}[+] Perk Added: {selected_perk['name']}{Style.RESET_ALL}")
                    # Trigger stat recalculation if necessary
                    player._recalculate_stats()
                else:
                    print(f"Please enter a number between 1 and {len(eligible_perks)}.")
            except (ValueError, IndexError):
                print("Invalid input. Please enter a valid number.")
            except EOFError:
                break

    def _load_perks(self) -> List[Dict]:
        """Load perks from perks.json"""
        perks_path = os.path.join(
            os.path.dirname(__file__), "data", "perks.json"
        )
        try:
            with open(perks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    if "perks" in data and isinstance(data["perks"], list):
                        return data["perks"]
                    return list(data.values())
                return []
        except Exception as e:
            print(f"Error loading perks: {e}")
            return []

    def _get_eligible_perks(self, player: Player, perks_db: List[Dict], chosen_perks: List[str]) -> List[Dict]:
        """Filter perks that the player meets requirements for and hasn't chosen yet"""
        eligible = []
        for perk in perks_db:
            if perk["name"] in chosen_perks:
                continue
                
            meets_reqs = True
            for req in perk.get("req", []):
                stat_val = getattr(player, req["stat"], 0)
                target_val = req["value"]
                op = req["op"]
                
                if op == ">=" and not (stat_val >= target_val):
                    meets_reqs = False
                    break
                elif op == ">" and not (stat_val > target_val):
                    meets_reqs = False
                    break
                elif op == "==" and not (stat_val == target_val):
                    meets_reqs = False
                    break
                    
            if meets_reqs:
                eligible.append(perk)
        return eligible
