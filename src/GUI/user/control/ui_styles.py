import flet as ft


PRIMARY = "#4CAF50"
SECONDARY = "#56CCF2"
WARNING = "#F2C94C"
DANGER = "#FF7A7A"
SURFACE = ft.Colors.with_opacity(0.14, ft.Colors.WHITE)
SURFACE_STRONG = ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
BORDER = ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
TEXT_PRIMARY = ft.Colors.WHITE
TEXT_DARK = "#06131B"


def _palette(kind: str):
    palettes = {
        "primary": (PRIMARY, TEXT_DARK),
        "secondary": (SECONDARY, TEXT_DARK),
        "warning": (WARNING, TEXT_DARK),
        "danger": (DANGER, TEXT_DARK),
        "surface": (SURFACE_STRONG, TEXT_PRIMARY),
        "ghost": (ft.Colors.TRANSPARENT, TEXT_PRIMARY),
    }
    return palettes.get(kind, palettes["primary"])


def button_style(kind: str = "primary", radius: int = 14, compact: bool = False):
    bgcolor, color = _palette(kind)
    return ft.ButtonStyle(
        bgcolor=bgcolor,
        color=color,
        padding=ft.padding.symmetric(horizontal=16 if compact else 20, vertical=10 if compact else 14),
        shape=ft.RoundedRectangleBorder(radius=radius),
        side=ft.BorderSide(1, BORDER if kind in {"surface", "ghost"} else bgcolor),
        text_style=ft.TextStyle(size=13 if compact else 14, weight=ft.FontWeight.W_700),
    )


def elevated_button(text: str = "", on_click=None, icon=None, kind: str = "primary", width=None, height: int = 48, disabled: bool = False, content=None):
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        content=content,
        on_click=on_click,
        width=width,
        height=height,
        disabled=disabled,
        style=button_style(kind),
    )


def text_button(text: str = "", on_click=None, icon=None, content=None, kind: str = "ghost"):
    return ft.TextButton(
        text=text,
        icon=icon,
        content=content,
        on_click=on_click,
        style=button_style(kind, radius=999, compact=True),
    )


def icon_button(icon, on_click=None, kind: str = "surface", icon_color=None, icon_size: int = 20, tooltip: str | None = None):
    bgcolor, default_icon_color = _palette(kind)
    return ft.IconButton(
        icon=icon,
        on_click=on_click,
        tooltip=tooltip,
        icon_color=icon_color or default_icon_color,
        icon_size=icon_size,
        style=ft.ButtonStyle(
            bgcolor=bgcolor,
            shape=ft.RoundedRectangleBorder(radius=999),
            side=ft.BorderSide(1, BORDER if kind in {"surface", "ghost"} else bgcolor),
            padding=ft.padding.all(10),
        ),
    )