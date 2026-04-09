import flet as ft
from datetime import datetime
import threading
import time
from .page.trang_chu import TrangChu
from .page.tai_xe import QuanLiTaiXe
from .page.phien_lai import PhienLaiPage
from .page.thong_ke import ThongKePage
from .page.quan_li_model_pt import QuanLiModel
from .page.quan_li_thong_bao_OA import QuanLiThongBao
from .page.cai_dat import CaiDatPage
from .ui_styles import BORDER, OVERLAY, TEXT_PRIMARY, TEXT_SECONDARY, icon_button


class AdminApp:
    def __init__(self, page: ft.Page, go_back_callback=None):
        self.page = page
        self.go_back_callback = go_back_callback
        self.page.title = "Admin Dashboard"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.DARK

        self.SIDEBAR_COLOR = "#0A0E13"
        self.TEXT_COLOR = TEXT_PRIMARY
        self.SELECTED_COLOR = ft.Colors.with_opacity(0.22, ft.Colors.WHITE)

        self.menu_items = {}
        self.current_page = "dashboard"
        self.sidebar_open = False

        self.header_title = ft.Text("Bảng Điều Khiển", size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
        self.time_text = ft.Text("", size=13, color=TEXT_SECONDARY)
        self.running = True

        self.content_area = ft.Container(expand=True, padding=0)
        self.sidebar_overlay = ft.Container(visible=False)
        self.sidebar_panel = ft.Container(width=0)
        self.sidebar_scrim = ft.Container(visible=False)
        self.menu_button = icon_button(ft.Icons.MENU, tooltip="Mở menu")

        self.init_ui()
        self.start_clock()

    def start_clock(self):
        def update_time():
            while self.running:
                now = datetime.now()
                self.time_text.value = now.strftime("%d/%m/%Y %H:%M:%S")
                try:
                    self.time_text.update()
                except Exception:
                    break
                time.sleep(1)

        threading.Thread(target=update_time, daemon=True).start()

    def switch_page(self, e):
        selected_page = e.control.data

        if self.current_page in self.menu_items:
            self.menu_items[self.current_page].bgcolor = None
            self.menu_items[self.current_page].update()

        self.current_page = selected_page
        if selected_page in self.menu_items:
            self.menu_items[selected_page].bgcolor = self.SELECTED_COLOR
            self.menu_items[selected_page].update()

        page_titles = {
            "dashboard": "Bảng Điều Khiển",
            "drivers": "Tài Xế",
            "sessions": "Phiên Lái",
            "thong_ke": "Thống Kê",
            "models": "Quản Lý Model",
            "data": "Quản Lý Dữ Liệu",
            "settings": "Cài Đặt",
        }
        if selected_page in page_titles:
            self.header_title.value = page_titles[selected_page]
            try:
                self.header_title.update()
            except Exception:
                pass

        self.content_area.content = None

        try:
            if selected_page == "dashboard":
                self.content_area.content = TrangChu()
            elif selected_page == "drivers":
                self.content_area.content = QuanLiTaiXe()
            elif selected_page == "sessions":
                self.content_area.content = PhienLaiPage()
            elif selected_page == "thong_ke":
                self.content_area.content = ThongKePage()
            elif selected_page == "models":
                self.content_area.content = QuanLiModel("Quản lý Model AI", self.page)
            elif selected_page == "data":
                self.content_area.content = QuanLiThongBao("Quản lý Dữ liệu")
            elif selected_page == "settings":
                self.content_area.content = CaiDatPage()
        except Exception as ex:
            import traceback

            print(f"[ERROR] switch_page '{selected_page}' failed: {ex}")
            traceback.print_exc()
            self.content_area.content = ft.Column(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=60, color=ft.Colors.RED_300),
                    ft.Text(f"Lỗi tải trang: {ex}", color=ft.Colors.RED_300, size=14),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        self.content_area.update()
        self.set_sidebar_open(False)

    def set_sidebar_open(self, open_state: bool):
        self.sidebar_open = open_state
        self.sidebar_overlay.visible = open_state
        self.sidebar_scrim.visible = open_state
        self.sidebar_scrim.bgcolor = ft.Colors.TRANSPARENT
        self.sidebar_panel.width = 280 if open_state else 0
        if open_state:
            self.menu_button.icon = ft.Icons.CLOSE
            self.menu_button.tooltip = "Đóng menu"
        else:
            self.menu_button.icon = ft.Icons.MENU
            self.menu_button.tooltip = "Mở menu"
        self.page.update()

    def toggle_sidebar(self, e=None):
        self.set_sidebar_open(not self.sidebar_open)

    def create_menu_item(self, icon, text, page_name):
        menu_container = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color=TEXT_SECONDARY, size=20),
                    ft.Container(width=8),
                    ft.Text(text, color=self.TEXT_COLOR, size=15, weight=ft.FontWeight.W_500),
                ]
            ),
            padding=ft.padding.symmetric(vertical=14, horizontal=16),
            ink=True,
            on_click=self.switch_page,
            data=page_name,
            border_radius=14,
            bgcolor=self.SELECTED_COLOR if page_name == "dashboard" else None,
        )
        self.menu_items[page_name] = menu_container
        return menu_container

    def init_ui(self):
        logo_image = ft.Image(
            src=r"src\GUI\data\image_admin\image_btnlogo_admin.png",
            width=72,
            height=72,
            fit=ft.ImageFit.CONTAIN,
            error_content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=50, color=ft.Colors.WHITE),
        )

        sidebar = ft.Container(
            width=280,
            padding=ft.padding.all(18),
            bgcolor=self.SIDEBAR_COLOR,
            border=ft.border.all(1, ft.Colors.with_opacity(0.10, ft.Colors.WHITE)),
            border_radius=26,
            shadow=ft.BoxShadow(blur_radius=36, color=ft.Colors.BLACK54, offset=ft.Offset(0, 18)),
            content=ft.Column(
                [
                    ft.Container(
                        padding=ft.padding.only(left=8, top=8, bottom=4),
                        content=icon_button(ft.Icons.ARROW_BACK, on_click=lambda e: self.go_back(), tooltip="Quay lại"),
                    ),
                    ft.Container(
                        padding=ft.padding.only(top=8, bottom=10, left=15, right=15),
                        content=ft.Column(
                            [
                                ft.Container(
                                    width=float("inf"),
                                    alignment=ft.alignment.center,
                                    content=logo_image,
                                ),
                                ft.Container(
                                    width=float("inf"),
                                    alignment=ft.alignment.center,
                                    content=ft.Text("ADMIN PANEL", size=17, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                    ),
                    ft.Divider(color=BORDER, height=1),
                    self.create_menu_item(ft.Icons.DASHBOARD, "Bảng điều khiển", "dashboard"),
                    self.create_menu_item(ft.Icons.PEOPLE, "Tài xế", "drivers"),
                    self.create_menu_item(ft.Icons.TIME_TO_LEAVE, "Phiên lái", "sessions"),
                    self.create_menu_item(ft.Icons.BAR_CHART, "Thống kê", "thong_ke"),
                    ft.Divider(color=BORDER, height=1),
                    self.create_menu_item(ft.Icons.MEMORY, "Quản lý Model", "models"),
                    self.create_menu_item(ft.Icons.DATASET, "Quản lý dữ liệu", "data"),
                    ft.Divider(color=BORDER, height=1),
                    self.create_menu_item(ft.Icons.SETTINGS, "Cài đặt", "settings"),
                    ft.Container(expand=True),
                    ft.Container(
                        padding=ft.padding.all(12),
                        content=ft.Text("© 2026 Admin Panel v1.0.0", size=10, color=ft.Colors.WHITE38),
                    ),
                ],
                expand=True,
                spacing=0,
            ),
        )
        self.sidebar_panel = ft.Container(
            width=0,
            content=ft.Container(
                width=280,
                height=float("inf"),
                padding=ft.padding.all(18),
                content=sidebar,
            ),
        )
        self.sidebar_scrim = ft.Container(
            expand=True,
            visible=False,
            bgcolor=ft.Colors.TRANSPARENT,
            on_click=lambda e: self.set_sidebar_open(False),
        )
        self.sidebar_overlay = ft.Row(
            [
                self.sidebar_panel,
                self.sidebar_scrim,
            ],
            expand=True,
            spacing=0,
            visible=False,
        )
        self.menu_button.on_click = self.toggle_sidebar

        header = ft.Container(
            height=82,
            bgcolor=self.SIDEBAR_COLOR,
            border=ft.border.all(1, BORDER),
            border_radius=24,
            padding=ft.padding.symmetric(horizontal=20),
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            content=ft.Row(
                [
                    ft.Row(
                        [
                            icon_button(ft.Icons.ARROW_BACK, on_click=lambda e: self.go_back(), tooltip="Quay lại"),
                            self.menu_button,
                            ft.CircleAvatar(
                                foreground_image_src="https://avatars.githubusercontent.com/u/1?v=4",
                                radius=22,
                                bgcolor=ft.Colors.GREY_300,
                            ),
                            icon_button(ft.Icons.NOTIFICATIONS_NONE, tooltip="Thông báo"),
                            ft.Column(
                                [
                                    ft.Text("Nguyen Ngoc Hieu", weight=ft.FontWeight.BOLD, size=14, color=TEXT_PRIMARY),
                                    ft.Text("Administrator", size=11, color=TEXT_SECONDARY),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=6,
                    ),
                    self.header_title,
                    self.time_text,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        shell_layout = ft.Stack(
            [
                ft.Container(
                    content=ft.Image(
                        src=r"src\GUI\Icons\Admin Dashboard\ThamGiaGiaoThong.png",
                        width=float("inf"),
                        height=float("inf"),
                        fit=ft.ImageFit.COVER,
                        error_content=ft.Container(bgcolor="#091017"),
                    ),
                    expand=True,
                    blur=18,
                ),
                ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.76, ft.Colors.BLACK)),
                ft.Container(
                    expand=True,
                    padding=ft.padding.all(20),
                    content=ft.Column(
                        [
                            header,
                            ft.Container(
                                expand=True,
                                border_radius=26,
                                bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                                border=ft.border.all(1, BORDER),
                                padding=24,
                                content=self.content_area,
                            ),
                        ],
                        expand=True,
                        spacing=16,
                    ),
                ),
                self.sidebar_overlay,
            ],
            expand=True,
        )

        self.content_area.content = TrangChu()
        self.page.add(shell_layout)

    def go_back(self):
        self.running = False
        if self.go_back_callback:
            self.page.controls.clear()
            self.page.update()
            self.go_back_callback()


def main(page: ft.Page, go_back_callback=None):
    AdminApp(page, go_back_callback)


if __name__ == "__main__":
    ft.app(target=main)