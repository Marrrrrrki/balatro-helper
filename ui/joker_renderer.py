
from pathlib import Path
import tkinter as tk

from PIL import Image, ImageTk


# Vanilla Balatro Joker sprite positions.
# Each position is (column, row) in Jokers.png.
JOKER_POSITIONS = {
    "j_8_ball": (0, 5),
    "j_abstract": (3, 3),
    "j_acrobat": (2, 1),
    "j_ancient": (7, 15),
    "j_arrowhead": (1, 8),
    "j_astronomer": (2, 7),
    "j_banner": (1, 2),
    "j_baron": (6, 12),
    "j_baseball": (6, 14),
    "j_blackboard": (2, 10),
    "j_bloodstone": (0, 8),
    "j_blue_joker": (7, 10),
    "j_blueprint": (0, 3),
    "j_bootstraps": (9, 8),
    "j_brainstorm": (7, 7),
    "j_bull": (7, 14),
    "j_burglar": (1, 10),
    "j_burnt": (3, 7),
    "j_business": (1, 4),
    "j_caino": (3, 8),
    "j_campfire": (5, 15),
    "j_card_sharp": (6, 11),
    "j_cartomancer": (7, 3),
    "j_castle": (9, 15),
    "j_cavendish": (5, 11),
    "j_ceremonial": (5, 5),
    "j_certificate": (8, 8),
    "j_chaos": (1, 0),
    "j_chicot": (6, 8),
    "j_clever": (2, 14),
    "j_cloud_9": (7, 12),
    "j_constellation": (9, 10),
    "j_crafty": (4, 14),
    "j_crazy": (5, 0),
    "j_credit_card": (5, 1),
    "j_delayed_grat": (4, 3),
    "j_devious": (3, 14),
    "j_diet_cola": (8, 14),
    "j_dna": (5, 10),
    "j_drivers_license": (0, 7),
    "j_droll": (6, 0),
    "j_drunkard": (1, 1),
    "j_duo": (5, 4),
    "j_dusk": (4, 7),
    "j_egg": (0, 10),
    "j_erosion": (5, 13),
    "j_even_steven": (8, 3),
    "j_faceless": (1, 11),
    "j_family": (7, 4),
    "j_fibonacci": (1, 5),
    "j_flash": (0, 15),
    "j_flower_pot": (0, 6),
    "j_fortune_teller": (7, 5),
    "j_four_fingers": (6, 6),
    "j_gift": (3, 13),
    "j_glass": (1, 3),
    "j_gluttenous_joker": (9, 1),
    "j_golden": (9, 2),
    "j_greedy_joker": (6, 1),
    "j_green_joker": (2, 11),
    "j_gros_michel": (7, 6),
    "j_hack": (5, 2),
    "j_half": (7, 0),
    "j_hallucination": (9, 13),
    "j_hanging_chad": (9, 6),
    "j_hiker": (0, 11),
    "j_hit_the_road": (8, 5),
    "j_hologram": (4, 12),
    "j_ice_cream": (4, 10),
    "j_idol": (6, 7),
    "j_invisible": (1, 7),
    "j_joker": (0, 0),
    "j_jolly": (2, 0),
    "j_juggler": (0, 1),
    "j_loyalty_card": (4, 2),
    "j_luchador": (1, 13),
    "j_lucky_cat": (5, 14),
    "j_lusty_joker": (7, 1),
    "j_mad": (4, 0),
    "j_madness": (8, 11),
    "j_mail": (7, 13),
    "j_marble": (3, 2),
    "j_matador": (4, 5),
    "j_merry_andy": (8, 0),
    "j_midas_mask": (0, 13),
    "j_mime": (4, 1),
    "j_misprint": (6, 2),
    "j_mr_bones": (3, 4),
    "j_mystic_summit": (2, 2),
    "j_obelisk": (9, 12),
    "j_odd_todd": (9, 3),
    "j_onyx_agate": (2, 8),
    "j_oops": (5, 6),
    "j_order": (8, 4),
    "j_pareidolia": (6, 3),
    "j_perkeo": (7, 8),
    "j_photograph": (2, 13),
    "j_popcorn": (1, 15),
    "j_raised_fist": (8, 2),
    "j_ramen": (2, 15),
    "j_red_card": (7, 11),
    "j_reserved_parking": (6, 13),
    "j_ride_the_bus": (1, 6),
    "j_riff_raff": (1, 12),
    "j_ring_master": (6, 5),
    "j_rocket": (8, 12),
    "j_rough_gem": (9, 7),
    "j_runner": (3, 10),
    "j_satellite": (8, 7),
    "j_scary_face": (2, 3),
    "j_scholar": (0, 4),
    "j_seance": (0, 12),
    "j_seeing_double": (4, 4),
    "j_selzer": (3, 15),
    "j_shoot_the_moon": (2, 6),
    "j_shortcut": (3, 12),
    "j_sixth_sense": (8, 10),
    "j_sly": (0, 14),
    "j_smeared": (4, 6),
    "j_smiley": (6, 15),
    "j_sock_and_buskin": (3, 1),
    "j_space": (3, 5),
    "j_splash": (6, 10),
    "j_square": (9, 11),
    "j_steel_joker": (7, 2),
    "j_stencil": (2, 5),
    "j_stone": (9, 0),
    "j_stuntman": (8, 6),
    "j_supernova": (2, 4),
    "j_superposition": (3, 11),
    "j_swashbuckler": (9, 5),
    "j_throwback": (5, 7),
    "j_ticket": (5, 3),
    "j_to_the_moon": (8, 13),
    "j_todo_list": (4, 11),
    "j_trading": (9, 14),
    "j_tribe": (9, 4),
    "j_triboulet": (4, 8),
    "j_trio": (6, 4),
    "j_troubadour": (0, 2),
    "j_trousers": (4, 15),
    "j_turtle_bean": (4, 13),
    "j_vagabond": (5, 12),
    "j_vampire": (2, 12),
    "j_walkie_talkie": (8, 15),
    "j_wee": (0, 0),
    "j_wily": (1, 14),
    "j_wrathful_joker": (8, 1),
    "j_yorick": (5, 8),
    "j_zany": (3, 0),
}


