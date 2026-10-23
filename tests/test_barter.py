import unittest
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace

from fallout_berlin.barter_state import BarterState
from fallout_berlin.dialogue import DialogueManager
from fallout_berlin.engine_states import ExplorationState
from fallout_berlin.improved_game_engine import ImprovedGameEngine
from fallout_berlin.inventory import Inventory
from fallout_berlin.item import create_item
from fallout_berlin.player import Player
from fallout_berlin.quest import Quest
from fallout_berlin.quest_log_state import QuestLogState


class BarterTests(unittest.TestCase):
    def setUp(self):
        self.player = Player("Trader")
        self.inventory = Inventory()
        self.inventory.add_caps(1000)
        self.state = SimpleNamespace(player=self.player, inventory=self.inventory)
        self.engine = SimpleNamespace(
            state=self.state,
            current_state=object(),
            current_dialogue_tree=SimpleNamespace(npc_id="trader_charlie"),
            change_state=lambda state: setattr(self.engine, "current_state", state),
            ui_manager=SimpleNamespace(
                clear_screen=lambda: None,
                display_header=lambda *_args, **_kwargs: None,
            ),
        )
        self.trade = BarterState(self.engine, "trader_charlie")
        self.engine.current_state = self.trade

    def test_caps_stack_and_survive_spending(self):
        self.inventory.add_caps(25)
        self.assertEqual(self.inventory.caps, 1025)
        self.assertTrue(self.inventory.remove_caps(40))
        self.assertEqual(self.inventory.caps, 985)
        self.assertFalse(self.inventory.remove_caps(1000))
        self.assertEqual(self.inventory.caps, 985)

    def test_buy_and_sell_loot_for_caps(self):
        stock_item = next(item for item in self.trade.stock if item.name == "Sani-Pack (Stimpak)")
        unit_price, _ = self.trade._prices(stock_item)
        self.trade.handle_input("buy stimpak 2")
        self.assertEqual(self.inventory.caps, 1000 - unit_price * 2)
        self.assertEqual(self.inventory.find_item("stimpak").quantity, 2)

        loot = create_item("scrap_metal")
        self.inventory.add_item(loot)
        _, sale_price = self.trade._prices(loot)
        self.trade.handle_input("sell scrap metal")
        self.assertEqual(self.inventory.caps, 1000 - unit_price * 2 + sale_price)
        self.assertIsNone(self.inventory.find_item("scrap_metal"))

    def test_buy_rejects_insufficient_caps_without_changing_stock(self):
        self.inventory.remove_caps(self.inventory.caps)
        stock_item = self.trade.stock[0]
        quantity = stock_item.quantity

        self.trade.handle_input(f"buy {stock_item.name}")

        self.assertEqual(self.inventory.caps, 0)
        self.assertEqual(stock_item.quantity, quantity)

    def test_cannot_sell_equipped_gear_after_loading_a_save(self):
        weapon = create_item("10mm_pistol")
        self.inventory.add_item(weapon)
        self.player.equipped_weapon = create_item("10mm_pistol")

        self.assertNotIn(weapon, self.trade._sellable_items())

    def test_dialogue_open_shop_action_enters_barter(self):
        manager = DialogueManager()
        option = manager.dialogue_trees["trader_charlie"].get_node("shop").options[0]
        self.state.quests = {}

        manager.process_option(option, self.engine)

        self.assertIsInstance(self.engine.current_state, BarterState)

    def test_q_opens_quest_log_instead_of_quitting(self):
        engine = ImprovedGameEngine.__new__(ImprovedGameEngine)
        engine.current_state = ExplorationState(engine)
        engine.state = SimpleNamespace(inventory=Inventory())
        engine.quest_manager = SimpleNamespace(
            get_active_quests=lambda: [],
            get_completed_quests=lambda: [],
        )
        engine.change_state = lambda state: setattr(engine, "current_state", state)
        engine._quit_game = lambda: self.fail("q must not quit the game")

        self.assertTrue(engine._handle_global_command("q"))
        self.assertEqual(type(engine.current_state).__name__, "QuestLogState")

        self.assertFalse(engine._handle_global_command("q"))
        engine.current_state.handle_input("q")
        self.assertIsInstance(engine.current_state, ExplorationState)

    def test_i_opens_inventory_from_exploration(self):
        engine = ImprovedGameEngine.__new__(ImprovedGameEngine)
        engine.current_state = ExplorationState(engine)
        engine.state = SimpleNamespace(inventory=Inventory())
        engine.change_state = lambda state: setattr(engine, "current_state", state)

        self.assertTrue(engine._handle_global_command("i"))
        self.assertEqual(type(engine.current_state).__name__, "InventoryState")

    def test_quest_log_lists_real_active_and_completed_quest_titles(self):
        active = Quest("active", "Active Quest", "An active quest.")
        active.start()
        completed = Quest("completed", "Completed Quest", "A completed quest.")
        completed.start()
        completed.complete()
        engine = SimpleNamespace(
            quest_manager=SimpleNamespace(
                get_active_quests=lambda: [active],
                get_completed_quests=lambda: [completed],
            ),
            ui_manager=SimpleNamespace(
                clear_screen=lambda: None,
                display_header=lambda *_args, **_kwargs: None,
            ),
        )
        state = QuestLogState(engine)
        output = StringIO()

        with redirect_stdout(output):
            state.render()

        self.assertIn("Active Quest", output.getvalue())
        self.assertIn("Completed Quest", output.getvalue())
        self.assertEqual(state.quests, [active, completed])

    def test_dialogue_json_actions_are_never_silently_dropped(self):
        manager = DialogueManager()
        trees = json.loads(
            (Path(__file__).parents[1] / "fallout_berlin" / "data" / "dialogues.json")
            .read_text(encoding="utf-8")
        )

        for tree_id, tree_data in trees.items():
            tree = manager.dialogue_trees[tree_id]
            for node_id, node_data in tree_data["nodes"].items():
                options = tree.nodes[node_id].options
                for option_data, option in zip(node_data.get("options", []), options):
                    if "action" in option_data:
                        with self.subTest(action=option_data["action"]):
                            self.assertIsNotNone(option.action)

    def test_vault_key_is_findable_at_the_quest_location(self):
        from fallout_berlin.location import LocationManager

        location = LocationManager().get_location("teufelsberg_station")

        self.assertIsNotNone(location.find_item("Vault B-12 Key"))


if __name__ == "__main__":
    unittest.main()
