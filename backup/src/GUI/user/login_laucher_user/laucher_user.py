import flet as ft
import os
import time

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
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Căn giữa nội dung theo chiều ngang khi phóng to
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # --- PHẦN TÀI NGUYÊN ---
    bg_image_src = r"src\GUI\data\image_user\backround.jpg"
    logo_src = r"src\GUI\data\image_user\Logo-removebg-preview.png"
    avatar_src = "https://avatars.githubusercontent.com/u/1?v=4" 

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

    # 2. Hành động Lịch Sử
    def handle_history_click(e):
        page.show_snack_bar(
            ft.SnackBar(content=ft.Text("Đang tải dữ liệu..."), action="OK")
        )

    # 3. Hành động Cài Đặt - BottomSheet cuộn được
    def handle_settings_click(e):
        def close_sheet(e):
            bottom_sheet.open = False
            page.update()

        # BottomSheet có khả năng cuộn nếu nội dung dài
        bottom_sheet = ft.BottomSheet(
            ft.Container(
                padding=20,
                # Cho phép cuộn nếu màn hình quá thấp
                content=ft.Column([
                    ft.Text("Cài Đặt Nhanh", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Switch(label="Chế độ ban đêm (Dark Mode)", value=False),
                    ft.Switch(label="Thông báo âm thanh", value=True),
                    ft.Switch(label="Tự động ghi hình", value=True),
                    ft.Switch(label="Cảnh báo rung", value=False),
                    ft.Divider(),
                    ft.ElevatedButton("Đóng", on_click=close_sheet, width=float("inf"))
                ], scroll=ft.ScrollMode.AUTO, tight=True), # tight=True để ôm sát nội dung
            )
        )
        page.overlay.append(bottom_sheet)
        bottom_sheet.open = True
        page.update()
    
    # 4. Hành động Đăng xuất
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

    # --- HÀM TẠO NÚT BẤM ---
    def create_custom_button(text, icon_name, bg_color, func_action, border_color=ft.Colors.BLACK):
        return ft.Container(
            width=320,
            height=80,
            bgcolor=bg_color,
            border_radius=15,
            border=ft.border.all(1, border_color),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=4, color=ft.Colors.BLACK38, offset=ft.Offset(0, 4),
            ),
            content=ft.Row([
                ft.Container(
                    width=50, height=50,
                    border=ft.border.all(2, ft.Colors.BLACK),
                    border_radius=25,
                    alignment=ft.alignment.center,
                    content=ft.Icon(icon_name, size=30, color=ft.Colors.BLACK),
                ),
                ft.Container(width=10),
                ft.Text(text, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
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
            fit=ft.ImageFit.COVER, # Ảnh luôn phủ kín màn hình dù resize
            error_content=ft.Text("Lỗi: Không tìm thấy ảnh nền", color=ft.Colors.RED),
        ),
        ft.Container(
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.50, ft.Colors.BLACK)
        )
    ])

    # --- 2. LOGO ---
    logo_layer = ft.Container(
        content=ft.Image(
            src=logo_src,
            width=80, height=80,
            fit=ft.ImageFit.CONTAIN,
            error_content=ft.Icon(ft.Icons.BROKEN_IMAGE, color=ft.Colors.RED),
        ),
        top=10, right=10, padding=5
    )

    # --- 3. THẺ NGƯỜI DÙNG ---
    # Lấy thông tin user từ parameter hoặc dùng default
    user_name = user_account.get('name', 'Guest User') if user_account else 'Guest User'
    user_driver_id = user_account.get('driver_id', 'N/A') if user_account else 'N/A'
    user_plan = user_account.get('plan', 'Normal') if user_account else 'Normal'
    
    # Màu sắc badge dựa theo plan
    plan_color = ft.Colors.ORANGE_400 if user_plan == "Pro" else ft.Colors.GREY_400
    
    user_card = ft.Container(
        width=320, height=120, # Tăng chiều cao để chứa thêm badge
        bgcolor="#D1E2D3",
        border=ft.border.all(1, ft.Colors.BLACK),
        border_radius=20,
        padding=15,
        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK26, offset=ft.Offset(0, 2)),
        content=ft.Row([
            ft.Container(
                width=70, height=70,
                border_radius=35,
                border=ft.border.all(2, ft.Colors.BLACK),
                content=ft.CircleAvatar(
                    foreground_image_src=avatar_src,
                    radius=33,
                    bgcolor=ft.Colors.GREY_300
                )
            ),
            ft.Container(width=10),
            ft.Column([
                ft.Text(user_name, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ft.Text(f"ID : {user_driver_id}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ft.Container(
                    content=ft.Text(f"Gói: {user_plan}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=plan_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    border_radius=10,
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)
        ])
    )

    # --- 4. CÁC NÚT CHỨC NĂNG ---
    btn_start = create_custom_button("Bắt Đầu Phiên Lái", ft.Icons.PLAY_ARROW, "#4CAF50", handle_start_click)
    btn_history = create_custom_button("Lịch Sử Phiên Lái", ft.Icons.HISTORY, "#2196F3", handle_history_click)
    btn_settings = create_custom_button("Cài Đặt", ft.Icons.SETTINGS, "#D68936", handle_settings_click)

    # --- 5. FOOTER ---
    footer_text = ft.Text("© 2026 Driver v1.0.0", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)

    # --- 6. BỐ CỤC CHÍNH (QUAN TRỌNG NHẤT) ---
    # Sử dụng ListView hoặc Column có scroll để tránh bị che khi thu nhỏ
    main_column = ft.Column(
        [
            ft.Container(height=60),
            user_card,
            ft.Container(height=30),
            btn_start,
            ft.Container(height=15),
            btn_history,
            ft.Container(height=15),
            btn_settings,
            ft.Container(height=40), # Spacer thay vì expand=True để scroll hoạt động tốt hơn
            ft.TextButton(
                "Đăng xuất",
                icon=ft.Icons.LOGOUT,
                icon_color=ft.Colors.RED_300,
                style=ft.ButtonStyle(color=ft.Colors.BLACK54),
                on_click=handle_logout
            ),
            footer_text,
            ft.Container(height=20),
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO, # <--- TỰ ĐỘNG HIỆN THANH CUỘN KHI CẦN
    )

    # Ghép layout
    layout = ft.Stack(
        [
            background_layer,
            # Căn giữa nội dung, đảm bảo không bị méo khi full screen
            ft.Container(
                content=main_column, 
                alignment=ft.alignment.center,
                width=float("inf"), # Chiếm toàn bộ chiều ngang
            ),
            logo_layer,
        ],
        expand=True
    )

    page.add(layout)

if __name__ == "__main__":
    ft.app(target=main)