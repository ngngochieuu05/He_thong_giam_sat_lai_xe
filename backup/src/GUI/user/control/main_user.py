import flet as ft
from datetime import datetime
import threading
import time
import json
import os

# --- IMPORT CÁC TRANG CON ---
# Sử dụng relative imports để tránh lỗi ModuleNotFoundError
from .page.phien_lai import PhienLaiPage
from .page.cai_dat import CaiDatPage
# [CẬP NHẬT 1] Import trang Tiện Ích
try:
    from .page.tien_ich import TienIchPage
except ImportError as e:
    print(f"Lỗi import tien_ich.py: {e}")
    TienIchPage = None

# Đường dẫn đến file dữ liệu
JSON_FILE = "src/GUI/data/accounts.json"

class UserApp:
    def __init__(self, page: ft.Page, go_back_callback=None, user_account=None):
        self.page = page
        self.go_back_callback = go_back_callback
        self.page.title = "Tài Xế - Driver System"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#D1E2D3" # Màu nền xanh nhạt

        # --- Style Config ---
        self.SIDEBAR_COLOR = "#4CAF50" # Xanh lá đậm
        self.TEXT_COLOR = ft.Colors.WHITE
        self.SELECTED_COLOR = "#81C784" # Xanh lá sáng (Highlight)

        # --- LOAD INFO USER TỪ JSON ---
        if user_account:
            self.current_user_info = user_account
            self.current_username = user_account.get("username", "user01")
        else:
            self.current_username = "user01" 
            self.current_user_info = self.get_user_info(self.current_username)

        self.menu_items = {}
        self.current_page = "session"
        self.running = True
        
        self.time_text = ft.Text("", size=14, color=ft.Colors.GREY_800)
        self.content_area = ft.Container(expand=True, padding=20) 
        
        # Biến tham chiếu để update sidebar
        self.sidebar_container = None 

        self.init_ui()
        self.start_clock()

    def get_user_info(self, username):
        """Đọc thông tin user từ JSON để hiển thị lên Sidebar"""
        default_user = {"name": "Tài xế", "driver_id": "N/A", "username": username, "plan": "Free"}
        
        # Logic tìm file JSON
        possible_paths = [
            JSON_FILE,
            "../../data/accounts.json", 
            "../../../src/GUI/data/accounts.json",
            "data/accounts.json"
        ]
        
        target_path = JSON_FILE
        for path in possible_paths:
            if os.path.exists(path):
                target_path = path
                break

        if os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for u in data.get("user_accounts", []):
                        if u["username"] == username:
                            if "plan" not in u:
                                u["plan"] = "Free"
                            return u
            except Exception as e:
                print(f"Lỗi đọc JSON User: {e}")
        return default_user

    def reload_sidebar_data(self):
        """Hàm callback: Đọc lại JSON và vẽ lại Sidebar"""
        # 1. Đọc lại dữ liệu mới nhất
        self.current_user_info = self.get_user_info(self.current_username)
        
        # 2. Xây dựng lại nội dung sidebar
        new_content = self.build_sidebar_column()
        
        # 3. Gán nội dung mới và cập nhật UI
        if self.sidebar_container:
            self.sidebar_container.content = new_content
            self.sidebar_container.update()

    def start_clock(self):
        def update_time():
            while self.running:
                now = datetime.now()
                self.time_text.value = now.strftime("%d/%m/%Y %H:%M")
                try:
                    self.time_text.update()
                except:
                    break
                time.sleep(1)
        threading.Thread(target=update_time, daemon=True).start()

    def switch_page(self, e):
        selected_page = e.control.data
        
        # Xử lý hiệu ứng chọn menu
        if self.current_page in self.menu_items:
            self.menu_items[self.current_page].bgcolor = None
            self.menu_items[self.current_page].update()
        
        self.current_page = selected_page
        if selected_page in self.menu_items:
            self.menu_items[selected_page].bgcolor = self.SELECTED_COLOR
            self.menu_items[selected_page].update()
        
        # Chuyển nội dung trang
        self.content_area.content = None
        
        if selected_page == "session":
            self.content_area.content = PhienLaiPage()
        
        # [CẬP NHẬT 2] Xử lý hiển thị trang Tiện Ích
        elif selected_page == "utilities":
            if TienIchPage:
                self.content_area.content = TienIchPage()
            else:
                self.content_area.content = ft.Text("Chưa tìm thấy file tien_ich.py", color="red")

        elif selected_page == "settings":
            # Truyền callback reload_sidebar_data vào đây
            self.content_area.content = CaiDatPage(
                page=self.page, 
                current_username=self.current_username,
                on_plan_changed=self.reload_sidebar_data 
            )
            
        self.content_area.update()

    def create_menu_item(self, icon, text, page_name):
        item = ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=self.TEXT_COLOR),
                ft.Text(text, color=self.TEXT_COLOR, size=16, weight=ft.FontWeight.BOLD)
            ]),
            padding=15, border_radius=10, ink=True,
            on_click=self.switch_page, data=page_name,
            bgcolor=self.SELECTED_COLOR if page_name == "session" else None
        )
        self.menu_items[page_name] = item
        return item

    def handle_logout(self, e):
        self.running = False
        if self.go_back_callback:
            self.page.controls.clear()
            self.page.update()
            self.go_back_callback()
        else:
            self.page.open(ft.SnackBar(ft.Text("Đã đăng xuất!"), bgcolor=ft.Colors.RED))

    def build_sidebar_column(self):
        """Hàm dựng nội dung Sidebar (được tách ra để tái sử dụng khi reload)"""
        # Lấy thông tin plan để hiển thị màu sắc
        plan_name = self.current_user_info.get("plan", "Free")
        plan_color = ft.Colors.AMBER_700 if plan_name.lower() == "pro" else ft.Colors.BLUE_GREY_400
        plan_icon = ft.Icons.WORKSPACE_PREMIUM if plan_name.lower() == "pro" else ft.Icons.VERIFIED_USER

        return ft.Column([
            # Avatar User
            ft.Container(
                padding=20, alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Stack([
                        ft.CircleAvatar(
                            foreground_image_src="https://avatars.githubusercontent.com/u/1?v=4", 
                            radius=40, bgcolor=ft.Colors.WHITE
                        ),
                        # Icon nhỏ hiển thị trạng thái gói
                        ft.Container(
                            content=ft.Icon(plan_icon, size=20, color=ft.Colors.WHITE),
                            bgcolor=plan_color,
                            border_radius=50,
                            padding=2,
                            border=ft.border.all(2, ft.Colors.WHITE),
                            right=0, bottom=0
                        )
                    ], width=80, height=80),
                    
                    ft.Container(height=5),
                    ft.Text(self.current_user_info.get("name", "User"), color=ft.Colors.WHITE, weight="bold", size=16, text_align="center"),
                    ft.Text(f"ID: {self.current_user_info.get('driver_id', 'N/A')}", color=ft.Colors.WHITE70, size=12),
                    
                    # Badge tên gói cước
                    ft.Container(
                        content=ft.Text(f"Gói: {plan_name.upper()}", color=ft.Colors.WHITE, size=10, weight="bold"),
                        bgcolor=plan_color,
                        padding=ft.padding.symmetric(horizontal=10, vertical=2),
                        border_radius=10,
                        margin=ft.margin.only(top=5)
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            ft.Divider(color=ft.Colors.WHITE24),
            
            # [CẬP NHẬT 3] Menu Items - Thêm nút Tiện Ích vào danh sách
            self.create_menu_item(ft.Icons.DIRECTIONS_CAR, "Phiên Lái", "session"),
            self.create_menu_item(ft.Icons.DASHBOARD_CUSTOMIZE, "Tiện Ích", "utilities"), # <-- MỚI THÊM
            self.create_menu_item(ft.Icons.SETTINGS, "Cài Đặt", "settings"),
            
            ft.Container(expand=True), 
            
            # Nút Logout
            ft.Container(
                content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.WHITE), ft.Text("Đăng xuất", color=ft.Colors.WHITE)]),
                padding=15, ink=True, on_click=self.handle_logout
            )
        ])

    def init_ui(self):
        # 1. Sidebar (Menu trái)
        # Sử dụng build_sidebar_column để tạo nội dung
        self.sidebar_container = ft.Container(
            width=220, bgcolor=self.SIDEBAR_COLOR, padding=10,
            content=self.build_sidebar_column()
        )

        # 2. Header (Thanh trên cùng)
        header = ft.Container(
            height=60, 
            content=ft.Row([
                ft.Text("Driver Management System", size=18, weight="bold", color=ft.Colors.BLUE_GREY_900),
                ft.Row([
                    ft.Icon(ft.Icons.NOTIFICATIONS_NONE, color=ft.Colors.BLUE_GREY_900),
                    self.time_text
                ], spacing=15)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20)
        )

        # 3. Layout Tổng
        layout = ft.Row(
            controls=[
                self.sidebar_container,
                ft.Column([
                    header,
                    self.content_area
                ], expand=True)
            ],
            expand=True, spacing=0
        )

        # Load mặc định trang Phiên Lái
        self.content_area.content = PhienLaiPage()
        self.page.add(layout)

def main(page: ft.Page):
    UserApp(page)

if __name__ == "__main__":
    ft.app(target=main)