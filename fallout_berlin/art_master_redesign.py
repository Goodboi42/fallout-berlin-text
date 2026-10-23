"""
FALLOUT BERLIN - MASTER ART SYSTEM (REDESIGNED)
================================================
Complete redesign with cohesive, high-quality ASCII art for all locations and characters.
Focus: Distinctive Berlin landmarks, memorable character designs, consistent visual style.
"""

import time
import random
import os
from typing import List, Dict, Optional, Tuple
from colorama import Fore, Back, Style, init

# Initialize colorama
init()

# ==============================================================================
# LOCATION ART - AUTHENTIC BERLIN LANDMARKS
# ==============================================================================

LOCATIONS = {
    # ICONIC LANDMARKS
    "brandenburg_gate": r"""
            ⚐  ⚐  ⚐  ⚐  ⚐  ⚐
          ╔════════════════════╗
          ║  ╔══════════════╗  ║
          ║  ║  ╔════════╗  ║  ║
          ║  ║  ║ BERLIN ║  ║  ║
          ║  ║  ╚════════╝  ║  ║
          ║  ╚══════════════╝  ║
          ╠════════╦═╦════════╣
          ║        ║ ║        ║
          ║        ║ ║        ║
     ═════╩════════╩═╩════════╩═════
    """,
    
    "fernsehturm": r"""
                ▲
                █
               ╱█╲
              ╱ █ ╲
             ╱  █  ╲
            {═══█═══}
               ║█║
               ║█║
               ║█║
              ╱║█║╲
             ╱ ║█║ ╲
            ╱  ║█║  ╲
           ╱___║█║___╲
          │           │
          │   ALEX    │
          │  PLATZ    │
          └───────────┘
    """,
    
    "reichstag": r"""
          ╔═══════════════════╗
          ║   ┌─────────┐     ║
          ║   │ GLAS ▓▓ │     ║
          ║   │ DOME ▓▓ │     ║
          ║   └─────────┘     ║
          ╠═══════════════════╣
          ║ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ║
          ║ ║ ║ ║ ║ ║ ║ ║ ║ ║
          ║ ║ ║ ║ ║ ║ ║ ║ ║ ║
          ║ ╚═╝ ╚═╝ ╚═╝ ╚═╝ ║
          ╚═══════════════════╝
    """,
    
    "checkpoint_charlie": r"""
     ╔═══════════════════════════╗
     ║  YOU ARE NOW LEAVING      ║
     ║  THE AMERICAN SECTOR      ║
     ║  SIE VERLASSEN DEN        ║
     ║  AMERIKANISCHEN SEKTOR    ║
     ╚═══════════════════════════╝
            │           │
      ╔═════╪═══════════╪═════╗
      ║                       ║
      ║  CHECKPOINT  CHARLIE  ║
      ║  KONTROLLPUNKT ⚐      ║
      ╚═══════════════════════╝
            │           │
          ┌─┴─┐       ┌─┴─┐
          │███│       │███│
          └───┘       └───┘
    """,
    
    "east_side_gallery": r"""
    ╔═══════════════════════════╗
    ║ ░▒▓ MAUER ▓▒░            ║
    ║                           ║
    ║  ╔═══╗    ╔═══╗          ║
    ║  ║ ☮ ║    ║ ✊ ║          ║
    ║  ╚═══╝    ╚═══╝          ║
    ║                           ║
    ║  "DIE MAUER IST WEG"      ║
    ║  "THE WALL IS GONE"       ║
    ╚═══════════════════════════╝
    ════════════════════════════
    """,
    
    "alexanderplatz": r"""
              │
             ╱█╲
            ╱ █ ╲
           ╱  █  ╲
          {═══█═══}
             ║█║
    ╔════════╬█╬════════╗
    ║  ALEX  ║█║  PLATZ ║
    ║  ╔══╗  ║█║  ╔══╗  ║
    ║  ║  ║  ║█║  ║  ║  ║
    ╚══╩══╩══╩█╩══╩══╩══╝
       └──────┴──────┘
    """,
    
    # DISTRICTS & NEIGHBORHOODS
    "kreuzberg": r"""
       ┌─────────────────┐
       │   KREUZBERG     │
       │  ╔═══╗  ╔═══╗   │
       │  ║ ₺ ║  ║ € ║   │
       │  ╚═══╝  ╚═══╝   │
       │   DÖNER  SPÄTI  │
       └─────────────────┘
         │    │    │
       ╔═╧════╧════╧═╗
       ║ ORANIENSTR. ║
       ╚══════════════╝
    """,
    
    "wedding": r"""
     ╔══════════════════╗
     ║   WEDDING        ║
     ║  ╔╗ ╔╗ ╔╗ ╔╗     ║
     ║  ║║ ║║ ║║ ║║     ║
     ║  ╚╝ ╚╝ ╚╝ ╚╝     ║
     ║   RAIDER ZONE    ║
     ╚══════════════════╝
      \\    |    |    /
       \\   |    |   /
        ═══════════
    """,
    
    "neukolln": r"""
    ┌───────────────────┐
    │   NEUKÖLLN        │
    │  ╔══════════════╗ │
    │  ║ U-BAHN ▼▼▼   ║ │
    │  ║ ENTRANCE     ║ │
    │  ╚══════════════╝ │
    └───────────────────┘
          │      │
       ┌──┴──────┴──┐
       │  TUNNELS   │
       └────────────┘
    """,
    
    "tempelhofer_feld": r"""
    ════════════════════════════
     TEMPELHOFER FELD AIRFIELD
    ════════════════════════════
    ╔══════════════════════════╗
    ║  ╔══════════════════╗    ║
    ║  ║  RUNWAY 27L/09R  ║    ║
    ║  ╚══════════════════╝    ║
    ║   ✈        ✈        ✈    ║
    ║  HANGARS  FARMS  COMMUNE ║
    ╚══════════════════════════╝
    """,
    
    "potsdamer_platz": r"""
         ╔═══════════════╗
         ║ CRATER MARKET ║
         ╚═══════════════╝
           ╲           ╱
            ╲  ╔═══╗  ╱
             ╲ ║ ☢ ║ ╱
              ╲╚═══╝╱
               ╲   ╱
                ╲ ╱
          ═══════●═══════
          40m DEEP CRATER
    """,
    
    # UNDERGROUND LOCATIONS
    "u_bahn_tunnel": r"""
    ╔═══════════════════════════╗
    ║    ╔═══════════════╗      ║
    ║    ║  U-BAHN  ║ ║  ║      ║
    ║    ║          ║ ║  ║      ║
    ║    ╚═══════════════╝      ║
    ╚═══════════════════════════╝
         ║              ║
         ║ ▓▓▓▓▓▓▓▓▓▓ ║
         ║ TRACKS      ║
         ╚═════════════╝
    """,
    
    "stasi_museum": r"""
    ╔════════════════════════╗
    ║  NORMANNENSTRASSE 20   ║
    ║  ┌──────────────────┐  ║
    ║  │ MINISTRY für     │  ║
    ║  │ STAATSSICHERHEIT │  ║
    ║  │ [CLASSIFIED]     │  ║
    ║  └──────────────────┘  ║
    ║   ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼    ║
    ║   DEEP LEVELS BELOW    ║
    ╚════════════════════════╝
    """,
    
    "vault_entrance": r"""
        ╔═══════════════╗
        ║  VAULT-TEC    ║
        ║   ╔═════╗     ║
        ║   ║  ⚙  ║     ║
        ║   ║ ███ ║     ║
        ║   ╚═════╝     ║
        ║  SHELTER 101  ║
        ╚═══════════════╝
         ║           ║
         ╚═══════════╝
    """,
    
    # SPECIAL LOCATIONS
    "museum_island": r"""
       ╔═══════════════════╗
       ║  MUSEUM  INSEL    ║
       ║   ╔═══════════╗   ║
       ║   ║ PERGAMON  ║   ║
       ║   ║  ╔═══╗    ║   ║
       ║   ║  ║ ◉ ║ ←  ║   ║
       ║   ║  ╚═══╝    ║   ║
       ║   ║ NEFERTITI ║   ║
       ║   ╚═══════════╝   ║
       ╚═══════════════════╝
        ~ S P R E E ~
    """,
    
    "spandau_citadel": r"""
        ╔═══════════════╗
        ║ ┌───────────┐ ║
        ║ │   ╔═╗     │ ║
        ║ │   ║░║     │ ║
        ║ │   ╚═╝     │ ║
        ║ │ SPANDAU   │ ║
        ║ │ ZITADELLE │ ║
        ║ └───────────┘ ║
        ╚═══════════════╝
      ≈≈≈ MOAT ≈≈≈≈≈≈≈≈≈
    """,
    
    "oberbaumbucke": r"""
         ╔═══╗     ╔═══╗
         ║ ◐ ║     ║ ◐ ║
         ╚═╦═╝     ╚═╦═╝
    ═══════╩═════════╩═══════
    ────── BRIDGE ──────────
    ═════════════════════════
       ~ ~ S P R E E ~ ~
    """,
    
    "grunewald": r"""
       🌲  🌲  🌲  🌲  🌲
         🌲  🌲  🌲  🌲
       🌲  🌲  ☠  🌲  🌲
         🌲  🌲  🌲  🌲
       🌲  🌲  🌲  🌲  🌲
       DARK FOREST ZONE
       RADIATION: HIGH
    """,
    
    "tiergarten": r"""
    ╔═══════════════════════╗
    ║   TIERGARTEN RUINS    ║
    ║     🌲  ☠  🌲         ║
    ║  🌲  🌲  🌲  🌲  🌲   ║
    ║     SIEGESSÄULE       ║
    ║        ┌─┐            ║
    ║        │⚐│            ║
    ║        └─┘            ║
    ║   "GOLDENER FINGER"   ║
    ╚═══════════════════════╝
    """,
}

