"""Prévia em camadas: foto, logo e coordenadas independentes de zoom/pan."""

from functools import lru_cache
import math
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageEnhance, ImageOps, ImageTk

from theme import COLORS as C, FONT
from watermark import ASSETS, Settings, load_logo, logo_geometry
from platform_support import IS_MAC, wheel_steps


@lru_cache(maxsize=1)
def background_image():
    with Image.open(ASSETS / "background.png") as image:
        return image.convert("RGB")


class BrandedHeader(tk.Canvas):
    def __init__(self, parent, brand, dp):
        super().__init__(parent, bg=C["background"], highlightthickness=0, height=dp(96))
        self.brand, self.dp = brand, dp
        self.photo = None
        self.bind("<Configure>", self._paint)

    def _paint(self, event=None):
        width, height = max(1, self.winfo_width()), max(1, self.winfo_height())
        image = ImageOps.fit(background_image(), (width, height), Image.Resampling.LANCZOS,
                             centering=(0.5, 0.0))
        self.photo = ImageTk.PhotoImage(ImageEnhance.Brightness(image).enhance(0.72))
        self.delete("all")
        self.create_image(0, 0, image=self.photo, anchor="nw")
        self.create_image(self.dp(28), height / 2, image=self.brand, anchor="w")
        left = self.dp(100)
        self.create_text(left, self.dp(31), anchor="w", text="Well Studio", font=(FONT, 23, "bold"),
                         fill=C["ink"])
        self.create_rectangle(left + self.dp(195), self.dp(19), left + self.dp(235), self.dp(44),
                              fill=C["accent_soft"], outline=C["accent"])
        self.create_text(left + self.dp(215), self.dp(31), text="V5", font=(FONT, 9, "bold"),
                         fill=C["accent"])
        self.create_text(left, self.dp(64), anchor="w", text="Marca d'água para fotos de imóveis",
                         font=(FONT, 10), fill=C["muted"])
        if width > self.dp(900):
            self.create_text(width - self.dp(29), height / 2, anchor="e",
                             text="Logo livre  ·  Zoom  ·  Pan", font=(FONT, 11), fill=C["accent"])
        self.create_line(0, height - 1, width, height - 1, fill=C["line"])


