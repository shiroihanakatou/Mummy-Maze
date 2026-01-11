"""Save/Load system for Mummy Maze - Local and Firebase"""
import json
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import time
from variable import debug_log

FIREBASE_URL = "https://mummy-maze-43e73-default-rtdb.asia-southeast1.firebasedatabase.app"

# Reuse a single HTTP session (faster TLS + keep-alive)
_HTTP = requests.Session()
_HTTP.headers.update({
    "Content-Type": "application/json",
    "Accept": "application/json"
})

def get_save_dir():
    """Ensure save directory exists"""
    save_dir = Path("save")
    save_dir.mkdir(exist_ok=True)
    return save_dir

def generate_guest_id():
    """Generate unique guest ID"""
    return f"guest_{uuid.uuid4().hex[:8]}"

def serialize_game_state(player, enemies, gamestate, grid, mode: str):
    """Convert current game state to JSON-serializable dict.
    For classic mode, saves map in the same format as level JSON files."""
    # Determine difficulty string
    if getattr(gamestate, "impossible_mode", False):
        diff_str = "impossible"
    elif gamestate.enemy_count == 1:
        diff_str = "easy"
    elif gamestate.enemy_count == 2:
        diff_str = "medium"
    else:
        diff_str = "hard"
    
    grid_size = len(grid)
    
    state = {
        "difficulty": diff_str,
        "impossible_mode": getattr(gamestate, "impossible_mode", False),
        "grid_size": grid_size,
        "chapter": getattr(gamestate, "chapter", 1),
        "level": getattr(gamestate, "level", 1),
        "player": {
            "row": player.row,
            "col": player.col,
            "direction": getattr(player, "direction", "down")
        },
        "enemies": [
            {
                "type": getattr(e, "type", "red_mummy"),
                "row": e.row,
                "col": e.col,
                "direction": getattr(e, "direction", "down")
            }
            for e in enemies
        ],
        "goal": {
            "row": gamestate.goal_row,
            "col": gamestate.goal_col
        },
        "items": {
            "keys": [list(k) for k in getattr(gamestate, "keys", set())],
            "traps": [list(t) for t in getattr(gamestate, "traps", set())],
            "has_key": getattr(gamestate, "has_key", False)
        },
        "gates": {
            "positions": [list(pos) for pos in getattr(gamestate, "gates_h", {}).keys()],
            "states": [state for state in getattr(gamestate, "gates_h", {}).values()]
        }
    }
    
    # For classic mode, save map data in level JSON format
    map_data = None
    if mode == "classic" or mode == "adventure":
        try:
            # Build tiles string (same format as level JSON)
            tiles = []
            for r in range(grid_size):
                row_str = ""
                for c in range(grid_size):
                    # Default empty cell
                    ch = "."
                    # Check for player
                    if player.row == r and player.col == c:
                        ch = "P"
                    # Check for enemies
                    for en in enemies:
                        if en.row == r and en.col == c:
                            if "white" in getattr(en, "type", ""):
                                ch = "W"
                            elif "scorpion" in getattr(en, "type", ""):
                                ch = "S"
                            else:
                                ch = "R"
                    # Check for key
                    if (r, c) in getattr(gamestate, "keys", set()):
                        if ch == ".":
                            ch = "K"
                    # Check for trap
                    if (r, c) in getattr(gamestate, "traps", set()):
                        if ch == ".":
                            ch = "T"
                    # Check for exit
                    if r == gamestate.goal_row and c == gamestate.goal_col:
                        if ch == ".":
                            ch = "E"
                    row_str += ch
                tiles.append(row_str)
        
            # Build walls_v strings (vertical walls between columns)
            # walls_v has grid_size rows and grid_size+1 columns
            walls_v = []
            for r in range(grid_size):
                row_str = ""
                for c in range(grid_size + 1):
                    if c == 0:
                        # Left border - check if cell has left wall
                        if grid[r][0].left == 1:
                            row_str += "|"
                        else:
                            row_str += " "
                    elif c == grid_size:
                        # Right border - check if last cell has right wall
                        if grid[r][c-1].right == 1:
                            row_str += "|"
                        else:
                            row_str += " "
                    else:
                        # Between cells - check if left cell has right wall or right cell has left wall
                        if grid[r][c].left == 1:
                            row_str += "|"
                        else:
                            row_str += " "
                walls_v.append(row_str)
        
            # Build walls_h strings (horizontal walls between rows)
            # walls_h has grid_size+1 rows and grid_size columns
            walls_h = []
            for r in range(grid_size + 1):
                row_str = ""
                for c in range(grid_size):
                    if r == 0:
                        # Top border - check if cell has up wall (always closed)
                        row_str += "-"
                    elif r == grid_size:
                        # Bottom border
                        row_str += "-"
                    else:
                        # Between rows - check cell above's down wall
                        cell_down = grid[r-1][c].down
                        if cell_down == 1:
                            row_str += "-"  # Wall
                        elif cell_down == 2:
                            row_str += "="  # Closed gate
                        elif cell_down == 3:
                            row_str += "~"  # Open gate
                        else:
                            row_str += " "  # No wall
                walls_h.append(row_str)
        
            map_data = {
                "size": {"rows": grid_size, "cols": grid_size},
                "tiles": tiles,
                "walls_v": walls_v,
                "walls_h": walls_h,
                "exit": {"row": gamestate.goal_row, "col": gamestate.goal_col}
            }
        except Exception as e:
            debug_log(f"[SAVE] Error building map_data: {e}")
            map_data = None
    
    # Serialize move history
    move_history = []
    for snapshot in getattr(gamestate, "storedmove", []):
        if len(snapshot) >= 4:
            p_row, p_col, p_dir, enemies_state = snapshot[:4]
            keys_state = snapshot[4] if len(snapshot) > 4 else set()
            gates_state = snapshot[5] if len(snapshot) > 5 else {}
            
            move_history.append({
                "player": [p_row, p_col, p_dir],
                "enemies": [[e[0], e[1], e[2], e[3]] for e in enemies_state],
                "keys": [list(k) for k in keys_state],
                "gates": {str(k): v for k, v in gates_state.items()}
            })
    
    return state, map_data, move_history

