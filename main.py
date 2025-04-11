import math
import os
import random
from pathlib import Path
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__, static_folder='images')

# ----------------------------------
# Global variable for background color.
# ----------------------------------
tournament_bg = "#f2f2f2"  # Default background color

# ----------------------------------
# 1. Player Loading: Register Keyboard Sets
# ----------------------------------
def load_sets(base_dir):
    """
    Scan the repository for keyboard sets and register them as players.
    For each set folder, load images from both "kits_pics" and "rendering_pics".
    Each player dictionary includes:
      - id: unique identifier
      - name: display name (e.g., "DSA Alchemy")
      - images: list of image file paths (relative to base_dir)
      - score: total wins (initially 0)
      - opponents: list of opponent IDs already played
      - active: True if still in tournament, False if eliminated
    """
    sets = []
    base_path = Path(base_dir)
    for source in ["dsa-keycaps", "gmk-keycaps"]:
        source_path = base_path / source
        if source_path.exists() and source_path.is_dir():
            for set_dir in source_path.iterdir():
                if set_dir.is_dir():
                    display_name = f"{source.split('-')[0].upper()} {set_dir.name.capitalize()}"
                    images = []
                    # Load kits_pics images.
                    kits_dir = set_dir / "kits_pics"
                    if kits_dir.exists() and kits_dir.is_dir():
                        for p in kits_dir.iterdir():
                            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
                                relative_path = p.relative_to(base_path)
                                images.append(str(relative_path))
                    # Load rendering_pics images.
                    rendering_dir = set_dir / "rendering_pics"
                    if rendering_dir.exists() and rendering_dir.is_dir():
                        for p in rendering_dir.iterdir():
                            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
                                relative_path = p.relative_to(base_path)
                                images.append(str(relative_path))
                    # Sort images (you can change the logic if desired)
                    images = sorted(images)
                    sets.append({
                        "name": display_name,
                        "images": images,
                        "score": 0,
                        "opponents": [],
                        "active": True
                    })
    # Assign a unique ID to each player.
    for idx, player in enumerate(sets):
        player["id"] = idx + 1
    return sets

keyboard_sets = load_sets("images")

# ----------------------------------
# 2. Global Tournament State Variables
# ----------------------------------
current_round = 1        # Round counter; no elimination in Round 1.
current_pairings = []    # List of pairings for the current round (tuple: (player, opponent)). For a bye, opponent is None.
match_index = 0          # Index of the next match in the current round.

