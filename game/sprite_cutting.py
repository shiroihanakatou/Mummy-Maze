import os
import json
import pygame
from PIL import Image

IN_PATH = r"D:\pygame\mummy_maze\game\assets\sprite_sheet\40750.png"

DIR_ORDER = ["up", "down", "left", "right"]
DEFAULT_SCRIPT = [0, 1, 2, 1, 2, 0]


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def norm_rect(x0, y0, x1, y1):
    x = min(x0, x1)
    y = min(y0, y1)
    w = abs(x1 - x0)
    h = abs(y1 - y0)
    return pygame.Rect(x, y, w, h)


def pack_vertical(rects, pad=2):
    if not rects:
        return 1, 1, []
    max_w = max(r.w for r in rects)
    W = max_w + pad * 2
    y = pad
    slots = []
    for r in rects:
        slots.append((pad, y))
        y += r.h + pad
    H = y
    return W, H, slots


def sanitize_filename(s: str) -> str:
    s = s.strip()
    if not s:
        return "atlas"
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    out = []
    for ch in s:
        if ch in allowed:
            out.append(ch)
        elif ch in (" ", "\t"):
            out.append("_")
    name = "".join(out).strip("_")
    return name if name else "atlas"


def parse_int(s, default=0):
    s = s.strip()
    if s == "":
        return default
    if s.isdigit():
        return int(s)
    try:
        return int(float(s))
    except:
        return default


def parse_float(s, default=1.0):
    s = s.strip()
    if s == "":
        return default
    try:
        return float(s)
    except:
        return default


def parse_int_list(s):
    t = s.strip()
    if t == "":
        return None
    t = t.replace("[", " ").replace("]", " ").replace("(", " ").replace(")", " ")
    t = t.replace(";", ",")
    parts = []
    cur = ""
    for ch in t:
        if ch in "0123456789-":
            cur += ch
        elif ch in ", \t\n\r":
            if cur != "":
                parts.append(cur)
                cur = ""
        else:
            if cur != "":
                parts.append(cur)
                cur = ""
    if cur != "":
        parts.append(cur)

    out = []
    for p in parts:
        try:
            out.append(int(p))
        except:
            return None
    return out if out else None


class Button:
    def __init__(self, rect, text, on_click):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_click = on_click

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surf, font, hover, active=False):
        if active:
            bg = (90, 70, 20)
            bd = (255, 215, 0)
        else:
            bg = (42, 42, 42) if not hover else (70, 70, 70)
            bd = (120, 120, 120) if not hover else (210, 210, 210)
        pygame.draw.rect(surf, bg, self.rect, border_radius=10)
        pygame.draw.rect(surf, bd, self.rect, 2, border_radius=10)
        t = font.render(self.text, True, (235, 235, 235))
        surf.blit(t, t.get_rect(center=self.rect.center))


class InputField:
    def __init__(self, label, kind, text=""):
        self.label = label
        self.kind = kind
        self.text = text
        self.rect = pygame.Rect(0, 0, 10, 10)

    def allowed(self, ch):
        if self.kind == "text":
            return ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- "
        if self.kind == "int":
            return ch.isdigit()
        if self.kind == "float":
            return ch in "0123456789."
        if self.kind == "list":
            return ch in "0123456789,-[]() ;"
        return False


def safe_set_mode_fullscreen_scaled():
    info = pygame.display.Info()
    dw, dh = info.current_w, info.current_h
    try:
        return pygame.display.set_mode((dw, dh), pygame.FULLSCREEN | pygame.SCALED)
    except pygame.error:
        return pygame.display.set_mode((dw, dh), pygame.FULLSCREEN)


def safe_set_mode_windowed(size=(1280, 800)):
    try:
        return pygame.display.set_mode(size, pygame.RESIZABLE | pygame.SCALED)
    except pygame.error:
        return pygame.display.set_mode(size, pygame.RESIZABLE)


def compute_view(canvas, ox, oy, zoom, IMG_W, IMG_H):
    vw = max(1, min(IMG_W, int(canvas.w / zoom)))
    vh = max(1, min(IMG_H, int(canvas.h / zoom)))
    view = pygame.Rect(int(ox), int(oy), vw, vh)
    view.x = clamp(view.x, 0, IMG_W - view.w)
    view.y = clamp(view.y, 0, IMG_H - view.h)
    return view


def screen_to_img(mx, my, canvas, view, IMG_W, IMG_H):
    px = mx - canvas.x
    py = my - canvas.y
    ix = view.x + int(px * view.w / canvas.w)
    iy = view.y + int(py * view.h / canvas.h)
    ix = clamp(ix, 0, IMG_W - 1)
    iy = clamp(iy, 0, IMG_H - 1)
    return ix, iy


def img_to_screen(ix, iy, canvas, view):
    sx = canvas.x + int((ix - view.x) * canvas.w / view.w)
    sy = canvas.y + int((iy - view.y) * canvas.h / view.h)
    return sx, sy


