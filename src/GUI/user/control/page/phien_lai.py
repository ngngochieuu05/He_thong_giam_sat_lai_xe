import flet as ft
import threading
import time
import json
import os
import requests
from datetime import datetime
from src.BUS.oa_core.sua_thong_bao.tuy_chinh_thong_bao import get_thong_bao_service
from src.config_loader import get_camera_index
from src.BUS.oa_core.telegram_link_service import _load_accounts
from ..ui_styles import elevated_button, icon_button

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"

class PhienLaiPage(ft.Stack):
    def __init__(self, user_account=None):
        # Đổi thành Stack và ép lề âm để tràn background
        super().__init__(expand=True)
        self.margin = ft.margin.all(-20)
        
        # --- LƯU THÔNG TIN USER HIỆN TẠI ---
        self.current_user = user_account
        
        # --- TRẠNG THÁI ---
        self.is_running = False
        self.seconds_elapsed = 0
        self.session_alerts = 0 # Đếm vi phạm trong 1 phiên lái
        
        # --- CHATBOX TRẠNG THÁI ---
        self.is_chat_open = False
        self.chat_window = None
        self.chat_history = ft.ListView(expand=True, spacing=12, padding=ft.padding.symmetric(horizontal=12, vertical=10), auto_scroll=True)
        self.is_ai_replying = False
        self.chat_send_btn = None
        self.chat_status_text = None
        self.txt_chat_input = ft.TextField(
            hint_text="Nhập tin nhắn...",
            border_radius=24, filled=True, bgcolor="#F2F4F8",
            border_color=ft.Colors.TRANSPARENT,
            text_size=14,
            expand=True, content_padding=10,
            on_submit=self.send_message
        )
        
        self.timer_text = ft.Text("00:00:00", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        
        # --- OA SERVICE ---
        self.oa_service = get_thong_bao_service()
        self.ai_api_key = self._load_groq_api_key()

        # --- DANH SÁCH NHẠC CHUÔNG ---
        self.SOUND_OPTIONS = {
            "🔔 Nhạc chuông báo thức": os.path.abspath("src/GUI/data/sound/sound_drive/nhac-chuong-bao-thuc-may-thuc-day-cho-tao-tu-sena.mp3"),
            "🎵 Dậy đi ông cháu ơi": os.path.abspath("src/GUI/data/sound/sound_drive/day di ong chau oi.mp3"),
        }
        self.selected_sound_label = list(self.SOUND_OPTIONS.keys())[0]

        self._frame_received = False
        self._frame_timeout_timer = None
        self.last_frame_time = 0
        self.camera_is_frozen = False
        self.init_ui()
        self._start_frame_timeout_checker()

    def get_current_user_chat_id(self):
        """Lấy chat_id từ DB trước, fallback sang accounts.json nếu cần."""
        if not self.current_user:
            return None
            
        username = self.current_user.get("username")
        if not username:
            return None

        try:
            from src.DAL.accounts_sync import get_driver_account_from_db
            user = get_driver_account_from_db(username)
            if user:
                tele_data = user.get("telegram_data") or {}
                if tele_data.get("chat_id"):
                    return tele_data.get("chat_id")
                if user.get("telegram_chat_id"):
                    return user.get("telegram_chat_id")
        except Exception:
            pass
            
        try:
            accounts_data = _load_accounts()
            users = accounts_data.get("user_accounts", [])
            for user in users:
                if user.get("username") == username:
                    tele_data = user.get("telegram_data")
                    if tele_data and tele_data.get("chat_id"):
                        return tele_data.get("chat_id")
        except Exception as e:
            print(f"Error getting chat_id for user {username}: {e}")
            
        return None

    def _load_groq_api_key(self):
        config_path = os.path.abspath("src/GUI/data/model_config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config = json.load(file)
            return config.get("ai_api", {}).get("groq_api_key", "").strip() or DEFAULT_GROQ_API_KEY
        except Exception as error:
            print(f"⚠️ [GROQ] Không đọc được model_config.json: {error}")
            return DEFAULT_GROQ_API_KEY

    # --- LOGIC CHATBOT GROQ ---
    def call_groq_api(self, prompt):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.ai_api_key}'
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "Bạn là trợ lý AI thông minh trên xe ô tô. Trả lời ngắn gọn, thân thiện, hữu ích bằng tiếng Việt."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.4,
            "max_tokens": 300,
        }
        try:
            response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                try:
                    return data['choices'][0]['message']['content'].strip()
                except (KeyError, IndexError):
                    return "AI không trả về nội dung."
            else:
                return f"Lỗi Groq ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Lỗi kết nối: {e}"

    def toggle_chat_window(self, e):
        self._set_chat_visible(not self.is_chat_open)

    def _set_chat_visible(self, visible: bool):
        self.is_chat_open = bool(visible)
        if self.chat_window:
            self.chat_window.visible = self.is_chat_open
            try:
                self.chat_window.update()
            except Exception:
                pass

    def send_message(self, e):
        user_text = (self.txt_chat_input.value or "").strip()
        if not user_text:
            return

        self._set_chat_visible(True)
        self.is_ai_replying = True
        if self.chat_send_btn:
            self.chat_send_btn.disabled = True
            self.chat_send_btn.icon = ft.Icons.HOURGLASS_TOP

        self.chat_history.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Text(user_text, color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.W_600),
                    bgcolor="#1E88E5",
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=ft.border_radius.only(16, 16, 4, 16),
                    width=260,
                )
            ], alignment=ft.MainAxisAlignment.END)
        )
        if self.chat_status_text:
            self.chat_status_text.value = "Đang soạn phản hồi..."
            self.chat_status_text.color = "#1E88E5"
        self.txt_chat_input.value = ""
        self.txt_chat_input.focus()
        try:
            self.chat_window.update()
        except Exception:
            pass

        full_prompt = f"Bạn là trợ lý AI thông minh trên xe ô tô. Tài xế hỏi: {user_text}. Hãy trả lời ngắn gọn, thân thiện và hữu ích bằng tiếng Việt."

        def call_ai():
            reply = self.call_groq_api(full_prompt)
            def _apply_reply():
                self._set_chat_visible(True)
                self.chat_history.controls.append(
                    ft.Row([
                        ft.Container(
                            content=ft.Text(reply, color="#1D2939", size=13, no_wrap=False),
                            bgcolor="#EEF2F7",
                            padding=ft.padding.symmetric(horizontal=12, vertical=10),
                            border_radius=ft.border_radius.only(16, 16, 16, 4),
                            width=290,
                        )
                    ], alignment=ft.MainAxisAlignment.START)
                )
                self.is_ai_replying = False
                if self.chat_send_btn:
                    self.chat_send_btn.disabled = False
                    self.chat_send_btn.icon = ft.Icons.SEND_ROUNDED
                if self.chat_status_text:
                    self.chat_status_text.value = "Sẵn sàng hỗ trợ"
                    self.chat_status_text.color = ft.Colors.WHITE70
                try:
                    self.chat_window.update()
                except Exception:
                    pass

            if self.page and hasattr(self.page, "call_from_thread"):
                try:
                    self.page.call_from_thread(_apply_reply)
                    return
                except Exception:
                    pass
            _apply_reply()

        threading.Thread(target=call_ai, daemon=True).start()

    def init_ui(self):
        # Init log list first
        self.log_list = ft.Column([
            self._create_log_item("SYSTEM", "Hệ thống sẵn sàng", "success"),
        ], scroll=ft.ScrollMode.AUTO, spacing=10)

        card_bg = ft.Colors.with_opacity(0.22, ft.Colors.BLACK)
        card_border = ft.Colors.with_opacity(0.18, ft.Colors.WHITE)
        panel_shadow = ft.BoxShadow(blur_radius=18, color=ft.Colors.BLACK38, offset=ft.Offset(0, 8))

        # ĐƯỜNG DẪN ẢNH TÀI NGUYÊN (SỬ DỤNG ĐƯỜNG DẪN TƯƠNG ĐỐI)
        IMG_BG = r"src\GUI\data\image_user\backround.jpg"
        IMG_CANH_BAO = r"src\GUI\data\image_user\canhBao.png"
        IMG_ROBOT = r"src\GUI\data\image_user\robot.png"
        IMG_TELE = r"src\GUI\data\image_user\logoTele.png"

        # --- LỚP NỀN BACKGROUND ---
        bg_image = ft.Image(src=IMG_BG, fit=ft.ImageFit.COVER, expand=True)
        bg_overlay = ft.Container(bgcolor=ft.Colors.BLACK54, expand=True, blur=10)

        # 1. CỘT TRÁI (SIDEBAR ĐIỀU KHIỂN - GIAO DIỆN MỚI)
        left_panel = ft.Container(
            width=280,
            padding=ft.padding.only(left=10, right=10, top=18, bottom=20),
            content=ft.Column([
                # Khung chọn nhạc + thời gian lái
                ft.Container(
                    bgcolor=card_bg,
                    border_radius=22,
                    padding=20,
                    height=250,
                    border=ft.border.all(1, card_border),
                    shadow=panel_shadow,
                    content=ft.Column([
                        # Dropdown chọn nhạc 
                        ft.Dropdown(
                            options=[ft.dropdown.Option(k) for k in self.SOUND_OPTIONS.keys()],
                            value=self.selected_sound_label,
                            bgcolor=ft.Colors.TRANSPARENT,
                            color=ft.Colors.WHITE,
                            border=ft.InputBorder.NONE,
                            text_size=13,
                            content_padding=8,
                            icon_enabled_color=ft.Colors.WHITE70,
                            on_change=self.on_sound_change,
                        ),
                        ft.Divider(height=1, color=ft.Colors.with_opacity(0.18, ft.Colors.WHITE)),
                        # Hiện thời gian lái
                        ft.Row([
                            ft.Text("Thời gian lái:", size=14, color=ft.Colors.WHITE, weight="bold"),
                            self.timer_text
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Row([
                            ft.Icon(ft.Icons.FAST_REWIND, color=ft.Colors.WHITE, size=30),
                            ft.Icon(ft.Icons.PAUSE, color=ft.Colors.WHITE, size=30),
                            ft.Icon(ft.Icons.FAST_FORWARD, color=ft.Colors.WHITE, size=30),
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], spacing=15)
                ),

                ft.Container(height=16),

                # C. Khu vực Thông báo
                ft.Container(
                    bgcolor=ft.Colors.with_opacity(0.22, self.PRIMARY if hasattr(self, 'PRIMARY') else ft.Colors.GREEN), 
                    padding=14, 
                    border_radius=ft.border_radius.only(top_left=18, top_right=18),
                    border=ft.border.all(1, card_border),
                    shadow=panel_shadow,
                    content=ft.Text("Thông báo", weight="bold", text_align="center", color=ft.Colors.WHITE, width=float("inf"))
                ),
                ft.Container(
                    bgcolor=card_bg, height=360, 
                    border_radius=ft.border_radius.only(bottom_left=18, bottom_right=18),
                    border=ft.border.all(1, card_border),
                    padding=14,
                    shadow=panel_shadow,
                    content=self.log_list
                ),
                
                ft.Container(expand=True), 
                
                # D. Thông báo gửi đi Telegram
                ft.Container(
                    bgcolor=card_bg, padding=ft.padding.symmetric(horizontal=15, vertical=12), border_radius=18,
                    border=ft.border.all(1, card_border),
                    shadow=panel_shadow,
                    content=ft.Row([
                        ft.Image(src=IMG_TELE, width=35, height=35),
                        ft.Text("Đã gửi cảnh báo qua Telegram", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600, expand=True)
                    ])
                )
            ])
        )

        # 2. CỘT PHẢI (VIDEO & BUTTONS)

        self.camera_error = None
        self.camera_image = ft.Image(
            src_base64=None,
            width=float("inf"),
            height=float("inf"),
            fit=ft.ImageFit.CONTAIN,
            gapless_playback=True,
            error_content=ft.Text("Không nhận được hình ảnh camera", color=ft.Colors.RED),
        )

        # Khởi động Camera Manager
        try:
            from src.BUS.ai_core.laucher_user.camera_manager import CameraManager
            self.camera_manager = CameraManager(self.update_camera_frame, self.handle_alert_callback, camera_index=get_camera_index())
            # self.camera_manager.start()  <- DI CHUYỂN SANG did_mount ĐỂ TRÁNH LỖI ĐỨNG HÌNH
        except Exception as e:
            self.camera_error = f"Lỗi import CameraManager: {e}"
            print(self.camera_error)
            self.camera_manager = None

        # Nếu có lỗi camera, hiển thị thông báo lỗi thay vì chỉ màn hình đen
        self._video_screen_container = ft.Container(
            expand=True,
            bgcolor=ft.Colors.BLACK,
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK45),
            alignment=ft.alignment.center,
            content=ft.Text("Đang khởi động camera...", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD)
        )
        if self.camera_error:
            self._video_screen_container.content = ft.Text(self.camera_error, color=ft.Colors.RED, size=16, weight=ft.FontWeight.BOLD)
        else:
            self._video_screen_container.content = ft.Stack([
                self.camera_image,
                ft.Container(
                    content=ft.Icon(ft.Icons.VOLUME_UP, color=ft.Colors.WHITE70, size=20),
                    bgcolor=ft.Colors.BLACK38,
                    padding=5,
                    border_radius=20,
                    top=15, left=15
                )
            ], expand=True)

        # --- NÚT ROBOT CHATBOX ---
        robot_btn = ft.Container(
            content=ft.Image(src=IMG_ROBOT, width=50, height=50),
            ink=True,
            on_click=self.toggle_chat_window,
            border_radius=25,
            tooltip="Mở Chatbox AI"
        )

        control_buttons = ft.Row([
            ft.Container(expand=True), 
            self._create_control_btn("Bắt đầu", ft.Icons.PLAY_ARROW, "#509F3D"),   
            self._create_control_btn("Tạm dừng", ft.Icons.PAUSE, "#FFC000"),       
            self._create_control_btn("Kết thúc", ft.Icons.CLOSE, "#F04C4C"),       
            ft.Container(expand=True), 
            robot_btn # Nút Robot ở góc cuối
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)

        right_panel = ft.Container(
            expand=True,
            padding=ft.padding.only(right=15, top=10, bottom=15),
            content=ft.Column([
                self._video_screen_container,
                ft.Container(height=5),
                control_buttons
            ])
        )

        # Container nội dung chính
        main_content = ft.Container(
            padding=ft.padding.only(left=30, right=30, top=20, bottom=20),
            expand=True,
            content=ft.Row([left_panel, right_panel], expand=True, spacing=0)
        )

        # --- UI CHATBOX ---
        self.chat_status_text = ft.Text("Sẵn sàng hỗ trợ", size=11, color=ft.Colors.WHITE70)
        self.chat_send_btn = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_color=ft.Colors.WHITE,
            bgcolor="#24B8E8",
            tooltip="Gửi tin nhắn",
            on_click=self.send_message,
        )

        self.chat_window = ft.Container(
            width=360,
            height=520,
            bgcolor="#FFFFFF",
            border_radius=22,
            border=ft.border.all(1, "#D8E3F2"),
            shadow=ft.BoxShadow(blur_radius=24, spread_radius=1, color=ft.Colors.with_opacity(0.28, ft.Colors.BLACK)),
            padding=0,
            right=34,
            bottom=84,
            visible=False, # Canh ngay phía trên con Robot
            content=ft.Column([
                ft.Container(
                    height=72,
                    padding=ft.padding.symmetric(horizontal=14),
                    gradient=ft.LinearGradient(colors=["#2E8DE7", "#2196F3"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                    border_radius=ft.border_radius.only(top_left=22, top_right=22),
                    content=ft.Row([
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.WHITE, size=22),
                        ft.Column(
                            [
                                ft.Text("Trợ lý Groq", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700, size=18),
                                self.chat_status_text,
                            ],
                            spacing=2,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
                            on_click=self.toggle_chat_window,
                            tooltip="Đóng chat",
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ),
                ft.Container(
                    expand=True,
                    bgcolor="#FFFFFF",
                    content=self.chat_history,
                ),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=10),
                    border=ft.border.only(top=ft.border.BorderSide(1, "#E6EAF0")),
                    content=ft.Row(
                        [
                            self.txt_chat_input,
                            self.chat_send_btn,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            ], spacing=0)
        )

        # --- GẮN VÀO STACK ---
        self.controls = [
            bg_image,
            bg_overlay,
            main_content,
            self.chat_window
        ]

    def _start_frame_timeout_checker(self):
        def check_timeout():
            # Chờ hệ thống ổn định lúc khởi động
            time.sleep(3)
            while True:
                # Nếu trang đã bị unmount, kết thúc luồng
                if not self.page:
                    break
                    
                current_time = time.time()
                
                # CHƯA NHẬN ĐƯỢC FRAME NÀO (KHỞI ĐỘNG)
                if not self._frame_received:
                    if self._video_screen_container:
                        self._video_screen_container.content = ft.Text(
                            "Đang chờ hình ảnh từ camera...",
                            color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
                        )
                        try:
                            self._video_screen_container.update()
                        except Exception:
                            pass
                
                # ĐÃ NHẬN FRAME NHƯNG GẦN ĐÂY BỊ ĐỨNG
                elif self._frame_received and (current_time - self.last_frame_time > 3.0):
                    if not self.camera_is_frozen:
                        self.camera_is_frozen = True
                        self.handle_alert_callback("⚠️ LỖI: Camera đang bị đứng hình!", type="warning")
                
                # Chậm lại nhịp đập của watchdog để tránh quá tải CPU
                time.sleep(3)

        self._frame_timeout_timer = threading.Thread(target=check_timeout, daemon=True)
        self._frame_timeout_timer.start()
    
    # --- ALERT LOGIC ---
    def handle_alert_callback(self, message: str, type: str = "warning", img_path: str = None):
        current_time = time.strftime("%H:%M")
        full_time = time.strftime("%H:%M:%S %d/%m/%Y")
        
        new_log = self._create_log_item(current_time, message, type)
        
        if type == "warning":
            try:
                username = self.current_user.get("username", "user01") if self.current_user else "user01"
                dashboard_file = "src/GUI/data/dashboard_data.json"
                
                dashboard_data = {"users": {}}
                if os.path.exists(dashboard_file):
                    with open(dashboard_file, "r", encoding="utf-8") as f:
                        dashboard_data = json.load(f)
                        
                if "users" not in dashboard_data:
                    dashboard_data["users"] = {}
                if username not in dashboard_data["users"]:
                    dashboard_data["users"][username] = {}
                    
                today_str = datetime.now().strftime("%Y-%m-%d")
                daily_alerts = dashboard_data["users"][username].get("daily_alerts", {})
                daily_alerts[today_str] = daily_alerts.get(today_str, 0) + 1
                dashboard_data["users"][username]["daily_alerts"] = daily_alerts
                
                dashboard_data["users"][username]["total_alerts"] = dashboard_data["users"][username].get("total_alerts", 0) + 1
                
                if self.is_running:
                    self.session_alerts += 1
                
                with open(dashboard_file, "w", encoding="utf-8") as f:
                    json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Lỗi lưu cảnh báo vào dashboard: {e}")

        if type == "warning" and self.oa_service.is_alert_enabled():
            token = self.oa_service.get_default_token()
            chat_id = self.get_current_user_chat_id()
            
            if token and chat_id:
                driver_name = self.current_user.get("name", "Unknown Driver") if self.current_user else "Unknown"
                
                tele_msg = f"""🚨 <b>CẢNH BÁO: TÀI XẾ BUỒN NGỦ!</b>

⏰ <b>Thời gian:</b> {full_time}
👤 <b>Tài xế:</b> {driver_name}
⚠️ <b>Nội dung:</b> {message}
📸 <b>Camera:</b> Dashboard (AI Detected)

<i>Hệ thống tự động phát hiện dấu hiệu buồn ngủ.</i>"""
                
                def _send_tele_alert():
                    try:
                        if img_path:
                            self.oa_service.send_photo(token, chat_id, img_path, tele_msg)
                            try:
                                import os
                                os.remove(img_path)
                                print(f"🗑️ [CLEANUP] Deleted temp image: {img_path}")
                            except Exception as e:
                                print(f"⚠️ [CLEANUP] Failed to delete temp image: {e}")
                        else:
                            self.oa_service.send_message(token, chat_id, tele_msg)
                    except Exception as e:
                        print(f"❌ [TELEGRAM] Error sending alert: {e}")

                threading.Thread(target=_send_tele_alert, daemon=True).start()
            else:
                if not chat_id:
                    print("⚠️ [TELEGRAM] Không gửi cảnh báo: Tài xế chưa liên kết Telegram")
        
        self.log_list.controls.insert(0, new_log)
        if len(self.log_list.controls) > 50:
            self.log_list.controls.pop()
            
        try:
            self.log_list.update()
        except Exception:
            pass

    # --- SOUND CHANGE HANDLER ---
    def on_sound_change(self, e):
        label = e.control.value
        if label and label in self.SOUND_OPTIONS:
            self.selected_sound_label = label
            sound_path = self.SOUND_OPTIONS[label]
            if self.camera_manager:
                self.camera_manager.set_sound_path(sound_path)

    # --- HELPERS ---
    def _create_log_item(self, time_str, msg, type_str):
        img_src = r"src\GUI\data\image_user\canhBao.png" if type_str == "warning" else r"src\GUI\data\image_user\check.png"
        
        return ft.Row([
            ft.Image(src=img_src, width=20, height=20),
            ft.Column([
                ft.Text(f"{time_str} :", weight="bold", size=12, color=ft.Colors.WHITE),
                ft.Text(msg, size=12, width=180, no_wrap=False, color=ft.Colors.WHITE70)
            ], spacing=0)
        ], vertical_alignment=ft.CrossAxisAlignment.START)

    def _create_control_btn(self, text, icon, color):
        on_click_func = None
        if text == "Bắt đầu": on_click_func = self.start_timer
        elif text == "Tạm dừng": on_click_func = self.pause_timer
        elif text == "Kết thúc": on_click_func = self.stop_timer

        accent_color = "#63D471"
        if text == "Tạm dừng":
            accent_color = "#F2C94C"
        elif text == "Kết thúc":
            accent_color = "#FF7A7A"

        return ft.ElevatedButton(
            text=text,
            icon=icon,
            on_click=on_click_func,
            height=54,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.24, ft.Colors.WHITE),
                    ft.ControlState.PRESSED: ft.Colors.with_opacity(0.30, ft.Colors.WHITE),
                    ft.ControlState.DISABLED: ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                },
                color=ft.Colors.WHITE,
                overlay_color=ft.Colors.with_opacity(0.10, accent_color),
                shadow_color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
                elevation={
                    ft.ControlState.DEFAULT: 0,
                    ft.ControlState.HOVERED: 4,
                    ft.ControlState.PRESSED: 1,
                },
                side={
                    ft.ControlState.DEFAULT: ft.BorderSide(1.2, ft.Colors.with_opacity(0.55, accent_color)),
                    ft.ControlState.HOVERED: ft.BorderSide(1.4, accent_color),
                    ft.ControlState.PRESSED: ft.BorderSide(1.4, accent_color),
                },
                padding=ft.padding.symmetric(horizontal=26, vertical=16),
                text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_700),
                shape=ft.RoundedRectangleBorder(radius=22),
            )
        )

    # --- TIMER LOGIC ---
    def start_timer(self, e):
        if not self.is_running:
            self.session_alerts = 0
            self.is_running = True
            threading.Thread(target=self._run_timer, daemon=True).start()
            if self.camera_manager:
                self.camera_manager.toggle_ai(True)
            e.page.update()

    def pause_timer(self, e):
        self.is_running = False
        if self.camera_manager:
            self.camera_manager.toggle_ai(False)

    def stop_timer(self, e):
        if self.seconds_elapsed > 0:
            self._save_driving_session()
            e.page.open(ft.SnackBar(ft.Text("Đã kết thúc và lưu phiên lái!"), bgcolor=ft.Colors.GREEN))
            
        self.is_running = False
        self.seconds_elapsed = 0
        self.timer_text.value = "00:00:00"
        if self.camera_manager:
            self.camera_manager.toggle_ai(False)
        e.page.update()

    def _save_driving_session(self):
        try:
            username = self.current_user.get("username", "user01") if self.current_user else "user01"
            dashboard_file = "src/GUI/data/dashboard_data.json"
            
            dashboard_data = {"users": {}}
            if os.path.exists(dashboard_file):
                with open(dashboard_file, "r", encoding="utf-8") as f:
                    dashboard_data = json.load(f)
                    
            if "users" not in dashboard_data:
                dashboard_data["users"] = {}
            if username not in dashboard_data["users"]:
                dashboard_data["users"][username] = {}
                
            if "driving_sessions" not in dashboard_data["users"][username]:
                dashboard_data["users"][username]["driving_sessions"] = []
                
            today_str = datetime.now().strftime("%Y-%m-%d")
            minutes = max(1, round(self.seconds_elapsed / 60))
            
            new_session = {
                "date": today_str,
                "duration_minutes": minutes,
                "alerts": self.session_alerts
            }
            
            dashboard_data["users"][username]["driving_sessions"].append(new_session)
            
            with open(dashboard_file, "w", encoding="utf-8") as f:
                json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
        except Exception as ex:
            print(f"❌ Lỗi lưu thông tin phiên lái: {ex}")

    # --- CAMERA LOGIC ---
    def update_camera_frame(self, b64_frame):
        # Nếu chưa được gắn vào trang (page is None), bỏ qua frame này
        if not self.page or not b64_frame:
            return

        try:
            self.last_frame_time = time.time()
            
            # Nếu camera vừa khởi động lại hoặc lần đầu nhận frame
            if not self._frame_received or self.camera_is_frozen:
                is_recovery = self.camera_is_frozen
                self._frame_received = True
                self.camera_is_frozen = False
                
                # Cập nhật thông báo hệ thống
                msg = "Hệ thống camera đã hoạt động trở lại" if is_recovery else "Camera đang hoạt động trơn tru"
                self.handle_alert_callback(msg, type="success")
                
                # THIẾT LẬP MÀN HÌNH VIDEO (CHỈ LÀM 1 LẦN DUY NHẤT)
                self.camera_image.src_base64 = b64_frame
                self._video_screen_container.content = ft.Stack([
                    self.camera_image,
                    ft.Container(
                        content=ft.Icon(ft.Icons.VOLUME_UP, color=ft.Colors.WHITE70, size=20),
                        bgcolor=ft.Colors.BLACK38,
                        padding=5,
                        border_radius=20,
                        top=15, left=15
                    )
                ], expand=True)
                self._video_screen_container.update()
                return

            # --- TRƯỜNG HỢP THÔNG THƯỜNG (PHẦN LỚN FRAME) ---
            # Chỉ cập nhật dữ liệu Base64, không thay đổi cấu trúc Stack/Container
            self.camera_image.src_base64 = b64_frame
            
            # Gọi update() trực tiếp trên Image là cách nhanh nhất và mượt nhất
            # Tuy nhiên thỉnh thoảng cần update Container cha để đảm bảo render (nếu đứng hình)
            self.camera_image.update()

        except Exception:
            pass

    def did_mount(self):
        super().did_mount()
        if self.camera_manager and not self.camera_manager.is_running:
            self.camera_manager.start()

    def will_unmount(self):
        super().will_unmount()
        if self.camera_manager:
            self.camera_manager.stop()

    def _run_timer(self):
        while self.is_running:
            time.sleep(1)
            self.seconds_elapsed += 1
            mins, secs = divmod(self.seconds_elapsed, 60)
            hours, mins = divmod(mins, 60)
            self.timer_text.value = "{:02d}:{:02d}:{:02d}".format(hours, mins, secs)
            try:
                self.timer_text.update()
            except:
                break
