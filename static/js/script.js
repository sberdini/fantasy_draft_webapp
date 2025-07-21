//const socket = io();
const socket = io('https://brajleaguedraft.onrender.com', { transports: ['websocket'] });
let myTeam = null;
let timerInterval = null;

// Clear localStorage on page load to reset roles for testing
window.addEventListener('load', () => {
    localStorage.clear();
});

function joinDraft() {
    const joinType = document.querySelector('input[name="join-type"]:checked').value;
    const team = document.getElementById('team-name').value.trim();
    let data = {};
    if (joinType === 'spectator') {
        data.is_spectator = true;
    } else if (joinType === 'team') {
        if (!team) {
            alert('Team name required for team join.');
            return;
        }
        data.team = team;
        data.is_admin = false;
    } else if (joinType === 'admin') {
        data.team = team;  // Optional
        data.is_admin = true;
    }
    socket.emit('join', data);
    myTeam = (joinType === 'spectator') ? 'Spectator' : (team || 'Admin');
    localStorage.setItem('myTeam', myTeam);
    localStorage.setItem('is_admin', data.is_admin ? 'true' : 'false');
    localStorage.setItem('is_spectator', data.is_spectator ? 'true' : 'false');
    document.getElementById('join-section').style.display = 'none';
    document.getElementById('draft-board').style.display = 'block';
    document.getElementById('start-btn').style.display = 'block';
}

function startDraft() {
    socket.emit('start_draft');
}

function makePick() {
    const select = document.getElementById('player-select');
    const player = select.value;
    if (player) {
        socket.emit('make_pick', { player });
    }
}

function pauseDraft() {
    socket.emit('pause_draft');
}

function revertPick() {
    socket.emit('revert_pick');
}

function adminMakePick() {
    const select = document.getElementById('player-select');
    const player = select.value;
    const forTeam = document.getElementById('admin-team-select').value;
    if (player && forTeam) {
        socket.emit('admin_make_pick', { player, for_team: forTeam });
    }
}

function saveDraftOrder() {
    const list = document.getElementById('draft-order-list');
    const newOrder = Array.from(list.children).map(li => li.textContent);
    socket.emit('reorder_teams', { new_order: newOrder });
}

function assignPlayer() {
    const team = document.getElementById('assign-team-select').value;
    const round = parseInt(document.getElementById('assign-round-select').value);
    const player = document.getElementById('assign-player-select').value;
    if (team && round && player) {
        socket.emit('assign_pick', { team, round, player });
    } else {
        alert('Please select team, round, and player.');
    }
}

function filterPlayers() {
    const input = document.getElementById('player-search').value.toLowerCase();
    const select = document.getElementById('player-select');
    for (let i = 0; i < select.options.length; i++) {
        const opt = select.options[i];
        const text = opt.text.toLowerCase();
        opt.style.display = text.includes(input) ? '' : 'none';
    }
}

function startTimer(turnStartTime) {
    if (timerInterval) clearInterval(timerInterval);
    const timerEl = document.getElementById('timer-live');
    const timerBoardEl = document.getElementById('timer-board');
    if (!turnStartTime) {
        timerEl.innerText = '00:00';
        timerBoardEl.innerText = '00:00';
        return;
    }
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() / 1000) - turnStartTime);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        const timeString = `${minutes}:${seconds}`;
        timerEl.innerText = timeString;
        timerBoardEl.innerText = timeString;
    }, 1000);
}

function exportRosters() {
    const state = window.draftState;
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
    document.getElementById('join-section').style.display = 'block';
    document.getElementById('draft-board').style.display = 'none';
});

