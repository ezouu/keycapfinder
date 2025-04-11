# app.py
import math
import random
from flask import Flask, render_template, request, redirect, url_for
from drafts.templates.load_sets import load_sets
from drafts.templates.tournament import swiss_pair, setup_new_round, eliminate_players

app = Flask(__name__)

# Load keyboard sets from the images directory.
keyboard_sets = load_sets("images")

# Global tournament state
current_round = 1
current_pairings = []
match_index = 0

# Initial pairing for round 1 (no elimination)
if keyboard_sets:
    temp_players = keyboard_sets.copy()
    random.shuffle(temp_players)
    current_pairings = []
    while len(temp_players) > 1:
        p = temp_players.pop(0)
        q = temp_players.pop(0)
        current_pairings.append((p, q))
    if temp_players:
        current_pairings.append((temp_players[0], None))

@app.route('/')
def index():
    return render_template("index.html", total_players=len(keyboard_sets), current_round=current_round)

@app.route('/list')
def list_sets():
    return render_template("list.html", keyboard_sets=keyboard_sets)

@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    global current_round, match_index, current_pairings, keyboard_sets
    active_players = [p for p in keyboard_sets if p["active"]]
    if len(active_players) < 2:
        return redirect(url_for('results'))
        
    if request.method == 'POST':
        winner_id = int(request.form.get('winner_id'))
        p1_id = int(request.form.get('p1_id'))
        p2_id = int(request.form.get('p2_id'))
        
        def find_player(pid):
            return next((p for p in keyboard_sets if p["id"] == pid), None)
        p1 = find_player(p1_id)
        p2 = find_player(p2_id)
        
        if p2 is not None:
            if winner_id == p1_id:
                p1["score"] += 1
            elif winner_id == p2_id:
                p2["score"] += 1
            if p2_id not in p1["opponents"]:
                p1["opponents"].append(p2_id)
            if p1_id not in p2["opponents"]:
                p2["opponents"].append(p1_id)
        match_index += 1
        
        if match_index >= len(current_pairings):
            # End of round: for round 2+ eliminate lowest scoring players.
            if current_round >= 2:
                eliminate_players(keyboard_sets, current_round)
            current_round += 1
            current_pairings = setup_new_round(keyboard_sets)
            match_index = 0
            return redirect(url_for('tournament'))
        else:
            return redirect(url_for('tournament'))
    else:
        if match_index >= len(current_pairings):
            if current_round >= 2:
                eliminate_players(keyboard_sets, current_round)
            current_round += 1
            current_pairings = setup_new_round(keyboard_sets)
            match_index = 0
            return redirect(url_for('tournament'))
            
        current_match = current_pairings[match_index]
        p_left, p_right = current_match
        if p_right is None:
            if not p_left.get("bye_awarded", False):
                p_left["score"] += 1
                p_left["bye_awarded"] = True
            match_index += 1
            return redirect(url_for('tournament'))
            
        round_progress = int((match_index / len(current_pairings)) * 100)
        return render_template("tournament.html", 
                               current_round=current_round,
                               match_index=match_index,
                               total_matches=len(current_pairings),
                               round_progress=round_progress,
                               p_left=p_left,
                               p_right=p_right)

@app.route('/results')
def results():
    sorted_players = sorted(keyboard_sets, key=lambda p: (-p["score"], p["id"]))
    return render_template("results.html", sorted_players=sorted_players)

if __name__ == '__main__':
    app.run(debug=True)
