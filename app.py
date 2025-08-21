import eventlet
eventlet.monkey_patch()  # Must be first!

import os
import time
from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Placeholder for players list
from players import players

# Admin password (use environment variable in production)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Braj2025')

# Draft state
draft_state = {
    "teams": [],  # Stores original case team names
    "rosters": {},  # Key: lowercase team name, Value: list of players
    "available_players": players.copy(),
    "current_round": 1,
    "current_pick": 0,
    "num_rounds": 17,
    "started": False,
    "paused": False,
    "turn_start_time": None,
    "draft_history": [],  # Uses original case for display_team, roster_team
    "player_queues": {},  # Key: lowercase team name, Value: list of players
    "assigned_spots": {},  # Key: round number, Value: {lowercase original_team: original case assigned_team}
    "team_name_map": {}  # Key: lowercase team name, Value: original case team name
}

def normalize_team_name(team_name):
    """Normalize team name to lowercase for internal comparisons."""
    return team_name.lower() if team_name else ''

def get_original_team_name(normalized_team_name):
    """Get the original case team name from the normalized (lowercase) name."""
    return draft_state["team_name_map"].get(normalized_team_name, normalized_team_name)

def get_current_order():
    round_num = draft_state["current_round"]
    if round_num == 1 or round_num == 2:
        return draft_state["teams"]  # Linear order: Team1, Team2, ..., TeamN
    else:
        # Start snake draft at Round 3: odd rounds reverse, even rounds forward
        return draft_state["teams"][::-1] if round_num % 2 == 1 else draft_state["teams"]

def get_assigned_team(round_num, original_team):
    """Get the team assigned to a specific round and original team, if any."""
    normalized_original_team = normalize_team_name(original_team)
    assigned_team = draft_state["assigned_spots"].get(round_num, {}).get(normalized_original_team, original_team)
    return assigned_team

def advance_to_next_open_pick():
    num_teams = len(draft_state["teams"])
    while draft_state["current_round"] <= draft_state["num_rounds"]:
        order = get_current_order()
        team = order[draft_state["current_pick"]]
        if any(p["round"] == draft_state["current_round"] and p["display_team"] == team for p in draft_state["draft_history"]):
            draft_state["current_pick"] += 1
            if draft_state["current_pick"] >= num_teams:
                draft_state["current_round"] += 1
                draft_state["current_pick"] = 0
        else:
            return
    # No open spots left, end draft
    draft_state["started"] = False
    draft_state["turn_start_time"] = None
    draft_state["current_round"] = draft_state["num_rounds"] + 1
    draft_state["current_pick"] = 0

def reverse_to_previous_open_pick():
    num_teams = len(draft_state["teams"])
    while draft_state["current_round"] >= 1:
        order = get_current_order()
        team = order[draft_state["current_pick"]]
        normalized_team = normalize_team_name(team)
        if any(p["round"] == draft_state["current_round"] and p["display_team"] == team for p in draft_state["draft_history"]):
            draft_state["current_pick"] -= 1
            if draft_state["current_pick"] < 0:
                draft_state["current_round"] -= 1
                draft_state["current_pick"] = num_teams - 1
        else:
            return
    # If no open previous, set to beginning
    draft_state["current_round"] = 1
    draft_state["current_pick"] = 0

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    if data.get('is_spectator'):
        session['is_spectator'] = True
        emit('update_draft', draft_state)
        return
    team_name = data.get('team', '')
    normalized_team_name = normalize_team_name(team_name)
    if not team_name:
        emit('join_error', {'msg': 'Team name required'})
        return
    if data.get('is_admin'):
        password = data.get('password', '')
        if password != ADMIN_PASSWORD:
            emit('join_error', {'msg': 'Invalid admin password.'})
            return
        session['is_admin'] = True
        if team_name:
            if draft_state["started"] and normalized_team_name not in [normalize_team_name(t) for t in draft_state["teams"]]:
                emit('join_error', {'msg': 'Draft has started, no new teams can join'})
                return
            if normalized_team_name not in [normalize_team_name(t) for t in draft_state["teams"]]:
                draft_state["teams"].append(team_name)  # Store original case
                draft_state["rosters"][normalized_team_name] = []
                draft_state["player_queues"][normalized_team_name] = []
                draft_state["team_name_map"][normalized_team_name] = team_name
            session['team'] = team_name  # Store original case in session
        else:
            session['team'] = 'Admin'
        emit('update_draft', draft_state, broadcast=True)
    else:
        if draft_state["started"] and normalized_team_name not in [normalize_team_name(t) for t in draft_state["teams"]]:
            emit('join_error', {'msg': 'Draft has started, no new teams can join'})
            return
        if normalized_team_name not in [normalize_team_name(t) for t in draft_state["teams"]]:
            draft_state["teams"].append(team_name)  # Store original case
            draft_state["rosters"][normalized_team_name] = []
            draft_state["player_queues"][normalized_team_name] = []
            draft_state["team_name_map"][normalized_team_name] = team_name
        session['team'] = team_name  # Store original case in session
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('reorder_teams')
def handle_reorder_teams(data):
    new_order = data['new_order']
    if 'is_admin' in session and session['is_admin'] and not draft_state["started"]:
        normalized_new_order = [normalize_team_name(t) for t in new_order]
        normalized_teams = [normalize_team_name(t) for t in draft_state["teams"]]
        if sorted(normalized_new_order) == sorted(normalized_teams):
            draft_state["teams"] = new_order  # Preserve original case
            emit('update_draft', draft_state, broadcast=True)

