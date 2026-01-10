"""Character skin selection screen with shop functionality"""
import pygame
from .skin_loader import AVAILABLE_SKINS, get_skin_preview, get_skin_info


class CharacterSkinScreen:
    """Character skin selection/shop screen with single skin view and buy/select functionality"""
    
    def __init__(self):
        self.font_large = pygame.font.SysFont("Verdana", 48, bold=True)
        self.font_normal = pygame.font.SysFont("Verdana", 24)
        self.font_small = pygame.font.SysFont("Verdana", 18)
        self.font_price = pygame.font.SysFont("Verdana", 32, bold=True)
        
        self.selected_skin = "explorer"
        self.current_index = 0  # Index of currently displayed skin
        self.skin_list = list(AVAILABLE_SKINS.keys())  # List of skin IDs
        
        self.skin_previews = {}  # skin_id -> pygame.Surface
        
        # Button rects (set during draw)
        self.left_arrow_rect = None
        self.right_arrow_rect = None
        self.action_btn_rect = None  # BUY or SELECT button
        self.back_rect = None
        
        # User info (set by main.py before drawing)
        self.user_points = 0
        self.owned_skins = ["explorer"]
        
        self._load_previews()
    
    def _load_previews(self):
        """Load preview images for all available skins"""
        for skin_id in self.skin_list:
            preview = get_skin_preview(skin_id, target_size=180)
            if preview:
                self.skin_previews[skin_id] = preview
    
    def set_user_data(self, points: int, owned_skins: list, current_skin: str):
        """Set user data for shop functionality"""
        self.user_points = points
        self.owned_skins = owned_skins if owned_skins else ["explorer"]
        self.selected_skin = current_skin
        # Set index to current skin
        if current_skin in self.skin_list:
            self.current_index = self.skin_list.index(current_skin)
    
    def _get_current_skin_id(self) -> str:
        """Get the currently displayed skin ID"""
        if 0 <= self.current_index < len(self.skin_list):
            return self.skin_list[self.current_index]
        return "explorer"
    
    def set_selected(self, skin_id: str):
        """Set the currently selected/equipped skin"""
        if skin_id in self.skin_list:
            self.selected_skin = skin_id
    
    def handle_event(self, event, mouse_pos):
        """Handle input events. Returns tuple (action, data) or None
        
        Actions:
        - ("back", None): Go back to selection menu
        - ("buy", skin_id): User wants to buy this skin
        - ("select", skin_id): User selects this skin (already owned)
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check arrow buttons
            if self.left_arrow_rect and self.left_arrow_rect.collidepoint(mouse_pos):
                self.current_index = (self.current_index - 1) % len(self.skin_list)
                return None
            
            if self.right_arrow_rect and self.right_arrow_rect.collidepoint(mouse_pos):
                self.current_index = (self.current_index + 1) % len(self.skin_list)
                return None
            
            # Check action button (BUY or SELECT)
            if self.action_btn_rect and self.action_btn_rect.collidepoint(mouse_pos):
                skin_id = self._get_current_skin_id()
                if skin_id in self.owned_skins:
                    return ("select", skin_id)
                else:
                    # Try to buy
                    skin_info = get_skin_info(skin_id)
                    if self.user_points >= skin_info["cost"]:
                        return ("buy", skin_id)
                    # Not enough points - do nothing
                return None
            
            # Check back button
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                return ("back", None)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return ("back", None)
            elif event.key == pygame.K_LEFT:
                self.current_index = (self.current_index - 1) % len(self.skin_list)
            elif event.key == pygame.K_RIGHT:
                self.current_index = (self.current_index + 1) % len(self.skin_list)
            elif event.key == pygame.K_RETURN:
                skin_id = self._get_current_skin_id()
                if skin_id in self.owned_skins:
                    return ("select", skin_id)
                else:
                    skin_info = get_skin_info(skin_id)
                    if self.user_points >= skin_info["cost"]:
                        return ("buy", skin_id)
        
        return None
    
    def draw(self, surface, screen_width, screen_height, mouse_pos):
        """Draw the character shop screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(240)
        overlay.fill((25, 25, 45))
        surface.blit(overlay, (0, 0))
        
        # Title
        title = self.font_large.render("CHARACTER SHOP", True, (255, 200, 100))
        title_rect = title.get_rect(center=(screen_width // 2, 60))
        surface.blit(title, title_rect)
        
        # Display user points at top right
        points_text = self.font_normal.render(f"Points: {self.user_points}", True, (255, 220, 100))
        surface.blit(points_text, (screen_width - points_text.get_width() - 30, 30))
        
        # Current skin info
        skin_id = self._get_current_skin_id()
        skin_info = get_skin_info(skin_id)
        is_owned = skin_id in self.owned_skins
        is_selected = skin_id == self.selected_skin
        
        # Layout: Left side = preview with arrows, Right side = info and buttons
        left_center_x = screen_width // 3
        right_center_x = screen_width * 2 // 3
        center_y = screen_height // 2 - 30
        
        # === LEFT SIDE: Preview with navigation arrows ===
        
        # Draw preview background/frame
        preview_bg_rect = pygame.Rect(0, 0, 260, 280)
        preview_bg_rect.center = (left_center_x, center_y)
        pygame.draw.rect(surface, (40, 40, 60), preview_bg_rect, border_radius=15)
        pygame.draw.rect(surface, (80, 80, 120), preview_bg_rect, 3, border_radius=15)
        
        # Draw preview image
        if skin_id in self.skin_previews:
            preview = self.skin_previews[skin_id]
            preview_rect = preview.get_rect(center=(left_center_x, center_y - 20))
            surface.blit(preview, preview_rect)
        else:
            placeholder = self.font_large.render("?", True, (100, 100, 100))
            placeholder_rect = placeholder.get_rect(center=(left_center_x, center_y - 20))
            surface.blit(placeholder, placeholder_rect)
        
        # Skin name below preview
        name_text = self.font_normal.render(skin_info["name"], True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(left_center_x, center_y + 100))
        surface.blit(name_text, name_rect)
        
        # Navigation arrows
        arrow_y = center_y
        arrow_size = 50
        
        # Left arrow
        self.left_arrow_rect = pygame.Rect(left_center_x - 180, arrow_y - arrow_size // 2, arrow_size, arrow_size)
        left_hover = self.left_arrow_rect.collidepoint(mouse_pos)
        arrow_color = (150, 150, 200) if left_hover else (100, 100, 150)
        pygame.draw.polygon(surface, arrow_color, [
            (self.left_arrow_rect.right - 10, self.left_arrow_rect.top + 10),
            (self.left_arrow_rect.left + 10, self.left_arrow_rect.centery),
            (self.left_arrow_rect.right - 10, self.left_arrow_rect.bottom - 10)
        ])
        
        # Right arrow
        self.right_arrow_rect = pygame.Rect(left_center_x + 130, arrow_y - arrow_size // 2, arrow_size, arrow_size)
        right_hover = self.right_arrow_rect.collidepoint(mouse_pos)
        arrow_color = (150, 150, 200) if right_hover else (100, 100, 150)
        pygame.draw.polygon(surface, arrow_color, [
            (self.right_arrow_rect.left + 10, self.right_arrow_rect.top + 10),
            (self.right_arrow_rect.right - 10, self.right_arrow_rect.centery),
            (self.right_arrow_rect.left + 10, self.right_arrow_rect.bottom - 10)
        ])
        
        # Skin counter (e.g., "1 / 3")
        counter_text = self.font_small.render(f"{self.current_index + 1} / {len(self.skin_list)}", True, (150, 150, 150))
        counter_rect = counter_text.get_rect(center=(left_center_x, center_y + 140))
        surface.blit(counter_text, counter_rect)
        
        # === RIGHT SIDE: Info and buttons ===
        
        # Status indicator
        if is_selected:
            status_text = self.font_normal.render("EQUIPPED", True, (100, 255, 100))
        elif is_owned:
            status_text = self.font_normal.render("OWNED", True, (100, 200, 100))
        else:
            status_text = self.font_normal.render("NOT OWNED", True, (200, 100, 100))
        status_rect = status_text.get_rect(center=(right_center_x, center_y - 80))
        surface.blit(status_text, status_rect)
        
        # Price display
        if is_owned:
            price_text = self.font_price.render("FREE" if skin_info["cost"] == 0 else "PURCHASED", True, (150, 200, 150))
        else:
            cost = skin_info["cost"]
            can_afford = self.user_points >= cost
            price_color = (255, 220, 100) if can_afford else (200, 100, 100)
            price_text = self.font_price.render(f"{cost} pts", True, price_color)
        price_rect = price_text.get_rect(center=(right_center_x, center_y))
        surface.blit(price_text, price_rect)
        
        # Action button (BUY or SELECT)
        btn_width = 180
        btn_height = 60
        self.action_btn_rect = pygame.Rect(right_center_x - btn_width // 2, center_y + 50, btn_width, btn_height)
        btn_hover = self.action_btn_rect.collidepoint(mouse_pos)
        
        if is_selected:
            # Already equipped - gray button
            btn_color = (60, 60, 60)
            btn_border = (80, 80, 80)
            btn_text = "EQUIPPED"
            text_color = (120, 120, 120)
        elif is_owned:
            # Owned but not selected - can select
            btn_color = (60, 120, 60) if btn_hover else (40, 100, 40)
            btn_border = (100, 200, 100) if btn_hover else (80, 160, 80)
            btn_text = "SELECT"
            text_color = (255, 255, 255)
        else:
            # Not owned - can buy (if enough points)
            can_afford = self.user_points >= skin_info["cost"]
            if can_afford:
                btn_color = (120, 100, 40) if btn_hover else (100, 80, 20)
                btn_border = (255, 220, 100) if btn_hover else (200, 180, 80)
                btn_text = "BUY"
                text_color = (255, 255, 255)
            else:
                btn_color = (60, 40, 40)
                btn_border = (100, 60, 60)
                btn_text = "NOT ENOUGH"
                text_color = (150, 100, 100)
        
        pygame.draw.rect(surface, btn_color, self.action_btn_rect, border_radius=10)
        pygame.draw.rect(surface, btn_border, self.action_btn_rect, 3, border_radius=10)
        
        action_text = self.font_normal.render(btn_text, True, text_color)
        action_text_rect = action_text.get_rect(center=self.action_btn_rect.center)
        surface.blit(action_text, action_text_rect)
        
        # Back button at bottom left
        self.back_rect = pygame.Rect(40, screen_height - 80, 120, 50)
        back_hover = self.back_rect.collidepoint(mouse_pos)
        back_color = (100, 100, 100) if back_hover else (60, 60, 60)
        pygame.draw.rect(surface, back_color, self.back_rect, border_radius=8)
        pygame.draw.rect(surface, (150, 150, 150) if back_hover else (100, 100, 100), self.back_rect, 2, border_radius=8)
        
        back_text = self.font_normal.render("Back", True, (200, 200, 200))
        back_text_rect = back_text.get_rect(center=self.back_rect.center)
        surface.blit(back_text, back_text_rect)
        
        # Instructions at bottom
        hint = self.font_small.render("Use arrow keys or click arrows to browse", True, (100, 100, 120))
        hint_rect = hint.get_rect(center=(screen_width // 2, screen_height - 25))
        surface.blit(hint, hint_rect)
