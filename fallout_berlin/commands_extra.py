from typing import List
from fallout_berlin.commands import Command
from colorama import Fore, Style
from fallout_berlin.item import create_item


class RecycleCommand(Command):
    def execute(self, game):
        # 1. Check if location has a Pfandautomat
        # Simplified: Check if "pfand" or "automat" is in the location actions or items?
        # Or better, just check if we are at a Späti location or Kotti.

        location = game.location_manager.get_location(game.state.current_location)
        if not location:
            return

        # Hardcode valid locations for now or add property later
        valid_locations = ["kotti", "checkpoint_charlie", "alexanderplatz"]
        if game.state.current_location not in valid_locations:
            print("There is no Pfandautomat (Recycling Machine) here.")
            return

        # 2. Count bottles
        empty_bottles = 0
        pfand_bottles = 0

        # Iterate backwards to remove safely
        to_remove = []
        for item in game.state.inventory.items:
            if item.name.lower() == "empty bottle":
                empty_bottles += item.quantity
                to_remove.append(item)
            elif item.name.lower() == "pfand bottle":
                pfand_bottles += item.quantity
                to_remove.append(item)

        if empty_bottles == 0 and pfand_bottles == 0:
            print("You don't have any bottles to return.")
            return

        # 3. Calculate payout
        # Empty bottle = 0.08 caps (rounded down? lets say 1 cap for simplicity)
        # Pfand bottle = 0.25 caps (say 3 caps)

        payout = (empty_bottles * 1) + (pfand_bottles * 3)

        # 4. Remove items
        for item in to_remove:
            game.state.inventory.remove_item(item.name, item.quantity)

        # 5. Add caps
        caps = create_item("caps", payout)
        game.state.inventory.add_item(caps)

        print(
            f"\n{Fore.GREEN}You insert the bottles into the machine...{Style.RESET_ALL}"
        )
        print("Clunk... Clunk... Whirrr...")
        print(f"The machine spits out {Fore.YELLOW}{payout} Caps{Style.RESET_ALL}.")
