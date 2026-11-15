from __future__ import annotations
from .evaluator import evaluate

# A deliberately explicit subset of vanilla Jokers. Unknown Jokers are reported,
# never silently treated as if their effects had been calculated.
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
}

def card_chips(card):
    if card.get("enhancement") == "m_stone":
        return 50
    rank = int(card.get("rank", 0) or 0)
    base = 11 if rank == 14 else 10 if rank >= 10 else rank
    ability = card.get("ability", {}) or {}
    return base + int(ability.get("bonus", 0) or 0) + int(ability.get("perma_bonus", 0) or 0)

def score_hand(selected, evaluation, hand_levels, jokers=None, held_cards=None):
    name = evaluation["name"]
    level = (hand_levels or {}).get(name, {}) or {}
    chips = float(level.get("chips", 0) or 0)
    mult = float(level.get("mult", 0) or 0)
    scoring = evaluation["scoring_cards"]
    notes = [f"{name} level {level.get('level', 1)}: {chips:g} chips × {mult:g} mult"]

    # Card chips and card-triggered enhancements, left to right.
    for card in scoring:
        if card.get("debuff"):
            continue
        chips += card_chips(card)
        enh = card.get("enhancement", "Base")
        ability = card.get("ability", {}) or {}
        if enh == "m_bonus":
            chips += 30
            notes.append(f"{card['name']}: Bonus +30 chips")
        elif enh == "m_mult":
            mult += 4
            notes.append(f"{card['name']}: Mult +4")
        elif enh == "m_glass":
            mult *= 2
            notes.append(f"{card['name']}: Glass ×2 mult")
        edition = card.get("edition")
        if edition == "foil":
            chips += 50
            notes.append(f"{card['name']}: Foil +50 chips")
        elif edition == "holo":
            mult += 10
            notes.append(f"{card['name']}: Holographic +10 mult")
        elif edition == "polychrome":
            mult *= 1.5
            notes.append(f"{card['name']}: Polychrome ×1.5 mult")

    # Held-in-hand effects supported in this release.
    for card in held_cards or []:
        if card in selected or card.get("debuff"):
            continue
        if card.get("enhancement") == "m_steel":
            mult *= 1.5
            notes.append(f"{card['name']}: held Steel ×1.5 mult")

    unsupported = []
    # Joker effects are processed in their saved left-to-right order.
    for joker in jokers or []:
        if joker.get("debuff"):
            continue
        key = (joker.get("save_fields") or {}).get("center", "")
        effect = JOKER_SIMPLE.get(key)
        if not effect:
            unsupported.append(joker.get("label") or key or "Unknown Joker")
            continue
        kind, value = effect
        if kind == "add_mult":
            mult += value
            notes.append(f"{key}: +{value} mult")
        elif kind == "suit_mult":
            suit, amount = value
            count = sum(1 for c in scoring if c.get("suit") == suit)
            mult += count * amount
            if count:
                notes.append(f"{key}: +{count*amount} mult ({count} {suit})")
        elif kind == "conditional_mult" and name == value[0]:
            mult += value[1]
            notes.append(f"{key}: +{value[1]} mult")
        elif kind == "conditional_chips" and name == value[0]:
            chips += value[1]
            notes.append(f"{key}: +{value[1]} chips")
        elif kind == "max_cards_mult" and len(selected) <= value[0]:
            mult += value[1]
            notes.append(f"{key}: +{value[1]} mult")
        elif kind == "joker_count_mult":
            mult += len(jokers or []) * value
            notes.append(f"{key}: +{len(jokers or [])*value} mult")

    score = max(0, int(round(chips * mult)))
    return {
        "chips": chips, "mult": mult, "score": score,
        "notes": notes, "unsupported_jokers": unsupported,
        "accuracy": "Partial" if unsupported else "Core effects only"
    }