# New: Separate serializers per mode for clarity and correctness
def serialize_classic(player, enemies, gamestate, grid):
    """Serialize classic mode: returns (state, map_data, move_history)."""
    mode = "classic"
    state, map_data, move_history = serialize_game_state(player, enemies, gamestate, grid, mode)
    # Debug log summary
    try:
        v_bar = sum(row.count('|') for row in map_data['walls_v']) if map_data else 0
        h_wall = sum(row.count('-') for row in map_data['walls_h']) if map_data else 0
        h_gate_closed = sum(row.count('=') for row in map_data['walls_h']) if map_data else 0
        h_gate_open = sum(row.count('~') for row in map_data['walls_h']) if map_data else 0
        exit_marks = sum(row.count('E') for row in map_data['tiles']) if map_data else 0
        debug_log(f"[SAVE][CLASSIC] grid={state.get('grid_size')} tiles={len(map_data['tiles']) if map_data else 0} vbars={v_bar} hwalls={h_wall} gates(closed={h_gate_closed},open={h_gate_open}) exits={exit_marks}")
    except Exception as e:
        debug_log(f"[SAVE][CLASSIC] debug summary failed: {e}")
    return state, map_data, move_history

def serialize_adventure(player, enemies, gamestate, grid):
    """Serialize adventure mode: returns (state, move_history) without map_data."""
    mode = "adventure"
    state, _map_data_unused, move_history = serialize_game_state(player, enemies, gamestate, grid, mode)
    # Debug log summary
    debug_log(f"[SAVE][ADVENTURE] grid_size={state.get('grid_size')} chapter={state.get('chapter')} level={state.get('level')} moves={len(move_history)}")
    return state,_map_data_unused, move_history

def create_save_data(username: str, password: Optional[str], is_guest: bool, score: int,
                     adventure_state=None, classic_state=None, skin: str = "explorer", 
                     owned_skins: list = None):
    """Create complete save data structure"""
    if owned_skins is None:
        owned_skins = ["explorer"]  # Explorer is free by default
    return {
        "player_info": {
            "username": username,
            "password": password,
            "is_guest": is_guest,
            "score": score,
            "skin": skin,
            "owned_skins": owned_skins
        },
        "adventure": adventure_state or {"game_state": None, "map_data": None, "move_history": []},
        "classic": classic_state or {"game_state": None, "map_data": None, "move_history": []}
    }

def save_local(username: str, save_data: Dict[str, Any]) -> bool:
    """Save to local JSON file"""
    try:
        save_path = get_save_dir() / f"{username}.json"
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        debug_log(f"[SaveLoad] Local save failed: {e}")
        return False

