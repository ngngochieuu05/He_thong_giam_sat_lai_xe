import flet as ft
import json
import os
from ..ui_styles import icon_button

DASHBOARD_DATA_FILE = "src/GUI/data/dashboard_data.json"

class LichSuPage(ft.Stack):
    def __init__(self, user_account=None, go_back_callback=None):
        # Đổi thành Stack và ép lề âm để tràn viền hoàn toàn
        super().__init__(expand=True)
        self.margin = ft.margin.all(-20)
        
        self.user_account = user_account or {}
        self.username = self.user_account.get("username", "user01")
        self.go_back_callback = go_back_callback
        
        # --- Bảng màu hiện đại (Glassmorphism) ---
        self.PRIMARY = "#4CAF50"
        self.TEXT_PRIMARY = ft.Colors.WHITE
        self.TEXT_SECONDARY = ft.Colors.WHITE70
        # Dùng màu nền nửa trong suốt để tạo hiệu ứng kính
        self.CARD_BG = ft.Colors.with_opacity(0.15, ft.Colors.WHITE)
        self.HEADER_BG = ft.Colors.with_opacity(0.3, ft.Colors.BLACK)
        
        self.init_ui()
        
    def _read_data(self):
        default_data = {"login_history": [], "driving_sessions": []}
        if os.path.exists(DASHBOARD_DATA_FILE):
            try:
                with open(DASHBOARD_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    users = data.get("users", {})
                    return users.get(self.username, default_data)
            except Exception as e:
                print(f"Lỗi đọc data: {e}")
        return default_data
        
    def init_ui(self):
        # --- 1. LỚP NỀN TRÀN VIỀN ---
        IMG_BG = r"E:\code\AppGS_v2\giam_sat_lai_xe\src\GUI\data\image_user\backround.jpg"
        
        bg_image = ft.Image(
            src=IMG_BG,
            fit=ft.ImageFit.COVER,
            expand=True
        )
        
        bg_overlay = ft.Container(
            bgcolor=ft.Colors.BLACK54, 
            expand=True,
            blur=10 # Làm mờ nền giúp bảng số liệu nổi bật
        )

        # --- ĐỌC DỮ LIỆU ---
        data = self._read_data()
        
        # --- 2. BẢNG ĐĂNG NHẬP ---
        logins = data.get("login_history", [])
        logins = logins[::-1] # Mới nhất lên trên
        
        if logins:
            headers = ft.Container(
                bgcolor=self.HEADER_BG, padding=ft.padding.symmetric(horizontal=20, vertical=15),
                border_radius=ft.border_radius.only(top_left=15, top_right=15),
                content=ft.Row([
                    ft.Text("Ngày đăng nhập", weight="bold", color=self.TEXT_PRIMARY, expand=1),
                    ft.Text("Thời gian", weight="bold", color=self.TEXT_PRIMARY, expand=1),
                ])
            )
            
            list_view = ft.ListView(expand=True, spacing=5, padding=ft.padding.only(top=5, bottom=5))
            for item in logins:
                list_view.controls.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=20, vertical=15),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                        border_radius=10,
                        # Hiệu ứng hover khi lướt qua dòng
                        ink=True,
                        on_hover=lambda e: self._hover_row(e),
                        content=ft.Row([
                            ft.Text(str(item.get("date", "")), color=self.TEXT_PRIMARY, expand=1, weight="w500"),
                            ft.Text(str(item.get("time", "")), color=self.TEXT_SECONDARY, expand=1),
                        ])
                    )
                )
                
            dt_logins = ft.Container(
                expand=True,
                content=ft.Column([headers, list_view], spacing=0)
            )
        else:
            dt_logins = ft.Container(
                content=ft.Text("Chưa có dữ liệu đăng nhập.", color=ft.Colors.WHITE54, italic=True, size=16),
                alignment=ft.alignment.center, expand=True
            )
        
        # --- 3. BẢNG PHIÊN LÁI ---
        sessions = data.get("driving_sessions", [])
        sessions = sessions[::-1]
        
        if sessions:
            headers2 = ft.Container(
                bgcolor=self.HEADER_BG, padding=ft.padding.symmetric(horizontal=20, vertical=15),
                border_radius=ft.border_radius.only(top_left=15, top_right=15),
                content=ft.Row([
                    ft.Text("Ngày", weight="bold", color=self.TEXT_PRIMARY, expand=2),
                    ft.Text("Thời lượng", weight="bold", color=self.TEXT_PRIMARY, expand=2),
                    ft.Text("Trạng thái vi phạm", weight="bold", color=self.TEXT_PRIMARY, expand=1, text_align=ft.TextAlign.CENTER),
                ])
            )
            
            list_view2 = ft.ListView(expand=True, spacing=5, padding=ft.padding.only(top=5, bottom=5))
            for item in sessions:
                alerts = item.get("alerts", 0)
                
                # Badge màu cho vi phạm
                alert_badge = ft.Container(
                    content=ft.Text(
                        f"{alerts} cảnh báo" if alerts > 0 else "An toàn", 
                        color=ft.Colors.WHITE, weight="bold", size=12, text_align=ft.TextAlign.CENTER
                    ),
                    bgcolor=ft.Colors.RED_500 if alerts > 0 else ft.Colors.GREEN_500,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=12,
                    alignment=ft.alignment.center
                )

                list_view2.controls.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=20, vertical=15),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                        border_radius=10,
                        ink=True,
                        on_hover=lambda e: self._hover_row(e),
                        content=ft.Row([
                            ft.Text(str(item.get("date", "")), color=self.TEXT_PRIMARY, expand=2, weight="w500"),
                            ft.Row([
                                ft.Icon(ft.Icons.TIMER, size=16, color=self.TEXT_SECONDARY),
                                ft.Text(f"{item.get('duration_minutes', 0)} phút", color=self.TEXT_SECONDARY)
                            ], expand=2),
                            ft.Container(content=alert_badge, expand=1, alignment=ft.alignment.center)
                        ])
                    )
                )
                
            dt_sessions = ft.Container(
                expand=True,
                content=ft.Column([headers2, list_view2], spacing=0)
            )
        else:
            dt_sessions = ft.Container(
                content=ft.Text("Chưa có phiên lái nào được ghi nhận.", color=ft.Colors.WHITE54, italic=True, size=16),
                alignment=ft.alignment.center, expand=True
            )

        # Hàm tạo hộp chứa bảng (Glassmorphism effect)
        def build_card_style(list_control):
            return ft.Container(
                content=list_control, 
                padding=20, 
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)), 
                border_radius=20, 
                bgcolor=self.CARD_BG, 
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
                expand=True,
                # clip_behavior giúp bo tròn cả nội dung bên trong
                clip_behavior=ft.ClipBehavior.HARD_EDGE 
            )

        # --- 4. CẤU TRÚC TAB ---
        tabs = ft.Tabs(
            selected_index=1,
            animation_duration=300,
            label_color=ft.Colors.WHITE,
            unselected_label_color=ft.Colors.WHITE54,
            indicator_color=self.PRIMARY,
            divider_color=ft.Colors.TRANSPARENT, # Giấu dòng kẻ ngang dưới tab cho thanh thoát
            tabs=[
                ft.Tab(
                    tab_content=ft.Row([ft.Icon(ft.Icons.LOGIN, size=20), ft.Text("Lịch Sử Đăng Nhập", weight="bold")]),
                    content=ft.Container(height=15, content=build_card_style(dt_logins), padding=ft.padding.only(top=20))
                ),
                ft.Tab(
                    tab_content=ft.Row([ft.Icon(ft.Icons.DIRECTIONS_CAR, size=20), ft.Text("Lịch Sử Phiên Lái", weight="bold")]),
                    content=ft.Container(height=15, content=build_card_style(dt_sessions), padding=ft.padding.only(top=20))
                )
            ],
            expand=True
        )

        # --- 5. HEADER KHUNG CHÍNH ---
        header_title = ft.Row([
            ft.Icon(ft.Icons.HISTORY, color=self.PRIMARY, size=30),
            ft.Text("Lịch Sử Hoạt Động", size=28, weight=ft.FontWeight.W_900, color=self.TEXT_PRIMARY),
        ])

        user_info_badge = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            border_radius=20,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            content=ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.WHITE, size=20),
                ft.Text(f"{self.user_account.get('name', self.username)}", size=14, color=ft.Colors.WHITE, weight="bold")
            ])
        )
        
        header = ft.Row([
            header_title,
            ft.Container(expand=True),
            user_info_badge
        ])
        
        # Xử lý nút back nếu mở từ luồng khác
        header_row_content = []
        if self.go_back_callback:
            back_btn = ft.Container(
                content=icon_button(ft.Icons.ARROW_BACK_IOS_NEW, on_click=lambda e: self.go_back_callback(), kind="surface", icon_size=20),
                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                border_radius=50,
                margin=ft.margin.only(right=15)
            )
            header_row_content.append(ft.Row([back_btn, header], expand=True))
        else:
            header_row_content.append(header)

        # Cột nội dung nổi trên nền ảnh
        main_content = ft.Container(
            padding=ft.padding.only(left=40, right=40, top=30, bottom=20),
            expand=True,
            content=ft.Column([
                *header_row_content,
                ft.Container(height=10),
                tabs
            ], expand=True)
        )

        # Gắn vào Stack
        self.controls = [
            bg_image,
            bg_overlay,
            main_content
        ]

    def _hover_row(self, e):
        """Tạo hiệu ứng sáng lên khi rê chuột vào từng dòng lịch sử"""
        e.control.bgcolor = ft.Colors.with_opacity(0.25, ft.Colors.WHITE) if e.data == "true" else ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
        e.control.update()