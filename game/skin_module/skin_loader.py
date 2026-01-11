"""Skin loader utilities for loading character skins from JSON files"""
import pygame
import json
from pathlib import Path

# Path to characters folder
CHARACTERS_DIR = Path("assets/characters")


# Available character skins (skin_id -> {name, cost})
# Will be auto-populated from JSON files in CHARACTERS_DIR
AVAILABLE_SKINS = {}



def _discover_skins():
    """Auto-discover all available skins from characters directory."""
    global AVAILABLE_SKINS
    # Always include explorer as built-in
    AVAILABLE_SKINS.clear()
    AVAILABLE_SKINS["explorer"] = {"name": "Explorer", "cost": 0}
    # Scan for all *.json files in CHARACTERS_DIR
    if CHARACTERS_DIR.exists():
        for json_file in CHARACTERS_DIR.glob("*.json"):
            skin_id = json_file.stem
            if skin_id == "explorer":
                continue  # Already added
            try:
                with open(json_file, "r") as f:
                    skin_data = json.load(f)
                name = skin_data.get("name", skin_id.title())
                cost = skin_data.get("cost", 1000)
                AVAILABLE_SKINS[skin_id] = {"name": name, "cost": cost}
            except Exception as e:
                print(f"[Skin] Error reading {json_file}: {e}")


def get_skin_info(skin_id: str) -> dict:
    """Get skin info including name and cost"""
    if skin_id in AVAILABLE_SKINS:
        return AVAILABLE_SKINS[skin_id].copy()
    return {"name": skin_id.title(), "cost": 0}


# Auto-discover skins at module load time
_discover_skins()


def load_skin(skin_id: str, entity):
    """Load a character skin and apply it to an entity.
    
    Args:
        skin_id: The skin identifier (e.g., 'explorer', 'ash')
        entity: The entity (Player) to apply the skin to
        
    Returns:
        True if skin loaded successfully, False otherwise
    """
    from module import add_sprite_frames
    
    entity.skin = skin_id
    
    if skin_id == "explorer":
        # Default explorer skin - use standard spritesheet
        entity.type = "explorer"
        entity.skin_scale = 1.0
        add_sprite_frames(entity)
        return True
    
    # Try to load custom skin from characters folder
    json_path = CHARACTERS_DIR / f"{skin_id}.json"
    
    if not json_path.exists():
        print(f"[Skin] Skin '{skin_id}' not found, using default")
        entity.skin = "explorer"
        entity.type = "explorer"
        entity.skin_scale = 1.0
        add_sprite_frames(entity)
        return False
    
    try:
        with open(json_path, "r") as f:
            skin_data = json.load(f)
        
        # Load the spritesheet image
        png_path = CHARACTERS_DIR / f"{skin_id}.png"
        if not png_path.exists():
            raise FileNotFoundError(f"Spritesheet {png_path} not found")
        
        sheet = pygame.image.load(str(png_path)).convert_alpha()
        
        # Apply background color filter if specified
        bg_color = skin_data.get("background_color")
        if bg_color:
            sheet = sheet.copy()
            # Chuẩn hóa danh sách màu
            colors = []
            if isinstance(bg_color, list) and len(bg_color) >= 3:
                for i in range(0, len(bg_color), 3):
                    color = tuple(bg_color[i:i+3])
                    if len(color) == 3:
                        colors.append(color)
            else:
                colors.append(tuple(bg_color))
            # Duyệt từng pixel và set alpha=0 nếu trùng màu colorkey
            arr = pygame.surfarray.pixels3d(sheet)
            alpha = pygame.surfarray.pixels_alpha(sheet)
            w, h = sheet.get_size()
            for color in colors:
                r, g, b = color
                mask = (arr[:,:,0] == r) & (arr[:,:,1] == g) & (arr[:,:,2] == b)
                alpha[mask] = 0
            del arr
            del alpha
        
        # Get sprite info
        sprites = skin_data.get("sprites", {})
        frames_per_row = skin_data.get("len", 1)  # Number of frames per row
        move_script = skin_data.get("move_script", {})
        
        entity.frames = {"up": [], "right": [], "down": [], "left": []}
        
        # Process each direction
        for direction in ["up", "down", "left", "right"]:
            sprite_info = sprites.get(direction)
            if not sprite_info:
                continue
            
            # Get the row rect (contains all frames for this direction)
            rect = sprite_info.get("atlas_rect", sprite_info.get("src_rect"))
            if not rect:
                continue
            
            x, y, total_w, h = rect
            frame_w = total_w // frames_per_row  # Width of each frame
            
            # Extract individual frames from the row
            direction_frames = []
            for i in range(frames_per_row):
                frame_x = x + i * frame_w
                frame_rect = pygame.Rect(frame_x, y, frame_w, h)
                frame = sheet.subsurface(frame_rect).copy()
                direction_frames.append(frame)
            
            # Apply move_script to create animation sequence
            script = move_script.get(direction, list(range(frames_per_row)))
            for frame_idx in script:
                if 0 <= frame_idx < len(direction_frames):
                    entity.frames[direction].append(direction_frames[frame_idx])
            
            # Ensure we have at least 5 frames (pad if needed)
            while len(entity.frames[direction]) < 5:
                entity.frames[direction].append(entity.frames[direction][-1] if entity.frames[direction] else direction_frames[0])
        

        # Handle missing left/right by flipping
        if not entity.frames["left"] or all(f is None for f in entity.frames["left"]):
            if entity.frames["right"]:
                entity.frames["left"] = [pygame.transform.flip(f, True, False) for f in entity.frames["right"]]
        if not entity.frames["right"] or all(f is None for f in entity.frames["right"]):
            if entity.frames["left"]:
                entity.frames["right"] = [pygame.transform.flip(f, True, False) for f in entity.frames["left"]]

        # Update animation sequence based on move_script length
        first_script = list(move_script.values())[0] if move_script else [0, 1, 2, 3, 4]
        entity.anim_sequences["move"] = list(range(len(first_script)))

        # Store frame dimensions
        first_dir = list(sprites.values())[0]
        rect = first_dir.get("atlas_rect", first_dir.get("src_rect"))
        entity.frame_w = rect[2] // frames_per_row
        entity.frame_h = rect[3]

        # Custom skins need extra scaling (default explorer is ~60px, custom may be smaller)
        # Scale factor from JSON, or calculate based on frame height
        entity.skin_scale = skin_data.get("scale", 2.0)  # Default 2x for custom skins

        print(f"[Skin] Loaded skin '{skin_id}' successfully (frames_per_row={frames_per_row}, scale={entity.skin_scale})")
        return True
        
    except Exception as e:
        print(f"[Skin] Error loading skin '{skin_id}': {e}")
        import traceback
        traceback.print_exc()
        entity.skin = "explorer"
        entity.type = "explorer"
        entity.skin_scale = 1.0
        add_sprite_frames(entity)
        return False


