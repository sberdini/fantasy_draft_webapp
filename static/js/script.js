
const socket = io();

let myTeam = null;
let timerInterval = null;
let pendingJoinData = null; // Store join data while waiting for password
let pendingSpotAssignment = null; // Store round and original_team for assignment modal

// Clear localStorage on page load to reset roles for testing
window.addEventListener('load', () => {
    localStorage.clear();
});

function joinDraft() {
    const joinType = document.querySelector('input[name="join-type"]:checked')?.value;
    const team = document.getElementById('team-name')?.value.trim();
    if (!joinType) {
        alert('Please select a join type.');
        return;
    }
    let data = {};
    if (joinType === 'spectator') {
        data.is_spectator = true;
        socket.emit('join', data);
        myTeam = 'Spectator';
        localStorage.setItem('myTeam', myTeam);
        localStorage.setItem('is_admin', 'false');
        localStorage.setItem('is_spectator', 'true');
        document.getElementById('join-section').style.display = 'none';
        document.getElementById('draft-board').style.display = 'block';
    } else if (joinType === 'team') {
        if (!team) {
            alert('Team name required for team join.');
            return;
        }
        data.team = team;
        data.is_admin = false;
        socket.emit('join', data);
        myTeam = team;
        localStorage.setItem('myTeam', myTeam);
        localStorage.setItem('is_admin', 'false');
        localStorage.setItem('is_spectator', 'false');
        document.getElementById('join-section').style.display = 'none';
        document.getElementById('draft-board').style.display = 'block';
    } else if (joinType === 'admin') {
        pendingJoinData = { team: team, is_admin: true };
        document.getElementById('admin-password-modal').style.display = 'flex';
        document.getElementById('admin-password-input').value = '';
        document.getElementById('admin-password-input').focus();
    }
}

function submitAdminPassword() {
    const password = document.getElementById('admin-password-input')?.value.trim();
    if (!password) {
        alert('Please enter a password.');
        return;
    }
    const data = { ...pendingJoinData, password };
    socket.emit('join', data);
    myTeam = pendingJoinData.team || 'Admin';
    localStorage.setItem('myTeam', myTeam);
    localStorage.setItem('is_admin', 'true');
    localStorage.setItem('is_spectator', 'false');
    document.getElementById('admin-password-modal').style.display = 'none';
    document.getElementById('join-section').style.display = 'none';
    document.getElementById('draft-board').style.display = 'block';
}

function cancelAdminPassword() {
    document.getElementById('admin-password-modal').style.display = 'none';
    pendingJoinData = null;
}

function openSpotAssignmentModal(round, original_team) {
    const isAdmin = localStorage.getItem('is_admin') === 'true';
    if (!isAdmin) {
        alert('Only admins can assign draft spots.');
        return;
    }
    pendingSpotAssignment = { round, original_team };
    document.getElementById('assign-spot-info').textContent = `Round ${round}, ${original_team}`;
    const teamSelect = document.getElementById('assign-spot-team-select');
    teamSelect.innerHTML = '';
    window.draftState.teams.forEach(team => {
        const opt = document.createElement('option');
        opt.value = team;
        opt.text = team;
        teamSelect.appendChild(opt);
    });
    document.getElementById('assign-spot-modal').style.display = 'flex';
    teamSelect.focus();
}

function submitSpotAssignment() {
    const assigned_team = document.getElementById('assign-spot-team-select')?.value;
    if (!assigned_team) {
        alert('Please select a team.');
        return;
    }
    if (pendingSpotAssignment) {
        socket.emit('assign_draft_spot', {
            round: pendingSpotAssignment.round,
            original_team: pendingSpotAssignment.original_team,
            assigned_team
        });
        document.getElementById('assign-spot-modal').style.display = 'none';
        pendingSpotAssignment = null;
    }
}

function cancelSpotAssignment() {
    document.getElementById('assign-spot-modal').style.display = 'none';
    pendingSpotAssignment = null;
}

function startDraft() {
    socket.emit('start_draft');
}

function makePick() {
    const select = document.getElementById('player-select');
    const player = select?.value;
    if (player) {
        socket.emit('make_pick', { player });
    } else {
        alert('Please select a player.');
    }
}

function pauseDraft() {
    socket.emit('pause_draft');
}

function revertPick() {
    const isAdmin = localStorage.getItem('is_admin') === 'true';
    if (!isAdmin) {
        alert('Only admins can revert picks.');
        return;
    }
    if (confirm('Are you sure you want to revert the last pick?')) {
        socket.emit('revert_pick');
    }
}

