from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False


class CardRenderer:
    """Loads and crops standard Balatro playing-card sprites."""

    CARD_WIDTH = 71
    CARD_HEIGHT = 95

    SUIT_ROWS = {
        "Spades": 0,
        "Hearts": 1,
        "Clubs": 2,
        "Diamonds": 3,
    }

    RANK_COLUMNS = {
        2: 0,
        3: 1,
        4: 2,
        5: 3,
        6: 4,
        7: 5,
        8: 6,
        9: 7,
        10: 8,
        11: 9,
        12: 10,
        13: 11,
        14: 12,
    }

    def __init__(self, root):
        self.root = root
        self.atlas_path = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "8BitDeck.png"
        )

        self.atlas = None
        self.cell_width = 0
        self.cell_height = 0
        self.error = None

        self._load_atlas()

    def _load_atlas(self):
        if not PIL_AVAILABLE:
            self.error = "Pillow is not installed."
            return

        if not self.atlas_path.exists():
            self.error = f"Card atlas not found: {self.atlas_path}"
            return

        try:
            self.atlas = Image.open(self.atlas_path).convert("RGBA")

            width, height = self.atlas.size

            if width >= 13 * 142 and height >= 4 * 190:
                self.cell_width = 142
                self.cell_height = 190
            elif width >= 13 * 71 and height >= 4 * 95:
                self.cell_width = 71
                self.cell_height = 95
            else:
                self.atlas = None
                self.error = (
                    "The atlas has an unexpected size. "
                    "Expected a 13 x 4 card grid."
                )

        except Exception as exc:
            self.atlas = None
            self.error = f"Could not load card atlas: {exc}"

    @property
    def available(self):
        return self.atlas is not None

    def get_card_image(self, card):
        if not self.available:
            return None

        try:
            rank = int(card.get("rank", 0))
            suit = str(card.get("suit", ""))

            if rank not in self.RANK_COLUMNS:
                return None

            if suit not in self.SUIT_ROWS:
                return None

            column = self.RANK_COLUMNS[rank]
            row = self.SUIT_ROWS[suit]

            x1 = column * self.cell_width
            y1 = row * self.cell_height
            x2 = x1 + self.cell_width
            y2 = y1 + self.cell_height

            sprite = self.atlas.crop((x1, y1, x2, y2))

            # Replace transparent pixels with solid white.
            white_background = Image.new(
                "RGBA",
                sprite.size,
                (255, 255, 255, 255),
)
            white_background.alpha_composite(sprite)
            sprite = white_background

            # Keep the original pixel-art style.
            sprite = sprite.resize(
                (self.CARD_WIDTH, self.CARD_HEIGHT),
                Image.Resampling.NEAREST,
            )

            return ImageTk.PhotoImage(sprite, master=self.root)

        except Exception:
            return None