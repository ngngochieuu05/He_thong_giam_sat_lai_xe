import flet as ft
import os
import time

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
    page.theme_mode = ft.ThemeMode.LIGHT
    
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

    # --- HÀM TẠO NÚT BẤM ---
    def create_custom_button(text, subtitle, icon_name, bg_color, func_action, border_color=ft.Colors.BLACK):
        return ft.Container(
            width=320,
            height=90,
            bgcolor=bg_color,
            border_radius=15,
            border=ft.border.all(1, border_color),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=4, color=ft.Colors.BLACK38, offset=ft.Offset(0, 4),
            ),
            content=ft.Row([
                ft.Container(
                    width=55, height=55,
                    border=ft.border.all(2, ft.Colors.BLACK),
                    border_radius=30,
                    alignment=ft.alignment.center,
                    content=ft.Icon(icon_name, size=30, color=ft.Colors.BLACK),
                ),
                ft.Container(width=15),
                ft.Column([
                    ft.Text(text, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                    ft.Text(subtitle, size=13, color=ft.Colors.BLACK54)
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=0)
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(left=20),
            ink=True,
            on_click=func_action
        )

    # --- 1. LỚP NỀN (BACKGROUND) - Tự động co giãn (Fit) ---
    background_layer = ft.Stack([
        ft.Image(
            src=bg_image_src,
            width=float("inf"),
            height=float("inf"),
            fit=ft.ImageFit.COVER,
            error_content=ft.Container(bgcolor=ft.Colors.BLUE_GREY_900),
        ),
        ft.Container(
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.50, ft.Colors.BLUE_GREY_900)
        )
    ])

    # --- 2. LOGO ---
    logo_layer = ft.Container(
        content=ft.Image(
            src=logo_src,
            width=80, height=80,
            fit=ft.ImageFit.CONTAIN,
            error_content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=ft.Colors.WHITE, size=60),
        ),
        top=10, right=10, padding=5
    )

    # --- 3. THẺ ADMIN ---
    admin_card = ft.Container(
        width=320, height=100,
        bgcolor="#CFD8DC",
        border=ft.border.all(1, ft.Colors.BLUE_GREY_200),
        border_radius=20,
        padding=15,
        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK26, offset=ft.Offset(0, 2)),
        content=ft.Row([
            ft.Container(
                width=70, height=70,
                border_radius=35,
                border=ft.border.all(2, ft.Colors.BLUE_GREY_700),
                content=ft.CircleAvatar(
                    foreground_image_src=avatar_src,
                    radius=33,
                    bgcolor=ft.Colors.GREY_300
                )
            ),
            ft.Container(width=10),
            ft.Column([
                ft.Text("Hieu", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=3),
                    bgcolor="#4a6fa5",
                    border_radius=15,
                    content=ft.Text("Super Admin", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)
        ])
    )

    # --- 4. CÁC NÚT CHỨC NĂNG ---
    btn_system = create_custom_button(
        "Quản Lý Hệ Thống", 
        "Tài xế, Thống kê, Báo cáo",
        ft.Icons.DASHBOARD_CUSTOMIZE, 
        "#4CAF50", 
        handle_system_click
    )
    btn_settings = create_custom_button(
        "Cài Đặt",
        "Cấu hình Camera & Hệ thống", 
        ft.Icons.SETTINGS, 
        "#D68936", 
        handle_settings_click
    )

    # --- 5. FOOTER ---
    logout_btn = ft.TextButton(
        "Đăng xuất",
        icon=ft.Icons.LOGOUT,
        icon_color=ft.Colors.RED_300,
        style=ft.ButtonStyle(color=ft.Colors.WHITE70),
        on_click=handle_logout
    )
    footer_text = ft.Text("© 2026 Admin System v1.0.0", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE54)

    # --- 6. BỐ CỤC CHÍNH (QUAN TRỌNG NHẤT) ---
    main_column = ft.Column(
        [
            ft.Container(height=60),
            admin_card,
            ft.Container(height=30),
            btn_system,
            ft.Container(height=15),
            btn_settings,
            ft.Container(height=40),
            logout_btn,
            footer_text,
            ft.Container(height=20),
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
    )

    # Ghép layout
    layout = ft.Stack(
        [
            background_layer,
            ft.Container(
                content=main_column, 
                alignment=ft.alignment.center,
                width=float("inf"),
            ),
            logo_layer,
        ],
        expand=True
    )

    page.add(layout)

if __name__ == "__main__":
    ft.app(target=main)