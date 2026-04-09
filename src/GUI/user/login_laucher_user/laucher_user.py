import flet as ft
import os
import time
from pathlib import Path
from ..control.ui_styles import BORDER, PRIMARY, SECONDARY, DANGER, icon_button

try:
    from src.DAL.accounts_sync import get_driver_account_from_db
except Exception:
    get_driver_account_from_db = None

PROJECT_ROOT = Path(__file__).resolve().parents[4]

def main(page: ft.Page, go_back_callback=None, user_account=None):
    # --- 1. CẤU HÌNH CỬA SỔ TỐI ƯU (RESPONSIVE) ---
    page.title = "Trang Chủ"
    
    # Kích thước mặc định
    page.window_width = 1280
    page.window_height = 800
    
    # Thiết lập kích thước tối thiểu để không bị vỡ giao diện khi thu nhỏ
    page.window_min_width = 400
    page.window_min_height = 600
    
    page.window_resizable = True
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    
    # Căn giữa nội dung theo chiều ngang khi phóng to
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    if user_account and user_account.get("username") and get_driver_account_from_db:
        try:
            db_user = get_driver_account_from_db(user_account.get("username"))
            if db_user:
                user_account = {**user_account, **db_user}
        except Exception:
            pass

    def resolve_avatar_src(avatar_path):
        if not avatar_path:
            return "https://avatars.githubusercontent.com/u/1?v=4"
        avatar_value = str(avatar_path).strip()
        if avatar_value.startswith(("http://", "https://")):
            return avatar_value

        avatar_file = Path(avatar_value)
        if not avatar_file.is_absolute():
            avatar_file = (PROJECT_ROOT / avatar_file).resolve()
        else:
            avatar_file = avatar_file.resolve()

        if avatar_file.exists():
            try:
                return str(avatar_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
            except ValueError:
                return str(avatar_file).replace("\\", "/")

        return avatar_value.replace("\\", "/")
    
    # --- PHẦN TÀI NGUYÊN ---
    bg_image_src = r"src\GUI\data\image_user\backround.jpg"
    logo_src = r"src\GUI\data\image_user\Logo-removebg-preview.png"
    avatar_src = resolve_avatar_src(user_account.get("avatar") if user_account else None)

    # ==============================================================================
    # --- KHU VỰC XỬ LÝ HÀNH ĐỘNG (ACTIONS) ---
    # ==============================================================================
    
    # 1. Hành động Bắt Đầu - Chuyển sang main_user
    def handle_start_click(e):
        page.open(ft.SnackBar(ft.Text("Đang khởi động phiên lái..."), bgcolor=ft.Colors.GREEN_700))
        page.update()
        
        time.sleep(0.5)
        
        try:
            # Xóa nội dung trang hiện tại
            page.controls.clear()
            page.update()
            
            # Import và chuyển sang main_user với callback để quay lại
            from ..control import main_user
            app = main_user.UserApp(
                page, 
                go_back_callback=lambda: main(page, go_back_callback, user_account),
                user_account=user_account
            )
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Lỗi khởi động: {ex}"), bgcolor=ft.Colors.RED_600))
            page.update()
    
    # 2. Hành động Đăng xuất
    def handle_logout(e):
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Đang đăng xuất...", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700
        )
        page.snack_bar.open = True
        page.update()
        
        time.sleep(0.5)
        
        if go_back_callback:
            page.controls.clear()
            page.update()
            go_back_callback()
        else:
            try:
                from . import login_user
                page.controls.clear()
                page.update()
                login_user.main(page, go_back_callback)
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Lỗi đăng xuất: {ex}"), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()

    # ==============================================================================

    def _animate_hover(e):
        e.control.scale = 1.02 if e.data == "true" else 1.0
        e.control.update()

    def glass_card(content, width=None, height=None, padding=24):
        return ft.Container(
            width=width,
            height=height,
            padding=padding,
            bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
            border=ft.border.all(1, BORDER),
            border_radius=28,
            shadow=ft.BoxShadow(blur_radius=28, color=ft.Colors.BLACK45, offset=ft.Offset(0, 14)),
            content=content,
        )

    def create_action_button(text, subtitle, icon_name, kind, on_click):
        accent = PRIMARY if kind == "primary" else (SECONDARY if kind == "secondary" else DANGER)
        return ft.Container(
            ink=True,
            on_click=on_click,
            animate_scale=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
            on_hover=_animate_hover,
            content=glass_card(
                width=360,
                padding=18,
                content=ft.Row([
                    ft.Container(
                        width=60,
                        height=60,
                        border_radius=20,
                        bgcolor=ft.Colors.with_opacity(0.18, accent),
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon_name, color=accent, size=30),
                    ),
                    ft.Container(width=16),
                    ft.Column([
                        ft.Text(text, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(subtitle, size=12, color=ft.Colors.WHITE70),
                    ], spacing=4, expand=True),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=14, vertical=10),
                        border_radius=16,
                        bgcolor=accent,
                        content=ft.Row([
                            ft.Text("Mở", size=13, weight=ft.FontWeight.BOLD, color="#06131B"),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color="#06131B"),
                        ], spacing=6),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ),
        )

    # --- 1. LỚP NỀN (BACKGROUND) - Tự động co giãn (Fit) ---
    background_layer = ft.Stack([
        ft.Container(
            expand=True,
            blur=12,
            content=ft.Image(
                src=bg_image_src,
                width=float("inf"),
                height=float("inf"),
                fit=ft.ImageFit.COVER,
                error_content=ft.Text("Lỗi: Không tìm thấy ảnh nền", color=ft.Colors.RED),
            ),
        ),
        ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.62, ft.Colors.BLACK))
    ])

    # --- 2. LOGO ---
    user_name = user_account.get('name', 'Guest User') if user_account else 'Guest User'
    user_driver_id = user_account.get('driver_id', 'N/A') if user_account else 'N/A'
    user_plan = user_account.get('plan', 'Normal') if user_account else 'Normal'
    
    plan_color = ft.Colors.ORANGE_400 if user_plan.lower() == "pro" else ft.Colors.GREY_400

    user_card = glass_card(
        width=420,
        padding=18,
        content=ft.Row([
            ft.Container(
                width=78, height=78,
                border_radius=39,
                border=ft.border.all(1.5, BORDER),
                content=ft.CircleAvatar(
                    content=ft.Image(src=avatar_src, fit=ft.ImageFit.COVER, width=74, height=74),
                    radius=37,
                    bgcolor=ft.Colors.GREY_300
                )
            ),
            ft.Container(width=14),
            ft.Column([
                ft.Text(user_name, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text(f"Mã tài xế: {user_driver_id}", size=13, color=ft.Colors.WHITE70),
                ft.Container(
                    content=ft.Text(f"Gói: {user_plan.upper()}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=plan_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    border_radius=10,
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6, expand=True)
        ])
    )

    btn_start = create_action_button("Bắt đầu phiên lái", "Khởi động dashboard và camera giám sát", ft.Icons.PLAY_ARROW_ROUNDED, "primary", handle_start_click)
    btn_logout = create_action_button("Đăng xuất", "Quay lại màn hình đăng nhập tài xế", ft.Icons.LOGOUT_ROUNDED, "danger", handle_logout)

    footer_text = ft.Text("© 2026 Driver v1.0.0", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE54)

    launcher_panel = glass_card(
        width=520,
        padding=28,
        content=ft.Column([
            ft.Row([
                icon_button(ft.Icons.ARROW_BACK, on_click=lambda e: handle_logout(e), kind="surface", tooltip="Quay lại"),
                ft.Container(expand=True),
                ft.Image(
                    src=logo_src,
                    width=58,
                    height=58,
                    fit=ft.ImageFit.CONTAIN,
                    error_content=ft.Icon(ft.Icons.DIRECTIONS_CAR, color=ft.Colors.WHITE70, size=40),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=6),
            ft.Text("Trung tâm phiên lái", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Khởi động nhanh vào trải nghiệm tài xế với cùng phong cách giao diện hiện tại.", size=13, color=ft.Colors.WHITE70),
            ft.Container(height=18),
            user_card,
            ft.Container(height=18),
            btn_start,
            ft.Container(height=14),
            btn_logout,
            ft.Container(height=10),
            ft.Container(content=footer_text, alignment=ft.alignment.center_right),
        ], scroll=ft.ScrollMode.AUTO),
    )

    layout = ft.Stack(
        [
            background_layer,
            ft.Container(
                content=launcher_panel, 
                alignment=ft.alignment.center,
                width=float("inf"),
                padding=24,
            ),
        ],
        expand=True
    )

    page.add(layout)

if __name__ == "__main__":
    ft.app(target=main)