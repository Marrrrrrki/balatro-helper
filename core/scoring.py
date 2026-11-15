
from __future__ import annotations

from .boss_blinds import card_is_blind_debuffed


JOKER_SIMPLE = {
    "j_joker": ("add_mult", 4),
    "j_greedy": ("suit_mult", ("Diamonds", 3)),
    "j_lusty": ("suit_mult", ("Hearts", 3)),
    "j_wrathful": ("suit_mult", ("Spades", 3)),
    "j_gluttenous": ("suit_mult", ("Clubs", 3)),

    "j_jolly": ("conditional_mult", ("Pair", 8)),
    "j_zany": ("conditional_mult", ("Three of a Kind", 12)),
    "j_mad": ("conditional_mult", ("Two Pair", 10)),
    "j_crazy": ("conditional_mult", ("Straight", 12)),
    "j_droll": ("conditional_mult", ("Flush", 10)),

    "j_sly": ("conditional_chips", ("Pair", 50)),
    "j_wily": ("conditional_chips", ("Three of a Kind", 100)),
    "j_clever": ("conditional_chips", ("Two Pair", 80)),
    "j_devious": ("conditional_chips", ("Straight", 100)),
    "j_crafty": ("conditional_chips", ("Flush", 80)),

    "j_half": ("max_cards_mult", (3, 20)),
    "j_abstract": ("joker_count_mult", 3),
    "j_banner": ("discard_chips", 30),
    "j_mystic_summit": ("no_discards_mult", 15),
    "j_blue_joker": ("deck_chips", 2),

    "j_even_steven": ("even_mult", 4),
    "j_odd_todd": ("odd_chips", 31),
    "j_scholar": ("ace_bonus", (20, 4)),
    "j_fibonacci": ("fibonacci_mult", 8),
    "j_walkie_talkie": ("walkie_bonus", (10, 4)),
    "j_smiley": ("face_mult", 5),

    "j_splash": ("all_cards_score", True),
}

FIBONACCI_RANKS = {2, 3, 5, 8, 14}
EVEN_RANKS = {2, 4, 6, 8, 10}
ODD_RANKS = {3, 5, 7, 9, 14}
FACE_RANKS = {11, 12, 13}


def card_chips(card):
    if card.get("enhancement") == "m_stone":
        return 50

    rank = int(card.get("rank", 0) or 0)
    base = 11 if rank == 14 else 10 if rank >= 10 else rank

    ability = card.get("ability", {}) or {}

    return (
        base
        + int(ability.get("bonus", 0) or 0)
        + int(ability.get("perma_bonus", 0) or 0)
    )


