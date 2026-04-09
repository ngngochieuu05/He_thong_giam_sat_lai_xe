import flet as ft
import json
import os
import webbrowser
from ..ui_styles import elevated_button, text_button
from src.DAL.tai_xe_dal import cap_nhat_tai_xe

try:
    from src.BUS.oa_core.telegram_link_service import generate_link_token, check_bound, get_bot_info
except Exception:
    generate_link_token = None
    check_bound = None
    get_bot_info = None

try:
    from src.DAL.accounts_sync import get_driver_account_from_db
except Exception:
    get_driver_account_from_db = None

JSON_FILE = "src/GUI/data/accounts.json"

class CaiDatPage(ft.Stack):
    def __init__(self, page=None, current_username=None, on_plan_changed=None, current_theme="dark", on_theme_changed=None):
        # Đổi sang Stack và ép lề âm để background tràn viền
        super().__init__(expand=True)
        self.margin = ft.margin.all(-20)
        
        self.page = page
        self.current_username = current_username
        self.on_plan_changed = on_plan_changed
        self.on_theme_changed = on_theme_changed
        self.payment_method = "bank" 
        self.current_plan = "free"
        self.current_theme = (current_theme or "dark").lower()
        self.notifications_enabled = True
        self.telegram_data = None
        self.telegram_token = ""
        self.selected_settings_tab = "general"
        self.PRIMARY = "#4CAF50"
        self.ACCENT_BLUE = "#56CCF2"
        self.ACCENT_GOLD = "#F2C94C"
        self._apply_palette(self.current_theme)
        
        # UI Elements
        self.plan_radio = None 
        self.btn_upgrade = None 
        self.theme_switch = None
        self.telegram_token_text = None
        self.telegram_status_text = None
        self.telegram_account_text = None
        self.open_telegram_button = None
        self.copy_token_button = None
        self.refresh_telegram_button = None
        
        self.load_current_plan()
        self.init_ui()

    def _apply_palette(self, theme_name):
        is_light = (theme_name or "dark").lower() == "light"
        self.current_theme = "light" if is_light else "dark"
        self.TEXT_PRIMARY = "#0F172A" if is_light else ft.Colors.WHITE
        self.TEXT_SECONDARY = "#475569" if is_light else ft.Colors.WHITE70
        self.CARD_BG = "#FFFFFFE6" if is_light else ft.Colors.with_opacity(0.28, ft.Colors.BLACK)
        self.CARD_BORDER = "#CBD5E1" if is_light else ft.Colors.with_opacity(0.22, ft.Colors.WHITE)
        self.INPUT_BG = "#F8FAFC" if is_light else ft.Colors.with_opacity(0.12, ft.Colors.WHITE)
        self.ROW_BG = "#FFFFFFCC" if is_light else ft.Colors.with_opacity(0.14, ft.Colors.WHITE)
        self.OVERLAY_BG = ft.Colors.with_opacity(0.12, ft.Colors.WHITE) if is_light else ft.Colors.BLACK54
        self.STATUS_BG = "#E2E8F0" if is_light else ft.Colors.with_opacity(0.14, ft.Colors.WHITE)
        self.TOKEN_BG = "#E2E8F0" if is_light else "#111827"
        self.TELEGRAM_PANEL_BG = "#F8FAFC" if is_light else "#1F2937"
        self.TAB_LABEL_COLOR = "#0F172A" if is_light else ft.Colors.WHITE

    def load_current_plan(self):
        """Đọc gói cước từ JSON"""
        db_user = None
        if self.current_username and get_driver_account_from_db:
            try:
                db_user = get_driver_account_from_db(self.current_username)
            except Exception as e:
                print(f"Lỗi đọc DB user settings: {e}")

        if os.path.exists(JSON_FILE) and self.current_username:
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user in data.get("user_accounts", []):
                        if user.get("username") == self.current_username:
                            self.current_plan = (user.get("plan") or user.get("goi_dich_vu") or "Free").lower()
                            self.current_theme = (user.get("theme_preference") or self.current_theme or "dark").lower()
                            self.notifications_enabled = bool(user.get("notifications_enabled", True))
                            self.telegram_data = user.get("telegram_data")
                            self._apply_palette(self.current_theme)
                            break
            except Exception as e:
                print(f"Lỗi đọc JSON: {e}")

        if db_user:
            self.current_plan = (db_user.get("plan") or db_user.get("goi_dich_vu") or self.current_plan or "free").lower()
            self.telegram_data = db_user.get("telegram_data") or self.telegram_data

    def save_user_preferences(self, updates: dict):
        if os.path.exists(JSON_FILE) and self.current_username:
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                user_found = False
                for user in data.get("user_accounts", []):
                    if user.get("username") == self.current_username:
                        user.update(updates)
                        user_found = True
                        break

                if user_found:
                    with open(JSON_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    return True
            except Exception as ex:
                print(f"Lỗi lưu user preferences: {ex}")
        return False

    def handle_theme_toggle(self, e):
        new_theme = "light" if bool(e.control.value) else "dark"
        self._apply_palette(new_theme)
        self.save_user_preferences({"theme_preference": new_theme})
        if self.on_theme_changed:
            self.on_theme_changed(new_theme)
        self.init_ui()
        self.update()
        self._show_snackbar(f"Đã chuyển sang giao diện {'sáng' if new_theme == 'light' else 'tối'}.", ft.Colors.GREEN)

    def handle_notification_toggle(self, e):
        self.notifications_enabled = bool(e.control.value)
        self.save_user_preferences({"notifications_enabled": self.notifications_enabled})
        self._show_snackbar("Đã cập nhật tùy chọn thông báo.", ft.Colors.GREEN)

    def _generate_telegram_token(self, e=None):
        if not generate_link_token or not self.current_username:
            self._show_snackbar("Không thể tạo token Telegram.", ft.Colors.RED)
            return
        try:
            self.telegram_token = generate_link_token(self.current_username)
            self._update_telegram_ui()
            self._show_snackbar("Đã tạo token Telegram mới.", ft.Colors.GREEN)
        except Exception as ex:
            print(f"Lỗi tạo token Telegram: {ex}")
            self._show_snackbar("Lỗi tạo token Telegram.", ft.Colors.RED)

    def _copy_telegram_token(self, e=None):
        if not self.page or not self.telegram_token:
            return
        self.page.set_clipboard(self.telegram_token)
        self._show_snackbar("Đã sao chép token Telegram.", ft.Colors.GREEN)

    def _open_telegram_link(self, e=None):
        if not self.telegram_token:
            self._generate_telegram_token()
        if not self.telegram_token:
            return
        bot_url = "https://t.me/safedrive_alert_bot"
        try:
            if get_bot_info:
                bot_url = get_bot_info().get("bot_url", bot_url)
        except Exception:
            pass
        webbrowser.open(f"{bot_url}?start={self.telegram_token}")

    def _show_telegram_guide(self, e=None):
        if not self.page:
            return

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Hướng dẫn liên kết Telegram", weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
            bgcolor=self.TELEGRAM_PANEL_BG,
            content=ft.Container(
                width=520,
                content=ft.Column([
                    ft.Text("1. Bấm Tạo token mới. Token này chỉ dành cho tài khoản đang đăng nhập.", size=14, color=self.TEXT_SECONDARY),
                    ft.Text("2. Bấm Mở Telegram Bot. Ứng dụng sẽ mở bot kèm sẵn token trong link.", size=14, color=self.TEXT_SECONDARY),
                    ft.Text("3. Trong Telegram, chỉ cần bấm Start. Không cần gõ lại token nếu bạn mở từ app.", size=14, color=self.TEXT_SECONDARY),
                    ft.Text("4. Nếu Telegram hỏi xác nhận, hãy cho phép bot bắt đầu cuộc trò chuyện.", size=14, color=self.TEXT_SECONDARY),
                    ft.Text("5. Quay lại app rồi bấm Kiểm tra liên kết. Khi thành công sẽ hiện Đã liên kết Telegram.", size=14, color=self.TEXT_SECONDARY),
                    ft.Container(height=8),
                    ft.Text("Nếu trạng thái chưa đổi ngay, chờ 3-5 giây rồi kiểm tra lại một lần nữa.", size=13, color=self.TEXT_SECONDARY),
                ], spacing=10),
            ),
            actions=[text_button("Đóng", on_click=lambda _: self.page.close(dialog), kind="surface")],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialog)

    def _refresh_telegram_status(self, e=None):
        if not check_bound or not self.current_username:
            self._show_snackbar("Không thể kiểm tra trạng thái Telegram.", ft.Colors.RED)
            return
        try:
            self.telegram_data = check_bound(self.current_username)
            self._update_telegram_ui()
            if self.telegram_data:
                self._show_snackbar("Tài khoản Telegram đã được liên kết.", ft.Colors.GREEN)
                if self.on_plan_changed:
                    self.on_plan_changed()
            else:
                self._show_snackbar("Chưa phát hiện liên kết Telegram cho tài khoản này.", ft.Colors.ORANGE)
        except Exception as ex:
            print(f"Lỗi kiểm tra Telegram: {ex}")
            self._show_snackbar("Lỗi kiểm tra trạng thái Telegram.", ft.Colors.RED)

    def _update_telegram_ui(self):
        if self.telegram_status_text:
            is_linked = bool((self.telegram_data or {}).get("chat_id"))
            self.telegram_status_text.value = "Đã liên kết Telegram" if is_linked else "Chưa liên kết Telegram"
            self.telegram_status_text.color = ft.Colors.GREEN if is_linked else self.ACCENT_GOLD
        if self.telegram_account_text:
            if self.telegram_data:
                username = self.telegram_data.get("telegram_username") or "Không có username"
                chat_id = self.telegram_data.get("chat_id") or "Không có chat_id"
                self.telegram_account_text.value = f"Username: {username}\nChat ID: {chat_id}"
            else:
                self.telegram_account_text.value = "Mở bot Telegram và bấm Kiểm tra liên kết sau khi xác nhận trong bot."
        if self.telegram_token_text:
            self.telegram_token_text.value = self.telegram_token or "Chưa tạo token Telegram"
        for control in [self.telegram_status_text, self.telegram_account_text, self.telegram_token_text]:
            if control and control.page:
                control.update()

    def switch_settings_tab(self, tab_name):
        self.selected_settings_tab = tab_name
        self.init_ui()
        self.update()

    def _build_settings_tab_button(self, label, tab_name):
        is_active = self.selected_settings_tab == tab_name
        return ft.Container(
            ink=True,
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            bgcolor=self.PRIMARY if is_active else self.ROW_BG,
            border=ft.border.all(1, self.PRIMARY if is_active else self.CARD_BORDER),
            on_click=lambda _: self.switch_settings_tab(tab_name),
            content=ft.Text(
                label,
                size=14,
                weight=ft.FontWeight.W_700,
                color=ft.Colors.WHITE if is_active else self.TEXT_PRIMARY,
            ),
        )

    def save_plan_to_json(self, new_plan):
        """Lưu gói cước vào JSON"""
        if os.path.exists(JSON_FILE) and self.current_username:
            try:
                db_saved = cap_nhat_tai_xe(self.current_username, goi_dich_vu=new_plan.capitalize())
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                users = data.get("user_accounts", [])
                user_found = False
                for user in data.get("user_accounts", []):
                    if user.get("username") == self.current_username:
                        user["plan"] = new_plan.capitalize()
                        user["goi_dich_vu"] = new_plan.capitalize()
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
                elif not db_saved:
                    self.page.open(ft.SnackBar(ft.Text("Không thể cập nhật gói tài khoản trong DB."), bgcolor=ft.Colors.RED))
                
            except Exception as e:
                print(f"Lỗi lưu JSON: {e}")
                self.page.open(ft.SnackBar(ft.Text("Lỗi lưu dữ liệu!"), bgcolor=ft.Colors.RED))

    def update_upgrade_button_state(self):
        """Hàm này cập nhật trạng thái nút và gọi update() (Chỉ dùng sau khi đã render)"""
        if self.btn_upgrade:
            is_pro = self.current_plan == "pro"
            self.btn_upgrade.text = "Đang sử dụng" if is_pro else "Nâng Cấp Ngay"
            self.btn_upgrade.disabled = is_pro
            self.btn_upgrade.style = ft.ButtonStyle(
                bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE) if is_pro else self.ACCENT_GOLD,
                color=ft.Colors.WHITE70 if is_pro else ft.Colors.BLACK,
                shape=ft.RoundedRectangleBorder(radius=14),
                side=ft.BorderSide(1, self.CARD_BORDER),
                text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_700),
            )
            
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
        current_page = self.page
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
            if self.plan_radio:
                self.plan_radio.value = "pro"
                self.plan_radio.update()
            current_page.close(dialog)

        qr_path = self._data_asset_path("qr_thanh_toan.jpg")
        
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
            ft.Text(f"Nội dung: PRO [{self.current_username}]", size=14, color=ft.Colors.GREY_700)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Quét Mã Để Thanh Toán", text_align=ft.TextAlign.CENTER),
            content=qr_content,
            actions=[
                text_button("Hủy bỏ", on_click=close_dialog, kind="surface"),
                elevated_button("Đã thanh toán", on_click=confirm_payment_action, kind="primary"),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        current_page.open(dialog)

    def _image_asset_path(self, filename):
        return os.path.abspath(os.path.join("src", "GUI", "data", "image_user", filename))

    def _data_asset_path(self, filename):
        return os.path.abspath(os.path.join("src", "GUI", "data", filename))

    def _show_snackbar(self, message, color):
        if not self.page:
            return
        if hasattr(self.page, "open"):
            self.page.open(ft.SnackBar(ft.Text(message), bgcolor=color))
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()

    def _create_glass_card(self, title, icon, content, width=900):
        return ft.Container(
            width=width,
            padding=24,
            border_radius=24,
            bgcolor=self.CARD_BG,
            border=ft.border.all(1, self.CARD_BORDER),
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        width=42,
                        height=42,
                        border_radius=21,
                        bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon, color=self.PRIMARY, size=22),
                    ),
                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
                ], spacing=12),
                ft.Container(height=18),
                content,
            ], spacing=0)
        )

    def _create_plan_card(self, value, title, price, subtitle, features, accent_color):
        is_selected = self.current_plan == value
        return ft.Container(
            expand=True,
            padding=20,
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.18 if is_selected else 0.12, ft.Colors.WHITE),
            border=ft.border.all(1.5 if is_selected else 1, accent_color if is_selected else self.CARD_BORDER),
            content=ft.Column([
                ft.Row([
                    ft.Radio(
                        value=value,
                        label=title,
                        fill_color=accent_color,
                        label_style=ft.TextStyle(color=self.TEXT_PRIMARY, weight=ft.FontWeight.BOLD, size=18),
                    ),
                    ft.Container(expand=True),
                    ft.Column([
                        ft.Text(price, size=22, weight=ft.FontWeight.W_900, color=self.TEXT_PRIMARY),
                        ft.Text(subtitle, size=11, color=self.TEXT_SECONDARY),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Container(height=14),
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=accent_color, size=16),
                        ft.Text(feature, size=13, color=self.TEXT_SECONDARY, expand=True),
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START)
                    for feature in features
                ], spacing=10),
            ], spacing=0)
        )

    def _create_payment_option(self, image_name, fallback_icon, label, value, accent_color):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
            border=ft.border.all(1, self.CARD_BORDER),
            content=ft.Row([
                ft.Image(
                    src=self._image_asset_path(image_name),
                    width=28,
                    height=28,
                    fit=ft.ImageFit.CONTAIN,
                    error_content=ft.Icon(fallback_icon, size=26, color=accent_color),
                ),
                ft.Radio(
                    value=value,
                    label=label,
                    fill_color=accent_color,
                    label_style=ft.TextStyle(color=self.TEXT_PRIMARY, size=14, weight=ft.FontWeight.W_600),
                ),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def init_ui(self):
        # --- 1. LỚP BACKGROUND TRÀN VIỀN ---
        IMG_BG = self._image_asset_path("backround.jpg")
        
        bg_image = ft.Image(
            src=IMG_BG,
            fit=ft.ImageFit.COVER,
            expand=True
        )
        
        bg_overlay = ft.Container(
            bgcolor=self.OVERLAY_BG, 
            expand=True,
            blur=10 
        )

        header_section = ft.Container(
            width=900,
            padding=ft.padding.symmetric(horizontal=24, vertical=22),
            border_radius=24,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            border=ft.border.all(1, self.CARD_BORDER),
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            content=ft.Row([
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SETTINGS_ROUNDED, color=self.PRIMARY, size=30),
                        ft.Text("Cài đặt hệ thống", size=28, weight=ft.FontWeight.W_900, color=self.TEXT_PRIMARY),
                    ], spacing=10),
                    ft.Container(height=6),
                    ft.Text(
                        "Quản lý tuỳ chọn trải nghiệm, liên kết Telegram và gói dịch vụ cho tài khoản tài xế.",
                        size=14,
                        color=self.TEXT_SECONDARY,
                    ),
                ], spacing=0, expand=True),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    border_radius=18,
                    bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
                    border=ft.border.all(1, self.CARD_BORDER),
                    content=ft.Column([
                        ft.Text("Gói hiện tại", size=12, color=self.TEXT_SECONDARY),
                        ft.Text(self.current_plan.upper(), size=18, weight=ft.FontWeight.BOLD, color=self.ACCENT_GOLD if self.current_plan == "pro" else self.PRIMARY),
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # --- 2. CÁC MỤC CÀI ĐẶT CƠ BẢN ---
        settings_container = self._create_glass_card(
            "Tuỳ chọn chung",
            ft.Icons.TUNE,
            content=ft.Column([
                self._create_setting_row("Thông báo", "Tắt", "Bật", self.notifications_enabled, on_change=self.handle_notification_toggle),
                ft.Container(height=10),
                self._create_setting_row("Giao diện", "Tối", "Sáng", self.current_theme == "light", on_change=self.handle_theme_toggle, highlight=True),
                ft.Container(height=10),
                self._create_dropdown_row("Ngôn ngữ", ["Tiếng Việt", "English", "日本語"]),
            ], spacing=0),
        )

        self.telegram_status_text = ft.Text("", size=15, weight=ft.FontWeight.W_700)
        self.telegram_account_text = ft.Text("", size=13, color=self.TEXT_SECONDARY)
        self.telegram_token_text = ft.Text("Chưa tạo token Telegram", size=16, weight=ft.FontWeight.W_700, color=self.TEXT_PRIMARY, selectable=True)
        self.copy_token_button = elevated_button("Sao chép token", icon=ft.Icons.COPY, on_click=self._copy_telegram_token, kind="surface")
        self.open_telegram_button = elevated_button("Mở Telegram Bot", icon=ft.Icons.TELEGRAM, on_click=self._open_telegram_link, kind="primary")
        self.refresh_telegram_button = elevated_button("Kiểm tra liên kết", icon=ft.Icons.REFRESH, on_click=self._refresh_telegram_status, kind="secondary")
        self.telegram_guide_button = elevated_button("Hướng dẫn liên kết", icon=ft.Icons.HELP_OUTLINE, on_click=self._show_telegram_guide, kind="surface")

        telegram_container = self._create_glass_card(
            "Liên kết Telegram",
            ft.Icons.TELEGRAM,
            content=ft.Column([
                ft.Container(
                    padding=18,
                    border_radius=18,
                    bgcolor=self.STATUS_BG,
                    border=ft.border.all(1, self.CARD_BORDER),
                    content=ft.Row([
                        ft.Icon(ft.Icons.MARK_CHAT_READ_ROUNDED, color=self.PRIMARY, size=24),
                        ft.Column([
                            self.telegram_status_text,
                            self.telegram_account_text,
                        ], spacing=6, expand=True),
                    ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ),
                ft.Container(height=14),
                ft.Container(
                    padding=20,
                    border_radius=18,
                    bgcolor=self.TELEGRAM_PANEL_BG,
                    border=ft.border.all(1, self.CARD_BORDER),
                    content=ft.Column([
                        ft.Text("Token liên kết", size=13, weight=ft.FontWeight.W_700, color=self.TEXT_SECONDARY),
                        ft.Container(height=10),
                        ft.Container(
                            width=float("inf"),
                            padding=16,
                            border_radius=14,
                            bgcolor=self.TOKEN_BG,
                            content=self.telegram_token_text,
                        ),
                        ft.Container(height=14),
                        ft.Row([
                            elevated_button("Tạo token mới", icon=ft.Icons.KEY, on_click=self._generate_telegram_token, kind="warning"),
                            self.copy_token_button,
                        ], wrap=True, spacing=10),
                        ft.Container(height=12),
                        ft.Text(
                            "1. Tạo token hoặc dùng token hiện có.\n2. Mở bot Telegram với nút bên dưới.\n3. Sau khi bot xác nhận, bấm Kiểm tra liên kết.",
                            size=13,
                            color=self.TEXT_SECONDARY,
                        ),
                        ft.Container(height=16),
                        ft.Row([
                            self.open_telegram_button,
                            self.refresh_telegram_button,
                            self.telegram_guide_button,
                        ], wrap=True, spacing=10),
                    ], spacing=0),
                ),
            ], spacing=0),
        )

        # --- 3. GÓI ĐĂNG KÝ & THANH TOÁN (GOM CHUNG) ---
        payment_radio = ft.RadioGroup(
            content=ft.Column([
                self._create_payment_option("logo_visa.png", ft.Icons.CREDIT_CARD, "Thẻ ngân hàng", "bank", self.ACCENT_BLUE),
                self._create_payment_option("logo_momo.png", ft.Icons.WALLET, "Momo", "momo", "#FF5AA5"),
            ]), 
            value="bank",
            on_change=lambda e: setattr(self, 'payment_method', e.control.value)
        )

        self.plan_radio = ft.RadioGroup(
            content=ft.Row([
                self._create_plan_card(
                    "free",
                    "Free",
                    "0 VND",
                    "mỗi tháng",
                    [
                        "Đầy đủ chức năng cơ bản để giám sát phiên lái.",
                        "Tốc độ phản hồi ổn định cho nhu cầu phổ thông.",
                        "Phù hợp để trải nghiệm và dùng hằng ngày.",
                    ],
                    self.PRIMARY,
                ),
                ft.Container(width=15),
                self._create_plan_card(
                    "pro",
                    "Pro",
                    "199.000 VND",
                    "mỗi tháng",
                    [
                        "Ưu tiên trải nghiệm tính năng mới sau mỗi đợt cập nhật.",
                        "Tối ưu tốc độ phản hồi và độ chính xác nhận diện.",
                        "Phù hợp cho người dùng cần độ ổn định cao hơn.",
                    ],
                    self.ACCENT_GOLD,
                )
            ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START),
            value=self.current_plan,
            on_change=self._on_plan_selected
        )

        self.btn_upgrade = elevated_button("Nâng Cấp Ngay", icon=ft.Icons.UPGRADE, on_click=self.show_payment_dialog, kind="warning")

        plan_container = self._create_glass_card(
            "Gói dịch vụ và thanh toán",
            ft.Icons.WORKSPACE_PREMIUM,
            content=ft.Row([
                ft.Column([
                    ft.Text("Phương thức thanh toán", size=13, color=self.TEXT_SECONDARY),
                    ft.Container(height=12),
                    payment_radio,
                    ft.Container(height=18),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=14, vertical=12),
                        border_radius=16,
                        bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
                        border=ft.border.all(1, self.CARD_BORDER),
                        content=ft.Column([
                            ft.Text("Lưu ý", size=13, weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
                            ft.Text(
                                "Sau khi xác nhận thanh toán, hệ thống sẽ cập nhật gói hiện tại và đồng bộ ra sidebar của user.",
                                size=12,
                                color=self.TEXT_SECONDARY,
                            ),
                        ], spacing=8),
                    ),
                ], expand=1, alignment=ft.MainAxisAlignment.START),

                ft.Container(
                    expand=3,
                    content=ft.Column([
                        self.plan_radio,
                        ft.Container(height=18),
                        ft.Row([self.btn_upgrade], alignment=ft.MainAxisAlignment.END),
                    ], spacing=0)
                )
            ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=18)
        )
        self.update_upgrade_button_state()

        self._update_telegram_ui()

        tab_content = settings_container
        if self.selected_settings_tab == "telegram":
            tab_content = telegram_container
        elif self.selected_settings_tab == "plan":
            tab_content = plan_container

        tab_bar = ft.Row(
            [
                self._build_settings_tab_button("Chung", "general"),
                self._build_settings_tab_button("Telegram", "telegram"),
                self._build_settings_tab_button("Gói dịch vụ", "plan"),
            ],
            wrap=True,
            spacing=10,
        )

        # --- 4. TẬP HỢP LAYOUT VÀO CUỘN ---
        scrollable_content = ft.Container(
            padding=ft.padding.only(left=40, right=40, top=30, bottom=20),
            expand=True,
            content=ft.Column(
                [
                    header_section,
                    ft.Container(height=20),
                    ft.Container(
                        width=900,
                        padding=ft.padding.symmetric(horizontal=20, vertical=14),
                        border_radius=24,
                        bgcolor=self.CARD_BG,
                        border=ft.border.all(1, self.CARD_BORDER),
                        content=ft.Column([
                            tab_bar,
                            ft.Container(height=18),
                            tab_content,
                        ], spacing=0),
                    ),
                    ft.Container(height=24),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
            )
        )

        self.controls = [
            bg_image,
            bg_overlay,
            scrollable_content
        ]

    def _create_setting_row(self, label, off_text, on_text, value, highlight=False, on_change=None):
        return ft.Container(
            bgcolor=self.ROW_BG,
            padding=16,
            border_radius=18,
            border=ft.border.all(1.2 if highlight else 1, self.PRIMARY if highlight else self.CARD_BORDER),
            content=ft.Row([
                ft.Container(
                    expand=True,
                    content=ft.Text(label, weight="bold", size=16, color=self.TEXT_PRIMARY),
                ),
                ft.Container(
                    width=210,
                    alignment=ft.alignment.center_right,
                    content=ft.Row([
                        ft.Container(width=42, alignment=ft.alignment.center, content=ft.Text(off_text, size=12, weight="bold", color=self.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER, no_wrap=True)),
                        ft.Switch(value=value, active_color=self.PRIMARY, thumb_color=ft.Colors.WHITE, on_change=on_change),
                        ft.Container(width=42, alignment=ft.alignment.center, content=ft.Text(on_text, size=12, weight="bold", color=self.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER, no_wrap=True)),
                    ], spacing=8, alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

    def _create_dropdown_row(self, label, options):
        return ft.Container(
            bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
            padding=16,
            border_radius=18,
            border=ft.border.all(1, self.CARD_BORDER),
            content=ft.Row([
                ft.Text(label, weight="bold", size=16, color=self.TEXT_PRIMARY),
                ft.Dropdown(
                    options=[ft.dropdown.Option(opt) for opt in options],
                    value=options[0],
                    width=150, 
                    content_padding=10,
                    text_size=14,
                    border_radius=10,
                    color=self.TEXT_PRIMARY,
                    bgcolor=self.INPUT_BG,
                    border_color=self.CARD_BORDER,
                    focused_border_color=self.PRIMARY,
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )