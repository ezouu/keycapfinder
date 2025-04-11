# tournament.py
import random

def swiss_pair(players):
    """
    Given a list of players (assumed already sorted by descending score),
    pair them trying to avoid repeat matchups. Return a list of pairs.
    If there is an odd number, the last pair is (player, None), indicating a bye.
    """
    pairings = []
    unpaired = players.copy()
    while len(unpaired) > 1:
        p = unpaired.pop(0)
        opponent = None
        for i, q in enumerate(unpaired):
            if q["id"] not in p["opponents"]:
                opponent = q
                unpaired.pop(i)
                break
        if opponent is None and unpaired:
            opponent = unpaired.pop(0)
        pairings.append((p, opponent))
    if unpaired:
        pairings.append((unpaired[0], None))
    return pairings

def setup_new_round(keyboard_sets):
    """
    Prepare a new round using only active players.
    Return the generated pairings and reset the match index.
    """
    active_players = [p for p in keyboard_sets if p["active"]]
    if not active_players:
        return []
    sorted_players = sorted(active_players, key=lambda p: (-p["score"], p["id"]))
    pairings = swiss_pair(sorted_players)
    return pairings

def eliminate_players(keyboard_sets, current_round):
    """
    For rounds 2 and higher, eliminate (i.e. mark inactive) players who are
    in the lowest performing group. In this custom system, at the end of each
    round we calculate the minimum score among active players and mark those with
    that score as eliminated—provided that not everyone would be eliminated.
    """
    active_players = [p for p in keyboard_sets if p["active"]]
    if len(active_players) < 3:
        return
    min_score = min(p["score"] for p in active_players)
    if any(p["score"] > min_score for p in active_players):
        for p in active_players:
            if p["score"] == min_score:
                p["active"] = False