@socketio.on('assign_pick')
def handle_assign_pick(data):
    if 'is_admin' in session and session['is_admin'] and not draft_state["started"]:
        team = data['team']
        normalized_team = normalize_team_name(team)
        original_team = get_original_team_name(normalized_team)
        player_name = data['player']
        round_num = data['round']
        player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
        if player and normalized_team in draft_state["rosters"] and 1 <= round_num <= draft_state["num_rounds"]:
            pick_in_round = draft_state["teams"].index(original_team) + 1 if round_num <= 2 else (len(draft_state["teams"]) - draft_state["teams"].index(original_team) if round_num % 2 == 0 else draft_state["teams"].index(original_team) + 1)
            overall_pick = (round_num - 1) * len(draft_state["teams"]) + pick_in_round
            if not any(p["round"] == round_num and p["display_team"] == original_team for p in draft_state["draft_history"]):
                draft_state["available_players"].remove(player)
                draft_state["rosters"][normalized_team].append(player)
                draft_state["draft_history"].append({
                    "round": round_num,
                    "overall_pick": overall_pick,
                    "display_team": original_team,
                    "roster_team": original_team,
                    "player": player,
                    "time_taken": 0
                })
                draft_state["draft_history"].sort(key=lambda x: x["overall_pick"])
                emit('update_draft', draft_state, broadcast=True)
            else:
                emit('error', {'msg': 'Spot already filled'})
        else:
            emit('error', {'msg': 'Invalid assignment'})

@socketio.on('assign_draft_spot')
def handle_assign_draft_spot(data):
    if 'is_admin' in session and session['is_admin'] and draft_state["started"] and not draft_state["paused"]:
        try:
            round_num = int(data['round'])
            original_team = data['original_team']
            normalized_original_team = normalize_team_name(original_team)
            assigned_team = data['assigned_team']
            normalized_assigned_team = normalize_team_name(assigned_team)
            if round_num < draft_state["current_round"] or round_num > draft_state["num_rounds"]:
                emit('error', {'msg': 'Invalid round for assignment'})
                return
            if normalized_original_team not in [normalize_team_name(t) for t in draft_state["teams"]] or normalized_assigned_team not in [normalize_team_name(t) for t in draft_state["teams"]]:
                emit('error', {'msg': 'Invalid team(s) for assignment'})
                return
            if any(p["round"] == round_num and p["display_team"] == original_team for p in draft_state["draft_history"]):
                emit('error', {'msg': 'Cannot assign already made pick'})
                return
            if round_num == draft_state["current_round"]:
                order = get_current_order()
                pick_index = order.index(original_team)
                if pick_index < draft_state["current_pick"]:
                    emit('error', {'msg': 'Cannot assign past or current pick in the current round'})
                    return
            # Initialize round in assigned_spots if not exists
            if round_num not in draft_state["assigned_spots"]:
                draft_state["assigned_spots"][round_num] = {}
            # Assign the spot using normalized original team as key
            draft_state["assigned_spots"][round_num][normalized_original_team] = assigned_team
            emit('update_draft', draft_state, broadcast=True)
        except (KeyError, ValueError):
            emit('error', {'msg': 'Invalid assignment parameters'})
    else:
        emit('error', {'msg': 'Action not allowed: Draft not started, paused, or not admin'})

