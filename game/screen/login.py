"""Login and Account Creation Screen"""
import pygame
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets/screen"
import pygame

class StoneButton:
    def __init__(self, image, center_pos):
        self.image = image
        # Lấy Rect trực tiếp từ ảnh đã scale và căn giữa
        self.rect = self.image.get_rect(center=center_pos)
        
    def draw(self, surface, mouse_pos):
        # Hiệu ứng hover sáng lên
        is_hover = self.rect.collidepoint(mouse_pos)
        display_img = self.image.copy()
        if is_hover:
            display_img.fill((40, 40, 40), special_flags=pygame.BLEND_RGB_ADD)
            
        surface.blit(display_img, self.rect.topleft)
        return self.rect # Giữ logic return rect của bạn

    def is_clicked(self, mouse_pos):
        """Kiểm tra va chạm chuột"""
        return self.rect.collidepoint(mouse_pos)
class LoginScreen:
    """Handles login UI and input"""
    
    def __init__(self, screen_width, screen_height):
        center_x, center_y=screen_width//2, screen_height//2
        self.font_title = pygame.font.SysFont("Impact", 32)
        self.font_label = pygame.font.SysFont("Verdana", 20, bold=True)
        self.font_input = pygame.font.SysFont("Verdana", 18)
        self.font_btn = pygame.font.SysFont("Impact", 24)
        self.font_small = pygame.font.SysFont("Verdana", 16)

        # --- TẢI TÀI NGUYÊN HÌNH ẢNH ---
       
        #self.bg_img = pygame.image.load(ASSETS_DIR / "mummy_maze_bg.jpg").convert()
        self.frame_img = pygame.image.load(ASSETS_DIR / "login_frame.png").convert_alpha()
        self.frame_img = pygame.transform.smoothscale(self.frame_img, (640, 720))
        self.frame_rect = self.frame_img.get_rect(center=(center_x, center_y))

        # Nút Login
        self.btn_login_img = pygame.image.load(ASSETS_DIR / "btn_login.png").convert_alpha()
        self.btn_login_img = pygame.transform.smoothscale(self.btn_login_img, (280, 120))
        self.login_button = StoneButton(self.btn_login_img, (center_x - 110, center_y + 72))

        # Nút Register
        self.btn_register_img = pygame.image.load(ASSETS_DIR / "btn_register.png").convert_alpha()
        self.btn_register_img = pygame.transform.smoothscale(self.btn_register_img, (280, 120))
        self.register_button = StoneButton(self.btn_register_img, (center_x + 110, center_y + 72))

        # Nút Guest
        self.btn_guest_img = pygame.image.load(ASSETS_DIR / "btn_guest.png").convert_alpha()
        self.btn_guest_img = pygame.transform.smoothscale(self.btn_guest_img, (220, 120))
        self.guest_button = StoneButton(self.btn_guest_img, (center_x - 105, center_y + 175))

        # Nút Exit (Tương ứng load_guest_btn trong return)
        self.btn_exit_img = pygame.image.load(ASSETS_DIR / "btn_exit.png").convert_alpha()
        self.btn_exit_img = pygame.transform.smoothscale(self.btn_exit_img, (220, 120))
        self.exit_button = StoneButton(self.btn_exit_img, (center_x + 105, center_y + 175))

        
        self.username_input = ""
        self.passcreen_widthord_input = ""
        self.active_input = None  # "username", "passcreen_widthord", or None
        self.error_message = ""
        self.screen_heightow_passcreen_widthord = False
        
        # Input box dimensions
        self.input_boxes = {}
        self.button_width = 200
        self.button_height = 50
        self.frame_rect = self.frame_img.get_rect(center=(screen_width // 2, screen_height// 2))
        # Font
        self.font_large = pygame.font.SysFont("Verdana", 36)
        self.font_normal = pygame.font.SysFont("Verdana", 24)
        self.font_small = pygame.font.SysFont("Verdana", 18)
        
        


    def handle_event(self, event):
        """Handle input events for login screen"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and self.active_input:
                # screen_widthitch between input fields
                self.active_input = "passcreen_widthord" if self.active_input == "username" else "username"
            elif event.key == pygame.K_BACKSPACE:
                if self.active_input == "username":
                    self.username_input = self.username_input[:-1]
                elif self.active_input == "passcreen_widthord":
                    self.passcreen_widthord_input = self.passcreen_widthord_input[:-1]
                self.error_message = ""
            elif event.key == pygame.K_RETURN and self.active_input:
                return "login"  # Signal to attempt login
            elif event.unicode.isprintable() and self.active_input:
                max_len = 20
                if self.active_input == "username":
                    if len(self.username_input) < max_len:
                        self.username_input += event.unicode
                elif self.active_input == "passcreen_widthord":
                    if len(self.passcreen_widthord_input) < max_len:
                        self.passcreen_widthord_input += event.unicode
                self.error_message = ""
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check which input box was clicked
            if "username_box" in self.input_boxes:
                if self.input_boxes["username_box"].collidepoint(event.pos):
                    self.active_input = "username"
                    return None
            if "passcreen_widthord_box" in self.input_boxes:
                if self.input_boxes["passcreen_widthord_box"].collidepoint(event.pos):
                    self.active_input = "passcreen_widthord"
                    return None
            
            # Check if clicked outside input boxes
            if "username_box" in self.input_boxes and not self.input_boxes["username_box"].collidepoint(event.pos):
                if "passcreen_widthord_box" in self.input_boxes and not self.input_boxes["passcreen_widthord_box"].collidepoint(event.pos):
                    self.active_input = None
            if self.login_button.is_clicked(event.pos): return "login"
            if self.register_button.is_clicked(event.pos): return "register"
            if self.guest_button.is_clicked(event.pos): return "guest"
            if self.exit_button.is_clicked(event.pos): return "exit"
        return None
    def _draw_image_button(self, surface, rect, image, text, font, text_color, mouse_pos):
        """Hàm vẽ nút bấm bằng ảnh + text center"""
        is_hover = rect.collidepoint(mouse_pos)
        
        # Vẽ ảnh nút (Co dãn ảnh cho vừa với Rect nếu cần)
        btn_img = pygame.transform.scale(image, (rect.width, rect.height))
        
        # Hiệu ứng hover: Làm ảnh sáng lên một chút
        
        surface.blit(btn_img, rect.topleft)
        
        # Vẽ chữ đè lên ảnh nút (Căn giữa hoàn hảo)
        txt_surf = font.render(text, True, text_color)
        txt_rect = txt_surf.get_rect(center=rect.center)
        surface.blit(txt_surf, txt_rect)

    def draw(self, surface, screen_width, screen_height, mouse_pos):
        """Draw login screen UI"""
        # 1. Vẽ hình nền và lớp phủ
        #surface.blit(pygame.transform.scale(self.bg_img, (screen_width, screen_height)), (0, 0))
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # 2. Vẽ khung đá
        surface.blit(self.frame_img, self.frame_rect)
        center_x, center_y = self.frame_rect.centerx, self.frame_rect.centery
        
        # 3. Vẽ ô nhập liệu (Căn theo Center X/Y để khớp vùng đen của ảnh)
        # Ô Username
        self.input_boxes["username_box"] = pygame.Rect(0, 0, 432, 48)
        self.input_boxes["username_box"].center = (center_x-3, center_y - 104)
        if self.active_input == "username":
            pygame.draw.rect(surface, (255, 215, 0), self.input_boxes["username_box"], 2)

        # Ô Passcreen_widthord
        self.input_boxes["passcreen_widthord_box"] = pygame.Rect(0, 0, 432, 48)
        self.input_boxes["passcreen_widthord_box"].center = (center_x-3, center_y - 13)
        if self.active_input == "passcreen_widthord":
            pygame.draw.rect(surface, (255, 215, 0), self.input_boxes["passcreen_widthord_box"], 2)

        # Hiển thị nội dung text nhập liệu
        username_text = self.font_normal.render(self.username_input, True, (255, 255, 255))
        surface.blit(username_text, (self.input_boxes["username_box"].left + 15, self.input_boxes["username_box"].top + 5))
        
        pwd_display = "*" * len(self.passcreen_widthord_input)
        passcreen_widthord_text = self.font_normal.render(pwd_display, True, (255, 255, 255))
        surface.blit(passcreen_widthord_text, (self.input_boxes["passcreen_widthord_box"].left + 15, self.input_boxes["passcreen_widthord_box"].top + 10))

        # 4. Tính toán và vẽ các nút bấm bằng ẢNH
        # Nút Login & Register (Hàng trên)
        login_btn = self.login_button.draw(surface, mouse_pos)
        create_btn = self.register_button.draw(surface, mouse_pos)
        guest_btn = self.guest_button.draw(surface, mouse_pos)
        exit_btn = self.exit_button.draw(surface, mouse_pos)
        # 5. Vẽ thông báo lỗi
        if self.error_message:
            error_text = self.font_small.render(self.error_message, True, (255, 100, 100))
            surface.blit(error_text, (center_x - 200, center_y + 45))

        # --- GIỮ NGUYÊN RETURN NHƯ CODE CŨ CỦA BẠN ---
        return {
            "login_btn": login_btn,
            "create_btn": create_btn,
            "guest_btn": guest_btn,
            "exit_btn": exit_btn,
        }
    
    def reset(self):
        """Reset login form"""
        self.username_input = ""
        self.passcreen_widthord_input = ""
        self.active_input = None
        self.error_message = ""
        self.screen_heightow_passcreen_widthord = False
        self.input_boxes = {}
    
    def _calculate_button_rects(self, screen_width, screen_height):
        """Calculate button rects without drawing - for event handling"""
        center_x = screen_width // 2
        center_y = screen_height // 2
        button_y = center_y + 170
        
        login_btn = pygame.Rect(center_x - 160, button_y, 140, 50)
        create_btn = pygame.Rect(center_x + 20, button_y, 140, 50)
        guest_btn = pygame.Rect(center_x - 210, button_y + 70, 180, 50)
        exit_btn = pygame.Rect(center_x + 30, button_y + 70, 180, 50)
        
        return {
            "login_btn": login_btn,
            "create_btn": create_btn,
            "guest_btn": guest_btn,
            "exit_btn": exit_btn,
        }
    
    def set_error(self, message):
        """Set error message"""
        self.error_message = message
    
    def get_credentials(self):
        """Get current username and passcreen_widthord"""
        return self.username_input, self.passcreen_widthord_input


class RegisterScreen:
    
    
    def __init__(self, sw, sh):
        cx, cy = sw // 2, sh // 2
        
        # --- DỮ LIỆU NHẬP LIỆU (Giữ nguyên tên biến của bạn) ---
        self.username_input = ""
        self.passcreen_widthord_input = "" # Password
        self.confirm_passcreen_widthord_input = "" # Confirm Password
        self.active_input = None
        self.error_message = ""
        
        # --- FONTS (Sử dụng style giống Guest) ---
        self.font_title = pygame.font.SysFont("Georgia", 32, bold=True)
        self.font_label = pygame.font.SysFont("Verdana", 20, bold=True)
        self.font_text = pygame.font.SysFont("Verdana", 18)
        self.font_hint = pygame.font.SysFont("Verdana", 14, italic=True)

        # --- TẢI TÀI NGUYÊN ---
        try:
            # Khung bảng đá lớn
            raw_frame = pygame.image.load(ASSETS_DIR / "register_frame.png").convert_alpha()
            self.frame_img = pygame.transform.smoothscale(raw_frame, (560, 620))
            
            # Nút đá
            raw_btn = pygame.image.load(ASSETS_DIR / "btn_stone.png").convert_alpha()
            self.btn_img = pygame.transform.smoothscale(raw_btn, (180, 55))
        except:
            self.frame_img = pygame.Surface((560, 620)); self.frame_img.fill((160, 120, 70))
            self.btn_img = pygame.Surface((180, 55)); self.btn_img.fill((100, 100, 100))

        self.frame_rect = self.frame_img.get_rect(center=(cx, cy))

        # --- KHỞI TẠO ĐỐI TƯỢNG NÚT BẤM ---
        # Vị trí nút Register và Back ở cuối bảng đá
        self.register_button = StoneButton(self.btn_img, (cx - 110, cy + 230))
        self.back_button = StoneButton(self.btn_img, (cx + 110, cy + 230))

        self.input_boxes = {}

    def handle_event(self, event, button_rects=None):
        """Xử lý sự kiện bàn phím và chuột"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                # Chuyển đổi giữa các ô
                order = ["username", "passcreen_widthord", "confirm"]
                idx = order.index(self.active_input) if self.active_input in order else -1
                self.active_input = order[(idx + 1) % len(order)]
            
            elif event.key == pygame.K_BACKSPACE:
                if self.active_input == "username": self.username_input = self.username_input[:-1]
                elif self.active_input == "passcreen_widthord": self.passcreen_widthord_input = self.passcreen_widthord_input[:-1]
                elif self.active_input == "confirm": self.confirm_passcreen_widthord_input = self.confirm_passcreen_widthord_input[:-1]
                self.error_message = ""

            elif event.key == pygame.K_RETURN:
                return "register"

            elif event.unicode.isprintable() and self.active_input:
                if len(getattr(self, f"{self.active_input}_input")) < 20:
                    setattr(self, f"{self.active_input}_input", getattr(self, f"{self.active_input}_input") + event.unicode)
                self.error_message = ""

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Kiểm tra click vào nút bấm (Sử dụng StoneButton.is_clicked)
            if self.register_button.is_clicked(event.pos): return "register"
            if self.back_button.is_clicked(event.pos): return "back"

            # Kiểm tra chọn ô nhập liệu
            for name, rect in self.input_boxes.items():
                if rect.collidepoint(event.pos):
                    self.active_input = name.replace("_box", "")
                    return None
            self.active_input = None
            
        return None

    def draw(self, surface, sw, sh, mouse_pos):
        """Vẽ giao diện Register Stone Style"""
        cx, cy = self.frame_rect.centerx, self.frame_rect.centery
        
        # 1. Vẽ lớp phủ tối và Bảng đá nền
        overlay = pygame.Surface((sw, sh))
        overlay.set_alpha(180); overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        surface.blit(self.frame_img, self.frame_rect)

        # 2. Tiêu đề (Màu nâu đậm Ai Cập)
        title_s = self.font_title.render("CREATE ACCOUNT", True, (40, 25, 10))
        surface.blit(title_s, title_s.get_rect(center=(cx, self.frame_rect.top + 70)))

        # 3. Vẽ các nhãn và ô nhập liệu
        # (Username, Password, Confirm)
        field_configs = [
            ("Username:", "username", -100),
            ("Password:", "passcreen_widthord", -5),
            ("Confirm Password:", "confirm_passcreen_widthord", 90)
        ]

        for label, key, offset_y in field_configs:
            # Nhãn chữ
            lbl_s = self.font_label.render(label, True, (60, 40, 20))
            surface.blit(lbl_s, (cx - 200, cy + offset_y - 30))
            
            # Ô nhập liệu (Dạng đục sâu vào đá)
            rect = pygame.Rect(cx - 200, cy + offset_y, 400, 45)
            self.input_boxes[f"{key}_box"] = rect
            
            # Màu viền đổi khi active
            border_color = (255, 215, 0) if self.active_input == key else (80, 60, 40)
            pygame.draw.rect(surface, (50, 40, 30), rect, border_radius=5) # Nền tối ô nhập
            pygame.draw.rect(surface, border_color, rect, 2, border_radius=5) # Viền
            
            # Chữ hiển thị
            val = self.username_input if key == "username" else "*" * len(getattr(self, f"{key}_input"))
            txt_s = self.font_text.render(val, True, (250, 240, 220))
            surface.blit(txt_s, (rect.x + 10, rect.y + 10))

        # 4. Vẽ thông báo lỗi
        if self.error_message:
            err_s = self.font_hint.render(self.error_message, True, (200, 50, 50))
            surface.blit(err_s, (cx - 200, cy + 150))

        # 5. Vẽ các nút đá
        reg_rect = self.register_button.draw(surface, mouse_pos)
        back_rect = self.back_button.draw(surface, mouse_pos)

        # Chữ trên nút
        reg_txt = self.font_label.render("Register", True, (255, 255, 255))
        surface.blit(reg_txt, reg_txt.get_rect(center=reg_rect.center))
        
        back_txt = self.font_label.render("Back", True, (255, 215, 0)) # Chữ vàng cho Back
        surface.blit(back_txt, back_txt.get_rect(center=back_rect.center))

        return {"register_btn": reg_rect, "back_btn": back_rect}

    def reset(self):
        self.username_input = ""; self.passcreen_widthord_input = ""; self.confirm_passcreen_widthord_input = ""
        self.active_input = None; self.error_message = ""
    def get_credentials(self):
   
         # Trả về đúng tên các biến gốc mà bạn muốn giữ
        return self.username_input, self.passcreen_widthord_input, self.confirm_passcreen_widthord_input
import pygame

class LeaderboardScreen:
    """Giao diện bảng điểm cao phong cách bảng đá cổ đại"""
    
    def __init__(self, sw, sh):
        # --- GIỮ NGUYÊN DỮ LIỆU THUẬT TOÁN ---
        self.leaderboard_data = []
        self.scroll_offset = 0
        
        # --- THIẾT LẬP STYLE (Đồng bộ với Guest/Register) ---
        self.font_large = pygame.font.SysFont("Georgia", 36, bold=True)
        self.font_normal = pygame.font.SysFont("Verdana", 20, bold=True)
        self.font_small = pygame.font.SysFont("Verdana", 14, italic=True)
        
        # Tải tài nguyên hình ảnh
        try:
            # Khung bảng đá lớn giống màn hình Register
            raw_frame = pygame.image.load(ASSETS_DIR / "register_frame.png").convert_alpha()
            self.frame_img = pygame.transform.smoothscale(raw_frame, (600, 650))
            
            # Nút đá xám cho phím Back
            raw_btn = pygame.image.load(ASSETS_DIR / "btn_stone_grey.png").convert_alpha()
            self.btn_img = pygame.transform.smoothscale(raw_btn, (160, 50))
        except:
            self.frame_img = pygame.Surface((600, 650)); self.frame_img.fill((160, 120, 70))
            self.btn_img = pygame.Surface((160, 50)); self.btn_img.fill((100, 100, 100))

        self.frame_rect = self.frame_img.get_rect(center=(sw // 2, sh // 2))
        # Nút Back sử dụng StoneButton chuyên dụng
        self.back_button = StoneButton(self.btn_img, (sw // 2, self.frame_rect.bottom - 75))

    def set_leaderboard(self, data):
        """Giữ nguyên thuật toán nạp dữ liệu"""
        self.leaderboard_data = data
        self.scroll_offset = 0
    
    def handle_event(self, event, button_rects=None):
        """Xử lý sự kiện (Giữ nguyên logic scroll)"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.key == pygame.K_DOWN:
                # Thuật toán cuộn không đổi
                self.scroll_offset = min(max(0, len(self.leaderboard_data) - 10), self.scroll_offset + 1)
            elif event.key == pygame.K_ESCAPE:
                return "back"
        
        # Xử lý click chuột cho nút Back
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                return "back"
        return None
    
    def draw(self, surface, screen_width, screen_height, mouse_pos):
        """Vẽ bảng điểm phong cách đá sa thạch"""
        center_x = screen_width // 2
        
        # 1. Overlay tối bán trong suốt
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(180); overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # 2. Vẽ bảng đá nền
        surface.blit(self.frame_img, self.frame_rect)
        
        # 3. Tiêu đề "LEADERBOARD" (Màu nâu đậm Ai Cập)
        title = self.font_large.render("LEADERBOARD", True, (40, 25, 10))
        surface.blit(title, title.get_rect(center=(center_x, self.frame_rect.top + 70)))
        
        # 4. Header (Màu vàng đất)
        header_y = self.frame_rect.top + 130
        rank_h = self.font_normal.render("Rank", True, (100, 70, 40))
        name_h = self.font_normal.render("Username", True, (100, 70, 40))
        score_h = self.font_normal.render("Score", True, (100, 70, 40))
        
        surface.blit(rank_h, (center_x - 220, header_y))
        surface.blit(name_h, (center_x - 80, header_y))
        surface.blit(score_h, (center_x + 120, header_y))
        
        # 5. Vẽ danh sách điểm (Áp dụng scroll_offset vào thuật toán hiển thị)
        max_display = 10
        # Cắt dữ liệu dựa trên offset để cuộn
        display_data = self.leaderboard_data[self.scroll_offset : self.scroll_offset + max_display]
        
        for i, entry in enumerate(display_data):
            entry_y = header_y + 45 + (i * 35)
            # Rank thực tế dựa trên offset
            actual_rank = i + self.scroll_offset + 1
            
            # Highlight Top 1 màu vàng kim, còn lại màu nâu đá
            color = (180, 140, 0) if actual_rank == 1 else (60, 45, 30)
            
            username = entry.get("username", "Unknown")
            score = entry.get("score", 0)
            
            rank_str = self.font_normal.render(f"#{actual_rank}", True, color)
            name_str = self.font_normal.render(username[:15], True, color)
            score_str = self.font_normal.render(f"{score:,}", True, color)
            
            surface.blit(rank_str, (center_x - 220, entry_y))
            surface.blit(name_str, (center_x - 80, entry_y))
            surface.blit(score_str, (center_x + 120, entry_y))
        
        # 6. Chỉ dẫn và Nút Back
        hint = self.font_small.render("Press ESC to go back | UP/DOWN to scroll", True, (80, 60, 40))
        surface.blit(hint, (center_x - 140, self.frame_rect.bottom - 45))
        
        # Vẽ nút Back Stone Style
        back_rect = self.back_button.draw(surface, mouse_pos)
        back_text = self.font_normal.render("Back", True, (255, 215, 0)) # Chữ vàng
        surface.blit(back_text, back_text.get_rect(center=back_rect.center))
        
        return {"back_btn": back_rect}

class GuestLoadScreen:
    """Handles guest profile selection with a stone tablet UI matching the reference game."""
    
    def __init__(self):
        # --- CẤU HÌNH FONT VÀ MÀU SẮC THEO ẢNH MẪU ---
        # Sử dụng font có chân (Serif) đậm và lớn cho tiêu đề
        self.font_title = pygame.font.SysFont("Georgia", 38, bold=True)
        # Sử dụng font rõ ràng, đậm cho các nút
        self.font_button = pygame.font.SysFont("Verdana", 20, bold=True)
        
        # Bảng màu được trích xuất từ ảnh mẫu
        self.colors = {
            # Nền tối bán trong suốt phía sau bảng đá
            "overlay": (20, 15, 10),
            
            # Màu cho tiêu đề (Nâu đen đậm)
            "text_title": (40, 25, 10),
            # Màu chữ cho các nút chính (Trắng kem)
            "text_light": (250, 245, 230),
            # Màu chữ cho nút Cancel/Back (Vàng kim)
            "text_gold": (255, 215, 50),
            
            # --- MÀU ĐÁ (SANDSTONE) ---
            # Màu chính của mặt đá (Nâu vàng cát)
            "stone_face": (180, 140, 90),
            # Màu tối tạo bóng/viền (Nâu đất đậm)
            "stone_dark": (100, 70, 40),
            # Màu sáng tạo viền nổi (Vàng cát sáng)
            "stone_highlight": (210, 170, 110),
            # Màu nền của bảng đá lớn (Tối hơn mặt nút một chút)
            "panel_bg": (160, 120, 70)
        }

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

    def _draw_stone_button(self, surface, rect, text, text_color, is_hovered):
        """Hàm hỗ trợ vẽ nút giả lập khối đá sa thạch 3D"""
        # Xác định màu sắc dựa trên trạng thái hover (sáng hơn khi rê chuột)
        face_color = self.colors["stone_highlight"] if is_hovered else self.colors["stone_face"]
        dark_color = self.colors["stone_dark"]
        
        # 1. Vẽ lớp nền tối bên ngoài (tạo bóng và độ dày)
        pygame.draw.rect(surface, dark_color, rect, border_radius=5)
        
        # 2. Vẽ mặt nút sáng hơn bên trong (tạo hiệu ứng nổi)
        # Thu nhỏ rect lại 4 pixel mỗi chiều để lộ viền tối
        inner_rect = rect.inflate(-4, -4) 
        pygame.draw.rect(surface, face_color, inner_rect, border_radius=5)
        
        # 3. Vẽ viền sáng nhẹ ở cạnh trên và trái để tăng cảm giác 3D
        pygame.draw.line(surface, self.colors["stone_highlight"], (inner_rect.left, inner_rect.top), (inner_rect.right, inner_rect.top), 2)
        pygame.draw.line(surface, self.colors["stone_highlight"], (inner_rect.left, inner_rect.top), (inner_rect.left, inner_rect.bottom), 2)

        # 4. Vẽ chữ căn giữa
        text_surf = self.font_button.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        # Thêm bóng nhẹ cho chữ để dễ đọc hơn trên nền đá
        shadow_surf = self.font_button.render(text, True, self.colors["stone_dark"])
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)

    def draw(self, surface, screen_width, screen_height, mouse_pos=None):
        """Draw the guest profile selection screen mimicking the stone tablet UI"""
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        # --- 1. Lớp phủ nền tối ---
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(220)
        overlay.fill(self.colors["overlay"])
        surface.blit(overlay, (0, 0))
        
        # --- 2. Vẽ Bảng Đá Nền (The Stone Tablet) ---
        # Kích thước bảng đá
        panel_width = 500
        panel_height = 550
        panel_rect = pygame.Rect(center_x - panel_width // 2, center_y - panel_height // 2, panel_width, panel_height)
        
        # Vẽ viền tối ngoài cùng của bảng đá
        pygame.draw.rect(surface, self.colors["stone_dark"], panel_rect, border_radius=12)
        # Vẽ mặt nền bảng đá bên trong
        inner_panel = panel_rect.inflate(-16, -16) # Viền dày
        pygame.draw.rect(surface, self.colors["panel_bg"], inner_panel, border_radius=8)
        # Vẽ một đường viền trang trí mỏng bên trong
        pygame.draw.rect(surface, self.colors["stone_dark"], inner_panel, 4, border_radius=8)

        # --- 3. Tiêu đề (Title) ---
        # Vẽ tiêu đề màu nâu đậm
        title_text = "Select Guest Profile"
        title = self.font_title.render(title_text, True, self.colors["text_title"])
        title_rect = title.get_rect(center=(center_x, panel_rect.top + 60))
        surface.blit(title, title_rect)
        
        # --- 4. Các nút đá (Stone Buttons) ---
        button_width = 400
        button_height = 55
        spacing = 15
        start_y = panel_rect.top + 120
        self.profile_rects = {}
        
        # Nút cho các Profile có sẵn (Dùng màu đá và chữ trắng kem)
        for idx, name in enumerate(self.profiles):
            rect = pygame.Rect(center_x - button_width // 2, start_y + idx * (button_height + spacing), button_width, button_height)
            self.profile_rects[name] = rect
            
            is_hover = mouse_pos and rect.collidepoint(mouse_pos)
            self._draw_stone_button(surface, rect, name, self.colors["text_light"], is_hover)
        
        # Vị trí cho nút tiếp theo
        current_y = start_y + len(self.profiles) * (button_height + spacing)
        
        # Nút "New Game" (Dùng chung kiểu với các nút trên)
        # Để cho giống ảnh, ta sẽ vẽ thêm các nút "NEW GAME" giả nếu chưa đủ 5 slot
        slots_to_fill = 5 - len(self.profiles)
        for i in range(slots_to_fill):
             rect = pygame.Rect(center_x - button_width // 2, current_y, button_width, button_height)
             # Đặt tên key đặc biệt để xử lý sau này
             key_name = f"_new_profile_{i}" 
             self.profile_rects[key_name] = rect
             
             is_hover = mouse_pos and rect.collidepoint(mouse_pos)
             # Tất cả đều là nút đá màu nâu với chữ sáng
             self._draw_stone_button(surface, rect, "NEW GAME", self.colors["text_light"], is_hover)
             current_y += button_height + spacing

        # Nút "Cancel" (Dùng màu đá nhưng chữ màu vàng kim)
        # Đặt nút này ở gần đáy bảng đá
        back_rect = pygame.Rect(center_x - button_width // 2, panel_rect.bottom - 80, button_width, button_height)
        self.profile_rects["_back"] = back_rect
        
        is_hover = mouse_pos and back_rect.collidepoint(mouse_pos)
        # Sử dụng màu chữ vàng cho nút này
        self._draw_stone_button(surface, back_rect, "Cancel", self.colors["text_gold"], is_hover)
        
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