# ==============================================================================
# CHARACTER & ENEMY ART - DISTINCT DESIGNS
# ==============================================================================

ENEMIES = {
    # HUMAN ENEMIES
    "iron_ring_soldier": r"""
        ╔═══╗
        ║ ◉ ║
        ╚═══╝
        ╱┃┃╲
     ═══┃┃┃═══
       ┃┃┃┃┃
       ▓▓ ▓▓
    [POWER ARMOR]
    """,
    
    "iron_ring_officer": r"""
        ╔═══╗
        ║ ◎ ║
        ╚═╬═╝
         ║║
      ═══╬╬═══
        ║║║║
       ┃┃ ┃┃
      [OFFICER]
    """,
    
    "feld_commune_guard": r"""
        ┌───┐
        │ ● │
        └─┬─┘
          ║
       ───╬───
         ╱║╲
        ┃ ║ ┃
       [GUARD]
    """,
    
    "wall_breaker_raider": r"""
       ∩╱╲∩
       │ ◉ │
       └─╥─┘
      ╱  ║  ╲
     ●───╬───●
        ║║║
       ┃┃ ┃┃
     [RAIDER]
    """,
    
    "bundesritter_knight": r"""
        ╔═╗
        ║◎║
        ╚═╝
        ╱║╲
     ═══╬╬╬═══
       ║║║║║
       ┃┃ ┃┃
    [KNIGHT]
    """,
    
    "werkbund_merchant": r"""
        ┌───┐
        │ ◕ │
        └─┬─┘
      ┌───╬───┐
      │TOOLS  │
      └───────┘
        ┃   ┃
     [MERCHANT]
    """,
    
    # CREATURES
    "radhund": r"""
       ╱◥▓◣
      ┃◢●◤
      ┃ ┃╲
      ┗━┛ ╲
     ╱┃    ┃╲
    ● ┃    ┃ ●
    [RAD-HUND]
    """,
    
    "radhund_alpha": r"""
        ╱◥◥▓◣◣
       ┃◢◢●◤◤
       ┃ ┃┃╲╲
       ┗━━┛ ╲╲
      ╱┃┃    ┃┃╲
     ●● ┃┃    ┃┃ ●●
     [ALPHA RADHUND]
    """,
    
    "spreeschwan": r"""
          ≈
         ╱◐╲
        ╱   ╲
       │ ⋈ ⋈ │
       ╲     ╱
        ╲___╱
      ≈≈≈║║≈≈≈
     [SPREE SWAN]
    """,
    
    "radroach": r"""
       ╱ ╲ ╱ ╲
      │●▓▓▓●│
       ╲║║║╱
      ━━╬╬╬━━
       ┃┃ ┃┃
     [RADROACH]
    """,
    
    "super_mutant": r"""
       ╔═══╗
       ║ ◎ ║
       ║   ║
       ╚═══╝
      ╱║║║║╲
     ┃ ║║║║ ┃
     ● ║║║║ ●
       ▓▓▓▓
    [MUTANT]
    """,
    
    "feral_ghoul": r"""
       ╔═══╗
       ║ ● ║
       ╚═╦═╝
      ╱  ║  ╲
     ┃   ║   ┃
     ●   ║   ●
        ┃┃
     [GHOUL]
    """,
    
    "stasi_ghost": r"""
       ┌───┐
       │ ◉ │
       └─┬─┘
         ║
      ═══╬═══
        ╱║╲
       ┃ ║ ┃
    [STASI]
    """,
    
    "kanalratte": r"""
       ╱◥◣
      │ ● │
      │   │
      ╲▓▓▓╱
       ║║
    [RAT]
    """,
    
    "baumgeist": r"""
        🌲
       ╱│╲
      🌲 ● 🌲
       ╱│╲
      🌲 │ 🌲
        ╱╲
    [TREE-GHOST]
    """,
    
    "wildschwein": r"""
       ╱◥▓◣╲
      │ ●  ╱
      │   ╱
      ╲__╱
      ╱║║║╲
     ● ║║║ ●
    [BOAR]
    """,
}