@socketio.on('start_draft')
def handle_start():
    if 'is_admin' in session and session['is_admin'] and not draft_state["started"] and len(draft_state["teams"]) >= 2:
        draft_state["started"] = True
        advance_to_next_open_pick()
        draft_state["turn_start_time"] = time.time()
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('pause_draft')
def handle_pause():
    if 'is_admin' in session and session['is_admin']:
        draft_state["paused"] = not draft_state["paused"]
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('revert_pick')
def handle_revert():
    if 'is_admin' in session and session['is_admin'] and draft_state["draft_history"]:
        last_pick = draft_state["draft_history"].pop()
        player = last_pick["player"]
        normalized_team = normalize_team_name(last_pick["roster_team"])
        draft_state["rosters"][normalized_team].pop()
        draft_state["available_players"].append(player)
        # Set to the exact position of the last pick
        draft_state["current_round"] = last_pick["round"]
        order = get_current_order()
        try:
            draft_state["current_pick"] = order.index(last_pick["display_team"])
        except ValueError:
            # Fallback to previous pick if display_team not in order
            draft_state["current_pick"] = 0
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('reset_draft')
def handle_reset_draft():
    if 'is_admin' in session and session['is_admin']:
        # Reset draft state to initial values
        draft_state["teams"] = []
        draft_state["rosters"] = {}
        draft_state["available_players"] = players.copy()
        draft_state["current_round"] = 1
        draft_state["current_pick"] = 0
        draft_state["started"] = False
        draft_state["paused"] = False
        draft_state["turn_start_time"] = None
        draft_state["draft_history"] = []
        draft_state["player_queues"] = {}
        draft_state["assigned_spots"] = {}
        draft_state["team_name_map"] = {}
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('add_to_queue')
def handle_add_to_queue(data):
    team = session.get('team')
    normalized_team = normalize_team_name(team)
    player_name = data['player']
    player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
    if team and player and normalized_team in draft_state["player_queues"] and player not in draft_state["player_queues"][normalized_team]:
        draft_state["player_queues"][normalized_team].append(player)
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('remove_from_queue')
def handle_remove_from_queue(data):
    team = session.get('team')
    normalized_team = normalize_team_name(team)
    player_name = data['player']
    if team and normalized_team in draft_state["player_queues"]:
        draft_state["player_queues"][normalized_team] = [p for p in draft_state["player_queues"][normalized_team] if p['name'] != player_name]
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('admin_make_pick')
def handle_admin_pick(data):
    if 'is_admin' in session and session['is_admin'] and draft_state["started"] and not draft_state["paused"]:
        current_order = get_current_order()
        current_team = current_order[draft_state["current_pick"]]
        assigned_team = get_assigned_team(draft_state["current_round"], current_team)
        normalized_assigned_team = normalize_team_name(assigned_team)
        if data['for_team']:
            assigned_team = data['for_team']
            normalized_assigned_team = normalize_team_name(assigned_team)
        player_name = data['player']
        player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
        if player and normalized_assigned_team in draft_state["rosters"]:
            draft_state["available_players"].remove(player)
            draft_state["rosters"][normalized_assigned_team].append(player)
            overall_pick = ((draft_state["current_round"] - 1) * len(draft_state["teams"])) + draft_state["current_pick"] + 1
            draft_state["draft_history"].append({
                "round": draft_state["current_round"],
                "overall_pick": overall_pick,
                "display_team": current_team,
                "roster_team": assigned_team,
                "player": player,
                "time_taken": time.time() - draft_state["turn_start_time"]
            })
            for queue_team in draft_state["player_queues"]:
                draft_state["player_queues"][queue_team] = [p for p in draft_state["player_queues"][queue_team] if p['name'] != player_name]
            advance_to_next_open_pick()
            if draft_state["current_round"] > draft_state["num_rounds"]:
                draft_state["started"] = False
                draft_state["turn_start_time"] = None
            else:
                draft_state["turn_start_time"] = time.time()
            emit('update_draft', draft_state, broadcast=True)
        else:
            emit('error', {'msg': 'Player not found or invalid team'})

