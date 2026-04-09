import flet as ft
import json
import os
import shutil
import time
from pathlib import Path
from ..ui_styles import elevated_button, text_button
from src.DAL.tai_xe_dal import cap_nhat_tai_xe

# Đường dẫn database
JSON_FILE = "src/GUI/data/accounts.json"
IMAGE_USER_DIR = "src/GUI/data/image_user/"
PROJECT_ROOT = Path(__file__).resolve().parents[5]

class ProfileUserPage(ft.Stack):
    def __init__(self, user_account=None, on_update_sidebar=None):
        # Đổi cấu trúc gốc thành Stack để chứa background và ép margin âm tràn viền
        super().__init__(expand=True)
        self.margin = ft.margin.all(-20) 
        
        self.user_account = user_account or {}
        self.on_update_sidebar = on_update_sidebar
        self.PRIMARY = "#4CAF50"
        self.TEXT_PRIMARY = ft.Colors.WHITE
        self.TEXT_SECONDARY = ft.Colors.WHITE70
        self.CARD_BG = ft.Colors.with_opacity(0.28, ft.Colors.BLACK)
        self.CARD_BORDER = ft.Colors.with_opacity(0.22, ft.Colors.WHITE)
        
        # UI References
        self.avatar_image = None
        self.name_input = None
        self.password_input = None
        
        # FilePicker for avatar
        self.file_picker = ft.FilePicker(on_result=self._on_file_result)
        
        self.init_ui()

    def _resolve_avatar_src(self, avatar_path):
        if not avatar_path:
            return "https://flet.dev/img/pages/branding/logo/flet-logo-white.svg"
        avatar_value = str(avatar_path).strip()
        if avatar_value.startswith(("http://", "https://")):
            return avatar_value

        avatar_file = Path(avatar_value)
        if not avatar_file.is_absolute():
            avatar_file = (PROJECT_ROOT / avatar_file).resolve()
        else:
            avatar_file = avatar_file.resolve()

        if avatar_file.exists():
            try:
                return str(avatar_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
            except ValueError:
                return str(avatar_file).replace("\\", "/")

        return avatar_value.replace("\\", "/")

    def _save_avatar_to_storage(self, avatar_value):
        updated = False
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for user in data.get("user_accounts", []):
                    if user.get("username") == self.user_account.get("username"):
                        user["avatar"] = avatar_value
                        updated = True
                        break

                if updated:
                    with open(JSON_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as error:
                print(f"❌ [PROFILE] Save avatar JSON error: {error}")

        try:
            cap_nhat_tai_xe(self.user_account.get("username", ""), avatar=avatar_value)
        except Exception as error:
            print(f"❌ [PROFILE] Save avatar DB error: {error}")

        return updated

    def did_mount(self):
        # Đảm bảo file_picker được gắn vào page
        if self.page and self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
            self.page.update()

    def _on_file_result(self, e: ft.FilePickerResultEvent):
        """Xử lý sau khi người dùng chọn ảnh"""
        if not e.files or len(e.files) == 0:
            return

        picked_file = e.files[0]
        username = self.user_account.get("username", "unknown")
        
        # Đảm bảo thư mục tồn tại
        if not os.path.exists(IMAGE_USER_DIR):
            os.makedirs(IMAGE_USER_DIR)
            
        ext = os.path.splitext(picked_file.name or "")[1].lower() or ".png"
        target_filename = f"{username}_{int(time.time())}{ext}"
        target_path = os.path.abspath(os.path.join(IMAGE_USER_DIR, target_filename))
        stored_avatar_path = os.path.join(IMAGE_USER_DIR, target_filename).replace("\\", "/")
        
        try:
            # Copy file vào thư mục hệ thống
            shutil.copy(picked_file.path, target_path)
            
            # Update preview
            self.user_account["avatar"] = stored_avatar_path
            self.avatar_image.content.src = self._resolve_avatar_src(stored_avatar_path)
            self.avatar_image.update()
            self._save_avatar_to_storage(stored_avatar_path)
            if self.on_update_sidebar:
                self.on_update_sidebar()
            
            print(f"📸 [PROFILE] Uploaded avatar to: {target_path}")
            self.page.open(ft.SnackBar(ft.Text("Đổi ảnh đại diện thành công!"), bgcolor=ft.Colors.GREEN))
            self.page.update()
        except Exception as err:
            print(f"❌ [PROFILE] Upload error: {err}")
            self.page.open(ft.SnackBar(ft.Text(f"Lỗi upload: {err}"), bgcolor=ft.Colors.RED))
            self.page.update()

    def save_changes(self, e):
        """Lưu Name, Password và Avatar vào JSON"""
        if not os.path.exists(JSON_FILE):
            self.page.open(ft.SnackBar(ft.Text("Lỗi: File dữ liệu không tồn tại!"), bgcolor=ft.Colors.RED))
            return

        target_username = self.user_account.get("username")
        new_name = self.name_input.value
        new_password = self.password_input.value
        new_avatar = self.user_account.get("avatar")

        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            users = data.get("user_accounts", [])
            user_found = False
            
            for user in users:
                if user.get("username") == target_username:
                    user["name"] = new_name
                    user["password"] = new_password
                    user["avatar"] = new_avatar
                    user_found = True
                    break
            
            if user_found:
                cap_nhat_tai_xe(target_username, name=new_name, password=new_password, avatar=new_avatar)
                with open(JSON_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Cập nhật context session
                self.user_account["name"] = new_name
                self.user_account["password"] = new_password
                
                self.page.open(ft.SnackBar(ft.Text("Lưu thông tin thành công!"), bgcolor="#4CAF50"))
                
                # Cập nhật Sidebar ngay lập tức
                if self.on_update_sidebar:
                    self.on_update_sidebar()
            else:
                self.page.open(ft.SnackBar(ft.Text("Lỗi: Không tìm thấy tài khoản!"), bgcolor=ft.Colors.RED))

        except Exception as error:
            print(f"❌ [PROFILE] Save error: {error}")
            self.page.open(ft.SnackBar(ft.Text(f"Lỗi hệ thống: {str(error)}"), bgcolor=ft.Colors.RED))

        self.page.update()

    def init_ui(self):
        # --- 1. NỀN BACKGROUND TRÀN VIỀN ---
        IMG_BG = os.path.abspath(os.path.join("src", "GUI", "data", "image_user", "backround.jpg"))
        
        bg_image = ft.Image(
            src=IMG_BG,
            fit=ft.ImageFit.COVER,
            expand=True
        )
        
        # Lớp phủ đen mờ để làm nổi nội dung lên trên ảnh nền
        bg_overlay = ft.Container(
            bgcolor=ft.Colors.BLACK54, 
            expand=True,
            blur=10 
        )

        # --- 2. HEADER AVATAR ---
        current_avatar = self._resolve_avatar_src(self.user_account.get("avatar"))
        
        self.avatar_image = ft.CircleAvatar(
            content=ft.Image(src=current_avatar, fit=ft.ImageFit.COVER, width=120, height=120),
            radius=60,
            bgcolor=ft.Colors.WHITE
        )

        header_section = ft.Container(
            width=860,
            padding=ft.padding.symmetric(horizontal=24, vertical=24),
            border_radius=24,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            border=ft.border.all(1, self.CARD_BORDER),
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            content=ft.Column([
                self.avatar_image,
                text_button("Đổi ảnh đại diện", icon=ft.Icons.CAMERA_ALT, on_click=lambda _: self.file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE), kind="surface"),
                ft.Container(height=5),
                ft.Text(self.user_account.get("name", "User Profile"), size=28, weight="bold", color=self.PRIMARY),
                ft.Text(f"ID: {self.user_account.get('driver_id', 'N/A')}  •  {self.user_account.get('plan', 'Free').upper()}", color=self.TEXT_SECONDARY, weight="bold")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # Lấy dữ liệu telegram
        tele_data = self.user_account.get("telegram_data", {})
        chat_id = tele_data.get("chat_id")
        teleg_username = tele_data.get("telegram_username", "Chưa xác định")
        has_tele = "Đã liên kết" if chat_id else "Chưa liên kết"

        # Khởi tạo các Inputs
        self.name_input = self._create_form_field("Họ và tên", self.user_account.get("name", ""), False)
        username_input = self._create_form_field("Username (Cố định)", self.user_account.get("username", ""), True)
        driver_id_input = self._create_form_field("Mã định danh (Driver ID)", self.user_account.get("driver_id", ""), True)
        plan_input = self._create_form_field("Gói dịch vụ (Plan)", self.user_account.get("plan", "Free"), True)
        self.password_input = self._create_form_field("Mật khẩu", self.user_account.get("password", ""), False, is_pass=True)
        
        # Form Container
        main_form = ft.Container(
            width=860,
            bgcolor=self.CARD_BG,
            padding=30,
            border_radius=24,
            border=ft.border.all(1, self.CARD_BORDER),
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.BADGE, color=self.PRIMARY), ft.Text("Thông tin tài khoản", size=20, weight="bold", color=self.TEXT_PRIMARY)]),
                ft.Container(height=10),
                self.name_input,
                username_input,
                driver_id_input,
                plan_input,
                self.password_input,
                ft.Container(height=20),
                
                ft.Row([ft.Icon(ft.Icons.TELEGRAM, color=self.PRIMARY), ft.Text("Liên kết hệ thống", size=20, weight="bold", color=self.TEXT_PRIMARY)]),
                ft.Container(height=10),
                ft.Row([ft.Text("Trạng thái:", weight="bold", size=14, color=self.TEXT_PRIMARY), ft.Container(expand=True), ft.Text(has_tele, color=ft.Colors.GREEN_300 if chat_id else ft.Colors.RED_300, weight="bold")]),
                ft.Row([ft.Text("Telegram Username:", weight="bold", size=14, color=self.TEXT_PRIMARY), ft.Container(expand=True), ft.Text(teleg_username, color=self.TEXT_SECONDARY)]),
                ft.Row([ft.Text("Chat ID:", weight="bold", size=14, color=self.TEXT_PRIMARY), ft.Container(expand=True), ft.Text(str(chat_id) if chat_id else "N/A", color=self.TEXT_SECONDARY)]),
            ], spacing=15)
        )

        # Nút Lưu
        save_button = elevated_button("Lưu thay đổi", icon=ft.Icons.SAVE, on_click=self.save_changes, kind="primary", width=320, height=52)

        # --- 3. GHÉP VÀO NỘI DUNG CUỘN ---
        scrollable_content = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            expand=True,
            content=ft.Column(
                [
                    ft.Container(height=10),
                    header_section,
                    main_form,
                    ft.Container(height=20),
                    ft.Row([save_button], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=40),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                spacing=20
            )
        )

        # --- 4. ÁP DỤNG STACK LỚP ---
        self.controls = [
            bg_image,
            bg_overlay,
            scrollable_content
        ]

    def _create_form_field(self, label, val, is_read_only, is_pass=False):
        return ft.TextField(
            label=label, value=str(val), read_only=is_read_only,
            password=is_pass, can_reveal_password=is_pass,
            border_radius=14,
            bgcolor=ft.Colors.with_opacity(0.12 if is_read_only else 0.16, ft.Colors.WHITE),
            color=self.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=self.TEXT_SECONDARY, weight="bold"),
            focused_border_color=self.PRIMARY,
            border_color=self.CARD_BORDER
        )