function resetDraft() {
    const isAdmin = localStorage.getItem('is_admin') === 'true';
    if (!isAdmin) {
        alert('Only admins can reset the draft.');
        return;
    }
    if (confirm('Are you sure you want to reset the entire draft? This will clear all teams and picks.')) {
        socket.emit('reset_draft');
    }
}

function adminMakePick() {
    const select = document.getElementById('player-select');
    const player = select?.value;
    const forTeam = document.getElementById('admin-team-select')?.value;
    if (player && forTeam) {
        socket.emit('admin_make_pick', { player, for_team: forTeam });
    } else {
        alert('Please select both a player and a team.');
    }
}

function adminManualPick() {
    const playerName = document.getElementById('admin-manual-player-input')?.value.trim();
    const forTeam = document.getElementById('admin-manual-team-select')?.value;
    const position = document.getElementById('admin-manual-position-select')?.value;
    if (playerName && forTeam && position) {
        socket.emit('admin_manual_pick', { player: playerName, position: position, for_team: forTeam });
    } else {
        alert('Please enter a player name, select a position, and select a team.');
    }
}

function saveDraftOrder() {
    const list = document.getElementById('draft-order-list');
    const newOrder = Array.from(list?.children || []).map(li => li.textContent);
    socket.emit('reorder_teams', { new_order: newOrder });
}

function assignPlayer() {
    const team = document.getElementById('assign-team-select')?.value;
    const round = parseInt(document.getElementById('assign-round-select')?.value);
    const player = document.getElementById('assign-player-select')?.value;
    if (team && round && player) {
        socket.emit('assign_pick', { team, round, player });
    } else {
        alert('Please select team, round, and player.');
    }
}

function addToQueue() {
    const select = document.getElementById('player-select');
    const player = select?.value;
    if (player) {
        socket.emit('add_to_queue', { player });
    } else {
        alert('Please select a player to add to queue.');
    }
}

function removeFromQueue(player) {
    socket.emit('remove_from_queue', { player });
}

function draftFromQueue(player) {
    socket.emit('make_pick', { player });
}

function filterPlayers() {
    const input = document.getElementById('player-search')?.value.toLowerCase() || '';
    const select = document.getElementById('player-select');
    select.innerHTML = '';

    const filteredPlayers = window.draftState?.available_players
        ?.sort((a, b) => a.rank - b.rank)
        .filter(p => {
            const text = `${p.rank}. ${p.name} (${p.pos}, ${p.team}) - Bye: ${p.bye}`.toLowerCase();
            return text.includes(input);
        }) || [];

    filteredPlayers.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.text = `${p.rank}. ${p.name} (${p.pos}, ${p.team}) - Bye: ${p.bye}`;
        select.appendChild(opt);
    });
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function startTimer(turnStartTime) {
    if (timerInterval) clearInterval(timerInterval);
    const timerEl = document.getElementById('timer-live');
    const timerBoardEl = document.getElementById('timer-board');
    if (!turnStartTime) {
        timerEl.textContent = '00:00';
        timerBoardEl.textContent = '00:00';
        return;
    }
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() / 1000) - turnStartTime);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        const timeString = `${minutes}:${seconds}`;
        timerEl.textContent = timeString;
        timerBoardEl.textContent = timeString;
    }, 1000);
}

function exportRosters() {
    const state = window.draftState;
    if (!state) return;
    let csvContent = 'Team,Player Name,Position,Team,Bye Week\n';
    state.teams.forEach(team => {
        state.rosters[team].forEach(player => {
            csvContent += `${team},${player.name},${player.pos},${player.team},${player.bye}\n`;
        });
    });
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'fantasy_rosters.csv';
    link.click();
    URL.revokeObjectURL(url);
}

function toggleView(view) {
    document.getElementById('live-view').style.display = view === 'live' ? 'block' : 'none';
    document.getElementById('board-view').style.display = view === 'board' ? 'block' : 'none';
}

socket.on('join_error', (data) => {
    alert(data.msg);
    document.getElementById('admin-password-modal').style.display = 'none';
    document.getElementById('join-section').style.display = 'block';
    document.getElementById('draft-board').style.display = 'none';
});

socket.on('error', (data) => {
    alert(data.msg);
});

