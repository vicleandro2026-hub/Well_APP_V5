"""Well Studio V4 — aplicativo independente para Windows."""

from concurrent.futures import ThreadPoolExecutor
import ctypes
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, ttk

from PIL import Image, ImageTk

from theme import COLORS as C, FONT, configure_styles
from watermark import (ASSETS, POSITIONS, POSITION_NAMES, Settings, export_photo,
                       inspect_photo, render_preview)


def photo_count(count):
    return f"{count} {'foto' if count == 1 else 'fotos'}"


class WellApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Well Studio · V4")
        self.root.configure(bg=C["background"])
        self.scale_factor = max(1.0, float(root.tk.call("tk", "scaling")) / (96 / 72))
        screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
        width = min(self.dp(1240), screen_w - 60)
        height = min(self.dp(850), screen_h - 90)
        root.geometry(f"{width}x{height}+{max(0, (screen_w-width)//2)}+{max(0, (screen_h-height)//2-20)}")
        root.minsize(min(self.dp(1000), screen_w - 40), min(self.dp(680), screen_h - 70))
        self.style = ttk.Style(root)
        configure_styles(self.style)
        self.style.configure("Treeview", rowheight=self.dp(29))
        self.root.option_add("*Font", (FONT, 10))

        self.photos = {}
        self.path_to_item = {}
        self.next_item = 0
        self.errors = []
        self.messages = queue.Queue()
        self.preview_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="WellPreview")
        self.pending_future = None
        self.cancel_event = threading.Event()
        self.closed = threading.Event()
        self.scanning = False
        self.exporting = False
        self.close_after_export = False
        self.preview_ticket = 0
        self.preview_after = None
        self.preview_pil = None
        self.preview_tk = None
        self.preview_loading = False
        self.last_export_dir = None
        self.setting_controls = []
        self.updating = False

        self.position = tk.StringVar(value="original")
        self.size = tk.DoubleVar(value=100)
        self.opacity = tk.DoubleVar(value=100)
        self.margin = tk.DoubleVar(value=4)
        self.destination = tk.StringVar()
        self.show_original = tk.BooleanVar(value=False)
        self.summary = tk.StringVar(value="Nenhuma foto adicionada.")
        self.status = tk.StringVar(value="Adicione suas fotos para começar.")
        self.preview_title = tk.StringVar(value="Prévia da foto")
        self.preview_subtitle = tk.StringVar(value="A marca acompanha o formato de cada imagem.")
        self.preview_counter = tk.StringVar(value="Nenhuma foto selecionada")
        self.position_caption = tk.StringVar(value="Selecionado: Padrão Well")

        with Image.open(ASSETS / "brand.png") as brand:
            icon = brand.convert("RGBA")
            self.app_icon = ImageTk.PhotoImage(icon)
            root.iconphoto(True, self.app_icon)
            icon.thumbnail((self.dp(48), self.dp(56)), Image.Resampling.LANCZOS)
            self.header_logo = ImageTk.PhotoImage(icon)
        self._build_header()
        self._build_body()
        self._build_footer()
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        self.destination.trace_add("write", lambda *_: self._refresh_controls())
        root.bind("<Control-o>", lambda event: self.add_photos())
        root.bind("<Control-Return>", lambda event: self.start_export())
        root.bind("<MouseWheel>", self._sidebar_wheel, add="+")
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._refresh_controls()
        root.after(80, self._poll)

    def dp(self, value):
        return max(1, round(value * self.scale_factor))

    def _build_header(self):
        header = ttk.Frame(self.root, padding=(self.dp(28), self.dp(17)))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, image=self.header_logo).grid(row=0, column=0, rowspan=2,
                                                     padx=(0, self.dp(18)))
        title = ttk.Frame(header)
        title.grid(row=0, column=1, sticky="w")
        ttk.Label(title, text="Well Studio", style="Title.TLabel").pack(side="left")
        tk.Label(title, text="V4", bg=C["accent_soft"], fg=C["accent"],
                 font=(FONT, 9, "bold"), padx=8, pady=4).pack(side="left", padx=12)
        ttk.Label(header, text="Marca d'água para fotos de imóveis", style="Muted.TLabel").grid(
            row=1, column=1, sticky="w", pady=(3, 0))
        header.grid_columnconfigure(2, weight=1)
        ttk.Label(header, text="Sua marca. Em cada foto.", foreground=C["accent"],
                  font=(FONT, 11)).grid(row=0, column=2, rowspan=2, sticky="e")

    def _build_body(self):
        body = ttk.Frame(self.root, style="Workspace.TFrame")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        sidebar_outer = ttk.Frame(body, width=self.dp(326))
        sidebar_outer.grid(row=0, column=0, sticky="ns")
        sidebar_outer.grid_propagate(False)
        sidebar_outer.grid_rowconfigure(0, weight=1)
        sidebar_outer.grid_columnconfigure(0, weight=1)
        self.sidebar_canvas = tk.Canvas(sidebar_outer, bg=C["surface"],
                                        highlightthickness=0, width=self.dp(310))
        sidebar_scroll = ttk.Scrollbar(sidebar_outer, orient="vertical", command=self.sidebar_canvas.yview)
        self.sidebar_canvas.configure(yscrollcommand=sidebar_scroll.set)
        self.sidebar_canvas.grid(row=0, column=0, sticky="nsew")
        sidebar_scroll.grid(row=0, column=1, sticky="ns")
        self.sidebar = ttk.Frame(self.sidebar_canvas, padding=(self.dp(22), self.dp(22)))
        self.sidebar_id = self.sidebar_canvas.create_window((0, 0), window=self.sidebar, anchor="nw")
        self.sidebar.bind("<Configure>", lambda event: self.sidebar_canvas.configure(
            scrollregion=self.sidebar_canvas.bbox("all")))
        self.sidebar_canvas.bind("<Configure>", lambda event: self.sidebar_canvas.itemconfigure(
            self.sidebar_id, width=event.width))
        self.sidebar.grid_columnconfigure(0, weight=1)
        self._build_settings()

        workspace = ttk.Frame(body, style="Workspace.TFrame",
                              padding=(self.dp(24), self.dp(20), self.dp(24), self.dp(16)))
        workspace.grid(row=0, column=1, sticky="nsew")
        workspace.grid_rowconfigure(1, weight=1)
        workspace.grid_columnconfigure(0, weight=1)
        preview_header = ttk.Frame(workspace, style="Workspace.TFrame")
        preview_header.grid(row=0, column=0, sticky="ew", pady=(0, self.dp(12)))
        preview_header.grid_columnconfigure(0, weight=1)
        ttk.Label(preview_header, textvariable=self.preview_title,
                  style="WorkspaceTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(preview_header, textvariable=self.preview_subtitle,
                  style="WorkspaceMuted.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.original_check = ttk.Checkbutton(preview_header, text="Ver original",
                                              variable=self.show_original, command=self.schedule_preview)
        self.original_check.grid(row=0, column=1, rowspan=2, padx=(10, 0))
        self.preview_canvas = tk.Canvas(workspace, bg=C["matte"], highlightthickness=0,
                                       takefocus=True, height=self.dp(300),
                                       highlightbackground=C["line"], highlightcolor=C["accent"])
        self.preview_canvas.grid(row=1, column=0, sticky="nsew")
        self.preview_canvas.bind("<Configure>", lambda event: self.schedule_preview())
        self.preview_canvas.bind("<Button-1>", lambda event: self.add_photos() if not self.photos else None)
        self.preview_canvas.bind("<Return>", lambda event: self.add_photos() if not self.photos else None)
        self.preview_canvas.bind("<Left>", lambda event: self.navigate(-1))
        self.preview_canvas.bind("<Right>", lambda event: self.navigate(1))
        navigation = ttk.Frame(workspace, style="Workspace.TFrame")
        navigation.grid(row=2, column=0, sticky="ew", pady=(self.dp(9), self.dp(13)))
        navigation.grid_columnconfigure(0, weight=1)
        ttk.Label(navigation, textvariable=self.preview_counter,
                  style="WorkspaceMuted.TLabel").grid(row=0, column=0, sticky="w")
        self.previous_btn = ttk.Button(navigation, text="Anterior", style="Small.TButton",
                                       command=lambda: self.navigate(-1))
        self.previous_btn.grid(row=0, column=1, padx=(0, 7))
        self.next_btn = ttk.Button(navigation, text="Próxima", style="Small.TButton",
                                   command=lambda: self.navigate(1))
        self.next_btn.grid(row=0, column=2)

        list_header = ttk.Frame(workspace, style="Workspace.TFrame")
        list_header.grid(row=3, column=0, sticky="ew", pady=(0, self.dp(8)))
        list_header.grid_columnconfigure(0, weight=1)
        ttk.Label(list_header, text="Fotos do lote", style="WorkspaceTitle.TLabel",
                  font=(FONT, 11, "bold")).grid(row=0, column=0, sticky="w")
        self.remove_btn = ttk.Button(list_header, text="Remover do lote", style="Small.TButton",
                                     command=self.remove_selected)
        self.remove_btn.grid(row=0, column=1, padx=(0, 7))
        self.clear_btn = ttk.Button(list_header, text="Limpar lote", style="Small.TButton", command=self.clear)
        self.clear_btn.grid(row=0, column=2)
        list_frame = ttk.Frame(workspace)
        list_frame.grid(row=4, column=0, sticky="ew")
        list_frame.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(list_frame, columns=("name", "format", "logo", "status"),
                                 show="headings", height=4, selectmode="extended")
        for key, label, width in (("name", "Arquivo", 240), ("format", "Formato", 95),
                                  ("logo", "Logo automático", 125), ("status", "Situação", 95)):
            self.tree.heading(key, text=label, anchor="w")
            self.tree.column(key, width=self.dp(width), minwidth=self.dp(70), stretch=key == "name")
        self.tree.grid(row=0, column=0, sticky="ew")
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=list_scroll.set)
        self.tree.tag_configure("error", foreground=C["error"])
        self.tree.tag_configure("exported", foreground=C["success"])
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)
        self.tree.bind("<Delete>", lambda event: self.remove_selected())
        self.tree.bind("<Control-a>", lambda event: self.tree.selection_set(self.tree.get_children()))

    def _build_settings(self):
        row = 0
        ttk.Label(self.sidebar, text="Preparar fotos", style="Section.TLabel").grid(
            row=row, column=0, sticky="w")
        row += 1
        self.add_btn = ttk.Button(self.sidebar, text="Adicionar fotos", command=self.add_photos)
        self.add_btn.grid(row=row, column=0, sticky="ew", pady=(self.dp(12), self.dp(8)))
        row += 1
        ttk.Label(self.sidebar, textvariable=self.summary, style="Muted.TLabel",
                  wraplength=self.dp(265)).grid(row=row, column=0, sticky="w")
        row += 1
        ttk.Separator(self.sidebar).grid(row=row, column=0, sticky="ew", pady=self.dp(17))
        row += 1
        ttk.Label(self.sidebar, text="Logo por orientação", style="Section.TLabel").grid(
            row=row, column=0, sticky="w")
        row += 1
        auto = ttk.Frame(self.sidebar)
        auto.grid(row=row, column=0, sticky="ew", pady=(self.dp(10), 0))
        for i, label in enumerate(("Foto vertical", "Foto horizontal")):
            item = ttk.Frame(auto)
            item.pack(fill="x", pady=3)
            ttk.Label(item, text=label, font=(FONT, 10)).pack(side="left")
            ttk.Label(item, text="Logo vertical" if i == 0 else "Logo horizontal",
                      foreground=C["success"], font=(FONT, 9, "bold")).pack(side="right")
        row += 1
        ttk.Label(self.sidebar, text="Seleção automática em cada foto.\nFotos quadradas usam o logo horizontal.",
                  style="Muted.TLabel", wraplength=self.dp(265)).grid(
            row=row, column=0, sticky="w", pady=(self.dp(7), 0))
        row += 1
        ttk.Separator(self.sidebar).grid(row=row, column=0, sticky="ew", pady=self.dp(17))
        row += 1
        ttk.Label(self.sidebar, text="Posição do logo", style="Section.TLabel").grid(
            row=row, column=0, sticky="w")
        row += 1
        original = self._position_button(self.sidebar, "Usar padrão Well", "original")
        original.grid(row=row, column=0, sticky="ew", pady=(self.dp(11), self.dp(7)))
        row += 1
        positions = ttk.Frame(self.sidebar)
        positions.grid(row=row, column=0, sticky="ew")
        for col in range(3):
            positions.grid_columnconfigure(col, weight=1, uniform="position")
        for index, (value, name) in enumerate(POSITIONS):
            self._position_button(positions, name, value).grid(
                row=index // 3, column=index % 3, sticky="ew", padx=2, pady=2)
        row += 1
        ttk.Label(self.sidebar, textvariable=self.position_caption, style="Muted.TLabel").grid(
            row=row, column=0, sticky="w", pady=(self.dp(8), self.dp(14)))
        row += 1
        for label, variable, minimum, maximum, suffix in (
            ("Tamanho do logo", self.size, 50, 250, "%"),
            ("Opacidade", self.opacity, 20, 100, "%"),
            ("Margem das bordas", self.margin, 0, 12, "%"),
        ):
            line = ttk.Frame(self.sidebar)
            line.grid(row=row, column=0, sticky="ew", pady=(self.dp(7), 0))
            line.grid_columnconfigure(0, weight=1)
            ttk.Label(line, text=label).grid(row=0, column=0, sticky="w")
            value_label = ttk.Label(line, text=f"{round(variable.get())}{suffix}", foreground=C["accent"],
                                    font=(FONT, 10, "bold"))
            value_label.grid(row=0, column=1, sticky="e")
            slider = ttk.Scale(self.sidebar, variable=variable, from_=minimum, to=maximum,
                               command=lambda value, var=variable, lab=value_label, unit=suffix:
                               self._slider_changed(var, lab, unit))
            row += 1
            slider.grid(row=row, column=0, sticky="ew", pady=(self.dp(3), self.dp(3)))
            self.setting_controls.append(slider)
            variable.trace_add("write", lambda *_, var=variable, lab=value_label, unit=suffix:
                               lab.configure(text=f"{round(var.get())}{unit}"))
            row += 1
        ttk.Label(self.sidebar, text="A margem vale para as nove posições.\n100% de tamanho preserva a proporção Well.",
                  style="Muted.TLabel", wraplength=self.dp(265)).grid(
            row=row, column=0, sticky="w", pady=(self.dp(6), self.dp(12)))
        row += 1
        reset = ttk.Button(self.sidebar, text="Restaurar padrão Well", style="Small.TButton", command=self.reset)
        reset.grid(row=row, column=0, sticky="ew")
        self.setting_controls.append(reset)

    def _position_button(self, parent, text, value):
        button = tk.Radiobutton(parent, text=text, value=value, variable=self.position,
                                indicatoron=False, command=self._settings_changed,
                                font=(FONT, 9), bg=C["surface"], fg=C["ink"],
                                selectcolor=C["accent_soft"], activebackground=C["hover"],
                                activeforeground=C["ink"], relief="flat", offrelief="flat",
                                overrelief="flat", borderwidth=0, padx=3, pady=self.dp(8),
                                highlightthickness=1, highlightbackground=C["line"],
                                highlightcolor=C["accent"], cursor="hand2", takefocus=True)
        self.setting_controls.append(button)
        return button

    def _build_footer(self):
        footer = ttk.Frame(self.root, padding=(self.dp(25), self.dp(14), self.dp(25), self.dp(12)))
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        destination_row = ttk.Frame(footer)
        destination_row.grid(row=0, column=0, sticky="ew")
        destination_row.grid_columnconfigure(1, weight=1)
        ttk.Label(destination_row, text="Salvar em", font=(FONT, 10, "bold")).grid(
            row=0, column=0, padx=(0, self.dp(12)))
        self.destination_entry = ttk.Entry(destination_row, textvariable=self.destination)
        self.destination_entry.grid(row=0, column=1, sticky="ew")
        self.browse_btn = ttk.Button(destination_row, text="Escolher pasta", command=self.choose_destination)
        self.browse_btn.grid(row=0, column=2, padx=(self.dp(9), 0))
        self.open_btn = ttk.Button(destination_row, text="Abrir pasta", command=self.open_destination)
        self.open_btn.grid(row=0, column=3, padx=(self.dp(8), 0))
        self.progress = ttk.Progressbar(footer, mode="determinate", maximum=100)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(self.dp(13), self.dp(12)))
        actions = ttk.Frame(footer)
        actions.grid(row=2, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        self.status_label = ttk.Label(actions, textvariable=self.status, foreground=C["muted"],
                                      font=(FONT, 9), wraplength=self.dp(500))
        self.status_label.grid(row=0, column=0, sticky="w", padx=(0, self.dp(10)))
        self.details_btn = ttk.Button(actions, text="Ver detalhes", style="Small.TButton", command=self.show_details)
        self.details_btn.grid(row=0, column=1, padx=(0, self.dp(8)))
        self.cancel_btn = ttk.Button(actions, text="Cancelar", command=self.cancel_export)
        self.cancel_btn.grid(row=0, column=2, padx=(0, self.dp(8)))
        self.export_btn = ttk.Button(actions, text="Exportar fotos", width=21,
                                     style="Primary.TButton", command=self.start_export)
        self.export_btn.grid(row=0, column=3)
        credit = ttk.Frame(self.root)
        credit.grid(row=3, column=0, sticky="ew")
        ttk.Label(credit, text="Desenvolvido por Victor Leandro | USBABC Conteúdo Criativo",
                  style="Muted.TLabel", font=(FONT, 8)).pack(pady=(0, self.dp(7)))

    def _sidebar_wheel(self, event):
        widget = event.widget
        while widget is not None:
            if widget == self.sidebar or widget == self.sidebar_canvas:
                if self.sidebar.winfo_height() > self.sidebar_canvas.winfo_height():
                    self.sidebar_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
                    return "break"
                break
            widget = getattr(widget, "master", None)

    def _settings(self):
        return Settings(self.position.get(), round(self.size.get()),
                        round(self.opacity.get()), round(self.margin.get()))

    def _slider_changed(self, variable, label, suffix):
        label.configure(text=f"{round(variable.get())}{suffix}")
        self._settings_changed()

    def _settings_changed(self):
        if self.updating:
            return
        self.position_caption.set(f"Selecionado: {POSITION_NAMES[self.position.get()]}")
        self.schedule_preview()

    def reset(self):
        if self.exporting:
            return
        self.updating = True
        self.position.set("original")
        self.size.set(100)
        self.opacity.set(100)
        self.margin.set(4)
        self.updating = False
        self._settings_changed()

    def _set_status(self, text, tone="muted"):
        self.status.set(text)
        self.status_label.configure(foreground=C[tone])

    def add_photos(self):
        if self.exporting or self.scanning:
            return
        files = filedialog.askopenfilenames(parent=self.root, title="Adicionar fotos ao lote",
            filetypes=[("Fotos", "*.jpg *.jpeg *.png *.webp"), ("Todos os arquivos", "*.*")])
        if not files:
            return
        paths = list(dict.fromkeys(str(Path(path).resolve()) for path in files))
        paths = [path for path in paths if os.path.normcase(path) not in self.path_to_item]
        if not paths:
            self._set_status("Essas fotos já estão no lote.")
            return
        self.scanning = True
        self._set_status(f"Identificando o formato de {photo_count(len(paths))}…")
        self._refresh_controls()
        threading.Thread(target=self._scan_worker, args=(paths,), daemon=True, name="WellImport").start()

    def _scan_worker(self, paths):
        added = 0
        for path in paths:
            if self.closed.is_set():
                return
            try:
                self.messages.put(("scan_photo", inspect_photo(path)))
                added += 1
            except Exception as error:
                self.messages.put(("scan_error", f"{Path(path).name}: {error}"))
        self.messages.put(("scan_done", added))

    def _insert_photo(self, photo):
        self.next_item += 1
        item = f"photo_{self.next_item}"
        self.photos[item] = photo
        self.path_to_item[os.path.normcase(photo.path)] = item
        self.tree.insert("", "end", iid=item, values=(Path(photo.path).name, photo.format_label,
                         f"Logo {photo.logo}", "Pronta"))
        if not self.tree.selection():
            self.tree.selection_set(item)
            self.tree.focus(item)
        if not self.destination.get().strip():
            self.destination.set(str(Path(photo.path).parent / "Well_exportadas"))

    def _selection_changed(self, event=None):
        self.preview_pil = None
        self._update_preview_labels()
        self.schedule_preview()
        self._refresh_controls()

    def _selected(self):
        selected = self.tree.selection()
        return next((key for key in selected if key in self.photos), None)

    def _update_preview_labels(self):
        key = self._selected()
        if key:
            photo = self.photos[key]
            name = Path(photo.path).name
            self.preview_title.set(name if len(name) <= 45 else name[:27] + "…" + name[-14:])
            self.preview_subtitle.set(f"{photo.format_label} · {photo.width} × {photo.height} px · Logo {photo.logo}")
            self.preview_counter.set(f"Foto {list(self.photos).index(key) + 1} de {len(self.photos)}")
        else:
            self.preview_title.set("Prévia da foto")
            self.preview_subtitle.set("A marca acompanha o formato de cada imagem.")
            self.preview_counter.set("Nenhuma foto selecionada")

    def navigate(self, delta):
        keys = list(self.photos)
        if not keys:
            return
        current = self._selected()
        index = keys.index(current) if current in keys else 0
        key = keys[max(0, min(len(keys) - 1, index + delta))]
        self.tree.selection_set(key)
        self.tree.focus(key)
        self.tree.see(key)

    def remove_selected(self):
        if self.exporting or self.scanning:
            return
        selected = list(self.tree.selection())
        for key in selected:
            photo = self.photos.pop(key, None)
            if photo:
                self.path_to_item.pop(os.path.normcase(photo.path), None)
                self.tree.delete(key)
        if self.photos and not self.tree.selection():
            self.tree.selection_set(next(iter(self.photos)))
        self.preview_pil = None
        self._refresh_summary()
        self._selection_changed()
        self._set_status("Fotos removidas do lote. Os arquivos originais foram preservados.")

    def clear(self):
        if self.exporting or self.scanning:
            return
        self.tree.delete(*self.tree.get_children())
        self.photos.clear()
        self.path_to_item.clear()
        self.preview_pil = None
        self.progress["value"] = 0
        self._refresh_summary()
        self._selection_changed()
        self._set_status("Lote vazio. Adicione novas fotos para continuar.")

    def _refresh_summary(self):
        if not self.photos:
            self.summary.set("Nenhuma foto adicionada.")
            return
        vertical = sum(photo.height > photo.width for photo in self.photos.values())
        horizontal = sum(photo.width > photo.height for photo in self.photos.values())
        square = len(self.photos) - vertical - horizontal
        parts = [photo_count(len(self.photos))]
        if vertical:
            parts.append(f"{vertical} {'vertical' if vertical == 1 else 'verticais'}")
        if horizontal:
            parts.append(f"{horizontal} {'horizontal' if horizontal == 1 else 'horizontais'}")
        if square:
            parts.append(f"{square} {'quadrada' if square == 1 else 'quadradas'}")
        self.summary.set(" · ".join(parts))

    def schedule_preview(self):
        if self.closed.is_set():
            return
        self.preview_ticket += 1
        if self.preview_after:
            self.root.after_cancel(self.preview_after)
        if self.pending_future:
            self.pending_future.cancel()
        self.preview_after = self.root.after(160, self._request_preview)

    def _request_preview(self):
        self.preview_after = None
        key = self._selected()
        if not key:
            self.preview_loading = False
            self.preview_pil = None
            self._paint_preview()
            return
        size = (max(100, self.preview_canvas.winfo_width() - self.dp(40)),
                max(100, self.preview_canvas.winfo_height() - self.dp(44)))
        self.preview_loading = True
        self._paint_preview()
        self.pending_future = self.preview_pool.submit(self._preview_worker, self.preview_ticket,
                               self.photos[key], self._settings(), size, self.show_original.get())

    def _preview_worker(self, ticket, photo, settings, size, original):
        try:
            image = render_preview(photo, settings, size, original)
            self.messages.put(("preview_ok", ticket, image))
        except Exception as error:
            self.messages.put(("preview_error", ticket, str(error)))

    def _paint_preview(self):
        canvas = self.preview_canvas
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if self.preview_pil is not None:
            image = self.preview_pil.copy()
            image.thumbnail((max(1, width - self.dp(40)), max(1, height - self.dp(44))),
                            Image.Resampling.LANCZOS)
            self.preview_tk = ImageTk.PhotoImage(image)
            canvas.create_image(width / 2, height / 2, image=self.preview_tk, anchor="center")
        elif self.photos:
            canvas.create_text(width / 2, height / 2, text="Carregando prévia…" if self.preview_loading
                               else "Selecione uma foto do lote.", fill=C["matte_text"], font=(FONT, 13))
        else:
            center = height / 2
            canvas.create_rectangle(width / 2 - self.dp(29), center - self.dp(66),
                                    width / 2 + self.dp(29), center - self.dp(21),
                                    outline=C["matte_muted"], width=2)
            canvas.create_line(width / 2 - self.dp(24), center - self.dp(27),
                               width / 2 - self.dp(8), center - self.dp(44),
                               width / 2 + self.dp(3), center - self.dp(33),
                               width / 2 + self.dp(14), center - self.dp(45),
                               width / 2 + self.dp(24), center - self.dp(28),
                               fill=C["matte_muted"], width=2)
            canvas.create_text(width / 2, center + self.dp(12), text="Prévia da foto",
                               fill=C["matte_text"], font=(FONT, 19, "bold"))
            canvas.create_text(width / 2, center + self.dp(47),
                               text="Adicione fotos para visualizar a marca d'água.",
                               fill=C["matte_muted"], font=(FONT, 10))
        if self.preview_loading and self.preview_pil is not None:
            canvas.create_text(width / 2, height - self.dp(12), text="Atualizando prévia…",
                               fill=C["matte_text"], font=(FONT, 9))
        canvas.configure(cursor="hand2" if not self.photos else "arrow")

    def choose_destination(self):
        if self.exporting:
            return
        current = self.destination.get().strip()
        initial = current if current and Path(current).is_dir() else str(Path.home())
        folder = filedialog.askdirectory(parent=self.root, title="Pasta para as fotos com marca d'água",
                                        initialdir=initial, mustexist=False)
        if folder:
            self.destination.set(folder)

    def open_destination(self):
        folder = self.last_export_dir or self.destination.get().strip()
        try:
            if not folder or not Path(folder).is_dir():
                raise FileNotFoundError("Escolha uma pasta existente ou exporte as fotos primeiro.")
            os.startfile(folder)
        except Exception as error:
            self._set_status(f"Não foi possível abrir a pasta. {error}", "error")

    def start_export(self):
        if self.exporting or self.scanning or not self.photos:
            return
        raw_destination = self.destination.get().strip()
        if not raw_destination:
            self._set_status("Escolha a pasta onde deseja salvar as fotos.", "error")
            self.destination_entry.focus_set()
            return
        destination = Path(raw_destination).expanduser()
        try:
            destination.mkdir(parents=True, exist_ok=True)
            if not destination.is_dir():
                raise NotADirectoryError(str(destination))
        except Exception as error:
            self._set_status(f"Não foi possível usar essa pasta. Escolha outra. {error}", "error")
            return
        self.exporting = True
        self.cancel_event.clear()
        self.progress.configure(maximum=len(self.photos), value=0)
        self._set_status("Preparando a exportação…")
        for item in self.photos:
            self.tree.set(item, "status", "Aguardando")
            self.tree.item(item, tags=())
        self._refresh_controls()
        threading.Thread(target=self._export_worker,
                         args=(list(self.photos.items()), str(destination), self._settings()),
                         daemon=True, name="WellExport").start()

    def _export_worker(self, items, destination, settings):
        completed, errors = 0, []
        for index, (key, photo) in enumerate(items, start=1):
            if self.cancel_event.is_set():
                break
            try:
                export_photo(photo, destination, settings)
                completed += 1
                self.messages.put(("export_progress", key, True, index, len(items)))
            except Exception as error:
                errors.append(f"{Path(photo.path).name}: {error}")
                self.messages.put(("export_progress", key, False, index, len(items)))
        self.messages.put(("export_done", completed, errors, self.cancel_event.is_set(), destination))

    def cancel_export(self):
        if self.exporting:
            self.cancel_event.set()
            self._set_status("Cancelando após a foto atual. As fotos já exportadas serão mantidas.")
            self.cancel_btn.state(["disabled"])

    def _refresh_controls(self):
        if not hasattr(self, "tree") or not hasattr(self, "export_btn"):
            return
        locked = self.exporting or self.scanning
        def enabled(control, value):
            control.state(["!disabled"] if value else ["disabled"])
        enabled(self.add_btn, not locked)
        enabled(self.remove_btn, bool(self.tree.selection()) and not locked)
        enabled(self.clear_btn, bool(self.photos) and not locked)
        enabled(self.export_btn, bool(self.photos) and bool(self.destination.get().strip()) and not locked)
        enabled(self.cancel_btn, self.exporting and not self.cancel_event.is_set())
        enabled(self.browse_btn, not self.exporting)
        enabled(self.destination_entry, not self.exporting)
        enabled(self.details_btn, bool(self.errors))
        enabled(self.original_check, bool(self.photos))
        folder = self.last_export_dir or self.destination.get().strip()
        enabled(self.open_btn, bool(folder) and Path(folder).is_dir())
        selected = self._selected()
        index = list(self.photos).index(selected) if selected in self.photos else 0
        enabled(self.previous_btn, bool(self.photos) and index > 0)
        enabled(self.next_btn, bool(self.photos) and index < len(self.photos) - 1)
        self.export_btn.configure(text="Exportando…" if self.exporting else
                                  f"Exportar {photo_count(len(self.photos))}" if self.photos else "Exportar fotos")
        for control in self.setting_controls:
            if isinstance(control, tk.Radiobutton):
                control.configure(state="disabled" if self.exporting else "normal",
                                  cursor="arrow" if self.exporting else "hand2")
            else:
                enabled(control, not self.exporting)

    def _poll(self):
        if self.closed.is_set():
            return
        for _ in range(80):
            try:
                message = self.messages.get_nowait()
            except queue.Empty:
                break
            kind, *data = message
            if kind == "scan_photo":
                self._insert_photo(data[0])
                self._refresh_summary()
            elif kind == "scan_error":
                self.errors.append(data[0])
            elif kind == "scan_done":
                self.scanning = False
                self._refresh_summary()
                self._update_preview_labels()
                self.schedule_preview()
                self._set_status(f"Lote pronto com {photo_count(data[0])}. Ajuste a posição e exporte."
                                 if data[0] else "Nenhuma foto pôde ser adicionada. Consulte os detalhes.",
                                 "muted" if data[0] else "error")
                self._refresh_controls()
            elif kind == "preview_ok":
                ticket, image = data
                if ticket == self.preview_ticket:
                    self.preview_pil = image
                    self.preview_loading = False
                    self._paint_preview()
            elif kind == "preview_error":
                ticket, error = data
                if ticket == self.preview_ticket:
                    self.preview_loading = False
                    self.preview_pil = None
                    self._paint_preview()
                    self.errors.append(f"Prévia: {error}")
                    self._set_status("Não foi possível mostrar esta foto. Consulte os detalhes ou escolha outra.", "error")
                    self._refresh_controls()
            elif kind == "export_progress":
                key, success, count, total = data
                self.tree.set(key, "status", "Exportada" if success else "Erro")
                self.tree.item(key, tags=("exported" if success else "error",))
                self.progress["value"] = count
                if not self.cancel_event.is_set():
                    self._set_status(f"Exportando {count} de {total} · {Path(self.photos[key].path).name}")
            elif kind == "export_done":
                completed, errors, cancelled, destination = data
                self.exporting = False
                self.errors.extend(errors)
                if completed:
                    self.last_export_dir = destination
                for key in self.photos:
                    if self.tree.set(key, "status") == "Aguardando":
                        self.tree.set(key, "status", "Não exportada")
                text = (f"Exportação cancelada. Fotos salvas: {completed}." if cancelled else
                        f"Exportação concluída: {photo_count(completed)}. Abra a pasta para ver o resultado.")
                if errors:
                    text += f" Falhas em {photo_count(len(errors))}; consulte os detalhes."
                self._set_status(text, "error" if errors else "muted" if cancelled else "success")
                self._refresh_controls()
                if self.close_after_export:
                    self._destroy()
                    return
        self.root.after(80, self._poll)

    def show_details(self):
        if not self.errors:
            return
        window = tk.Toplevel(self.root)
        window.title("Detalhes do processamento · Well V4")
        window.geometry(f"{self.dp(660)}x{self.dp(390)}")
        window.transient(self.root)
        window.configure(bg=C["surface"])
        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Arquivos que precisam de atenção", style="Section.TLabel").pack(anchor="w", pady=(0, 12))
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True)
        text = tk.Text(text_frame, wrap="word", relief="flat", bg=C["background"], fg=C["ink"],
                       padx=12, pady=12, font=(FONT, 10), highlightthickness=1,
                       highlightbackground=C["line"], highlightcolor=C["accent"])
        scroll = ttk.Scrollbar(text_frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        text.insert("1.0", "\n\n".join(self.errors))
        text.configure(state="disabled")
        close = ttk.Button(frame, text="Fechar", command=window.destroy)
        close.pack(anchor="e", pady=(12, 0))
        window.bind("<Escape>", lambda event: window.destroy())
        close.focus_set()

    def close(self):
        if self.exporting:
            self.close_after_export = True
            self.cancel_export()
        else:
            self._destroy()

    def _destroy(self):
        self.closed.set()
        self.cancel_event.set()
        self.preview_pool.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


def main():
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (OSError, AttributeError):
            pass
    root = tk.Tk()
    WellApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
