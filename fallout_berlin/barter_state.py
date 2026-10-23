import math
from typing import TYPE_CHECKING

from colorama import Fore, Style

from fallout_berlin.engine_states import EngineState
from fallout_berlin.item import Item, create_item

if TYPE_CHECKING:
    from fallout_berlin.improved_game_engine import ImprovedGameEngine


class BarterState(EngineState):
    """Buy from a merchant or sell carried loot."""

    STOCK = {
        "trader_charlie": ["stimpak", "ammo_10mm", "currywurst"],
        "merchant_jakob": ["stimpak", "scrap_metal", "ammo_10mm"],
        "werkbund_merchant": ["leather_jacket", "laser_pistol", "stimpak"],
        "execution_vendor": ["10mm_pistol", "leather_jacket", "radaway"],
        "ghoul_vendor_gori": ["radaway", "stimpak", "scrap_metal"],
    }

    def __init__(self, engine: "ImprovedGameEngine", vendor_id: str):
        super().__init__(engine, "Barter")
        self.vendor_id = vendor_id
        self.stock = []
        for item_id in self.STOCK.get(vendor_id, ["stimpak", "ammo_10mm"]):
            item = create_item(item_id)
            if item:
                if item.stackable:
                    item.quantity = 5
                self.stock.append(item)

    def _prices(self, item: Item):
        skill = max(0, self.engine.state.player.get_skill("Barter"))
        discount = min(25, skill // 2)
        buy_price = max(1, math.ceil(item.value * (100 - discount) / 100))
        sell_price = max(1, math.floor(item.value * (50 + discount) / 100))
        return buy_price, sell_price

    def render(self):
        self.engine.ui_manager.clear_screen()
        self.engine.ui_manager.display_header("BARTER", style="double", color=Fore.YELLOW)
        print(f"\nCaps: {self.engine.state.inventory.caps}")
        print(f"\n{Fore.CYAN}Merchant stock:{Style.RESET_ALL}")
        if self.stock:
            for item in self.stock:
                buy_price, _ = self._prices(item)
                print(f"  {item.name} x{item.quantity} - {buy_price} caps each")
        else:
            print("  No goods available.")

        print(f"\n{Fore.CYAN}Your sellable loot:{Style.RESET_ALL}")
        sellable = self._sellable_items()
        if sellable:
            for item in sellable:
                _, sell_price = self._prices(item)
                print(f"  {item.name} x{item.quantity} - {sell_price} caps each")
        else:
            print("  Nothing the merchant will buy.")
        print("\nCommands: buy <item> [quantity], sell <item> [quantity], list, close")

    def _sellable_items(self):
        player = self.engine.state.player
        equipped = [player.equipped_weapon, player.equipped_armor]
        return [
            item
            for item in self.engine.state.inventory.items
            if item.item_type not in {"currency", "quest"}
            and not any(
                item is gear
                or (
                    gear
                    and item.item_type == gear.item_type
                    and item.name.casefold() == gear.name.casefold()
                )
                for gear in equipped
            )
        ]

    @staticmethod
    def _parse_trade(command):
        parts = command.split()
        if len(parts) < 2:
            return None, None, 1
        quantity = 1
        if parts[-1].isdigit():
            quantity = int(parts.pop())
        return parts[0], " ".join(parts[1:]), quantity

    @staticmethod
    def _find_item(items, name):
        needle = name.casefold()
        matches = [item for item in items if item.name.casefold() == needle]
        if not matches:
            matches = [item for item in items if needle in item.name.casefold()]
        return matches[0] if len(matches) == 1 else None

    def handle_input(self, command: str):
        cmd = command.strip().casefold()
        if cmd in {"c", "close", "exit", "back", "q"}:
            from fallout_berlin.engine_states import ExplorationState
            self.engine.change_state(ExplorationState(self.engine))
            return
        if cmd == "list":
            self.render()
            return

        action, item_name, quantity = self._parse_trade(cmd)
        if action not in {"buy", "sell"} or not item_name or quantity <= 0:
            print("Use: buy <item> [quantity], sell <item> [quantity], list, or close.")
            return
        if action == "buy":
            self._buy(item_name, quantity)
        else:
            self._sell(item_name, quantity)

    def _buy(self, name: str, quantity: int):
        item = self._find_item(self.stock, name)
        if not item:
            print(f"The merchant doesn't have '{name}'.")
            return
        if not item.stackable and quantity != 1:
            print("That item can only be bought one at a time.")
            return
        if item.quantity < quantity:
            print(f"Only {item.quantity} available.")
            return

        price, _ = self._prices(item)
        total = price * quantity
        inventory = self.engine.state.inventory
        if inventory.caps < total:
            print(f"Not enough caps. This costs {total}; you have {inventory.caps}.")
            return

        bought = Item.from_dict(item.to_dict())
        bought.quantity = quantity
        if not inventory.can_add_item(bought):
            print("You don't have enough carry capacity.")
            return
        inventory.remove_caps(total)
        inventory.add_item(bought)

        item.quantity -= quantity
        if item.quantity == 0:
            self.stock.remove(item)
        print(f"Bought {bought.name} x{quantity} for {total} caps.")

    def _sell(self, name: str, quantity: int):
        inventory = self.engine.state.inventory
        item = self._find_item(self._sellable_items(), name)
        if not item:
            print(f"You can't sell '{name}'.")
            return
        if not item.stackable and quantity != 1:
            print("That item can only be sold one at a time.")
            return
        if item.quantity < quantity:
            print(f"You only have {item.quantity}.")
            return

        _, price = self._prices(item)
        payment = price * quantity
        sold = Item.from_dict(item.to_dict())
        sold.quantity = quantity
        if item.quantity == quantity:
            inventory.remove_item(item.name, quantity)
        else:
            item.quantity -= quantity
        self.engine.state.inventory.add_caps(payment)

        stock_item = self._find_item(self.stock, sold.name)
        if stock_item and stock_item.stackable:
            stock_item.quantity += quantity
        else:
            self.stock.append(sold)
        print(f"Sold {sold.name} x{quantity} for {payment} caps.")
