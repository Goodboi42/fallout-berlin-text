"""
Enhanced ASCII Art System for Fallout Berlin
Provides advanced visual elements including animations, effects, and dynamic rendering
"""

import time
import random
import math
from typing import List, Dict, Optional, Tuple, Callable, Any, TYPE_CHECKING
from colorama import Fore, Back, Style
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path if running as a script to handle imports
if __name__ == "__main__":
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

if TYPE_CHECKING:
    from fallout_berlin.ui import PipBoyRenderer


class LightingManager:
    """Manages dynamic lighting and flicker effects"""
    
    @staticmethod
    def get_intensity(flicker: bool = False) -> float:
        """Calculate current light intensity based on time"""
        # Sine wave base (0.7 to 1.0)
        base = 0.85 + 0.15 * math.sin(time.time() * 2.0)
        
        # Add random flicker spikes
        if flicker and random.random() < 0.1:
            return base * random.uniform(0.4, 0.6)
            
        return base

    @staticmethod
    def apply_lighting(text: str, intensity: float) -> str:
        """Apply style based on intensity with color support"""
        if intensity < 0.4:
            return f"{Style.DIM}{Fore.BLACK}{text}{Style.NORMAL}{Style.RESET_ALL}"
        elif intensity < 0.6:
            return f"{Style.DIM}{text}{Style.NORMAL}"
        elif intensity > 0.95:
            return f"{Style.BRIGHT}{text}{Style.NORMAL}"
        return text


class ArtFrame:
    """Represents a single frame of ASCII art with optional color"""
    
    def __init__(self, art: str, color: str = Style.RESET_ALL, delay: float = 0.1):
        self.art = art
        self.color = color
        self.delay = delay
    
    def render(self, lighting: Optional[float] = None) -> str:
        content = self.art
        if lighting is not None:
            content = LightingManager.apply_lighting(content, lighting)
        return f"{self.color}{content}{Style.RESET_ALL}"


class Animation:
    """Handles frame-by-frame ASCII animations"""
    
    def __init__(self, frames: List[ArtFrame], loop: bool = False, callback: Optional[Callable] = None):
        self.frames = frames
        self.loop = loop
        self.current_frame = 0
        self.callback = callback
    
    def play(self, clear_screen: bool = True, use_lighting: bool = False):
        """Play the animation"""
        iterations = 0
        while True:
            if clear_screen:
                os.system('clear' if os.name != 'nt' else 'cls')
            
            intensity = LightingManager.get_intensity(flicker=True) if use_lighting else None
            frame = self.frames[self.current_frame]
            
            if self.callback:
                self.callback(self.current_frame)
                
            print(frame.render(lighting=intensity))
            time.sleep(frame.delay)
            
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            if self.current_frame == 0:
                iterations += 1
                if not self.loop:
                    break
                if iterations >= 3:  # Limit loops
                    break
    
    def get_frame(self, index: int, lighting: Optional[float] = None) -> str:
        """Get a specific frame without playing"""
        return self.frames[index % len(self.frames)].render(lighting=lighting)




class ArtComposer:
    """Composes complex scenes from multiple art elements"""
    
    @staticmethod
    def center_text(text: str, width: int = 80) -> str:
        """Center text within a given width"""
        lines = text.split('\n')
        centered = []
        for line in lines:
            stripped = line.rstrip()
            padding = (width - len(stripped)) // 2
            centered.append(' ' * padding + stripped)
        return '\n'.join(centered)
    
    @staticmethod
    def create_border(text: str, style: str = "double", color: str = Fore.CYAN) -> str:
        """Add a border around text (using ASCII for compatibility)"""
        lines = text.split('\n')
        width = max(len(line) for line in lines) + 4
        
        # Simplified to ASCII for maximum compatibility across terminals
        top = "+" + "-" * (width - 2) + "+"
        bottom = "+" + "-" * (width - 2) + "+"
        side = "|"
        
        result = [f"{color}{top}{Style.RESET_ALL}"]
        for line in lines:
            padded = line.ljust(width - 4)
            result.append(f"{color}{side}{Style.RESET_ALL} {padded} {color}{side}{Style.RESET_ALL}")
        result.append(f"{color}{bottom}{Style.RESET_ALL}")
        
        return '\n'.join(result)
    
    @staticmethod
    def overlay(background: str, foreground: str, x: int = 0, y: int = 0) -> str:
        """Overlay one ASCII art on another at position (x, y)"""
        bg_lines = background.split('\n')
        fg_lines = foreground.split('\n')
        
        result = [list(line) for line in bg_lines]
        
        for i, fg_line in enumerate(fg_lines):
            target_y = y + i
            if 0 <= target_y < len(result):
                for j, char in enumerate(fg_line):
                    target_x = x + j
                    if 0 <= target_x < len(result[target_y]) and char != ' ':
                        result[target_y][target_x] = char
        
        return '\n'.join([''.join(line) for line in result])
    
    @staticmethod
    def add_shadow(art: str, direction: str = "right") -> str:
        """Add a shadow effect to ASCII art"""
        lines = art.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            if direction == "right":
                shadow = ' ' + line.replace(' ', '') + f"{Fore.BLACK}#{Style.RESET_ALL}"
            elif direction == "bottom":
                result.append(line)
                if i == len(lines) - 1:
                    result.append(f"{Fore.BLACK}{'#' * len(line)}{Style.RESET_ALL}")
                continue
            else:
                shadow = line
            result.append(shadow)
        
        return '\n'.join(result)


