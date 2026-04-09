import flet as ft
import json
import os

JSON_FILE = "src/GUI/data/accounts.json"

class CaiDatPage(ft.Column):
    def __init__(self, page=None, current_username=None, on_plan_changed=None):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page = page
        self.current_username = current_username
        self.on_plan_changed = on_plan_changed
        self.payment_method = "bank" 
        self.current_plan = "free"
        
        # UI Elements
        self.plan_radio = None 
        self.btn_upgrade = None 
        
        self.load_current_plan()
        self.init_ui()

    def load_current_plan(self):
        """Đọc gói cước từ JSON"""
        if os.path.exists(JSON_FILE) and self.current_username:
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user in data.get("user_accounts", []):
                        if user.get("username") == self.current_username:
                            self.current_plan = user.get("plan", "Free").lower()
                            break
            except Exception as e:
                print(f"Lỗi đọc JSON: {e}")

    def save_plan_to_json(self, new_plan):
        """Lưu gói cước vào JSON"""
        if os.path.exists(JSON_FILE) and self.current_username:
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                users = data.get("user_accounts", [])
                user_found = False
                for user in users:
                    if user.get("username") == self.current_username:
                        user["plan"] = new_plan.capitalize()
                        user_found = True
                        break
                
                if user_found:
                    with open(JSON_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    self.current_plan = new_plan
                    
                    # Cập nhật giao diện sau khi lưu thành công
                    self.update_upgrade_button_state()
                    
                    self.page.open(ft.SnackBar(ft.Text(f"Thành công! Gói hiện tại: {new_plan.capitalize()}"), bgcolor=ft.Colors.GREEN))
                    self.page.update()

                    # Báo cho main_user cập nhật Sidebar
                    if self.on_plan_changed:
                        self.on_plan_changed()
                
            except Exception as e:
                print(f"Lỗi lưu JSON: {e}")
                self.page.open(ft.SnackBar(ft.Text("Lỗi lưu dữ liệu!"), bgcolor=ft.Colors.RED))

    def update_upgrade_button_state(self):
        """Hàm này cập nhật trạng thái nút và gọi update() (Chỉ dùng sau khi đã render)"""
        if self.btn_upgrade:
            is_pro = self.current_plan == "pro"
            self.btn_upgrade.text = "Đang sử dụng" if is_pro else "Nâng Cấp Ngay"
            self.btn_upgrade.disabled = is_pro
            self.btn_upgrade.bgcolor = ft.Colors.GREEN if is_pro else ft.Colors.BLUE
            
            # Chỉ update nếu nút đã nằm trên page (Tránh lỗi AssertionError)
            if self.btn_upgrade.page:
                self.btn_upgrade.update()

    def _on_plan_selected(self, e):
        """Xử lý khi chọn Radio"""
        selected_plan = e.control.value
        if selected_plan == self.current_plan:
            return

        if selected_plan == "pro":
            self.show_payment_dialog(e)
        else:
            self.save_plan_to_json("free")

    def show_payment_dialog(self, e=None):
        """Hiển thị Popup QR"""
        
        # Dùng self.page vì đã được truyền từ main_user
        current_page = self.page
        
        print(f"[DEBUG] show_payment_dialog - current_page: {current_page}")
        print(f"[DEBUG] show_payment_dialog - payment_method: {self.payment_method}")
        print(f"[DEBUG] show_payment_dialog - current_username: {self.current_username}")
        
        if not current_page:
            print("[ERROR] Không có page để hiển thị dialog!")
            return

        def close_dialog(e):
            # Hủy bỏ: Trả radio về gói cũ
            if self.plan_radio:
                self.plan_radio.value = self.current_plan 
                self.plan_radio.update()
            
            current_page.close(dialog)

        def confirm_payment_action(e):
            # Xác nhận: Lưu gói Pro
            self.save_plan_to_json("pro") 
            
            # Cập nhật Radio thành Pro
            if self.plan_radio:
                self.plan_radio.value = "pro"
                self.plan_radio.update()
            
            # Đóng popup
            current_page.close(dialog)

        qr_path = r"D:\TestGUI\src\GUI\data\qr_thanh_toan.jpg"
        
        qr_content = ft.Column([
            ft.Text(f"Thanh toán qua {self.payment_method.upper()}", size=16, weight="bold"),
            ft.Container(height=10),
            ft.Image(
                src=qr_path,
                width=250, height=250, fit=ft.ImageFit.CONTAIN,
                error_content=ft.Column([
                    ft.Icon(ft.Icons.QR_CODE_2, size=100, color=ft.Colors.BLACK54),
                    ft.Text("Mã QR Thanh Toán", size=12)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            ft.Container(height=10),
            ft.Text("Số tiền: 199.000 VND", size=18, weight="bold", color=ft.Colors.BLUE),
            ft.Text(f"Nội dung: PRO LGBT [{self.current_username}]", size=14, color=ft.Colors.GREY_700)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Quét Mã Để Thanh Toán", text_align=ft.TextAlign.CENTER),
            content=qr_content,
            actions=[
                ft.TextButton("Hủy bỏ", on_click=close_dialog),
                ft.ElevatedButton("Đã thanh toán", on_click=confirm_payment_action, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        print(f"[DEBUG] Dialog created, opening with page.open()...")
        
        # Cách đúng để mở dialog trong Flet
        current_page.open(dialog)
        
        print(f"[DEBUG] Dialog opened!")

    def init_ui(self):
        # 1. Các mục cài đặt
        settings_container = ft.Container(
            width=600,
            content=ft.Column([
                self._create_setting_row("Thông báo", "Tắt", "Bật", True),
                ft.Container(height=10),
                self._create_setting_row("Giao diện", "Tối", "Sáng", True, highlight=True),
                ft.Container(height=10),
                self._create_dropdown_row("Ngôn ngữ", ["Tiếng Việt", "English", "日本語"]),
            ])
        )

        # Radio Phương thức thanh toán
        payment_radio = ft.RadioGroup(
            content=ft.Column([
                ft.Row([
                    ft.Image(src=r"src\GUI\data\image_user\logo_visa.png", width=30, height=30, fit=ft.ImageFit.CONTAIN, error_content=ft.Icon(ft.Icons.CREDIT_CARD, size=30, color=ft.Colors.BLUE)),
                    ft.Radio(value="bank", label="Thẻ ngân hàng", fill_color=ft.Colors.BLUE_GREY),
                ], spacing=10),
                ft.Row([
                    ft.Image(src=r"src\GUI\data\image_user\logo_momo.png", width=30, height=30, fit=ft.ImageFit.CONTAIN, error_content=ft.Icon(ft.Icons.WALLET, size=30, color=ft.Colors.PINK)),
                    ft.Radio(value="momo", label="Momo", fill_color=ft.Colors.PINK),
                ], spacing=10),
            ]), 
            value="bank",
            on_change=lambda e: setattr(self, 'payment_method', e.control.value)
        )

        # Radio Gói đăng ký
        self.plan_radio = ft.RadioGroup(
            content=ft.Row([
                # Gói Free
                ft.Container(
                    expand=True, padding=15, border=ft.border.all(2, ft.Colors.GREY_300), border_radius=10, bgcolor=ft.Colors.GREY_50,
                    content=ft.Column([
                        ft.Radio(value="free", label="Free", fill_color=ft.Colors.GREEN),
                        ft.Text("0 VND / tháng", size=12, weight="bold"),
                        ft.Divider(),
                        ft.Row([ft.Icon(ft.Icons.BUILD, size=14), ft.Text("Chức năng cơ bản", size=11)], spacing=5),
                        ft.Row([ft.Icon(ft.Icons.FLASH_ON, size=14), ft.Text("Tốc độ khá", size=11)], spacing=5),
                    ])
                ),
                ft.Container(width=20),
                
                # Gói Pro
                ft.Container(
                    expand=True, padding=15, border=ft.border.all(2, ft.Colors.BLUE_300), border_radius=10, bgcolor=ft.Colors.BLUE_50,
                    content=ft.Column([
                        ft.Row([
                            ft.Radio(value="pro", label="", fill_color=ft.Colors.BLUE),
                            ft.Text("Pro", weight="bold", size=16, color=ft.Colors.BLUE_700),
                        ]),
                        ft.Text("199.000 VND / tháng", size=12, weight="bold", color=ft.Colors.BLUE_700),
                        ft.Divider(),
                        ft.Row([ft.Icon(ft.Icons.DIAMOND, size=14, color=ft.Colors.BLUE), ft.Text("Ưu tiên tính năng mới", size=11)], spacing=5),
                        ft.Row([ft.Icon(ft.Icons.ROCKET_LAUNCH, size=14, color=ft.Colors.BLUE), ft.Text("AI chính xác cao", size=11)], spacing=5)
                    ])
                )
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START),
            value=self.current_plan,
            on_change=self._on_plan_selected
        )

        # Layout chính
        plan_container = ft.Container(
            width=700, 
            bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
            border=ft.border.all(1, ft.Colors.BLACK12),
            content=ft.Column([
                ft.Text("Gói đăng ký", size=18, weight="bold"),
                ft.Container(height=10),
                ft.Text("Phương thức thanh toán", size=12, color=ft.Colors.GREY),
                payment_radio,
                ft.Container(height=20),
                ft.Text("Chọn gói của bạn", size=12, color=ft.Colors.GREY),
                ft.Container(height=10),
                self.plan_radio,
            ])
        )

        self.controls = [
            ft.Container(height=30),
            ft.Text("Cài Đặt Người Dùng", size=28, weight="bold"),
            ft.Container(height=30),
            settings_container,
            ft.Container(height=20),
            plan_container
        ]

    def _create_setting_row(self, label, off_text, on_text, value, highlight=False):
        border_style = ft.border.all(2, ft.Colors.BLUE) if highlight else ft.border.all(1, ft.Colors.BLACK12)
        return ft.Container(
            bgcolor=ft.Colors.WHITE, padding=15, border_radius=15, border=border_style,
            content=ft.Row([
                ft.Text(label, weight="bold", size=16),
                ft.Row([
                    ft.Text(off_text, size=12, weight="bold"),
                    ft.Switch(value=value, active_color=ft.Colors.BLUE_GREY_700),
                    ft.Text(on_text, size=12, weight="bold"),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

    def _create_dropdown_row(self, label, options):
        return ft.Container(
            bgcolor=ft.Colors.WHITE, padding=15, border_radius=15, border=ft.border.all(1, ft.Colors.BLACK12),
            content=ft.Row([
                ft.Text(label, weight="bold", size=16),
                ft.Dropdown(
                    options=[ft.dropdown.Option(opt) for opt in options],
                    value=options[0],
                    width=150, 
                    content_padding=10,
                    text_size=14, border_radius=8,
                    bgcolor=ft.Colors.GREY_100, border_color=ft.Colors.GREY_400
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )