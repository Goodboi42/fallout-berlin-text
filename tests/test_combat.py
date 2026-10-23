import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fallout_berlin.combat import CombatManager
from fallout_berlin.engine_states import CombatState
from fallout_berlin.enemy import Enemy
from fallout_berlin.effect_manager import EffectManager
from fallout_berlin.inventory import Inventory
from fallout_berlin.item import create_item
from fallout_berlin.player import Player
from fallout_berlin.vats_state import VatsState


class CombatManagerTests(unittest.TestCase):
    def setUp(self):
        self.player = Player("Test")
        self.state = SimpleNamespace(
            player=self.player,
            inventory=Inventory(),
            killed_creatures={},
        )
        self.manager = CombatManager(self.state, None, None)

    def test_normal_attack_does_not_spend_ap(self):
        enemy = Enemy("Target", "", 1, 100, 0, 0)
        self.manager.start_combat(enemy)
        starting_ap = self.player.current_ap

        with patch("fallout_berlin.combat.random.randint", return_value=1):
            status, _ = self.manager.process_combat_turn("attack", None)

        self.assertEqual(status, "CONTINUE")
        self.assertEqual(
            self.player.current_ap,
            min(self.player.max_ap, starting_ap + 2 + self.player.agility // 2),
        )
        self.assertLess(enemy.hp, enemy.max_hp)

    def test_normal_attack_works_with_no_ap(self):
        enemy = Enemy("Target", "", 1, 100, 20, 0)
        self.manager.start_combat(enemy)
        self.player.current_ap = 0
        starting_hp = self.player.hit_points

        with patch("fallout_berlin.combat.random.randint", return_value=1):
            status, _ = self.manager.process_combat_turn("attack", None)

        self.assertEqual(status, "CONTINUE")
        self.assertLess(enemy.hp, enemy.max_hp)
        self.assertLess(self.player.hit_points, starting_hp)
        self.assertEqual(self.player.current_ap, 2 + self.player.agility // 2)

    def test_ending_turn_recovers_ap_and_advances_combat(self):
        enemy = Enemy("Target", "", 1, 100, 0, 0)
        self.manager.start_combat(enemy)
        self.player.current_ap = 4

        status, _ = self.manager.process_combat_turn("end turn", None)

        self.assertEqual(status, "CONTINUE")
        self.assertGreater(self.player.current_ap, 4)
        self.assertEqual(enemy.hp, enemy.max_hp)

    def test_victory_awards_xp_and_kill_credit_only_once(self):
        enemy = Enemy("Rad Hund", "", 1, 1, 0, 25)
        enemy.enemy_id = "radhund_alpha"
        self.manager.start_combat(enemy)

        with patch("fallout_berlin.combat.random.randint", return_value=1):
            first_status, _ = self.manager.process_combat_turn("attack", None)
            second_status, _ = self.manager.process_combat_turn("attack", None)

        self.assertEqual((first_status, second_status), ("VICTORY", "VICTORY"))
        self.assertEqual(self.player.experience, 25)
        self.assertEqual(self.state.killed_creatures, {"radhund_alpha": 1})

    def test_heal_shortcut_uses_shared_consumable_effect(self):
        self.player.perks = [{"name": "Medic"}]
        self.player.max_hit_points = 100
        self.player.hit_points = 1
        stimpak = create_item("stimpak")
        self.state.inventory.add_item(stimpak)
        self.manager.start_combat(Enemy("Target", "", 1, 100, 0, 0))
        engine = SimpleNamespace(effect_manager=EffectManager())

        status, _ = self.manager.process_combat_turn("heal", engine)

        self.assertEqual(status, "CONTINUE")
        self.assertEqual(self.player.hit_points, 45)
        self.assertIn("Healed 45 HP", self.manager.last_action_feedback)
        self.assertFalse(self.state.inventory.has_item("stimpak"))

    def test_combat_action_shortcuts_dispatch_expected_commands(self):
        engine = SimpleNamespace(combat_manager=self.manager)
        dispatched = []

        def process(command, _engine):
            dispatched.append(command)
            return "CONTINUE", None

        self.manager.process_combat_turn = process
        state = CombatState(engine)

        for shortcut, expected in (
            ("A", "attack"),
            ("H", "heal"),
            ("C", "take cover"),
            ("F", "flee"),
        ):
            with self.subTest(shortcut=shortcut):
                state.handle_input(shortcut)
                self.assertEqual(dispatched[-1], expected)

    def test_v_shortcut_enters_vats_and_targeting_executes_attack(self):
        enemy = Enemy("Target", "", 1, 100, 0, 0)
        self.manager.start_combat(enemy)
        self.player.current_ap = 10
        calls = []
        engine = SimpleNamespace(
            combat_manager=self.manager,
            state=self.state,
            current_state=None,
            change_state=lambda state: setattr(engine, "current_state", state),
        )
        self.manager.process_combat_turn = lambda command, _engine: (
            calls.append(command) or ("CONTINUE", None)
        )

        combat_state = CombatState(engine)
        engine.current_state = combat_state
        combat_state.handle_input("V")
        self.assertIsInstance(engine.current_state, VatsState)
        self.assertTrue(self.manager.in_vats)

        engine.current_state.handle_input("1")

        self.assertEqual(calls, ["vats head"])
        self.assertIsInstance(engine.current_state, CombatState)
        self.assertFalse(self.manager.in_vats)

    def test_vats_attack_spends_ap_and_applies_headshot_critical(self):
        enemy = Enemy("Target", "", 1, 100, 0, 0)
        self.manager.start_combat(enemy)
        self.player.current_ap = 10

        with patch("fallout_berlin.combat.random.randint", return_value=1):
            status, _ = self.manager.process_combat_turn("vats head", None)

        self.assertEqual(status, "CONTINUE")
        self.assertEqual(
            self.player.current_ap,
            min(self.player.max_ap, 10 - self.manager.ATTACK_AP_COST + 2 + self.player.agility // 2),
        )
        self.assertIn("in the Head", self.manager.last_action_feedback)
        self.assertIn("(CRITICAL)", self.manager.last_action_feedback)

    def test_vats_attack_with_insufficient_ap_does_not_take_a_turn(self):
        enemy = Enemy("Target", "", 1, 100, 20, 0)
        self.manager.start_combat(enemy)
        self.player.current_ap = self.manager.ATTACK_AP_COST - 1
        starting_hp = self.player.hit_points

        status, _ = self.manager.process_combat_turn("vats head", None)

        self.assertEqual(status, "CONTINUE")
        self.assertEqual(self.player.current_ap, self.manager.ATTACK_AP_COST - 1)
        self.assertEqual(self.player.hit_points, starting_hp)
        self.assertEqual(enemy.hp, enemy.max_hp)

    def test_combat_exit_restores_full_ap(self):
        enemy = Enemy("Target", "", 1, 100, 0, 0)
        self.manager.start_combat(enemy)
        self.player.current_ap = 2
        self.player.hit_points = 1

        status, _ = self.manager.process_combat_turn("take cover", None)

        self.assertEqual(status, "DEFEAT")
        self.assertEqual(self.player.current_ap, self.player.max_ap)
        self.assertFalse(self.manager.in_combat)

    def test_escape_restores_full_ap(self):
        enemy = Enemy("Target", "", 1, 100, 0, 0)
        self.manager.start_combat(enemy)
        self.player.current_ap = 1

        with patch("fallout_berlin.combat.random.random", return_value=0):
            status, _ = self.manager.process_combat_turn("flee", None)

        self.assertEqual(status, "ESCAPED")
        self.assertEqual(self.player.current_ap, self.player.max_ap)
        self.assertFalse(self.manager.in_combat)

    def test_victory_restores_full_ap(self):
        enemy = Enemy("Target", "", 1, 1, 0, 0)
        self.manager.start_combat(enemy)
        self.player.current_ap = 2

        with patch("fallout_berlin.combat.random.randint", return_value=1):
            status, _ = self.manager.process_combat_turn("attack", None)

        self.assertEqual(status, "VICTORY")
        self.assertEqual(self.player.current_ap, self.player.max_ap)
        self.assertFalse(self.manager.in_combat)

    def test_victory_removes_defeated_enemy_from_current_location(self):
        enemy = Enemy("Target", "", 1, 1, 0, 0)
        location = SimpleNamespace(enemies=[enemy])
        self.state.current_location = "test_location"
        self.manager.location_manager = SimpleNamespace(
            get_location=lambda _location_id: location
        )
        self.manager.start_combat(enemy)

        with patch("fallout_berlin.combat.random.randint", return_value=1):
            self.manager.process_combat_turn("attack", None)

        self.assertEqual(location.enemies, [])


if __name__ == "__main__":
    unittest.main()