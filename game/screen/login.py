"""Login and Account Creation Screen"""
import pygame
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"

class LoginScreen:
    """Handles login UI and input"""
    
    def __init__(self):
        self.username_input = ""
        self.password_input = ""
        self.active_input = None  # "username", "password", or None
        self.error_message = ""
        self.show_password = False
        
        # Input box dimensions
        self.input_boxes = {}
        self.button_width = 200
        self.button_height = 50
        
        # Font
        self.font_large = pygame.font.SysFont("Verdana", 36)
        self.font_normal = pygame.font.SysFont("Verdana", 24)
        self.font_small = pygame.font.SysFont("Verdana", 18)
        
    def handle_event(self, event):
        """Handle input events for login screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and self.active_input:
                # Switch between input fields
                self.active_input = "password" if self.active_input == "username" else "username"
            elif event.key == pygame.K_BACKSPACE:
                if self.active_input == "username":
                    self.username_input = self.username_input[:-1]
                elif self.active_input == "password":
                    self.password_input = self.password_input[:-1]
                self.error_message = ""
            elif event.key == pygame.K_RETURN and self.active_input:
                return "login"  # Signal to attempt login
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
            # Check which input box was clicked
            if "username_box" in self.input_boxes:
                if self.input_boxes["username_box"].collidepoint(event.pos):
                    self.active_input = "username"
                    return None
            if "password_box" in self.input_boxes:
                if self.input_boxes["password_box"].collidepoint(event.pos):
                    self.active_input = "password"
                    return None
            
            # Check if clicked outside input boxes
            if "username_box" in self.input_boxes and not self.input_boxes["username_box"].collidepoint(event.pos):
                if "password_box" in self.input_boxes and not self.input_boxes["password_box"].collidepoint(event.pos):
                    self.active_input = None
        
        return None
    
    def draw(self, surface, screen_width, screen_height):
        """Draw login screen UI"""
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(230)
        overlay.fill((20, 20, 40))
        surface.blit(overlay, (0, 0))
        
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        # Title
        title = self.font_large.render("Login", True, (255, 200, 100))
        title_rect = title.get_rect(center=(center_x, center_y - 150))
        surface.blit(title, title_rect)
        
        # Username label
        user_label = self.font_normal.render("Username:", True, (200, 200, 200))
        surface.blit(user_label, (center_x - 150, center_y - 60))
        
        # Username input box
        username_rect = pygame.Rect(center_x - 150, center_y - 30, 300, 40)
        self.input_boxes["username_box"] = username_rect
        box_color = (255, 200, 100) if self.active_input == "username" else (100, 100, 120)
        pygame.draw.rect(surface, box_color, username_rect, 3)
        
        username_text = self.font_normal.render(self.username_input, True, (255, 255, 255))
        surface.blit(username_text, (username_rect.x + 10, username_rect.y + 5))
        
        # Password label
        pwd_label = self.font_normal.render("Password:", True, (200, 200, 200))
        surface.blit(pwd_label, (center_x - 150, center_y + 30))
        
        # Password input box
        password_rect = pygame.Rect(center_x - 150, center_y + 60, 300, 40)
        self.input_boxes["password_box"] = password_rect
        box_color = (255, 200, 100) if self.active_input == "password" else (100, 100, 120)
        pygame.draw.rect(surface, box_color, password_rect, 3)
        
        pwd_display = "*" * len(self.password_input)
        password_text = self.font_normal.render(pwd_display, True, (255, 255, 255))
        surface.blit(password_text, (password_rect.x + 10, password_rect.y + 5))
        
        # Error message
        if self.error_message:
            error_text = self.font_small.render(self.error_message, True, (255, 100, 100))
            surface.blit(error_text, (center_x - 150, center_y + 120))
        
        # Buttons
        button_y = center_y + 170
        
        # Login button
        login_btn = pygame.Rect(center_x - 160, button_y, 140, 50)
        pygame.draw.rect(surface, (100, 150, 100), login_btn)
        pygame.draw.rect(surface, (150, 200, 150), login_btn, 2)
        login_text = self.font_normal.render("Login", True, (255, 255, 255))
        login_rect = login_text.get_rect(center=login_btn.center)
        surface.blit(login_text, login_rect)
        
        # Create Account button
        create_btn = pygame.Rect(center_x + 20, button_y, 140, 50)
        pygame.draw.rect(surface, (100, 100, 150), create_btn)
        pygame.draw.rect(surface, (150, 150, 200), create_btn, 2)
        create_text = self.font_normal.render("Register", True, (255, 255, 255))
        create_rect = create_text.get_rect(center=create_btn.center)
        surface.blit(create_text, create_rect)
        
        # Play as Guest button
        guest_btn = pygame.Rect(center_x - 210, button_y + 70, 180, 50)
        pygame.draw.rect(surface, (100, 100, 100), guest_btn)
        pygame.draw.rect(surface, (150, 150, 150), guest_btn, 2)
        guest_text = self.font_small.render("Play as Guest", True, (255, 255, 255))
        guest_rect = guest_text.get_rect(center=guest_btn.center)
        surface.blit(guest_text, guest_rect)

        # Load Local Save (guest only)
        load_guest_btn = pygame.Rect(center_x + 30, button_y + 70, 180, 50)
        pygame.draw.rect(surface, (80, 120, 180), load_guest_btn)
        pygame.draw.rect(surface, (130, 170, 220), load_guest_btn, 2)
        load_text = self.font_small.render("Load Local Save", True, (255, 255, 255))
        load_rect = load_text.get_rect(center=load_guest_btn.center)
        surface.blit(load_text, load_rect)
        
        # Hint
        hint = self.font_small.render("Click input boxes to type, TAB to switch, ENTER to login", True, (150, 150, 150))
        surface.blit(hint, (center_x - 220, button_y + 140))
        
        return {
            "login_btn": login_btn,
            "create_btn": create_btn,
            "guest_btn": guest_btn,
            "load_guest_btn": load_guest_btn,
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
    """Handles account registration UI and input"""
    
    def __init__(self):
        self.username_input = ""
        self.password_input = ""
        self.confirm_password_input = ""
        self.active_input = None  # "username", "password", or "confirm"
        self.error_message = ""
        
        # Input box dimensions
        self.input_boxes = {}
        self.button_width = 200
        self.button_height = 50
        
        # Font
        self.font_large = pygame.font.SysFont("Verdana", 36)
        self.font_normal = pygame.font.SysFont("Verdana", 24)
        self.font_small = pygame.font.SysFont("Verdana", 18)
        
    def handle_event(self, event):
        """Handle input events for register screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and self.active_input:
                # Switch between input fields
                if self.active_input == "username":
                    self.active_input = "password"
                elif self.active_input == "password":
                    self.active_input = "confirm"
                else:
                    self.active_input = "username"
            elif event.key == pygame.K_BACKSPACE:
                if self.active_input == "username":
                    self.username_input = self.username_input[:-1]
                elif self.active_input == "password":
                    self.password_input = self.password_input[:-1]
                elif self.active_input == "confirm":
                    self.confirm_password_input = self.confirm_password_input[:-1]
                self.error_message = ""
            elif event.key == pygame.K_RETURN and self.active_input:
                return "register"  # Signal to attempt registration
            elif event.unicode.isprintable() and self.active_input:
                max_len = 20
                if self.active_input == "username":
                    if len(self.username_input) < max_len:
                        self.username_input += event.unicode
                elif self.active_input == "password":
                    if len(self.password_input) < max_len:
                        self.password_input += event.unicode
                elif self.active_input == "confirm":
                    if len(self.confirm_password_input) < max_len:
                        self.confirm_password_input += event.unicode
                self.error_message = ""
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check which input box was clicked
            for box_name in ["username_box", "password_box", "confirm_box"]:
                if box_name in self.input_boxes:
                    if self.input_boxes[box_name].collidepoint(event.pos):
                        self.active_input = box_name.replace("_box", "")
                        return None
        
        return None
    
    def draw(self, surface, screen_width, screen_height):
        """Draw register screen UI"""
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(230)
        overlay.fill((20, 20, 40))
        surface.blit(overlay, (0, 0))
        
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        # Title
        title = self.font_large.render("Create Account", True, (255, 200, 100))
        title_rect = title.get_rect(center=(center_x, center_y - 180))
        surface.blit(title, title_rect)
        
        # Username label
        user_label = self.font_normal.render("Username:", True, (200, 200, 200))
        surface.blit(user_label, (center_x - 150, center_y - 90))
        
        # Username input box
        username_rect = pygame.Rect(center_x - 150, center_y - 60, 300, 40)
        self.input_boxes["username_box"] = username_rect
        box_color = (255, 200, 100) if self.active_input == "username" else (100, 100, 120)
        pygame.draw.rect(surface, box_color, username_rect, 3)
        username_text = self.font_normal.render(self.username_input, True, (255, 255, 255))
        surface.blit(username_text, (username_rect.x + 10, username_rect.y + 5))
        
        # Password label
        pwd_label = self.font_normal.render("Password:", True, (200, 200, 200))
        surface.blit(pwd_label, (center_x - 150, center_y))
        
        # Password input box
        password_rect = pygame.Rect(center_x - 150, center_y + 30, 300, 40)
        self.input_boxes["password_box"] = password_rect
        box_color = (255, 200, 100) if self.active_input == "password" else (100, 100, 120)
        pygame.draw.rect(surface, box_color, password_rect, 3)
        pwd_display = "*" * len(self.password_input)
        password_text = self.font_normal.render(pwd_display, True, (255, 255, 255))
        surface.blit(password_text, (password_rect.x + 10, password_rect.y + 5))
        
        # Confirm password label
        confirm_label = self.font_normal.render("Confirm Password:", True, (200, 200, 200))
        surface.blit(confirm_label, (center_x - 150, center_y + 90))
        
        # Confirm password input box
        confirm_rect = pygame.Rect(center_x - 150, center_y + 120, 300, 40)
        self.input_boxes["confirm_box"] = confirm_rect
        box_color = (255, 200, 100) if self.active_input == "confirm" else (100, 100, 120)
        pygame.draw.rect(surface, box_color, confirm_rect, 3)
        confirm_display = "*" * len(self.confirm_password_input)
        confirm_text = self.font_normal.render(confirm_display, True, (255, 255, 255))
        surface.blit(confirm_text, (confirm_rect.x + 10, confirm_rect.y + 5))
        
        # Error message
        if self.error_message:
            error_text = self.font_small.render(self.error_message, True, (255, 100, 100))
            surface.blit(error_text, (center_x - 150, center_y + 180))
        
        # Buttons
        button_y = center_y + 230
        
        # Register button
        register_btn = pygame.Rect(center_x - 160, button_y, 140, 50)
        pygame.draw.rect(surface, (100, 150, 100), register_btn)
        pygame.draw.rect(surface, (150, 200, 150), register_btn, 2)
        register_text = self.font_normal.render("Register", True, (255, 255, 255))
        register_rect = register_text.get_rect(center=register_btn.center)
        surface.blit(register_text, register_rect)
        
        # Back button
        back_btn = pygame.Rect(center_x + 20, button_y, 140, 50)
        pygame.draw.rect(surface, (100, 100, 100), back_btn)
        pygame.draw.rect(surface, (150, 150, 150), back_btn, 2)
        back_text = self.font_normal.render("Back", True, (255, 255, 255))
        back_rect = back_text.get_rect(center=back_btn.center)
        surface.blit(back_text, back_rect)
        
        # Hint
        hint = self.font_small.render("Click input boxes to type, TAB to switch, ENTER to register", True, (150, 150, 150))
        surface.blit(hint, (center_x - 220, button_y + 70))
        
        return {
            "register_btn": register_btn,
            "back_btn": back_btn
        }
    
    def reset(self):
        """Reset register form"""
        self.username_input = ""
        self.password_input = ""
        self.confirm_password_input = ""
        self.active_input = None
        self.error_message = ""
        self.input_boxes = {}
    
    def _calculate_button_rects(self, screen_width, screen_height):
        """Calculate button rects without drawing - for event handling"""
        center_x = screen_width // 2
        center_y = screen_height // 2
        button_y = center_y + 230
        
        register_btn = pygame.Rect(center_x - 160, button_y, 140, 50)
        back_btn = pygame.Rect(center_x + 20, button_y, 140, 50)
        
        return {
            "register_btn": register_btn,
            "back_btn": back_btn
        }
    
    def set_error(self, message):
        """Set error message"""
        self.error_message = message
    
    def get_credentials(self):
        """Get current username and passwords"""
        return self.username_input, self.password_input, self.confirm_password_input