# ==============================================================================
# NPC CHARACTER ART
# ==============================================================================

NPCS = {
    "generaloberst_von_stahl": r"""
        ╔═══╗
        ║ ◎ ║ ← HUMAN EYE
        ╚═╬═╝
      ━━━╬╬╬━━━ ← CYBERNETICS
        ▓║║║▓
        ▓▓▓▓▓
    [VON STAHL - 80% MACHINE]
    """,
    
    "mother_renate": r"""
        ┌───┐
        │ ◕ │
        └─┬─┘
      ╔═══╬═══╗
      ║ ROBES  ║
      ╚═══════╝
         ┃ ┃
    [MOTHER RENATE]
    """,
    
    "the_broker": r"""
        ╔═══════╗
        ║ ? ? ? ║
        ║   ?   ║
        ╚═══════╝
       [UNKNOWN]
    """,
    
    "jakob_drei_finger": r"""
        ┌───┐
        │ ◕ │
        └─┬─┘
      ┌───╬───┐
      │SUIT   │
      └───────┘
        ┃   ┃
     [DREI-FINGER]
    """,
    
    "schwertmeister": r"""
        ╔═╗
        ║◎║
        ╚═╝
        ╱║╲
     ═══╬╬╬═══
       ║║║║║
       ┃┃ ┃┃
    [SWORD MASTER]
    """,
    
    "radio_bela": r"""
        ┌─●─┐
        │ ◕ │ ← GAS MASK
        └─┬─┘
          ║
      ┌───╬───┐
      │HEADSET│
      └───────┘
    [RADIO BELA]
    """,
    
    "ticket_toni": r"""
        ┌───┐
        │ ◔ │
        └─┬─┘
      ┌───╬───┐
      │TICKETS│
      └───────┘
        ┃   ┃
    [TICKET-TONI]
    """,
    
    "oma_gertrude": r"""
        ┌───┐
        │ ◉ │
        └─┬─┘
          ║
     ═════╬═════
         ╱║╲
      🌺  ║  🔫
    [OMA GERTRUDE]
    """,
    
    "mehmet_mutant": r"""
       ╔═══╗
       ║ ◉ ║
       ║   ║
       ╚═══╝
      ╱║║║║╲
     ┃ ║║║║ ┃
      DÖNER STAND
    [MEHMET]
    """,
}