def get_skin_preview(skin_id: str, target_size: int = 120):
    """Load a preview image for a skin.
    
    Args:
        skin_id: The skin identifier
        target_size: Target size for the preview image
        
    Returns:
        pygame.Surface or None if failed
    """
    try:
        if skin_id == "explorer":
            # Default explorer - use first frame from spritesheet
            sheet = pygame.image.load("assets/images/explorer6.png").convert_alpha()
            frame_w = sheet.get_width() // 5
            frame_h = sheet.get_height() // 4
            # Get the "down" direction first frame (row 2, col 0)
            preview = sheet.subsurface(pygame.Rect(0, frame_h * 2, frame_w, frame_h)).copy()
            
            # Scale with smoothscale for explorer
            w, h = preview.get_size()
            scale = min(target_size / w, target_size / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            return pygame.transform.smoothscale(preview, (new_w, new_h))
        else:
            # Custom skin from characters folder
            json_path = CHARACTERS_DIR / f"{skin_id}.json"
            png_path = CHARACTERS_DIR / f"{skin_id}.png"
            
            if json_path.exists() and png_path.exists():
                with open(json_path, "r") as f:
                    skin_data = json.load(f)
                
                sheet = pygame.image.load(str(png_path)).convert_alpha()
                
                # Apply background color filter if specified
                bg_color = skin_data.get("background_color")
                if bg_color:
                    sheet = sheet.copy()
                    colors = []
                    if isinstance(bg_color, list) and len(bg_color) >= 3:
                        for i in range(0, len(bg_color), 3):
                            color = tuple(bg_color[i:i+3])
                            if len(color) == 3:
                                colors.append(color)
                    else:
                        colors.append(tuple(bg_color))
                    arr = pygame.surfarray.pixels3d(sheet)
                    alpha = pygame.surfarray.pixels_alpha(sheet)
                    w, h = sheet.get_size()
                    for color in colors:
                        r, g, b = color
                        mask = (arr[:,:,0] == r) & (arr[:,:,1] == g) & (arr[:,:,2] == b)
                        alpha[mask] = 0
                    del arr
                    del alpha
                
                sprites = skin_data.get("sprites", {})
                frames_per_row = skin_data.get("len", 1)
                
                # Use "down" direction for preview, or first available
                sprite_info = sprites.get("down") or list(sprites.values())[0] if sprites else None
                
                if sprite_info:
                    rect = sprite_info.get("atlas_rect", sprite_info.get("src_rect"))
                    if rect:
                        x, y, total_w, h = rect
                        frame_w = total_w // frames_per_row
                        # Get first frame of the row
                        preview = sheet.subsurface(pygame.Rect(x, y, frame_w, h)).copy()
                        
                        # Scale with nearest-neighbor for pixel art
                        w, h = preview.get_size()
                        scale = min(target_size / w, target_size / h)
                        new_w = int(w * scale)
                        new_h = int(h * scale)
                        return pygame.transform.scale(preview, (new_w, new_h))
        
        return None
        
    except Exception as e:
        print(f"[Skin] Error loading preview for {skin_id}: {e}")
        return None
