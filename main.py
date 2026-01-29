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
    bg_path = r"D:\TestGUI\src\GUI\data\image_user\backround.jpg" 
    # Logo và Icon
    logo_path = r"D:\TestGUI\src\GUI\data\image_laucher\Logo-removebg-preview.png"
    admin_icon_path = r"D:\TestGUI\src\GUI\data\image_admin\image_btnlogo_admin.png"
    driver_icon_path = r"D:\TestGUI\src\GUI\data\image_laucher\image_btnlogo_user.png"

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
        src=logo_path, width=180, height=180, fit=ft.ImageFit.CONTAIN,
        error_content=ft.Icon(ft.Icons.SHIELD, size=80, color=ft.Colors.WHITE54)
    )

    title = ft.Text("HỆ THỐNG GIÁM SÁT LÁI XE", size=36, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    subtitle = ft.Text("An toàn trên mọi nẻo đường", size=18, color=ft.Colors.WHITE70, italic=True)

    # --- NÚT ADMIN ---
    admin_button = ft.Container(
        content=ft.Column(
            [
                ft.Image(src=admin_icon_path, width=90, height=90, fit=ft.ImageFit.CONTAIN,
                         error_content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=70, color=ft.Colors.WHITE)),
                ft.Container(height=15),
                ft.Text("QUẢN TRỊ VIÊN", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("Thiết lập & Báo cáo", size=13, color=ft.Colors.WHITE70)
            ],
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        width=280, height=260,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
            colors=["#4a6fa5", "#375a8c"]
        ),
        border_radius=25, padding=20, ink=True,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK54, offset=ft.Offset(0, 8)),
        on_click=go_to_admin_page,
        animate_scale=ft.Animation(100, ft.AnimationCurve.EASE_OUT),
        on_hover=lambda e: _animate_hover(e)
    )

    # --- NÚT TÀI XẾ (ĐÃ SỬA ON_CLICK) ---
    driver_button = ft.Container(
        content=ft.Column(
            [
                ft.Image(src=driver_icon_path, width=90, height=90, fit=ft.ImageFit.CONTAIN,
                         error_content=ft.Icon(ft.Icons.DIRECTIONS_CAR, size=70, color=ft.Colors.WHITE)),
                ft.Container(height=15),
                ft.Text("TÀI XẾ", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("Giám sát hành trình", size=13, color=ft.Colors.WHITE70)
            ],
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        width=280, height=260,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
            colors=["#2e7d6a", "#205c4d"]
        ),
        border_radius=25, padding=20, ink=True,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK54, offset=ft.Offset(0, 8)),
        
        # --- THAY ĐỔI Ở ĐÂY: GỌI HÀM CHUYỂN TRANG ---
        on_click=go_to_user_page, 
        
        animate_scale=ft.Animation(100, ft.AnimationCurve.EASE_OUT),
        on_hover=lambda e: _animate_hover(e)
    )

    footer = ft.Container(
        content=ft.Text("© 2026 Driver v1.0.0", size=12, color=ft.Colors.WHITE38),
        padding=ft.padding.only(bottom=20)
    )

    # --- 4. BỐ CỤC CHÍNH ---
    main_content = ft.Column(
        [
            ft.Container(height=40),
            logo, title, subtitle,
            ft.Container(height=40),
            ft.Row([admin_button, driver_button], spacing=50, alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            ft.Container(expand=True),
            footer
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.HIDDEN
    )

    # --- 5. LỚP NỀN ---
    background_layer = ft.Stack([
        ft.Image(src=bg_path, width=float("inf"), height=float("inf"), fit=ft.ImageFit.COVER, 
                 error_content=ft.Container(bgcolor=ft.Colors.BLUE_GREY_900)),
        ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.50, ft.Colors.BLACK))
    ])

    # --- 6. GHÉP ---
    layout = ft.Stack([
        background_layer,
        ft.Container(content=main_content, alignment=ft.alignment.center, padding=20)
    ], expand=True)

    page.add(layout)

if __name__ == "__main__":
    ft.app(target=main, assets_dir=".")