# ----------------------------------
# 3. Pairing Helper Functions
# ----------------------------------
def swiss_pair(players):
    """
    Given a list of players (sorted descending by score),
    return a list of pairs (tuples). If an odd number remains,
    the last pairing is (player, None) indicating a bye.
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

def setup_new_round():
    """
    Prepare a new round using only active players.
    Sort them (by descending score, then by id) and generate pairings.
    Reset match_index to 0.
    """
    global current_pairings, match_index
    active_players = [p for p in keyboard_sets if p["active"]]
    if not active_players:
        current_pairings = []
        return
    sorted_players = sorted(active_players, key=lambda p: (-p["score"], p["id"]))
    current_pairings = swiss_pair(sorted_players)
    match_index = 0

def eliminate_players():
    """
    Eliminate (mark as inactive) all players with the lowest score among the active players,
    provided that elimination does not drop the number of active players below 2.
    This custom rule will remove the lowest-performing group at the end of each round (starting with round 2).
    """
    global keyboard_sets
    active_players = [p for p in keyboard_sets if p["active"]]
    if len(active_players) < 3:
        return
    min_score = min(p["score"] for p in active_players)
    survivors = [p for p in active_players if p["score"] > min_score]
    if survivors:
        for p in active_players:
            if p["score"] == min_score:
                p["active"] = False

# ----------------------------------
# 4. Initial Pairings for Round 1 (No elimination)
# ----------------------------------
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

# ----------------------------------
# 5. Flask Routes
# ----------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    global tournament_bg
    if request.method == 'POST':
        chosen_color = request.form.get("bg_color")
        if chosen_color:
            tournament_bg = chosen_color
        return redirect(url_for('index'))
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <title>Keyboard Swiss Tournament</title>
        <style>
          body {
            background-color: {{ tournament_bg }};
            font-family: Arial, sans-serif;
            margin: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
          }
          h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
          }
          p, ul, form {
            font-size: 1.2em;
          }
          ul {
            list-style: none;
            padding: 0;
            margin: 20px 0;
          }
          li {
            margin: 10px 0;
          }
          a {
            color: #007BFF;
            text-decoration: none;
            font-weight: bold;
          }
          a:hover {
            text-decoration: underline;
          }
          input[type="color"] {
            width: 50px;
            height: 50px;
            border: none;
            margin-top: 10px;
          }
          button {
            margin-top: 10px;
            padding: 10px 20px;
            background-color: #007BFF;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 1em;
          }
          button:hover {
            background-color: #0056b3;
          }
        </style>
      </head>
      <body>
        <h1>Keyboard Swiss Tournament</h1>
        <p>Registered Players: {{ total_players }} | Current Round: {{ current_round }}</p>
        <ul>
          <li><a href="{{ url_for('tournament') }}">Continue Tournament</a></li>
          <li><a href="{{ url_for('list_sets') }}">View All Keyboard Sets</a></li>
        </ul>
        <form method="POST" action="{{ url_for('index') }}">
          <label for="bg_color">Choose your website background color:</label><br>
          <input type="color" id="bg_color" name="bg_color" value="{{ tournament_bg }}">
          <br>
          <button type="submit">Set Background Color</button>
        </form>
      </body>
    </html>
    """
    return render_template_string(html,
                                  total_players=len(keyboard_sets),
                                  current_round=current_round,
                                  tournament_bg=tournament_bg)

