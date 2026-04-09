import flet as ft
from ..ui_styles import elevated_button

class UserDashboardPage(ft.Container):
    def __init__(self, user_account, switch_page_callback=None):
        super().__init__(expand=True)
        self.user_account = user_account or {}
        self.switch_page_callback = switch_page_callback
        
        # Lấy thông tin user
        user_name = self.user_account.get("name", "Tài xế")
        user_avatar = self.user_account.get("avatar", r"src\GUI\data\image_user\profile.png")

        self.content = ft.Column(
            [
                ft.Container(height=20),
                ft.Text(f"Xin chào, {user_name}!", size=32, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text("Sẵn sàng cho một hành trình an toàn", size=18, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                ft.Container(height=40),
                
                # Nút bắt đầu phiên lái
                ft.Container(
                    content=elevated_button(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=40),
                                ft.Text("Bắt Đầu Phiên Lái", size=20, weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        width=350,
                        height=80,
                        kind="primary",
                        on_click=lambda e: self.switch_page_callback("session") if self.switch_page_callback else None,
                    ),
                    alignment=ft.alignment.center
                ),
                
                ft.Container(height=20),

                # Các thẻ thông tin khác
                ft.Row(
                    [
                        self.create_info_card("Thống kê", ft.Icons.INSIGHTS, "history"),
                        self.create_info_card("Tiện ích", ft.Icons.MUSIC_NOTE, "utilities"),
                        self.create_info_card("Cài đặt", ft.Icons.SETTINGS, "settings"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20
                ),
                ft.Container(expand=True),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )

    def create_info_card(self, title, icon, page_name):
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(icon, size=30),
                        ft.Container(height=10),
                        ft.Text(title, weight=ft.FontWeight.BOLD),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20,
                width=150,
                height=120,
                on_click=lambda e: self.switch_page_callback(page_name) if self.switch_page_callback else None,
                ink=True,
            )
        )

# Để có thể import, ta cần một hàm trả về class
def get_user_dashboard_page():
    return UserDashboardPage