socket.on('update_draft', (state) => {
    window.draftState = state;
    if (state.started) {
        document.getElementById('start-btn').style.display = 'none';
    } else {
        document.getElementById('export-btn').style.display = state.current_round > state.num_rounds ? 'block' : 'none';
    }

    // Show admin controls if admin
    const isAdmin = localStorage.getItem('is_admin') === 'true';
    const isSpectator = localStorage.getItem('is_spectator') === 'true';
    document.getElementById('admin-controls').style.display = isAdmin ? 'block' : 'none';
    document.getElementById('draft-order-controls').style.display = (isAdmin && !state.started) ? 'block' : 'none';
    document.getElementById('pre-assign-controls').style.display = (isAdmin && !state.started) ? 'block' : 'none';

    if (isAdmin) {
        const teamSelect = document.getElementById('admin-team-select');
        teamSelect.innerHTML = '';
        state.teams.forEach(team => {
            const opt = document.createElement('option');
            opt.value = team;
            opt.text = team;
            teamSelect.add(opt);
        });
    }

    if (isAdmin && !state.started) {
        const list = document.getElementById('draft-order-list');
        list.innerHTML = '';
        state.teams.forEach(team => {
            const li = document.createElement('li');
            li.innerText = team;
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
            assignTeamSelect.add(opt);
        });

        const assignRoundSelect = document.getElementById('assign-round-select');
        assignRoundSelect.innerHTML = '';
        for (let r = 1; r <= state.num_rounds; r++) {
            const opt = document.createElement('option');
            opt.value = r;
            opt.text = `Round ${r}`;
            assignRoundSelect.add(opt);
        }

        const assignPlayerSelect = document.getElementById('assign-player-select');
        assignPlayerSelect.innerHTML = '';
        state.available_players.sort((a, b) => a.rank - b.rank).forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.name;
            opt.text = `${p.rank}. ${p.name} (${p.pos}, ${p.team}) - Bye: ${p.bye}`;
            assignPlayerSelect.add(opt);
        });
    }

    // Update round and team for both views
    document.getElementById('current-round-live').innerText = state.current_round;
    document.getElementById('current-round-board').innerText = state.current_round;
    const order = state.current_round % 2 === 1 ? state.teams : state.teams.slice().reverse();
    const currentTeam = order[state.current_pick] || 'Draft Over';
    document.getElementById('current-team-live').innerText = currentTeam;
    document.getElementById('current-team-board').innerText = currentTeam;

    // Update available players
    const select = document.getElementById('player-select');
    select.innerHTML = '';
    state.available_players.sort((a, b) => a.rank - b.rank).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.text = `${p.rank}. ${p.name} (${p.pos}, ${p.team}) - Bye: ${p.bye}`;
        select.add(opt);
    });

    // Show pick button only if it's my turn or admin
    document.getElementById('pick-btn').style.display = ( (myTeam === currentTeam || isAdmin) && state.started && !state.paused ) ? 'block' : 'none';

    // Update rosters
    const rostersDiv = document.getElementById('rosters');
    rostersDiv.innerHTML = '';
    state.teams.forEach(team => {
        const div = document.createElement('div');
        div.innerHTML = `<h4>${team}</h4><ul>${state.rosters[team].map(p => `<li>${p.name} (${p.pos}, ${p.team})</li>`).join('')}</ul>`;
        rostersDiv.appendChild(div);
    });

    // Update draft board grid
    const table = document.getElementById('draft-grid');
    const thead = table.querySelector('thead tr');
    thead.innerHTML = '<th>Round</th>';  // Reset headers
    state.teams.forEach(team => {
        const th = document.createElement('th');
        th.innerText = team;
        thead.appendChild(th);
    });

    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    for (let round = 1; round <= state.num_rounds; round++) {
        const tr = document.createElement('tr');
        const roundTd = document.createElement('td');
        roundTd.innerText = round;
        tr.appendChild(roundTd);

        state.teams.forEach(team => {
            const td = document.createElement('td');
            // Find pick for this team in this round
            const pick = state.draft_history.find(p => p.round === round && p.team === team);
            if (pick) {
                const player = pick.player;
                const nameParts = player.name.split(' ');
                const firstName = nameParts[0];
                const lastName = nameParts.slice(1).join(' ');
                td.innerHTML = `${firstName}<br>${lastName}<br>(${player.pos}, ${player.team}) - Bye: ${player.bye}`;
                // Add class for color-coding
                const posClass = `pos-${player.pos.toLowerCase()}`;
                td.classList.add(posClass);
            } else {
                td.innerText = '';  // Blank for undrafted
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    }

    // Start timer only if not paused
    if (!state.paused) {
        startTimer(state.turn_start_time);
    } else if (timerInterval) {
        clearInterval(timerInterval);
    }

    // For spectators, hide join section and show board by default, hide buttons
    if (localStorage.getItem('is_spectator') === 'true') {
        document.getElementById('join-section').style.display = 'none';
        document.getElementById('start-btn').style.display = 'none';
        document.querySelector('button[onclick="toggleView(\'live\')"]').style.display = 'none';
        document.querySelector('button[onclick="toggleView(\'board\')"]').style.display = 'none';
        toggleView('board');  // Default to board for spectators
        document.getElementById('player-search').style.display = 'none';
        document.getElementById('player-select').style.display = 'none';
    }

});