# ==============================================================================
# ITEMS & OBJECTS
# ==============================================================================

ITEMS = {
    "currywurst": r"""
      ╔═══════╗
      ║~~~~~~~║
      ║CURRY░░║
      ║WURST░░║
      ╚═══════╝
    """,
    
    "berliner_weisse": r"""
       ╔═╗
       ║ ║
       ║B║
       ║W║
       ╚═╝
    [BEER]
    """,
    
    "nuka_cola": r"""
       ╔═╗
       ║N║
       ║U║
       ║K║
       ║A║
       ╚═╝
    """,
    
    "form_27b": r"""
      ╔═════════╗
      ║ FORM    ║
      ║  27-B   ║
      ║─────────║
      ║│││││││││║
      ║│││││││││║
      ╚═════════╝
    """,
    
    "anmeldung": r"""
      ╔═════════╗
      ║ANMELDUNG║
      ║─────────║
      ║ NAME:   ║
      ║ ADDR:   ║
      ║ DATE:   ║
      ╚═════════╝
    """,
    
    "laser_pistol": r"""
      ═══╦═══►
         ║
    [LASER]
    """,
    
    "gauss_rifle": r"""
     ══════╦══════►
           ║
    [GAUSS RIFLE]
    """,
    
    "pipe_rifle": r"""
      ════╬════►
          ║
    [PIPE GUN]
    """,
    
    "power_armor": r"""
        ╔═══╗
        ║   ║
        ╚═╦═╝
      ════╬════
        ║║║║
       ┃┃ ┃┃
    [P-ARMOR]
    """,
    
    "stimpak": r"""
       ╔═╗
       ║+║
       ╚═╝
    [STIM]
    """,
    
    "rad_x": r"""
       ╔═╗
       ║☢║
       ╚═╝
    [RAD-X]
    """,
    
    "nefertiti_bust": r"""
        ╔═╗
       ╱ ◉ ╲
      │  ─  │
       ╲___╱
    [NEFERTITI]
    """,
    
    "trabant": r"""
      ╔═════╗
      ║ ◐ ◐ ║
      ╚═╦═╦═╝
        ║ ║
       ●●●●●
    [TRABANT]
    """,
}