class WeatherEffect:
    """Generate atmospheric weather effects"""
    
    @staticmethod
    def generate_rain(width: int = 80, height: int = 10, intensity: float = 0.3) -> str:
        """Generate rain effect"""
        rain_chars = ['|', '¦', '|', '¦', '/', '\\']
        lines = []
        for _ in range(height):
            line = []
            for _ in range(width):
                if random.random() < intensity:
                    line.append(random.choice(rain_chars))
                else:
                    line.append(' ')
            lines.append(''.join(line))
        return f"{Fore.BLUE}{''.join(lines)}{Style.RESET_ALL}"
    
    @staticmethod
    def generate_radiation_storm(width: int = 80, height: int = 10) -> str:
        """Generate radioactive storm effect"""
        rad_chars = ['!', '?', '=', '~', '^', '@']
        lines = []
        for _ in range(height):
            line = []
            for _ in range(width):
                if random.random() < 0.15:
                    char = random.choice(rad_chars)
                    color = random.choice([Fore.GREEN, Fore.YELLOW, Fore.LIGHTGREEN_EX])
                    line.append(f"{color}{char}{Style.RESET_ALL}")
                else:
                    line.append(' ')
            lines.append(''.join(line))
        return '\n'.join(lines)
    
    @staticmethod
    def generate_fog(width: int = 80, height: int = 5) -> str:
        """Generate fog effect"""
        fog_chars = [':', '.', ';', ' ', ' ']
        lines = []
        for _ in range(height):
            line = ''.join(random.choice(fog_chars) for _ in range(width))
            lines.append(f"{Fore.WHITE}{line}{Style.RESET_ALL}")
        return '\n'.join(lines)

    @staticmethod
    def generate_wind_dust(width: int = 80, height: int = 5) -> str:
        """Generate wind and dust particles effect"""
        # Removed '\u02d9' (˙) as it causes encoding issues on some Windows terminals
        dust_chars = ['.', '*', '~', ' ', ' ', ' ']
        lines = []
        for _ in range(height):
            line = ''.join(random.choice(dust_chars) for _ in range(width))
            lines.append(f"{Fore.YELLOW}{Style.DIM}{line}{Style.RESET_ALL}")
        return '\n'.join(lines)

    @staticmethod
    def play_audio_cue(type: str = "text"):
        """Audio cues disabled as per user request."""
        pass


