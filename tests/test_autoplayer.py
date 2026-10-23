import unittest
from contextlib import redirect_stdout
from io import StringIO
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fallout_berlin.autoplayer_v3 import (
    CombatExecutor,
    DialogueExecutor,
    Intention,
    IntentionType,
    LootExecutor,
    NavigationExecutor,
    SurvivalExecutor,
    WorldModel,
    analyze_location_connectivity,
)
from fallout_berlin.dialogue import DialogueManager
from fallout_berlin.improved_game_engine import ImprovedGameEngine
from fallout_berlin.character_creation import CharacterCreator
from fallout_berlin.commands import MoveCommand
from fallout_berlin.looting_state import LootingState
from fallout_berlin.input_parser import InputParser
from fallout_berlin.quest import QuestManager, QuestState
from fallout_berlin.location import LocationManager
from fallout_berlin.ui import UIManager


class AutoplayerConnectivityTests(unittest.TestCase):
    def test_down_command_reaches_the_ubahn_and_prioritizes_location_enemies(self):
        destination = SimpleNamespace(
            get_property=lambda key, default=None: 0 if key == "radiation_level" else default
        )
        locations = {
            "checkpoint_charlie": SimpleNamespace(connections={"down": "u_bahn_tunnel"}),
            "u_bahn_tunnel": destination,
        }
        player = SimpleNamespace(is_sneaking=False)
        engine = SimpleNamespace(
            location_manager=SimpleNamespace(
                get_location=locations.get,
                can_travel=lambda _location, _direction: "u_bahn_tunnel",
                visit_location=Mock(),
            ),
            state=SimpleNamespace(
                current_location="checkpoint_charlie",
                inventory=None,
                player=player,
                location_states={},
            ),
            _sync_location_state=Mock(),
            _update_survival=Mock(),
            event_manager=SimpleNamespace(dispatch=Mock()),
            _check_location_enemies=Mock(return_value=True),
            _check_random_encounter=Mock(return_value=True),
        )

        command = InputParser().parse("down")
        self.assertIsInstance(command, MoveCommand)
        self.assertEqual(
            LocationManager().can_travel("checkpoint_charlie", command.direction),
            "u_bahn_tunnel",
        )
        command.execute(engine)

        self.assertEqual(engine.state.current_location, "u_bahn_tunnel")
        engine._check_location_enemies.assert_called_once_with("u_bahn_tunnel")
        engine._check_random_encounter.assert_not_called()

    def test_exploration_attack_command_engages_a_local_enemy(self):
        enemy = SimpleNamespace(name="Feral Ghoul", enemy_id="feral_ghoul")
        engine = SimpleNamespace(
            location_manager=SimpleNamespace(
                get_location=lambda _location: SimpleNamespace(enemies=[enemy])
            ),
            state=SimpleNamespace(current_location="u_bahn_tunnel"),
            start_combat=Mock(),
        )

        command = InputParser().parse("attack feral ghoul")
        command.execute(engine)

        engine.start_combat.assert_called_once_with(enemy)

    def test_hostile_location_engages_its_enemy_on_entry(self):
        enemy = SimpleNamespace(name="Feral Ghoul", level=3)
        location = SimpleNamespace(
            name="U-Bahn Tunnel",
            enemies=[enemy],
            get_property=lambda key, default=None: (
                True if key == "hostile" else default
            ),
        )
        engine = ImprovedGameEngine.__new__(ImprovedGameEngine)
        engine.location_manager = SimpleNamespace(
            get_location=lambda _location_id: location
        )
        engine.state = SimpleNamespace(
            player=SimpleNamespace(is_sneaking=False)
        )
        engine.start_combat = Mock()

        self.assertTrue(engine._check_location_enemies("u_bahn_tunnel"))
        engine.start_combat.assert_called_once_with(enemy)

    def test_connectivity_requires_mutual_reachability_and_valid_exits(self):
        locations = {
            "a": SimpleNamespace(connections={"east": "b"}),
            "b": SimpleNamespace(connections={"east": "missing"}),
        }

        report = analyze_location_connectivity(locations)

        self.assertFalse(report["strongly_connected"])
        self.assertEqual(report["unreachable_from"], {"b": ["a"]})
        self.assertEqual(report["dangling_exits"], [
            {"from": "b", "direction": "east", "to": "missing"}
        ])

        locations["b"].connections = {"west": "a"}
        report = analyze_location_connectivity(locations)
        self.assertTrue(report["strongly_connected"])
        self.assertEqual(report["unreachable_from"], {})
        self.assertEqual(report["dangling_exits"], [])

    def test_npc_display_name_fallback_supports_talk_command(self):
        self.assertEqual(UIManager.get_npc_name("trader_charlie"), "Trader Charlie")

    def test_dialogue_executor_prefers_quest_actions_then_exits_visited_nodes(self):
        class Option:
            def __init__(self, next_node=None, end_dialogue=False, action=None):
                self.next_node = next_node
                self.end_dialogue = end_dialogue
                self.action = action

        options = [Option("start"), Option("start", action=lambda: None), Option(end_dialogue=True)]
        node = SimpleNamespace(
            node_id="start",
            get_available_options=lambda _state: options,
        )
        engine = SimpleNamespace(current_dialogue_node=node, state=object())
        view = SimpleNamespace(context="DIALOGUE", dialogue_partner="trader_charlie")
        world_model = WorldModel()
        world_model.dialogue_nodes_by_npc["trader_charlie"] = {"start"}
        intention = Intention(IntentionType.DIALOGUE, 1.0, "test")
        executor = DialogueExecutor()

        self.assertEqual(executor.execute(view, world_model, intention, engine), "2")
        options[1].action = None
        options[0].next_node = "new_node"
        self.assertEqual(executor.execute(view, world_model, intention, engine), "1")
        options[0].next_node = "start"
        self.assertEqual(executor.execute(view, world_model, intention, engine), "3")
        options.pop()
        self.assertEqual(executor.execute(view, world_model, intention, engine), "bye")

    def test_combat_survival_uses_supported_heal_or_flee_commands(self):
        view = SimpleNamespace(
            context="COMBAT",
            player_status={"hp_percent": 0.2},
        )
        intention = Intention(IntentionType.SURVIVE, 1.0, "critical health")
        executor = SurvivalExecutor()
        engine = SimpleNamespace(
            state=SimpleNamespace(
                inventory=SimpleNamespace(find_item=lambda _name: object())
            )
        )

        self.assertEqual(executor.execute(view, WorldModel(), intention, engine), "heal")
        engine.state.inventory.find_item = lambda _name: None
        self.assertEqual(executor.execute(view, WorldModel(), intention, engine), "flee")
        view.context = "EXPLORATION"
        self.assertEqual(executor.execute(view, WorldModel(), intention, engine), "camp")

        combat_engine = SimpleNamespace(
            combat_manager=SimpleNamespace(
                current_enemy=SimpleNamespace(hp=10),
                in_vats=False,
                ATTACK_AP_COST=5,
            ),
            state=SimpleNamespace(
                player=SimpleNamespace(hit_points=20, max_hit_points=100),
                inventory=SimpleNamespace(
                    find_item=lambda _name: None,
                    items=[],
                ),
            ),
        )
        self.assertEqual(
            CombatExecutor().execute(
                view, WorldModel(), intention, combat_engine
            ),
            "flee",
        )
        combat_engine.state.player.hit_points = 40
        combat_engine.state.player.current_ap = 10
        with patch("fallout_berlin.autoplayer_v3.random.random", return_value=1.0):
            self.assertEqual(
                CombatExecutor().execute(
                    view, WorldModel(), intention, combat_engine
                ),
                "attack",
            )
        combat_engine.state.player.current_ap = 4
        self.assertEqual(
            CombatExecutor().execute(
                view, WorldModel(), intention, combat_engine
            ),
            "end turn",
        )

    def test_navigation_avoids_a_failed_edge(self):
        locations = {
            "start": SimpleNamespace(
                connections={"west": "blocked", "north": "unvisited"},
                properties={},
                enemies=[],
            ),
            "blocked": SimpleNamespace(connections={}, properties={}, enemies=[]),
            "unvisited": SimpleNamespace(connections={}, properties={}, enemies=[]),
        }
        player = SimpleNamespace(
            level=1,
            hit_points=20,
            max_hit_points=30,
            is_overencumbered=lambda _weight: False,
        )
        inventory = SimpleNamespace(items=[], get_total_weight=lambda: 0)
        engine = SimpleNamespace(
            location_manager=SimpleNamespace(locations=locations),
            state=SimpleNamespace(player=player, inventory=inventory),
        )
        world_model = WorldModel()
        world_model.beliefs["start"] = SimpleNamespace()
        world_model.failed_edges[("start", "west")] = ((), 1, True)
        view = SimpleNamespace(
            current_location_id="start",
            local_affordances={"exits": ["west", "north"]},
        )

        with patch("fallout_berlin.autoplayer_v3.random.random", return_value=1.0):
            command = NavigationExecutor().execute(
                view, world_model, Intention(IntentionType.EXPLORE, 1.0, "test"), engine
            )
        self.assertEqual(command, "go north")