def score_hand(
    selected,
    evaluation,
    hand_levels,
    jokers=None,
    held_cards=None,
    remaining_discards=None,
    remaining_deck=None,
    details=True,
    blind_rules=None,
):
    """
    Calculate a Balatro hand score.

    blind_rules is optional so existing callers remain compatible.
    """
    jokers = jokers or []
    held_cards = held_cards or []
    blind_rules = blind_rules or {}

    name = evaluation["name"]
    level = (hand_levels or {}).get(name, {}) or {}

    chips = float(level.get("chips", 0) or 0)
    mult = float(level.get("mult", 0) or 0)

    # Flint halves the base hand values before card and Joker effects.
    chips *= float(blind_rules.get("chip_factor", 1.0))
    mult *= float(blind_rules.get("mult_factor", 1.0))

    scoring = list(evaluation["scoring_cards"])
    notes = []

    if details:
        notes.append(
            f"{name} level {level.get('level', 1)}: "
            f"{chips:g} chips × {mult:g} mult"
        )

        description = blind_rules.get("description")
        if description:
            notes.append(description)

        warning = blind_rules.get("warning")
        if warning:
            notes.append(f"BLIND WARNING: {warning}")

    # Splash makes every played card score, except debuffed cards.
    if any(
        (joker.get("save_fields") or {}).get("center") == "j_splash"
        and not joker.get("debuff")
        for joker in jokers
    ):
        scoring = list(selected)

        if details:
            notes.append("Splash: All played cards score")

    # Playing card effects.
    for card in scoring:
        if card_is_blind_debuffed(card, blind_rules):
            continue

        chips += card_chips(card)

        enhancement = card.get("enhancement", "Base")

        if enhancement == "m_bonus":
            chips += 30
            if details:
                notes.append(f"{card['name']}: Bonus +30 chips")

        elif enhancement == "m_mult":
            mult += 4
            if details:
                notes.append(f"{card['name']}: Mult +4")

        elif enhancement == "m_glass":
            mult *= 2
            if details:
                notes.append(f"{card['name']}: Glass ×2 mult")

        edition = card.get("edition")

        if edition == "foil":
            chips += 50
            if details:
                notes.append(f"{card['name']}: Foil +50 chips")

        elif edition == "holo":
            mult += 10
            if details:
                notes.append(f"{card['name']}: Holographic +10 mult")

        elif edition == "polychrome":
            mult *= 1.5
            if details:
                notes.append(f"{card['name']}: Polychrome ×1.5 mult")

    # Held card effects.
    for card in held_cards:
        if card_is_blind_debuffed(card, blind_rules):
            continue

        if card.get("enhancement") == "m_steel":
            mult *= 1.5
            if details:
                notes.append(f"{card['name']}: Steel ×1.5 mult")

    # Process Jokers from left to right.
    unsupported = []

    for joker in jokers:
        if joker.get("debuff"):
            continue

        key = (joker.get("save_fields") or {}).get("center", "")
        effect = JOKER_SIMPLE.get(key)

        if not effect:
            if details:
                unsupported.append(
                    joker.get("label") or key or "Unknown Joker"
                )
            continue

        kind, value = effect

        if kind == "add_mult":
            mult += value
            if details:
                notes.append(f"Joker: +{value} mult")

        elif kind == "suit_mult":
            suit, amount = value
            count = sum(
                1 for card in scoring
                if card.get("suit") == suit
                and not card_is_blind_debuffed(card, blind_rules)
            )

            if count:
                mult += count * amount
                if details:
                    notes.append(
                        f"Joker: +{count * amount} mult "
                        f"({count} {suit})"
                    )

        elif kind == "conditional_mult":
            required_hand, amount = value
            if name == required_hand:
                mult += amount
                if details:
                    notes.append(f"Joker: +{amount} mult")

        elif kind == "conditional_chips":
            required_hand, amount = value
            if name == required_hand:
                chips += amount
                if details:
                    notes.append(f"Joker: +{amount} chips")

        elif kind == "max_cards_mult":
            max_cards, amount = value
            if len(selected) <= max_cards:
                mult += amount
                if details:
                    notes.append(f"Joker: +{amount} mult")

        elif kind == "joker_count_mult":
            amount = len(jokers) * value
            mult += amount
            if details:
                notes.append(f"Abstract: +{amount} mult")

        elif kind == "discard_chips":
            if remaining_discards is not None:
                amount = max(0, int(remaining_discards)) * value
                chips += amount
                if details and amount:
                    notes.append(f"Banner: +{amount} chips")

        elif kind == "no_discards_mult":
            if remaining_discards == 0:
                mult += value
                if details:
                    notes.append(f"Mystic Summit: +{value} mult")

        elif kind == "deck_chips":
            if remaining_deck is not None:
                amount = max(0, int(remaining_deck)) * value
                chips += amount
                if details and amount:
                    notes.append(f"Blue Joker: +{amount} chips")

        elif kind == "even_mult":
            count = sum(
                1 for card in scoring
                if card.get("rank") in EVEN_RANKS
                and not card_is_blind_debuffed(card, blind_rules)
            )
            if count:
                mult += count * value
                if details:
                    notes.append(f"Even Steven: +{count * value} mult")

        elif kind == "odd_chips":
            count = sum(
                1 for card in scoring
                if card.get("rank") in ODD_RANKS
                and not card_is_blind_debuffed(card, blind_rules)
            )
            if count:
                chips += count * value
                if details:
                    notes.append(f"Odd Todd: +{count * value} chips")

        elif kind == "ace_bonus":
            chip_bonus, mult_bonus = value
            count = sum(
                1 for card in scoring
                if card.get("rank") == 14
                and not card_is_blind_debuffed(card, blind_rules)
            )
            if count:
                chips += count * chip_bonus
                mult += count * mult_bonus
                if details:
                    notes.append(
                        f"Scholar: +{count * chip_bonus} chips "
                        f"and +{count * mult_bonus} mult"
                    )

        elif kind == "fibonacci_mult":
            count = sum(
                1 for card in scoring
                if card.get("rank") in FIBONACCI_RANKS
                and not card_is_blind_debuffed(card, blind_rules)
            )
            if count:
                mult += count * value
                if details:
                    notes.append(f"Fibonacci: +{count * value} mult")

        elif kind == "walkie_bonus":
            chip_bonus, mult_bonus = value
            count = sum(
                1 for card in scoring
                if card.get("rank") in (4, 10)
                and not card_is_blind_debuffed(card, blind_rules)
            )
            if count:
                chips += count * chip_bonus
                mult += count * mult_bonus
                if details:
                    notes.append(
                        f"Walkie Talkie: +{count * chip_bonus} chips "
                        f"and +{count * mult_bonus} mult"
                    )

        elif kind == "face_mult":
            count = sum(
                1 for card in scoring
                if card.get("rank") in FACE_RANKS
                and not card_is_blind_debuffed(card, blind_rules)
            )
            if count:
                mult += count * value
                if details:
                    notes.append(f"Smiley Face: +{count * value} mult")

    score = max(0, int(round(chips * mult)))

    return {
        "chips": chips,
        "mult": mult,
        "score": score,
        "notes": notes,
        "unsupported_jokers": unsupported,
        "accuracy": "Partial" if unsupported else "Core effects only",
    }
