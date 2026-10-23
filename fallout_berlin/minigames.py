import random
from typing import List, Optional
from colorama import Fore, Style
from fallout_berlin.player import Player
from fallout_berlin.ui import UIManager

class BureaucracyMinigame:
    """
    "Anmeldung" Minigame (Bureaucracy Battles).
    A puzzle minigame where players must present the correct combination of forms/stamps.
    """
    def __init__(self, ui_manager: UIManager):
        self.ui_manager = ui_manager

    def play_check(self, location_id: str, location_name: str, player: Player, inventory) -> bool:
        """
        Handle a bureaucracy check where the player must present the correct documents.
        Returns True if access is granted, False otherwise.
        """
        # Intelligence and Charisma help with bureaucracy
        # High stats can provide "clues" or bypass minor errors
        stat_bonus = (player.intelligence + player.charisma) / 2.0

        requirements = {
            "reichstag": ["Permit A-38", "Pre-War Passport"],
            "charlottenburg_palace": ["Royal Visitation Form 7B-Slash-9"],
            "buergeramt": ["Anmeldung Form 27-B", "Passierschein A39"],
        }
        
        if location_id not in requirements:
            # No specific check needed for other locations here
            return True
            
        required_docs = requirements[location_id]
        
        self.ui_manager.display_header(f"SECURITY CHECKPOINT: {location_name.upper()}", style="double", color=Fore.RED)
        
        print(f"\n{Fore.YELLOW}OFFICIAL:{Style.RESET_ALL} \"Halt! To enter {location_name}, you must present: {', '.join(required_docs)}.\"")
        
        # Collect potential documents from inventory
        # Assuming documents are 'misc' items
        documents = [item for item in inventory.items if item.item_type == 'misc']
        
        if not documents:
            print(f"\n{Fore.YELLOW}OFFICIAL:{Style.RESET_ALL} \"You have no papers? Unbelievable! Get out!\"")
            return False
            
        print("\nSelect documents to present (enter numbers separated by spaces, e.g., '1 3'):")
        for i, doc in enumerate(documents):
            print(f"  {i+1}. {doc.name}")
            
        try:
            selection = input(f"\n{Fore.GREEN}>{Style.RESET_ALL} ").strip()
        except EOFError:
            return False
            
        if not selection:
            print(f"\n{Fore.YELLOW}OFFICIAL:{Style.RESET_ALL} \"Silence is not a form! Next!\"")
            return False
            
        try:
            indices = [int(x) - 1 for x in selection.split()]
            presented_docs = []
            for idx in indices:
                if 0 <= idx < len(documents):
                    presented_docs.append(documents[idx])
        except ValueError:
            print(f"\n{Fore.YELLOW}OFFICIAL:{Style.RESET_ALL} \"This application is illegible!\"")
            return False
            
        presented_names = [d.name for d in presented_docs]
        print(f"\nYou present: {', '.join(presented_names)}")
        
        # Verification Logic
        missing = [req for req in required_docs if req not in presented_names]
        extras = [doc for doc in presented_names if doc not in required_docs]
        
        if not missing and not extras:
            print(f"\n{Fore.YELLOW}OFFICIAL:{Style.RESET_ALL} \"Hmph. Everything seems to be in order. You may proceed.\"")
            return True
        elif missing:
            # High Charisma/Intelligence might allow talking your way through minor missing docs
            if len(missing) == 1 and stat_bonus >= 8:
                print(f"\n{Fore.CYAN}[PERSUASION/LOGIC] You explain that {missing[0]} was lost in a recent rad-storm, but your other papers are impeccable.{Style.RESET_ALL}")
                print(f"\n{Fore.YELLOW}OFFICIAL:{Style.RESET_ALL} \"...I suppose mistakes happen. Just this once. Move along!\"")
                return True
            print(f"\n{Fore.YELLOW}OFFICIAL:{Style.RESET_ALL} \"Incomplete application! You are missing: {', '.join(missing)}. Denied!\"")
        else: # extras
            # High Intelligence helps realize you should only present what was asked
            if stat_bonus >= 7:
                 print(f"\n{Fore.CYAN}[INTELLECT] You realize the official is getting annoyed by the extra clutter and quickly withdraw it.{Style.RESET_ALL}")
                 print(f"\n{Fore.YELLOW}OFFICIAL:{Style.RESET_ALL} \"...Better. Yes, these are the correct papers. Proceed.\"")
                 return True
            print(f"\n{Fore.YELLOW}OFFICIAL:{Style.RESET_ALL} \"What is this extra garbage? I only asked for the specific papers. Are you trying to bribe me with trash? Denied!\"")
             
        return False

