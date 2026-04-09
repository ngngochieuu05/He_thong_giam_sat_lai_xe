import flet as ft
import html
import json
import os
from datetime import datetime
from ..ui_styles import BORDER, DANGER, PRIMARY, SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, elevated_button, glass_card, icon_button, input_style, section_title, text_button
from src.BUS.oa_core.sua_thong_bao.tuy_chinh_thong_bao import get_thong_bao_service

# Đường dẫn file dữ liệu (chỉ dùng khi cần đọc ảnh/face_data qua JSON)
JSON_FILE = "src/GUI/data/accounts.json"
ICONS_DIR = r"src\GUI\Icons\Driver Management"

class QuanLiTaiXe(ft.Column):
    def __init__(self):
        super().__init__(expand=True)
        self.oa_service = get_thong_bao_service()
        self.drivers = []
        self.selected_driver = None
        self.search_query = ""
        field_style = input_style()

        # --- FORM FIELDS (dùng chung cho add/edit dialog) ---
        self.txt_id       = ft.TextField(label="Mã tài xế", width=350, **field_style)
        self.txt_username = ft.TextField(label="Username", width=350, **field_style)
        self.txt_name     = ft.TextField(label="Họ Tên", width=350, **field_style)
        self.txt_phone    = ft.TextField(label="Số điện thoại", width=350, **field_style)
        self.txt_cccd     = ft.TextField(label="CCCD/GPLX", width=350, **field_style)
        self.txt_password = ft.TextField(label="Mật khẩu", width=350, password=True, can_reveal_password=True, **field_style)
        self.txt_telegram = ft.TextField(
            label="Telegram Chat ID", width=350,
            input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$", replacement_string=""),
            prefix_icon=ft.Icons.TELEGRAM, hint_text="Chỉ nhập số", **field_style
        )

        # --- SEARCH FIELD ---
        self.search_field = ft.TextField(
            hint_text="Tìm kiếm theo tên hoặc mã tài xế ...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True, height=46,
            **field_style,
            on_change=self.on_search_change
        )

        # --- FILTER DROPDOWN ---
        self.filter_dropdown = ft.Dropdown(
            width=130, border_radius=8,
            bgcolor=SURFACE,
            color=TEXT_PRIMARY,
            border_color=BORDER,
            focused_border_color=PRIMARY,
            options=[
                ft.dropdown.Option("Tất cả"),
                ft.dropdown.Option("Hoạt động"),
                ft.dropdown.Option("Ngừng hoạt động"),
            ],
            value="Tất cả",
        )

        # --- TABLE ---
        self.table_headers = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border_radius=ft.border_radius.only(top_left=18, top_right=18),
            content=ft.Row([
                ft.Text("Mã tài xế", weight="bold", size=13, expand=2, color=TEXT_PRIMARY),
                ft.Text("Họ tên", weight="bold", size=13, expand=3, color=TEXT_PRIMARY),
                ft.Text("Số điện thoại", weight="bold", size=13, expand=2, color=TEXT_PRIMARY),
                ft.Text("CCCD/GPLX", weight="bold", size=13, expand=2, color=TEXT_PRIMARY),
                ft.Text("Ngày đăng ký", weight="bold", size=13, expand=2, color=TEXT_PRIMARY),
                ft.Text("Thao tác", weight="bold", size=13, expand=2, color=TEXT_PRIMARY),
            ])
        )
        self.data_rows_container = ft.ListView(expand=True, spacing=0)
        self.table_container = glass_card(
            expand=True,
            padding=0,
            radius=18,
            content=ft.Column([self.table_headers, self.data_rows_container], spacing=0)
        )

        # --- LOAD COUNTS TRƯỚC KHI BUILD CONTROLS ---
        total_drivers, active_sessions, new_today = self._load_counts()

        # --- LAYOUT CHÍNH ---
        self.controls = [
            section_title("Quản lý tài xế", ft.Icons.PEOPLE_ALT_ROUNDED),
            ft.Text("Đồng bộ giao diện glass với phần user, giữ nguyên các thao tác quản trị hiện có.", size=13, color=TEXT_SECONDARY),
            ft.Container(height=10),
            # 1. Stat cards
            ft.Row([
                self._stat_card(fr"{ICONS_DIR}\driver (1).png",    "Tổng số tài xế",  f"{total_drivers} Nhân sự",  ft.Icons.PEOPLE),
                self._stat_card(fr"{ICONS_DIR}\play-button (3).png","Đang hoạt động",  f"{active_sessions} Phiên",   ft.Icons.PLAY_CIRCLE),
                self._stat_card(fr"{ICONS_DIR}\website.png",        "Đăng ký mới",     f"{new_today} Hôm nay",     ft.Icons.COMPUTER),
            ], spacing=15),
            ft.Container(height=15),
            # 2. Search + Filter + Add button
            ft.Row([
                self.search_field,
                ft.Container(width=8),
                ft.Text("Bộ lọc", size=13, color=TEXT_PRIMARY),
                self.filter_dropdown,
                ft.Container(width=8),
                elevated_button("+ Thêm tài xế", on_click=lambda _: self.open_add_dialog(), kind="primary"),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=10),
            # 3. Bảng tài xế (full width)
            self.table_container,
        ]

    # ===========================================================================
    # UI HELPER
    # ===========================================================================
    def _load_counts(self):
        """Load số liệu tổng hợp từ DB để hiển thị ở stat cards"""
        total_drivers = 0
        active_sessions = 0
        new_today = 0
        try:
            from src.DAL.tai_xe_dal import lay_tat_ca_tai_xe, lay_tat_ca_phien_lai
            drivers = lay_tat_ca_tai_xe()
            total_drivers = len(drivers)
            today = datetime.now().date()
            for d in drivers:
                created = getattr(d, 'created_at', None)
                if created and hasattr(created, 'date') and created.date() == today:
                    new_today += 1
            active_sessions = len(lay_tat_ca_phien_lai())
        except Exception as ex:
            print(f"[WARN] _load_counts error: {ex}")
        return total_drivers, active_sessions, new_today

    def _stat_card(self, icon_path, title, subtitle, fallback_icon):
        return glass_card(
            expand=True, height=92, padding=12, radius=18,
            content=ft.Row([
                ft.Container(
                    width=56, height=56, border_radius=16,
                    bgcolor=ft.Colors.with_opacity(0.16, PRIMARY),
                    alignment=ft.alignment.center,
                    content=ft.Image(src=icon_path, width=34, height=34, fit=ft.ImageFit.CONTAIN,
                         error_content=ft.Icon(fallback_icon, size=28, color=PRIMARY)),
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(title, weight=ft.FontWeight.BOLD, size=14, color=TEXT_PRIMARY),
                    ft.Text(subtitle, size=12, color=TEXT_SECONDARY)
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2, expand=True)
            ])
        )

    def _action_icon(self, icon_path, fallback_icon, fallback_color, tooltip, on_click):
        return ft.Container(
            content=ft.Image(src=icon_path, width=24, height=24, fit=ft.ImageFit.CONTAIN,
                             error_content=ft.Icon(fallback_icon, size=20, color=fallback_color)),
            on_click=on_click,
            ink=True, border_radius=4, padding=4, tooltip=tooltip
        )

    # ===========================================================================
    # DATA OPERATIONS
    # ===========================================================================
    def did_mount(self):
        self.load_data()

    def on_search_change(self, e):
        self.search_query = e.control.value.lower()
        self.update_table()

    def load_data(self):
        try:
            from src.DAL.accounts_sync import get_all_driver_accounts_from_db
            rows = get_all_driver_accounts_from_db(include_inactive=True)
            self.drivers = []
            for r in rows:
                created = r.get("created_at") if isinstance(r, dict) else getattr(r, 'created_at', None)
                if created and hasattr(created, 'strftime'):
                    reg_date = created.strftime("%d/%m/%Y")
                else:
                    reg_date = str(created) if created else "—"
                self.drivers.append({
                    "driver_id":        r.get("driver_id", "") if isinstance(r, dict) else r.driver_id,
                    "username":         r.get("username", "") if isinstance(r, dict) else r.username,
                    "name":             r.get("name", "") if isinstance(r, dict) else r.name,
                    "phone":            (r.get("phone") if isinstance(r, dict) else getattr(r, "phone", "")) or "—",
                    "cccd":             "—",
                    "password":         r.get("password", "") if isinstance(r, dict) else "",
                    "registered_date":  reg_date,
                    "telegram_chat_id": (r.get("telegram_chat_id", "") if isinstance(r, dict) else getattr(r, 'telegram_chat_id', "")) or "",
                    "goi_dich_vu":      r.get("goi_dich_vu", 'Free') if isinstance(r, dict) else getattr(r, 'goi_dich_vu', 'Free'),
                })
        except Exception as e:
            print(f"Lỗi load data từ DB: {e}")
            self.drivers = []
        self.update_table()

    def update_table(self):
        self.data_rows_container.controls.clear()

        filtered = [d for d in self.drivers if
                    self.search_query in d.get("driver_id", "").lower() or
                    self.search_query in d.get("name", "").lower() or
                    self.search_query in d.get("username", "").lower()]

        for driver in filtered:
            row = ft.Container(
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))),
                content=ft.Row([
                    ft.Text(str(driver.get("driver_id", "")), expand=2, size=13, weight="bold", color=TEXT_PRIMARY),
                    ft.Text(driver.get("name", ""), expand=3, size=13, color=TEXT_PRIMARY),
                    ft.Text(driver.get("phone", "—"), expand=2, size=13, color=TEXT_SECONDARY),
                    ft.Text(driver.get("cccd", "—"), expand=2, size=13, color=TEXT_SECONDARY),
                    ft.Text(driver.get("registered_date", "—"), expand=2, size=13, color=TEXT_SECONDARY),
                    ft.Row([
                        self._action_icon(
                            fr"{ICONS_DIR}\pencil.png", ft.Icons.EDIT, ft.Colors.ORANGE,
                            "Chỉnh sửa", lambda e, d=driver: self.open_edit_dialog(d)
                        ),
                        self._action_icon(
                            fr"{ICONS_DIR}\telegram.png", ft.Icons.SEND_ROUNDED, ft.Colors.LIGHT_BLUE,
                            "Gửi tin nhắn", lambda e, d=driver: self.open_send_message_dialog(d)
                        ),
                        self._action_icon(
                            fr"{ICONS_DIR}\yellowbell.png", ft.Icons.NOTIFICATIONS, ft.Colors.AMBER,
                            "Thông báo", lambda e, d=driver: self.notify_driver(d)
                        ),
                        self._action_icon(
                            fr"{ICONS_DIR}\delete.png", ft.Icons.DELETE, ft.Colors.RED,
                            "Xóa", lambda e, d=driver: self.handle_delete_driver(d)
                        ),
                        ft.Container(
                            content=ft.Icon(ft.Icons.FACE_RETOUCHING_OFF, size=20, color=ft.Colors.PURPLE),
                            on_click=lambda e, d=driver: self.open_clear_face_dialog(d),
                            ink=True, border_radius=4, padding=4, tooltip="Xóa Face ID"
                        ),
                    ], spacing=6, expand=2)
                ])
            )
            self.data_rows_container.controls.append(row)
        self.update()

    def _build_admin_message(self, driver, raw_message):
        driver_name = html.escape((driver.get("name", "Tài xế") or "Tài xế").strip())
        driver_id = html.escape((driver.get("driver_id", "") or "").strip())
        driver_phone = html.escape((driver.get("phone", "") or "Chưa cập nhật").strip())
        safe_body = html.escape((raw_message or "").strip())
        full_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

        return f"""📩 <b>TIN NHẮN TỪ QUẢN TRỊ VIÊN</b>

👤 <b>Tài xế:</b> {driver_name}
🪪 <b>Mã tài xế:</b> {driver_id}
📞 <b>Số điện thoại:</b> {driver_phone}
⏰ <b>Thời gian:</b> {full_time}

{safe_body}"""

    def _send_driver_message(self, driver, raw_message, dialog=None):
        if not self.page:
            return

        token = self.oa_service.get_default_token()
        chat_id = (driver.get("telegram_chat_id") or "").strip()
        driver_name = driver.get("name", "Tài xế") or "Tài xế"

        if not token:
            self.page.open(ft.SnackBar(
                ft.Text("Bot Telegram chưa được cấu hình token, chưa thể gửi tin nhắn."),
                bgcolor=ft.Colors.RED,
            ))
            return

        if not chat_id or chat_id == "—":
            self.page.open(ft.SnackBar(
                ft.Text(f"Tài khoản {driver_name} chưa liên kết Telegram nên không thể gửi tin nhắn."),
                bgcolor=ft.Colors.ORANGE,
            ))
            return

        message = (raw_message or "").strip()
        if not message:
            self.page.open(ft.SnackBar(
                ft.Text("Vui lòng nhập nội dung tin nhắn trước khi gửi."),
                bgcolor=ft.Colors.RED,
            ))
            return

        tele_msg = self._build_admin_message(driver, message)

        self.page.open(ft.SnackBar(
            ft.Text(f"Đang gửi tin nhắn đến {driver_name}..."),
            bgcolor=ft.Colors.BLUE_GREY,
        ))

        try:
            result = self.oa_service.send_message(token, chat_id, tele_msg)
        except Exception as ex:
            self.page.open(ft.SnackBar(
                ft.Text(f"❌ Gửi Telegram thất bại: {ex}"),
                bgcolor=ft.Colors.RED,
            ))
            return

        if result.get("ok"):
            if dialog:
                self.page.close(dialog)
            self.page.open(ft.SnackBar(
                ft.Text(f"✅ Đã gửi tin nhắn đến {driver_name}."),
                bgcolor=ft.Colors.GREEN,
            ))
            return

        error = result.get("error") or result.get("description") or "Lỗi không xác định"
        self.page.open(ft.SnackBar(
            ft.Text(f"❌ Không gửi được Telegram cho {driver_name}: {error}"),
            bgcolor=ft.Colors.RED,
        ))

    # ===========================================================================
    # DIALOGS
    # ===========================================================================
    def open_send_message_dialog(self, driver):
        if not self.page:
            return

        driver_name = driver.get("name", "Tài xế") or "Tài xế"
        chat_id = (driver.get("telegram_chat_id") or "").strip()

        if not chat_id or chat_id == "—":
            self.page.open(ft.SnackBar(
                ft.Text(f"Tài khoản {driver_name} chưa liên kết Telegram nên không thể gửi tin nhắn."),
                bgcolor=ft.Colors.ORANGE,
            ))
            return

        message_field = ft.TextField(
            label="Nội dung tin nhắn",
            multiline=True,
            min_lines=5,
            max_lines=8,
            value=f"Xin chào {driver_name},\n\nAdmin cần bạn kiểm tra lại trạng thái tài khoản và phản hồi sớm giúp hệ thống.",
            **input_style(),
        )

        dialog = ft.AlertDialog(
            bgcolor=ft.Colors.with_opacity(0.92, "#081019"),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Row([
                ft.Icon(ft.Icons.SEND_ROUNDED, color=ft.Colors.LIGHT_BLUE),
                ft.Text("Gửi tin nhắn cho tài xế", size=18, weight="bold", color=TEXT_PRIMARY)
            ]),
            content=glass_card(
                width=420,
                padding=14,
                radius=20,
                bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                content=ft.Column([
                    ft.Text(f"Tài xế: {driver_name}", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(f"Chat ID: {chat_id}", size=12, color=TEXT_SECONDARY),
                    message_field,
                ], spacing=10, tight=True),
            ),
            actions=[
                text_button("Hủy", on_click=lambda _: self.page.close(dialog), kind="ghost"),
                elevated_button(
                    "Gửi tin nhắn",
                    icon=ft.Icons.SEND,
                    kind="primary",
                    on_click=lambda _: self._send_driver_message(driver, message_field.value, dialog),
                ),
            ]
        )
        self.page.open(dialog)

    def notify_driver(self, driver):
        if not self.page:
            return

        token = self.oa_service.get_default_token()
        chat_id = (driver.get("telegram_chat_id") or "").strip()
        driver_name = driver.get("name", "Tài xế") or "Tài xế"
        driver_id = driver.get("driver_id", "") or ""
        driver_phone = driver.get("phone", "") or "Chưa cập nhật"

        if not token:
            self.page.open(ft.SnackBar(
                ft.Text("Bot Telegram chưa được cấu hình token, chưa thể gửi thông báo."),
                bgcolor=ft.Colors.RED,
            ))
            return

        if not chat_id or chat_id == "—":
            self.page.open(ft.SnackBar(
                ft.Text(f"Tài khoản {driver_name} chưa liên kết Telegram nên không thể gửi thông báo."),
                bgcolor=ft.Colors.ORANGE,
            ))
            return

        full_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        tele_msg = f"""📢 <b>THÔNG BÁO TỪ QUẢN TRỊ VIÊN</b>

👤 <b>Tài xế:</b> {driver_name}
🪪 <b>Mã tài xế:</b> {driver_id}
📞 <b>Số điện thoại:</b> {driver_phone}
⏰ <b>Thời gian:</b> {full_time}

Admin vừa gửi thông báo kiểm tra trạng thái tài khoản của bạn.
Nếu bạn nhận được tin nhắn này, kết nối Telegram đang hoạt động bình thường."""

        self.page.open(ft.SnackBar(
            ft.Text(f"Đang gửi thông báo đến {driver_name}..."),
            bgcolor=ft.Colors.BLUE_GREY,
        ))

        try:
            result = self.oa_service.send_message(token, chat_id, tele_msg)
        except Exception as ex:
            self.page.open(ft.SnackBar(
                ft.Text(f"❌ Gửi Telegram thất bại: {ex}"),
                bgcolor=ft.Colors.RED,
            ))
            return

        if result.get("ok"):
            self.page.open(ft.SnackBar(
                ft.Text(f"✅ Đã gửi thông báo Telegram đến {driver_name}."),
                bgcolor=ft.Colors.GREEN,
            ))
            return

        error = result.get("error") or result.get("description") or "Lỗi không xác định"
        self.page.open(ft.SnackBar(
            ft.Text(f"❌ Không gửi được Telegram cho {driver_name}: {error}"),
            bgcolor=ft.Colors.RED,
        ))

    def open_add_dialog(self):
        self.selected_driver = None
        self.txt_id.value = f"TX{len(self.drivers) + 1:03d}"
        self.txt_id.read_only = False
        self.txt_id.bgcolor = ft.Colors.WHITE
        self.txt_username.value = ""
        self.txt_username.read_only = False
        self.txt_username.bgcolor = ft.Colors.WHITE
        self.txt_name.value = ""
        self.txt_phone.value = ""
        self.txt_cccd.value = ""
        self.txt_password.value = ""
        self.txt_telegram.value = ""
        self._open_form_dialog("Thêm Tài Xế Mới", ft.Icons.PERSON_ADD, ft.Colors.GREEN)

    def open_edit_dialog(self, driver):
        self.selected_driver = driver
        chat_id = driver.get("telegram_chat_id", "")
        if not chat_id and "telegram_data" in driver:
            chat_id = driver["telegram_data"].get("chat_id", "")

        self.txt_id.value = driver.get("driver_id", "")
        self.txt_id.read_only = True
        self.txt_id.bgcolor = ft.Colors.GREY_100
        self.txt_username.value = driver.get("username", "")
        self.txt_username.read_only = True
        self.txt_username.bgcolor = ft.Colors.GREY_100
        self.txt_name.value = driver.get("name", "")
        self.txt_phone.value = driver.get("phone", "")
        self.txt_cccd.value = driver.get("cccd", "")
        self.txt_password.value = driver.get("password", "")
        self.txt_telegram.value = str(chat_id)
        self._open_form_dialog("Chỉnh Sửa Tài Xế", ft.Icons.EDIT, ft.Colors.BLUE)

    def _open_form_dialog(self, title, icon, color):
        dialog = ft.AlertDialog(
            bgcolor=ft.Colors.with_opacity(0.92, "#081019"),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Row([ft.Icon(icon, color=color), ft.Text(title, size=18, weight="bold", color=TEXT_PRIMARY)]),
            content=glass_card(
                width=380,
                content=ft.Column([
                    self.txt_id,
                    self.txt_username,
                    self.txt_name,
                    self.txt_phone,
                    self.txt_cccd,
                    self.txt_password,
                    ft.Row([
                        self.txt_telegram,
                        icon_button(ft.Icons.DELETE_SWEEP, icon_color=DANGER, tooltip="Xóa Chat ID", on_click=lambda _: self._clear_chat_id())
                    ], spacing=0)
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                padding=10,
                radius=20,
                bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            ),
            actions=[
                text_button("Hủy", on_click=lambda e: self.page.close(dialog), kind="ghost"),
                elevated_button("Lưu", on_click=lambda e: self._handle_save_dialog(dialog), kind="primary")
            ]
        )
        self.page.open(dialog)

    def _clear_chat_id(self):
        self.txt_telegram.value = ""
        self.txt_telegram.update()

    def _handle_save_dialog(self, dialog):
        if not self.txt_username.value or not self.txt_name.value or not self.txt_id.value:
            self.page.open(ft.SnackBar(ft.Text("Vui lòng điền đầy đủ thông tin bắt buộc!"), bgcolor=ft.Colors.RED))
            return

        try:
            from src.DAL.tai_xe_dal import them_tai_xe, cap_nhat_tai_xe
            from src.DAL.accounts_sync import export_accounts_to_json
            if self.selected_driver:
                # Cập nhật tài xế
                cap_nhat_tai_xe(
                    username=self.txt_username.value,
                    name=self.txt_name.value or None,
                    password=self.txt_password.value or None,
                    phone=self.txt_phone.value or None,
                )
                # Cập nhật telegram_chat_id nếu có
                chat_id = self.txt_telegram.value.strip()
                if chat_id:
                    try:
                        from src.DAL.tai_xe_dal import lien_ket_telegram
                        from src.DAL.accounts_sync import export_accounts_to_json
                        lien_ket_telegram(self.txt_username.value, chat_id)
                        export_accounts_to_json()
                    except Exception:
                        pass
            else:
                # Kiểm tra ID trùng trong bộ nhớ local
                if any(d["driver_id"] == self.txt_id.value for d in self.drivers):
                    self.page.open(ft.SnackBar(ft.Text("ID này đã tồn tại!"), bgcolor=ft.Colors.RED))
                    return
                them_tai_xe(
                    driver_id=self.txt_id.value,
                    username=self.txt_username.value,
                    name=self.txt_name.value,
                    password=self.txt_password.value or "changeme",
                    phone=self.txt_phone.value or None,
                )

            export_accounts_to_json()
        except Exception as ex:
            self.page.close(dialog)
            self.page.open(ft.SnackBar(ft.Text(f"❌ Lỗi lưu DB: {ex}"), bgcolor=ft.Colors.RED))
            return

        self.page.close(dialog)
        self.page.open(ft.SnackBar(ft.Text("Đã lưu thành công!"), bgcolor=ft.Colors.GREEN))
        self.load_data()

    def handle_delete_driver(self, driver):
        def confirm_delete(ev):
            try:
                from src.DAL.accounts_sync import export_accounts_to_json
                from src.DAL.tai_xe_dal import xoa_tai_xe_theo_rang_buoc

                result = xoa_tai_xe_theo_rang_buoc(driver["driver_id"])
                if not result.get("success"):
                    raise ValueError(result.get("message") or "Xóa tài xế thất bại")

                export_accounts_to_json()
            except Exception as ex:
                self.page.close(confirm_dlg)
                self.page.open(ft.SnackBar(ft.Text(f"❌ Lỗi xóa DB: {ex}"), bgcolor=ft.Colors.RED))
                return
            self.selected_driver = None
            self.page.close(confirm_dlg)
            self.load_data()

            session_count = result.get("session_count", 0)
            message = f"Đã xóa tài xế khỏi hệ thống. Dữ liệu DB được giữ lại (phiên lái: {session_count})."

            self.page.open(ft.SnackBar(ft.Text(message), bgcolor=ft.Colors.BLUE_GREY))

        confirm_dlg = ft.AlertDialog(
            bgcolor=ft.Colors.with_opacity(0.92, "#081019"),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Text("Xác nhận xóa", color=TEXT_PRIMARY),
            content=ft.Text(
                f"Bạn có chắc muốn xóa tài xế '{driver.get('name', '')}' không?\n\n"
                "Tài xế sẽ bị xóa khỏi hệ thống (soft delete). Dữ liệu DB luôn được giữ lại để thống kê.",
                color=TEXT_SECONDARY
            ),
            actions=[
                text_button("Hủy", on_click=lambda _: self.page.close(confirm_dlg), kind="ghost"),
                elevated_button("Xóa", on_click=confirm_delete, kind="danger")
            ]
        )
        self.page.open(confirm_dlg)

    def commit_to_json(self):
        """Kept for legacy compatibility. Data is now stored in SQL DB."""
        pass

    def open_clear_face_dialog(self, driver):
        def confirm_clear(ev):
            try:
                from src.DAL.tai_xe_dal import cap_nhat_tai_xe
                cap_nhat_tai_xe(username=driver.get("username", ""), face_data="")
                # Cũng xóa khỏi accounts.json nếu tồn tại
                if os.path.exists(JSON_FILE):
                    try:
                        with open(JSON_FILE, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        changed = False
                        for acc in data.get("user_accounts", []):
                            if acc.get("driver_id") == driver.get("driver_id"):
                                if "face_data" in acc:
                                    del acc["face_data"]
                                    changed = True
                                break
                        if changed:
                            with open(JSON_FILE, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                self.page.close(dialog)
                self.page.open(ft.SnackBar(
                    ft.Text(f"✅ Đã xóa Face ID của {driver.get('name', '')}! Tài xế cần đăng ký lại."),
                    bgcolor=ft.Colors.PURPLE
                ))
                self.load_data()
            except Exception as ex:
                self.page.close(dialog)
                self.page.open(ft.SnackBar(ft.Text(f"❌ Lỗi: {ex}"), bgcolor=ft.Colors.RED))

        dialog = ft.AlertDialog(
            bgcolor=ft.Colors.with_opacity(0.92, "#081019"),
            shape=ft.RoundedRectangleBorder(radius=24),
            title=ft.Row([
                ft.Icon(ft.Icons.FACE_RETOUCHING_OFF, color=ft.Colors.PURPLE_700),
                ft.Text("Xác nhận xóa Face ID", weight="bold", color=TEXT_PRIMARY)
            ]),
            content=ft.Text(
                f"Bạn có chắc muốn xóa tài xế '{driver.get('name', '')}' không?\n\n"
                "Tài xế sẽ bị xóa khỏi hệ thống (soft delete). Dữ liệu DB luôn được giữ lại để thống kê.",
                color=TEXT_SECONDARY
            ),
            actions=[
                text_button("Hủy", on_click=lambda _: self.page.close(dialog), kind="ghost"),
                elevated_button("Xóa Face ID", on_click=confirm_clear, kind="secondary")
            ]
        )
        self.page.open(dialog)

    # --- Legacy compatibility ---
    def select_driver(self, driver):
        self.open_edit_dialog(driver)

    def show_edit_form(self, is_adding=False):
        if is_adding:
            self.open_add_dialog()

    def handle_save(self, e): pass
    def handle_delete(self, e):
        if self.selected_driver:
            self.handle_delete_driver(self.selected_driver)
    def clear_chat_id_input(self):
        self._clear_chat_id()
