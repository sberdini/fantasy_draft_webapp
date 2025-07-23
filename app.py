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
    "teams": [],
    "rosters": {},
    "available_players": players.copy(),
    "current_round": 1,
    "current_pick": 0,
    "num_rounds": 17,
    "started": False,
    "paused": False,
    "turn_start_time": None,
    "draft_history": [],
}

def get_current_order():
    if draft_state["current_round"] % 2 == 1:
        return draft_state["teams"]
    else:
        return draft_state["teams"][::-1]

def advance_to_next_open_pick():
    num_teams = len(draft_state["teams"])
    while draft_state["current_round"] <= draft_state["num_rounds"]:
        order = get_current_order()
        team = order[draft_state["current_pick"]]
        if any(p["round"] == draft_state["current_round"] and p["team"] == team for p in draft_state["draft_history"]):
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
        if any(p["round"] == draft_state["current_round"] and p["team"] == team for p in draft_state["draft_history"]):
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
    if data.get('is_admin'):
        password = data.get('password', '')
        if password != ADMIN_PASSWORD:
            emit('join_error', {'msg': 'Invalid admin password.'})
            return
        session['is_admin'] = True
        if team_name:
            if draft_state["started"] and team_name not in draft_state["teams"]:
                emit('join_error', {'msg': 'Draft has started, no new teams can join'})
                return
            if team_name not in draft_state["teams"]:
                draft_state["teams"].append(team_name)
                draft_state["rosters"][team_name] = []
            session['team'] = team_name
        else:
            session['team'] = 'Admin'
        emit('update_draft', draft_state, broadcast=True)
    else:
        if draft_state["started"] and team_name not in draft_state["teams"]:
            emit('join_error', {'msg': 'Draft has started, no new teams can join'})
            return
        if not team_name:
            emit('join_error', {'msg': 'Team name required'})
            return
        if team_name not in draft_state["teams"]:
            draft_state["teams"].append(team_name)
            draft_state["rosters"][team_name] = []
        session['team'] = team_name
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('reorder_teams')
def handle_reorder_teams(data):
    new_order = data['new_order']
    if 'is_admin' in session and session['is_admin'] and not draft_state["started"]:
        if sorted(new_order) == sorted(draft_state["teams"]):
            draft_state["teams"] = new_order
            emit('update_draft', draft_state, broadcast=True)

@socketio.on('assign_pick')
def handle_assign_pick(data):
    if 'is_admin' in session and session['is_admin'] and not draft_state["started"]:
        team = data['team']
        player_name = data['player']
        round_num = data['round']
        player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
        if player and team in draft_state["rosters"] and 1 <= round_num <= draft_state["num_rounds"]:
            pick_in_round = draft_state["teams"].index(team) + 1 if round_num % 2 == 1 else len(draft_state["teams"]) - draft_state["teams"].index(team)
            overall_pick = (round_num - 1) * len(draft_state["teams"]) + pick_in_round
            if not any(p["round"] == round_num and p["team"] == team for p in draft_state["draft_history"]):
                draft_state["available_players"].remove(player)
                draft_state["rosters"][team].append(player)
                draft_state["draft_history"].append({
                    "round": round_num,
                    "overall_pick": overall_pick,
                    "team": team,
                    "player": player
                })
                draft_state["draft_history"].sort(key=lambda x: x["overall_pick"])
                emit('update_draft', draft_state, broadcast=True)
            else:
                emit('error', {'msg': 'Spot already filled'})
        else:
            emit('error', {'msg': 'Invalid assignment'})

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
        team = last_pick["team"]
        draft_state["rosters"][team].pop()
        draft_state["available_players"].append(player)
        # Set to last pick's position before reversing
        draft_state["current_round"] = last_pick["round"]
        order = get_current_order()
        draft_state["current_pick"] = order.index(last_pick["team"])
        reverse_to_previous_open_pick()  # Now it will stay at the reverted spot since it's open
        draft_state["turn_start_time"] = time.time()
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
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('admin_make_pick')
def handle_admin_pick(data):
    if 'is_admin' in session and session['is_admin'] and draft_state["started"] and not draft_state["paused"]:
        current_order = get_current_order()
        current_team = current_order[draft_state["current_pick"]]
        if data['for_team']:
            current_team = data['for_team']
        player_name = data['player']
        player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
        if player:
            draft_state["available_players"].remove(player)
            draft_state["rosters"][current_team].append(player)
            overall_pick = ((draft_state["current_round"] - 1) * len(draft_state["teams"])) + draft_state["current_pick"] + 1
            draft_state["draft_history"].append({
                "round": draft_state["current_round"],
                "overall_pick": overall_pick,
                "team": current_team,
                "player": player,
                "time_taken": time.time() - draft_state["turn_start_time"]  # Record time taken for this pick
            })
            advance_to_next_open_pick()
            if draft_state["current_round"] > draft_state["num_rounds"]:
                draft_state["started"] = False
                draft_state["turn_start_time"] = None
            else:
                draft_state["turn_start_time"] = time.time()
            emit('update_draft', draft_state, broadcast=True)

@socketio.on('make_pick')
def handle_pick(data):
    if not draft_state["started"] or draft_state["paused"] or 'team' not in session:
        return
    current_order = get_current_order()
    current_team = current_order[draft_state["current_pick"]]
    if session['team'] != current_team:
        return  # Not your turn

    player_name = data['player']
    player = next((p for p in draft_state["available_players"] if p['name'] == player_name), None)
    if player:
        draft_state["available_players"].remove(player)
        draft_state["rosters"][current_team].append(player)
        
        # Add to draft history
        overall_pick = ((draft_state["current_round"] - 1) * len(draft_state["teams"])) + draft_state["current_pick"] + 1
        draft_state["draft_history"].append({
            "round": draft_state["current_round"],
            "overall_pick": overall_pick,
            "team": current_team,
            "player": player,
            "time_taken": time.time() - draft_state["turn_start_time"]  # Record time taken for this pick
        })
        
        # Advance to next open pick
        advance_to_next_open_pick()
        if draft_state["current_round"] > draft_state["num_rounds"]:
            draft_state["started"] = False  # Draft over
            draft_state["turn_start_time"] = None
        else:
            draft_state["turn_start_time"] = time.time()
        
        emit('update_draft', draft_state, broadcast=True)

@socketio.on('connect')
def handle_connect():
    emit('update_draft', draft_state)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)