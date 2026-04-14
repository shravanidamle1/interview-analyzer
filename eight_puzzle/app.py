from flask import Flask, render_template, jsonify, request, session
import heapq
import random
from collections import deque
import time

app = Flask(__name__)
app.secret_key = 'eight_puzzle_ai_2024'

# ─── Goal State ────────────────────────────────────────────
GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)  # 0 = blank tile

# ─── Heuristics ────────────────────────────────────────────

def manhattan_distance(state):
    """Sum of Manhattan distances of each tile from its goal position."""
    total = 0
    goal_pos = {v: (i // 3, i % 3) for i, v in enumerate(GOAL)}
    for i, val in enumerate(state):
        if val == 0:
            continue
        gr, gc = goal_pos[val]
        cr, cc = i // 3, i % 3
        total += abs(gr - cr) + abs(gc - cc)
    return total

def misplaced_tiles(state):
    """Count of tiles not in their goal position."""
    return sum(1 for i, v in enumerate(state) if v != 0 and v != GOAL[i])

# ─── Puzzle Mechanics ──────────────────────────────────────

def get_neighbors(state):
    """Return list of (new_state, move_direction) from current state."""
    neighbors = []
    idx = state.index(0)
    r, c = idx // 3, idx % 3
    moves = [(-1, 0, 'up'), (1, 0, 'down'), (0, -1, 'left'), (0, 1, 'right')]
    for dr, dc, direction in moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            new_state = list(state)
            new_idx = nr * 3 + nc
            new_state[idx], new_state[new_idx] = new_state[new_idx], new_state[idx]
            neighbors.append((tuple(new_state), direction, new_idx))
    return neighbors

def is_solvable(state):
    """Check if puzzle is solvable by counting inversions."""
    flat = [x for x in state if x != 0]
    inversions = 0
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            if flat[i] > flat[j]:
                inversions += 1
    return inversions % 2 == 0

def generate_puzzle(difficulty='medium'):
    """Generate a random solvable puzzle."""
    shuffles = {'easy': 10, 'medium': 30, 'hard': 60}
    n = shuffles.get(difficulty, 30)

    state = list(GOAL)
    for _ in range(n * 5):
        idx = state.index(0)
        r, c = idx // 3, idx % 3
        moves = []
        if r > 0: moves.append(idx - 3)
        if r < 2: moves.append(idx + 3)
        if c > 0: moves.append(idx - 1)
        if c < 2: moves.append(idx + 1)
        swap = random.choice(moves)
        state[idx], state[swap] = state[swap], state[idx]

    return tuple(state)

# ─── A* Solver ─────────────────────────────────────────────

def solve_astar(start, heuristic='manhattan'):
    """A* search algorithm. Returns (path, nodes_explored, time_taken)."""
    h_func = manhattan_distance if heuristic == 'manhattan' else misplaced_tiles

    start_time = time.time()
    open_set = []
    counter = 0  # tiebreaker
    heapq.heappush(open_set, (h_func(start), counter, 0, start, [start]))

    visited = {}  # state -> g_cost
    nodes_explored = 0

    while open_set:
        f, _, g, current, path = heapq.heappop(open_set)
        nodes_explored += 1

        if current == GOAL:
            return path, nodes_explored, round(time.time() - start_time, 4)

        if current in visited and visited[current] <= g:
            continue
        visited[current] = g

        for new_state, direction, _ in get_neighbors(current):
            new_g = g + 1
            new_h = h_func(new_state)
            new_f = new_g + new_h
            if new_state not in visited or visited.get(new_state, float('inf')) > new_g:
                counter += 1
                heapq.heappush(open_set, (new_f, counter, new_g, new_state, path + [new_state]))

    return None, nodes_explored, round(time.time() - start_time, 4)

# ─── BFS Solver ────────────────────────────────────────────

def solve_bfs(start):
    """BFS solver. Returns (path, nodes_explored, time_taken)."""
    start_time = time.time()
    if start == GOAL:
        return [start], 0, 0

    queue = deque()
    queue.append((start, [start]))
    visited = {start}
    nodes_explored = 0

    while queue:
        current, path = queue.popleft()
        nodes_explored += 1

        for new_state, _, _ in get_neighbors(current):
            if new_state == GOAL:
                return path + [new_state], nodes_explored, round(time.time() - start_time, 4)
            if new_state not in visited:
                visited.add(new_state)
                queue.append((new_state, path + [new_state]))

    return None, nodes_explored, round(time.time() - start_time, 4)

# ─── Routes ────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new_puzzle', methods=['POST'])
def new_puzzle():
    data = request.get_json()
    difficulty = data.get('difficulty', 'medium')
    state = generate_puzzle(difficulty)
    session['state'] = list(state)
    session['initial'] = list(state)
    session['moves'] = 0
    session['difficulty'] = difficulty
    return jsonify({
        'state': list(state),
        'goal': list(GOAL),
        'moves': 0,
        'solved': state == GOAL,
        'manhattan': manhattan_distance(state),
        'misplaced': misplaced_tiles(state)
    })

@app.route('/api/move', methods=['POST'])
def move_tile():
    data = request.get_json()
    tile_index = data.get('tile_index')  # index of tile clicked

    if 'state' not in session:
        return jsonify({'error': 'No puzzle in session'}), 400

    state = tuple(session['state'])
    blank_idx = state.index(0)

    # Check if clicked tile is adjacent to blank
    br, bc = blank_idx // 3, blank_idx % 3
    tr, tc = tile_index // 3, tile_index % 3

    if abs(br - tr) + abs(bc - tc) != 1:
        return jsonify({'valid': False, 'state': list(state)})

    new_state = list(state)
    new_state[blank_idx], new_state[tile_index] = new_state[tile_index], new_state[blank_idx]
    new_state = tuple(new_state)

    session['state'] = list(new_state)
    session['moves'] = session.get('moves', 0) + 1

    solved = new_state == GOAL
    return jsonify({
        'valid': True,
        'state': list(new_state),
        'moves': session['moves'],
        'solved': solved,
        'blank_moved_to': tile_index,
        'manhattan': manhattan_distance(new_state),
        'misplaced': misplaced_tiles(new_state)
    })

@app.route('/api/solve', methods=['POST'])
def solve():
    data = request.get_json()
    algorithm = data.get('algorithm', 'astar')
    heuristic = data.get('heuristic', 'manhattan')

    if 'state' not in session:
        return jsonify({'error': 'No puzzle'}), 400

    state = tuple(session['state'])

    if state == GOAL:
        return jsonify({'path': [list(state)], 'steps': 0, 'nodes': 0, 'time': 0, 'already_solved': True})

    if algorithm == 'astar':
        path, nodes, t = solve_astar(state, heuristic)
    else:
        path, nodes, t = solve_bfs(state)

    if path is None:
        return jsonify({'error': 'No solution found'}), 400

    return jsonify({
        'path': [list(s) for s in path],
        'steps': len(path) - 1,
        'nodes': nodes,
        'time': t,
        'algorithm': algorithm,
        'heuristic': heuristic if algorithm == 'astar' else 'none'
    })

@app.route('/api/hint', methods=['POST'])
def hint():
    """Return the next best move using A*."""
    if 'state' not in session:
        return jsonify({'error': 'No puzzle'}), 400

    state = tuple(session['state'])
    path, _, _ = solve_astar(state, 'manhattan')

    if path and len(path) > 1:
        next_state = path[1]
        blank_now = state.index(0)
        blank_next = next_state.index(0)
        # The tile that moved is the one that was at blank_next in current state
        tile_that_moves = state[blank_next]
        return jsonify({
            'next_state': list(next_state),
            'tile_index': blank_next,   # where to click
            'tile_value': tile_that_moves,
            'steps_remaining': len(path) - 1
        })
    return jsonify({'already_solved': True})

@app.route('/api/reset', methods=['POST'])
def reset():
    if 'initial' not in session:
        return jsonify({'error': 'No puzzle'}), 400
    session['state'] = session['initial'][:]
    session['moves'] = 0
    state = tuple(session['state'])
    return jsonify({
        'state': list(state),
        'moves': 0,
        'solved': state == GOAL,
        'manhattan': manhattan_distance(state),
        'misplaced': misplaced_tiles(state)
    })

@app.route('/api/set_state', methods=['POST'])
def set_state():
    """Set a custom puzzle state."""
    data = request.get_json()
    state = tuple(data.get('state', []))
    if len(state) != 9 or set(state) != set(range(9)):
        return jsonify({'error': 'Invalid state'}), 400
    if not is_solvable(state):
        return jsonify({'error': 'This puzzle configuration is not solvable!'}), 400
    session['state'] = list(state)
    session['initial'] = list(state)
    session['moves'] = 0
    return jsonify({
        'state': list(state),
        'moves': 0,
        'solved': state == GOAL,
        'manhattan': manhattan_distance(state),
        'misplaced': misplaced_tiles(state)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