@socketio.on('admin_manual_pick')
def handle_admin_manual_pick(data):
    if 'is_admin' in session and session['is_admin'] and draft_state["started"] and not draft_state["paused"]:
        current_order = get_current_order()
        current_team = current_order[draft_state["current_pick"]]
        assigned_team = get_assigned_team(draft_state["current_round"], current_team)
        normalized_assigned_team = normalize_team_name(assigned_team)
        if data['for_team']:
            assigned_team = data['for_team']
            normalized_assigned_team = normalize_team_name(assigned_team)
        player_name = data['player'].strip()
        position = data['position']
        player = next((p for p in draft_state["available_players"] if p['name'].lower() == player_name.lower()), None)
        if not player:
            player = {
                'name': player_name,
                'pos': position,
                'team': 'Custom',
                'bye': 0,
                'rank': 9999
            }
        else:
            draft_state["available_players"].remove(player)
        if normalized_assigned_team in draft_state["rosters"]:
            draft_state["rosters"][normalized_assigned_team].append(player)
            overall_pick = ((draft_state["current_round"] - 1) * len(draft_state["teams"])) + draft_state["current_pick"] + 1
            draft_state["draft_history"].append({
                "round": draft_state["current_round"],
                "overall_pick": overall_pick,
                "display_team": current_team,
                "roster_team": assigned_team,
                "player": player,
                "time_taken": time.time() - draft_state["turn_start_time"]
            })
            for queue_team in draft_state["player_queues"]:
                draft_state["player_queues"][queue_team] = [p for p in draft_state["player_queues"][queue_team] if p['name'].lower() != player_name.lower()]
            advance_to_next_open_pick()
            if draft_state["current_round"] > draft_state["num_rounds"]:
                draft_state["started"] = False
                draft_state["turn_start_time"] = None
            else:
                draft_state["turn_start_time"] = time.time()
            emit('update_draft', draft_state, broadcast=True)
        else:
            emit('error', {'msg': 'Invalid team selected'})
    else:
        emit('error', {'msg': 'Action not allowed: Draft not started, paused, or not admin'})

@socketio.on('make_pick')
def handle_pick(data):
    if not draft_state["started"] or draft_state["paused"] or 'team' not in session:
        emit('error', {'msg': 'Draft not started, paused, or no team assigned'})
        return
    current_order = get_current_order()
    current_team = current_order[draft_state["current_pick"]]
    assigned_team = get_assigned_team(draft_state["current_round"], current_team)
    normalized_assigned_team = normalize_team_name(assigned_team)
    normalized_session_team = normalize_team_name(session.get('team'))
    if normalized_session_team != normalized_assigned_team and not session.get('is_admin', False):
        emit('error', {'msg': f'Not your turn. Expected: {assigned_team}, Got: {session.get("team")}'})
        return

    player_name = data['player']
    player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
    if player and normalized_assigned_team in draft_state["rosters"]:
        draft_state["available_players"].remove(player)
        draft_state["rosters"][normalized_assigned_team].append(player)
        overall_pick = ((draft_state["current_round"] - 1) * len(draft_state["teams"])) + draft_state["current_pick"] + 1
        draft_state["draft_history"].append({
            "round": draft_state["current_round"],
            "overall_pick": overall_pick,
            "display_team": current_team,
            "roster_team": assigned_team,
            "player": player,
            "time_taken": time.time() - draft_state["turn_start_time"]
        })
        for queue_team in draft_state["player_queues"]:
            draft_state["player_queues"][queue_team] = [p for p in draft_state["player_queues"][queue_team] if p['name'] != player_name]
        advance_to_next_open_pick()
        if draft_state["current_round"] > draft_state["num_rounds"]:
            draft_state["started"] = False
            draft_state["turn_start_time"] = None
        else:
            draft_state["turn_start_time"] = time.time()
        emit('update_draft', draft_state, broadcast=True)
    else:
        emit('error', {'msg': 'Player not found or invalid team'})

@socketio.on('connect')
def handle_connect():
    emit('update_draft', draft_state)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)