class AdvancedArtLibrary:
    """Extended art library with animations and effects"""
    
    # Animated sequences
    ANIMATIONS = {
        "combat_initiate": [
            ArtFrame("""
                    X
                   X X
                  X   X
            """, Fore.RED, 0.2),
            ArtFrame("""
                  X   X
                 X  X  X
                X   X   X
            """, Fore.LIGHTRED_EX, 0.2),
            ArtFrame("""
                X   X   X
               X  X X  X
              X X X X X
            """, Fore.RED, 0.2),
        ],
        
        "level_up": [
            ArtFrame("""
                    *
            """, Fore.YELLOW, 0.15),
            ArtFrame("""
                  * * *
                    *
            """, Fore.LIGHTYELLOW_EX, 0.15),
            ArtFrame("""
                *   *   *
                  * * *
                    *
                  * * *
                *   *   *
            """, Fore.YELLOW, 0.15),
        ],
        
        "radiation_pulse": [
            ArtFrame("""
                    !
            """, Fore.GREEN, 0.2),
            ArtFrame("""
                  ~ ! ~
            """, Fore.LIGHTGREEN_EX, 0.2),
            ArtFrame("""
                ~ ~ ~ ~ ~
                  ~ ! ~
                ~ ~ ~ ~ ~
            """, Fore.GREEN, 0.2),
        ],
    }
    
    # Enhanced location art with detail
    DETAILED_LOCATIONS = {
        "brandenburg_gate": """
                    |  |  |  |  |  |
                  ______________________
                 |  _______________     |
                 | |  ___________  |    |
                 | | |           | |    |
                 | | |  BERLIN   | |    |
                 | | |___________| |    |
                 | |_______________     |
                 |______________________|
                    |     |  |     |
                    |     |  |     |
               _____|_____|__|_____|_____
        """,
        
        "fernsehturm_detailed": r"""
                      ▲
                      |
                     /H\
                    |HHH|
                     \H/
                      |
                    {===}
                      |
                     /|\
                    / | \
                   /  |  \
                  /   |   \
                 /_________\
                |           |
                |    TV     |
                |   TOWER   |
                |___________|
        """,
        
        "checkpoint_charlie_scene": """
         ═══════════════════════════════════════
         ║  YOU ARE NOW LEAVING              ║
         ║     THE AMERICAN SECTOR           ║
         ║  SIE VERLASSEN DEN AMERIKANISCHEN ║
         ║           SEKTOR                  ║
         ═══════════════════════════════════════
                    |           |
              ______|___________|______
             |                         |
             |    CHECKPOINT CHARLIE   |
             |      KONTROLLPUNKT      |
             |_________________________|
                    |           |
                  [###]       [###]
                    |           |
        """,
        
        "wasteland_scene": """
         ~  ~                              ~  ~
             ~    #                   #    ~
          ~         ....          ....
         +------+    ..     X     ..    +--+
         |      |=======================|  |
         |RUINS |                       +--+
         +------+     ..   ..   ..
              ..    ..  ..  ..  ..    ..
        """,
        
        "u_bahn_entrance": """
              ┌───────────────┐
              │   ║     ║     │
              │   U     B     │
              │               │
              └───────────────┘
                 │         │
              ═══╪═════════╪═══
                 │         │
               ┌─┴─────────┴─┐
               │   EINGANG   │
               │   ENTRANCE  │
               └─────────────┘
                    │  │
                    ▼  ▼
               ############
        """,
       
       "alexanderplatz_detailed": r"""
                    .||.
                    |  |
                ____|  |____
               /    |  |    \
              |     '--'     |
              |  [ Fernseh ]  |
              |  [  Turm   ]  |
               \____    ____/
                    |  |
                    |  |
             _______|__|_______
            /  U-BAHN RUINS    \
           |____________________|
       """,

       "reichstag_detailed": r"""
                   __________
                _ |  IRON    | _
               / \|  RING    |/ \
              |   |  BANNER  |   |
              |___|__________|___|
               | | | | | | | | |
              [=================]
              |  BRUTALIST STEEL |
              |  REINFORCEMENTS  |
              |__________________|
               |  |  |    |  |  |
              / \/ \/ \  / \/ \/ \
       """,

       "tiergarten_detailed": r"""
                \  /      \  /
                 \/        \/
              ---(MUTATED)---
                 /\ JUNGLE /\
                /  \      /  \
               /      ||      \
              |   GOLDENE FINGER |
              |     MONUMENT     |
               \______||______/
                 /    ||    \
                /     ||     \
       """,

       "victory_column_detailed": """
                    |
                   [ ]
                  /   \
                 |  G  |
                 |  O  |
                 |  L  |
                 |  D  |
                /       \
               [=========]
               |  VICTORY |
               |  COLUMN  |
               |  BERLIN  |
               |_________|
                | | | | |
               /=========\
       """,

       "kaiser_wilhelm_church_detailed": """
                    _
                   / \
                  /   \
                 | [ ] |
                 |  _  |
                 | | | |
               __| |_| |__
              /           \
             |   BROKEN    |
             |   STEEPLE   |
             |   (CHURCH)  |
             |_____________|
              | | | | | | |
       """,

       "teufelsberg_detailed": r"""
                     ___
                   /     \
                  |  ( )  |
                   \ ___ /
                     | |
                _____| |_____
               /             \
              |   RADAR       |
              |   STATION     |
              |   RUINS       |
              |               |
             /_________________\
            /   DEVIL'S HILL    \
       """,
    }
    
    # Combat art with variations (using simplified ASCII for compatibility)
    COMBAT_SCENES = {
        "melee_attack": """
              / \\
             |   |          --[=====>
             | |     --->
             |_|
        """,
        
        "ranged_attack": """
              / \\
             |   |
             | |     ===========>  #
             |_|                   *
        """,
        
        "critical_hit": """
             +---+   *
             | O |  /|\\ *
             +---+ *  *
               |
              ###     #### CRITICAL ####
        """,
        
        "enemy_defeated": """
                 X
               / | \\
              X  X  X
               \\ | /
                 X
        """,
    }
    
    # Enhanced enemy art
    DETAILED_ENEMIES = {
        "super_mutant_aggressive": """
              +--------+
              | O  O  |
              |   V    |
              +--------+
               ||  ||
              /||  ||\\
             * ||  || *
               ##  ##
        """,
        
        "ghoul_feral": """
              +---+
              |O O|
              | n |
              +---+
              /| |\\
             * | | *
              #| |#
        """,
        
        "radroach_swarm": """
           ▓▓  ▓▓  ▓▓
          O##O##O##
          #########
        """,
        
        "raider_boss": """
            ████████
            # O  O #
            █  ╱╲  █
            ████████
              ╱┃┃╲
          ▓▓▓╱ ┃┃ ╲▓▓▓
            ▓  ┃┃  ▓
              ▓▓▓▓
        """,
        "super_mutant_warlord": """
                 __________
                /  MUTANT  \\
               |  [ WARLORD ] |
               |   (X _ X)   |
                \\__________/
               /|  SCRAP   |\\
              / |  METAL   | \\
             |  |  ARMOR   |  |
             |__|__________|__|
                |  |    |  |
        """,

        "yao_guai": """
                 __      __
                /  \\____/  \\
               |  (◉)  (◉)  |
               |     ▲      |
                \\   _-_    /
                 |/     \\|
               /|  MUTATED  |\\
              | |   BEAR    | |
               \\|           |/
                '--'-----'--'
        """,

       "radroach_reworked": r"""
    ~   ~
     / \
    / _ \
   |/   \|
   |\   /|
   | \ / |
   |  v  |
    \ | /
     \|/
       """,

       "super_mutant_reworked": r"""
     /=======\
    /  [o]--. \
   /  / \   `\ \
  /  |   |    \ \
 |   |   |     |
 |  / \  |     |
/  /   \ |     |
|  /     \|     |
| |       |     |
\ \     /      /
 \ \___/      /
  \          /
   \________/
       """,

       "raider_reworked": r"""
     /=======\
    /  / \  \ \
   /  |o o|  \ \
  /   | V |   \ \
 /    |---|    \ \
       """,

       "ghoul_reworked": r"""
     /=======\
    /  (o). ( \
   /  /   \  `\ \
  /  |     |   \ \
 /   |     |    \ \
|    '.___.'     |
|     / \      |
/     /   \     |
|    |     |    |
|    |     |    |
\   '.___.'   /
 \           /
  \         /
   \_______/
       """,
    }
    
    # Status indicators
    STATUS_BARS = {
        "health_full": f"{Fore.GREEN}#####################{Style.RESET_ALL}",
        "health_high": f"{Fore.GREEN}################{Style.RESET_ALL}{Fore.BLACK}-----{Style.RESET_ALL}",
        "health_medium": f"{Fore.YELLOW}############{Style.RESET_ALL}{Fore.BLACK}---------{Style.RESET_ALL}",
        "health_low": f"{Fore.RED}#####{Style.RESET_ALL}{Fore.BLACK}################{Style.RESET_ALL}",
        "health_critical": f"{Fore.RED}##{Style.RESET_ALL}{Fore.BLACK}###################{Style.RESET_ALL}",
    }
    
    # Atmospheric elements
    ATMOSPHERE = {
        "dust_particles": f"{Fore.WHITE}. * . * . * . * .{Style.RESET_ALL}",
        "radiation_glow": f"{Fore.GREEN}... ! ...{Style.RESET_ALL}",
        "broken_lights": f"{Fore.YELLOW}O{Style.RESET_ALL} {Fore.BLACK}X{Style.RESET_ALL} {Fore.YELLOW}O{Style.RESET_ALL} {Fore.BLACK}X{Style.RESET_ALL}",
        "smoke": f"{Fore.WHITE}≈ ≋ ≈ ≋ ≈{Style.RESET_ALL}",
        "sparks": f"{Fore.YELLOW}✦ ✧ ✦ ✧{Style.RESET_ALL}",
    }
    
    # Interactive elements
    INTERACTIVE = {
        "terminal": """
        +-------------------+
        | ROBCO INDUSTRIES  |
        | (TM) TERMLINK     |
        |                   |
        | > _               |
        |                   |
        +-------------------+
        """,
        
        "locked_door": """
        +---------------+
        |     +---+     |
        |     | X |     |
        |     |###|     |
        |     +---+     |
        |  [  LOCKED  ] |
        +---------------+
        """,
        
        "loot_container": """
          +---------+
          | ....... |
          |.       .|
          |.  ?  ? .|
          |.   ?   .|
          | ....... |
          +---------+
        """,
    }


