import flet as ft
import os
import time
from ..control.ui_styles import BORDER, PRIMARY, SECONDARY, WARNING, DANGER, elevated_button, glass_card, icon_button

def main(page: ft.Page, go_back_callback=None):
    # --- 1. CẤU HÌNH CỬA SỔ TỐI ƯU (RESPONSIVE) ---
    page.title = "Trang Quản Trị - Admin"
    
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
    
    # --- PHẦN TÀI NGUYÊN ---
    bg_image_src = r"src\GUI\data\image_user\backround.jpg"
    logo_src = r"src\GUI\data\image_laucher\Logo-removebg-preview.png"
    avatar_src = r"src\GUI\data\image_admin\avatar_super_admin.jpg"

    # ==============================================================================
    # --- KHU VỰC XỬ LÝ HÀNH ĐỘNG (ACTIONS) ---
    # ==============================================================================
    
    # 1. Hành động Quản Lý Hệ Thống
    def handle_system_click(e):
        try:
            from ..control import main_admin
            page.controls.clear()
            page.update()
            main_admin.main(page, go_back_callback)
        except Exception as ex:
            import traceback
            error_msg = f"Lỗi: {ex}\n{traceback.format_exc()}"
            print(error_msg)
            page.snack_bar = ft.SnackBar(ft.Text(f"Lỗi mở quản lý: {ex}"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()

    # 2. Hành động Cài Đặt - BottomSheet cuộn được
    def handle_settings_click(e):
        def close_sheet(e):
            bottom_sheet.open = False
            page.update()

        # BottomSheet có khả năng cuộn nếu nội dung dài
        bottom_sheet = ft.BottomSheet(
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Cài Đặt Hệ Thống", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Switch(label="Chế độ ban đêm (Dark Mode)", value=False),
                    ft.Switch(label="Thông báo âm thanh", value=True),
                    ft.Switch(label="Tự động sao lưu dữ liệu", value=True),
                    ft.Switch(label="Gửi email báo cáo", value=False),
                    ft.Divider(),
                    ft.ElevatedButton("Đóng", on_click=close_sheet, width=float("inf"))
                ], scroll=ft.ScrollMode.AUTO, tight=True),
            )
        )
        page.overlay.append(bottom_sheet)
        bottom_sheet.open = True
        page.update()
    
    # 3. Hành động Đăng xuất
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
                from . import login_admin
                page.controls.clear()
                page.update()
                login_admin.main(page, go_back_callback)
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Lỗi đăng xuất: {ex}"), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()

    # ==============================================================================

    def _animate_hover(e):
        e.control.scale = 1.02 if e.data == "true" else 1.0
        e.control.update()

    def create_action_button(text, subtitle, icon_name, kind, func_action):
        accent = PRIMARY if kind == "primary" else (WARNING if kind == "warning" else DANGER)
        return ft.Container(
            ink=True,
            on_click=func_action,
            animate_scale=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
            on_hover=_animate_hover,
            content=glass_card(
                width=380,
                padding=18,
                content=ft.Row([
                    ft.Container(
                        width=60,
                        height=60,
                        border_radius=20,
                        bgcolor=ft.Colors.with_opacity(0.16, accent),
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon_name, size=30, color=accent),
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
            blur=14,
            content=ft.Image(
                src=bg_image_src,
                width=float("inf"),
                height=float("inf"),
                fit=ft.ImageFit.COVER,
                error_content=ft.Container(bgcolor=ft.Colors.BLUE_GREY_900),
            ),
        ),
        ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.68, ft.Colors.BLACK))
    ])

    # --- 3. THẺ ADMIN ---
    admin_card = glass_card(
        width=430,
        padding=18,
        content=ft.Row([
            ft.Container(
                width=78, height=78,
                border_radius=39,
                border=ft.border.all(1.5, BORDER),
                content=ft.CircleAvatar(
                    foreground_image_src=avatar_src,
                    radius=37,
                    bgcolor=ft.Colors.GREY_300
                )
            ),
            ft.Container(width=14),
            ft.Column([
                ft.Text("Nguyen Ngoc Hieu", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=3),
                    bgcolor=SECONDARY,
                    border_radius=15,
                    content=ft.Text("Administrator", size=12, color="#06131B", weight=ft.FontWeight.BOLD)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6, expand=True)
        ])
    )

    btn_system = create_action_button("Quản lý hệ thống", "Tài xế, thống kê, dữ liệu và báo cáo", ft.Icons.DASHBOARD_CUSTOMIZE_ROUNDED, "primary", handle_system_click)
    btn_settings = create_action_button("Cài đặt nhanh", "Kiểm tra các công tắc cấu hình hệ thống", ft.Icons.SETTINGS_ROUNDED, "warning", handle_settings_click)

    # --- 5. FOOTER ---
    logout_btn = create_action_button("Đăng xuất", "Quay lại màn hình đăng nhập quản trị", ft.Icons.LOGOUT_ROUNDED, "danger", handle_logout)
    footer_text = ft.Text("© 2026 Admin System v1.0.0", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE54)

    launcher_panel = glass_card(
        width=560,
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
                    error_content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=ft.Colors.WHITE70, size=42),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=6),
            ft.Text("Trung tâm điều phối admin", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Launcher được đồng bộ với giao diện phiên admin và user: tối, kính mờ, thông tin rõ ràng.", size=13, color=ft.Colors.WHITE70),
            ft.Container(height=18),
            admin_card,
            ft.Container(height=18),
            btn_system,
            ft.Container(height=14),
            btn_settings,
            ft.Container(height=14),
            logout_btn,
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