class MiniGameManager:
    """Manages mini-games like Hacking and Form Filling."""

    def __init__(self, ui_manager: UIManager):
        self.ui_manager = ui_manager
        self.bureaucracy = BureaucracyMinigame(ui_manager)

    def handle_hack(self, args: List[str], player: Player, current_location: str):
        """Attempt to hack a terminal"""
        if not args:
            print("Hack what?")
            return

        target = " ".join(args).lower()
        if "terminal" not in target:
            print("You can't hack that.")
            return

        # Check for perk
        if "Hacker" not in getattr(player, "perks", []):
            print(f"{Fore.RED}[FAILURE] Security protocols are too advanced. Requires 'Hacker' perk.{Style.RESET_ALL}")
            return

        # Check location (Simulated availability)
        allowed_locations = ["checkpoint_charlie", "fernsehturm", "reichstag", "u_bahn_tunnel", "kotti"]
        if current_location not in allowed_locations:
            print("You don't see any active terminals here.")
            return

        self.ui_manager.display_terminal("CONNECTING TO ROBCO INDUSTRIES TERMLINK...")
        
        if self._play_hacking_minigame():
            print(f"\n{Fore.GREEN}[ACCESS GRANTED]{Style.RESET_ALL}")
            print("You download encrypted data.")
            xp = 50
            print(f"{Fore.GREEN}[+] Gained {xp} XP{Style.RESET_ALL}")
            player.add_experience(xp)
        else:
            print(f"\n{Fore.RED}[ACCESS DENIED] Terminal locked out.{Style.RESET_ALL}")

    def _play_hacking_minigame(self) -> bool:
        """Execute terminal hacking mini-game"""
        words = [
            "BERLIN", "BUNKER", "WEAPON", "ATTACK", "DEFEND", 
            "MUTANT", "ATOMIC", "SYSTEM", "ACCESS", "SERVER", 
            "HACKER", "DANGER", "ROBOTS", "PLASMA", "RADIUM"
        ]
        
        # Select 7 random words
        candidates = random.sample(words, 7)
        password = random.choice(candidates)
        attempts = 4
        
        print(f"\n{Fore.GREEN}ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL{Style.RESET_ALL}")
        print(f"Password Required. Attempts Remaining: {attempts}")
        
        while attempts > 0:
            print("\nCandidates:")
            for w in candidates:
                print(f"  {w}")
            
            try:
                guess = input(f"\n{Fore.GREEN}>{Style.RESET_ALL} ").upper().strip()
            except EOFError:
                return False

            if guess == password:
                return True
            
            if guess in candidates:
                attempts -= 1
                likeness = sum(1 for a, b in zip(guess, password) if a == b)
                print(f"{Fore.YELLOW}Entry Denied.{Style.RESET_ALL} Likeness={likeness}/{len(password)}")
                print(f"Attempts Remaining: {attempts}")
            else:
                print("Error. Invalid selection.")
                
        return False

    def handle_form_filling(self, item, player: Player):
        """Handle filling out bureaucratic forms"""
        from fallout_berlin.enhanced_art_system import BureaucracyRenderer
        form_art = BureaucracyRenderer.render_form(
            f"FORM FILLING: {item.name}\nBureaucracy requires precision. One mistake and you start over.",
            fields={"Subject": player.name, "Form": item.name}
        )
        print(form_art)
        
        if self._play_form_filling_minigame(player):
            print(f"\n{Fore.GREEN}[SUCCESS] Form 27-B is perfectly filled out.{Style.RESET_ALL}")
            print("It just needs a stamp from the Werkbund now.")
            
            # Transform item
            item.name = "Filled Form 27-B"
            item.description = "A meticulously filled out form. Ready for stamping."
            player.add_experience(50)
        else:
            print(f"\n{Fore.RED}[FAILURE] You used the wrong ink color or missed a checkbox.{Style.RESET_ALL}")
            print("The form is ruined. (Just kidding, you can erase it in this game version).")

    def _play_form_filling_minigame(self, player: Player) -> bool:
        """Execute form filling mini-game"""
        print(f"\n{Fore.YELLOW}=== ANMELDUNG FORM 27-B ==={Style.RESET_ALL}")
        
        # Intelligence provides auto-correct or hints
        has_int_bonus = player.intelligence >= 7
        if has_int_bonus:
            print(f"{Fore.CYAN}[INTELLIGENCE] Your keen eye helps you spot bureaucratic traps.{Style.RESET_ALL}")

        # 1. Name
        print("\n[FIELD 1] Name (UPPERCASE):")
        try:
            val = input("> ").strip()
        except EOFError:
            return False
            
        if val != player.name.upper():
            if has_int_bonus:
                print(f"{Fore.CYAN}[AUTO-CORRECT] You catch yourself before using lowercase and fix the entry.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}REJECTED: Name must be uppercase and match ID.{Style.RESET_ALL}")
                return False
            
        # 2. Date
        print("\n[FIELD 2] Current Year (YYYY):")
        try:
            val = input("> ").strip()
        except EOFError:
            return False

        if val != "2287":
            print(f"{Fore.RED}REJECTED: Incorrect year.{Style.RESET_ALL}")
            return False
            
        # 3. Origin
        origin_key = player.origin
        origin_name = Player.ORIGINS[origin_key]['name']
        
        print(f"\n[FIELD 3] Origin ({origin_name}):")
        try:
            val = input("> ").strip()
        except EOFError:
            return False

        if val.lower() != origin_name.lower():
            print(f"{Fore.RED}REJECTED: Origin mismatch.{Style.RESET_ALL}")
            return False
            
        # 4. Purpose
        print("\n[FIELD 4] Purpose of Visit (Business/Pleasure/Survival):")
        try:
            val = input("> ").strip().lower()
        except EOFError:
            return False

        if val not in ["business", "pleasure", "survival"]:
            print(f"{Fore.RED}REJECTED: Invalid purpose.{Style.RESET_ALL}")
            return False
            
        return True

    def handle_bureaucracy_check(self, location_id: str, location_name: str, player: Player, inventory) -> bool:
        """Proxy for the bureaucracy minigame"""
        return self.bureaucracy.play_check(location_id, location_name, player, inventory)
