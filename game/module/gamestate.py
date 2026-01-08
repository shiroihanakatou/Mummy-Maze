import pygame, sys, random
from pathlib import Path
from pygame.locals import *
from variable import *

def slice_sheet(sheet_surf, frame_count):
    """Slice sprite sheet into individual frames."""
    w, h = sheet_surf.get_size()
    fw = w // frame_count
    frames = []
    for i in range(frame_count):
        r = pygame.Rect(i * fw, 0, fw, h)
        frames.append(sheet_surf.subsurface(r).copy())
    return frames

def load_frames_with_mask(color_path, mask_path, frame_count):
    """Load sprite frames with alpha mask for transparency."""
    color_sheet = pygame.image.load(color_path).convert_alpha()
    mask_sheet = pygame.image.load(mask_path).convert_alpha()

    color_frames = slice_sheet(color_sheet, frame_count)
    mask_frames = slice_sheet(mask_sheet, frame_count)

    out_frames = []
    for c, m in zip(color_frames, mask_frames):
        c = c.convert_alpha()
        m = m.convert_alpha()

        out = pygame.Surface(c.get_size(), pygame.SRCALPHA, 32)
        out.blit(c, (0, 0))

        a = pygame.surfarray.array3d(m)[:, :, 0]
        out_a = pygame.surfarray.pixels_alpha(out)
        out_a[:, :] = a
        del out_a

        out_frames.append(out)

    return out_frames