# ==============================================================================
# UI ELEMENTS & SYMBOLS
# ==============================================================================

UI_ELEMENTS = {
    "pip_boy": r"""
    ┌───────────────┐
    │  ║ PIP-BOY ║  │
    │ ┌───────────┐ │
    │ │ ● HP: ██  │ │
    │ │ ☢ RAD: ░  │ │
    │ │ ⚡ AP: ███ │ │
    │ └───────────┘ │
    └───────────────┘
    """,
    
    "compass": r"""
        N
        ↑
    W ← ● → E
        ↓
        S
    """,
    
    "terminal": r"""
    ┌─────────────────┐
    │ ROBCO TERMLINK  │
    ├─────────────────┤
    │ >_              │
    │                 │
    │                 │
    └─────────────────┘
    """,
    
    "locked_door": r"""
    ╔═══════════╗
    ║  ┌─────┐  ║
    ║  │ [⊗] │  ║
    ║  │LOCKED│  ║
    ║  └─────┘  ║
    ╚═══════════╝
    """,
    
    "loot_container": r"""
    ┌───────────┐
    │ ┌───────┐ │
    │ │ ? ? ? │ │
    │ │  ???  │ │
    │ └───────┘ │
    └───────────┘
    """,
    
    "radiation_symbol": "☢",
    "bullet": "●",
    "star": "★",
    "warning": "⚠",
    "skull": "☠",
    "radioactive": "☢",
    "peace": "☮",
    "fist": "✊",
}

# ==============================================================================
# WEATHER & ATMOSPHERIC EFFECTS
# ==============================================================================

def generate_rain(width: int = 60, height: int = 5) -> str:
    """Generate rain effect"""
    rain_chars = ['│', '¦', '|', '/', '\\']
    lines = []
    for _ in range(height):
        line = ''.join(
            random.choice(rain_chars) if random.random() < 0.3 else ' '
            for _ in range(width)
        )
        lines.append(f"{Fore.BLUE}{line}{Style.RESET_ALL}")
    return '\n'.join(lines)

def generate_radiation_storm(width: int = 60, height: int = 5) -> str:
    """Generate radioactive storm"""
    rad_chars = ['☢', '≈', '~', '∿']
    lines = []
    for _ in range(height):
        line = ''.join(
            f"{random.choice([Fore.GREEN, Fore.YELLOW])}{random.choice(rad_chars)}{Style.RESET_ALL}"
            if random.random() < 0.2 else ' '
            for _ in range(width)
        )
        lines.append(line)
    return '\n'.join(lines)