class GameplaySafetyRegressionTests(unittest.TestCase):
    def test_character_perks_load_outside_the_project_directory(self):
        original_directory = os.getcwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                perks = CharacterCreator(None)._load_perks()
            finally:
                os.chdir(original_directory)

        self.assertTrue(perks)
        self.assertTrue(all("name" in perk for perk in perks))

    def test_loot_exit_closes_loot_state_instead_of_quitting_game(self):
        class ExplorationStateStub:
            def __init__(self, _engine):
                pass

        engine = ImprovedGameEngine.__new__(ImprovedGameEngine)
        engine.current_state = LootingState(engine, "Test Loot", [])
        engine._get_engine_states = lambda: (
            ExplorationStateStub, None, None, None
        )
        engine.change_state = lambda state: setattr(engine, "current_state", state)

        self.assertFalse(engine._handle_global_command("exit"))
        engine.current_state.handle_input("exit")
        self.assertIsInstance(engine.current_state, ExplorationStateStub)

    def test_engine_initializes_console_after_platform_stream_setup(self):
        with patch(
            "fallout_berlin.improved_game_engine.colorama.just_fix_windows_console"
        ) as initialize_console:
            ImprovedGameEngine()

        initialize_console.assert_called_once_with()

    def test_quest_turn_in_action_can_find_inactive_quest_definitions(self):
        manager = DialogueManager()
        quest_manager = QuestManager()
        state = SimpleNamespace(quests=quest_manager.quests)

        manager._action_start_iron_will(state)

        self.assertEqual(
            state.quests["iron_will"].state,
            QuestState.ACTIVE,
        )

    def test_iron_will_turn_in_requires_active_quest(self):
        manager = DialogueManager()
        state = SimpleNamespace(
            quests={},
            inventory=SimpleNamespace(
                has_item=lambda _item, _quantity=1: True,
                remove_item=lambda _item: self.fail(
                    "Turn-in must not consume an item without an active quest"
                ),
            ),
        )
        join_node = manager.get_dialogue_tree("general_von_stahl").get_node("join")

        available_text = {
            option.text for option in join_node.get_available_options(state)
        }
        self.assertNotIn("I have the data drive.", available_text)
        manager._action_complete_iron_will(state)

    def test_engine_errors_do_not_overwrite_autosaves(self):
        engine = ImprovedGameEngine.__new__(ImprovedGameEngine)
        engine.config = SimpleNamespace(debug_mode=False)
        engine._autosave = lambda: self.fail(
            "Error handling must not overwrite an existing autosave"
        )

        with redirect_stdout(StringIO()):
            engine._handle_error(RuntimeError("test"))

    def test_starting_npc_dialogue_sets_quest_trigger_flag(self):
        class DialogueStateStub:
            def __init__(self, _engine, npc_id, current_node):
                self.npc_id = npc_id
                self.current_node = current_node

        engine = ImprovedGameEngine.__new__(ImprovedGameEngine)
        engine.dialogue_manager = DialogueManager()
        engine.state = SimpleNamespace(set_world_flag=lambda flag: flags.setdefault(flag, True))
        engine._get_engine_states = lambda: (None, None, DialogueStateStub, None)
        engine.change_state = lambda _state: None
        flags = {}

        engine._start_dialogue("mother_renate")

        self.assertTrue(flags["talked_to_mother_renate"])

    def test_looting_skips_items_that_wont_fit_in_inventory(self):
        loot_item = SimpleNamespace(name="light item", weight=1)
        engine = SimpleNamespace(
            state=SimpleNamespace(
                inventory=SimpleNamespace(can_add_item=lambda item: item is loot_item)
            ),
            current_state=SimpleNamespace(items=[loot_item]),
        )
        view = SimpleNamespace(context="LOOTING", local_affordances={"items": []})

        self.assertEqual(LootExecutor().execute(view, WorldModel(), None, engine), "take light item")
        engine.state.inventory.can_add_item = lambda _item: False
        self.assertEqual(LootExecutor().execute(view, WorldModel(), None, engine), "done")


if __name__ == "__main__":
    unittest.main()
