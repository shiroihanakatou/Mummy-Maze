"""Login and Account Creation Screen - Stone-styled UI"""
import pygame
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "screen"
ASSETS_DIR_ = Path(__file__).parent.parent / "assets"


class StoneButton:
    """Image-based button with stone texture and hover effects"""
    def __init__(self, image, center_pos):
        self.image = image
        self.rect = self.image.get_rect(center=center_pos)
        
    def draw(self, surface, mouse_pos):
        """Draw button with hover effect (brighten on hover)"""
        is_hover = self.rect.collidepoint(mouse_pos)
        display_img = self.image.copy()
        if is_hover:
            display_img.fill((40, 40, 40), special_flags=pygame.BLEND_RGB_ADD)
        surface.blit(display_img, self.rect.topleft)
        return self.rect

    def is_clicked(self, mouse_pos):
        """Check if button was clicked"""
        return self.rect.collidepoint(mouse_pos)


class LoginScreen:
    """Handles login UI and input with Egyptian stone-styled visuals"""
    
    def __init__(self, screen_width, screen_height):
        center_x, center_y = screen_width // 2, screen_height // 2
        
        # Font setup
        self.font_title = pygame.font.SysFont("Impact", 32)
        self.font_label = pygame.font.SysFont("Verdana", 20, bold=True)
        self.font_input = pygame.font.SysFont("Verdana", 18)
        self.font_btn = pygame.font.SysFont("Impact", 24)
        self.font_small = pygame.font.SysFont("Verdana", 16)
        self.font_large = pygame.font.SysFont("Verdana", 36)
        self.font_normal = pygame.font.SysFont("Verdana", 24)

        # --- Load image assets ---
        try:
            self.frame_img = pygame.image.load(ASSETS_DIR / "login_frame.png").convert_alpha()
            self.frame_img = pygame.transform.smoothscale(self.frame_img, (640, 720))
        except:
            self.frame_img = pygame.Surface((640, 720))
            self.frame_img.fill((160, 120, 70))
        
        self.frame_rect = self.frame_img.get_rect(center=(center_x, center_y))

        # Login button
        try:
            self.btn_login_img = pygame.image.load(ASSETS_DIR / "btn_login.png").convert_alpha()
            self.btn_login_img = pygame.transform.smoothscale(self.btn_login_img, (225, 72))
        except:
            self.btn_login_img = pygame.Surface((225, 72))
            self.btn_login_img.fill((100, 150, 100))
        self.login_button = StoneButton(self.btn_login_img, (center_x - 110, center_y + 72))

        # Register button
        try:
            self.btn_register_img = pygame.image.load(ASSETS_DIR / "btn_register.png").convert_alpha()
            self.btn_register_img = pygame.transform.smoothscale(self.btn_register_img, (225, 72))
        except:
            self.btn_register_img = pygame.Surface((225, 72))
            self.btn_register_img.fill((100, 100, 150))
        self.register_button = StoneButton(self.btn_register_img, (center_x + 110, center_y + 72))

        # Guest button
        try:
            self.btn_guest_img = pygame.image.load(ASSETS_DIR / "btn_guest.png").convert_alpha()
            self.btn_guest_img = pygame.transform.smoothscale(self.btn_guest_img, (180, 72))
        except:
            self.btn_guest_img = pygame.Surface((180, 72))
            self.btn_guest_img.fill((100, 100, 100))
        self.guest_button = StoneButton(self.btn_guest_img, (center_x - 105, center_y + 171))

        # Exit button (replaces Load Guest)
        try:
            self.btn_exit_img = pygame.image.load(ASSETS_DIR / "btn_exit.png").convert_alpha()
            self.btn_exit_img = pygame.transform.smoothscale(self.btn_exit_img, (180, 72))
        except:
            self.btn_exit_img = pygame.Surface((180, 72))
            self.btn_exit_img.fill((120, 60, 60))
        self.exit_button = StoneButton(self.btn_exit_img, (center_x + 105, center_y + 171))

        # Input data
        self.username_input = ""
        self.password_input = ""
        self.active_input = None  # "username", "password", or None
        self.error_message = ""
        self.show_password = False
        self.input_boxes = {}
        self.button_width = 200
        self.button_height = 50

    def handle_event(self, event):
        """Handle input events for login screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and self.active_input:
                self.active_input = "password" if self.active_input == "username" else "username"
            elif event.key == pygame.K_BACKSPACE:
                if self.active_input == "username":
                    self.username_input = self.username_input[:-1]
                elif self.active_input == "password":
                    self.password_input = self.password_input[:-1]
                self.error_message = ""
            elif event.key == pygame.K_RETURN and self.active_input:
                return "login"
            elif event.unicode.isprintable() and self.active_input:
                max_len = 20
                if self.active_input == "username":
                    if len(self.username_input) < max_len:
                        self.username_input += event.unicode
                elif self.active_input == "password":
                    if len(self.password_input) < max_len:
                        self.password_input += event.unicode
                self.error_message = ""
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check input box clicks
            if "username_box" in self.input_boxes:
                if self.input_boxes["username_box"].collidepoint(event.pos):
                    self.active_input = "username"
                    return None
            if "password_box" in self.input_boxes:
                if self.input_boxes["password_box"].collidepoint(event.pos):
                    self.active_input = "password"
                    return None
            
            # Check clicks outside input boxes
            if "username_box" in self.input_boxes and not self.input_boxes["username_box"].collidepoint(event.pos):
                if "password_box" in self.input_boxes and not self.input_boxes["password_box"].collidepoint(event.pos):
                    self.active_input = None
                    
            # Check button clicks
            if self.login_button.is_clicked(event.pos): return "login"
            if self.register_button.is_clicked(event.pos): return "register"
            if self.guest_button.is_clicked(event.pos): return "guest"
            if self.exit_button.is_clicked(event.pos): return "exit"
        return None

    def draw(self, surface, screen_width, screen_height, mouse_pos):
        """Draw login screen UI with stone tablet style"""
        # 1. Dark overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # 2. Draw stone frame
        surface.blit(self.frame_img, self.frame_rect)
        center_x, center_y = self.frame_rect.centerx, self.frame_rect.centery
        
        # 3. Draw input boxes (aligned to frame center)
        # Username box
        self.input_boxes["username_box"] = pygame.Rect(0, 0, 432, 48)
        self.input_boxes["username_box"].center = (center_x - 3, center_y - 104)
        if self.active_input == "username":
            pygame.draw.rect(surface, (255, 215, 0), self.input_boxes["username_box"], 2, border_radius=5)

        # Password box
        self.input_boxes["password_box"] = pygame.Rect(0, 0, 432, 48)
        self.input_boxes["password_box"].center = (center_x - 3, center_y - 13)
        if self.active_input == "password":
            pygame.draw.rect(surface, (255, 215, 0), self.input_boxes["password_box"], 2, border_radius=5)

        # Draw input text
        username_text = self.font_normal.render(self.username_input, True, (255, 215, 0))
        surface.blit(username_text, (self.input_boxes["username_box"].left + 15, self.input_boxes["username_box"].top + 5))
        
        pwd_display = "*" * len(self.password_input)
        password_text = self.font_normal.render(pwd_display, True, (250, 215, 0))
        surface.blit(password_text, (self.input_boxes["password_box"].left + 15, self.input_boxes["password_box"].top + 10))

        # 4. Draw buttons using images
        login_btn = self.login_button.draw(surface, mouse_pos)
        create_btn = self.register_button.draw(surface, mouse_pos)
        guest_btn = self.guest_button.draw(surface, mouse_pos)
        exit_btn = self.exit_button.draw(surface, mouse_pos)
        
        # 5. Draw error message
        if self.error_message:
            error_text = self.font_small.render(self.error_message, True, (255, 50, 50))
            surface.blit(error_text, (center_x - 220, center_y + 14))

        return {
            "login_btn": login_btn,
            "create_btn": create_btn,
            "guest_btn": guest_btn,
            "exit_btn": exit_btn,
        }
    
    def reset(self):
        """Reset login form"""
        self.username_input = ""
        self.password_input = ""
        self.active_input = None
        self.error_message = ""
        self.show_password = False
        self.input_boxes = {}
    
    def _calculate_button_rects(self, screen_width, screen_height):
        """Calculate button rects without drawing - for event handling"""
        center_x = screen_width // 2
        center_y = screen_height // 2
        button_y = center_y + 170
        
        login_btn = pygame.Rect(center_x - 160, button_y, 140, 50)
        create_btn = pygame.Rect(center_x + 20, button_y, 140, 50)
        guest_btn = pygame.Rect(center_x - 210, button_y + 70, 180, 50)
        load_guest_btn = pygame.Rect(center_x + 30, button_y + 70, 180, 50)
        
        return {
            "login_btn": login_btn,
            "create_btn": create_btn,
            "guest_btn": guest_btn,
            "load_guest_btn": load_guest_btn,
        }
    
    def set_error(self, message):
        """Set error message"""
        self.error_message = message
    
    def get_credentials(self):
        """Get current username and password"""
        return self.username_input, self.password_input


class RegisterScreen:
    """Registration screen with Egyptian stone tablet style"""
    
    def __init__(self, sw, sh):
        cx, cy = sw // 2, sh // 2
        
        # Input data
        self.username_input = ""
        self.password_input = "" 
        self.confirm_password_input = ""
        self.active_input = None
        self.error_message = ""
        
        # Fonts
        self.font_title = pygame.font.SysFont("Georgia", 32, bold=True)
        self.font_label = pygame.font.SysFont("Verdana", 20, bold=True)
        self.font_text = pygame.font.SysFont("Verdana", 18)
        self.font_hint = pygame.font.SysFont("Verdana", 14, italic=True)

        # Load assets
        try:
            self.bg_img = pygame.image.load(ASSETS_DIR / "register_frame.png").convert_alpha()
            self.bg_img = pygame.transform.smoothscale(self.bg_img, (600, 600))
            
            img_reg = pygame.image.load(ASSETS_DIR / "btn_register.png").convert_alpha()
            self.reg_btn_img = pygame.transform.smoothscale(img_reg, (153, 63))
            
            img_back = pygame.image.load(ASSETS_DIR / "btn_back.png").convert_alpha()
            self.back_btn_img = pygame.transform.smoothscale(img_back, (153, 63))
        except:
            self.bg_img = pygame.Surface((600, 600))
            self.bg_img.fill((160, 120, 70))
            self.reg_btn_img = pygame.Surface((160, 50))
            self.reg_btn_img.fill((100, 150, 100))
            self.back_btn_img = pygame.Surface((160, 50))
            self.back_btn_img.fill((100, 100, 100))

        self.bg_rect = self.bg_img.get_rect(center=(cx, cy))

        # Input box positions (aligned to stone tablet hollows)
        self.input_boxes = {
            "username_box": pygame.Rect(cx - 210, cy - 103, 414, 36),
            "password_box": pygame.Rect(cx - 210, cy - 29, 414, 36),
            "confirm_password_box": pygame.Rect(cx - 210, cy + 46, 414, 36)
        }

        # Stone buttons
        self.register_button = StoneButton(self.reg_btn_img, (cx - 100, cy + 140))
        self.back_button = StoneButton(self.back_btn_img, (cx + 100, cy + 140))
        
    def handle_event(self, event, button_rects=None):
        """Handle input events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                order = ["username", "password", "confirm_password"]
                idx = order.index(self.active_input) if self.active_input in order else -1
                self.active_input = order[(idx + 1) % len(order)]
            
            elif event.key == pygame.K_BACKSPACE and self.active_input:
                attr = f"{self.active_input}_input"
                setattr(self, attr, getattr(self, attr)[:-1])
                self.error_message = ""

            elif event.key == pygame.K_RETURN:
                return "register"

            elif event.unicode.isprintable() and self.active_input:
                attr = f"{self.active_input}_input"
                if len(getattr(self, attr)) < 20:
                    setattr(self, attr, getattr(self, attr) + event.unicode)
                self.error_message = ""

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.register_button.is_clicked(event.pos): return "register"
            if self.back_button.is_clicked(event.pos): return "back"

            for name, rect in self.input_boxes.items():
                if rect.collidepoint(event.pos):
                    self.active_input = name.replace("_box", "")
                    return None
            self.active_input = None
            
        return None

    def draw(self, surface, sw, sh, mouse_pos):
        """Draw registration screen with stone tablet style"""
        cx, cy = self.bg_rect.centerx, self.bg_rect.centery
        
        # 1. Dark overlay and stone background
        overlay = pygame.Surface((sw, sh))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        surface.blit(self.bg_img, self.bg_rect)

        # 2. Draw input text in hollows
        field_keys = ["username", "password", "confirm_password"]

        for key in field_keys:
            rect = self.input_boxes[f"{key}_box"]
            
            if self.active_input == key:
                pygame.draw.rect(surface, (255, 215, 0), rect, 2, border_radius=5)
            
            val = getattr(self, f"{key}_input")
            display_val = val if key == "username" else "*" * len(val)
            
            txt_s = self.font_text.render(display_val, True, (255, 215, 0))
            surface.blit(txt_s, (rect.x + 15, rect.y + 5))

        # 3. Error message
        if self.error_message:
            err_s = self.font_hint.render(self.error_message, True, (255, 50, 50))
            surface.blit(err_s, (cx - 210, cy + 84))

        # 4. Draw stone buttons
        reg_rect = self.register_button.draw(surface, mouse_pos)
        back_rect = self.back_button.draw(surface, mouse_pos)

        return {"register_btn": reg_rect, "back_btn": back_rect}
    
    def set_error(self, message):
        """Set error message"""
        self.error_message = message
    
    def reset(self):
        """Reset form"""
        self.username_input = ""
        self.password_input = ""
        self.confirm_password_input = ""
        self.active_input = None
        self.error_message = ""
        
    def get_credentials(self):
        """Return input values"""
        return self.username_input, self.password_input, self.confirm_password_input