def generate_fog(width: int = 60, height: int = 3) -> str:
    """Generate fog effect"""
    fog_chars = ['░', '▒', ' ', ' ']
    lines = []
    for _ in range(height):
        line = ''.join(random.choice(fog_chars) for _ in range(width))
        lines.append(f"{Fore.WHITE}{line}{Style.RESET_ALL}")
    return '\n'.join(lines)

def generate_dust(width: int = 60, height: int = 3) -> str:
    """Generate dust particles"""
    dust_chars = ['·', '˙', ' ', ' ', ' ']
    lines = []
    for _ in range(height):
        line = ''.join(random.choice(dust_chars) for _ in range(width))
        lines.append(f"{Fore.WHITE}{line}{Style.RESET_ALL}")
    return '\n'.join(lines)

# ==============================================================================
# ANIMATION SUPPORT CLASSES
# ==============================================================================

class ArtFrame:
    """Single frame of animation"""
    def __init__(self, art: str, color: str = Style.RESET_ALL, delay: float = 0.1):
        self.art = art
        self.color = color
        self.delay = delay
    
    def render(self) -> str:
        return f"{self.color}{self.art}{Style.RESET_ALL}"

class Animation:
    """Animation sequence"""
    def __init__(self, frames: List[ArtFrame], loop: bool = False):
        self.frames = frames
        self.loop = loop
    
    def play(self, clear_screen: bool = False, max_loops: int = 3):
        """Play animation"""
        loops = 0
        while True:
            for frame in self.frames:
                if clear_screen:
                    os.system('clear' if os.name != 'nt' else 'cls')
                print(frame.render())
                time.sleep(frame.delay)
            
            loops += 1
            if not self.loop or loops >= max_loops:
                break

# ==============================================================================
# COMPOSER & UTILITY FUNCTIONS
# ==============================================================================

class ArtComposer:
    """Compose and format ASCII art"""
    
    @staticmethod
    def center_text(text: str, width: int = 80) -> str:
        """Center text"""
        lines = text.split('\n')
        centered = []
        for line in lines:
            stripped = line.rstrip()
            padding = (width - len(stripped)) // 2
            centered.append(' ' * padding + stripped)
        return '\n'.join(centered)
    
    @staticmethod
    def create_border(text: str, style: str = "double", color: str = Fore.CYAN) -> str:
        """Add border around text"""
        lines = text.split('\n')
        width = max(len(line) for line in lines) + 4
        
        if style == "double":
            top = "╔" + "═" * (width - 2) + "╗"
            bottom = "╚" + "═" * (width - 2) + "╝"
            side = "║"
        elif style == "single":
            top = "┌" + "─" * (width - 2) + "┐"
            bottom = "└" + "─" * (width - 2) + "┘"
            side = "│"
        elif style == "heavy":
            top = "┏" + "━" * (width - 2) + "┓"
            bottom = "┗" + "━" * (width - 2) + "┛"
            side = "┃"
        else:
            top = "+" + "-" * (width - 2) + "+"
            bottom = "+" + "-" * (width - 2) + "+"
            side = "|"
        
        result = [f"{color}{top}{Style.RESET_ALL}"]
        for line in lines:
            padded = line.ljust(width - 4)
            result.append(f"{color}{side}{Style.RESET_ALL} {padded} {color}{side}{Style.RESET_ALL}")
        result.append(f"{color}{bottom}{Style.RESET_ALL}")
        
        return '\n'.join(result)

# ==============================================================================
# SPECIAL EFFECTS & ANIMATIONS
# ==============================================================================

