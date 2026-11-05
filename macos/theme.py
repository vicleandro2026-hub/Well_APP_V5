"""Tokens visuais da V5: carvão e ouro velho, com fonte nativa por plataforma."""

from platform_support import FONT_FAMILY

COLORS = {
    "background": "#121313",
    "surface": "#1C1D1C",
    "ink": "#EEE8DC",
    "muted": "#B4AFA4",
    "accent": "#B69A61",
    "accent_hover": "#CCB17B",
    "accent_soft": "#3C3323",
    "line": "#39392F",
    "hover": "#2B2C27",
    "selected": "#47402D",
    "matte": "#101211",
    "matte_text": "#EAE3D3",
    "matte_muted": "#BBB09B",
    "success": "#A3C7A2",
    "error": "#F09D8E",
    "disabled": "#2B2C29",
    "disabled_ink": "#8B8980",
    "on_accent": "#171812",
}

FONT = FONT_FAMILY


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
    style.configure("Primary.TButton", background=COLORS["accent"], foreground=COLORS["on_accent"],
                    font=(FONT, 10, "bold"), padding=(18, 12),
                    bordercolor=COLORS["accent"], lightcolor=COLORS["accent"],
                    darkcolor=COLORS["accent"], focuscolor=COLORS["on_accent"])
    style.map("Primary.TButton", background=[("disabled", COLORS["disabled"]),
              ("pressed", COLORS["accent_hover"]), ("active", COLORS["accent_hover"])],
              foreground=[("disabled", COLORS["disabled_ink"]), ("!disabled", COLORS["on_accent"])],
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

    style.configure("Mode.Toolbutton", background=COLORS["surface"], foreground=COLORS["muted"],
                    padding=(10, 7), font=(FONT, 9), borderwidth=1, relief="flat",
                    focuscolor=COLORS["accent"], focusthickness=1)
    style.map("Mode.Toolbutton", background=[("selected", COLORS["accent_soft"]),
              ("active", COLORS["hover"])], foreground=[("disabled", COLORS["disabled_ink"]),
              ("selected", COLORS["ink"])], bordercolor=[("selected", COLORS["accent"])])
    style.configure("TSpinbox", fieldbackground=COLORS["background"], foreground=COLORS["ink"],
                    background=COLORS["hover"], arrowcolor=COLORS["accent"], padding=(6, 6),
                    bordercolor=COLORS["line"], insertcolor=COLORS["ink"],
                    selectbackground=COLORS["selected"], selectforeground=COLORS["ink"])
    style.map("TSpinbox", bordercolor=[("focus", COLORS["accent"])],
              fieldbackground=[("disabled", COLORS["disabled"])])
