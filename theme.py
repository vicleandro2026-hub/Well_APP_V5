"""Tokens visuais da V4. A V3 permanece independente."""

COLORS = {
    "background": "#F3F4F1",
    "surface": "#FFFFFF",
    "ink": "#26342E",
    "muted": "#637069",
    "accent": "#89652A",
    "accent_hover": "#6F501E",
    "accent_soft": "#F1E9D9",
    "line": "#DEE3DC",
    "hover": "#EEF2ED",
    "selected": "#E5ECDD",
    "matte": "#26332E",
    "matte_text": "#E1E8DF",
    "matte_muted": "#B6C3B9",
    "success": "#326347",
    "error": "#A13737",
    "disabled": "#E5E8E2",
    "disabled_ink": "#747D75",
}

FONT = "Segoe UI"


def configure_styles(style):
    style.theme_use("clam")
    style.configure(".", font=(FONT, 10), background=COLORS["surface"],
                    foreground=COLORS["ink"], borderwidth=0)
    style.configure("TFrame", background=COLORS["surface"])
    style.configure("Workspace.TFrame", background=COLORS["background"])
    style.configure("TLabel", background=COLORS["surface"], foreground=COLORS["ink"])
    style.configure("Muted.TLabel", foreground=COLORS["muted"], font=(FONT, 9))
    style.configure("Title.TLabel", font=(FONT, 23, "bold"))
    style.configure("Section.TLabel", font=(FONT, 12, "bold"))
    style.configure("Workspace.TLabel", background=COLORS["background"])
    style.configure("WorkspaceTitle.TLabel", background=COLORS["background"],
                    font=(FONT, 14, "bold"))
    style.configure("WorkspaceMuted.TLabel", background=COLORS["background"],
                    foreground=COLORS["muted"], font=(FONT, 9))
    style.configure("TSeparator", background=COLORS["line"])
    style.configure("TButton", padding=(12, 9), background=COLORS["surface"],
                    foreground=COLORS["ink"], bordercolor=COLORS["line"],
                    lightcolor=COLORS["line"], darkcolor=COLORS["line"],
                    borderwidth=1, focusthickness=2, focuscolor=COLORS["accent"])
    style.map("TButton", background=[("disabled", COLORS["disabled"]),
              ("pressed", COLORS["selected"]), ("active", COLORS["hover"])],
              foreground=[("disabled", COLORS["disabled_ink"])],
              bordercolor=[("focus", COLORS["accent"])])
    style.configure("Primary.TButton", background=COLORS["accent"], foreground="white",
                    font=(FONT, 10, "bold"), padding=(18, 12),
                    bordercolor=COLORS["accent"], lightcolor=COLORS["accent"],
                    darkcolor=COLORS["accent"], focuscolor="white")
    style.map("Primary.TButton", background=[("disabled", COLORS["disabled"]),
              ("pressed", COLORS["accent_hover"]), ("active", COLORS["accent_hover"])],
              foreground=[("disabled", COLORS["disabled_ink"]), ("!disabled", "white")],
              bordercolor=[("disabled", COLORS["disabled"]),
                           ("!disabled", COLORS["accent"])])
    style.configure("Small.TButton", padding=(9, 5), font=(FONT, 9))
    style.configure("TEntry", padding=(9, 8), fieldbackground=COLORS["surface"],
                    bordercolor=COLORS["line"], lightcolor=COLORS["line"],
                    darkcolor=COLORS["line"], borderwidth=1,
                    insertcolor=COLORS["ink"], selectbackground=COLORS["selected"],
                    selectforeground=COLORS["ink"])
    style.map("TEntry", bordercolor=[("focus", COLORS["accent"])])
    style.configure("TCheckbutton", background=COLORS["background"], padding=(5, 5))
    style.map("TCheckbutton", background=[("active", COLORS["background"])])
    style.configure("Horizontal.TScale", background=COLORS["surface"],
                    troughcolor=COLORS["line"], sliderlength=20,
                    bordercolor=COLORS["surface"], lightcolor=COLORS["accent"],
                    darkcolor=COLORS["accent"])
    style.configure("Horizontal.TProgressbar", background=COLORS["accent"],
                    troughcolor=COLORS["hover"], borderwidth=0,
                    lightcolor=COLORS["accent"], darkcolor=COLORS["accent"])
    style.configure("Treeview", background=COLORS["surface"],
                    fieldbackground=COLORS["surface"], foreground=COLORS["ink"],
                    rowheight=30, borderwidth=0)
    style.map("Treeview", background=[("selected", COLORS["selected"])],
              foreground=[("selected", COLORS["ink"])])
    style.configure("Treeview.Heading", background=COLORS["hover"],
                    foreground=COLORS["muted"], font=(FONT, 9, "bold"),
                    padding=(8, 8), relief="flat")
    style.map("Treeview.Heading", background=[("active", COLORS["hover"])])
    style.configure("Vertical.TScrollbar", background=COLORS["line"],
                    troughcolor=COLORS["background"], arrowcolor=COLORS["muted"],
                    borderwidth=0, arrowsize=12)
    style.map("Vertical.TScrollbar", background=[("active", COLORS["muted"])])