class PhotoPreview(ttk.Frame):
    def __init__(self, parent, on_move, on_add, dp):
        super().__init__(parent, style="Workspace.TFrame")
        self.on_move, self.on_add, self.dp = on_move, on_add, dp
        self.photo = None
        self.source = None
        self.settings = Settings()
        self.original = False
        self.locked = False
        self.loading = False
        self.error = None
        self.view_scale = 1.0
        self.center_x = self.center_y = 0.0
        self.fitted = True
        self.viewport = (1, 1)
        self.drag_kind = None
        self.drag_start = None
        self.drag_offset = (0, 0)
        self.space_down = False
        self.draw_after = None
        self.background_size = None
        self.background_tk = self.base_tk = self.logo_tk = None
        self.logo_cache = None
        self.logo_cache_key = None
        self.tool = tk.StringVar(value="logo")
        self.zoom_label = tk.StringVar(value="—")
        self.hint = tk.StringVar(value="Adicione fotos para posicionar a marca diretamente na prévia.")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        toolbar = ttk.Frame(self, padding=(8, 7))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_columnconfigure(2, weight=1)
        self.move_btn = ttk.Radiobutton(toolbar, text="Mover logo", variable=self.tool, value="logo",
                                        style="Mode.Toolbutton", command=self._tool_changed)
        self.move_btn.grid(row=0, column=0, padx=(0, 5))
        self.pan_btn = ttk.Radiobutton(toolbar, text="Navegar", variable=self.tool, value="pan",
                                       style="Mode.Toolbutton", command=self._tool_changed)
        self.pan_btn.grid(row=0, column=1)
        self.zoom_out_btn = ttk.Button(toolbar, text="−", width=3, style="Small.TButton",
                                       command=lambda: self.zoom_by(1 / 1.25))
        self.zoom_out_btn.grid(row=0, column=3)
        ttk.Label(toolbar, textvariable=self.zoom_label, width=7, anchor="center",
                  foreground=C["accent"], font=(FONT, 9, "bold")).grid(row=0, column=4)
        self.zoom_in_btn = ttk.Button(toolbar, text="+", width=3, style="Small.TButton",
                                      command=lambda: self.zoom_by(1.25))
        self.zoom_in_btn.grid(row=0, column=5, padx=(0, 7))
        self.fit_btn = ttk.Button(toolbar, text="Ajustar", style="Small.TButton", command=self.fit)
        self.fit_btn.grid(row=0, column=6, padx=(0, 5))
        self.actual_btn = ttk.Button(toolbar, text="1:1", style="Small.TButton",
                                     command=lambda: self.set_zoom(1.0))
        self.actual_btn.grid(row=0, column=7)
        self.canvas = tk.Canvas(self, bg=C["matte"], height=dp(300), takefocus=True,
                                highlightthickness=1, highlightbackground=C["line"],
                                highlightcolor=C["accent"])
        self.canvas.grid(row=1, column=0, sticky="nsew")
        ttk.Label(self, textvariable=self.hint, style="WorkspaceMuted.TLabel",
                  wraplength=dp(760)).grid(row=2, column=0, sticky="ew", pady=(7, 0))
        self.canvas.bind("<Configure>", self._resize)
        for button in (1, 2, 3):
            self.canvas.bind(f"<ButtonPress-{button}>", self._press)
            self.canvas.bind(f"<B{button}-Motion>", self._motion)
            self.canvas.bind(f"<ButtonRelease-{button}>", self._release)
        self.canvas.bind("<Motion>", self._hover)
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<Double-Button-1>", lambda event: self.fit())
        self.canvas.bind("<KeyPress-space>", self._space_press)
        self.canvas.bind("<KeyRelease-space>", self._space_release)
        self.canvas.bind("<FocusOut>", self._release)
        self.canvas.bind("<Escape>", self._release)
        self.canvas.bind("<Return>", lambda event: self.on_add() if self.photo is None else self.fit())
        for key, dx, dy in (("Left", -1, 0), ("Right", 1, 0), ("Up", 0, -1), ("Down", 0, 1)):
            self.canvas.bind(f"<{key}>", lambda event, x=dx, y=dy: self._key_move(event, x, y))
        self.canvas.bind("<plus>", lambda event: self.zoom_by(1.25))
        self.canvas.bind("<equal>", lambda event: self.zoom_by(1.25))
        self.canvas.bind("<minus>", lambda event: self.zoom_by(1 / 1.25))
        self.canvas.bind("<Home>", lambda event: self.fit())
        self._controls()

    def has_photo(self, path):
        return self.photo is not None and self.photo.path == path and self.source is not None

    def set_photo(self, photo, image, settings, original=False):
        self.photo, self.source = photo, image
        self.settings, self.original = settings, original
        self.loading, self.error = False, None
        self.logo_cache_key = None
        self.fit()
        self._controls()

    def clear(self, loading=False, error=None):
        self.photo = self.source = None
        self.base_tk = self.logo_tk = None
        self.loading, self.error = loading, error
        self.drag_kind = None
        self.zoom_label.set("—")
        self.redraw()
        self._controls()

    def set_settings(self, settings, original=False):
        self.settings, self.original = settings, original
        if self.source is not None:
            self._draw_logo()
        self._controls()

    def set_locked(self, value):
        if self.locked != value:
            self.locked = value
            self.drag_kind = None
            self._draw_logo()
            self._controls()

    def _controls(self):
        ready = self.photo is not None and self.source is not None
        for control in (self.pan_btn, self.zoom_out_btn, self.zoom_in_btn, self.fit_btn, self.actual_btn):
            control.state(["!disabled"] if ready else ["disabled"])
        self.move_btn.state(["!disabled"] if ready and not self.locked and not self.original else ["disabled"])
        if not ready:
            self.hint.set("Adicione fotos para posicionar a marca diretamente na prévia.")
        elif self.original:
            self.hint.set("Original sem marca na prévia. Roda: zoom · arrastar: navegar · Ajustar: ver a foto inteira.")
        elif self.locked:
            self.hint.set("Exportação em andamento. Zoom e navegação continuam disponíveis.")
        elif self.tool.get() == "pan":
            self.hint.set("Arraste para navegar · roda: zoom · duplo clique ou Ajustar: ver a foto inteira.")
        else:
            self.hint.set("Arraste o logo para posicionar · roda: zoom · Espaço + arrastar: navegar · setas: mover o logo.")

    def _tool_changed(self):
        self._draw_logo()
        self._controls()
        self.canvas.focus_set()
        self.canvas.configure(cursor="fleur" if self.tool.get() == "pan" else "arrow")

    def _resize(self, event):
        old_w, old_h = self.viewport
        self.viewport = (event.width, event.height)
        if self.photo:
            if self.fitted:
                self._fit_geometry()
            else:
                self.center_x += (event.width - old_w) / 2
                self.center_y += (event.height - old_h) / 2
                self._constrain_pan()
        self._queue_draw()

    def _fit_geometry(self):
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        padding = self.dp(22)
        self.view_scale = max(0.01, min(8.0, (width - padding * 2) / self.photo.width,
                                       (height - padding * 2) / self.photo.height))
        self.center_x, self.center_y = width / 2, height / 2
        self._zoom_text()

    def fit(self):
        if self.photo is None:
            return
        self.fitted = True
        self._fit_geometry()
        self.redraw()

    def _zoom_text(self):
        percent = self.view_scale * 100
        self.zoom_label.set(f"{percent:.1f}%" if percent < 10 else f"{percent:.0f}%")

    def zoom_by(self, factor, anchor=None):
        self.set_zoom(self.view_scale * factor, anchor)

    def set_zoom(self, scale, anchor=None):
        if self.photo is None:
            return
        x, y = anchor or (self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2)
        new_scale = max(0.01, min(8.0, scale))
        ratio = new_scale / self.view_scale
        self.center_x = x + (self.center_x - x) * ratio
        self.center_y = y + (self.center_y - y) * ratio
        self.view_scale, self.fitted = new_scale, False
        self._constrain_pan()
        self._zoom_text()
        self._queue_draw()

    def _wheel(self, event):
        if self.photo:
            steps = wheel_steps(event.delta)
            self.zoom_by(1.14 ** steps, (event.x, event.y))
        return "break"

    def _constrain_pan(self):
        if self.photo is None:
            return
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        photo_w, photo_h = self.photo.width * self.view_scale, self.photo.height * self.view_scale
        padding = self.dp(22)
        if photo_w <= width - padding * 2:
            self.center_x = width / 2
        else:
            self.center_x = max(width - padding - photo_w / 2,
                                min(padding + photo_w / 2, self.center_x))
        if photo_h <= height - padding * 2:
            self.center_y = height / 2
        else:
            self.center_y = max(height - padding - photo_h / 2,
                                min(padding + photo_h / 2, self.center_y))

    def _photo_box(self):
        width, height = self.photo.width * self.view_scale, self.photo.height * self.view_scale
        return (self.center_x - width / 2, self.center_y - height / 2,
                self.center_x + width / 2, self.center_y + height / 2)

    def _logo_box(self):
        x, y, width, height = logo_geometry((self.photo.width, self.photo.height), self.settings, self.photo.logo)
        left, top, _, _ = self._photo_box()
        return (left + x * self.view_scale, top + y * self.view_scale,
                left + (x + width) * self.view_scale, top + (y + height) * self.view_scale)

    def _hit_logo(self, x, y):
        if self.photo is None or self.original or self.locked or self.tool.get() != "logo":
            return False
        left, top, right, bottom = self._logo_box()
        padding = self.dp(7)
        return left - padding <= x <= right + padding and top - padding <= y <= bottom + padding

    def _press(self, event):
        self.canvas.focus_set()
        if self.photo is None:
            if not self.loading and event.num == 1:
                self.on_add()
            return "break"
        secondary_click = IS_MAC and bool(event.state & 0x4)
        if event.num == 1 and not secondary_click and not self.space_down and self._hit_logo(event.x, event.y):
            self.drag_kind = "logo"
            left, top, right, bottom = self._logo_box()
            self.drag_offset = (event.x - (left + right) / 2, event.y - (top + bottom) / 2)
        else:
            self.drag_kind = "pan"
            self.drag_start = (event.x, event.y, self.center_x, self.center_y)
        self.canvas.configure(cursor="fleur")
        return "break"

    def _motion(self, event):
        if self.photo is None:
            return "break"
        if self.drag_kind == "logo" and not self.locked and not self.original:
            left, top, _, _ = self._photo_box()
            x = (event.x - self.drag_offset[0] - left) / self.view_scale / self.photo.width
            y = (event.y - self.drag_offset[1] - top) / self.view_scale / self.photo.height
            self._move_logo(x, y)
        elif self.drag_kind == "pan" and self.drag_start:
            x, y, center_x, center_y = self.drag_start
            self.center_x, self.center_y = center_x + event.x - x, center_y + event.y - y
            self.fitted = False
            self._constrain_pan()
            self._queue_draw()
        return "break"

    def _move_logo(self, x, y):
        _, _, width, height = logo_geometry((self.photo.width, self.photo.height), self.settings, self.photo.logo)
        x = max(width / self.photo.width / 2, min(1 - width / self.photo.width / 2, x))
        y = max(height / self.photo.height / 2, min(1 - height / self.photo.height / 2, y))
        self.on_move(x, y)

    def _release(self, event=None):
        self.drag_kind = self.drag_start = None
        self.space_down = False
        self.canvas.configure(cursor="fleur" if self.tool.get() == "pan" and self.photo else "arrow")
        return "break"

    def _hover(self, event):
        if self.drag_kind:
            return
        cursor = ("hand2" if self._hit_logo(event.x, event.y) else
                  "fleur" if self.photo and (self.tool.get() == "pan" or self.space_down) else
                  "hand2" if self.photo is None and not self.loading else "arrow")
        self.canvas.configure(cursor=cursor)

    def _space_press(self, event):
        self.space_down = True
        self.canvas.configure(cursor="fleur")
        return "break"

    def _space_release(self, event):
        self.space_down = False
        return "break"

    def _key_move(self, event, dx, dy):
        if self.photo is None:
            return "break"
        if self.tool.get() == "logo" and not self.locked and not self.original and not self.space_down:
            x, y, width, height = logo_geometry((self.photo.width, self.photo.height), self.settings, self.photo.logo)
            step = 10 if event.state & 0x1 else 1
            self._move_logo((x + width / 2 + dx * step) / self.photo.width,
                            (y + height / 2 + dy * step) / self.photo.height)
        else:
            step = self.dp(60 if event.state & 0x1 else 20)
            self.center_x -= dx * step
            self.center_y -= dy * step
            self.fitted = False
            self._constrain_pan()
            self._queue_draw()
        return "break"

    def _queue_draw(self):
        if self.draw_after is None:
            self.draw_after = self.after(16, self.redraw)

    def _background(self):
        size = (max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height()))
        if size != self.background_size:
            image = ImageOps.fit(background_image(), size, Image.Resampling.BICUBIC)
            image = ImageEnhance.Brightness(image).enhance(0.60)
            self.background_tk = ImageTk.PhotoImage(image)
            self.background_size = size
            self.canvas.delete("backdrop")
            self.canvas.create_image(0, 0, image=self.background_tk, anchor="nw", tags="backdrop")
            self.canvas.tag_lower("backdrop")

    def _visible_raster(self, source, box):
        """Rasteriza apenas o retângulo visível, mesmo com zoom de 800%."""
        left, top, right, bottom = box
        x0, y0 = math.ceil(max(1, left)), math.ceil(max(1, top))
        x1 = math.floor(min(self.canvas.winfo_width() - 1, right))
        y1 = math.floor(min(self.canvas.winfo_height() - 1, bottom))
        if x1 <= x0 or y1 <= y0:
            return None
        ratio_x, ratio_y = source.width / (right - left), source.height / (bottom - top)
        crop = ((x0 - left) * ratio_x, (y0 - top) * ratio_y,
                (x1 - left) * ratio_x, (y1 - top) * ratio_y)
        image = source.transform((x1 - x0, y1 - y0), Image.Transform.EXTENT, crop,
                                 resample=Image.Resampling.BICUBIC)
        return image, x0, y0

    def redraw(self):
        if self.draw_after is not None:
            self.after_cancel(self.draw_after)
            self.draw_after = None
        self._background()
        self.canvas.delete("base")
        self.canvas.delete("empty")
        if self.source is not None and self.photo is not None:
            raster = self._visible_raster(self.source, self._photo_box())
            if raster:
                image, x, y = raster
                self.base_tk = ImageTk.PhotoImage(image)
                self.canvas.create_image(x, y, image=self.base_tk, anchor="nw", tags="base")
        else:
            width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
            headline = "Carregando foto…" if self.loading else "Prévia indisponível" if self.error else "Sua foto, com a assinatura Well."
            detail = "Aguarde um instante." if self.loading else "Escolha outra foto ou consulte os detalhes." if self.error else "Adicione fotos para começar a editar."
            self.canvas.create_text(width / 2, height / 2 - self.dp(15), text=headline,
                                    font=(FONT, 17, "bold"), fill=C["ink"], tags="empty")
            self.canvas.create_text(width / 2, height / 2 + self.dp(25), text=detail,
                                    font=(FONT, 10), fill=C["muted"], tags="empty")
        self._draw_logo()

    def _draw_logo(self):
        self.canvas.delete("logo")
        if self.photo is None or self.source is None or self.original:
            return
        cache_key = (self.photo.logo, self.settings.opacity)
        if cache_key != self.logo_cache_key:
            self.logo_cache = load_logo(self.photo.logo).copy()
            opacity = max(0, min(100, self.settings.opacity)) / 100
            self.logo_cache.putalpha(self.logo_cache.getchannel("A").point(lambda value: round(value * opacity)))
            self.logo_cache_key = cache_key
        box = self._logo_box()
        raster = self._visible_raster(self.logo_cache, box)
        if raster:
            image, x, y = raster
            self.logo_tk = ImageTk.PhotoImage(image)
            self.canvas.create_image(x, y, image=self.logo_tk, anchor="nw", tags="logo")
            if self.tool.get() == "logo" and not self.locked:
                left, top, right, bottom = box
                self.canvas.create_rectangle(left - 3, top - 3, right + 3, bottom + 3,
                                              outline=C["accent"], width=1, dash=(4, 3), tags="logo")
                for px, py in ((left - 3, top - 3), (right + 3, top - 3),
                                (left - 3, bottom + 3), (right + 3, bottom + 3)):
                    self.canvas.create_rectangle(px - 2, py - 2, px + 2, py + 2,
                                                  fill=C["accent"], outline="", tags="logo")
