
from __future__ import annotations

from copy import deepcopy


# Per-level increases used by vanilla Balatro. Arm removes one level's
# worth of chips and Mult from the played hand.
LEVEL_INCREASES = {
    "High Card": (10, 1),
    "Pair": (15, 1),
    "Two Pair": (20, 1),
    "Three of a Kind": (20, 2),
    "Straight": (30, 3),
    "Flush": (15, 2),
    "Full House": (25, 2),
    "Four of a Kind": (30, 3),
    "Straight Flush": (40, 4),
    "Five of a Kind": (35, 3),
    "Flush House": (40, 4),
    "Flush Five": (50, 3),
}

KNOWN_UNSIMULATED = {
    "bl_hook": "The Hook discards cards after a hand is played.",
    "bl_ox": "The Ox changes your money when you play a specific hand.",
    "bl_house": "The House can hide cards face down.",
    "bl_wall": "The Wall changes the blind target; its target is read from the save.",
    "bl_wheel": "The Wheel can hide cards face down.",
    "bl_mark": "The Mark can hide face cards face down.",
    "bl_needle": "The Needle limits the number of hands.",
    "bl_water": "The Water removes your discards.",
    "bl_eye": "The Eye prevents repeating hand types.",
    "bl_mouth": "The Mouth restricts the hand type you can play.",
    "bl_pillar": "The Pillar debuffs cards played earlier in the ante.",
    "bl_serpent": "The Serpent changes card draws after plays and discards.",
    "bl_pillar": "The Pillar needs a history of cards played earlier in the ante.",
    "bl_crimson_heart": "Crimson Heart disables a Joker during the round.",
    "bl_cerulean_bell": "Cerulean Bell forces a card selection.",
    "bl_verdant_leaf": "Verdant Leaf debuffs cards until a Joker is sold.",
    "bl_amber_acorn": "Amber Acorn shuffles Joker order.",
    "bl_violet_vessel": "Violet Vessel changes the blind target; its target is read from the save.",
}


def _normalise(value):
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def get_blind_rules(state):
    """Return the boss-blind rules that can be safely inferred from the save."""
    name = str(state.get("blind_name") or "Unknown blind")
    key = _normalise(state.get("blind_key"))

    if not key:
        key = "bl_" + _normalise(name)

    rules = {
        "key": key,
        "name": name,
        "exact_cards": None,
        "chip_factor": 1.0,
        "mult_factor": 1.0,
        "level_delta": 0,
        "debuffed_suits": set(),
        "debuff_faces": False,
        "description": "",
        "warning": "",
    }

    if key == "bl_psychic" or _normalise(name) == "psychic":
        rules["exact_cards"] = 5
        rules["description"] = "Psychic: you must play exactly 5 cards."

    elif key == "bl_flint" or _normalise(name) == "flint":
        rules["chip_factor"] = 0.5
        rules["mult_factor"] = 0.5
        rules["description"] = "Flint: base hand Chips and Mult are halved."

    elif key == "bl_arm" or _normalise(name) == "the_arm":
        rules["level_delta"] = -1
        rules["description"] = "The Arm: the played poker hand loses 1 level."

    elif key == "bl_goad" or _normalise(name) == "the_goad":
        rules["debuffed_suits"].add("Spades")
        rules["description"] = "The Goad: Spades are debuffed."

    elif key == "bl_head" or _normalise(name) == "the_head":
        rules["debuffed_suits"].add("Hearts")
        rules["description"] = "The Head: Hearts are debuffed."

    elif key == "bl_window" or _normalise(name) == "the_window":
        rules["debuffed_suits"].add("Diamonds")
        rules["description"] = "The Window: Diamonds are debuffed."

    elif key == "bl_club" or _normalise(name) == "the_club":
        rules["debuffed_suits"].add("Clubs")
        rules["description"] = "The Club: Clubs are debuffed."

    elif key == "bl_plant" or _normalise(name) == "the_plant":
        rules["debuff_faces"] = True
        rules["description"] = "The Plant: face cards are debuffed."

    elif key in KNOWN_UNSIMULATED:
        rules["warning"] = KNOWN_UNSIMULATED[key]

    else:
        # Don't silently claim an unidentified blind has been simulated.
        if key.startswith("bl_") and key not in ("bl_small", "bl_big"):
            rules["warning"] = (
                f"{name} is not currently simulated. "
                "The recommendation may not account for its special rule."
            )

    return rules


def card_is_blind_debuffed(card, rules):
    if card.get("debuff"):
        return True

    if card.get("suit") in rules.get("debuffed_suits", set()):
        return True

    if rules.get("debuff_faces"):
        rank = card.get("rank")
        try:
            if int(rank) in (11, 12, 13):
                return True
        except (TypeError, ValueError):
            pass

    return False


def apply_blind_to_levels(hand_levels, rules):
    """Make a safe copy of hand levels and apply The Arm if active."""
    levels = deepcopy(hand_levels or {})

    if rules.get("level_delta") >= 0:
        return levels

    for hand_name, level_data in levels.items():
        if not isinstance(level_data, dict):
            continue

        chips_per_level, mult_per_level = LEVEL_INCREASES.get(
            hand_name, (None, None)
        )

        if chips_per_level is None:
            continue

        level_data["chips"] = max(
            0, float(level_data.get("chips", 0) or 0) - chips_per_level
        )
        level_data["mult"] = max(
            0, float(level_data.get("mult", 0) or 0) - mult_per_level
        )
        level_data["level"] = max(
            1, int(level_data.get("level", 1) or 1) - 1
        )

    return levels
