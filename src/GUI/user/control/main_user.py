import asyncio
import flet as ft
from datetime import datetime
import threading
import time
import json
import os
from pathlib import Path
import requests

MusicPlayerManager = None
_MusicPlayerManager = None

# --- IMPORT CÁC TRANG CON BẰNG ĐƯỜNG DẪN TƯƠNG ĐỐI ---
from .page.phien_lai import PhienLaiPage
from .page.cai_dat import CaiDatPage
from .page.bangdieukhien import BangDieuKhienPage
try:
    from .page.tien_ich import TienIchPage, YouTubePlayerManager, MusicPlayerManager as _MusicPlayerManager
except ImportError as e:
    print(f"Lá»—i import tien_ich.py: {e}")
    TienIchPage = None
    YouTubePlayerManager = None
    _MusicPlayerManager = None

MusicPlayerManager = _MusicPlayerManager

from .page.profile_user import ProfileUserPage
from .page.lich_su import LichSuPage 
from .ui_styles import icon_button

try:
    from src.DAL.accounts_sync import get_driver_account_from_db
except Exception:
    get_driver_account_from_db = None

JSON_FILE = "src/GUI/data/accounts.json"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
MODEL_CONFIG_PATH = PROJECT_ROOT / "src" / "GUI" / "data" / "model_config.json"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class UserApp:
    def __init__(self, page: ft.Page, go_back_callback=None, user_account=None):
        self.page = page
        self.go_back_callback = go_back_callback
        self.page.title = "Tài Xế - Driver System"
        self.page.padding = 0

        self.TEXT_COLOR = ft.Colors.WHITE

        if user_account:
            self.current_username = user_account.get("username", "user01")
            refreshed_user = self.get_user_info(self.current_username)
            self.current_user_info = {**user_account, **refreshed_user}
        else:
            self.current_username = "user01" 
            self.current_user_info = self.get_user_info(self.current_username)

        self.apply_theme_mode(self.current_user_info.get("theme_preference", "dark"), refresh=False)
        self.model_config = self._load_model_config()
        self.ai_api_key = ((self.model_config.get("ai_api") or {}).get("groq_api_key") or "").strip()

        self.menu_items = {}
        self.current_page = "dashboard"
        self.running = True
        
        # Biến trạng thái để kiểm soát Menu đang mở hay đóng
        self.is_sidebar_open = False
        
        self.time_text = ft.Text("", size=13, color=ft.Colors.WHITE)
        self.content_area = ft.Container(expand=True, padding=0) 
        
        self.page_titles = {
            "dashboard": "Bảng điều khiển",
            "session": "Phiên lái",
            "history": "Thống kê",
            "settings": "Cài đặt",
            "profile": "Tài khoản",
            "utilities": "Tiện ích"
        }

        self.header_title_text = ft.Text(self.page_titles["dashboard"], size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        self.sidebar_container = None 
        self.youtube_player_container = None
        self.youtube_player_shell = None
        self.youtube_drag_layer = None
        self.youtube_box_title = ft.Text("YouTube", size=12, color=ft.Colors.WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        self.youtube_box_subtitle = ft.Text("Sẵn sàng phát", size=10, color=ft.Colors.WHITE70)
        self.youtube_video = ft.Video(
            playlist=[],
            autoplay=False,
            show_controls=True,
            aspect_ratio=16 / 9,
            fit=ft.ImageFit.COVER,
            visible=True,
            on_loaded=self.on_youtube_video_loaded,
            on_error=self.on_youtube_video_error,
            on_completed=self.on_youtube_video_completed,
        )
        self.youtube_progress_slider = ft.Slider(
            min=0,
            max=0,
            value=0,
            expand=True,
            active_color="#FF5F5F",
            inactive_color=ft.Colors.WHITE24,
            thumb_color="#FF3B30",
            on_change=self._on_mini_youtube_slider_change,
            on_change_end=self._on_mini_youtube_slider_change_end,
        )
        self.youtube_time_current = ft.Text("0:00", size=10, color=ft.Colors.WHITE70, weight=ft.FontWeight.W_600)
        self.youtube_time_total = ft.Text("--:--", size=10, color=ft.Colors.WHITE38, weight=ft.FontWeight.W_600)
        self.youtube_slider_loop_running = False
        self.youtube_slider_user_dragging = False
        self.youtube_position_event_bound = False
        self.youtube_video_paused = False
        self.youtube_pause_button = icon_button(ft.Icons.PAUSE, on_click=self.pause_youtube_player, kind="surface", icon_size=18, tooltip="Tạm dừng/tiếp tục video")
        self.youtube_stop_button = icon_button(ft.Icons.STOP_ROUNDED, on_click=self.stop_youtube_player, kind="danger", icon_size=18, tooltip="Dừng video mini")
        self.youtube_box_left = 0
        self.youtube_box_top = 0
        self.youtube_current_stream = ""
        self.youtube_current_video_id = ""
        self.youtube_pending_seek = 0.0
        self.utilities_page = None
        self.header_avatar = None
        self.header_user_name_text = None

        # --- Chatbox State ---
        self.is_chat_open = False
        self.chat_history = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)
        self.chat_send_button = None
        self.chat_sending = False
        self.txt_chat_input = ft.TextField(
            hint_text="Nhập tin nhắn...",
            border_radius=20,
            filled=True,
            bgcolor="#F5F7FB",
            color="#0F172A",
            text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_600, color="#0F172A"),
            hint_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600, color="#64748B"),
            border_color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            expand=True, content_padding=10,
            on_submit=self.send_message
        )
        self.chat_window = None
        self.chat_window_left = 20
        self.chat_window_top = 90
        self.fab_chat_left = 20
        self.fab_chat_bottom = 20

        self.init_ui()
        self.start_clock()

        if YouTubePlayerManager:
            YouTubePlayerManager.register_listener(self.refresh_youtube_player)

        try:
            temp_db = BangDieuKhienPage(user_account=self.current_user_info)
            temp_db._record_login()
        except Exception as e:
            print(f"Lá»—i khá»Ÿi táº¡o Ä‘Äƒng nháº­p: {e}")

    def _load_model_config(self):
        try:
            if MODEL_CONFIG_PATH.exists():
                with open(MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f) or {}
        except Exception:
            pass
        return {}

    @staticmethod
    def _format_mmss(seconds: float) -> str:
        try:
            seconds = max(0, int(seconds or 0))
        except Exception:
            seconds = 0
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"

    @staticmethod
    def _normalize_video_position(raw_value: float, duration_seconds: float | None = None) -> float:
        if YouTubePlayerManager and hasattr(YouTubePlayerManager, "normalize_player_position"):
            try:
                return float(YouTubePlayerManager.normalize_player_position(raw_value, duration_seconds))
            except Exception:
                pass

        # Fallback heuristic if manager is unavailable
        try:
            raw_value = float(raw_value or 0.0)
        except Exception:
            raw_value = 0.0
        try:
            duration_seconds = float(duration_seconds or 0.0)
        except Exception:
            duration_seconds = 0.0
        if duration_seconds > 0 and raw_value > max(1200.0, duration_seconds * 10.0):
            return max(0.0, raw_value / 1000.0)
        if duration_seconds <= 0 and raw_value > 60000.0:
            return max(0.0, raw_value / 1000.0)
        return max(0.0, raw_value)

    def _youtube_raw_from_seconds(self, seconds: float) -> float:
        seconds = max(0.0, float(seconds or 0.0))
        if YouTubePlayerManager and hasattr(YouTubePlayerManager, "position_scale"):
            try:
                scale = getattr(YouTubePlayerManager, "position_scale", None)
                if scale is not None and float(scale) > 0:
                    return seconds / float(scale)
            except Exception:
                pass
        return seconds

    def _infer_youtube_scale_if_needed(self, duration_seconds: float | None = None):
        if not YouTubePlayerManager or not hasattr(YouTubePlayerManager, "set_position_scale"):
            return
        try:
            if getattr(YouTubePlayerManager, "position_scale", None) is not None:
                return
        except Exception:
            pass
        try:
            raw = float(self.youtube_video.get_current_position() or 0.0)
        except Exception:
            return
        try:
            duration_seconds = float(duration_seconds or 0.0)
        except Exception:
            duration_seconds = 0.0
        if raw <= 0:
            return
        if duration_seconds > 0 and raw > max(1200.0, duration_seconds * 10.0):
            YouTubePlayerManager.set_position_scale(0.001)
        elif duration_seconds <= 0 and raw > 60000.0:
            YouTubePlayerManager.set_position_scale(0.001)
        else:
            YouTubePlayerManager.set_position_scale(1.0)

    def _maybe_set_youtube_position_scale_from_raw(self, raw_value: float, duration_seconds: float):
        if not YouTubePlayerManager or not hasattr(YouTubePlayerManager, "set_position_scale"):
            return
        try:
            if getattr(YouTubePlayerManager, "position_scale", None) is not None:
                return
        except Exception:
            pass

        try:
            raw_value = float(raw_value or 0.0)
        except Exception:
            raw_value = 0.0
        if raw_value <= 0:
            return

        normalized = self._normalize_video_position(raw_value, duration_seconds=duration_seconds)
        if normalized <= 0:
            return

        scale_guess = normalized / raw_value
        # Snap to the two realistic modes
        scale = 0.001 if scale_guess < 0.01 else 1.0
        try:
            YouTubePlayerManager.set_position_scale(scale)
        except Exception:
            pass

    def _youtube_jump_to_seconds(self, seconds: float):
        if YouTubePlayerManager:
            try:
                duration = float(YouTubePlayerManager.get_state().get("duration") or 0.0)
            except Exception:
                duration = 0.0
            self._infer_youtube_scale_if_needed(duration)
        raw = self._youtube_raw_from_seconds(seconds)
        try:
            self.youtube_video.jump_to(raw)
        except Exception:
            pass

    def _detect_youtube_position_scale(self):
        if not YouTubePlayerManager or not hasattr(YouTubePlayerManager, "set_position_scale"):
            return
        # If already detected, don't re-run.
        try:
            if getattr(YouTubePlayerManager, "position_scale", None) is not None:
                return
        except Exception:
            pass

        def worker():
            try:
                p1 = float(self.youtube_video.get_current_position() or 0.0)
                time.sleep(1.0)
                p2 = float(self.youtube_video.get_current_position() or 0.0)
            except Exception:
                return

            delta = max(0.0, p2 - p1)
            # ~1s elapsed: if delta is huge, raw unit is milliseconds
            scale = 0.001 if delta > 10.0 else 1.0
            try:
                YouTubePlayerManager.set_position_scale(scale)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()
    def toggle_chat_window(self, e=None):
        self.is_chat_open = not self.is_chat_open
        if self.chat_window:
            self.chat_window.visible = self.is_chat_open
            self.chat_window.update()

    def send_message(self, e=None):
        if self.chat_sending:
            return
        msg = self.txt_chat_input.value.strip()
        if not msg:
            return
        self.chat_history.controls.append(ft.Text(f"Bạn: {msg}", size=14, color="#0F172A"))
        self.txt_chat_input.value = ""
        self.chat_history.update()
        self.txt_chat_input.update()
        self._set_chat_sending(True)
        self.page.run_task(self._ai_reply_task, msg)

    def _set_chat_sending(self, sending: bool):
        self.chat_sending = bool(sending)
        if self.chat_send_button:
            self.chat_send_button.icon = ft.Icons.HOURGLASS_TOP if self.chat_sending else ft.Icons.SEND
            self.chat_send_button.disabled = self.chat_sending
            try:
                self.chat_send_button.update()
            except Exception:
                pass

    def _call_groq_api(self, prompt: str) -> str:
        api_key = (self.ai_api_key or "").strip()
        if not api_key:
            # Reload on-demand in case admin has updated it while app is running
            self.model_config = self._load_model_config()
            self.ai_api_key = ((self.model_config.get("ai_api") or {}).get("groq_api_key") or "").strip()
            api_key = (self.ai_api_key or "").strip()
        if not api_key:
            return "Chưa cấu hình Groq API key (Admin → Quản lý dữ liệu/OA)."

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Bạn là trợ lý của hệ thống giám sát lái xe. "
                        "Chỉ trả lời các câu hỏi liên quan đến thời tiết, giao thông, lộ trình, an toàn lái xe, "
                        "bản đồ và tính năng của hệ thống. Nếu ngoài phạm vi, từ chối ngắn gọn và gợi ý chủ đề phù hợp."
                    ),
                },
                {"role": "user", "content": prompt or ""},
            ],
            "temperature": 0.4,
            "max_tokens": 300,
        }

        try:
            response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=25)
            if response.status_code != 200:
                return f"Lỗi Groq ({response.status_code})."
            data = response.json() or {}
            return (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip() or "AI không trả về nội dung."
        except Exception as ex:
            return f"Lỗi kết nối: {ex}"

    async def _ai_reply_task(self, msg: str):
        reply = await asyncio.to_thread(self._call_groq_api, msg)
        self.chat_history.controls.append(ft.Text(f"AI: {reply}", size=14, color="#2563EB"))
        try:
            self.chat_history.update()
        except Exception:
            pass

        self._set_chat_sending(False)

        # Auto-close chatbox after responding to save space
        self.is_chat_open = False
        if self.chat_window:
            self.chat_window.visible = False
            try:
                self.chat_window.update()
            except Exception:
                pass


    def get_user_info(self, username):
        default_user = {"name": "Tài xế", "driver_id": "N/A", "username": username, "plan": "Free"}
        json_user = None
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
                            json_user = dict(u)
                            break
            except Exception as e:
                print(f"Lỗi đọc JSON User: {e}")

        db_user = None
        if get_driver_account_from_db:
            try:
                db_user = get_driver_account_from_db(username)
            except Exception as e:
                print(f"Lỗi đọc DB User: {e}")

        merged_user = dict(default_user)
        if json_user:
            merged_user.update(json_user)
        if db_user:
            merged_user.update(db_user)

        if "plan" not in merged_user:
            merged_user["plan"] = merged_user.get("goi_dich_vu") or "Free"
        return merged_user

    def _resolve_avatar_src(self, avatar_path):
        if not avatar_path:
            return "https://avatars.githubusercontent.com/u/1?v=4"
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

    def reload_sidebar_data(self):
        self.current_user_info = self.get_user_info(self.current_username)
        if self.header_avatar:
            self.header_avatar.content.src = self._resolve_avatar_src(self.current_user_info.get("avatar"))
        if self.header_user_name_text:
            self.header_user_name_text.value = self.current_user_info.get("name", "User")
        if hasattr(self, 'sidebar_inner'):
            self.sidebar_inner.content = self.build_sidebar_column()
            self.sidebar_inner.update()
        try:
            if self.header_avatar:
                self.header_avatar.update()
            if self.header_user_name_text:
                self.header_user_name_text.update()
        except Exception:
            pass

    def apply_theme_mode(self, theme_name, refresh=True):
        normalized = (theme_name or "dark").lower()
        is_light = normalized == "light"
        self.page.theme_mode = ft.ThemeMode.LIGHT if is_light else ft.ThemeMode.DARK
        self.TEXT_COLOR = "#0F172A" if is_light else ft.Colors.WHITE

        if hasattr(self, "header_title_text"):
            self.header_title_text.color = self.TEXT_COLOR
        if hasattr(self, "time_text"):
            self.time_text.color = self.TEXT_COLOR

        if hasattr(self, "sidebar_inner"):
            self.sidebar_inner.content = self.build_sidebar_column()
            try:
                self.sidebar_inner.update()
            except Exception:
                pass

        if refresh:
            try:
                self.page.update()
            except Exception:
                pass

    def start_clock(self):
        def update_time():
            while self.running:
                now = datetime.now()
                self.time_text.value = now.strftime("%d/%m/%Y  %H:%M")
                try:
                    self.time_text.update()
                except:
                    break
                time.sleep(1)
        threading.Thread(target=update_time, daemon=True).start()

    def go_to_page(self, page_name):
        class DummyEvent:
            pass
        e = DummyEvent()
        e.control = ft.Container(data=page_name)
        self.switch_page(e)

    def switch_page(self, e):
        selected_page = e.control.data

        self.sync_active_youtube_position(target_page=selected_page)

        if self.current_page in self.menu_items:
            self.menu_items[self.current_page].bgcolor = ft.Colors.TRANSPARENT
            self.menu_items[self.current_page].update()

        self.current_page = selected_page

        if selected_page in self.menu_items:
            self.menu_items[selected_page].bgcolor = ft.Colors.with_opacity(0.3, ft.Colors.WHITE)
            self.menu_items[selected_page].update()

        self.header_title_text.value = self.page_titles.get(selected_page, "Tài Xế")
        self.header_title_text.update()

        try:
            content = None
            if selected_page == "dashboard":
                content = BangDieuKhienPage(user_account=self.current_user_info, switch_page_callback=self.go_to_page)
            elif selected_page == "session":
                if not hasattr(self, "session_page"):
                    self.session_page = PhienLaiPage(user_account=self.current_user_info)
                content = self.session_page
            elif selected_page == "utilities":
                if TienIchPage:
                    if self.utilities_page is None:
                        self.utilities_page = TienIchPage(user_account=self.current_user_info)
                    content = self.utilities_page
                else:
                    content = ft.Text("Chưa tìm thấy file tien_ich.py", color="red")
            elif selected_page == "settings":
                content = CaiDatPage(
                    page=self.page,
                    current_username=self.current_username,
                    on_plan_changed=self.reload_sidebar_data,
                    current_theme=self.page.theme_mode.value,
                    on_theme_changed=self.apply_theme_mode,
                )
            elif selected_page == "profile":
                content = ProfileUserPage(user_account=self.current_user_info, on_update_sidebar=self.reload_sidebar_data)
            elif selected_page == "history":
                content = LichSuPage(user_account=self.current_user_info)

            if content is None:
                raise Exception(f"Không thể khởi tạo giao diện cho trang '{selected_page}'!")
            self.content_area.content = content
        except Exception as ex:
            import traceback
            tb = traceback.format_exc()
            self.content_area.content = ft.Column([
                ft.Text("LỖI GIAO DIỆN! Không thể hiển thị trang này.", color="red", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(str(ex), color="red", size=16),
                ft.Text(tb, color="red", size=12, max_lines=10),
                ft.ElevatedButton("Quay lại Dashboard", on_click=lambda e: self.go_to_page("dashboard"))
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.content_area.update()
        if selected_page == "utilities" and self.utilities_page:
            try:
                self.utilities_page.refresh_selected_youtube()
            except Exception:
                pass
        self.refresh_youtube_player()

        # TỰ ĐỘNG THU GỌN MENU SAU KHI CHỌN TRANG
        if self.is_sidebar_open:
            self.toggle_sidebar(None)

    def create_menu_item(self, text, page_name):
        def _on_hover(e):
            if self.current_page != page_name:
                e.control.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
                e.control.update()

        item = ft.Container(
            content=ft.Row([
                ft.Text(text, color=self.TEXT_COLOR, size=16, weight=ft.FontWeight.W_600)
            ]),
            padding=ft.padding.only(left=25, top=12, bottom=12), 
            margin=ft.margin.symmetric(horizontal=10, vertical=2), 
            border_radius=10,
            ink=True,
            on_click=self.switch_page, data=page_name,
            on_hover=_on_hover,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.WHITE) if page_name == "dashboard" else ft.Colors.TRANSPARENT 
        )
        self.menu_items[page_name] = item
        return item

    def handle_logout(self, e):
        self.running = False
        if YouTubePlayerManager:
            YouTubePlayerManager.unregister_listener(self.refresh_youtube_player)
        if self.go_back_callback:
            self.page.controls.clear()
            self.page.update()
            self.go_back_callback()
        else:
            self.page.open(ft.SnackBar(ft.Text("Đã đăng xuất!"), bgcolor=ft.Colors.RED))

    def build_sidebar_column(self):
        user_avatar = self._resolve_avatar_src(self.current_user_info.get("avatar"))
        return ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE, size=24),
                    padding=ft.padding.only(left=15, top=20),
                    on_click=self.handle_logout,
                    ink=True,
                    tooltip="Đăng Xuất"
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Icon(ft.Icons.CLOSE, color=ft.Colors.WHITE, size=24),
                    padding=ft.padding.only(right=15, top=20),
                    on_click=self.toggle_sidebar,
                    ink=True,
                    tooltip="Đóng Menu"
                ),
            ]),
            ft.Container(
                padding=ft.padding.only(top=5, bottom=5), 
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.CircleAvatar(
                        content=ft.Image(src=user_avatar, fit=ft.ImageFit.COVER, width=84, height=84),
                        radius=42,
                        bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
                    ),
                    ft.Container(height=5),
                    ft.Text("Driver PANEL", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=18)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            
            ft.Container(
                content=ft.Divider(color=ft.Colors.WHITE24, height=1, thickness=1),
                padding=ft.padding.symmetric(horizontal=20, vertical=10)
            ),
            
            self.create_menu_item("Bảng điều khiển", "dashboard"),
            self.create_menu_item("Tiện ích", "utilities"),       
            self.create_menu_item("Phiên lái", "session"),
            self.create_menu_item("Thống kê", "history"),     
            
            ft.Container(height=10),
            self.create_menu_item("Cài đặt", "settings"),
            ft.Container(expand=True), 
        ], spacing=0)

    # --- HÀM ẨN/HIỆN THANH MENU DỰA TRÊN NÚT BẤM ---
    def toggle_sidebar(self, e):
        # Đảo ngược trạng thái mở/đóng
        self.is_sidebar_open = not self.is_sidebar_open
        
        if self.is_sidebar_open: 
            self.sidebar_container.width = 250
            self.sidebar_container.bgcolor = ft.Colors.with_opacity(0.3, ft.Colors.BLACK) 
            self.sidebar_container.shadow = ft.BoxShadow(blur_radius=30, color=ft.Colors.BLACK54, offset=ft.Offset(5, 0))
            self.sidebar_container.blur = 20 
            
            self.sidebar_inner.opacity = 1
            self.sidebar_inner.visible = True
        else: 
            # Ẩn đi hoàn toàn bằng chiều rộng 0 thay vì 15 như trước
            self.sidebar_container.width = 0 
            self.sidebar_container.bgcolor = ft.Colors.TRANSPARENT
            self.sidebar_container.shadow = None
            self.sidebar_container.blur = 0
            
            self.sidebar_inner.opacity = 0
            self.sidebar_inner.visible = False

        self.sidebar_container.update()
        self.sidebar_inner.update()

    def toggle_mini_player_music(self, e):
        if MusicPlayerManager:
            MusicPlayerManager.toggle_play()

    def stop_mini_player_music(self, e):
        if MusicPlayerManager:
            MusicPlayerManager.stop_music()

    def refresh_mini_player(self):
        if not self.mini_player_container or not MusicPlayerManager:
            return

        state = MusicPlayerManager.get_state()
        should_show = state["song_loaded"] and self.current_page not in {"utilities", "session"}
        self.mini_player_container.visible = should_show
        if should_show:
            self.mini_player_title.value = state["title"]
            self.mini_player_subtitle.value = "Đang phát" if state["is_playing"] else "Đã tạm dừng"
            self.mini_player_play_button.icon = ft.Icons.PAUSE if state["is_playing"] else ft.Icons.PLAY_ARROW

        try:
            self.mini_player_container.update()
            self.mini_player_title.update()
            self.mini_player_subtitle.update()
            self.mini_player_play_button.update()
        except Exception:
            pass

    def build_mini_player(self):
        self.mini_player_play_button.on_click = self.toggle_mini_player_music
        return ft.Container(
            visible=False,
            right=20,
            bottom=20,
            width=320,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.BLACK),
            border=ft.border.all(1, ft.Colors.with_opacity(0.18, ft.Colors.WHITE)),
            shadow=ft.BoxShadow(blur_radius=18, color=ft.Colors.BLACK54, offset=ft.Offset(0, 8)),
            content=ft.Row([
                ft.Container(
                    width=38,
                    height=38,
                    border_radius=19,
                    bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.WHITE, size=20),
                ),
                ft.Column([
                    self.mini_player_title,
                    self.mini_player_subtitle,
                ], spacing=2, expand=True),
                self.mini_player_play_button,
                icon_button(ft.Icons.STOP_ROUNDED, on_click=self.stop_mini_player_music, kind="danger", icon_size=20, tooltip="Tắt nhạc"),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

    def _youtube_default_position(self):
        width = 360
        height = 300
        page_width = max(float(getattr(self.page, "window_width", 0) or 0), float(getattr(self.page, "width", 0) or 0), 1280.0)
        page_height = max(float(getattr(self.page, "window_height", 0) or 0), float(getattr(self.page, "height", 0) or 0), 800.0)
        left = max(0, page_width - width - 18)
        top = max(90, page_height - height - 28)
        return left, top, width, height

    def _clamp_youtube_position(self, left: float, top: float, width: float, height: float):
        page_width = max(float(getattr(self.page, "window_width", 0) or 0), float(getattr(self.page, "width", 0) or 0), 1280.0)
        page_height = max(float(getattr(self.page, "window_height", 0) or 0), float(getattr(self.page, "height", 0) or 0), 800.0)
        max_left = max(0, page_width - width - 18)
        max_top = max(72, page_height - height - 12)
        return max(0, min(left, max_left)), max(72, min(top, max_top))

    def sync_active_youtube_position(self, target_page: str | None = None):
        if not YouTubePlayerManager:
            return

        state = YouTubePlayerManager.get_state()
        previous_position = float(state.get("playback_position") or 0.0)
        duration = float(state.get("duration") or 0.0)

        if self.current_page == "utilities" and self.utilities_page:
            # Khi rời tab Tiện ích, tránh gọi get_current_position() của embedded player
            # vì có thể gây block ngắn làm lag chuyển trang.
            if target_page and target_page != "utilities":
                return
            try:
                self.utilities_page.sync_youtube_state_to_manager()
            except Exception:
                pass
            return

        if not self.youtube_current_stream:
            return

        try:
            raw = float(self.youtube_video.get_current_position() or 0.0)
            position_seconds = self._normalize_video_position(raw, duration_seconds=duration)
        except Exception:
            position_seconds = 0.0
        if position_seconds > 0.5 or previous_position <= 0.5:
            YouTubePlayerManager.set_playback_position(max(position_seconds, previous_position))

    def _youtube_seek_relative(self, delta_seconds: float):
        if not YouTubePlayerManager:
            return
        state = YouTubePlayerManager.get_state()
        duration = float(state.get("duration") or 0.0)

        # Prefer the player's actual position (normalized), then fall back to manager state.
        try:
            raw = float(self.youtube_video.get_current_position() or 0.0)
            position = self._normalize_video_position(raw, duration_seconds=duration)
        except Exception:
            position = float(state.get("playback_position") or 0.0)

        new_pos = max(0.0, position + float(delta_seconds or 0))
        if duration > 0:
            new_pos = min(new_pos, duration)
        self._youtube_jump_to_seconds(new_pos)
        YouTubePlayerManager.set_playback_position(new_pos)

    def youtube_prev_video(self, e):
        if not YouTubePlayerManager:
            return
        ok, message = YouTubePlayerManager.play_prev()
        if not ok and message:
            self.youtube_box_subtitle.value = message
            try:
                self.youtube_box_subtitle.update()
            except Exception:
                pass

    def youtube_next_video(self, e):
        if not YouTubePlayerManager:
            return
        ok, message = YouTubePlayerManager.play_next()
        if not ok and message:
            self.youtube_box_subtitle.value = message
            try:
                self.youtube_box_subtitle.update()
            except Exception:
                pass

    def on_youtube_pan_update(self, e):
        if not self.youtube_player_container or not self.youtube_player_shell:
            return
        left = float(self.youtube_player_container.left or 0) + e.delta_x
        top = float(self.youtube_player_container.top or 0) + e.delta_y
        width = float(self.youtube_player_shell.width or 360)
        height = float(self.youtube_player_shell.height or 250)
        left, top = self._clamp_youtube_position(left, top, width, height)
        self.youtube_player_container.left = left
        self.youtube_player_container.top = top
        if YouTubePlayerManager:
            YouTubePlayerManager.set_position(left, top)
        try:
            self.youtube_player_container.update()
        except Exception:
            pass

    def open_utilities_from_youtube(self, e):
        self.go_to_page("utilities")

    def close_youtube_player(self, e):
        self._stop_mini_youtube_slider_loop()
        self.youtube_video_paused = False
        self._refresh_mini_youtube_pause_icon()
        if YouTubePlayerManager:
            YouTubePlayerManager.close()
        try:
            self.youtube_video.pause()
            self.youtube_video.stop()
        except Exception:
            pass
        self.youtube_current_stream = ""
        self.youtube_current_video_id = ""
        try:
            self._clear_youtube_playlist()
        except Exception:
            pass
        if self.youtube_player_container:
            self.youtube_player_container.visible = False
            try:
                self.youtube_player_container.update()
            except Exception:
                pass

    def pause_youtube_player(self, e):
        if not self.youtube_video:
            return
        duration = 0.0
        if YouTubePlayerManager:
            try:
                duration = float(YouTubePlayerManager.get_state().get("duration") or 0.0)
            except Exception:
                duration = 0.0

        try:
            raw = float(self.youtube_video.get_current_position() or 0.0)
            current_position = self._normalize_video_position(raw, duration_seconds=duration)
        except Exception:
            current_position = 0.0

        if self.youtube_video_paused:
            try:
                self.youtube_video.play()
            except Exception:
                pass
            self.youtube_video_paused = False
            if YouTubePlayerManager:
                YouTubePlayerManager.mark_play_started()
                YouTubePlayerManager.set_paused(False)
        else:
            try:
                self.youtube_video.pause()
            except Exception:
                pass
            self.youtube_video_paused = True
            if YouTubePlayerManager:
                YouTubePlayerManager.set_paused(True)

        if YouTubePlayerManager:
            YouTubePlayerManager.set_playback_position(current_position)
        self._refresh_mini_youtube_pause_icon()

    def stop_youtube_player(self, e):
        self.youtube_video_paused = False
        self._refresh_mini_youtube_pause_icon()
        self.close_youtube_player(e)

    def _on_mini_youtube_slider_change(self, e):
        # While user drags, we stop syncing so slider doesn't "snap back".
        self.youtube_slider_user_dragging = True
        if not YouTubePlayerManager:
            return
        state = YouTubePlayerManager.get_state()
        duration = float(state.get("duration") or 0.0)
        if duration <= 0:
            return
        pos = max(0.0, min(float(e.control.value or 0.0), duration))
        self.youtube_time_current.value = self._format_mmss(pos)
        try:
            self.youtube_time_current.update()
        except Exception:
            pass

    def _on_mini_youtube_slider_change_end(self, e):
        self.youtube_slider_user_dragging = False
        if not YouTubePlayerManager:
            return
        state = YouTubePlayerManager.get_state()
        duration = float(state.get("duration") or 0.0)
        if duration <= 0:
            return
        pos = max(0.0, min(float(e.control.value or 0), duration))
        self._youtube_jump_to_seconds(pos)
        YouTubePlayerManager.set_playback_position(pos)
        # Keep paused state consistent; seeking shouldn't unpause.
        if YouTubePlayerManager:
            YouTubePlayerManager.set_paused(bool(self.youtube_video_paused))
        self.youtube_time_current.value = self._format_mmss(pos)
        try:
            self.youtube_time_current.update()
        except Exception:
            pass

    def _update_mini_youtube_slider(self):
        if not self.youtube_progress_slider or not YouTubePlayerManager:
            return
        if self.youtube_slider_user_dragging:
            return
        state = YouTubePlayerManager.get_state()
        duration = max(0.0, float(state.get("duration") or 0))
        manager_position = max(0.0, float(state.get("playback_position") or 0.0))
        self.youtube_progress_slider.disabled = duration <= 0

        # Use real player position when possible to keep slider/buttons accurate.
        position = 0.0
        try:
            raw = float(self.youtube_video.get_current_position() or 0.0)
            position = self._normalize_video_position(raw, duration_seconds=duration)
            # Only sync back when drift is noticeable to avoid listener storms.
            if position > 0.0 and abs(position - manager_position) > 1.5:
                YouTubePlayerManager.set_playback_position(position)
        except Exception:
            position = manager_position

        self.youtube_progress_slider.max = duration
        self.youtube_progress_slider.value = min(position, duration) if duration > 0 else 0.0
        self.youtube_time_current.value = self._format_mmss(position)
        self.youtube_time_total.value = self._format_mmss(duration) if duration > 0 else "--:--"
        try:
            self.youtube_progress_slider.update()
            self.youtube_time_current.update()
            self.youtube_time_total.update()
        except Exception:
            pass

    def _start_mini_youtube_slider_loop(self):
        if self.youtube_slider_loop_running:
            return
        self.youtube_slider_loop_running = True

        def loop():
            while self.youtube_slider_loop_running:
                if not self.youtube_player_container or not self.youtube_player_container.visible or not YouTubePlayerManager:
                    break
                self._update_mini_youtube_slider()
                time.sleep(0.8)
            self.youtube_slider_loop_running = False

        threading.Thread(target=loop, daemon=True).start()

    def _stop_mini_youtube_slider_loop(self):
        self.youtube_slider_loop_running = False

    def _refresh_mini_youtube_pause_icon(self):
        if not hasattr(self, "youtube_pause_button") or not self.youtube_pause_button:
            return
        self.youtube_pause_button.icon = ft.Icons.PLAY_ARROW if self.youtube_video_paused else ft.Icons.PAUSE
        try:
            self.youtube_pause_button.update()
        except Exception:
            pass

    def _toggle_youtube_controls(self, e):
        show = str(getattr(e, "data", "")) == "true"
        if not hasattr(self, "youtube_controls_overlay") or not self.youtube_controls_overlay:
            return
        self.youtube_controls_overlay.visible = show
        try:
            self.youtube_controls_overlay.update()
        except Exception:
            pass

    def on_youtube_video_error(self, e):
        self.youtube_box_subtitle.value = "Không phát được video trong player"
        try:
            self.youtube_box_subtitle.update()
        except Exception:
            pass

    def on_youtube_video_loaded(self, e):
        try:
            if self.youtube_pending_seek > 0.5:
                self._youtube_jump_to_seconds(self.youtube_pending_seek)
            self.youtube_video.play()
            self.youtube_pending_seek = 0.0
            if YouTubePlayerManager:
                YouTubePlayerManager.mark_play_started()
                YouTubePlayerManager.set_paused(False)
            try:
                duration = float(YouTubePlayerManager.get_state().get("duration") or 0.0) if YouTubePlayerManager else 0.0
                raw_now = float(self.youtube_video.get_current_position() or 0.0)
                self._maybe_set_youtube_position_scale_from_raw(raw_now, duration_seconds=duration)
            except Exception:
                pass
            self._detect_youtube_position_scale()
        except Exception:
            pass

    def on_youtube_duration_change(self, e):
        try:
            duration = float(getattr(e.control, "duration", 0.0) or 0.0)
        except Exception:
            duration = 0.0
        if YouTubePlayerManager and hasattr(YouTubePlayerManager, "lock"):
            try:
                with YouTubePlayerManager.lock:
                    YouTubePlayerManager.current_video["duration"] = duration
            except Exception:
                pass
        if self.youtube_progress_slider:
            self.youtube_progress_slider.max = duration
        if self.youtube_time_total:
            self.youtube_time_total.value = self._format_mmss(duration) if duration > 0 else "--:--"
        try:
            self.youtube_progress_slider.update()
            self.youtube_time_total.update()
        except Exception:
            pass

    def on_youtube_position_change(self, e):
        if not YouTubePlayerManager:
            return
        try:
            raw = float(getattr(e, "data", 0.0) or 0.0)
        except Exception:
            raw = 0.0
        try:
            duration = float(YouTubePlayerManager.get_state().get("duration") or 0.0)
        except Exception:
            duration = 0.0
        self._maybe_set_youtube_position_scale_from_raw(raw, duration_seconds=duration)
        position = self._normalize_video_position(raw, duration_seconds=duration)
        YouTubePlayerManager.set_playback_position(position)
        if self.youtube_slider_user_dragging:
            return
        if self.youtube_progress_slider:
            self.youtube_progress_slider.max = duration
            self.youtube_progress_slider.value = min(position, duration) if duration > 0 else 0.0
        if self.youtube_time_current:
            self.youtube_time_current.value = self._format_mmss(position)
        if self.youtube_time_total:
            self.youtube_time_total.value = self._format_mmss(duration) if duration > 0 else "--:--"
        try:
            self.youtube_progress_slider.update()
            self.youtube_time_current.update()
            self.youtube_time_total.update()
        except Exception:
            pass

    def on_youtube_video_completed(self, e):
        if not YouTubePlayerManager:
            return
        if not YouTubePlayerManager.can_auto_advance():
            return
        YouTubePlayerManager.set_playback_position(0.0)
        ok, message = YouTubePlayerManager.play_next()
        if not ok:
            self.youtube_box_subtitle.value = message
            try:
                self.youtube_box_subtitle.update()
            except Exception:
                pass

    def _clear_youtube_playlist(self):
        playlist = self.youtube_video.playlist
        if playlist is None:
            return
        playlist.clear()

    def _set_youtube_media(self, stream_url: str, http_headers=None):
        playlist = self.youtube_video.playlist
        if playlist is None:
            return
        playlist.clear()
        playlist.append(
            ft.VideoMedia(
                resource=stream_url,
                http_headers=http_headers or None,
            )
        )

    def refresh_youtube_player(self):
        if not self.youtube_player_container or not YouTubePlayerManager:
            return

        state = YouTubePlayerManager.get_state()
        visible = (
            self.current_page != "utilities"
            and bool(state.get("visible"))
            and bool(state.get("stream_url") or state.get("loading"))
        )
        self.youtube_player_container.visible = visible

        if not visible:
            self._stop_mini_youtube_slider_loop()
            try:
                self.youtube_video.pause()
                self.youtube_video.update()
            except Exception:
                pass
            try:
                self.youtube_progress_slider.max = 0
                self.youtube_progress_slider.value = 0
                self.youtube_progress_slider.update()
            except Exception:
                pass
            try:
                self.youtube_player_container.update()
            except Exception:
                pass
            return

        default_left, default_top, width, height = self._youtube_default_position()
        left = state.get("left", 0) or default_left
        top = state.get("top", 0) or default_top
        left, top = self._clamp_youtube_position(left, top, width, height)

        self.youtube_player_container.left = left
        self.youtube_player_container.top = top
        self.youtube_player_shell.width = width
        self.youtube_player_shell.height = height

        title = state.get("title") or "YouTube"
        channel = state.get("channel") or "YouTube"
        if state.get("loading"):
            subtitle = "Đang tải video..."
        else:
            subtitle = channel if self.current_page == "utilities" else "Mini YouTube"

        self.youtube_box_title.value = title
        self.youtube_box_subtitle.value = subtitle

        video_id = state.get("video_id") or ""
        if state.get("loading") and video_id and video_id != self.youtube_current_video_id:
            self.youtube_current_video_id = video_id
            self.youtube_current_stream = ""
            self._clear_youtube_playlist()
            try:
                self.youtube_video.stop()
                self.youtube_video.update()
            except Exception:
                pass

        stream_url = state.get("stream_url") or ""
        if stream_url and stream_url != self.youtube_current_stream:
            self.youtube_current_video_id = video_id
            self.youtube_current_stream = stream_url
            self._set_youtube_media(stream_url, state.get("http_headers"))
            try:
                self.youtube_pending_seek = max(0.0, float(state.get("playback_position") or 0.0))
                self.youtube_video.update()
                self.youtube_video_paused = False
                self._refresh_mini_youtube_pause_icon()
            except Exception as ex:
                self.youtube_box_subtitle.value = f"Lỗi phát video: {ex}"
                try:
                    self.youtube_box_subtitle.update()
                except Exception:
                    pass
        elif stream_url and self.youtube_player_container.visible:
            try:
                self.youtube_video.play()
                self.youtube_video_paused = False
                self._refresh_mini_youtube_pause_icon()
            except Exception:
                pass

        self._update_mini_youtube_slider()
        if not self.youtube_position_event_bound:
            self._start_mini_youtube_slider_loop()

        try:
            self.youtube_player_shell.update()
            self.youtube_player_container.update()
        except Exception:
            pass

    def build_youtube_player(self):
        header = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.BLACK),
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED, color="#FF3B30", size=18),
                    ft.Column([self.youtube_box_title, self.youtube_box_subtitle], spacing=0, expand=True),
                    icon_button(ft.Icons.SKIP_PREVIOUS, on_click=self.youtube_prev_video, kind="surface", icon_size=16, tooltip="Trước"),
                    icon_button(ft.Icons.REPLAY_10, on_click=lambda e: self._youtube_seek_relative(-10), kind="surface", icon_size=16, tooltip="Tua -10s"),
                    icon_button(ft.Icons.FORWARD_10, on_click=lambda e: self._youtube_seek_relative(10), kind="surface", icon_size=16, tooltip="Tua +10s"),
                    icon_button(ft.Icons.SKIP_NEXT, on_click=self.youtube_next_video, kind="surface", icon_size=16, tooltip="Sau"),
                    self.youtube_stop_button,
                    icon_button(ft.Icons.APPS_ROUNDED, on_click=self.open_utilities_from_youtube, kind="surface", icon_size=18, tooltip="Mở tab Tiện ích"),
                    icon_button(ft.Icons.CLOSE, on_click=self.close_youtube_player, kind="danger", icon_size=18, tooltip="Đóng"),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.youtube_controls_overlay = ft.Container(
            visible=False,
            left=0,
            top=0,
            right=0,
            height=56,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.MOVE,
                drag_interval=16,
                on_pan_update=self.on_youtube_pan_update,
                content=header,
            ),
        )

        self.youtube_player_shell = ft.Container(
            width=320,
            height=300,
            border_radius=22,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=ft.Colors.with_opacity(0.96, ft.Colors.BLACK),
            border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
            shadow=ft.BoxShadow(blur_radius=26, color=ft.Colors.with_opacity(0.55, ft.Colors.RED), offset=ft.Offset(0, 10)),
            on_hover=lambda e: self._toggle_youtube_controls(e),
            content=ft.Stack(
                [
                    ft.Container(
                        expand=True,
                        bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.RED),
                        shadow=ft.BoxShadow(blur_radius=120, color=ft.Colors.with_opacity(0.25, ft.Colors.RED), offset=ft.Offset(0, 0)),
                    ),
                    ft.Container(
                        expand=True,
                        bgcolor=ft.Colors.BLACK,
                        content=ft.Stack(
                            [
                                ft.Container(expand=True, alignment=ft.alignment.center, content=self.youtube_video),
                            ],
                            expand=True,
                        ),
                    ),
                    self.youtube_controls_overlay,
                ],
                expand=True,
            ),
        )

        self.youtube_player_container = ft.Container(
            visible=False,
            left=900,
            top=110,
            content=self.youtube_player_shell,
        )
        return self.youtube_player_container

    # --- Chatbox and UI helpers ---
    @staticmethod
    def _chat_icon_button(icon, on_click=None, kind="surface", icon_size=20, tooltip=None):
        return ft.IconButton(
            icon=icon,
            icon_size=icon_size,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor="#E0E7EF" if kind == "surface" else ("#2563EB" if kind == "secondary" else "#F87171"),
                color="#2563EB" if kind == "surface" else ("#FFF" if kind == "secondary" else "#FFF"),
                overlay_color="#CBD5E1",
            ),
            tooltip=tooltip,
            on_click=on_click,
        )

    def _drag_chat_window(self, e):
        self.chat_window_left = max(0, self.chat_window_left + (e.delta_x or 0))
        self.chat_window_top = max(0, self.chat_window_top + (e.delta_y or 0))
        if self.chat_window:
            self.chat_window.left = self.chat_window_left
            self.chat_window.top = self.chat_window_top
            try:
                self.chat_window.update()
            except Exception:
                pass

    def _drag_fab_chat(self, e):
        self.fab_chat_left = max(0, self.fab_chat_left + (e.delta_x or 0))
        self.fab_chat_bottom = max(0, self.fab_chat_bottom - (e.delta_y or 0))
        if hasattr(self, 'fab_chat_container') and self.fab_chat_container:
            self.fab_chat_container.left = self.fab_chat_left
            self.fab_chat_container.bottom = self.fab_chat_bottom
            try:
                self.fab_chat_container.update()
            except Exception:
                pass

    def init_ui(self):
        user_avatar = self._resolve_avatar_src(self.current_user_info.get("avatar"))
        user_name = self.current_user_info.get("name", "User")

        # Nút Menu 3 gạch
        hamburger_btn = icon_button(ft.Icons.MENU, on_click=self.toggle_sidebar, kind="surface", tooltip="Mở Menu Điều Hướng")
        self.header_avatar = ft.CircleAvatar(content=ft.Image(src=user_avatar, fit=ft.ImageFit.COVER, width=44, height=44), radius=22)
        self.header_user_name_text = ft.Text(user_name, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

        # --- 1. HEADER TRONG SUỐT & ĐỔ BÓNG ---
        header = ft.Container(
            height=65, 
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), # Nền kính mờ
            blur=15, 
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE))),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 5)),
            content=ft.Row([
                ft.Container(
                    expand=1,
                    alignment=ft.alignment.center_left,
                    content=ft.Row([
                        hamburger_btn, # Chèn nút 3 gạch vào đầu header
                        ft.Container(
                            content=self.header_avatar,
                            on_click=self.switch_page,
                            data="profile",
                            ink=True,
                            tooltip="Đổi tài khoản / Xem hồ sơ"
                        ),
                        ft.Column([
                            self.header_user_name_text,
                            ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=18, color=ft.Colors.WHITE)
                        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
                    ], spacing=10)
                ),
                ft.Container(
                    expand=1,
                    alignment=ft.alignment.center,
                    content=self.header_title_text
                ),
                ft.Container(
                    expand=1,
                    alignment=ft.alignment.center_right,
                    content=self.time_text
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, expand=True),
            padding=ft.padding.symmetric(horizontal=20),
        )

        # --- 2. SIDEBAR TÀNG HÌNH & TRƯỢT RA ---
        self.sidebar_inner = ft.Container(
            width=250,
            content=self.build_sidebar_column(),
            animate_opacity=200, 
            opacity=0, 
            visible=False 
        )

        self.sidebar_container = ft.Container(
            width=0, # Mặc định chiều rộng 0 để giấu hoàn toàn
            bgcolor=ft.Colors.TRANSPARENT,
            clip_behavior=ft.ClipBehavior.HARD_EDGE, 
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE), 
            content=self.sidebar_inner,
            left=0, top=0, bottom=0, 
        )

        # Gói Header và Content chính lại
        content_wrapper = ft.Column([
            header,
            self.content_area
        ], expand=True, spacing=0)

        # --- 3. GHÉP BẰNG STACK ---

        header_row = ft.Container(
            bgcolor=ft.Colors.BLUE_600, padding=15, border_radius=ft.border_radius.only(20, 20, 0, 0),
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, color="white"),
                ft.Text("Trợ lý Groq", color="white", weight=ft.FontWeight.BOLD, size=16),
                ft.Container(expand=True),
                self._chat_icon_button(ft.Icons.CLOSE, on_click=self.toggle_chat_window, kind="ghost", icon_size=20)
            ])
        )

        self.chat_send_button = self._chat_icon_button(ft.Icons.SEND, on_click=self.send_message, kind="secondary")

        self.chat_window = ft.Container(
            width=350, height=500, bgcolor=ft.Colors.WHITE, border_radius=20, shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26),
            padding=0, left=self.chat_window_left, top=self.chat_window_top, visible=False,
            content=ft.Column([
                ft.GestureDetector(
                    mouse_cursor=ft.MouseCursor.MOVE,
                    on_pan_update=self._drag_chat_window,
                    content=header_row,
                ),
                self.chat_history,
                ft.Container(
                    padding=10,
                    border=ft.border.only(top=ft.border.BorderSide(1, ft.Colors.GREY_300)),
                    content=ft.Row(
                        [
                            self.txt_chat_input,
                            self.chat_send_button,
                        ]
                    ),
                ),
            ], spacing=0)
        )

        fab_chat = ft.Container(
            width=64,
            height=64,
            border_radius=32,
            bgcolor=ft.Colors.BLUE_600,
            shadow=ft.BoxShadow(blur_radius=18, color=ft.Colors.BLACK26),
            ink=True,
            on_click=self.toggle_chat_window,
            content=ft.Stack([
                ft.Container(
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.SMART_TOY_ROUNDED, color=ft.Colors.WHITE, size=30),
                ),
                ft.Container(
                    right=6,
                    top=6,
                    width=12,
                    height=12,
                    border_radius=6,
                    bgcolor=ft.Colors.AMBER_400,
                ),
            ])
        )

        fab_drag = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.MOVE,
            on_pan_update=self._drag_fab_chat,
            content=fab_chat,
        )

        self.fab_chat_container = ft.Container(content=fab_drag, left=self.fab_chat_left, bottom=self.fab_chat_bottom)
        layout = ft.Stack([
            content_wrapper,
            self.sidebar_container,
            self.build_youtube_player(),
            self.chat_window,
            self.fab_chat_container,
        ], expand=True)

        self.youtube_player_container = layout.controls[2]

        self.content_area.content = BangDieuKhienPage(
            user_account=self.current_user_info,
            switch_page_callback=self.go_to_page
        )
        self.page.add(layout)
        self.refresh_youtube_player()

def main(page: ft.Page):
    UserApp(page)

if __name__ == "__main__":
    ft.app(target=main)
