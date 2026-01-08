"""Save/Load system for Mummy Maze - Local and Firebase"""
import json
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
import urllib.request
import urllib.error

FIREBASE_URL = "https://mummy-maze-43e73-default-rtdb.asia-southeast1.firebasedatabase.app"

def get_save_dir():
    """Ensure save directory exists"""
    save_dir = Path("save")
    save_dir.mkdir(exist_ok=True)
    return save_dir

def generate_guest_id():
    """Generate unique guest ID"""
    return f"guest_{uuid.uuid4().hex[:8]}"

def serialize_game_state(player, enemies, gamestate, grid, mode: str):
    """Convert current game state to JSON-serializable dict"""
    state = {
        "difficulty": "easy" if gamestate.enemy_count == 1 else ("medium" if gamestate.enemy_count == 2 else "hard"),
        "grid_size": len(grid),
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
    
    # For classic mode, save map data
    map_data = None
    if mode == "classic":
        tiles = []
        walls_v = []
        walls_h = []
        for row in grid:
            tile_row = []
            wall_v_row = []
            wall_h_row = []
            for cell in row:
                tile_row.append(cell.down if hasattr(cell, 'down') else 0)
                wall_v_row.append(cell.left if hasattr(cell, 'left') else 0)
                wall_h_row.append(cell.down if hasattr(cell, 'down') else 0)
            tiles.append(tile_row)
            walls_v.append(wall_v_row)
            walls_h.append(wall_h_row)
        
        map_data = {
            "tiles": tiles,
            "walls_v": walls_v,
            "walls_h": walls_h
        }
    
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

def create_save_data(username: str, password: Optional[str], is_guest: bool, score: int,
                     adventure_state=None, classic_state=None):
    """Create complete save data structure"""
    return {
        "player_info": {
            "username": username,
            "password": password,
            "is_guest": is_guest,
            "score": score
        },
        "adventure": adventure_state or {"game_state": None, "move_history": []},
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
        print(f"[SaveLoad] Local save failed: {e}")
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
        print(f"[SaveLoad] Local load failed: {e}")
        return None

def save_firebase(username: str, save_data: Dict[str, Any]) -> bool:
    """Save to Firebase RTDB"""
    try:
        url = f"{FIREBASE_URL}/saves/{username}.json"
        data = json.dumps(save_data).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='PUT')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        print(f"[SaveLoad] Firebase save failed: {e}")
        return False

def load_firebase(username: str) -> Optional[Dict[str, Any]]:
    """Load from Firebase RTDB"""
    try:
        url = f"{FIREBASE_URL}/saves/{username}.json"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data if data else None
    except Exception as e:
        print(f"[SaveLoad] Firebase load failed: {e}")
        return None

def get_leaderboard(limit: int = 10) -> list:
    """Get top scores from Firebase leaderboard"""
    try:
        url = f"{FIREBASE_URL}/saves.json"
        with urllib.request.urlopen(url, timeout=5) as response:
            all_saves = json.loads(response.read().decode('utf-8'))
            
            if not all_saves:
                return []
            
            # Extract scores with usernames
            scores = []
            for username, save_data in all_saves.items():
                if save_data and isinstance(save_data, dict):
                    player_info = save_data.get("player_info", {})
                    score = player_info.get("score", 0)
                    is_guest = player_info.get("is_guest", False)
                    
                    # Skip guests or invalid scores
                    if not is_guest and score > 0:
                        scores.append({
                            "username": username,
                            "score": score
                        })
            
            # Sort by score descending
            scores.sort(key=lambda x: x["score"], reverse=True)
            return scores[:limit]
            
    except Exception as e:
        print(f"[SaveLoad] Leaderboard fetch failed: {e}")
        return []

def calculate_score(difficulty: str, minutes: float, actual_moves: int, solution_len: int) -> int:
    """Calculate score based on difficulty, time, and move efficiency
    
    Formula: base_score / minutes * (solution_len / actual_moves)
    """
    if minutes <= 0 or actual_moves <= 0 or solution_len <= 0:
        return 0
    
    base_scores = {
        "easy": 1000,
        "medium": 2000,
        "hard": 5000
    }
    
    base = base_scores.get(difficulty, 1000)
    move_ratio = min(1.0, solution_len / actual_moves)  # Cap at 1.0
    
    score = int((base / minutes) * move_ratio)
    return max(0, score)

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
