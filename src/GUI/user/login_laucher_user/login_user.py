import flet as ft
import time
import os
import json
from . import laucher_user

class UserUI:
    def __init__(self, page: ft.Page, go_back_callback=None):
        self.page = page
        self.go_back_callback = go_back_callback
        self.page.title = "Đăng Kí / Đăng Nhập Tài Xế"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # =====================================================================
        # --- CẤU HÌNH TÀI NGUYÊN (ĐÃ SỬA: Thêm self. và khớp tên biến) ---
        # =====================================================================
        
        # 1. Ảnh nền chính (Khớp với self.bg_image_path bên dưới)
        self.bg_image_path = r"D:\TestGUI\src\GUI\data\image_user\backround.jpg" 
        
        # 2. Icon hiển thị ở màn hình Login (Khớp với self.login_car_icon_path bên dưới)
        # Bạn có thể thay bằng đường dẫn ảnh chiếc xe hoặc logo tùy ý
        self.login_car_icon_path = r"src\GUI\data\image_laucher\image_btnlogo_user.png"
        
        # 3. Avatar mặc định cho Dashboard
        self.avatar_url = "https://avatars.githubusercontent.com/u/1?v=4"
        
        # --- TRẠNG THÁI NGƯỜI DÙNG ---
        self.current_user_name = "Hieu"
        self.current_user_id = "12345"

        # Khởi động vào màn hình Đăng nhập
        self.show_login_view()

    # =========================================================================
    # 1. MÀN HÌNH ĐĂNG NHẬP (LOGIN VIEW)
    # =========================================================================
    def show_login_view(self):
        self.page.clean()
        
        # Input fields
        user_input = ft.TextField(label="Tài khoản", value= "user01", prefix_icon=ft.Icons.PERSON, border_radius=10, bgcolor=ft.Colors.WHITE, text_size=14)
        pass_input = ft.TextField(label="Mật khẩu", value= "123456", prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True, border_radius=10, bgcolor=ft.Colors.WHITE, text_size=14)

        # Login Card
        login_card = ft.Container(
            width=400,
            padding=40,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK12),
            content=ft.Column([
                # Nút quay lại và Logo
                ft.Container(
                    content=ft.Stack([
                        ft.Container(
                            content=ft.Column([
                                ft.Image(
                                    src=self.login_car_icon_path, 
                                    width=100, height=80, 
                                    fit=ft.ImageFit.CONTAIN,
                                    error_content=ft.Column([
                                        ft.Icon(ft.Icons.DIRECTIONS_CAR_FILLED, size=60, color=ft.Colors.BLUE),
                                        ft.Text("Ảnh lỗi", size=10, color=ft.Colors.RED)
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                                ),
                                ft.Text("ĐĂNG NHẬP", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800),
                                ft.Text("Hệ thống giám sát lái xe", size=14, color=ft.Colors.GREY),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=ft.Colors.GREEN_700,
                                on_click=lambda e: self._go_back_to_main(),
                                tooltip="Quay lại"
                            ),
                            left=0,
                            top=0
                        )
                    ]),
                    height=150
                ),
                ft.Container(height=10),
                
                user_input,
                ft.Container(height=15),
                pass_input,
                ft.Container(
                    content=ft.TextButton(
                        "Quên mật khẩu?",
                        on_click=lambda e: self._handle_forgot_password(),
                        style=ft.ButtonStyle(color=ft.Colors.BLUE_700)
                    ),
                    alignment=ft.alignment.center_right
                ),
                ft.Container(height=10),
                
                # Nút Đăng nhập
                ft.ElevatedButton(
                    "Đăng nhập", 
                    width=float("inf"), 
                    height=50,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700, 
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    on_click=lambda e: self._handle_login(user_input.value, pass_input.value)
                ),
                
                ft.Container(height=15),
                
                # Divider
                ft.Row([
                    ft.Container(content=ft.Divider(), expand=True), 
                    ft.Text("HOẶC", size=12, color=ft.Colors.GREY), 
                    ft.Container(content=ft.Divider(), expand=True)
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Container(height=15),
                
                # Nút Face ID
                ft.OutlinedButton(
                    "Đăng nhập bằng khuôn mặt",
                    icon=ft.Icons.FACE_RETOUCHING_NATURAL,
                    width=float("inf"),
                    height=50,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREEN_700,
                        side=ft.BorderSide(1, ft.Colors.GREEN_700),
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    on_click=lambda e: self._handle_face_login()
                ),
                
                ft.Container(height=20),
                ft.TextButton("Đăng ký tài khoản mới", on_click=lambda e: self.show_register_view())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # Layout chính
        layout = ft.Stack([
            # Lớp 1: Ảnh nền
            ft.Image(
                src=self.bg_image_path,
                width=float("inf"), height=float("inf"),
                fit=ft.ImageFit.COVER,
                error_content=ft.Container(bgcolor="#E0F2F1")
            ),
            # Lớp 2: Phủ mờ
            ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK)),
            
            # Lớp 3: Card đăng nhập
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=login_card
            )
        ], expand=True)
        
        self.page.add(layout)

    # =========================================================================
    # 2. MÀN HÌNH ĐĂNG KÝ
    # =========================================================================
    def show_register_view(self):
        self.page.clean()
        
        input_style = {"border_radius": 10, "bgcolor": ft.Colors.WHITE, "text_size": 14, "content_padding": 15}
        
        txt_name = ft.TextField(label="Họ tên", prefix_icon=ft.Icons.PERSON_OUTLINE, **input_style)
        txt_phone = ft.TextField(label="SĐT", prefix_icon=ft.Icons.PHONE, **input_style)
        txt_username = ft.TextField(label="Tên đăng nhập", prefix_icon=ft.Icons.ACCOUNT_CIRCLE, **input_style)
        txt_password = ft.TextField(label="Mật khẩu", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True, can_reveal_password=True, **input_style)
        txt_password_confirm = ft.TextField(label="Nhập lại mật khẩu", prefix_icon=ft.Icons.LOCK_RESET, password=True, can_reveal_password=True, **input_style)

        register_card = ft.Container(
            width=450,
            padding=40,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK12),
            content=ft.Column([
                ft.Stack([
                    ft.Container(
                        content=ft.Column([
                            ft.Image(src=self.login_car_icon_path, width=60, height=60, fit=ft.ImageFit.CONTAIN),
                            ft.Text("ĐĂNG KÝ TÀI XẾ MỚI", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800),
                            ft.Text("Điền đầy đủ thông tin", size=12, color=ft.Colors.GREY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: self.show_login_view(),
                            tooltip="Quay lại"
                        ),
                        left=0,
                        top=0
                    )
                ]),
                
                ft.Container(height=20),
                txt_name,
                ft.Container(height=10),
                txt_phone,
                ft.Container(height=10),
                txt_username,
                ft.Container(height=10),
                txt_password,
                ft.Container(height=10),
                txt_password_confirm,
                ft.Container(height=20),
                
                # Nút Đăng ký chính
                ft.ElevatedButton(
                    "Đăng Ký",
                    icon=ft.Icons.PERSON_ADD,
                    width=float("inf"),
                    height=50,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    on_click=lambda e: self._handle_register(
                        txt_name.value, txt_phone.value,
                        txt_username.value, txt_password.value, txt_password_confirm.value
                    )
                ),
                
                ft.Container(height=15),
                
                # Divider
                ft.Row([
                    ft.Container(content=ft.Divider(), expand=True), 
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Container(height=26),
                
                # Nút quét khuôn mặt (tùy chọn)
                ft.OutlinedButton(
                    "Đăng ký khuôn mặt",
                    icon=ft.Icons.FACE,
                    width=float("inf"),
                    height=50,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREEN_700,
                        side=ft.BorderSide(1, ft.Colors.GREEN_700),
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    on_click=lambda e: self._handle_face_register()
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        )

        layout = ft.Stack([
            ft.Image(src=self.bg_image_path, width=float("inf"), height=float("inf"), fit=ft.ImageFit.COVER),
            ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK)),
            ft.Container(expand=True, alignment=ft.alignment.center, content=register_card)
        ], expand=True)
        
        self.page.add(layout)

    # =========================================================================
    # 3. MÀN HÌNH DASHBOARD
    # =========================================================================
    def show_dashboard_view(self):
        self.page.clean()
        
        user_info_card = ft.Container(
            width=350,
            padding=15,
            bgcolor="#D1E2D3",
            border=ft.border.all(1, ft.Colors.BLACK54),
            border_radius=15,
            content=ft.Row([
                ft.CircleAvatar(src=self.avatar_url, radius=30, bgcolor=ft.Colors.WHITE),
                ft.Column([
                    ft.Text(self.current_user_name, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.BLACK),
                    ft.Text(f"ID : {self.current_user_id}", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLACK),
                ], spacing=3)
            ], alignment=ft.MainAxisAlignment.START)
        )

        def create_dashboard_btn(text, icon, bg_color):
            return ft.Container(
                width=350, height=80,
                bgcolor=bg_color,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.BLACK54),
                padding=ft.padding.symmetric(horizontal=20),
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK26, offset=ft.Offset(0, 3)),
                ink=True,
                on_click=lambda e: print(f"Click: {text}"),
                content=ft.Row([
                    ft.Container(
                        width=50, height=50,
                        border=ft.border.all(2, ft.Colors.BLACK),
                        border_radius=25,
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon, color=ft.Colors.BLACK, size=30)
                    ),
                    ft.Container(width=15),
                    ft.Text(text, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
                ])
            )

        btn_start = create_dashboard_btn("Bắt Đầu Phiên Lái", ft.Icons.PLAY_ARROW, "#4CAF50")
        btn_history = create_dashboard_btn("Lịch Sử Phiên Lái", ft.Icons.HISTORY, "#2E7D9E")
        btn_settings = create_dashboard_btn("Cài Đặt", ft.Icons.SETTINGS, "#D68936")

        content_column = ft.Column(
            [
                ft.Container(height=50),
                user_info_card,
                ft.Container(height=30),
                btn_start,
                ft.Container(height=15),
                btn_history,
                ft.Container(height=15),
                btn_settings,
                ft.Container(expand=True),
                ft.Text("© 2026 Driver Driver v1.0.0", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(height=20)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        layout = ft.Stack([
            ft.Image(
                src=self.bg_image_path,
                width=float("inf"), height=float("inf"),
                fit=ft.ImageFit.COVER,
                error_content=ft.Container(bgcolor=ft.Colors.BLUE_GREY_900)
            ),
            ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
            ft.Container(
                content=content_column,
                alignment=ft.alignment.center,
                expand=True
            )
        ], expand=True)
        
        self.page.add(layout)

    # =========================================================================
    # 4. LOGIC XỬ LÝ
    # =========================================================================
    def _go_back_to_main(self):
        if self.go_back_callback:
            self.page.controls.clear()
            self.page.update()
            self.go_back_callback()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Không thể quay lại"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()

    def _handle_login(self, user, pwd):
        # Kiểm tra tài khoản trống
        if not user:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Tài khoản không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        # Kiểm tra mật khẩu trống
        if not pwd:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Mật khẩu không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        # Hiển thị thông báo đang xác thực
        self.page.open(ft.SnackBar(ft.Text("🔄 Đang xác thực tài khoản..."), bgcolor=ft.Colors.BLUE_400))
        self.page.update()
        
        time.sleep(0.3)  # Hiệu ứng loading nhẹ
        
        # Đọc tài khoản từ file JSON
        try:
            accounts_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "accounts.json")
            with open(accounts_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_accounts = data.get("user_accounts", [])
            
            # Kiểm tra tài khoản
            account_found = None
            for acc in user_accounts:
                if acc["username"] == user and acc["password"] == pwd:
                    account_found = acc
                    break
            
            if account_found:
                # Thông báo đăng nhập thành công
                self.page.open(ft.SnackBar(ft.Text(f"✅ Đăng nhập thành công! Xin chào {account_found['name']}"), bgcolor=ft.Colors.GREEN_600))
                self.page.update()
                
                time.sleep(0.8)
                self.current_user_name = account_found["name"]
                self.current_user_id = account_found["driver_id"]
                
                # Xóa form login và chuyển sang laucher_user
                self.page.controls.clear()
                self.page.update()
                laucher_user.main(self.page, self.go_back_callback)
            else:
                # Thông báo lỗi tài khoản/mật khẩu
                self.page.open(ft.SnackBar(ft.Text("❌ Sai tên đăng nhập hoặc mật khẩu!"), bgcolor=ft.Colors.RED_600))
                self.page.update()
        except FileNotFoundError:
            self.page.open(ft.SnackBar(ft.Text("❌ Không tìm thấy file tài khoản!"), bgcolor=ft.Colors.RED_600))
            self.page.update()
        except Exception as e:
            self.page.open(ft.SnackBar(ft.Text(f"❌ Lỗi hệ thống: {str(e)}"), bgcolor=ft.Colors.RED_600))
            self.page.update()

    def _handle_forgot_password(self):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("🔑 Tính năng khôi phục mật khẩu đang phát triển..."),
            bgcolor=ft.Colors.ORANGE_400
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _handle_face_login(self):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("📷 Đang mở camera nhận diện..."),
            bgcolor=ft.Colors.BLUE_400
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _handle_register(self, name, phone, username, password, password_confirm):
        # Kiểm tra từng trường riêng biệt
        if not name:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Họ tên không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        if not phone:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Số điện thoại không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        if not username:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Tên đăng nhập không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        if not password:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Mật khẩu không được để trống!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        if not password_confirm:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Vui lòng nhập lại mật khẩu!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        # Kiểm tra mật khẩu khớp
        if password != password_confirm:
            self.page.open(ft.SnackBar(ft.Text("⚠️ Mật khẩu nhập lại không khớp!"), bgcolor=ft.Colors.RED_400))
            self.page.update()
            return
        
        # Thông báo đang xử lý
        self.page.open(ft.SnackBar(ft.Text("🔄 Đang xử lý đăng ký..."), bgcolor=ft.Colors.BLUE_400))
        self.page.update()
        
        time.sleep(0.5)
        
        try:
            # Đọc file accounts.json
            accounts_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "accounts.json")
            if os.path.exists(accounts_path):
                with open(accounts_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"admin_accounts": [], "user_accounts": []}
            
            # Kiểm tra username đã tồn tại chưa
            for acc in data.get("user_accounts", []):
                if acc["username"] == username:
                    self.page.open(ft.SnackBar(ft.Text("❌ Tên đăng nhập đã tồn tại!"), bgcolor=ft.Colors.RED_600))
                    self.page.update()
                    return
            
            # Tự động tạo driver_id (TX001, TX002, ...)
            existing_ids = [acc.get("driver_id", "") for acc in data.get("user_accounts", [])]
            driver_id = f"TX{len(existing_ids) + 1:03d}"
            
            # Thêm tài khoản mới
            new_account = {
                "username": username,
                "password": password,
                "name": name,
                "driver_id": driver_id,
                "phone": phone
            }
            data["user_accounts"].append(new_account)
            
            # Lưu file
            with open(accounts_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Thông báo thành công
            self.page.open(ft.SnackBar(ft.Text("✅ Đăng ký thành công! Đang chuyển sang trang đăng nhập..."), bgcolor=ft.Colors.GREEN_600))
            self.page.update()
            
            time.sleep(1.5)
            self.show_login_view()
            
        except Exception as e:
            self.page.open(ft.SnackBar(ft.Text(f"❌ Lỗi: {str(e)}"), bgcolor=ft.Colors.RED_600))
            self.page.update()
    
    def _handle_face_register(self):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("📷 Tính năng đăng ký bằng khuôn mặt đang phát triển..."),
            bgcolor=ft.Colors.ORANGE_400
        )
        self.page.snack_bar.open = True
        self.page.update()

# --- Entry Point ---
def main(page: ft.Page, go_back_callback=None):
    UserUI(page, go_back_callback)

if __name__ == "__main__":
    ft.app(target=main)