class JokerRenderer:
    def __init__(self, root):
        self.root = root
        self.atlas = None
        self.available = False

        self.cell_width = 71
        self.cell_height = 95

        self._load_atlas()

    def _load_atlas(self):
        project_root = Path(__file__).resolve().parent.parent
        atlas_path = project_root / "assets" / "Jokers.png"

        if not atlas_path.exists():
            return

        try:
            self.atlas = Image.open(atlas_path).convert("RGBA")

            width, height = self.atlas.size

            # Support both 1x and 2x game textures.
            if width >= 710 * 2 and height >= 1520 * 2:
                self.cell_width = 142
                self.cell_height = 190

            self.available = True

        except Exception:
            self.atlas = None
            self.available = False

    def get_joker_image(self, joker, size=1.0):
        if not self.available:
            return None

        save_fields = joker.get("save_fields", {}) or {}
        center = save_fields.get("center", "")

        position = JOKER_POSITIONS.get(center)

        if position is None:
            return None

        column, row = position

        x1 = column * self.cell_width
        y1 = row * self.cell_height
        x2 = x1 + self.cell_width
        y2 = y1 + self.cell_height

        try:
            sprite = self.atlas.crop((x1, y1, x2, y2))

            # Use a solid white background behind transparent pixels.
            white = Image.new(
                "RGBA",
                sprite.size,
                (255, 255, 255, 255),
            )
            white.alpha_composite(sprite)
            sprite = white

            if size != 1.0:
                new_size = (
                    int(71 * size),
                    int(95 * size),
                )
                sprite = sprite.resize(
                    new_size,
                    Image.Resampling.NEAREST,
                )

            return ImageTk.PhotoImage(sprite, master=self.root)

        except Exception:
            return None