class ArtEffects:
    """Special visual effects"""
    
    @staticmethod
    def explosion_sequence() -> Animation:
        """Explosion animation"""
        frames = [
            ArtFrame("     ·     ", Fore.YELLOW, 0.1),
            ArtFrame("   · ● ·   ", Fore.YELLOW, 0.1),
            ArtFrame(" · ● ◉ ● · ", Fore.RED, 0.1),
            ArtFrame("· ● ◉◉◉ ● ·", Fore.RED, 0.1),
            ArtFrame(" · ~ ~ ~ · ", Fore.WHITE, 0.15),
        ]
        return Animation(frames, loop=False)
    
    @staticmethod
    def level_up_sequence() -> Animation:
        """Level up celebration"""
        frames = [
            ArtFrame("    ★    ", Fore.YELLOW, 0.15),
            ArtFrame("  ★ ★ ★  ", Fore.YELLOW, 0.15),
            ArtFrame("★ ★ ★ ★ ★", Fore.YELLOW, 0.15),
            ArtFrame("""
    ╔═══════════╗
    ║ LEVEL UP! ║
    ╚═══════════╝
            """, Fore.YELLOW, 0.5),
        ]
        return Animation(frames, loop=False)
    
    @staticmethod
    def radiation_pulse() -> Animation:
        """Radiation exposure"""
        frames = [
            ArtFrame("    ☢    ", Fore.GREEN, 0.2),
            ArtFrame("  ~ ☢ ~  ", Fore.LIGHTGREEN_EX, 0.2),
            ArtFrame("~ ~ ☢ ~ ~", Fore.GREEN, 0.2),
        ]
        return Animation(frames, loop=True)
    
    @staticmethod
    def combat_start() -> Animation:
        """Combat initiation"""
        frames = [
            ArtFrame("    ⚔    ", Fore.RED, 0.2),
            ArtFrame("  ⚔ ⚔ ⚔  ", Fore.RED, 0.2),
            ArtFrame(" ⚔ ⚔ ⚔ ⚔ ", Fore.LIGHTRED_EX, 0.2),
        ]
        return Animation(frames, loop=False)
    
    @staticmethod
    def healing_effect() -> str:
        """Healing visual"""
        return f"""
{Fore.GREEN}
    +  +  +
  +  ❤  +
    +  +  +
{Style.RESET_ALL}
        """
    
    @staticmethod
    def quest_complete() -> str:
        """Quest completion"""
        return f"""
{Fore.CYAN}
╔═══════════════════════╗
║  ✓ QUEST COMPLETED ✓  ║
╚═══════════════════════╝
{Style.RESET_ALL}
        """
    
    @staticmethod
    def death_screen() -> str:
        """Game over"""
        return f"""
{Fore.RED}
╔═══════════════════════╗
║                       ║
║     ☠  YOU DIED  ☠    ║
║                       ║
╚═══════════════════════╝
{Style.RESET_ALL}
        """

# ==============================================================================
# SCENE RENDERER
# ==============================================================================

