import flet as ft
import threading
import time

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

        self.init_ui()

    def init_ui(self):
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
                    content=ft.Column([
                        self._create_log_item("19:35", "Cảnh báo buồn ngủ", "warning"),
                        self._create_log_item("19:36", "Cảnh báo buồn ngủ", "warning"),
                        self._create_log_item("19:37", "Không phát hiện bất thường", "success"),
                    ], scroll=ft.ScrollMode.AUTO, spacing=10)
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
        video_screen = ft.Container(
            expand=True,
            bgcolor=ft.Colors.BLACK87,
            border_radius=10,
            alignment=ft.alignment.center,
            content=ft.Stack([
                ft.Image(
                    src="https://media.istockphoto.com/id/1152600472/photo/driver-cabin-view-inside-taxi.jpg?s=612x612&w=0&k=20&c=J9QhKqQ_S0XqQ9Q9Q9Q9Q9Q9Q9Q9Q9Q9Q9Q9Q9Q9Q9Q=", 
                    fit=ft.ImageFit.COVER, width=float("inf"), height=float("inf"), opacity=0.6
                ),
                ft.Column([
                    ft.Icon(ft.Icons.VIDEOCAM_OFF, size=50, color=ft.Colors.WHITE54),
                    ft.Text("Camera Feed (Simulation)", color=ft.Colors.WHITE54)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ])
        )

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
    def start_timer(self, e):
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self._run_timer, daemon=True).start()
            e.page.update()

    def pause_timer(self, e):
        self.is_running = False

    def stop_timer(self, e):
        self.is_running = False
        self.seconds_elapsed = 0
        self.timer_text.value = "00:00:00"
        e.page.update()

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