class SceneRenderer:
    """Renders complete scenes with multiple elements"""
    
    def __init__(self, width: int = 80, settings: Optional[Any] = None):
        self.width = width
        self.composer = ArtComposer()
        self.settings = settings
    
    def render_location_scene(self, location_id: str, weather: Optional[str] = None,
                             time_of_day: str = "day", pip_boy: bool = False) -> str:
        """Render a complete location scene with atmosphere and optional Pip-Boy styling"""
        
        # Priority for Iron Ring / Lore assets
        from fallout_berlin.art_berlin import BERLIN_ART
        
        art = ""
        if location_id in BERLIN_ART:
            art = BERLIN_ART[location_id]
        elif f"{location_id}_detailed" in AdvancedArtLibrary.DETAILED_LOCATIONS:
            art = AdvancedArtLibrary.DETAILED_LOCATIONS[f"{location_id}_detailed"]
        elif location_id in AdvancedArtLibrary.DETAILED_LOCATIONS:
            art = AdvancedArtLibrary.DETAILED_LOCATIONS[location_id]
        else:
            art = AdvancedArtLibrary.DETAILED_LOCATIONS.get("wasteland_scene", "")
        
        # Apply lighting
        flicker_enabled = True
        if self.settings:
            flicker_enabled = self.settings.get("ui", "flicker", True)
            if self.settings.get("accessibility", "disable_animations", False):
                flicker_enabled = False

        intensity = LightingManager.get_intensity(flicker=flicker_enabled)
        art = LightingManager.apply_lighting(art, intensity)

        # Apply color based on time of day
        if not pip_boy:
            if time_of_day == "night":
                art = f"{Fore.BLUE}{art}{Style.RESET_ALL}"
            elif time_of_day == "dusk":
                art = f"{Fore.MAGENTA}{art}{Style.RESET_ALL}"
            elif time_of_day == "dawn":
                art = f"{Fore.YELLOW}{art}{Style.RESET_ALL}"
            else:
                art = f"{Fore.WHITE}{art}{Style.RESET_ALL}"
        
        # Add weather effects
        scene_parts = []
        
        if weather == "rain":
            scene_parts.append(WeatherEffect.generate_rain(self.width, 4, intensity=0.4))
        elif weather == "radiation_storm":
            scene_parts.append(WeatherEffect.generate_radiation_storm(self.width, 4))
            WeatherEffect.play_audio_cue("alert")
        elif weather == "fog":
            scene_parts.append(WeatherEffect.generate_fog(self.width, 3))
        elif weather == "wind" or weather == "dust":
            scene_parts.append(WeatherEffect.generate_wind_dust(self.width, 4))
        
        # Overlay atmospheric particles on the art itself for better immersion
        dust = self.composer.center_text(AdvancedArtLibrary.ATMOSPHERE['dust_particles'], self.width)
        scene_parts.append(dust)
        scene_parts.append(art)
        
        # Combine everything
        result = '\n'.join(scene_parts)
        
        if pip_boy:
            try:
                from fallout_berlin.ui import PipBoyRenderer
            except (ImportError, ModuleNotFoundError):
                from .ui import PipBoyRenderer
            result = PipBoyRenderer.apply_theme(result, theme="green", scanlines=True, settings=self.settings)
            
        return result
    
    def render_combat_scene(self, player_health: int, enemy_name: str,
                          enemy_health: int, action: Optional[str] = None,
                          enemy_level: int = 1, player_level: int = 1) -> str:
        """Render a dynamic combat scene"""
        
        # Health bars
        player_hp_percent = player_health / 100
        enemy_hp_percent = enemy_health / 100
        
        player_bar = self._get_health_bar(player_hp_percent)
        enemy_bar = self._get_health_bar(enemy_hp_percent)

        # Danger indicator
        danger_tag = ""
        if enemy_level > player_level + 3:
            danger_tag = f" {Fore.RED}[!!!]{Style.RESET_ALL}"
        elif enemy_level > player_level:
            danger_tag = f" {Fore.YELLOW}[!]{Style.RESET_ALL}"
        
        # Enemy art
        enemy_art_key = f"{enemy_name.lower().replace(' ', '_')}"
        
        from fallout_berlin.art_berlin import BERLIN_ART

        enemy_art = BERLIN_ART.get(enemy_art_key)
        if not enemy_art:
            enemy_art = AdvancedArtLibrary.DETAILED_ENEMIES.get(
                enemy_art_key,
                AdvancedArtLibrary.DETAILED_ENEMIES.get("ghoul_feral", "")
            )

        # Color mapping for reworked enemies
        reworked_color_map = {
            "radroach_reworked": Fore.GREEN,
            "super_mutant_reworked": Fore.YELLOW,
            "raider_reworked": Fore.RED,
            "ghoul_reworked": Fore.WHITE,
        }

        reworked_enemy_art_key = f"{enemy_art_key}_reworked"
        if reworked_enemy_art_key in AdvancedArtLibrary.DETAILED_ENEMIES:
            enemy_art = AdvancedArtLibrary.DETAILED_ENEMIES[reworked_enemy_art_key]
            if reworked_enemy_art_key in reworked_color_map:
                enemy_art = f"{reworked_color_map[reworked_enemy_art_key]}{enemy_art}{Style.RESET_ALL}"
        
        # Action art
        action_art = ""
        if action:
            action_art = AdvancedArtLibrary.COMBAT_SCENES.get(action, "")
        
        # Compose scene
        scene = f"""
{SceneRenderer.render_combat_header("  COMBAT ENGAGEMENT: IRON RING PROTOCOL  ")}

{Fore.CYAN}PLAYER (LVL {player_level}){Style.RESET_ALL}
{player_bar}

{Fore.RED}{enemy_name.upper()} (LVL {enemy_level}){danger_tag}{Style.RESET_ALL}
{enemy_bar}

{self.composer.center_text(enemy_art, self.width)}

{self.composer.center_text(action_art, self.width) if action_art else ""}
        """
        
        return scene
    
    @staticmethod
    def render_combat_header(text: str) -> str:
        """Border style using # and X (barbed wire) for the Berlin Wall aesthetic"""
        lines = text.split('\n')
        width = max(len(line) for line in lines) + 8
        
        top = "#X" * (width // 2) + "#"
        bottom = "#X" * (width // 2) + "#"
        side = "##"
        
        result = [Fore.RED + top + Style.RESET_ALL]
        for line in lines:
            padded = line.center(width - 6)
            result.append(f"{Fore.RED}{side}{Style.RESET_ALL} {padded} {Fore.RED}{side}{Style.RESET_ALL}")
        result.append(Fore.RED + bottom + Style.RESET_ALL)
        
        return '\n'.join(result)

    def _get_health_bar(self, percent: float) -> str:
        """Generate a health bar based on percentage"""
        if percent > 0.8:
            return AdvancedArtLibrary.STATUS_BARS["health_full"]
        elif percent > 0.6:
            return AdvancedArtLibrary.STATUS_BARS["health_high"]
        elif percent > 0.4:
            return AdvancedArtLibrary.STATUS_BARS["health_medium"]
        elif percent > 0.2:
            return AdvancedArtLibrary.STATUS_BARS["health_low"]
        else:
            return AdvancedArtLibrary.STATUS_BARS["health_critical"]
    
    def render_dialogue_scene(self, npc_name: str, npc_art: str, dialogue: str) -> str:
        """Render a dialogue scene"""
        
        # Format dialogue with word wrap
        wrapped_dialogue = self._word_wrap(dialogue, 60)
        dialogue_box = self.composer.create_border(wrapped_dialogue, "single", Fore.CYAN)
        
        scene = f"""
{self.composer.center_text(npc_art, self.width)}

{Fore.YELLOW}{npc_name.upper()}{Style.RESET_ALL}
{dialogue_box}
        """
        
        return scene
    
    def _word_wrap(self, text: str, width: int) -> str:
        """Wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)


class BureaucracyRenderer:
    """Renders bureaucratic forms and Cold War terminal effects"""
    
    @staticmethod
    def render_form(content: str, fields: Optional[Dict[str, str]] = None) -> str:
        """Wraps content in a 27-B style form"""
        lines = content.split('\n')
        if fields:
            for key, value in fields.items():
                lines.append(f"{key.upper()}: {value}")
        
        width = max(len(line) for line in lines) + 6
        width = max(width, 30)
        
        top = " ___________________________ "
        header = "|  BEZIRKSAMT BERLIN        |"
        sub_header = "|  FORMULAR 27-B            |"
        divider = "|                           |"
        
        result = [Fore.WHITE + top + Style.RESET_ALL]
        result.append(Fore.WHITE + header.ljust(width) + "|" + Style.RESET_ALL)
        result.append(Fore.WHITE + sub_header.ljust(width) + "|" + Style.RESET_ALL)
        result.append(Fore.WHITE + divider.ljust(width) + "|" + Style.RESET_ALL)
        
        for line in lines:
            padded = f"|  {line}".ljust(width)
            result.append(Fore.WHITE + padded + "|" + Style.RESET_ALL)
            
        result.append(Fore.WHITE + "|___________________________|".ljust(width + 1, "_") + Style.RESET_ALL)
        
        return '\n'.join(result)

    @staticmethod
    def apply_glitch_effect(text: str, intensity: float = 0.05) -> str:
        """Occasional character swaps to simulate radiation/failing hardware"""
        chars = list(text)
        glitch_chars = ["@", "#", "$", "%", "&", "*", "!", "?", "0", "1"]
        
        for i in range(len(chars)):
            if chars[i] not in ["\n", " ", "|", "_", "[", "]"] and random.random() < intensity:
                chars[i] = random.choice(glitch_chars)
        
        return "".join(chars)

    @staticmethod
    def render_wall_border(text: str) -> str:
        """Border style using # and X (barbed wire) for the Berlin Wall aesthetic"""
        lines = text.split('\n')
        width = max(len(line) for line in lines) + 8
        
        top = "#X" * (width // 2) + "#"
        bottom = "#X" * (width // 2) + "#"
        side = "##"
        
        result = [Fore.RED + top + Style.RESET_ALL]
        for line in lines:
            padded = line.center(width - 6)
            result.append(f"{Fore.RED}{side}{Style.RESET_ALL} {padded} {Fore.RED}{side}{Style.RESET_ALL}")
        result.append(Fore.RED + bottom + Style.RESET_ALL)
        
        return '\n'.join(result)


class ArtEffects:
    """Special visual effects for game events"""
    
    @staticmethod
    def explosion_sequence() -> Animation:
        """Create explosion animation"""
        frames = [
            ArtFrame("""
                ·
            """, Fore.YELLOW, 0.1),
            ArtFrame("""
               · ·
              . O .
               · ·
            """, Fore.YELLOW, 0.1),
            ArtFrame("""
              · · ·
             . OOO .
            . OOOOO .
             . OOO .
              · · ·
            """, Fore.RED, 0.1),
            ArtFrame("""
             · · · ·
            · ~ ~ ~ ·
           · ~ ◇ ◇ ~ ·
            · ~ ~ ~ ·
             · · · ·
            """, Fore.WHITE, 0.15),
        ]
        return Animation(frames, loop=False)
    
    @staticmethod
    def healing_sequence() -> Animation:
        """Create healing animation (Stimpak use)"""
        frames = [
            ArtFrame("""
                  _
                 | |
                 | |
                 |_|
            """, Fore.WHITE, 0.15),
            ArtFrame("""
                  _
                 | |
                /---\\
               | [ ] |
                \\---/
            """, Fore.LIGHTWHITE_EX, 0.15),
            ArtFrame("""
                  _
                 | |
                /-S-\\
               | [=] |
                \\---/
            """, Fore.CYAN, 0.15),
            ArtFrame("""
                (  +  )
                 \\ | /
                -- + --
                 / | \\
                (  +  )
            """, Fore.LIGHTGREEN_EX, 0.2),
            ArtFrame("""
                   +
                 +   +
                   +
            """, Fore.GREEN, 0.2),
        ]
        return Animation(frames, loop=False)

    @staticmethod
    def looting_sequence() -> Animation:
        """Create looting animation"""
        frames = [
            ArtFrame("""
               _________
              |         |
              | [LOOT?] |
              |_________|
            """, Fore.YELLOW, 0.15),
            ArtFrame("""
               _________
              /        /|
             |________| |
             |  OPEN  |/
             |________|
            """, Fore.LIGHTYELLOW_EX, 0.15),
            ArtFrame("""
               _________
              /  _|_   /|
             |  (o o) | |
             |   -|-  |/
             |________|
            """, Fore.YELLOW, 0.15),
            ArtFrame("""
               _________
              /  $$$$  /|
             |  (v v) | |
             |   ---  |/
             |________|
            """, Fore.LIGHTCYAN_EX, 0.2),
            ArtFrame("""
                [ ITEM ]
                [ FOUND]
            """, Fore.CYAN, 0.2),
        ]
        return Animation(frames, loop=False)

    @staticmethod
    def lockpicking_sequence() -> Animation:
        """Create lockpicking animation"""
        frames = [
            ArtFrame("""
                [ ( O ) ]
                   /
                  /
            """, Fore.WHITE, 0.15),
            ArtFrame("""
                [ ( | ) ]
                  --
            """, Fore.LIGHTWHITE_EX, 0.15),
            ArtFrame("""
                [ ( \\ ) ]
                   \\
                    \\
            """, Fore.WHITE, 0.15),
            ArtFrame("""
                [ ( - ) ]
                  *TICK*
            """, Fore.YELLOW, 0.15),
            ArtFrame("""
                [ OPEN! ]
                 *CLICK*
            """, Fore.GREEN, 0.3),
        ]
        return Animation(frames, loop=False)

    @staticmethod
    def radiation_exposure() -> str:
        """Show radiation exposure effect"""
        return f"""
{Fore.GREEN}
    ! ! ! ! ! ! ! ! ! !
   ! ~ ~ ~ ~ ~ ~ ~ ~ ~ !
  !  RADIATION EXPOSURE  !
   ! ~ ~ ~ ~ ~ ~ ~ ~ ~ !
    ! ! ! ! ! ! ! ! ! !
{Style.RESET_ALL}
        """
    
    @staticmethod
    def level_up_splash() -> str:
        """Show level up effect"""
        return f"""
{Fore.YELLOW}
        +-------------------------+
        |                         |
        |   *** LEVEL UP! ***     |
        |                         |
        +-------------------------+
{Style.RESET_ALL}
        """

    @staticmethod
    def spree_swan_flap() -> Animation:
        """Create Spree Swan flapping animation"""
        try:
            from fallout_berlin.art_berlin import SPREE_SWAN_CHARM, SPREE_SWAN_FLAP
        except (ImportError, ModuleNotFoundError):
            try:
                from .art_berlin import SPREE_SWAN_CHARM, SPREE_SWAN_FLAP
            except (ImportError, ValueError):
                SPREE_SWAN_CHARM, SPREE_SWAN_FLAP = "", ""

        frames = [
            ArtFrame(SPREE_SWAN_CHARM, Fore.GREEN, 0.2),
            ArtFrame(SPREE_SWAN_FLAP, Fore.LIGHTGREEN_EX, 0.2),
        ]
        return Animation(frames, loop=True)

    @staticmethod
    def rad_wolf_wag() -> Animation:
        """Create Rad-Wolf tail wagging animation"""
        try:
            from fallout_berlin.art_berlin import RAD_WOLF, RAD_WOLF_WAG
        except (ImportError, ModuleNotFoundError):
            try:
                from .art_berlin import RAD_WOLF, RAD_WOLF_WAG
            except (ImportError, ValueError):
                RAD_WOLF, RAD_WOLF_WAG = "", ""

        frames = [
            ArtFrame(RAD_WOLF, Fore.YELLOW, 0.3),
            ArtFrame(RAD_WOLF_WAG, Fore.LIGHTYELLOW_EX, 0.3),
        ]
        return Animation(frames, loop=True)

    @staticmethod
    def level_up_charm() -> Animation:
        """Enhanced level up effect with Berlin stars and Currywurst icons"""
        frames = [
            ArtFrame("""
                   *
                (     )
                 )   (
               +-------+
               | LEVEL |
               |  UP!  |
               +-------+
            """, Fore.YELLOW, 0.2),
            ArtFrame("""
                *  [ ]  *
                (  *  )
                 ) * (
               +-------+
               | LEVEL |
               |  UP!  |
               +-------+
            """, Fore.LIGHTYELLOW_EX, 0.2),
            ArtFrame("""
               *   *   *
                ( CURRY )
                 ) WURST (
               +-------+
               | LEVEL |
               |  UP!  |
               +-------+
            """, Fore.YELLOW, 0.2),
        ]
        return Animation(frames, loop=False)

    @staticmethod
    def radiation_pulse() -> Animation:
        """Radiation pulse animation with green/lightgreen flicker"""
        frames = [
            ArtFrame("""
                ! ! ! ! !
                ~ ~ ~ ~ ~
                ! RAD !
                ~ ~ ~ ~ ~
                ! ! ! ! !
            """, Fore.GREEN, 0.15),
            ArtFrame("""
                ! ! ! ! !
                ~ ~ ~ ~ ~
                ! RAD !
                ~ ~ ~ ~ ~
                ! ! ! ! !
            """, Fore.LIGHTGREEN_EX, 0.15),
            ArtFrame("""
                ! ! ! ! !
                ~ ~ ~ ~ ~
                ! RAD !
                ~ ~ ~ ~ ~
                ! ! ! ! !
            """, Fore.GREEN, 0.15),
        ]
        return Animation(frames, loop=True)

    @staticmethod
    def radroach_twitch() -> Animation:
        """Create Radroach antenna twitch animation"""
        frames = [
            ArtFrame(r"""
     ~   ~
      / \
     / _ \
    |/   \|
    |\   /|
    | \ / |
    |  v  |
     \ | /
      \|/
            """, Fore.GREEN, 0.5),
            ArtFrame(r"""
     ´   ´
      / \
     / _ \
    |/   \|
    |\   /|
    | \ / |
    |  v  |
     \ | /
      \|/
            """, Fore.LIGHTGREEN_EX, 0.2),
        ]
        return Animation(frames, loop=True)

    @staticmethod
    def quest_complete() -> str:
        """Show quest completion"""
        return f"""
{Fore.CYAN}
    +-------------------------------+
    |  V  QUEST COMPLETED  V        |
    +-------------------------------+
{Style.RESET_ALL}
        """

    @staticmethod
    def title_animation() -> Animation:
        """Flickering neon Berlin title animation"""
        try:
            from fallout_berlin.art import TITLE
        except (ImportError, ModuleNotFoundError):
            try:
                from .art import TITLE
            except (ImportError, ValueError):
                TITLE = ""
        
        # Create frames with flickering elements
        # BERLIN is on line 32 of TITLE (index 31)
        lines = TITLE.split('\n')
        
        # Frame 1: Normal
        frame1_art = TITLE
        
        # Frame 2: "BERLIN" highlighted/flickering
        lines_flicker = lines.copy()
        if len(lines_flicker) > 32:
            original_line = lines_flicker[32]
            # Replace [ B E R L I N ] with a glowing version
            # Line 32: |       [ 2 2 8 7 ]       |||    [ B E R L I N ]      |
            flicker_line = original_line.replace("[ B E R L I N ]", f"{Fore.CYAN}[ B E R L I N ]{Style.RESET_ALL}{Fore.GREEN}")
            lines_flicker[32] = flicker_line
        frame2_art = '\n'.join(lines_flicker)

        # Frame 3: Dimmer
        frame3_art = TITLE

        frames = [
            ArtFrame(frame1_art, Fore.GREEN, 0.3),
            ArtFrame(frame2_art, Fore.GREEN, 0.1),
            ArtFrame(frame3_art, Fore.GREEN, 0.2),
            ArtFrame(frame2_art, Fore.LIGHTGREEN_EX, 0.05),
        ]
        
        return Animation(frames, loop=True)


# Demonstration function
def demonstrate_art_system():
    """Demonstrate the enhanced art system capabilities"""
    
    print("\n" + "="*80)
    print("FALLOUT BERLIN - ENHANCED ASCII ART SYSTEM DEMO")
    print("="*80 + "\n")
    
    # 1. Location Scene
    renderer = SceneRenderer()
    print("\n1. LOCATION SCENE WITH WEATHER AND PIP-BOY:")
    print(renderer.render_location_scene("alexanderplatz", weather="dust", time_of_day="day", pip_boy=True))
    time.sleep(2)

    # 1b. New Locations
    print("\n1b. NEW LOCATIONS (REICHSTAG):")
    print(renderer.render_location_scene("reichstag", weather="none", time_of_day="dusk"))
    time.sleep(2)
    
    # 2. Combat Scene
    print("\n2. COMBAT SCENE:")
    print(renderer.render_combat_scene(75, "Super Mutant", 60, action="ranged_attack"))
    time.sleep(2)
    
    # 3. Border Examples
    print("\n3. BORDER STYLES:")
    composer = ArtComposer()
    sample_text = "This is a sample\nmulti-line text\nwith borders"
    print(composer.create_border(sample_text, "double", Fore.CYAN))
    time.sleep(1)
    
    # 4. Animation
    print("\n4. NEW ANIMATIONS (HEALING):")
    healing = ArtEffects.healing_sequence()
    healing.play(clear_screen=False, use_lighting=True)
    time.sleep(1)

    print("\n4b. LOCKPICKING:")
    lockpick = ArtEffects.lockpicking_sequence()
    lockpick.play(clear_screen=False)
    time.sleep(1)
    
    # 5. Effects
    print("\n5. SPECIAL EFFECTS:")
    print(ArtEffects.level_up_splash())
    print(ArtEffects.quest_complete())
    print(ArtEffects.radiation_exposure())

    # 6. New Berlin Effects
    print("\n6. NEW BERLIN EFFECTS:")
    print("\n6a. SPREE SWAN FLAP:")
    ArtEffects.spree_swan_flap().play(clear_screen=False, use_lighting=True)
    
    print("\n6b. RAD-WOLF WAG:")
    ArtEffects.rad_wolf_wag().play(clear_screen=False, use_lighting=True)
    
    print("\n6c. LEVEL UP CHARM:")
    ArtEffects.level_up_charm().play(clear_screen=False, use_lighting=True)
    
    print("\n6d. RADIATION PULSE:")
    ArtEffects.radiation_pulse().play(clear_screen=False, use_lighting=True)
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    demonstrate_art_system()