class LeaderboardScreen:
    """Leaderboard with ancient stone tablet style"""
    
    def __init__(self, sw, sh):
        self.leaderboard_data = []
        self.scroll_offset = 0
        
        # Try to load custom fonts, fallback to system fonts
        try:
            self.font_large = pygame.font.Font(str(ASSETS_DIR_ / "font" / "romeo.ttf"), 54)
            self.font_normal = pygame.font.Font(str(ASSETS_DIR_ / "font" / "romeo.ttf"), 36)
            self.font_small = pygame.font.Font(str(ASSETS_DIR_ / "font" / "romeo.ttf"), 25)
        except:
            self.font_large = pygame.font.SysFont("Georgia", 48, bold=True)
            self.font_normal = pygame.font.SysFont("Georgia", 32)
            self.font_small = pygame.font.SysFont("Georgia", 22)
        
        # Load assets (use ladder_frame.png for leaderboard background)
        try:
            raw_frame = pygame.image.load(ASSETS_DIR / "ladder_frame.png").convert_alpha()
            self.frame_img = pygame.transform.smoothscale(raw_frame, (600, 650))
        except:
            self.frame_img = pygame.Surface((600, 650))
            self.frame_img.fill((120, 100, 60))  # Unique color for leaderboard
        try:
            raw_btn = pygame.image.load(ASSETS_DIR / "btn_back.png").convert_alpha()
            self.btn_img = pygame.transform.smoothscale(raw_btn, (160, 50))
        except:
            self.btn_img = pygame.Surface((160, 50))
            self.btn_img.fill((100, 100, 100))

        self.frame_rect = self.frame_img.get_rect(center=(sw // 2, sh // 2))
        self.back_button = StoneButton(self.btn_img, (sw // 2, self.frame_rect.bottom - 75))

    def set_leaderboard(self, data):
        """Set leaderboard data"""
        self.leaderboard_data = data
        self.scroll_offset = 0
    
    def handle_event(self, event, button_rects=None):
        """Handle scroll and back events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.key == pygame.K_DOWN:
                self.scroll_offset = min(max(0, len(self.leaderboard_data) - 10), self.scroll_offset + 1)
            elif event.key == pygame.K_ESCAPE:
                return "back"
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                return "back"
        return None
    
    def draw(self, surface, screen_width, screen_height, mouse_pos):
        """Draw leaderboard with sandstone style"""
        center_x = screen_width // 2
        
        # 1. Dark overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # 2. Stone frame background
        surface.blit(self.frame_img, self.frame_rect)
        
        # 3. Title (Egyptian brown)
        title = self.font_large.render("LEADERBOARD", True, (40, 25, 10))
        surface.blit(title, title.get_rect(center=(center_x, self.frame_rect.top + 70)))
        
        # 4. Header (Earthy yellow)
        header_y = self.frame_rect.top + 130
        rank_h = self.font_normal.render("Rank", True, (100, 70, 40))
        name_h = self.font_normal.render("Username", True, (100, 70, 40))
        score_h = self.font_normal.render("Score", True, (100, 70, 40))
        
        surface.blit(rank_h, (center_x - 220, header_y))
        surface.blit(name_h, (center_x - 80, header_y))
        surface.blit(score_h, (center_x + 120, header_y))
        
        # 5. Leaderboard entries with scroll
        max_display = 10
        display_data = self.leaderboard_data[self.scroll_offset : self.scroll_offset + max_display]
        
        for i, entry in enumerate(display_data):
            entry_y = header_y + 45 + (i * 35)
            actual_rank = i + self.scroll_offset + 1
            
            # Gold for #1, brown for others
            color = (180, 140, 0) if actual_rank == 1 else (60, 45, 30)
            
            username = entry.get("username", "Unknown")
            score = entry.get("score", 0)
            
            rank_str = self.font_normal.render(f"#{actual_rank}", True, color)
            name_str = self.font_normal.render(username[:15], True, color)
            score_str = self.font_normal.render(f"{score:,}", True, color)
            
            surface.blit(rank_str, (center_x - 220, entry_y))
            surface.blit(name_str, (center_x - 80, entry_y))
            surface.blit(score_str, (center_x + 120, entry_y))
        
        # 6. Hint and Back button
        hint = self.font_small.render("Press ESC to go back | UP/DOWN to scroll", True, (80, 60, 40))
        surface.blit(hint, (center_x - 180, self.frame_rect.bottom - 36))
        
        # Draw back button as text only (no background)
        back_text = self.font_normal.render("Back", True, (255, 215, 0))
        back_rect = back_text.get_rect(center=(screen_width // 2, self.frame_rect.bottom - 50))
        surface.blit(back_text, back_rect)
        return {"back_btn": back_rect}


class GuestLoadScreen:
    """Guest profile selection with stone tablet UI"""
    
    def __init__(self):
        # Fonts and colors
        try:
            self.font_title = pygame.font.Font(str(ASSETS_DIR_ / "font" / "romeo.ttf"), 45)
            self.font_button = pygame.font.Font(str(ASSETS_DIR_ / "font" / "romeo.ttf"), 27)
        except:
            self.font_title = pygame.font.SysFont("Georgia", 40, bold=True)
            self.font_button = pygame.font.SysFont("Georgia", 24)
            
        self.colors = {
            "overlay": (20, 15, 10),
            "text_title": (40, 25, 10),
            "text_light": (250, 245, 230),
            "text_gold": (255, 215, 50),
            "stone_face": (180, 140, 90),
            "stone_dark": (100, 70, 40),
            "stone_highlight": (210, 170, 110),
            "panel_bg": (160, 120, 70),
            "text_input": (255, 248, 220),
            "text_active": (255, 215, 0),
            "text_error": (190, 30, 30),
            "input_bg": (40, 30, 20),
            "border_active": (218, 165, 32)
        }

        self.profiles = []
        self.profile_rects = {}
    
    def set_profiles(self, profiles):
        """Set the list of available guest profiles"""
        self.profiles = profiles
        self.profile_rects = {}
    
    def handle_event(self, event):
        """Handle input events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
        return None

    def _draw_stone_button(self, surface, rect, text, text_color, is_hovered):
        """Draw 3D stone button"""
        face_color = self.colors["stone_highlight"] if is_hovered else self.colors["stone_face"]
        dark_color = self.colors["stone_dark"]
        
        # Shadow layer
        pygame.draw.rect(surface, dark_color, rect, border_radius=5)
        
        # Face layer
        inner_rect = rect.inflate(-4, -4) 
        pygame.draw.rect(surface, face_color, inner_rect, border_radius=5)
        
        # Highlight edges
        pygame.draw.line(surface, self.colors["stone_highlight"], (inner_rect.left, inner_rect.top), (inner_rect.right, inner_rect.top), 2)
        pygame.draw.line(surface, self.colors["stone_highlight"], (inner_rect.left, inner_rect.top), (inner_rect.left, inner_rect.bottom), 2)

        # Text with shadow
        text_surf = self.font_button.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        shadow_surf = self.font_button.render(text, True, self.colors["stone_dark"])
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)

    def draw(self, surface, screen_width, screen_height, mouse_pos=None):
        """Draw guest profile selection with stone tablet UI"""
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        # 1. Dark overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(220)
        overlay.fill(self.colors["overlay"])
        surface.blit(overlay, (0, 0))
        
        # 2. Stone panel
        panel_width = 500
        panel_height = 550
        panel_rect = pygame.Rect(center_x - panel_width // 2, center_y - panel_height // 2, panel_width, panel_height)
        
        pygame.draw.rect(surface, self.colors["stone_dark"], panel_rect, border_radius=12)
        inner_panel = panel_rect.inflate(-16, -16)
        pygame.draw.rect(surface, self.colors["panel_bg"], inner_panel, border_radius=8)
        pygame.draw.rect(surface, self.colors["stone_dark"], inner_panel, 4, border_radius=8)

        # 3. Title
        title_text = "Select Guest Profile"
        title = self.font_title.render(title_text, True, self.colors["text_title"])
        title_rect = title.get_rect(center=(center_x, panel_rect.top + 60))
        surface.blit(title, title_rect)
        
        # 4. Profile buttons
        button_width = 400
        button_height = 55
        spacing = 15
        start_y = panel_rect.top + 120
        self.profile_rects = {}
        
        for idx, name in enumerate(self.profiles):
            rect = pygame.Rect(center_x - button_width // 2, start_y + idx * (button_height + spacing), button_width, button_height)
            self.profile_rects[name] = rect
            
            is_hover = mouse_pos and rect.collidepoint(mouse_pos)
            self._draw_stone_button(surface, rect, name, self.colors["text_light"], is_hover)
        
        # Fill remaining slots with "NEW GAME"
        current_y = start_y + len(self.profiles) * (button_height + spacing)
        slots_to_fill = 5 - len(self.profiles)
        for i in range(slots_to_fill):
            rect = pygame.Rect(center_x - button_width // 2, current_y, button_width, button_height)
            key_name = f"_new_profile_{i}" 
            self.profile_rects[key_name] = rect
            
            is_hover = mouse_pos and rect.collidepoint(mouse_pos)
            self._draw_stone_button(surface, rect, "NEW GAME", self.colors["text_light"], is_hover)
            current_y += button_height + spacing

        # Back/Cancel button
        back_rect = pygame.Rect(center_x - button_width // 2, panel_rect.bottom - 80, button_width, button_height)
        self.profile_rects["_back"] = back_rect
        
        is_hover = mouse_pos and back_rect.collidepoint(mouse_pos)
        self._draw_stone_button(surface, back_rect, "Cancel", self.colors["text_gold"], is_hover)
        
        return self.profile_rects
    
    def get_clicked_profile(self, mouse_pos):
        """Return the profile name if clicked, or special action"""
        for key, rect in self.profile_rects.items():
            if rect.collidepoint(mouse_pos):
                return key
        return None


class SaveDialog:
    """Save confirmation dialog with Egyptian stone style"""
    
    def __init__(self, sw, sh):
        # Fonts
        try:
            self.font_title = pygame.font.Font(str(ASSETS_DIR_ / "font" / "romeo.ttf"), 63)
            self.font_msg = pygame.font.Font(str(ASSETS_DIR_ / "font" / "romeo.ttf"), 45)
            self.font_btn = pygame.font.Font(str(ASSETS_DIR_ / "font" / "romeo.ttf"), 30)
        except:
            self.font_title = pygame.font.SysFont("Georgia", 54, bold=True)
            self.font_msg = pygame.font.SysFont("Georgia", 38)
            self.font_btn = pygame.font.SysFont("Georgia", 26)
            
        self.colors = {
            "panel_bg": (180, 140, 90),
            "panel_border": (100, 70, 40),
            "text_gold": (255, 215, 0),
            "text_ivory": (250, 245, 230),
            "btn_yes": (60, 120, 60),
            "btn_no": (140, 60, 60),
            "btn_stone": (120, 100, 80),
            "btn_shadow": (60, 40, 20)
        }

        self.dialog_type = "save_before_exit"
        self.phase = "confirm"
        self.message = ""
        self.profiles = []
        self.selected_profile = None
        
    def set_state(self, dialog_type, message, profiles=None):
        """Configure the dialog"""
        self.dialog_type = dialog_type
        self.message = message
        self.phase = "confirm"
        self.profiles = profiles or []
        self.selected_profile = self.profiles[0] if self.profiles else None

    def _draw_stone_button(self, surface, rect, color, text, is_hover):
        """Draw 3D stone button"""
        main_color = [min(255, c + 30) for c in color] if is_hover else color
        shadow_color = self.colors["btn_shadow"]
        
        # Shadow
        pygame.draw.rect(surface, shadow_color, rect.move(0, 4), border_radius=5)
        # Face
        pygame.draw.rect(surface, main_color, rect, border_radius=5)
        # Border
        pygame.draw.rect(surface, self.colors["text_gold"] if is_hover else shadow_color, rect, 2, border_radius=5)
        
        # Text with shadow
        txt_shadow = self.font_btn.render(text, True, (20, 10, 5))
        txt_s = self.font_btn.render(text, True, self.colors["text_ivory"])
        t_rect = txt_s.get_rect(center=rect.center)
        surface.blit(txt_shadow, (t_rect.x + 1, t_rect.y + 1))
        surface.blit(txt_s, t_rect)

    def draw(self, surface, screen_width, screen_height, mouse_pos=None):
        """Draw dialog and return button rects"""
        # 1. Dark overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # 2. Dialog panel
        dw = 500
        dh = 400 if self.phase == "confirm" else 450
        dx = (screen_width - dw) // 2
        dy = (screen_height - dh) // 2
        panel_rect = pygame.Rect(dx, dy, dw, dh)
        
        pygame.draw.rect(surface, self.colors["panel_bg"], panel_rect, border_radius=10)
        pygame.draw.rect(surface, self.colors["panel_border"], panel_rect, 5, border_radius=10)
        pygame.draw.rect(surface, self.colors["panel_border"], panel_rect.inflate(-15, -15), 2, border_radius=8)

        button_rects = {}
        cx = screen_width // 2
        y_offset = dy + 50
        
        if self.phase == "confirm":
            # Title (Gold)
            title_str = "Save?" if self.dialog_type == "save_before_exit" else "Quit?"
            title_s = self.font_title.render(title_str, True, self.colors["text_gold"])
            surface.blit(title_s, title_s.get_rect(center=(cx, y_offset)))
            
            # Message (Ivory)
            y_offset += 70
            msg_s = self.font_msg.render(self.message, True, self.colors["text_ivory"])
            surface.blit(msg_s, msg_s.get_rect(center=(cx, y_offset)))
            
            # YES/NO buttons
            y_offset += 100
            bw, bh = 140, 55
            yes_r = pygame.Rect(cx - 160, y_offset, bw, bh)
            no_r = pygame.Rect(cx + 20, y_offset, bw, bh)
            
            self._draw_stone_button(surface, yes_r, self.colors["btn_yes"], "YES", mouse_pos and yes_r.collidepoint(mouse_pos))
            self._draw_stone_button(surface, no_r, self.colors["btn_no"], "NO", mouse_pos and no_r.collidepoint(mouse_pos))
            
            button_rects["yes"] = yes_r
            button_rects["no"] = no_r
            
        elif self.phase == "select_profile":
            # Title
            title_s = self.font_title.render("SELECT PROFILE", True, self.colors["text_gold"])
            surface.blit(title_s, title_s.get_rect(center=(cx, y_offset)))
            
            y_offset += 60
            bw, bh = 350, 50
            for profile in self.profiles:
                p_rect = pygame.Rect(cx - bw // 2, y_offset, bw, bh)
                is_h = mouse_pos and p_rect.collidepoint(mouse_pos)
                self._draw_stone_button(surface, p_rect, self.colors["btn_stone"], profile, is_h)
                button_rects[profile] = p_rect
                y_offset += bh + 15
            
            # Back button
            y_offset += 10
            back_r = pygame.Rect(cx - bw // 2, y_offset, bw, bh)
            self._draw_stone_button(surface, back_r, (80, 80, 80), "BACK", mouse_pos and back_r.collidepoint(mouse_pos))
            button_rects["back"] = back_r
        
        return button_rects

    def handle_event(self, event):
        """Handle ESC key"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "cancel"
        return None

    def _calculate_button_rects(self, screen_width, screen_height):
        """Calculate button rects without drawing - for event handling"""
        dw = 500
        dh = 400 if self.phase == "confirm" else 450
        dx = (screen_width - dw) // 2
        dy = (screen_height - dh) // 2
        
        button_rects = {}
        cx = screen_width // 2
        y_offset = dy + 50
        
        if self.phase == "confirm":
            y_offset += 70  # Title space
            y_offset += 100  # Message space + button offset
            bw, bh = 140, 55
            yes_r = pygame.Rect(cx - 160, y_offset, bw, bh)
            no_r = pygame.Rect(cx + 20, y_offset, bw, bh)
            button_rects["yes"] = yes_r
            button_rects["no"] = no_r
            
        elif self.phase == "select_profile":
            y_offset += 60
            bw, bh = 350, 50
            for profile in self.profiles:
                p_rect = pygame.Rect(cx - bw // 2, y_offset, bw, bh)
                button_rects[profile] = p_rect
                y_offset += bh + 15
            
            y_offset += 10
            back_r = pygame.Rect(cx - bw // 2, y_offset, bw, bh)
            button_rects["back"] = back_r
        
        return button_rects

    def get_clicked(self, mouse_pos, button_rects):
        """Check which button was clicked"""
        for name, rect in button_rects.items():
            if rect.collidepoint(mouse_pos):
                return name
        return None