def fit_text(font, text, max_w):
    if font.size(text)[0] <= max_w:
        return text
    ell = "..."
    s = text
    while s and font.size(s + ell)[0] > max_w:
        s = s[:-1]
    return s + ell if s else ell


def draw_field(screen, font, font_small, field, active, x, y, w, h):
    label = font_small.render(field.label, True, (220, 220, 220))
    screen.blit(label, (x, y))
    r = pygame.Rect(x, y + 18, w, h)
    field.rect = r

    bg = (55, 55, 55) if active else (40, 40, 40)
    bd = (220, 220, 220) if active else (130, 130, 130)
    pygame.draw.rect(screen, bg, r, border_radius=10)
    pygame.draw.rect(screen, bd, r, 2, border_radius=10)

    inner_w = r.w - 16
    txt = field.text.strip()
    if txt == "":
        placeholder = font_small.render("enter", True, (170, 170, 170))
        screen.blit(placeholder, (r.x + 8, r.y + 8))
    else:
        shown = fit_text(font_small, txt, inner_w)
        t = font_small.render(shown, True, (240, 240, 240))
        screen.blit(t, (r.x + 8, r.y + 8))

    return r.bottom


def main():
    pil_img = Image.open(IN_PATH).convert("RGBA")
    IMG_W, IMG_H = pil_img.size

    pygame.init()
    pygame.font.init()

    screen = safe_set_mode_fullscreen_scaled()
    pygame.display.set_caption("Sprite Picker")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)
    font_small = pygame.font.SysFont(None, 18)

    sheet = pygame.image.fromstring(pil_img.tobytes(), pil_img.size, "RGBA").convert_alpha()

    pad_ui = 10
    gap = 10
    toolbar_h = 56
    panel_w = 420

    is_fullscreen = True
    show_panel = True

    zoom = 2.0
    ox, oy = 0.0, 0.0

    selecting = False
    select_start = (0, 0)
    current_rect = None

    panning = False
    pan_start_mouse = (0, 0)
    pan_start_off = (0.0, 0.0)
    pan_scale_x = 1.0
    pan_scale_y = 1.0

    picked = []
    last_msg = ""

    bg_pick_armed = False
    background_color = (0, 0, 0)

    fields = {
        "file_name": InputField("file_name", "text", "ash"),
        "len": InputField("len", "int", "3"),
        "cost": InputField("cost", "int", "1000"),
        "scale": InputField("scale", "float", "1.5"),
        "script_up": InputField("move_script.up", "list", "0,1,2,1,2,0"),
        "script_down": InputField("move_script.down", "list", "0,1,2,1,2,0"),
        "script_left": InputField("move_script.left", "list", "0,1,2,1,2,0"),
        "script_right": InputField("move_script.right", "list", "0,1,2,1,2,0"),
    }
    active_field_key = None
    panel_scroll = 0

    SCROLLBAR = 12
    SCROLL_M = 3
    SCROLL_THUMB_MIN = 24

    scroll_drag = None
    scroll_drag_start_mouse = (0, 0)
    scroll_drag_start_view = (0, 0)
    scroll_drag_max_thumb = 1
    scroll_drag_img_range = 1

    REVIEW_TH = 32
    REVIEW_AH = 64
    REVIEW_MS = 120
    review_cache = {}

    edit_mode = None
    edit_handle = None
    edit_start_mouse = (0, 0)
    edit_start_rect = None
    HANDLE_PX = 10

    def get_layout():
        sw, sh = screen.get_size()
        toolbar = pygame.Rect(0, 0, sw, toolbar_h)
        if show_panel:
            panel = pygame.Rect(sw - panel_w, toolbar_h, panel_w, sh - toolbar_h)
            canvas = pygame.Rect(0, toolbar_h, sw - panel_w, sh - toolbar_h)
        else:
            panel = pygame.Rect(sw, toolbar_h, 0, sh - toolbar_h)
            canvas = pygame.Rect(0, toolbar_h, sw, sh - toolbar_h)
        return sw, sh, toolbar, canvas, panel

    def clamp_view_bounds(canvas):
        nonlocal ox, oy
        view_w = min(IMG_W, canvas.w / zoom)
        view_h = min(IMG_H, canvas.h / zoom)
        ox = clamp(ox, 0, max(0, IMG_W - view_w))
        oy = clamp(oy, 0, max(0, IMG_H - view_h))

    def fit_to_screen(canvas):
        nonlocal zoom, ox, oy
        zx = canvas.w / IMG_W
        zy = canvas.h / IMG_H
        zoom = clamp(min(zx, zy), 0.25, 16.0)
        ox, oy = 0.0, 0.0
        clamp_view_bounds(canvas)

    def zoom_at(mx, my, delta, canvas):
        nonlocal zoom, ox, oy
        cur_view = compute_view(canvas, ox, oy, zoom, IMG_W, IMG_H)
        ix, iy = screen_to_img(mx, my, canvas, cur_view, IMG_W, IMG_H)

        zoom *= (1.15 ** delta)
        zoom = clamp(zoom, 0.25, 16.0)

        new_view_w = min(IMG_W, canvas.w / zoom)
        new_view_h = min(IMG_H, canvas.h / zoom)

        px = mx - canvas.x
        py = my - canvas.y

        ox = ix - (px * new_view_w / canvas.w)
        oy = iy - (py * new_view_h / canvas.h)

        ox = clamp(ox, 0, max(0, IMG_W - new_view_w))
        oy = clamp(oy, 0, max(0, IMG_H - new_view_h))

    def toggle_fullscreen():
        nonlocal is_fullscreen, screen
        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            screen = safe_set_mode_fullscreen_scaled()
        else:
            screen = safe_set_mode_windowed((1280, 800))

    def toggle_panel():
        nonlocal show_panel
        show_panel = not show_panel

    def arm_bg_pick():
        nonlocal bg_pick_armed, last_msg
        bg_pick_armed = True
        last_msg = "BG PICK armed: click on canvas to pick color."

    def add_current():
        nonlocal last_msg
        if len(picked) >= 4:
            last_msg = "Only 4 sprites: up, down, left, right."
            return
        if current_rect and current_rect.w > 0 and current_rect.h > 0:
            picked.append(current_rect.copy())
            last_msg = f"Added {DIR_ORDER[len(picked)-1]} ({len(picked)}/4)"

    def undo():
        nonlocal last_msg
        if picked:
            removed = DIR_ORDER[len(picked)-1]
            picked.pop()
            last_msg = f"Undo {removed} -> {len(picked)}/4"

    def clear():
        nonlocal last_msg
        picked.clear()
        last_msg = "Cleared."

    def export_vertical():
        nonlocal last_msg

        if len(picked) < 4:
            last_msg = "Need 4 sprites: up, down, left, right."
            return

        file_name = sanitize_filename(fields["file_name"].text)

        assets_dir = os.path.dirname(os.path.dirname(IN_PATH))
        out_dir = os.path.join(assets_dir, "characters")
        os.makedirs(out_dir, exist_ok=True)

        out_png = os.path.join(out_dir, f"{file_name}.png")
        out_json = os.path.join(out_dir, f"{file_name}.json")

        len_value = max(1, parse_int(fields["len"].text, 1))
        cost_value = parse_int(fields["cost"].text, 0)
        scale_value = parse_float(fields["scale"].text, 1.0)

        ms_up = parse_int_list(fields["script_up"].text) or DEFAULT_SCRIPT[:]
        ms_down = parse_int_list(fields["script_down"].text) or DEFAULT_SCRIPT[:]
        ms_left = parse_int_list(fields["script_left"].text) or DEFAULT_SCRIPT[:]
        ms_right = parse_int_list(fields["script_right"].text) or DEFAULT_SCRIPT[:]

        outW, outH, slots = pack_vertical(picked, pad=2)
        atlas = Image.new("RGBA", (outW, outH), (0, 0, 0, 0))

        sprites = {}
        for i, (r, (dx, dy)) in enumerate(zip(picked, slots)):
            crop = pil_img.crop((r.x, r.y, r.x + r.w, r.y + r.h))
            atlas.paste(crop, (dx, dy))
            key = DIR_ORDER[i]
            sprites[key] = {
                "src_rect": [r.x, r.y, r.w, r.h],
                "atlas_rect": [dx, dy, r.w, r.h],
            }

        data = {
            "file_name": file_name,
            "layout": "vertical",
            "len": len_value,
            "background_color": [int(background_color[0]), int(background_color[1]), int(background_color[2])],
            "cost": cost_value,
            "scale": scale_value,
            "move_script": {
                "up": ms_up,
                "down": ms_down,
                "left": ms_left,
                "right": ms_right
            },
            "sprites": sprites
        }

        atlas.save(out_png)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        last_msg = f"Exported: {out_png}, {out_json}"

    def quit_app():
        pygame.quit()
        raise SystemExit

    buttons = []

    def rebuild_buttons():
        nonlocal buttons
        x = pad_ui
        y = 10
        h = 36

        def add_btn(text, cb, w):
            nonlocal x
            buttons.append(Button((x, y, w, h), text, cb))
            x += w + gap

        buttons = []
        add_btn("ADD", add_current, 85)
        add_btn("UNDO", undo, 90)
        add_btn("CLEAR", clear, 95)
        add_btn("BG PICK", arm_bg_pick, 110)
        add_btn("EXPORT", export_vertical, 110)
        add_btn("FIT", lambda: fit_to_screen(get_layout()[3]), 75)
        add_btn("ZOOM +", lambda: zoom_at(*pygame.mouse.get_pos(), 1, get_layout()[3]), 95)
        add_btn("ZOOM -", lambda: zoom_at(*pygame.mouse.get_pos(), -1, get_layout()[3]), 95)
        add_btn("PANEL", toggle_panel, 95)
        add_btn("WINDOW", toggle_fullscreen, 120)
        add_btn("QUIT", quit_app, 80)

    def scroll_ui(canvas, view):
        x0, y0 = canvas.x, canvas.y
        x1, y1 = canvas.right, canvas.bottom

        hbar = pygame.Rect(x0, y1 - SCROLLBAR, max(0, canvas.w - SCROLLBAR), SCROLLBAR)
        vbar = pygame.Rect(x1 - SCROLLBAR, y0, SCROLLBAR, max(0, canvas.h - SCROLLBAR))
        corner = pygame.Rect(x1 - SCROLLBAR, y1 - SCROLLBAR, SCROLLBAR, SCROLLBAR)

        h_enabled = IMG_W > view.w and hbar.w > (SCROLL_M * 2 + SCROLL_THUMB_MIN + 4)
        v_enabled = IMG_H > view.h and vbar.h > (SCROLL_M * 2 + SCROLL_THUMB_MIN + 4)

        hthumb = pygame.Rect(0, 0, 0, 0)
        vthumb = pygame.Rect(0, 0, 0, 0)

        h_max_thumb = 1
        v_max_thumb = 1

        if h_enabled:
            track_w = hbar.w - 2 * SCROLL_M
            thumb_w = max(SCROLL_THUMB_MIN, int(track_w * view.w / IMG_W))
            thumb_w = min(track_w, thumb_w)
            h_max_thumb = max(1, track_w - thumb_w)
            ratio = 0.0 if (IMG_W - view.w) <= 0 else (view.x / (IMG_W - view.w))
            tx = hbar.x + SCROLL_M + int(h_max_thumb * ratio)
            hthumb = pygame.Rect(tx, hbar.y + SCROLL_M, thumb_w, hbar.h - 2 * SCROLL_M)

        if v_enabled:
            track_h = vbar.h - 2 * SCROLL_M
            thumb_h = max(SCROLL_THUMB_MIN, int(track_h * view.h / IMG_H))
            thumb_h = min(track_h, thumb_h)
            v_max_thumb = max(1, track_h - thumb_h)
            ratio = 0.0 if (IMG_H - view.h) <= 0 else (view.y / (IMG_H - view.h))
            ty = vbar.y + SCROLL_M + int(v_max_thumb * ratio)
            vthumb = pygame.Rect(vbar.x + SCROLL_M, ty, vbar.w - 2 * SCROLL_M, thumb_h)

        return {
            "hbar": hbar, "vbar": vbar, "corner": corner,
            "hthumb": hthumb, "vthumb": vthumb,
            "h_enabled": h_enabled, "v_enabled": v_enabled,
            "h_max_thumb": h_max_thumb, "v_max_thumb": v_max_thumb
        }

    def draw_scrollbars(ui):
        hbar, vbar, corner = ui["hbar"], ui["vbar"], ui["corner"]
        hthumb, vthumb = ui["hthumb"], ui["vthumb"]
        h_enabled, v_enabled = ui["h_enabled"], ui["v_enabled"]

        tr = (28, 28, 28)
        bd = (80, 80, 80)
        th = (150, 150, 150) if (scroll_drag is None) else (190, 190, 190)

        if hbar.w > 0 and hbar.h > 0:
            pygame.draw.rect(screen, tr, hbar)
            pygame.draw.rect(screen, bd, hbar, 1)
            if h_enabled:
                pygame.draw.rect(screen, th, hthumb, border_radius=6)
                pygame.draw.rect(screen, (210, 210, 210), hthumb, 1, border_radius=6)
            else:
                pygame.draw.rect(screen, (60, 60, 60), hbar.inflate(-2, -2), border_radius=6)

        if vbar.w > 0 and vbar.h > 0:
            pygame.draw.rect(screen, tr, vbar)
            pygame.draw.rect(screen, bd, vbar, 1)
            if v_enabled:
                pygame.draw.rect(screen, th, vthumb, border_radius=6)
                pygame.draw.rect(screen, (210, 210, 210), vthumb, 1, border_radius=6)
            else:
                pygame.draw.rect(screen, (60, 60, 60), vbar.inflate(-2, -2), border_radius=6)

        if corner.w > 0 and corner.h > 0:
            pygame.draw.rect(screen, (22, 22, 22), corner)
            pygame.draw.rect(screen, bd, corner, 1)

    def make_frame_rects(r, n):
        if r.w <= 0 or r.h <= 0:
            return []
        n = max(1, min(n, r.w))
        rects = []
        for i in range(n):
            x0 = r.x + (i * r.w) // n
            x1 = r.x + ((i + 1) * r.w) // n
            if x1 <= x0:
                x1 = x0 + 1
            if x0 >= r.x + r.w:
                break
            if x1 > r.x + r.w:
                x1 = r.x + r.w
            w = x1 - x0
            if w <= 0:
                continue
            rects.append(pygame.Rect(x0, r.y, w, r.h))
        return rects

    def review_assets(r, n, use_cache=True):
        nonlocal review_cache
        n = max(1, min(n, r.w if r.w > 0 else 1))
        key = (r.x, r.y, r.w, r.h, n, REVIEW_TH, REVIEW_AH)
        if use_cache and key in review_cache:
            return review_cache[key]

        frs = make_frame_rects(r, n)
        thumbs = []
        anims = []
        for fr in frs:
            sub = sheet.subsurface(fr)
            st = REVIEW_TH / max(1, fr.h)
            sa = REVIEW_AH / max(1, fr.h)
            tw = max(1, int(fr.w * st))
            th = max(1, int(fr.h * st))
            aw = max(1, int(fr.w * sa))
            ah = max(1, int(fr.h * sa))
            thumbs.append(pygame.transform.scale(sub, (tw, th)))
            anims.append(pygame.transform.scale(sub, (aw, ah)))

        if len(review_cache) > 200:
            review_cache.clear()
        if use_cache:
            review_cache[key] = (thumbs, anims, frs)
        return thumbs, anims, frs

    def clamp_rect_to_image(r):
        r.x = clamp(r.x, 0, IMG_W)
        r.y = clamp(r.y, 0, IMG_H)
        r.w = clamp(r.w, 0, IMG_W - r.x)
        r.h = clamp(r.h, 0, IMG_H - r.y)
        if r.w <= 0:
            r.w = 1
        if r.h <= 0:
            r.h = 1
        if r.x + r.w > IMG_W:
            r.w = max(1, IMG_W - r.x)
        if r.y + r.h > IMG_H:
            r.h = max(1, IMG_H - r.y)
        return r

    def get_edit_hit(mx, my, canvas, view, r):
        if r is None or r.w <= 0 or r.h <= 0:
            return None, False

        x1, y1 = img_to_screen(r.x, r.y, canvas, view)
        x2, y2 = img_to_screen(r.x + r.w, r.y + r.h, canvas, view)

        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1

        hs = HANDLE_PX
        handles = {
            "nw": pygame.Rect(x1 - hs, y1 - hs, 2 * hs, 2 * hs),
            "ne": pygame.Rect(x2 - hs, y1 - hs, 2 * hs, 2 * hs),
            "sw": pygame.Rect(x1 - hs, y2 - hs, 2 * hs, 2 * hs),
            "se": pygame.Rect(x2 - hs, y2 - hs, 2 * hs, 2 * hs),
        }
        for k, hr in handles.items():
            if hr.collidepoint((mx, my)):
                return k, True

        inside = pygame.Rect(x1, y1, x2 - x1, y2 - y1).collidepoint((mx, my))
        return None, inside

    rebuild_buttons()
    sw, sh, toolbar, canvas, panel = get_layout()
    fit_to_screen(canvas)

    running = True
    while running:
        sw, sh, toolbar, canvas, panel = get_layout()
        view = compute_view(canvas, ox, oy, zoom, IMG_W, IMG_H)
        ui = scroll_ui(canvas, view)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            elif e.type == pygame.VIDEORESIZE and not is_fullscreen:
                screen = safe_set_mode_windowed(e.size)

            elif e.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                dxw = getattr(e, "x", 0)
                dyw = getattr(e, "y", 0)
                mods = pygame.key.get_mods()

                if canvas.collidepoint((mx, my)):
                    if mods & pygame.KMOD_SHIFT:
                        step = max(1, int(view.w * 0.12))
                        ox -= dyw * step
                        ox -= dxw * step
                        clamp_view_bounds(canvas)
                    elif mods & pygame.KMOD_CTRL:
                        step = max(1, int(view.h * 0.12))
                        oy -= dyw * step
                        clamp_view_bounds(canvas)
                    else:
                        zoom_at(mx, my, dyw, canvas)
                elif show_panel and panel.collidepoint((mx, my)):
                    panel_scroll -= dyw * 40
                    panel_scroll = max(0, panel_scroll)

            elif e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos

                if e.button == 1:
                    active_field_key = None

                    if ui["h_enabled"] and (ui["hthumb"].collidepoint((mx, my)) or ui["hbar"].collidepoint((mx, my))):
                        if ui["hthumb"].collidepoint((mx, my)):
                            scroll_drag = "h"
                            scroll_drag_start_mouse = (mx, my)
                            scroll_drag_start_view = (view.x, view.y)
                            scroll_drag_max_thumb = ui["h_max_thumb"]
                            scroll_drag_img_range = max(1, IMG_W - view.w)
                        else:
                            track_x0 = ui["hbar"].x + SCROLL_M
                            track_w = ui["hbar"].w - 2 * SCROLL_M
                            thumb_w = ui["hthumb"].w
                            max_thumb = max(1, track_w - thumb_w)
                            px = clamp(mx - track_x0 - thumb_w // 2, 0, max_thumb)
                            ratio = px / max_thumb
                            ox = ratio * (IMG_W - view.w)
                            clamp_view_bounds(canvas)
                        continue

                    if ui["v_enabled"] and (ui["vthumb"].collidepoint((mx, my)) or ui["vbar"].collidepoint((mx, my))):
                        if ui["vthumb"].collidepoint((mx, my)):
                            scroll_drag = "v"
                            scroll_drag_start_mouse = (mx, my)
                            scroll_drag_start_view = (view.x, view.y)
                            scroll_drag_max_thumb = ui["v_max_thumb"]
                            scroll_drag_img_range = max(1, IMG_H - view.h)
                        else:
                            track_y0 = ui["vbar"].y + SCROLL_M
                            track_h = ui["vbar"].h - 2 * SCROLL_M
                            thumb_h = ui["vthumb"].h
                            max_thumb = max(1, track_h - thumb_h)
                            py = clamp(my - track_y0 - thumb_h // 2, 0, max_thumb)
                            ratio = py / max_thumb
                            oy = ratio * (IMG_H - view.h)
                            clamp_view_bounds(canvas)
                        continue

                    for b in buttons:
                        if b.hit((mx, my)):
                            b.on_click()
                            break
                    else:
                        if show_panel and panel.collidepoint((mx, my)):
                            for k, f in fields.items():
                                if f.rect.collidepoint((mx, my)):
                                    active_field_key = k
                                    break
                        elif canvas.collidepoint((mx, my)):
                            if bg_pick_armed:
                                ix, iy = screen_to_img(mx, my, canvas, view, IMG_W, IMG_H)
                                r, g, b_, a = pil_img.getpixel((ix, iy))
                                background_color = (r, g, b_)
                                bg_pick_armed = False
                                last_msg = f"BG color: {r},{g},{b_}"
                            else:
                                handle, inside = get_edit_hit(mx, my, canvas, view, current_rect)
                                if current_rect is not None and current_rect.w > 0 and current_rect.h > 0 and (handle or inside):
                                    ix, iy = screen_to_img(mx, my, canvas, view, IMG_W, IMG_H)
                                    edit_start_mouse = (ix, iy)
                                    edit_start_rect = current_rect.copy()
                                    selecting = False
                                    if handle:
                                        edit_mode = "resize"
                                        edit_handle = handle
                                    else:
                                        edit_mode = "move"
                                        edit_handle = None
                                else:
                                    edit_mode = None
                                    edit_handle = None
                                    edit_start_rect = None
                                    selecting = True
                                    select_start = screen_to_img(mx, my, canvas, view, IMG_W, IMG_H)
                                    current_rect = pygame.Rect(select_start[0], select_start[1], 0, 0)

                elif e.button == 3:
                    if canvas.collidepoint((mx, my)):
                        panning = True
                        pan_start_mouse = e.pos
                        pan_start_off = (ox, oy)
                        pan_scale_x = view.w / canvas.w
                        pan_scale_y = view.h / canvas.h

            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button == 1:
                    selecting = False
                    scroll_drag = None
                    edit_mode = None
                    edit_handle = None
                    edit_start_rect = None
                elif e.button == 3:
                    panning = False

            elif e.type == pygame.MOUSEMOTION:
                mx, my = e.pos

                if scroll_drag == "h":
                    dx = mx - scroll_drag_start_mouse[0]
                    ox = scroll_drag_start_view[0] + (dx * scroll_drag_img_range / max(1, scroll_drag_max_thumb))
                    clamp_view_bounds(canvas)

                elif scroll_drag == "v":
                    dy = my - scroll_drag_start_mouse[1]
                    oy = scroll_drag_start_view[1] + (dy * scroll_drag_img_range / max(1, scroll_drag_max_thumb))
                    clamp_view_bounds(canvas)

                elif panning:
                    sx, sy = pan_start_mouse
                    dx = (sx - mx) * pan_scale_x
                    dy = (sy - my) * pan_scale_y
                    ox = pan_start_off[0] + dx
                    oy = pan_start_off[1] + dy
                    clamp_view_bounds(canvas)

                if edit_mode is not None and current_rect is not None and edit_start_rect is not None:
                    ix, iy = screen_to_img(mx, my, canvas, view, IMG_W, IMG_H)

                    if edit_mode == "move":
                        dx = ix - edit_start_mouse[0]
                        dy = iy - edit_start_mouse[1]
                        nr = edit_start_rect.copy()
                        nr.x += dx
                        nr.y += dy
                        nr.x = clamp(nr.x, 0, IMG_W - nr.w)
                        nr.y = clamp(nr.y, 0, IMG_H - nr.h)
                        current_rect = nr

                    elif edit_mode == "resize":
                        sr = edit_start_rect
                        if edit_handle == "nw":
                            ax, ay = sr.x + sr.w, sr.y + sr.h
                            nr = norm_rect(ix, iy, ax, ay)
                        elif edit_handle == "ne":
                            ax, ay = sr.x, sr.y + sr.h
                            nr = norm_rect(ix, iy, ax, ay)
                        elif edit_handle == "sw":
                            ax, ay = sr.x + sr.w, sr.y
                            nr = norm_rect(ix, iy, ax, ay)
                        else:
                            ax, ay = sr.x, sr.y
                            nr = norm_rect(ix, iy, ax, ay)

                        current_rect = clamp_rect_to_image(nr)

                if selecting and current_rect is not None:
                    ix, iy = screen_to_img(mx, my, canvas, view, IMG_W, IMG_H)
                    r = norm_rect(select_start[0], select_start[1], ix, iy)
                    r.x = clamp(r.x, 0, IMG_W)
                    r.y = clamp(r.y, 0, IMG_H)
                    r.w = clamp(r.w, 0, IMG_W - r.x)
                    r.h = clamp(r.h, 0, IMG_H - r.y)
                    current_rect = r

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False

                if active_field_key is not None:
                    f = fields[active_field_key]
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if active_field_key == "file_name":
                            f.text = sanitize_filename(f.text)
                        active_field_key = None
                    elif e.key == pygame.K_BACKSPACE:
                        f.text = f.text[:-1]
                    else:
                        ch = e.unicode
                        if ch and f.allowed(ch):
                            if f.kind == "text" and len(f.text) < 32:
                                f.text += ch
                            elif f.kind in ("int", "float") and len(f.text) < 16:
                                f.text += ch
                            elif f.kind == "list" and len(f.text) < 64:
                                f.text += ch
                else:
                    if e.key == pygame.K_LEFT:
                        ox -= max(1, int(view.w * 0.08))
                        clamp_view_bounds(canvas)
                    elif e.key == pygame.K_RIGHT:
                        ox += max(1, int(view.w * 0.08))
                        clamp_view_bounds(canvas)
                    elif e.key == pygame.K_UP:
                        oy -= max(1, int(view.h * 0.08))
                        clamp_view_bounds(canvas)
                    elif e.key == pygame.K_DOWN:
                        oy += max(1, int(view.h * 0.08))
                        clamp_view_bounds(canvas)

        clamp_view_bounds(canvas)
        view = compute_view(canvas, ox, oy, zoom, IMG_W, IMG_H)
        ui = scroll_ui(canvas, view)

        screen.fill((10, 10, 10))

        pygame.draw.rect(screen, (22, 22, 22), toolbar)
        pygame.draw.line(screen, (70, 70, 70), (0, toolbar_h - 1), (sw, toolbar_h - 1), 1)

        mx, my = pygame.mouse.get_pos()
        for b in buttons:
            active = (b.text == "BG PICK" and bg_pick_armed)
            b.draw(screen, font, b.hit((mx, my)), active=active)

        hint = "LMB drag: select/edit | RMB drag: pan | Wheel: zoom | Shift+Wheel: scroll X | Ctrl+Wheel: scroll Y"
        status = f"{len(picked)}/4 | zoom={zoom:.2f} | bg={background_color[0]},{background_color[1]},{background_color[2]}"
        screen.blit(font_small.render(hint, True, (200, 200, 200)), (pad_ui, 36))
        screen.blit(font_small.render(status, True, (220, 220, 220)), (pad_ui, 18))
        if last_msg:
            screen.blit(font_small.render(last_msg, True, (230, 230, 230)), (pad_ui + 520, 18))

        sub = sheet.subsurface(view)
        scaled = pygame.transform.scale(sub, (canvas.w, canvas.h))
        screen.blit(scaled, canvas.topleft)

        for i, r in enumerate(picked):
            x1, y1 = img_to_screen(r.x, r.y, canvas, view)
            x2, y2 = img_to_screen(r.x + r.w, r.y + r.h, canvas, view)
            pygame.draw.rect(screen, (255, 215, 0), pygame.Rect(x1, y1, x2 - x1, y2 - y1), 2)
            screen.blit(font_small.render(DIR_ORDER[i], True, (255, 215, 0)), (x1 + 4, y1 + 4))

        if current_rect and current_rect.w > 0 and current_rect.h > 0:
            x1, y1 = img_to_screen(current_rect.x, current_rect.y, canvas, view)
            x2, y2 = img_to_screen(current_rect.x + current_rect.w, current_rect.y + current_rect.h, canvas, view)
            pygame.draw.rect(screen, (80, 200, 255), pygame.Rect(x1, y1, x2 - x1, y2 - y1), 2)
            hs = 6
            for (hx, hy) in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                pygame.draw.rect(screen, (80, 200, 255), pygame.Rect(hx - hs, hy - hs, 2 * hs, 2 * hs))

        draw_scrollbars(ui)

        if show_panel:
            pygame.draw.rect(screen, (18, 18, 18), panel)
            pygame.draw.line(screen, (70, 70, 70), (panel.x, panel.y), (panel.x, panel.bottom), 1)

            px = panel.x + 12
            py = panel.y + 12 - panel_scroll
            w = panel.w - 24
            box_h = 34

            title = font.render("JSON Inputs", True, (235, 235, 235))
            screen.blit(title, (px, py))
            py += 30

            swatch = pygame.Rect(px, py, 42, box_h)
            pygame.draw.rect(screen, background_color, swatch, border_radius=10)
            pygame.draw.rect(screen, (210, 210, 210), swatch, 2, border_radius=10)
            screen.blit(font_small.render("background_color (pick via BG PICK)", True, (210, 210, 210)),
                        (px + 52, py + 10))
            py += 52

            order = ["file_name", "len", "cost", "scale", "script_up", "script_down", "script_left", "script_right"]
            for k in order:
                f = fields[k]
                active = (active_field_key == k)
                py = draw_field(screen, font, font_small, f, active, px, py, w, box_h) + 12

            len_value = max(1, parse_int(fields["len"].text, 1))
            len_value = clamp(len_value, 1, 64)

            py += 6
            screen.blit(font_small.render(f"Review (cut by len={len_value})", True, (210, 210, 210)), (px, py))
            py += 22

            tick = pygame.time.get_ticks()
            anim_idx = (tick // REVIEW_MS)

            def draw_review_card(label, r, y0, use_cache):
                if r is None or r.w <= 0 or r.h <= 0:
                    return y0
                thumbs, anims, frs = review_assets(r, len_value, use_cache=use_cache)
                if not frs:
                    return y0

                pad = 10
                card_x = px
                card_w = w

                ai = anim_idx % max(1, len(anims))
                anim = anims[ai]
                anim_w, anim_h = anim.get_width(), anim.get_height()

                header_h = max(anim_h, 48)

                line1 = font_small.render(f"{label}  src={r.w}x{r.h}  frames={len(frs)}", True, (220, 220, 220))
                fw0 = frs[0].w if frs else 0
                line2 = font_small.render(f"frame_w≈{fw0}px", True, (180, 180, 180))

                gx = card_x + pad
                gy = y0 + pad + header_h + 8
                max_x = card_x + card_w - pad
                curx, cury = gx, gy
                for tmb in thumbs:
                    tw, th = tmb.get_width(), tmb.get_height()
                    if curx + tw > max_x:
                        curx = gx
                        cury += (REVIEW_TH + 6)
                    curx += tw + 6

                grid_h = (cury + REVIEW_TH) - gy if thumbs else 0
                card_h = pad + header_h + 8 + max(0, grid_h) + pad
                card = pygame.Rect(card_x, y0, card_w, card_h)

                pygame.draw.rect(screen, (30, 30, 30), card, border_radius=10)
                pygame.draw.rect(screen, (90, 90, 90), card, 1, border_radius=10)

                screen.blit(anim, (card_x + pad, y0 + pad))
                tx = card_x + pad + anim_w + 10
                screen.blit(line1, (tx, y0 + pad + 2))
                screen.blit(line2, (tx, y0 + pad + 20))

                curx, cury = gx, gy
                for tmb in thumbs:
                    tw, th = tmb.get_width(), tmb.get_height()
                    if curx + tw > max_x:
                        curx = gx
                        cury += (REVIEW_TH + 6)
                    screen.blit(tmb, (curx, cury))
                    curx += tw + 6

                return y0 + card_h + 12

            if current_rect and current_rect.w > 0 and current_rect.h > 0:
                py = draw_review_card("current", current_rect, py, use_cache=False)

            if picked:
                for i, r in enumerate(picked):
                    py = draw_review_card(DIR_ORDER[i], r, py, use_cache=True)

            py += 6
            screen.blit(font_small.render("Picked sprites (must be 4):", True, (210, 210, 210)), (px, py))
            py += 22

            y_preview = py
            for i, r in enumerate(picked):
                crop = sheet.subsurface(r)
                sc = min(1.0, (w - 20) / max(1, r.w))
                tw = max(1, int(r.w * sc))
                th = max(1, int(r.h * sc))
                thumb = pygame.transform.scale(crop, (tw, th))

                card = pygame.Rect(px, y_preview, w, th + 26)
                pygame.draw.rect(screen, (30, 30, 30), card, border_radius=10)
                pygame.draw.rect(screen, (90, 90, 90), card, 1, border_radius=10)

                screen.blit(thumb, (px + 10, y_preview + 10))
                lab = font_small.render(f"{DIR_ORDER[i]}  src={r.w}x{r.h}", True, (210, 210, 210))
                screen.blit(lab, (px + 10 + tw + 10, y_preview + 12))
                y_preview += th + 36

            content_h = (y_preview - (panel.y + 12)) + panel_scroll
            max_scroll = max(0, content_h - panel.h + 20)
            panel_scroll = clamp(panel_scroll, 0, max_scroll)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