class SceneRenderer:
    """Render complete game scenes"""
    
    def __init__(self, width: int = 80):
        self.width = width
        self.composer = ArtComposer()
    
    def render_location(self, location_id: str, weather: Optional[str] = None,
                       time_of_day: str = "day", show_pip_boy: bool = False) -> str:
        """Render location scene"""
        # Get location art
        location_art = LOCATIONS.get(location_id, LOCATIONS.get("u_bahn_tunnel", ""))
        
        # Apply time coloring
        if time_of_day == "night":
            location_art = f"{Fore.BLUE}{location_art}{Style.RESET_ALL}"
        elif time_of_day == "dusk":
            location_art = f"{Fore.MAGENTA}{location_art}{Style.RESET_ALL}"
        else:
            location_art = f"{Fore.WHITE}{location_art}{Style.RESET_ALL}"
        
        # Build scene
        scene = []
        
        # Weather
        if weather == "rain":
            scene.append(generate_rain(self.width, 3))
        elif weather == "radiation_storm":
            scene.append(generate_radiation_storm(self.width, 3))
        elif weather == "fog":
            scene.append(generate_fog(self.width, 3))
        elif weather == "dust":
            scene.append(generate_dust(self.width, 2))
        
        # Location
        scene.append(self.composer.center_text(location_art, self.width))
        
        # Pip-Boy
        if show_pip_boy:
            scene.append("\n" + self.composer.center_text(UI_ELEMENTS["pip_boy"], self.width))
        
        return '\n'.join(scene)
    
    def render_combat(self, player_hp: int, enemy_name: str, enemy_hp: int,
                     action: Optional[str] = None) -> str:
        """Render combat scene"""
        # Get enemy art
        enemy_key = enemy_name.lower().replace(" ", "_").replace("-", "_")
        enemy_art = ENEMIES.get(enemy_key, ENEMIES.get("raider", ""))
        
        # Health bars
        player_bar = self._create_health_bar(player_hp, 100)
        enemy_bar = self._create_health_bar(enemy_hp, 100)
        
        # Build scene
        scene = f"""
{self.composer.create_border("⚔ COMBAT ⚔", "heavy", Fore.RED)}

{Fore.CYAN}PLAYER{Style.RESET_ALL}
{player_bar}

{Fore.RED}{enemy_name.upper()}{Style.RESET_ALL}
{enemy_bar}

{self.composer.center_text(enemy_art, self.width)}
        """
        
        # Add action
        if action:
            action_text = {
                "melee": ">>> MELEE ATTACK <<<",
                "ranged": "═══► SHOT FIRED ◄═══",
                "critical": "★★★ CRITICAL HIT! ★★★",
            }.get(action, "")
            
            if action_text:
                scene += f"\n{self.composer.center_text(action_text, self.width)}\n"
        
        return scene
    
    def _create_health_bar(self, current: int, maximum: int, length: int = 30) -> str:
        """Create health bar"""
        percent = current / maximum
        filled = int(length * percent)
        
        if percent > 0.6:
            color = Fore.GREEN
        elif percent > 0.3:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        
        bar = f"{color}{'█' * filled}{Fore.BLACK}{'█' * (length - filled)}{Style.RESET_ALL}"
        return f"[{bar}] {current}/{maximum}"

# ==============================================================================
# TITLE SCREEN
# ==============================================================================

TITLE_LOGO = r"""
███████╗ █████╗ ██╗     ██╗      ██████╗ ██╗   ██╗████████╗
██╔════╝██╔══██╗██║     ██║     ██╔═══██╗██║   ██║╚══██╔══╝
█████╗  ███████║██║     ██║     ██║   ██║██║   ██║   ██║   
██╔══╝  ██╔══██║██║     ██║     ██║   ██║██║   ██║   ██║   
██║     ██║  ██║███████╗███████╗╚██████╔╝╚██████╔╝   ██║   
╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝    ╚═╝   
    ██████╗ ███████╗██████╗ ██╗     ██╗███╗   ██╗          
    ██╔══██╗██╔════╝██╔══██╗██║     ██║████╗  ██║          
    ██████╔╝█████╗  ██████╔╝██║     ██║██╔██╗ ██║          
    ██╔══██╗██╔══╝  ██╔══██╗██║     ██║██║╚██╗██║          
    ██████╔╝███████╗██║  ██║███████╗██║██║ ╚████║          
    ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝          
"""

# ==============================================================================
# DEMO FUNCTION
# ==============================================================================

def demo():
    """Demonstrate the art system"""
    print(f"{Fore.GREEN}{TITLE_LOGO}{Style.RESET_ALL}")
    print("\n" + "=" * 80)
    print("FALLOUT BERLIN - REDESIGNED ART SYSTEM DEMO")
    print("=" * 80 + "\n")
    
    time.sleep(1)
    
    # Show locations
    print("\n1. ICONIC LANDMARKS:")
    renderer = SceneRenderer()
    
    for loc_id in ["brandenburg_gate", "fernsehturm", "checkpoint_charlie"]:
        print(f"\n{loc_id.upper().replace('_', ' ')}:")
        print(renderer.render_location(loc_id))
        time.sleep(2)
    
    # Show combat
    print("\n\n2. COMBAT SCENE:")
    print(renderer.render_combat(75, "radhund", 60, action="ranged"))
    time.sleep(2)
    
    # Show effects
    print("\n\n3. SPECIAL EFFECTS:")
    print("\nLevel Up:")
    ArtEffects.level_up_sequence().play(max_loops=1)
    time.sleep(1)
    
    print("\nExplosion:")
    ArtEffects.explosion_sequence().play()
    time.sleep(1)
    
    print("\n" + ArtEffects.quest_complete())
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    demo()
