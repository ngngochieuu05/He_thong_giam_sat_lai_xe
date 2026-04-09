import flet as ft
import requests
import threading
import time
import json

# --- CẤU HÌNH API ---
# 1. Key Gemini của bạn (Lấy từ ảnh bạn gửi)
GEMINI_API_KEY = "AIzaSyBthVtyDj_NYpu9FlUa48Y5kO2pK0CvZm0"

# 2. Gọi trực tiếp qua URL (Không dùng thư viện google-generativeai để tránh lỗi)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# 3. Key thời tiết
WEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"
CITY = "Ho Chi Minh City"

class TienIchPage(ft.Stack):
    def __init__(self):
        super().__init__(expand=True)
        
        # Trạng thái
        self.weather_context = "Chưa có dữ liệu thời tiết"
        self.is_chat_open = False 
        self.is_pro_user = False
        
        # UI Components
        self.chat_window = None
        self.chat_history = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)
        self.txt_chat_input = ft.TextField(
            hint_text="Nhập tin nhắn...",
            border_radius=20, filled=True, bgcolor=ft.Colors.GREY_100,
            expand=True, content_padding=10,
            on_submit=self.send_message
        )

        self.init_ui()
        self.load_weather_data()

    # --- HÀM GỌI GEMINI TRỰC TIẾP (REST API) ---
    def call_gemini_api(self, prompt):
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            response = requests.post(GEMINI_URL, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                # Lấy nội dung trả lời từ cấu trúc JSON của Google
                try:
                    return data['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    return "AI không trả về nội dung."
            else:
                return f"Lỗi Google ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Lỗi kết nối: {e}"

    # --- LOGIC THỜI TIẾT ---
    def load_weather_data(self):
        def fetch():
            if "YOUR_" in WEATHER_API_KEY:
                time.sleep(0.5)
                temp, desc = 32, "Nắng đẹp"
            else:
                try:
                    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
                    res = requests.get(url).json()
                    temp = int(res["main"]["temp"])
                    desc = res["weather"][0]["description"]
                except:
                    temp, desc = 0, "Không xác định"

            self.weather_context = f"Thời tiết tại {CITY}: {temp} độ C, {desc}."
            
            try:
                self.txt_temp.value = f"{temp}°C"
                self.txt_desc.value = desc
                self.txt_city.value = CITY
                self.icon_weather.name = ft.Icons.WB_SUNNY
                self.update()
            except: pass

        threading.Thread(target=fetch, daemon=True).start()

    # --- LOGIC CHATBOT ---
    def toggle_chat_window(self, e):
        self.is_chat_open = not self.is_chat_open
        self.chat_window.visible = self.is_chat_open
        self.chat_window.update()

    def send_message(self, e):
        user_text = self.txt_chat_input.value
        if not user_text: return

        # 1. Hiện tin nhắn User
        self.chat_history.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Text(user_text, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.BLUE_600, padding=10, border_radius=ft.border_radius.only(15, 15, 0, 15)
                )
            ], alignment=ft.MainAxisAlignment.END)
        )
        self.txt_chat_input.value = ""
        self.txt_chat_input.focus()
        self.chat_window.update()

        # 2. Logic gọi AI trong luồng riêng
        full_prompt = f"Bạn là trợ lý lái xe. Thông tin môi trường: {self.weather_context}. Người dùng hỏi: {user_text}. Hãy trả lời ngắn gọn, thân thiện bằng tiếng Việt."

        def call_ai():
            reply = self.call_gemini_api(full_prompt)

            # Hiện tin nhắn Bot
            self.chat_history.controls.append(
                ft.Row([
                    ft.Container(
                        content=ft.Text(reply, color=ft.Colors.BLACK87),
                        bgcolor=ft.Colors.GREY_200, padding=10, border_radius=ft.border_radius.only(15, 15, 15, 0),
                        width=280
                    )
                ], alignment=ft.MainAxisAlignment.START)
            )
            self.chat_window.update()

        threading.Thread(target=call_ai, daemon=True).start()

    # --- UI POPUPS ---
    def open_map_dialog(self, e):
        map_img_url = "https://media.wired.com/photos/59269cd37034dc5f91bec0f1/191:100/w_1280,c_limit/GoogleMapTA.jpg"
        dialog = ft.AlertDialog(
            title=ft.Text("Bản Đồ Khu Vực", text_align=ft.TextAlign.CENTER),
            content=ft.Container(
                width=500, height=300, border_radius=10, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Stack([
                    ft.Image(src=map_img_url, fit=ft.ImageFit.COVER, opacity=0.9),
                    ft.Container(alignment=ft.alignment.center, content=ft.ElevatedButton("Mở Google Maps", icon=ft.Icons.DIRECTIONS, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, on_click=lambda _: e.page.launch_url(f"https://www.google.com/maps/search/{CITY}")))
                ])
            )
        )
        e.page.dialog = dialog
        dialog.open = True
        e.page.update()

    def open_music_dialog(self, e):
        dialog = ft.AlertDialog(
            title=ft.Text("Music Player"),
            content=ft.Container(height=100, content=ft.Column([
                ft.Text("Đang phát: Lạc Trôi - Sơn Tùng MTP", weight="bold"),
                ft.Row([ft.IconButton(ft.Icons.SKIP_PREVIOUS), ft.IconButton(ft.Icons.PLAY_ARROW), ft.IconButton(ft.Icons.SKIP_NEXT)], alignment="center")
            ]))
        )
        e.page.dialog = dialog
        dialog.open = True
        e.page.update()

    def init_ui(self):
        # --- UI CHÍNH ---
        self.txt_city = ft.Text("Đang tải...", size=20, weight="bold", color=ft.Colors.WHITE)
        self.txt_temp = ft.Text("--", size=50, weight="bold", color=ft.Colors.WHITE)
        self.txt_desc = ft.Text("...", color=ft.Colors.WHITE70, size=16)
        self.icon_weather = ft.Icon(ft.Icons.CLOUD, color=ft.Colors.WHITE, size=60)

        weather_widget = ft.Container(
            gradient=ft.LinearGradient(colors=[ft.Colors.BLUE_600, ft.Colors.INDIGO_900]),
            border_radius=20, padding=30,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLUE_GREY_100),
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.LOCATION_ON, color="white"), self.txt_city]),
                ft.Container(height=10),
                ft.Row([self.icon_weather, self.txt_temp], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(alignment=ft.alignment.center, content=self.txt_desc)
            ])
        )

        def create_tool_btn(text, icon, bg_color, text_color, func):
            return ft.Container(
                content=ft.Row([ft.Icon(icon, size=30, color=text_color), ft.Text(text, size=18, weight="bold", color=ft.Colors.BLACK87)], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.Colors.WHITE, border_radius=15, padding=20, width=float("inf"), ink=True, shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12), on_click=func
            )

        main_content = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Thông Tin & Tiện Ích", size=24, weight="bold", color=ft.Colors.BLUE_GREY_800),
                weather_widget,
                ft.Container(height=20),
                ft.Text("Công Cụ Hỗ Trợ", size=18, weight="bold", color=ft.Colors.GREY_600),
                create_tool_btn("Bản Đồ & Dẫn Đường", ft.Icons.MAP, ft.Colors.GREEN_100, ft.Colors.GREEN_800, self.open_map_dialog),
                ft.Container(height=10),
                create_tool_btn("Trình Phát Nhạc", ft.Icons.MUSIC_NOTE, ft.Colors.PINK_100, ft.Colors.PINK_800, self.open_music_dialog),
            ], scroll=ft.ScrollMode.AUTO)
        )

        # --- UI CHATBOT ---
        self.chat_window = ft.Container(
            width=350, height=500, bgcolor=ft.Colors.WHITE, border_radius=20, shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26),
            padding=0, right=20, bottom=90, visible=False,
            content=ft.Column([
                ft.Container(
                    bgcolor=ft.Colors.BLUE_600, padding=15, border_radius=ft.border_radius.only(20, 20, 0, 0),
                    content=ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, color="white"), ft.Text("Trợ lý Gemini", color="white", weight="bold", size=16), ft.Container(expand=True), ft.IconButton(ft.Icons.CLOSE, icon_color="white", icon_size=20, on_click=self.toggle_chat_window)])
                ),
                self.chat_history,
                ft.Container(padding=10, border=ft.border.only(top=ft.border.BorderSide(1, ft.Colors.GREY_200)), content=ft.Row([self.txt_chat_input, ft.IconButton(ft.Icons.SEND, icon_color=ft.Colors.BLUE_600, on_click=self.send_message)]))
            ], spacing=0)
        )

        # --- NÚT FAB ---
        bot_avatar_url = "https://cdn-icons-png.flaticon.com/512/4712/4712035.png" 
        fab_chat = ft.FloatingActionButton(
            content=ft.Container(content=ft.Image(src=bot_avatar_url, fit=ft.ImageFit.CONTAIN, width=35, height=35), padding=5),
            bgcolor=ft.Colors.WHITE, on_click=self.toggle_chat_window
        )

        self.controls = [main_content, self.chat_window, ft.Container(content=fab_chat, right=20, bottom=20)]