socket.on('update_draft', (state) => {
    window.draftState = state;
    const isAdmin = localStorage.getItem('is_admin') === 'true';
    const isSpectator = localStorage.getItem('is_spectator') === 'true';
    if (state.started) {
        document.getElementById('start-btn').style.display = 'none';
    } else {
        document.getElementById('start-btn').style.display = isAdmin ? 'block' : 'none';
        document.getElementById('export-btn').style.display = state.current_round > state.num_rounds ? 'block' : 'none';
        if (!localStorage.getItem('myTeam')) {
            document.getElementById('join-section').style.display = 'block';
            document.getElementById('draft-board').style.display = 'none';
        }
    }

    document.getElementById('admin-controls').style.display = isAdmin ? 'block' : 'none';
    document.getElementById('draft-order-controls').style.display = (isAdmin && !state.started) ? 'block' : 'none';
    document.getElementById('pre-assign-controls').style.display = (isAdmin && !state.started) ? 'block' : 'none';
    document.getElementById('reset-draft-btn').style.display = isAdmin ? 'block' : 'none';

    if (isAdmin) {
        const teamSelect = document.getElementById('admin-team-select');
        teamSelect.innerHTML = '';
        const manualTeamSelect = document.getElementById('admin-manual-team-select');
        manualTeamSelect.innerHTML = '';
        const order = state.current_round <= 2 ? state.teams : (state.current_round % 2 === 1 ? state.teams.slice().reverse() : state.teams);
        const currentTeam = state.started && state.current_round <= state.num_rounds ? 
            (state.assigned_spots[state.current_round]?.[order[state.current_pick]] || order[state.current_pick]) : 
            (state.teams[0] || 'Draft Over');
        state.teams.forEach(team => {
            const opt = document.createElement('option');
            opt.value = team;
            opt.text = team;
            if (team === currentTeam) {
                opt.selected = true;
            }
            teamSelect.appendChild(opt);
            const manualOpt = document.createElement('option');
            manualOpt.value = team;
            manualOpt.text = team;
            if (team === currentTeam) {
                manualOpt.selected = true;
            }
            manualTeamSelect.appendChild(manualOpt);
        });
    }

    if (isAdmin && !state.started) {
        const list = document.getElementById('draft-order-list');
        list.innerHTML = '';
        state.teams.forEach(team => {
            const li = document.createElement('li');
            li.textContent = team;
            list.appendChild(li);
        });
        Sortable.create(list, {
            animation: 150,
            ghostClass: 'sortable-ghost'
        });
    }

    if (isAdmin && !state.started) {
        const assignTeamSelect = document.getElementById('assign-team-select');
        assignTeamSelect.innerHTML = '';
        state.teams.forEach(team => {
            const opt = document.createElement('option');
            opt.value = team;
            opt.text = team;
            assignTeamSelect.appendChild(opt);
        });

        const assignRoundSelect = document.getElementById('assign-round-select');
        assignRoundSelect.innerHTML = '';
        for (let r = 1; r <= state.num_rounds; r++) {
            const opt = document.createElement('option');
            opt.value = r;
            opt.text = `Round ${r}`;
            assignRoundSelect.appendChild(opt);
        }

        const assignPlayerSelect = document.getElementById('assign-player-select');
        assignPlayerSelect.innerHTML = '';
        state.available_players.sort((a, b) => a.rank - b.rank).forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.name;
            opt.text = `${p.rank}. ${p.name} (${p.pos}, ${p.team}) - Bye: ${p.bye}`;
            assignPlayerSelect.appendChild(opt);
        });
    }

    document.getElementById('current-round-live').textContent = state.current_round;
    document.getElementById('current-round-board').textContent = state.current_round;
    const order = state.current_round <= 2 ? state.teams : (state.current_round % 2 === 1 ? state.teams.slice().reverse() : state.teams);
    const currentTeam = state.started && state.current_round <= state.num_rounds ? 
        (state.assigned_spots[state.current_round]?.[order[state.current_pick]] || order[state.current_pick]) : 
        'Draft Over';
    document.getElementById('current-team-live').textContent = currentTeam;
    document.getElementById('current-team-board').textContent = currentTeam;

    const draftStatus = document.getElementById('draft-status');
    const draftCompleteBanner = document.getElementById('draft-complete-banner');
    if (state.current_round > state.num_rounds && !state.started) {
        draftStatus.style.display = 'none';
        draftCompleteBanner.style.display = 'block';
    } else {
        draftStatus.style.display = 'block';
        draftCompleteBanner.style.display = 'none';
    }

    const select = document.getElementById('player-select');
    select.innerHTML = '';
    state.available_players.sort((a, b) => a.rank - b.rank).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.text = `${p.rank}. ${p.name} (${p.pos}, ${p.team}) - Bye: ${p.bye}`;
        select.appendChild(opt);
    });

    document.getElementById('pick-btn').style.display = ((myTeam === currentTeam || isAdmin) && state.started && !state.paused) ? 'block' : 'none';
    document.getElementById('queue-btn').style.display = (!isSpectator && state.current_round <= state.num_rounds) ? 'block' : 'none';
    document.getElementById('player-queue').style.display = (!isSpectator) ? 'block' : 'none';

    const queueList = document.getElementById('queue-list');
    queueList.innerHTML = '';
    const queue = state.player_queues[myTeam] || [];
    const draftedPlayers = new Set(state.draft_history.map(p => p.player.name));
    queue.forEach(p => {
        if (draftedPlayers.has(p.name)) {
            removeFromQueue(p.name);
            return;
        }
        const li = document.createElement('li');
        li.textContent = `${p.rank}. ${p.name} (${p.pos}, ${p.team}) - Bye: ${p.bye}`;
        const removeBtn = document.createElement('button');
        removeBtn.textContent = 'Remove';
        removeBtn.onclick = () => removeFromQueue(p.name);
        li.appendChild(removeBtn);
        const isMyTurn = myTeam === currentTeam && state.started && !state.paused;
        if (isMyTurn) {
            const draftBtn = document.createElement('button');
            draftBtn.textContent = 'Draft';
            draftBtn.classList.add('draft-queue-btn');
            draftBtn.onclick = () => draftFromQueue(p.name);
            li.appendChild(draftBtn);
        }
        queueList.appendChild(li);
    });

    const rostersDiv = document.getElementById('rosters');
    rostersDiv.innerHTML = '';
    state.teams.forEach(team => {
        const div = document.createElement('div');
        div.innerHTML = `<h4>${team}</h4><ul>${state.rosters[team].map(p => `<li>${p.name} (${p.pos}, ${p.team})</li>`).join('')}</ul>`;
        rostersDiv.appendChild(div);
    });

    const table = document.getElementById('draft-grid');
    const thead = table.querySelector('thead tr');
    thead.innerHTML = '<th>Round</th>'; // Reset headers
    state.teams.forEach(team => {
        const th = document.createElement('th');
        const totalTime = state.draft_history
            .filter(p => p.roster_team === team)
            .reduce((sum, p) => sum + (p.time_taken || 0), 0);
        th.innerHTML = `${team}<br><span class="total-time">${formatTime(totalTime)}</span>`;
        thead.appendChild(th);
    });

    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    for (let round = 1; round <= state.num_rounds; round++) {
        const tr = document.createElement('tr');
        const roundTd = document.createElement('td');
        roundTd.textContent = round;
        tr.appendChild(roundTd);

        state.teams.forEach(team => {
            const td = document.createElement('td');
            td.dataset.round = round;
            td.dataset.team = team;
            const pick = state.draft_history.find(p => p.round === round && p.display_team === team);
            if (pick && pick.player) {
                const player = pick.player;
                const nameParts = player.name.split(' ');
                const firstName = nameParts[0];
                const lastName = nameParts.slice(1).join(' ');
                td.innerHTML = `${firstName}<br>${lastName}<br>(${player.pos}, ${player.team}) - Bye: ${player.bye}`;
                const posClass = `pos-${player.pos.toLowerCase()}`;
                td.classList.add(posClass);
                const assigned_team = state.assigned_spots[round]?.[team];
                if (assigned_team && assigned_team !== team) {
                    td.classList.add('assigned');
                    td.innerHTML += `<span class="assigned-text">Traded to ${assigned_team}</span>`;
                }
            } else {
                td.innerHTML = '';
                const assigned_team = state.assigned_spots[round]?.[team];
                if (assigned_team && assigned_team !== team) {
                    td.classList.add('assigned');
                    td.innerHTML = `<span class="assigned-text">Traded to ${assigned_team}</span>`;
                }
            }
            if (isAdmin && !pick && (round > state.current_round || (round === state.current_round && order.indexOf(team) >= state.current_pick))) {
                td.style.cursor = 'pointer';
                td.onclick = () => openSpotAssignmentModal(round, team);
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    }

    if (!state.paused && state.started) {
        startTimer(state.turn_start_time);
    } else if (timerInterval) {
        clearInterval(timerInterval);
    }

    if (isSpectator) {
        document.getElementById('join-section').style.display = 'none';
        document.getElementById('start-btn').style.display = 'none';
        document.querySelector('button[onclick="toggleView(\'live\')"]').style.display = 'none';
        document.querySelector('button[onclick="toggleView(\'board\')"]').style.display = 'none';
        toggleView('board');
        document.getElementById('player-search').style.display = 'none';
        document.getElementById('player-select').style.display = 'none';
        document.getElementById('queue-btn').style.display = 'none';
        document.getElementById('player-queue').style.display = 'none';
    }
});