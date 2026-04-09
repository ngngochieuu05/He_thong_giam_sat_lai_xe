import flet as ft
import sys
import os
from src.GUI.user.login_laucher_user import login_user
from src.GUI.admin.login_laucher_admin import login_admin
# --- IMPORT FILE GIAO DIỆN USER & ADMIN ---
# Import từ thư mục GUI/user/ và GUI/admin/


def main(page: ft.Page):
    # --- 1. CẤU HÌNH CỬA SỔ TỐI ƯU ---
    page.title = "Cổng Đăng Nhập Hệ Thống"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK 
    page.padding = 0 
    
    page.window_width = 1280
    page.window_height = 800
    page.window_min_width = 1024
    page.window_min_height = 720
    page.window_resizable = True

    # --- 2. KHU VỰC ĐƯỜNG DẪN ẢNH (Thay thế tại đây) ---
    # Ảnh nền chính
    bg_path = r"src\GUI\data\image_user\backround.jpg" 
    # Logo và Icon
    logo_path = r"src\GUI\data\image_laucher\Logo-removebg-preview.png"
    admin_icon_path = r"src\GUI\data\image_admin\image_btnlogo_admin.png"
    driver_icon_path = r"src\GUI\data\image_laucher\image_btnlogo_user.png"

    def glass_card(content, width=None, height=None, padding=24):
        return ft.Container(
            width=width,
            height=height,
            padding=padding,
            bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.18, ft.Colors.WHITE)),
            border_radius=28,
            shadow=ft.BoxShadow(blur_radius=28, color=ft.Colors.BLACK45, offset=ft.Offset(0, 14)),
            content=content,
        )

    # --- HÀM CHUYỂN TRANG (MỚI THÊM) ---
    def go_to_user_page(e):
        print(">> Đang chuyển sang giao diện Tài xế...")
        try:
            # Xóa toàn bộ nội dung trang hiện tại
            page.controls.clear()
            page.update()
            # Gọi hàm main của login_user và truyền callback để quay lại
            login_user.main(page, go_back_callback=lambda: main(page)) 
        except Exception as ex:
            print(f"Lỗi khi chuyển trang: {ex}")
            # Hiển thị thông báo lỗi lên màn hình nếu không chuyển được
            page.snack_bar = ft.SnackBar(ft.Text(f"Không thể mở file User: {ex}"))
            page.snack_bar.open = True
            page.update()
    
    def go_to_admin_page(e):
        print(">> Đang chuyển sang giao diện Quản trị viên...")
        try:
            # Xóa toàn bộ nội dung trang hiện tại
            page.controls.clear()
            page.update()
            # Gọi hàm main của login_admin và truyền callback để quay lại
            login_admin.main(page, go_back_callback=lambda: main(page))
        except Exception as ex:
            print(f"Lỗi khi chuyển trang: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Không thể mở trang Admin: {ex}"))
            page.snack_bar.open = True
            page.update()

    # Hàm xử lý hiệu ứng hover
    def _animate_hover(e):
        e.control.scale = 1.05 if e.data == "true" else 1.0
        e.control.update()

    # --- 3. UI COMPONENTS ---

    logo = ft.Image(
        src=logo_path, width=88, height=88, fit=ft.ImageFit.CONTAIN,
        error_content=ft.Icon(ft.Icons.SHIELD, size=64, color=ft.Colors.WHITE54)
    )

    title = ft.Text("HỆ THỐNG GIÁM SÁT LÁI XE", size=34, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE)
    subtitle = ft.Text("Chọn vai trò để vào launcher đồng bộ cùng giao diện phiên hiện tại.", size=15, color=ft.Colors.WHITE70, text_align=ft.TextAlign.CENTER)

    def create_role_card(title_text, subtitle_text, image_src, fallback_icon, accent_color, on_click):
        return ft.Container(
            ink=True,
            on_click=on_click,
            animate_scale=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
            on_hover=_animate_hover,
            content=glass_card(
                width=290,
                height=240,
                padding=22,
                content=ft.Column([
                    ft.Container(
                        width=84,
                        height=84,
                        border_radius=24,
                        bgcolor=ft.Colors.with_opacity(0.16, accent_color),
                        alignment=ft.alignment.center,
                        content=ft.Image(
                            src=image_src,
                            width=64,
                            height=64,
                            fit=ft.ImageFit.CONTAIN,
                            error_content=ft.Icon(fallback_icon, size=56, color=accent_color),
                        ),
                    ),
                    ft.Container(height=12),
                    ft.Text(title_text, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(subtitle_text, size=13, color=ft.Colors.WHITE70, text_align=ft.TextAlign.CENTER),
                    ft.Container(expand=True),
                    ft.Container(
                        width=float("inf"),
                        height=52,
                        border_radius=16,
                        bgcolor=accent_color,
                        alignment=ft.alignment.center,
                        content=ft.Row([
                            ft.Text("Truy cập", size=15, weight=ft.FontWeight.BOLD, color="#06131B"),
                            ft.Icon(ft.Icons.ARROW_FORWARD, color="#06131B", size=20),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
        )

    admin_button = create_role_card("Quản trị viên", "Thiết lập hệ thống, thống kê và quản lý dữ liệu", admin_icon_path, ft.Icons.ADMIN_PANEL_SETTINGS, "#56CCF2", go_to_admin_page)
    driver_button = create_role_card("Tài xế", "Đăng nhập, bắt đầu phiên lái và dùng tiện ích", driver_icon_path, ft.Icons.DIRECTIONS_CAR, "#63D471", go_to_user_page)

    footer = ft.Container(
        content=ft.Text("© 2026 Driver v1.0.0", size=12, color=ft.Colors.WHITE38),
        padding=ft.padding.only(bottom=20)
    )

    # --- 4. BỐ CỤC CHÍNH ---
    main_content = glass_card(
        width=760,
        padding=30,
        content=ft.Column(
            [
                logo,
                title,
                subtitle,
                ft.Container(height=28),
                ft.Row([admin_button, driver_button], spacing=24, alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                ft.Container(height=10),
                footer,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
    )

    # --- 5. LỚP NỀN ---
    background_layer = ft.Stack([
        ft.Container(
            expand=True,
            blur=14,
            content=ft.Image(src=bg_path, width=float("inf"), height=float("inf"), fit=ft.ImageFit.COVER, 
                     error_content=ft.Container(bgcolor=ft.Colors.BLUE_GREY_900)),
        ),
        ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.62, ft.Colors.BLACK))
    ])

    # --- 6. GHÉP ---
    layout = ft.Stack([
        background_layer,
        ft.Container(content=main_content, alignment=ft.alignment.center, padding=24)
    ], expand=True)

    page.add(layout)

if __name__ == "__main__":
    ft.app(target=main, assets_dir=".")