class Gamestate:
    def __init__(self):
        self.mode = "classic"
        self.chapter = 1
        self.level = 1
        self.state = "Home"

        self.keys = set()
        self.traps = set()
        self.gates_h = {}
        self.has_key = False

        self.result = None
        self.gameover = False

        self.storedmove = []
        self.initpos = None
        self.pending_snapshot = False
        self.enemy_count = 1

        self.solution = []
        self.goal_row = ROWS - 1
        self.goal_col = COLS - 1
        
        # Initialize empty sfx dict (will be populated by _load_special_sprites)
        self.sfx = {}

        try:
            self.sprite_sheet = pygame.image.load(f"game/assets/images/stairs{ROWS}.png").convert_alpha()
        except Exception:
            self.sprite_sheet = pygame.image.load("game/assets/images/stairs6.png").convert_alpha()

        self._build_stairs_frames()
        self._load_special_sprites()

    def _load_special_sprites(self):
        """Load sprites for key, gate, and trap animations with masking (Phase 2)."""
        try:
            # Key: 36 frames horizontal with mask
            self.key_frames = load_frames_with_mask(
                "game/assets/images/key.gif",
                "game/assets/images/_key.gif",
                36
            )
            self.key_anim_idx = 0
            self.key_anim_timer = 0.0
            # print("[Gamestate] Key sprite loaded with mask (36 frames)")
        except Exception as e:
            print(f"[Gamestate] Key sprite load failed: {e}")
            self.key_frames = None

        try:
            # Gate: 8 frames horizontal (no mask available)
            gate_sheet = pygame.image.load("game/assets/images/gate6.gif").convert_alpha()
            self.gate_frames = slice_sheet(gate_sheet, 8)
            self.gate_anim_state = {}  # {(r, c): {"frame": idx, "time": t, "is_closing": bool}}
            # print("[Gamestate] Gate sprite loaded (8 frames)")
        except Exception as e:
            print(f"[Gamestate] Gate sprite load failed: {e}")
            self.gate_frames = None

        try:
            # Trap: 1 frame (static) with mask
            self.trap_frames = load_frames_with_mask(
                "game/assets/images/trap6.gif",
                "game/assets/images/_trap6.gif",
                1
            )
            # print("[Gamestate] Trap sprite loaded with mask (1 frame)")
        except Exception as e:
            print(f"[Gamestate] Trap sprite load failed: {e}")
            self.trap_frames = None

        # Phase 4: death assets
        try:
            self.expfall_frames = load_frames_with_mask(
                "game/assets/images/expfall6.gif",
                "game/assets/images/_expfall6.gif",
                4,
            )
            # print("[Gamestate] Expfall sprite loaded (4 frames)")
        except Exception as e:
            print(f"[Gamestate] Expfall sprite load failed: {e}")
            self.expfall_frames = None

        try:
            # Dark hole overlay for trap death
            self.floor_dark_frames = load_frames_with_mask(
                "game/assets/images/floordark6.jpg",
                "game/assets/images/_floordark6.gif",
                1,
            )
            # print("[Gamestate] Floor dark loaded")
        except Exception as e:
            print(f"[Gamestate] Floor dark load failed: {e}")
            self.floor_dark_frames = None

        try:
            self.dust_frames = load_frames_with_mask(
                "game/assets/images/dust6.gif",
                "game/assets/images/_dust6.gif",
                32,
            )
            # print("[Gamestate] Dust sprite loaded (32 frames)")
        except Exception as e:
            print(f"[Gamestate] Dust sprite load failed: {e}")
            self.dust_frames = None

        # Block trap + player freakout (new death type)
        try:
            # Block sheet has no separate alpha mask; slice directly
            block_sheet = pygame.image.load("game/assets/images/block6.gif").convert_alpha()
            self.block_frames = slice_sheet(block_sheet, 16)
            # print("[Gamestate] Block sprite loaded (10 frames)")
        except Exception as e:
            print(f"[Gamestate] Block sprite load failed: {e}")
            self.block_frames = None

        try:
            self.freakout_frames = load_frames_with_mask(
                "game/assets/images/freakout6.gif",
                "game/assets/images/_freakout6.gif",
                16,
            )
            # print("[Gamestate] Freakout sprite loaded (16 frames)")
        except Exception as e:
            print(f"[Gamestate] Freakout sprite load failed: {e}")
            self.freakout_frames = None

        try:
            self.red_fight_frames = load_frames_with_mask(
                "game/assets/images/redfight6.gif",
                "game/assets/images/_redfight6.gif",
                1,
            )
            self.white_fight_frames = load_frames_with_mask(
                "game/assets/images/whitefight6.gif",
                "game/assets/images/_whitefight6.gif",
                1,
            )
            self.stung_frames = load_frames_with_mask(
                "game/assets/images/stung6.gif",
                "game/assets/images/_stung6.gif",
                20,
            )
            # print("[Gamestate] Fight sprites loaded")
        except Exception as e:
            print(f"[Gamestate] Fight sprite load failed: {e}")
            self.red_fight_frames = self.white_fight_frames = self.stung_frames = None

        # Phase 5: Sound effects
        self._load_sound_effects()
        self.death_state = None

    def _load_sound_effects(self):
        """Load sound effects for gameplay events."""
        self.sfx = {}
        self.sfx_channels = {}
        base_dir = Path(__file__).resolve().parent.parent  # points to project root

        # Fallback list per sound; will try in order until one loads
        candidates = {
            # UI sounds
            "click": ["click.wav", "click.ogg", "click.mp3"],
            # Death sounds
            "pummel": ["pummel.mp3", "pummel.wav", "pummel.ogg"],          # red/white fight
            "poison": ["poison.wav", "poison.ogg", "poison.mp3"],          # scorpion sting
            "pit": ["pit.wav", "pit.ogg", "pit.mp3"],                     # trap death
            "badankh": ["badankh.wav", "badankh.ogg"],                      # mummy appears/spawn
            # Item/Gate sounds
            "gate": ["gate.wav", "gate.ogg", "gate.mp3"],                 # gate open/close
            "opentreasure": ["opentreasure.wav", "opentreasure.ogg"],       # pick up key
            "tombslide": ["tombslide.wav", "tombslide.ogg"],                # trap activation
            "block": ["block.wav", "block.ogg"],                            # collision/blocked
            # Win sound
            "finishedlevel": ["finishedlevel.wav", "finishedlevel.ogg", "finishedlevel.mp3"],
            # Footstep sounds (by grid size: 15, 30, 60 cells)
            "mumwalk_small": ["mumwalk15a.wav", "mumwalk15b.wav"],
            "mumwalk_medium": ["mumwalk30a.wav", "mumwalk30b.wav"],
            "mumwalk_large": ["mumwalk60a.wav", "mumwalk60b.wav"],
            "expwalk_small": ["expwalk15a.wav", "expwalk15b.wav"],
            "expwalk_medium": ["expwalk30a.wav", "expwalk30b.wav"],
            "expwalk_large": ["expwalk60a.wav", "expwalk60b.wav"],
            "scorpwalk": ["scorpwalk1.wav", "scorpwalk2.wav"],
            "mummyhowl": ["mummyhowl.wav"],                                 # enemy howl/alert
        }

        # print("[Gamestate] ===== Sound Loading Debug =====")
        for name, variants in candidates.items():
            loaded = False
            for fname in variants:
                path = base_dir / "assets" / "sounds" / fname
                # print(f"[Gamestate] Checking {name}: {path}")
                if not path.exists():
                    # print(f"[Gamestate]   -> File not found")
                    continue
                try:
                    from variable import BASE_SOUND_VOLUME
                    snd = pygame.mixer.Sound(str(path))
                    snd.set_volume(BASE_SOUND_VOLUME)
                    self.sfx[name] = snd
                    # print(f"[Gamestate]   -> LOADED from {fname}")
                    loaded = True
                    break
                except Exception as e:
                    pass  # print(f"[Gamestate]   -> Load error: {e}")
            if not loaded:
                self.sfx[name] = None
                # print(f"[Gamestate] {name}: FAILED - no valid file found")
        # print("[Gamestate] ===== Sound Loading Complete =====")

    def start_game(self):
        self.state = "PLAYING"

    def _build_stairs_frames(self):
        sheet_rect = self.sprite_sheet.get_rect()
        w = sheet_rect.width // 4
        h = sheet_rect.height

        stairs_location = {
            "up": pygame.Rect(0 * w, 0, w, h),
            "right": pygame.Rect(1 * w, 0, w, h),
            "down": pygame.Rect(2 * w, 0, w, h),
            "left": pygame.Rect(3 * w, 0, w, h),
        }

        self.stairs_frames = {}
        for k, r in stairs_location.items():
            img = self.sprite_sheet.subsurface(r).copy()
            # Left and right stairs get 20% taller
            if k in ["left", "right"]:
                self.stairs_frames[k] = pygame.transform.smoothscale(img, (CELL_SIZE, CELL_SIZE))
            else:
                self.stairs_frames[k] = pygame.transform.smoothscale(img, (CELL_SIZE, CELL_SIZE))

    def draw_stairs(self, surface):
        x = OFFSET_X + self.goal_col * CELL_SIZE
        y = OFFSET_Y + self.goal_row * CELL_SIZE

        if self.goal_row == 0:
            direction = "up"
        elif self.goal_row == ROWS - 1:
            direction = "down"
        elif self.goal_col == 0:
            direction = "left"
        else:
            direction = "right"

        frame = self.stairs_frames[direction]
        if direction == "up":
            stair_rect = pygame.Rect(x, y - CELL_SIZE+stair_padding, CELL_SIZE, CELL_SIZE)
        elif direction == "down":
            stair_rect = pygame.Rect(x, y + CELL_SIZE-stair_padding, CELL_SIZE, CELL_SIZE)
        elif direction == "left":
            stair_rect = pygame.Rect(x - CELL_SIZE+stair_padding, y, CELL_SIZE, CELL_SIZE)
        else: 
            stair_rect = pygame.Rect(x + CELL_SIZE-stair_padding, y, CELL_SIZE, CELL_SIZE)


        surface.blit(frame, stair_rect)

    def reset_items(self):
        self.keys.clear()
        self.traps.clear()
        self.gates_h.clear()
        self.has_key = False

    def set_gate_h(self, rh: int, c: int, is_open: bool):
        self.gates_h[(rh, c)] = bool(is_open)

    def get_gate_h(self, rh: int, c: int):
        return self.gates_h.get((rh, c), None)