def load_local(username: str) -> Optional[Dict[str, Any]]:
    """Load from local JSON file"""
    try:
        save_path = get_save_dir() / f"{username}.json"
        if not save_path.exists():
            return None
        with open(save_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        debug_log(f"[SaveLoad] Local load failed: {e}")
        return None

def list_local_saves(limit: int = 5):
    """List up to `limit` local save profile names (without .json extension)."""
    save_dir = get_save_dir()
    profiles = []
    try:
        files = sorted(save_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in files[:limit]:
            profiles.append(p.stem)
    except Exception as e:
        debug_log(f"[SaveLoad] list_local_saves failed: {e}")
    return profiles

def save_firebase(username: str, save_data: Dict[str, Any]) -> bool:
    """Save to Firebase RTDB (requests)."""
    try:
        url = f"{FIREBASE_URL}/saves/{username}.json"

        r = _HTTP.put(url, json=save_data, timeout=(2, 5))
        ok = (200 <= r.status_code < 300)

        # Keep leaderboard as a separate lightweight node (Firebase only).
        # This avoids downloading massive save blobs when rendering leaderboard.
        try:
            if ok:
                player_info = (save_data or {}).get("player_info", {}) if isinstance(save_data, dict) else {}
                is_guest = bool(player_info.get("is_guest", False))
                score = int(player_info.get("score", 0) or 0)
                if (not is_guest) and score > 0:
                    update_leaderboard(username, score)
        except Exception as ex:
            debug_log(f"[SaveLoad] Leaderboard update skipped: {ex}")

        return ok
    except Exception as e:
        debug_log(f"[SaveLoad] Firebase save failed: {e}")
        return False

def load_firebase(username: str) -> Optional[Dict[str, Any]]:
    """Load from Firebase RTDB (requests)."""
    try:
        url = f"{FIREBASE_URL}/saves/{username}.json"
        r = _HTTP.get(url, timeout=(2, 5))
        if not (200 <= r.status_code < 300):
            return None
        data = r.json()
        return data if data else None
    except Exception as e:
        debug_log(f"[SaveLoad] Firebase load failed: {e}")
        return None

def update_leaderboard(username: str, score: int) -> bool:
    """Update Firebase leaderboard entry for a user (Firebase only, requests)."""
    try:
        url = f"{FIREBASE_URL}/leaderboard/{username}.json"
        payload = {"score": int(score), "ts": int(time.time())}

        r = _HTTP.put(url, json=payload, timeout=(2, 3))
        return (200 <= r.status_code < 300)
    except Exception as e:
        debug_log(f"[SaveLoad] Leaderboard update failed: {e}")
        return False

def get_leaderboard(limit: int = 10) -> list:
    """Get top scores from Firebase leaderboard (Firebase only, requests).

    Reads from /leaderboard, not /saves (fast).
    """
    try:
        limit = int(limit) if limit else 10
        if limit <= 0:
            return []

        # Query only the highest `limit` scores.
        # Firebase returns ascending; we reverse after parsing.
        url = f"{FIREBASE_URL}/leaderboard.json"
        params = {"orderBy": '"score"', "limitToLast": str(limit)}
        r = _HTTP.get(url, params=params, timeout=(2, 5))
        if not (200 <= r.status_code < 300):
            return []
        data = r.json()
        print(data,url)
        if not data or not isinstance(data, dict):
            return []

        scores = []
        for username, entry in data.items():
            if entry and isinstance(entry, dict):
                score = int(entry.get("score", 0) or 0)
                if score > 0:
                    scores.append({"username": username, "score": score})

        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:limit]
    except Exception as e:
        debug_log(f"[SaveLoad] Leaderboard fetch failed: {e}")
        return []

def calculate_score(difficulty: str, minutes: float, actual_moves: int, solution_len: int, is_adventure: bool = False) -> dict:
    """Calculate score based on difficulty, time, and move efficiency
    
    New formula:
    - Base points: 100 (easy), 200 (medium), 500 (hard), 1000 (impossible)
    - Adventure mode: doubles base points
    - Time bonus: base_points * 3 / minutes
    - Move bonus: base_points * 3 * (solution_len / actual_moves)
    
    Returns dict with breakdown: base, time_bonus, move_bonus, total
    """
    if minutes <= 0 or actual_moves <= 0 or solution_len <= 0:
        return {"base": 0, "time_bonus": 0, "move_bonus": 0, "total": 0}
    
    base_scores = {
        "easy": 100,
        "medium": 200,
        "hard": 500,
        "impossible": 1000
    }
    
    base = base_scores.get(difficulty, 100)
    
    # Adventure mode doubles base points
    if is_adventure:
        base *= 2
    
    # Time bonus: faster = higher bonus
    time_bonus = int(base * 3 / minutes)
    
    # Move bonus: fewer moves = higher bonus (capped at optimal)
    move_ratio = min(1.0, solution_len / actual_moves)
    move_bonus = int(base * 3 * move_ratio)
    
    total = base + time_bonus + move_bonus
    
    return {
        "base": base,
        "time_bonus": time_bonus,
        "move_bonus": move_bonus,
        "total": total
    }

def verify_login(username: str, password: str) -> bool:
    """Verify login credentials (local first, then Firebase)"""
    # Try local first
    save_data = load_local(username)
    if save_data:
        player_info = save_data.get("player_info", {})
        return player_info.get("password") == password
    
    # Try Firebase
    save_data = load_firebase(username)
    if save_data:
        player_info = save_data.get("player_info", {})
        return player_info.get("password") == password
    
    return False

def create_account(username: str, password: str) -> bool:
    """Create new account (check if username exists)"""
    # Check local
    if load_local(username):
        return False
    
    # Check Firebase
    if load_firebase(username):
        return False
    
    # Create new save
    save_data = create_save_data(username, password, False, 0)
    
    # Save both local and online
    local_ok = save_local(username, save_data)
    firebase_ok = save_firebase(username, save_data)
    
    return local_ok or firebase_ok