@app.route('/list')
def list_sets():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <title>All Keyboard Sets</title>
        <style>
          body {
            background-color: {{ tournament_bg }};
            font-family: Arial, sans-serif;
            background: {{ tournament_bg }};
            padding: 20px;
          }
          h1 { text-align: center; }
          ul { list-style: none; padding: 0; }
          li { margin-bottom: 20px; }
          img { margin: 5px; }
          a { color: #007BFF; text-decoration: none; }
          a:hover { text-decoration: underline; }
        </style>
      </head>
      <body>
        <h1>All Keyboard Sets</h1>
        <ul>
          {% for k in keyboard_sets %}
            <li>
              <strong>{{ k.name }}</strong> - Score: {{ k.score }} {% if not k.active %}(Eliminated){% endif %}<br>
              {% for img in k.images %}
                <img src="{{ url_for('static', filename=img) }}" alt="{{ k.name }}" width="100">
              {% endfor %}
            </li>
          {% endfor %}
        </ul>
        <p><a href="{{ url_for('index') }}">Back to Home</a></p>
      </body>
    </html>
    """
    return render_template_string(html, keyboard_sets=keyboard_sets, tournament_bg=tournament_bg)

@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    global current_round, match_index, current_pairings, keyboard_sets
    # Use only active players.
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
            # End of round: for rounds 2+, eliminate lowest scoring players.
            if current_round >= 2:
                eliminate_players()
            current_round += 1
            setup_new_round()
            return redirect(url_for('tournament'))
        else:
            return redirect(url_for('tournament'))
    else:
        if match_index >= len(current_pairings):
            if current_round >= 2:
                eliminate_players()
            current_round += 1
            setup_new_round()
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
        html = """
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="UTF-8">
            <title>Round {{ current_round }} - Match {{ match_index + 1 }} of {{ total_matches }}</title>
            <style>
              html, body {
                margin: 0; padding: 0; height: 100%;
                font-family: Arial, sans-serif;
                background-color: {{ tournament_bg }};
              }
              .progress-container {
                position: fixed; top: 0; left: 0; width: 100%;
                background: #ddd; padding: 5px 0; z-index: 200;
              }
              .progress {
                height: 10px; background: #007BFF;
                width: {{ round_progress }}%;
                transition: width 0.5s;
              }
              .progress-text {
                text-align: center; font-size: 14px; color: #333;
              }
              h1 {
                text-align: center; margin-top: 50px;
              }
              .panels {
                display: flex; margin-top: 20px;
                height: calc(100vh - 130px);
              }
              .panel {
                flex: 1; overflow-y: auto; padding: 10px; box-sizing: border-box;
              }
              .left-panel { border-right: 1px solid #ccc; }
              .right-panel { border-left: 1px solid #ccc; }
              .images-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 10px;
                justify-items: center;
              }
              .images-grid img {
                width: 200px; height: 200px;
                object-fit: cover; border: 1px solid #ddd;
              }
              .center-buttons {
                width: 240px;
                position: fixed; top: 50%;
                left: calc(50% - 120px);
                transform: translateY(-50%);
                display: flex;
                flex-direction: row;
                gap: 10px;
                z-index: 100;
              }
              .center-buttons button {
                flex: 1;
                padding: 8px;
                background-color: #007BFF;
                color: #fff;
                border: none;
                cursor: pointer;
                font-size: 14px;
              }
              .center-buttons button:hover {
                background-color: #0056b3;
              }
              .back-link {
                text-align: center; margin-top: 20px;
              }
            </style>
          </head>
          <body>
            <div class="progress-container">
              <div class="progress"></div>
              <div class="progress-text">Round {{ current_round }}: Match {{ match_index + 1 }} of {{ total_matches }}</div>
            </div>
            <h1>Round {{ current_round }} - Select the Winner</h1>
            <form method="post">
              <div class="panels">
                <div class="panel left-panel">
                  <div class="images-grid">
                    {% for img in p_left.images %}
                      <img src="{{ url_for('static', filename=img) }}" alt="{{ p_left.name }}">
                    {% endfor %}
                  </div>
                  <p style="text-align: center;"><strong>{{ p_left.name }}</strong></p>
                </div>
                <div class="panel right-panel">
                  <div class="images-grid">
                    {% for img in p_right.images %}
                      <img src="{{ url_for('static', filename=img) }}" alt="{{ p_right.name }}">
                    {% endfor %}
                  </div>
                  <p style="text-align: center;"><strong>{{ p_right.name }}</strong></p>
                </div>
              </div>
              <div class="center-buttons">
                <button type="submit" name="winner_id" value="{{ p_left.id }}">Left</button>
                <button type="submit" name="winner_id" value="{{ p_right.id }}">Right</button>
              </div>
              <input type="hidden" name="p1_id" value="{{ p_left.id }}">
              <input type="hidden" name="p2_id" value="{{ p_right.id }}">
            </form>
            <p class="back-link"><a href="{{ url_for('index') }}">Back to Home</a></p>
          </body>
        </html>
        """
        return render_template_string(html,
                                      current_round=current_round,
                                      match_index=match_index,
                                      total_matches=len(current_pairings),
                                      round_progress=round_progress,
                                      tournament_bg=tournament_bg,
                                      p_left=current_pairings[match_index][0],
                                      p_right=current_pairings[match_index][1])
                                      
@app.route('/results')
def results():
    sorted_players = sorted(keyboard_sets, key=lambda p: (-p["score"], p["id"]))
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <title>Final Tournament Results</title>
        <style>
          body {
            background-color: {{ tournament_bg }};
            font-family: Arial, sans-serif;
            background: {{ tournament_bg }};
            text-align: center;
            padding: 20px;
          }
          h1, h2 { margin-top: 20px; }
          ol { display: inline-block; text-align: left; font-size: 18px; }
          li { margin-bottom: 10px; }
          a { color: #007BFF; text-decoration: none; }
          a:hover { text-decoration: underline; }
        </style>
      </head>
      <body>
        <h1>Tournament Complete!</h1>
        <h2>Final Rankings</h2>
        <ol>
          {% for p in sorted_players %}
            <li>{{ p.name }} - Score: {{ p.score }} {% if not p.active %}(Eliminated){% endif %}</li>
          {% endfor %}
        </ol>
        <p><a href="{{ url_for('index') }}">Back to Home</a></p>
      </body>
    </html>
    """
    return render_template_string(html, sorted_players=sorted_players, tournament_bg=tournament_bg)

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)