class LeaderboardScreen:
    """Handles leaderboard display"""
    
    def __init__(self):
        self.font_large = pygame.font.SysFont("Verdana", 36)
        self.font_normal = pygame.font.SysFont("Verdana", 24)
        self.font_small = pygame.font.SysFont("Verdana", 18)
        self.leaderboard_data = []
        self.scroll_offset = 0
        
    def set_leaderboard(self, data):
        """Set leaderboard data
        data: list of dicts with 'username' and 'score' keys
        """
        self.leaderboard_data = data
        self.scroll_offset = 0
    
    def handle_event(self, event):
        """Handle input events for leaderboard screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.key == pygame.K_DOWN:
                self.scroll_offset = min(len(self.leaderboard_data) - 1, self.scroll_offset + 1)
            elif event.key == pygame.K_ESCAPE:
                return "back"
        
        return None
    
    def draw(self, surface, screen_width, screen_height):
        """Draw leaderboard"""
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(230)
        overlay.fill((20, 20, 40))
        surface.blit(overlay, (0, 0))
        
        center_x = screen_width // 2
        
        # Title
        title = self.font_large.render("Leaderboard", True, (255, 200, 100))
        title_rect = title.get_rect(center=(center_x, 50))
        surface.blit(title, title_rect)
        
        # Header
        header_y = 120
        rank_text = self.font_normal.render("Rank", True, (255, 200, 100))
        name_text = self.font_normal.render("Username", True, (255, 200, 100))
        score_text = self.font_normal.render("Score", True, (255, 200, 100))
        
        surface.blit(rank_text, (center_x - 300, header_y))
        surface.blit(name_text, (center_x - 150, header_y))
        surface.blit(score_text, (center_x + 100, header_y))
        
        # Draw leaderboard entries
        entry_y = header_y + 60
        entry_height = 40
        max_entries = 10
        
        for i, entry in enumerate(self.leaderboard_data[:max_entries]):
            rank = i + 1
            username = entry.get("username", "Unknown")
            score = entry.get("score", 0)
            
            # Highlight current user (if applicable)
            color = (255, 255, 100) if i == 0 else (200, 200, 200)
            
            rank_str = self.font_normal.render(f"#{rank}", True, color)
            name_str = self.font_normal.render(username[:15], True, color)
            score_str = self.font_normal.render(str(score), True, color)
            
            surface.blit(rank_str, (center_x - 300, entry_y))
            surface.blit(name_str, (center_x - 150, entry_y))
            surface.blit(score_str, (center_x + 100, entry_y))
            
            entry_y += entry_height
        
        # Instructions
        hint = self.font_small.render("Press ESC to go back | UP/DOWN to scroll", True, (150, 150, 150))
        surface.blit(hint, (center_x - 200, screen_height - 80))
        
        # Back button
        back_btn = pygame.Rect(center_x - 70, screen_height - 130, 140, 50)
        pygame.draw.rect(surface, (100, 100, 100), back_btn)
        pygame.draw.rect(surface, (150, 150, 150), back_btn, 2)
        back_text = self.font_normal.render("Back", True, (255, 255, 255))
        back_rect = back_text.get_rect(center=back_btn.center)
        surface.blit(back_text, back_rect)
        
        return {
            "back_btn": back_btn
        }

    def _calculate_button_rects(self, screen_width, screen_height):
        """Calculate back button rect without drawing - for event handling."""
        center_x = screen_width // 2
        back_btn = pygame.Rect(center_x - 70, screen_height - 130, 140, 50)
        return {"back_btn": back_btn}

class GuestLoadScreen:
    """Handles guest profile selection"""
    
    def __init__(self):
        self.font_large = pygame.font.SysFont("Verdana", 36)
        self.font_normal = pygame.font.SysFont("Verdana", 24)
        self.font_small = pygame.font.SysFont("Verdana", 18)
        self.profiles = []
        self.profile_rects = {}
    
    def set_profiles(self, profiles):
        """Set the list of available guest profiles"""
        self.profiles = profiles
        self.profile_rects = {}
    
    def handle_event(self, event):
        """Handle input events for guest load screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
        return None
    
    def draw(self, surface, screen_width, screen_height):
        """Draw guest profile selection screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(230)
        overlay.fill((20, 20, 40))
        surface.blit(overlay, (0, 0))
        
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        # Title
        title = self.font_large.render("Select Guest Profile", True, (255, 200, 100))
        title_rect = title.get_rect(center=(center_x, center_y - 200))
        surface.blit(title, title_rect)
        
        # Profile buttons
        button_y = center_y - 100
        button_width = 280
        button_height = 50
        self.profile_rects = {}
        
        for idx, name in enumerate(self.profiles):
            profile_rect = pygame.Rect(center_x - button_width // 2, button_y + idx * (button_height + 10), button_width, button_height)
            self.profile_rects[name] = profile_rect
            pygame.draw.rect(surface, (100, 150, 200), profile_rect)
            pygame.draw.rect(surface, (150, 200, 255), profile_rect, 2)
            name_text = self.font_normal.render(name, True, (255, 255, 255))
            surface.blit(name_text, name_text.get_rect(center=profile_rect.center))
        
        # New guest profile button
        new_guest_y = button_y + len(self.profiles) * (button_height + 10) + 20
        new_guest_rect = pygame.Rect(center_x - button_width // 2, new_guest_y, button_width, button_height)
        self.profile_rects["_new_profile"] = new_guest_rect
        pygame.draw.rect(surface, (150, 200, 150), new_guest_rect)
        pygame.draw.rect(surface, (200, 255, 200), new_guest_rect, 2)
        new_text = self.font_normal.render("New Guest Profile", True, (255, 255, 255))
        surface.blit(new_text, new_text.get_rect(center=new_guest_rect.center))
        
        # Back button
        back_y = new_guest_y + button_height + 40
        back_rect = pygame.Rect(center_x - button_width // 2, back_y, button_width, button_height)
        self.profile_rects["_back"] = back_rect
        pygame.draw.rect(surface, (100, 100, 100), back_rect)
        pygame.draw.rect(surface, (150, 150, 150), back_rect, 2)
        back_text = self.font_normal.render("Back", True, (255, 255, 255))
        surface.blit(back_text, back_text.get_rect(center=back_rect.center))
        
        return self.profile_rects
    
    def get_clicked_profile(self, mouse_pos):
        """Return the profile name if clicked, or special action if other button clicked"""
        for key, rect in self.profile_rects.items():
            if rect.collidepoint(mouse_pos):
                return key
        return None


class SaveDialog:
    """Save dialog screen similar to LoginScreen/GuestLoadScreen"""
    
    def __init__(self):
        self.font_large = pygame.font.SysFont("Verdana", 36)
        self.font_normal = pygame.font.SysFont("Verdana", 24)
        self.font_small = pygame.font.SysFont("Verdana", 18)
        
        self.dialog_type = "save_before_exit"  # "save_before_exit", "back_confirm", "quit_confirm"
        self.phase = "confirm"  # "confirm" or "select_profile"
        self.message = ""
        self.profiles = []
        self.selected_profile = None
        self.profile_rects = {}
        self.screen_width = 1280
        self.screen_height = 800
        
    def set_state(self, dialog_type, message, profiles=None):
        """Configure the dialog"""
        self.dialog_type = dialog_type
        self.message = message
        self.phase = "confirm"
        self.profiles = profiles or []
        self.selected_profile = self.profiles[0] if self.profiles else None
        self.profile_rects = {}
        
    def handle_event(self, event):
        """Handle input events. Returns action or None"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "cancel"
        return None
    
    def _calculate_button_rects(self, screen_width, screen_height):
        """Calculate button rects without drawing - used for event handling"""
        dialog_width = min(500, screen_width // 2.5)
        dialog_height = min(400, screen_height // 2)
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        
        button_rects = {}
        y_offset = dialog_y + 30
        
        if self.phase == "confirm":
            # Match draw() spacing exactly
            y_offset += 50  # Title space
            y_offset += 80  # Message space + button offset
            
            button_width = 120
            button_height = 50
            
            yes_rect = pygame.Rect(dialog_x + dialog_width // 4 - button_width // 2, y_offset, button_width, button_height)
            no_rect = pygame.Rect(dialog_x + 3 * dialog_width // 4 - button_width // 2, y_offset, button_width, button_height)
            
            button_rects["yes"] = yes_rect
            button_rects["no"] = no_rect
            
        elif self.phase == "select_profile":
            y_offset += 60
            button_width = 280
            button_height = 50
            
            for profile in self.profiles:
                profile_rect = pygame.Rect(
                    dialog_x + (dialog_width - button_width) // 2,
                    y_offset,
                    button_width,
                    button_height
                )
                button_rects[profile] = profile_rect
                y_offset += button_height + 10
            
            # Back button
            back_rect = pygame.Rect(
                dialog_x + (dialog_width - button_width) // 2,
                y_offset,
                button_width,
                button_height
            )
            button_rects["back"] = back_rect
        
        return button_rects
        
    def draw(self, surface, screen_width, screen_height, mouse_pos=None):
        """Draw the dialog and return button rects"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        dialog_width = min(500, screen_width // 2.5)
        dialog_height = min(400, screen_height // 2)
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Dialog box
        pygame.draw.rect(surface, (50, 50, 50), (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(surface, (100, 150, 200), (dialog_x, dialog_y, dialog_width, dialog_height), 3)
        
        button_rects = {}
        y_offset = dialog_y + 30
        
        if self.phase == "confirm":
            # Title
            title_text = self.font_large.render(
                "Save?" if self.dialog_type == "save_before_exit" else 
                "Quit?" if self.dialog_type == "quit_confirm" else "Back?",
                True, (255, 255, 255)
            )
            title_rect = title_text.get_rect(center=(screen_width // 2, y_offset))
            surface.blit(title_text, title_rect)
            
            # Message
            y_offset += 50
            msg_text = self.font_normal.render(self.message, True, (200, 200, 200))
            msg_rect = msg_text.get_rect(center=(screen_width // 2, y_offset))
            surface.blit(msg_text, msg_rect)
            
            # Buttons
            button_width = 120
            button_height = 50
            y_offset += 80
            
            yes_rect = pygame.Rect(dialog_x + dialog_width // 4 - button_width // 2, y_offset, button_width, button_height)
            no_rect = pygame.Rect(dialog_x + 3 * dialog_width // 4 - button_width // 2, y_offset, button_width, button_height)
            
            # Yes button with hover effect
            yes_hover = mouse_pos and yes_rect.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (70, 200, 70) if yes_hover else (50, 150, 50), yes_rect)
            pygame.draw.rect(surface, (150, 255, 150) if yes_hover else (100, 200, 100), yes_rect, 2)
            yes_text = self.font_normal.render("Yes", True, (255, 255, 255))
            surface.blit(yes_text, yes_text.get_rect(center=yes_rect.center))
            button_rects["yes"] = yes_rect
            
            # No button with hover effect
            no_hover = mouse_pos and no_rect.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (200, 70, 70) if no_hover else (150, 50, 50), no_rect)
            pygame.draw.rect(surface, (255, 150, 150) if no_hover else (200, 100, 100), no_rect, 2)
            no_text = self.font_normal.render("No", True, (255, 255, 255))
            surface.blit(no_text, no_text.get_rect(center=no_rect.center))
            button_rects["no"] = no_rect
            
        elif self.phase == "select_profile":
            # Title
            title_text = self.font_large.render("Select Profile", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(screen_width // 2, y_offset))
            surface.blit(title_text, title_rect)
            
            # Profile buttons
            y_offset += 60
            button_width = 280
            button_height = 50
            
            for profile in self.profiles:
                profile_rect = pygame.Rect(
                    dialog_x + (dialog_width - button_width) // 2,
                    y_offset,
                    button_width,
                    button_height
                )
                
                is_selected = profile == self.selected_profile
                is_hover = mouse_pos and profile_rect.collidepoint(mouse_pos)
                
                # Brighter colors on hover
                if is_hover:
                    pygame.draw.rect(surface, (100, 150, 200), profile_rect)
                elif is_selected:
                    pygame.draw.rect(surface, (80, 120, 160), profile_rect)
                else:
                    pygame.draw.rect(surface, (50, 80, 130), profile_rect)
                    
                pygame.draw.rect(surface, (200, 255, 255) if is_hover else (150, 200, 255) if is_selected else (100, 150, 200), profile_rect, 2)
                
                profile_text = self.font_normal.render(profile, True, (255, 255, 255))
                surface.blit(profile_text, profile_text.get_rect(center=profile_rect.center))
                
                button_rects[profile] = profile_rect
                y_offset += button_height + 10
            
            # Back button with hover
            back_rect = pygame.Rect(
                dialog_x + (dialog_width - button_width) // 2,
                y_offset,
                button_width,
                button_height
            )
            back_hover = mouse_pos and back_rect.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (180, 180, 180) if back_hover else (150, 150, 150), back_rect)
            pygame.draw.rect(surface, (220, 220, 220) if back_hover else (180, 180, 180), back_rect, 2)
            back_text = self.font_normal.render("Back", True, (255, 255, 255))
            surface.blit(back_text, back_text.get_rect(center=back_rect.center))
            button_rects["back"] = back_rect
        
        return button_rects
    
    def get_clicked(self, mouse_pos, button_rects):
        """Return clicked button name or None"""
        for name, rect in button_rects.items():
            if rect.collidepoint(mouse_pos):
                return name
        return None