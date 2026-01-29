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

class AdminApp:
    def __init__(self, page: ft.Page, go_back_callback=None):
        self.page = page
        self.go_back_callback = go_back_callback
        self.page.title = "Hệ thống giám sát lái xe - Admin"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # --- Sidebar Style ---
        self.SIDEBAR_COLOR = "#6B8E23" # Màu xanh rêu giống ảnh
        self.TEXT_COLOR = ft.Colors.WHITE
        self.SELECTED_COLOR = "#9ACD32" # Màu highlight khi chọn
        
        # Lưu trữ menu items để highlight
        self.menu_items = {}
        self.current_page = "dashboard"
        
        # Thời gian realtime
        self.time_text = ft.Text("", size=14, color=ft.Colors.GREY)
        self.running = True

        # --- Content Area ---
        self.content_area = ft.Container(expand=True, padding=20, bgcolor="#F0F2F5")

        self.init_ui()
        self.start_clock()

    def start_clock(self):
        def update_time():
            while self.running:
                now = datetime.now()
                time_str = now.strftime("%d/%m/%Y %H:%M:%S")
                self.time_text.value = time_str
                try:
                    self.time_text.update()
                except:
                    break
                time.sleep(1)
        
        thread = threading.Thread(target=update_time, daemon=True)
        thread.start()

    def switch_page(self, e):
        # Lấy index của nút được bấm (dùng data để định danh)
        selected_page = e.control.data
        
        # Bỏ highlight cũ
        if self.current_page in self.menu_items:
            self.menu_items[self.current_page].bgcolor = None
            self.menu_items[self.current_page].update()
        
        # Thêm highlight mới
        self.current_page = selected_page
        if selected_page in self.menu_items:
            self.menu_items[selected_page].bgcolor = self.SELECTED_COLOR
            self.menu_items[selected_page].update()
        
        self.content_area.content = None # Clear cũ
        
        if selected_page == "dashboard":
            self.content_area.content = TrangChu()
        elif selected_page == "drivers":
            self.content_area.content = QuanLiTaiXe()
        elif selected_page == "sessions":
            self.content_area.content = PhienLaiPage()
        elif selected_page == "stats":
            self.content_area.content = ThongKePage()
        elif selected_page == "models":
            self.content_area.content = QuanLiModel("Quản lý Model AI", self.page)
        elif selected_page == "data":
            self.content_area.content = QuanLiThongBao("Quản lý Dữ liệu")
        elif selected_page == "settings":
            self.content_area.content = CaiDatPage()
            
        self.content_area.update()

    def create_menu_item(self, icon, text, page_name):
        menu_container = ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=self.TEXT_COLOR),
                ft.Text(text, color=self.TEXT_COLOR, size=16, weight=ft.FontWeight.W_500)
            ]),
            padding=ft.padding.symmetric(vertical=15, horizontal=20),
            ink=True,
            on_click=self.switch_page,
            data=page_name, # Dùng data để xác định trang cần chuyển
            border_radius=10,
            bgcolor=self.SELECTED_COLOR if page_name == "dashboard" else None
        )
        self.menu_items[page_name] = menu_container
        return menu_container

    def init_ui(self):
        # Logo/Icon image
        logo_image = ft.Image(
            src="src\GUI\data\image_admin\image_btnlogo_admin.png",
            width=60,
            height=60,
            fit=ft.ImageFit.CONTAIN
        )
        
        # 1. Sidebar (Cột bên trái)
        sidebar = ft.Container(
            width=250,
            bgcolor=self.SIDEBAR_COLOR,
            padding=10,
            content=ft.Column([
                # Header Sidebar
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        logo_image,
                        ft.Text("ADMIN PANEL", size=20, weight=ft.FontWeight.BOLD, color=self.TEXT_COLOR)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Divider(color=ft.Colors.WHITE24),
                
                # Menu Items
                self.create_menu_item(ft.Icons.DASHBOARD, "Bảng điều khiển", "dashboard"),
                self.create_menu_item(ft.Icons.PEOPLE, "Tài xế", "drivers"),
                self.create_menu_item(ft.Icons.TIME_TO_LEAVE, "Phiên lái", "sessions"),
                self.create_menu_item(ft.Icons.BAR_CHART, "Thống kê", "stats"),
                ft.Divider(color=ft.Colors.WHITE24),
                self.create_menu_item(ft.Icons.MEMORY, "Quản lý Model", "models"),
                self.create_menu_item(ft.Icons.DATASET, "Quản lý Dữ liệu", "data"),
                ft.Divider(color=ft.Colors.WHITE24),
                self.create_menu_item(ft.Icons.SETTINGS, "Cài đặt", "settings"),
            ])
        )

        # 2. Header (Thanh trên cùng bên phải)
        header = ft.Container(
            height=60, bgcolor=ft.Colors.WHITE, padding=ft.padding.symmetric(horizontal=20),
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
            content=ft.Row([
                ft.Text("Hệ Thống Giám Sát", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.time_text,
                    ft.CircleAvatar(
                        foreground_image_src="https://avatars.githubusercontent.com/u/1?v=4",
                        content=ft.Text("A")
                    ),
                    ft.Text("Nguyen Ngoc Hieu", weight=ft.FontWeight.BOLD)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

        # 3. Main Layout: Row(Sidebar, Column(Header, Content))
        layout = ft.Row(
            controls=[
                sidebar,
                ft.Column([
                    header,
                    self.content_area
                ], expand=True)
            ],
            expand=True,
            spacing=0
        )

        # Mặc định load trang chủ
        self.content_area.content = TrangChu()
        self.page.add(layout)
    
    def go_back(self):
        self.running = False  # Stop clock thread
        if self.go_back_callback:
            self.page.controls.clear()
            self.page.update()
            self.go_back_callback()

def main(page: ft.Page, go_back_callback=None):
    AdminApp(page, go_back_callback)

if __name__ == "__main__":
    ft.app(target=main)