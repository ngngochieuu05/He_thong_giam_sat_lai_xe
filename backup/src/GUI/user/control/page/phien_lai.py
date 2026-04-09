import flet as ft
import threading
import time
import json
import os
from src.BUS.oa_core.sua_thong_bao.tuy_chinh_thong_bao import get_thong_bao_service
from src.config_loader import get_camera_index

class PhienLaiPage(ft.Column):
    def __init__(self):
        super().__init__(expand=True)
        
        # --- MÀU SẮC ---
        self.BG_COLOR = "#D1E2D3"
        self.CARD_COLOR = "#E8F5E9"
        
        # --- TRẠNG THÁI ---
        self.is_running = False
        self.seconds_elapsed = 0
        self.timer_text = ft.Text("00:00:00", size=20, weight=ft.FontWeight.BOLD)

        self.timer_text = ft.Text("00:00:00", size=20, weight=ft.FontWeight.BOLD)
        
        # --- OA SERVICE ---
        self.oa_service = get_thong_bao_service()

        # --- DANH SÁCH NHẠC CHUÔNG ---
        self.SOUND_OPTIONS = {
            "🔔 Nhạc chuông báo thức": os.path.abspath("src/GUI/data/sound/sound_drive/nhac-chuong-bao-thuc-may-thuc-day-cho-tao-tu-sena.mp3"),
            "🎵 Dậy đi ông cháu ơi": os.path.abspath("src/GUI/data/sound/sound_drive/day di ong chau oi.mp3"),
        }
        self.selected_sound_label = list(self.SOUND_OPTIONS.keys())[0]

        self.init_ui()

    def init_ui(self):
        # Init log list first
        self.log_list = ft.Column([
            # Log mẫu
            self._create_log_item("SYSTEM", "Hệ thống sẵn sàng", "success"),
        ], scroll=ft.ScrollMode.AUTO, spacing=10)

        # 1. CỘT TRÁI (SIDEBAR ĐIỀU KHIỂN)
        left_panel = ft.Container(
            width=300,
            padding=10,
            content=ft.Column([
                # A. Chọn Camera
                ft.Row([ft.Icon(ft.Icons.CAMERA_ALT), ft.Text("Lựa chọn camera", weight="bold")]),
                
                ft.Dropdown(
                    options=[ft.dropdown.Option("Camera trước"), ft.dropdown.Option("Camera sau")],
                    value="Camera trước",
                    bgcolor=ft.Colors.WHITE, 
                    text_size=14, 
                    content_padding=10, 
                    border_radius=10
                ),
                
                ft.Container(height=10),

                # B1. Chọn nhạc chuông cảnh báo ngủ gật
                ft.Row([ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.TEAL_700), ft.Text("Nhạc chuông cảnh báo", weight="bold")]),
                ft.Dropdown(
                    options=[ft.dropdown.Option(k) for k in self.SOUND_OPTIONS.keys()],
                    value=self.selected_sound_label,
                    bgcolor=ft.Colors.WHITE,
                    text_size=13,
                    content_padding=10,
                    border_radius=10,
                    on_change=self.on_sound_change,
                ),

                ft.Container(height=10),

                # B. Thời gian lái
                ft.Container(
                    bgcolor=ft.Colors.WHITE, border_radius=10, padding=15,
                    border=ft.border.all(1, ft.Colors.BLACK12),
                    content=ft.Row([
                        ft.Text("Thời gian lái : ", size=14, weight="bold"),
                        self.timer_text
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ),
                ft.Container(height=10),

                ft.Container(height=10),

                # C. Khu vực Thông báo

                ft.Container(
                    bgcolor="#C8E6C9", padding=10, 
                    # [SỬA LỖI] Đổi ft.border thành ft.border_radius
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                    border=ft.border.all(1, ft.Colors.BLACK26),
                    content=ft.Text("Thông báo", weight="bold", text_align="center", color=ft.Colors.BLACK)
                ),
                ft.Container(
                    bgcolor=ft.Colors.WHITE, height=250, 
                    # [SỬA LỖI] Đổi ft.border thành ft.border_radius
                    border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10),
                    border=ft.border.all(1, ft.Colors.BLACK26),
                    padding=10,
                    content=self.log_list
                ),
                ft.Container(height=10),

                # D. Trạng thái Telegram
                ft.Container(
                    bgcolor=ft.Colors.WHITE, padding=10, border_radius=10,
                    border=ft.border.all(1, ft.Colors.BLACK12),
                    content=ft.Row([
                        ft.Text("Telegram : ", weight="bold"),
                        ft.Text("Connect", color=ft.Colors.GREEN, weight="bold")
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ),
                
                ft.Container(height=20),
                # E. Thông báo gửi đi
                ft.Container(
                    bgcolor=ft.Colors.WHITE, padding=15, border_radius=10,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
                    content=ft.Row([
                        ft.Icon(ft.Icons.MARK_EMAIL_READ, color=ft.Colors.AMBER_700),
                        ft.Text("Đã gửi cảnh báo qua Telegram", size=12, expand=True)
                    ])
                )
            ])
        )

        # 2. CỘT PHẢI (VIDEO & BUTTONS)
        self.camera_image = ft.Image(
            src="",
            src_base64=None,
            width=float("inf"),
            height=float("inf"),
            fit=ft.ImageFit.COVER, # Fill đầy khung, có thể crop nhẹ
            gapless_playback=True,
            error_content=ft.Text("Đang tải camera...", color=ft.Colors.WHITE54),
        )

        video_screen = ft.Container(
            expand=True,
            bgcolor=ft.Colors.BLACK, # Khung nền đen
            border_radius=10,
            alignment=ft.alignment.center,
            content=self.camera_image # Hiển thị camera
        )

        # Khởi động Camera Manager
        try:
            from src.BUS.ai_core.laucher_user.camera_manager import CameraManager
            # Pass thêm callback handle_alert và camera index từ config
            self.camera_manager = CameraManager(self.update_camera_frame, self.handle_alert_callback, camera_index=get_camera_index())
            self.camera_manager.start()
        except Exception as e:
            print(f"Lỗi import CameraManager: {e}")
            self.camera_manager = None

        control_buttons = ft.Row([
            self._create_control_btn("Bắt đầu", ft.Icons.PLAY_ARROW, "#8BC34A", self.start_timer),
            self._create_control_btn("Tạm dừng", ft.Icons.PAUSE, "#FFEB3B", self.pause_timer, text_color=ft.Colors.BLACK),
            self._create_control_btn("Kết thúc", ft.Icons.CLOSE, "#E57373", self.stop_timer),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)

        right_panel = ft.Container(
            expand=True,
            padding=10,
            content=ft.Column([
                video_screen,
                ft.Container(height=10),
                control_buttons,
                ft.Container(height=10),
            ])
        )

        # Thiết lập nội dung cho Column chính
        self.controls.append(
            ft.Row([left_panel, right_panel], expand=True, spacing=0)
        )
    
    # --- ALERT LOGIC ---
    def handle_alert_callback(self, message: str, type: str = "warning", img_path: str = None):
        """Callback khi nhận cảnh báo từ AI"""
        current_time = time.strftime("%H:%M")
        full_time = time.strftime("%H:%M:%S %d/%m/%Y")
        
        new_log = self._create_log_item(current_time, message, type)
        
        # Logic gửi Telegram
        if type == "warning" and self.oa_service.is_alert_enabled():
            token = self.oa_service.get_default_token()
            chat_id = self.oa_service.get_default_chat_id()
            
            if token and chat_id:
                tele_msg = f"""🚨 <b>CẢNH BÁO: TÀI XẾ BUỒN NGỦ!</b>

⏰ <b>Thời gian:</b> {full_time}
⚠️ <b>Nội dung:</b> {message}
📸 <b>Camera:</b> Dashboard (AI Detected)

<i>Hệ thống tự động phát hiện dấu hiệu buồn ngủ.</i>"""
                
                # Hàm gửi nội bộ chạy trong thread
                def _send_tele_alert():
                    try:
                        if img_path:
                            # Gửi ảnh kèm caption
                            self.oa_service.send_photo(token, chat_id, img_path, tele_msg)
                            # Xóa ảnh tạm sau khi gửi
                            try:
                                import os
                                os.remove(img_path)
                                print(f"🗑️ [CLEANUP] Deleted temp image: {img_path}")
                            except Exception as e:
                                print(f"⚠️ [CLEANUP] Failed to delete temp image: {e}")
                        else:
                            # Gửi tin nhắn text
                            self.oa_service.send_message(token, chat_id, tele_msg)
                    except Exception as e:
                        print(f"❌ [TELEGRAM] Error sending alert: {e}")

                # Chạy trong thread riêng để không block UI camera
                threading.Thread(
                    target=_send_tele_alert,
                    daemon=True
                ).start()
        
        # Thêm vào đầu danh sách (insert at 0)
        self.log_list.controls.insert(0, new_log)
        
        # Giới hạn số lượng log (ví dụ 50)
        if len(self.log_list.controls) > 50:
            self.log_list.controls.pop()
            
        try:
            self.log_list.update()
        except Exception:
            pass

    # --- SOUND CHANGE HANDLER ---
    def on_sound_change(self, e):
        """Xử lý khi người dùng chọn nhạc chuông khác"""
        label = e.control.value
        if label and label in self.SOUND_OPTIONS:
            self.selected_sound_label = label
            sound_path = self.SOUND_OPTIONS[label]
            if self.camera_manager:
                self.camera_manager.set_sound_path(sound_path)
            print(f"🎵 [UI] Người dùng chọn nhạc: {label}")

    # --- HELPERS ---
    def _create_log_item(self, time, msg, type):
        icon = ft.Icons.WARNING_AMBER if type == "warning" else ft.Icons.CHECK_CIRCLE
        color = ft.Colors.AMBER_700 if type == "warning" else ft.Colors.GREEN
        return ft.Row([
            ft.Icon(icon, color=color, size=20),
            ft.Column([
                ft.Text(f"{time} :", weight="bold", size=12),
                ft.Text(msg, size=12, width=180, no_wrap=False)
            ], spacing=0)
        ], vertical_alignment=ft.CrossAxisAlignment.START)

    def _create_control_btn(self, text, icon, color, func, text_color=ft.Colors.WHITE):
        return ft.ElevatedButton(
            text=text, icon=icon, on_click=func,
            style=ft.ButtonStyle(
                bgcolor=color, color=text_color,
                padding=ft.padding.symmetric(horizontal=30, vertical=20),
                text_style=ft.TextStyle(size=16, weight="bold"),
                shape=ft.RoundedRectangleBorder(radius=30)
            )
        )

    # --- TIMER LOGIC ---
    # --- TIMER LOGIC ---
    def start_timer(self, e):
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self._run_timer, daemon=True).start()
            # Bật AI
            if self.camera_manager:
                self.camera_manager.toggle_ai(True)
            e.page.update()

    def pause_timer(self, e):
        self.is_running = False
        # Tắt AI
        if self.camera_manager:
            self.camera_manager.toggle_ai(False)

    def stop_timer(self, e):
        self.is_running = False
        self.seconds_elapsed = 0
        self.timer_text.value = "00:00:00"
        # Tắt AI
        if self.camera_manager:
            self.camera_manager.toggle_ai(False)
        e.page.update()

    # --- CAMERA LOGIC ---
    def update_camera_frame(self, b64_frame):
        try:
            self.camera_image.src_base64 = b64_frame
            self.camera_image.update()
        except Exception:
            # Raise để CameraManager biết là UI đã đóng -> Stop loop
            raise Exception("UI_CLOSED")

    def did_mount(self):
        # Được gọi khi control được thêm vào page
        super().did_mount()
        
        if self.camera_manager and not self.camera_manager.is_running:
            self.camera_manager.start()

    def will_unmount(self):
        # Được gọi khi control bị xóa khỏi page
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