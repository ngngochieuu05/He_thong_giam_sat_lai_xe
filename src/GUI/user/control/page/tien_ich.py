import flet as ft
import requests
import threading
import time
import json
import os
import shutil
from pathlib import Path
from ..ui_styles import elevated_button, text_button, icon_button

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    yt_dlp = None
    YT_DLP_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_POPULAR_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_VIDEO_BASE = "https://www.youtube.com/watch?v="
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_CITY = "Ho Chi Minh City"
SUPPORTED_EXT = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
WEATHER_REFRESH_INTERVAL_SECONDS = 15
OPENWEATHER_ICON_MAP = {
    "01d": (ft.Icons.WB_SUNNY, ft.Colors.AMBER_400),
    "01n": (ft.Icons.NIGHTS_STAY, ft.Colors.BLUE_GREY_100),
    "02d": (ft.Icons.WB_CLOUDY, ft.Colors.WHITE),
    "02n": (ft.Icons.WB_CLOUDY, ft.Colors.BLUE_GREY_100),
    "03d": (ft.Icons.CLOUD, ft.Colors.WHITE),
    "03n": (ft.Icons.CLOUD, ft.Colors.BLUE_GREY_100),
    "04d": (ft.Icons.CLOUD, ft.Colors.BLUE_GREY_100),
    "04n": (ft.Icons.CLOUD, ft.Colors.BLUE_GREY_100),
    "09d": (ft.Icons.WATER_DROP, ft.Colors.LIGHT_BLUE_200),
    "09n": (ft.Icons.WATER_DROP, ft.Colors.LIGHT_BLUE_200),
    "10d": (ft.Icons.UMBRELLA, ft.Colors.LIGHT_BLUE_200),
    "10n": (ft.Icons.UMBRELLA, ft.Colors.LIGHT_BLUE_200),
    "11d": (ft.Icons.THUNDERSTORM, ft.Colors.AMBER_200),
    "11n": (ft.Icons.THUNDERSTORM, ft.Colors.AMBER_200),
    "13d": (ft.Icons.AC_UNIT, ft.Colors.WHITE),
    "13n": (ft.Icons.AC_UNIT, ft.Colors.WHITE),
    "50d": (ft.Icons.FOGGY, ft.Colors.BLUE_GREY_100),
    "50n": (ft.Icons.FOGGY, ft.Colors.BLUE_GREY_100),
}


class MusicPlayerManager:
    playlist = []
    current_song_index = 0
    is_playing = False
    song_loaded = False
    song_length = 0
    playback_offset = 0.0
    playback_started_at = None
    slider_update_thread = None
    listeners = []
    initialized = False
    lock = threading.RLock()
    music_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
    music_folder = os.path.join(music_dir, "music")

    @classmethod
    def initialize(cls):
        with cls.lock:
            if not cls.initialized and PYGAME_AVAILABLE:
                try:
                    pygame.mixer.init()
                except Exception as error:
                    print("Lỗi khởi tạo pygame mixer:", error)
                cls.initialized = True
            cls.load_music_library()

    @classmethod
    def load_music_library(cls):
        json_path = os.path.join(cls.music_dir, "music_library.json")
        title_by_filename = {}
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                title_by_filename = {
                    song.get("filename", ""): song.get("title", "")
                    for song in data.get("songs", [])
                }
        except Exception as error:
            print(f"Lỗi đọc {json_path}: {error}")

        playlist = []
        music_path = Path(cls.music_folder)
        if music_path.exists():
            for file_path in sorted(music_path.iterdir()):
                if file_path.suffix.lower() not in {".mp3", ".wav", ".ogg"}:
                    continue
                playlist.append({
                    "title": title_by_filename.get(file_path.name) or file_path.stem,
                    "filename": file_path.name,
                })

        cls.playlist = playlist

    @classmethod
    def save_music_library(cls, songs):
        json_path = os.path.join(cls.music_dir, "music_library.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as file:
            json.dump({"songs": songs}, file, ensure_ascii=False, indent=2)

    @classmethod
    def add_music_files(cls, files):
        cls.initialize()
        os.makedirs(cls.music_folder, exist_ok=True)

        existing_titles = {}
        json_path = os.path.join(cls.music_dir, "music_library.json")
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                for song in data.get("songs", []):
                    existing_titles[song.get("filename", "")] = song.get("title", "")
        except Exception:
            pass

        added = 0
        for picked_file in files or []:
            ext = os.path.splitext(picked_file.name)[1].lower()
            if ext not in SUPPORTED_EXT:
                continue

            destination = os.path.join(cls.music_folder, picked_file.name)
            if not os.path.exists(destination):
                try:
                    shutil.copy2(picked_file.path, destination)
                except Exception:
                    continue

            if picked_file.name not in existing_titles:
                existing_titles[picked_file.name] = os.path.splitext(picked_file.name)[0]
                added += 1

        songs = [
            {"title": title or Path(filename).stem, "filename": filename}
            for filename, title in sorted(existing_titles.items())
        ]
        cls.save_music_library(songs)
        cls.load_music_library()
        cls.notify_listeners()
        return added

    @classmethod
    def register_listener(cls, callback):
        with cls.lock:
            if callback not in cls.listeners:
                cls.listeners.append(callback)

    @classmethod
    def unregister_listener(cls, callback):
        with cls.lock:
            if callback in cls.listeners:
                cls.listeners.remove(callback)

    @classmethod
    def notify_listeners(cls):
        callbacks = list(cls.listeners)
        for callback in callbacks:
            try:
                callback()
            except Exception:
                continue

    @classmethod
    def get_current_song(cls):
        if not cls.playlist:
            return None
        return cls.playlist[cls.current_song_index]

    @classmethod
    def get_current_song_path(cls):
        song = cls.get_current_song()
        if not song:
            return None
        return os.path.join(cls.music_folder, song.get("filename", ""))

    @classmethod
    def get_song_duration(cls, file_path):
        if not PYGAME_AVAILABLE or not file_path or not os.path.exists(file_path):
            return 0
        try:
            return max(1, int(pygame.mixer.Sound(file_path).get_length()))
        except Exception:
            return 0

    @classmethod
    def get_current_position(cls):
        if cls.is_playing and cls.playback_started_at is not None:
            elapsed = time.monotonic() - cls.playback_started_at
            return min(cls.song_length, cls.playback_offset + max(0.0, elapsed))
        return min(cls.song_length, cls.playback_offset)

    @classmethod
    def get_state(cls):
        song = cls.get_current_song() or {}
        return {
            "title": song.get("title", "Tổng hợp nhạc remix 2026"),
            "filename": song.get("filename", ""),
            "is_playing": cls.is_playing,
            "song_loaded": cls.song_loaded,
            "song_length": cls.song_length,
            "current_position": cls.get_current_position(),
        }

    @classmethod
    def start_slider_loop(cls):
        if cls.slider_update_thread is None or not cls.slider_update_thread.is_alive():
            cls.slider_update_thread = threading.Thread(target=cls.slider_loop, daemon=True)
            cls.slider_update_thread.start()

    @classmethod
    def slider_loop(cls):
        while True:
            time.sleep(0.4)
            if not cls.song_loaded:
                continue
            cls.notify_listeners()
            if cls.is_playing and cls.song_length and cls.get_current_position() >= max(0, cls.song_length - 1):
                cls.next_song()
                time.sleep(0.2)

    @classmethod
    def play_song(cls, index=None, start_position=0.0):
        cls.initialize()
        if not PYGAME_AVAILABLE or not cls.playlist:
            return

        if index is not None:
            cls.current_song_index = index % len(cls.playlist)

        file_path = cls.get_current_song_path()
        song = cls.get_current_song() or {}
        if not file_path or not os.path.exists(file_path):
            return

        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(start=max(0.0, start_position))
            cls.song_length = song.get("duration") or cls.get_song_duration(file_path) or 300
            cls.playback_offset = max(0.0, start_position)
            cls.playback_started_at = time.monotonic()
            cls.song_loaded = True
            cls.is_playing = True
            cls.start_slider_loop()
            cls.notify_listeners()
        except Exception as error:
            print("Lỗi Play:", error)

    @classmethod
    def pause_music(cls):
        if not PYGAME_AVAILABLE or not cls.song_loaded or not cls.is_playing:
            return
        pygame.mixer.music.pause()
        cls.playback_offset = cls.get_current_position()
        cls.playback_started_at = None
        cls.is_playing = False
        cls.notify_listeners()

    @classmethod
    def resume_music(cls):
        if not PYGAME_AVAILABLE or not cls.song_loaded:
            return
        pygame.mixer.music.unpause()
        cls.playback_started_at = time.monotonic()
        cls.is_playing = True
        cls.start_slider_loop()
        cls.notify_listeners()

    @classmethod
    def toggle_play(cls):
        if not PYGAME_AVAILABLE:
            return
        if cls.is_playing:
            cls.pause_music()
        else:
            if not cls.song_loaded:
                cls.play_song()
            else:
                cls.resume_music()

    @classmethod
    def seek_to(cls, position_seconds):
        if not PYGAME_AVAILABLE or not cls.song_loaded:
            return
        file_path = cls.get_current_song_path()
        if not file_path or not os.path.exists(file_path):
            return

        was_playing = cls.is_playing
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(start=position_seconds)
            cls.playback_offset = position_seconds
            if was_playing:
                cls.playback_started_at = time.monotonic()
                cls.is_playing = True
            else:
                pygame.mixer.music.pause()
                cls.playback_started_at = None
                cls.is_playing = False
            cls.notify_listeners()
        except Exception as error:
            print("Lỗi khi tua nhạc:", error)

    @classmethod
    def next_song(cls):
        if not cls.playlist:
            return
        cls.current_song_index = (cls.current_song_index + 1) % len(cls.playlist)
        cls.play_song()

    @classmethod
    def prev_song(cls):
        if not cls.playlist:
            return
        cls.current_song_index = (cls.current_song_index - 1) % len(cls.playlist)
        cls.play_song()

    @classmethod
    def stop_music(cls):
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        cls.is_playing = False
        cls.song_loaded = False
        cls.song_length = 0
        cls.playback_offset = 0.0
        cls.playback_started_at = None
        cls.notify_listeners()


class YouTubePlayerManager:
    listeners = []
    lock = threading.RLock()    # Some Flet targets return/expect milliseconds for `Video.get_current_position()`/`jump_to()`.
    # `position_scale` converts raw units -> seconds. (ms => 0.001, seconds => 1.0)
    position_scale = None
    current_video = {
        "video_id": "",
        "title": "",
        "channel": "",
        "thumbnail": "",
        "stream_url": "",
        "web_url": "",
        "http_headers": {},
        "visible": False,
        "loading": False,
        "error": "",
        "playback_position": 0.0,
        "playback_anchor_position": 0.0,
        "playback_updated_at": 0.0,
        "play_started_at": 0.0,
        "duration": 0.0,
        "paused": False,
    }
    queue = []
    queue_index = -1
    left = 0
    top = 0

    @classmethod
    def register_listener(cls, callback):
        with cls.lock:
            if callback not in cls.listeners:
                cls.listeners.append(callback)

    @classmethod
    def unregister_listener(cls, callback):
        with cls.lock:
            if callback in cls.listeners:
                cls.listeners.remove(callback)

    @classmethod
    def notify_listeners(cls):
        callbacks = list(cls.listeners)
        for callback in callbacks:
            try:
                callback()
            except Exception:
                continue

    @classmethod
    def get_state(cls):
        with cls.lock:
            state = dict(cls.current_video)
            anchor_position = float(state.get("playback_anchor_position") or state.get("playback_position") or 0.0)
            updated_at = float(state.get("playback_updated_at") or 0.0)
            if state.get("stream_url") and not state.get("loading") and not state.get("paused") and updated_at > 0:
                elapsed = max(0.0, time.time() - updated_at)
                state["playback_position"] = max(float(state.get("playback_position") or 0.0), anchor_position + elapsed)
            state["left"] = cls.left
            state["top"] = cls.top
            state["queue_index"] = cls.queue_index
            return state

    @classmethod
    def set_position_scale(cls, scale: float | None):
        with cls.lock:
            if scale is None:
                cls.position_scale = None
                return
            try:
                scale = float(scale)
            except Exception:
                return
            if scale <= 0:
                return
            cls.position_scale = scale

    @classmethod
    def normalize_player_position(cls, raw_value: float, duration_seconds: float | None = None) -> float:
        try:
            raw_value = float(raw_value or 0.0)
        except Exception:
            raw_value = 0.0

        with cls.lock:
            scale = cls.position_scale

        if scale is not None:
            return max(0.0, raw_value * float(scale))

        # Heuristic fallback when scale is unknown
        try:
            duration_seconds = float(duration_seconds or 0.0)
        except Exception:
            duration_seconds = 0.0

        if duration_seconds > 0 and raw_value > max(1200.0, duration_seconds * 10.0):
            return max(0.0, raw_value / 1000.0)
        if duration_seconds <= 0 and raw_value > 60000.0:
            return max(0.0, raw_value / 1000.0)
        return max(0.0, raw_value)

    @classmethod
    def set_queue(cls, items, current_video_id: str = ""):
        filtered_items = []
        for item in items or []:
            video_id = (item or {}).get("video_id", "")
            if not video_id:
                continue
            filtered_items.append({
                "video_id": video_id,
                "title": item.get("title", "YouTube"),
                "channel": item.get("channel", "YouTube"),
                "thumbnail": item.get("thumbnail", ""),
            })

        with cls.lock:
            cls.queue = filtered_items
            if not filtered_items:
                cls.queue_index = -1
            elif current_video_id:
                cls.queue_index = next((index for index, item in enumerate(filtered_items) if item.get("video_id") == current_video_id), 0)
            else:
                cls.queue_index = 0

    @classmethod
    def set_playback_position(cls, position_seconds):
        with cls.lock:
            position_seconds = max(0.0, float(position_seconds or 0.0))
            cls.current_video["playback_position"] = position_seconds
            cls.current_video["playback_anchor_position"] = position_seconds
            cls.current_video["playback_updated_at"] = time.time()
        cls.notify_listeners()

    @classmethod
    def set_paused(cls, paused: bool):
        with cls.lock:
            cls.current_video["paused"] = bool(paused)
            # Freeze anchor at current known position
            cls.current_video["playback_anchor_position"] = max(0.0, float(cls.current_video.get("playback_position") or 0.0))
            cls.current_video["playback_updated_at"] = time.time()
        cls.notify_listeners()

    @classmethod
    def mark_play_started(cls):
        with cls.lock:
            cls.current_video["play_started_at"] = time.time()
            cls.current_video["playback_anchor_position"] = max(0.0, float(cls.current_video.get("playback_position") or 0.0))
            cls.current_video["playback_updated_at"] = time.time()
            cls.current_video["paused"] = False

    @classmethod
    def can_auto_advance(cls, min_elapsed_seconds: float = 3.0):
        with cls.lock:
            started_at = float(cls.current_video.get("play_started_at") or 0.0)
        return started_at > 0 and (time.time() - started_at) >= min_elapsed_seconds

    @classmethod
    def play_next(cls):
        with cls.lock:
            if not cls.queue:
                return False, "Không còn video tiếp theo."

            next_index = cls.queue_index + 1
            if next_index >= len(cls.queue):
                return False, "Đã phát hết danh sách đề xuất."

            cls.queue_index = next_index
            next_item = dict(cls.queue[next_index])

        return cls.load_video(next_item, start_position=0.0)

    @classmethod
    def play_prev(cls):
        with cls.lock:
            if not cls.queue:
                return False, "Không còn video trước đó."

            prev_index = cls.queue_index - 1
            if prev_index < 0:
                return False, "Đã ở video đầu tiên."

            cls.queue_index = prev_index
            prev_item = dict(cls.queue[prev_index])

        return cls.load_video(prev_item, start_position=0.0)

    @classmethod
    def set_position(cls, left: float, top: float):
        with cls.lock:
            cls.left = max(0, left)
            cls.top = max(0, top)
        cls.notify_listeners()

    @classmethod
    def close(cls):
        with cls.lock:
            cls.current_video.update({
                "stream_url": "",
                "visible": False,
                "loading": False,
                "error": "",
                "playback_position": 0.0,
                "playback_anchor_position": 0.0,
                "playback_updated_at": 0.0,
                "play_started_at": 0.0,
                "paused": False,
            })
        cls.notify_listeners()

    @classmethod
    def load_video(cls, item: dict, start_position: float = 0.0):
        video_id = (item or {}).get("video_id", "")
        if not video_id:
            return False, "Thiếu video_id YouTube."

        web_url = f"{YOUTUBE_VIDEO_BASE}{video_id}"
        with cls.lock:
            if cls.queue:
                matched_index = next((index for index, row in enumerate(cls.queue) if row.get("video_id") == video_id), -1)
                if matched_index >= 0:
                    cls.queue_index = matched_index

            if cls.current_video.get("video_id") == video_id and cls.current_video.get("stream_url"):
                cls.current_video["visible"] = True
                cls.current_video["error"] = ""
                resume_position = max(0.0, float(start_position or cls.current_video.get("playback_position") or 0.0))
                cls.current_video["playback_position"] = resume_position
                cls.current_video["playback_anchor_position"] = resume_position
                cls.current_video["playback_updated_at"] = time.time()
                cls.notify_listeners()
                return True, ""

            cls.current_video.update({
                "video_id": video_id,
                "title": item.get("title", "YouTube"),
                "channel": item.get("channel", "YouTube"),
                "thumbnail": item.get("thumbnail", ""),
                "stream_url": "",
                "web_url": web_url,
                "http_headers": {},
                "visible": True,
                "loading": True,
                "error": "",
                "playback_position": max(0.0, float(start_position or 0.0)),
                "playback_anchor_position": max(0.0, float(start_position or 0.0)),
                "playback_updated_at": 0.0,
                "play_started_at": 0.0,
                "paused": False,
            })
        cls.notify_listeners()

        if not YT_DLP_AVAILABLE:
            with cls.lock:
                cls.current_video["loading"] = False
                cls.current_video["visible"] = False
                cls.current_video["error"] = "Thiếu yt-dlp để phát video trong ứng dụng."
            cls.notify_listeners()
            return False, "Thiếu yt-dlp để phát video trong ứng dụng."

        ydl_options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": False,
            "format": "best[ext=mp4][height<=720]/best[height<=720]/best",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(web_url, download=False)

            stream_url = info.get("url")
            if not stream_url:
                raise RuntimeError("Không lấy được stream URL từ YouTube.")

            with cls.lock:
                cls.current_video.update({
                    "title": info.get("title") or cls.current_video.get("title", "YouTube"),
                    "channel": info.get("uploader") or cls.current_video.get("channel", "YouTube"),
                    "thumbnail": info.get("thumbnail") or cls.current_video.get("thumbnail", ""),
                    "stream_url": stream_url,
                    "http_headers": info.get("http_headers") or {},
                    "loading": False,
                    "visible": True,
                    "error": "",
                    "duration": float(info.get("duration") or 0.0),
                })
            cls.notify_listeners()
            return True, ""
        except Exception as error:
            with cls.lock:
                cls.current_video["loading"] = False
                cls.current_video["visible"] = False
                cls.current_video["error"] = str(error)
            cls.notify_listeners()
            return False, str(error)

class TienIchPage(ft.Stack):
    def __init__(self, user_account=None):
        super().__init__(expand=True)
        self.user_account = user_account or {}
        
        self.weather_context = "Chưa có dữ liệu thời tiết"
        self.is_chat_open = False 
        
        self.chat_window = None
        self.chat_history = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)
        self.weather_loop_running = False
        self.weather_loop_thread = None
        self.weather_request_in_progress = False
        self.last_weather_refresh_at = time.time() - WEATHER_REFRESH_INTERVAL_SECONDS
        self.current_youtube_item = None
        self.current_youtube_feed = []
        self.weather_data = {
            "temperature": 0,
            "description": "Không xác định",
            "apparent_temperature": 0,
            "humidity": 0,
            "wind_speed": 0,
            "precipitation": 0,
        }
        
        self.music_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
        self.is_syncing_slider = False
        self.model_config = self.load_model_config()
        self.ai_api_key = self.model_config.get("ai_api", {}).get("groq_api_key", "").strip()
        self.weather_api_key = self.model_config.get("ai_api", {}).get("weather_api_key", "").strip()
        self.city = self.model_config.get("ai_api", {}).get("city", DEFAULT_CITY)
        self.youtube_api_key = self.model_config.get("ai_api", {}).get("youtube_api_key", "").strip()
        self.youtube_default_loaded = False
        self.yt_view_mode = "home"

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

        self.init_ui()

    def load_model_config(self):
        config_path = os.path.join(self.music_dir, "model_config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as error:
            print(f"Lỗi đọc model_config.json: {error}")
            return {}

    def call_groq_api(self, prompt):
        if not self.ai_api_key:
            return "Chưa cấu hình Groq API key trong model_config.json."

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.ai_api_key}'
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "Bạn là trợ lý của hệ thống giám sát lái xe. Chỉ trả lời các câu hỏi liên quan đến thời tiết, giao thông, lộ trình, an toàn lái xe, bản đồ và tính năng của hệ thống. Nếu câu hỏi ngoài phạm vi này, hãy từ chối ngắn gọn và hướng người dùng quay lại chủ đề thời tiết hoặc giao thông."
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

    def load_weather_data(self):
        if self.weather_request_in_progress:
            return

        def fetch():
            self.weather_request_in_progress = True
            temp = 0
            desc = "Không xác định"
            apparent_temperature = 0
            humidity = 0
            wind_speed = 0
            precipitation = 0
            icon_name = ft.Icons.CLOUD
            icon_color = ft.Colors.WHITE
            provider_label = "OpenWeather"
            try:
                if not self.weather_api_key:
                    raise RuntimeError("Thiếu weather_api_key")

                response = requests.get(
                    OPENWEATHER_URL,
                    params={
                        "q": self.city,
                        "appid": self.weather_api_key,
                        "units": "metric",
                        "lang": "vi",
                    },
                    timeout=4,
                )
                response.raise_for_status()
                payload = response.json()
                main = payload.get("main", {})
                weather_info = (payload.get("weather") or [{}])[0]
                wind = payload.get("wind", {})
                rain = payload.get("rain", {}) or {}
                snow = payload.get("snow", {}) or {}

                temp = int(round(float(main.get("temp", 0))))
                apparent_temperature = int(round(float(main.get("feels_like", temp))))
                humidity = int(main.get("humidity", 0))
                wind_speed = int(round(float(wind.get("speed", 0)) * 3.6))
                precipitation = float(rain.get("1h", rain.get("3h", snow.get("1h", snow.get("3h", 0))) or 0))
                desc = (weather_info.get("description") or "Không xác định").capitalize()
                icon_name, icon_color = OPENWEATHER_ICON_MAP.get(
                    weather_info.get("icon", ""),
                    (ft.Icons.CLOUD, ft.Colors.WHITE),
                )
            except Exception:
                temp, desc = 29, "Ít mây"
                apparent_temperature = 31
                humidity = 70
                wind_speed = 8
                precipitation = 0
                icon_name = ft.Icons.WB_CLOUDY
                icon_color = ft.Colors.WHITE
                provider_label = "Dữ liệu dự phòng"

            self.weather_data = {
                "temperature": temp,
                "description": desc,
                "apparent_temperature": apparent_temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "precipitation": precipitation,
            }

            self.weather_context = f"Thời tiết tại {self.city}: {temp} độ C, {desc}."
            
            try:
                self.apply_weather_values(
                    temp=temp,
                    desc=desc,
                    apparent_temperature=apparent_temperature,
                    humidity=humidity,
                    wind_speed=wind_speed,
                    precipitation=precipitation,
                    icon_name=icon_name,
                    icon_color=icon_color,
                    update_label=f"Cập nhật {provider_label} {time.strftime('%H:%M:%S')}",
                )
                self.last_weather_refresh_at = time.time()
                    
                if self.page:
                    self.update()
            except Exception:
                pass
            finally:
                self.weather_request_in_progress = False

        threading.Thread(target=fetch, daemon=True).start()

    def apply_weather_values(self, temp, desc, apparent_temperature, humidity, wind_speed, precipitation, icon_name, icon_color, update_label):
        self.txt_temp.value = f"{temp} °C"
        self.txt_desc.value = desc.capitalize()
        self.txt_city.value = self.city
        self.txt_weather_update.value = update_label
        self.txt_feels_like.value = f"Cảm nhận {apparent_temperature}°C"
        self.txt_humidity.value = f"Độ ẩm {humidity}%"
        self.txt_wind.value = f"Gió {wind_speed} km/h"
        self.txt_precipitation.value = f"Mưa {precipitation:.1f} mm"
        self.icon_weather.name = icon_name
        self.icon_weather.color = icon_color

    def refresh_live_weather_ui(self):
        if not getattr(self, "page", None):
            return

        try:
            self.txt_weather_clock.value = time.strftime("%H:%M:%S")
            if self.page:
                self.txt_weather_clock.update()

            now = time.time()
            if now - self.last_weather_refresh_at >= WEATHER_REFRESH_INTERVAL_SECONDS:
                self.load_weather_data()
        except Exception:
            pass

    def start_weather_live_updates(self):
        if self.weather_loop_running:
            return

        self.weather_loop_running = True

        def loop():
            while self.weather_loop_running:
                self.refresh_live_weather_ui()
                time.sleep(1)

        self.weather_loop_thread = threading.Thread(target=loop, daemon=True)
        self.weather_loop_thread.start()

    def toggle_chat_window(self, e):
        self.is_chat_open = not self.is_chat_open
        self.chat_window.visible = self.is_chat_open
        if self.page:
            self.chat_window.update()

    def create_chat_bubble(self, text, sender="user"):
        is_user = sender == "user"
        bubble_color = ft.Colors.BLUE_700 if is_user else "#F1F5F9"
        text_color = ft.Colors.WHITE if is_user else "#0F172A"
        radius = ft.border_radius.only(16, 16, 2 if is_user else 16, 16 if is_user else 2)
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(
                        text,
                        color=text_color,
                        size=14,
                        weight=ft.FontWeight.W_600,
                        selectable=True,
                    ),
                    bgcolor=bubble_color,
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    border_radius=radius,
                    width=300 if not is_user else None,
                    border=None if is_user else ft.border.all(1, ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
                )
            ],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
        )

    def send_message(self, e):
        user_text = self.txt_chat_input.value
        if not user_text: return

        self.chat_history.controls.append(self.create_chat_bubble(user_text, sender="user"))
        self.txt_chat_input.value = ""
        self.txt_chat_input.focus()
        if self.page:
            self.chat_window.update()

        if not self.is_allowed_chat_topic(user_text):
            reply = "Tôi chỉ hỗ trợ câu hỏi về thời tiết, giao thông, lộ trình và các tính năng của hệ thống giám sát lái xe."
            self.chat_history.controls.append(self.create_chat_bubble(reply, sender="assistant"))
            if self.page:
                self.chat_window.update()
            return

        full_prompt = f"Bạn là trợ lý lái xe của hệ thống giám sát. Thông tin môi trường: {self.weather_context}. Người dùng hỏi: {user_text}. Chỉ trả lời trong phạm vi thời tiết, giao thông, an toàn lái xe, lộ trình và tính năng hệ thống. Hãy trả lời ngắn gọn, thân thiện bằng tiếng Việt."

        def call_ai():
            reply = self.call_groq_api(full_prompt)
            self.chat_history.controls.append(self.create_chat_bubble(reply, sender="assistant"))
            if self.page:
                self.chat_window.update()

        threading.Thread(target=call_ai, daemon=True).start()

    # ─────────────────────── YouTube helpers ──────────────────────────
    def search_youtube(self, query: str):
        """Gọi YouTube Data API v3, trả về list dict {title, video_id, thumbnail}."""
        if not self.youtube_api_key:
            return None  # chưa cấu hình key
        try:
            params = {
                "key": self.youtube_api_key,
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": 6,
                "relevanceLanguage": "vi",
            }
            resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=8)
            if resp.status_code != 200:
                return []
            items = resp.json().get("items", [])
            results = []
            for item in items:
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId", "")
                if not video_id:
                    continue
                results.append({
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                    "video_id": video_id,
                })
            return results
        except Exception as ex:
            print(f"[YouTube] Lỗi tìm kiếm: {ex}")
            return []

    def get_youtube_home_videos(self):
        if not self.youtube_api_key:
            return None
        try:
            params = {
                "key": self.youtube_api_key,
                "part": "snippet",
                "chart": "mostPopular",
                "regionCode": "VN",
                "maxResults": 8,
            }
            resp = requests.get(YOUTUBE_POPULAR_URL, params=params, timeout=8)
            if resp.status_code != 200:
                return []

            items = resp.json().get("items", [])
            results = []
            for item in items:
                snippet = item.get("snippet", {})
                video_id = item.get("id", "")
                if not video_id:
                    continue
                results.append({
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                    "video_id": video_id,
                })
            return results
        except Exception as ex:
            print(f"[YouTube] Lỗi tải home feed: {ex}")
            return []

    def _open_youtube_video(self, item: dict):
        title = item.get("title", "YouTube")
        self._set_current_youtube_item(item, subtitle="Đang chuẩn bị phát video")
        # Chuyển sang player ngay để người dùng thấy trạng thái tải thay vì đứng ở Home.
        self._show_yt_view("player")
        self._show_yt_status(f"⏳ Đang tải: {title[:38]}...", error=False)
        if YouTubePlayerManager:
            queue_items = self.current_youtube_feed or [item]
            YouTubePlayerManager.set_queue(queue_items, item.get("video_id", ""))
            YouTubePlayerManager.set_playback_position(0.0)

        def load_video():
            ok, message = YouTubePlayerManager.load_video(item)
            if ok:
                self._show_yt_status(f"▶️ Đang phát: {title[:42]}", error=False)
                try:
                    self.refresh_selected_youtube()
                except Exception:
                    pass
                self._load_recommended_youtube_feed(item)
            else:
                self._show_yt_status(f"❌ Không phát được video: {message}", error=True)

        threading.Thread(target=load_video, daemon=True).start()

    def _do_youtube_search(self, e):
        query = ""
        if hasattr(self, "yt_search_field_home") and self.yt_search_field_home.value:
            query = self.yt_search_field_home.value.strip()
        if not query and hasattr(self, "yt_search_field_player") and self.yt_search_field_player.value:
            query = self.yt_search_field_player.value.strip()

        if not query:
            self._load_default_youtube_feed()
            return

        self._sync_yt_search_fields(query)
        self._show_yt_view("home")
        if not self.youtube_api_key:
            self._show_yt_status("⚠️ Chưa cấu hình YouTube API Key (Admin → Quản lý dữ liệu)", error=True)
            return

        self._show_yt_status("⏳ Đang tìm kiếm...", error=False)
        self._render_youtube_home([])

        def fetch():
            results = self.search_youtube(query)
            self.current_youtube_feed = [dict(row) for row in results or []]
            if results is None:
                self._show_yt_status("⚠️ Chưa cấu hình YouTube API Key", error=True)
                return
            if not results:
                self._show_yt_status("❌ Không tìm thấy kết quả", error=True)
                return
            self._show_yt_status(f"✅ Tìm thấy {len(results)} kết quả", error=False)
            self._render_youtube_home(results)

        threading.Thread(target=fetch, daemon=True).start()

    def _show_yt_view(self, mode: str):
        self.yt_view_mode = "player" if mode == "player" else "home"
        if hasattr(self, "yt_home_view"):
            self.yt_home_view.visible = self.yt_view_mode == "home"
        if hasattr(self, "yt_player_view"):
            self.yt_player_view.visible = self.yt_view_mode == "player"
        if hasattr(self, "yt_back_button"):
            self.yt_back_button.visible = self.yt_view_mode == "player"
            try:
                self.yt_back_button.update()
            except Exception:
                pass
        try:
            if hasattr(self, "yt_view_stack") and self.yt_view_stack:
                self.yt_view_stack.update()
        except Exception:
            pass

    def _render_youtube_home(self, items):
        if not hasattr(self, "yt_home_grid") or not self.yt_home_grid:
            return
        self.yt_home_grid.controls.clear()
        for row in items or []:
            self.yt_home_grid.controls.append(self._build_yt_result_card(row, variant="home"))
        try:
            self.yt_home_grid.update()
        except Exception:
            pass

    def _render_youtube_sidebar(self, items):
        if not hasattr(self, "yt_sidebar_list") or not self.yt_sidebar_list:
            return
        self.yt_sidebar_list.controls.clear()
        for row in items or []:
            self.yt_sidebar_list.controls.append(self._build_yt_result_card(row, variant="sidebar"))
        try:
            self.yt_sidebar_list.update()
        except Exception:
            pass

    def _on_yt_back(self, e):
        self._show_yt_view("home")

    def _sync_yt_search_fields(self, query: str):
        if hasattr(self, "yt_search_field_home"):
            self.yt_search_field_home.value = query
        if hasattr(self, "yt_search_field_player"):
            self.yt_search_field_player.value = query
        try:
            if hasattr(self, "yt_search_field_home"):
                self.yt_search_field_home.update()
            if hasattr(self, "yt_search_field_player"):
                self.yt_search_field_player.update()
        except Exception:
            pass

    def _load_default_youtube_feed(self):
        self._show_yt_view("home")
        if not self.youtube_api_key:
            self._show_yt_status("⚠️ Chưa cấu hình YouTube API Key", error=True)
            return

        self._show_yt_status("⏳ Đang tải trang chủ YouTube...", error=False)
        self._render_youtube_home([])

        def fetch():
            results = self.get_youtube_home_videos()
            self.current_youtube_feed = [dict(row) for row in results or []]
            if results is None:
                self._show_yt_status("⚠️ Chưa cấu hình YouTube API Key", error=True)
                return
            if not results:
                self._show_yt_status("❌ Không tải được trang chủ YouTube", error=True)
                return

            if not self.current_youtube_item:
                self._set_current_youtube_item(results[0], subtitle="Nổi bật hôm nay")
            self._show_yt_status("🔥 Video nổi bật trên YouTube hôm nay", error=False)
            self._render_youtube_home(results)

        threading.Thread(target=fetch, daemon=True).start()

    def _show_yt_status(self, msg: str, error: bool = False):
        if hasattr(self, "yt_status_text"):
            self.yt_status_text.value = msg
            self.yt_status_text.color = ft.Colors.RED_300 if error else ft.Colors.GREEN_400
            try:
                self.yt_status_text.update()
            except Exception:
                pass

    def _set_current_youtube_item(self, item: dict | None, subtitle: str | None = None):
        item = item or {}
        self.current_youtube_item = dict(item) if item else None

        thumbnail = item.get("thumbnail") or "https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?q=80&w=1000&auto=format&fit=crop"
        title = item.get("title") or "Chọn một video YouTube để phát"
        channel = item.get("channel") or "Video hiện tại sẽ hiển thị ở đây"
        helper_text = subtitle or ("Đang chọn" if item.get("video_id") else "Video hiện tại")

        if hasattr(self, "yt_current_image"):
            self.yt_current_image.src = thumbnail
            self.yt_current_title.value = title
            self.yt_current_channel.value = channel
            self.yt_current_hint.value = helper_text
            for control in [self.yt_current_image, self.yt_current_title, self.yt_current_channel, self.yt_current_hint]:
                try:
                    control.update()
                except Exception:
                    pass

    def _clear_embedded_youtube_playlist(self):
        playlist = self.yt_embedded_video.playlist if hasattr(self, "yt_embedded_video") else None
        if playlist is None:
            return
        playlist.clear()

    def _set_embedded_youtube_media(self, stream_url: str, http_headers=None):
        playlist = self.yt_embedded_video.playlist if hasattr(self, "yt_embedded_video") else None
        if playlist is None:
            return
        playlist.clear()
        playlist.append(
            ft.VideoMedia(
                resource=stream_url,
                http_headers=http_headers or None,
            )
        )

    def on_embedded_youtube_error(self, e):
        self._show_yt_status("❌ Không phát được video trong tab Tiện ích", error=True)
        self.yt_embedded_video.visible = False
        self.yt_current_image.visible = True
        try:
            self.yt_embedded_video.update()
            self.yt_current_image.update()
        except Exception:
            pass

    def on_embedded_youtube_loaded(self, e):
        try:
            if self.yt_embedded_pending_seek > 0.5:
                self._yt_jump_to_seconds(self.yt_embedded_pending_seek)
            self.yt_embedded_video.play()
            self.yt_embedded_pending_seek = 0.0
            if YouTubePlayerManager:
                YouTubePlayerManager.mark_play_started()
                YouTubePlayerManager.set_paused(False)
        except Exception:
            pass

    def on_embedded_youtube_position_change(self, e):
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
        try:
            position = float(YouTubePlayerManager.normalize_player_position(raw, duration))
        except Exception:
            position = 0.0
        YouTubePlayerManager.set_playback_position(position)
        if self.yt_is_syncing_slider:
            return
        if self.yt_progress_slider:
            self.yt_progress_slider.max = duration
            self.yt_progress_slider.value = min(position, duration) if duration > 0 else 0.0
        if self.yt_time_current:
            self.yt_time_current.value = self.format_time(position)
        if self.yt_time_total:
            self.yt_time_total.value = self.format_time(duration) if duration > 0 else "--:--"
        try:
            self.yt_progress_slider.update()
            self.yt_time_current.update()
            self.yt_time_total.update()
        except Exception:
            pass

    def on_embedded_youtube_completed(self, e):
        if YouTubePlayerManager:
            if not YouTubePlayerManager.can_auto_advance():
                return
            YouTubePlayerManager.set_playback_position(0.0)
            ok, message = YouTubePlayerManager.play_next()
            if not ok:
                self._show_yt_status(f"ℹ️ {message}", error=False)

    def sync_youtube_state_to_manager(self):
        if not YouTubePlayerManager or not getattr(self, "yt_embedded_stream", ""):
            return
        state = YouTubePlayerManager.get_state()
        previous_position = float(state.get("playback_position") or 0.0)
        duration = float(state.get("duration") or 0.0)
        try:
            raw = float(self.yt_embedded_video.get_current_position() or 0.0)
            position_seconds = float(YouTubePlayerManager.normalize_player_position(raw, duration))
        except Exception:
            position_seconds = 0.0
        if position_seconds > 0.5 or previous_position <= 0.5:
            YouTubePlayerManager.set_playback_position(max(position_seconds, previous_position))

    def refresh_selected_youtube(self):
        state = YouTubePlayerManager.get_state() if YouTubePlayerManager else {}
        if state.get("video_id"):
            self._set_current_youtube_item(
                {
                    "video_id": state.get("video_id", ""),
                    "title": state.get("title", "YouTube"),
                    "channel": state.get("channel", "YouTube"),
                    "thumbnail": state.get("thumbnail", ""),
                },
                subtitle="Đang tải video..." if state.get("loading") else "Đang phát trong ứng dụng",
            )

        stream_url = state.get("stream_url") or ""
        if state.get("loading"):
            self.yt_current_image.visible = True
            self.yt_embedded_video.visible = False
            try:
                self.yt_current_image.update()
                self.yt_embedded_video.update()
            except Exception:
                pass
            return

        if not stream_url:
            self._clear_embedded_youtube_playlist()
            self.yt_embedded_video.visible = False
            self.yt_current_image.visible = True
            try:
                self.yt_embedded_video.stop()
                self.yt_embedded_video.update()
                self.yt_current_image.update()
            except Exception:
                pass
            return

        if stream_url != getattr(self, "yt_embedded_stream", ""):
            self.yt_embedded_stream = stream_url
            self._set_embedded_youtube_media(stream_url, state.get("http_headers"))
            self.yt_current_image.visible = False
            self.yt_embedded_video.visible = True
            try:
                self.yt_embedded_pending_seek = max(0.0, float(state.get("playback_position") or 0.0))
                self.yt_embedded_video.update()
                self.yt_current_image.update()
            except Exception as ex:
                self._show_yt_status(f"❌ Lỗi phát video: {ex}", error=True)
        elif stream_url and self.yt_embedded_video.visible:
            try:
                self.yt_embedded_video.play()
            except Exception:
                pass

    def get_youtube_recommendations(self, item: dict | None = None):
        if not self.youtube_api_key:
            return None

        current = item or self.current_youtube_item or {}
        video_id = current.get("video_id", "")

        try:
            if video_id:
                params = {
                    "key": self.youtube_api_key,
                    "part": "snippet",
                    "type": "video",
                    "maxResults": 8,
                    "relatedToVideoId": video_id,
                }
                resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=8)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    results = []
                    for row in items:
                        snippet = row.get("snippet", {})
                        rel_video_id = row.get("id", {}).get("videoId", "")
                        if not rel_video_id or rel_video_id == video_id:
                            continue
                        results.append({
                            "title": snippet.get("title", ""),
                            "channel": snippet.get("channelTitle", ""),
                            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                            "video_id": rel_video_id,
                        })
                    if results:
                        return results
        except Exception as ex:
            print(f"[YouTube] Lỗi tải video đề xuất: {ex}")

        fallback_query = f"{current.get('title', '')} {current.get('channel', '')}".strip()
        if fallback_query:
            return self.search_youtube(fallback_query)
        return self.get_youtube_home_videos()

    def _load_recommended_youtube_feed(self, item: dict | None = None):
        self._show_yt_status("⏳ Đang tải video đề xuất...", error=False)
        self._render_youtube_sidebar([])

        def fetch():
            results = self.get_youtube_recommendations(item)
            queue_seed = []
            if item and item.get("video_id"):
                queue_seed.append(dict(item))
            queue_seed.extend(dict(row) for row in results or [] if row.get("video_id") != (item or {}).get("video_id"))
            self.current_youtube_feed = queue_seed
            if YouTubePlayerManager:
                YouTubePlayerManager.set_queue(self.current_youtube_feed, (item or {}).get("video_id", ""))
            if results is None:
                self._show_yt_status("⚠️ Chưa cấu hình YouTube API Key", error=True)
                return
            if not results:
                self._show_yt_status("❌ Không tải được video đề xuất", error=True)
                return

            self._show_yt_status("🎯 Video đề xuất cho bạn", error=False)
            self._render_youtube_sidebar(results)

        threading.Thread(target=fetch, daemon=True).start()

    def _on_youtube_result_click(self, e):
        payload = getattr(e.control, "data", None)
        if not isinstance(payload, dict):
            self._show_yt_status("❌ Dữ liệu video không hợp lệ", error=True)
            return
        self._open_youtube_video(dict(payload))

    def _scroll_yt_results(self, delta: int):
        if not hasattr(self, 'yt_results_col') or not self.yt_results_col:
            return
        total = len(getattr(self.yt_results_col, 'controls', []) or [])
        if total <= 0:
            return
        if not hasattr(self, 'yt_scroll_index'):
            self.yt_scroll_index = 0
        self.yt_scroll_index = max(0, min(int(self.yt_scroll_index) + int(delta or 0), total - 1))
        try:
            self.yt_results_col.scroll_to(index=self.yt_scroll_index, duration=280)
        except Exception:
            pass

    def _build_yt_result_card(self, item: dict, variant: str = "home") -> ft.Container:
        payload = {
            "video_id": item.get("video_id", ""),
            "title": item.get("title", "YouTube"),
            "channel": item.get("channel", "YouTube"),
            "thumbnail": item.get("thumbnail", ""),
        }
        if variant == "sidebar":
            return ft.Container(
                key=f"yt-side-{payload['video_id']}",
                border_radius=10,
                bgcolor="#181818",
                padding=ft.padding.all(8),
                ink=True,
                data=payload,
                on_click=self._on_youtube_result_click,
                content=ft.Row(
                    [
                        ft.Container(
                            width=120,
                            height=70,
                            border_radius=8,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            content=ft.Image(
                                src=payload["thumbnail"],
                                fit=ft.ImageFit.COVER,
                                width=120,
                                height=70,
                                error_content=ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, color=ft.Colors.RED_400, size=24),
                            ),
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    payload["title"],
                                    size=12,
                                    weight=ft.FontWeight.W_700,
                                    color=ft.Colors.WHITE,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    payload["channel"],
                                    size=10,
                                    color=ft.Colors.WHITE70,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            )

        return ft.Container(
            key=f"yt-{payload['video_id']}",
            border_radius=14,
            bgcolor="#181818",
            padding=0,
            ink=True,
            data=payload,
            on_click=self._on_youtube_result_click,
            content=ft.Column(
                [
                    ft.Container(
                        width=float("inf"),
                        height=160,
                        border_radius=12,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Image(
                            src=payload["thumbnail"],
                            fit=ft.ImageFit.COVER,
                            width=float("inf"),
                            height=160,
                            error_content=ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, color=ft.Colors.RED_400, size=30),
                        ),
                    ),
                    ft.Container(
                        padding=ft.padding.only(left=6, right=6, top=6, bottom=8),
                        content=ft.Column(
                            [
                                ft.Text(
                                    payload["title"],
                                    size=12,
                                    weight=ft.FontWeight.W_700,
                                    color=ft.Colors.WHITE,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    payload["channel"],
                                    size=11,
                                    color=ft.Colors.WHITE70,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            spacing=4,
                        ),
                    ),
                ],
                spacing=0,
            ),
        )

    def is_allowed_chat_topic(self, user_text):
        normalized_text = (user_text or "").lower()
        keywords = [
            "thời tiết", "nhiệt độ", "mưa", "nắng", "gió", "sương mù", "bão",
            "giao thông", "kẹt xe", "tai nạn", "đường", "lộ trình", "bản đồ", "di chuyển",
            "phiên lái", "an toàn", "buồn ngủ", "cảnh báo", "camera", "telegram", "hệ thống",
            "giám sát", "tuyến đường", "xe", "lái xe"
        ]
        return any(keyword in normalized_text for keyword in keywords)

    def open_music_library_dialog(self, e):
        if not self.music_manager.playlist:
            if self.page:
                self.page.open(ft.SnackBar(ft.Text("Không tìm thấy bài nhạc trong thư mục data/music."), bgcolor=ft.Colors.RED_600))
                self.page.update()
            return

        dialog = None

        def select_song(index: int):
            self.music_manager.play_song(index=index)
            if dialog and self.page:
                self.page.close(dialog)
                self.page.update()

        items = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.BLUE_600),
                title=ft.Text(song.get("title", "Unknown"), max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                subtitle=ft.Text(song.get("filename", ""), max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                trailing=ft.Icon(ft.Icons.PLAY_ARROW, color=ft.Colors.GREEN_700),
                on_click=lambda _, song_index=index: select_song(song_index),
            )
            for index, song in enumerate(self.music_manager.playlist)
        ]

        dialog = ft.AlertDialog(
            title=ft.Text("Danh sách nhạc", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=520,
                height=420,
                content=ft.ListView(controls=items, spacing=4, auto_scroll=False),
            ),
            actions=[text_button("Đóng", on_click=lambda _: self.page.close(dialog), kind="surface")],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialog)
        self.page.update()

    def update_music_ui(self):
        state = self.music_manager.get_state()
        self.txt_song_title.value = state["title"]
        self.btn_play_pause.icon = ft.Icons.PAUSE if state["is_playing"] else ft.Icons.PLAY_ARROW
        self.music_slider.max = state["song_length"] or 100
        self.txt_current_time.value = self.format_time(state["current_position"])
        self.txt_total_time.value = self.format_time(state["song_length"])
        try:
            if getattr(self, "page", None):
                self.txt_song_title.update()
                self.btn_play_pause.update()
                self.music_slider.update()
                self.txt_current_time.update()
                self.txt_total_time.update()
        except: pass

    def format_time(self, seconds):
        total_seconds = max(0, int(seconds or 0))
        minutes, remain = divmod(total_seconds, 60)
        return f"{minutes:02d}:{remain:02d}"

    def get_current_position(self):
        return self.music_manager.get_current_position()

    def sync_slider_ui(self, value):
        self.is_syncing_slider = True
        try:
            state = self.music_manager.get_state()
            self.music_slider.max = state["song_length"] or 100
            self.music_slider.value = max(0, min(value, state["song_length"] or 0))
            self.txt_current_time.value = self.format_time(value)
            if self.page:
                self.music_slider.update()
                self.txt_current_time.update()
        finally:
            self.is_syncing_slider = False

    def refresh_music_from_manager(self):
        state = self.music_manager.get_state()
        self.sync_slider_ui(state["current_position"])
        self.update_music_ui()

    def on_slider_change(self, e):
        state = self.music_manager.get_state()
        if self.is_syncing_slider or not state["song_loaded"]:
            return

        new_pos = max(0.0, min(float(e.control.value or 0), float(state["song_length"] or 0)))
        self.txt_current_time.value = self.format_time(new_pos)
        if self.page:
            self.txt_current_time.update()

    def on_slider_change_end(self, e):
        state = self.music_manager.get_state()
        if self.is_syncing_slider or not state["song_loaded"]:
            return

        new_pos = max(0.0, min(float(e.control.value or 0), float(state["song_length"] or 0)))
        self.music_manager.seek_to(new_pos)

    def seek_to(self, position_seconds):
        self.music_manager.seek_to(position_seconds)

    def play_song(self):
        self.music_manager.play_song()

    def toggle_play(self, e):
        self.music_manager.toggle_play()

    def next_song(self, e):
        self.music_manager.next_song()

    def prev_song(self, e):
        self.music_manager.prev_song()

    def _yt_raw_from_seconds(self, seconds: float) -> float:
        seconds = max(0.0, float(seconds or 0.0))
        if YouTubePlayerManager and getattr(YouTubePlayerManager, "position_scale", None) is not None:
            try:
                scale = float(getattr(YouTubePlayerManager, "position_scale"))
                if scale > 0:
                    return seconds / scale
            except Exception:
                pass
        return seconds

    def _yt_jump_to_seconds(self, seconds: float):
        if YouTubePlayerManager:
            try:
                duration = float(YouTubePlayerManager.get_state().get("duration") or 0.0)
            except Exception:
                duration = 0.0
            if getattr(YouTubePlayerManager, "position_scale", None) is None:
                try:
                    raw_now = float(self.yt_embedded_video.get_current_position() or 0.0)
                except Exception:
                    raw_now = 0.0
                if raw_now > 0:
                    if duration > 0 and raw_now > max(1200.0, duration * 10.0):
                        YouTubePlayerManager.set_position_scale(0.001)
                    elif duration <= 0 and raw_now > 60000.0:
                        YouTubePlayerManager.set_position_scale(0.001)
                    else:
                        YouTubePlayerManager.set_position_scale(1.0)
        raw = self._yt_raw_from_seconds(seconds)
        try:
            self.yt_embedded_video.jump_to(raw)
        except Exception:
            pass

    def _on_yt_slider_change(self, e):
        if self.yt_is_syncing_slider or not YouTubePlayerManager:
            return
        state = YouTubePlayerManager.get_state()
        duration = float(state.get("duration") or 0)
        if duration > 0:
            pos = max(0.0, min(float(e.control.value or 0), duration))
            self.yt_time_current.value = self.format_time(pos)
            try:
                self.yt_time_current.update()
            except Exception:
                pass

    def _on_yt_slider_change_end(self, e):
        if self.yt_is_syncing_slider or not YouTubePlayerManager:
            return
        state = YouTubePlayerManager.get_state()
        duration = float(state.get("duration") or 0)
        if duration > 0:
            pos = max(0.0, min(float(e.control.value or 0), duration))
            try:
                self._yt_jump_to_seconds(pos)
                YouTubePlayerManager.set_playback_position(pos)
            except Exception:
                pass

    def yt_seek_relative(self, delta_seconds: float):
        if not YouTubePlayerManager:
            return
        state = YouTubePlayerManager.get_state()
        duration = float(state.get("duration") or 0.0)
        position = float(state.get("playback_position") or 0.0)
        new_pos = max(0.0, position + float(delta_seconds or 0.0))
        if duration > 0:
            new_pos = min(new_pos, duration)
        self._yt_jump_to_seconds(new_pos)
        YouTubePlayerManager.set_playback_position(new_pos)

    def yt_prev_video(self, e):
        if not YouTubePlayerManager:
            return
        ok, message = YouTubePlayerManager.play_prev()
        if not ok and message:
            self._show_yt_status(message, error=False)

    def yt_next_video(self, e):
        if not YouTubePlayerManager:
            return
        ok, message = YouTubePlayerManager.play_next()
        if not ok and message:
            self._show_yt_status(message, error=False)

    def _update_yt_progress(self):
        if not YouTubePlayerManager or not getattr(self, "page", None):
            return
        state = YouTubePlayerManager.get_state()
        duration = float(state.get("duration") or 0)
        position = float(state.get("playback_position") or 0)
        if not state.get("stream_url") or state.get("loading"):
            return
        self.yt_is_syncing_slider = True
        try:
            if duration > 0:
                self.yt_progress_slider.max = duration
                self.yt_progress_slider.value = min(position, duration)
                self.yt_time_current.value = self.format_time(position)
                self.yt_time_total.value = self.format_time(duration)
            else:
                self.yt_progress_slider.value = 0
                self.yt_time_current.value = self.format_time(position)
        finally:
            self.yt_is_syncing_slider = False
        try:
            self.yt_progress_slider.update()
            self.yt_time_current.update()
            self.yt_time_total.update()
        except Exception:
            pass

    def _start_yt_slider_loop(self):
        if getattr(self, "yt_position_event_bound", False):
            return
        if self.yt_slider_loop_running:
            return
        self.yt_slider_loop_running = True
        def loop():
            while self.yt_slider_loop_running:
                self._update_yt_progress()
                time.sleep(1)
        threading.Thread(target=loop, daemon=True).start()

    def did_mount(self):
        super().did_mount()
        if YouTubePlayerManager:
            YouTubePlayerManager.register_listener(self.refresh_selected_youtube)
        self.yt_embedded_stream = ""  # Force media reload khi tab được hiện lại
        self.refresh_selected_youtube()
        self.start_weather_live_updates()
        self.load_weather_data()
        self._start_yt_slider_loop()
        if not self.youtube_default_loaded:
            self.youtube_default_loaded = True
            self._load_default_youtube_feed()

    def will_unmount(self):
        super().will_unmount()
        if YouTubePlayerManager:
            YouTubePlayerManager.unregister_listener(self.refresh_selected_youtube)
        self.weather_loop_running = False
        self.yt_slider_loop_running = False

    def open_add_music_dialog(self, e):
        if not self.page or not self.music_file_picker:
            return
        self.music_file_picker.pick_files(
            dialog_title="Chọn file nhạc",
            allowed_extensions=["mp3", "wav", "ogg", "flac", "m4a"],
            allow_multiple=True,
        )

    def on_music_files_picked(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        added = self.music_manager.add_music_files(e.files)
        self.refresh_music_from_manager()

        if not self.page:
            return

        if added > 0:
            self.page.open(ft.SnackBar(
                ft.Text(f"✅ Đã thêm {added} bài nhạc vào tiện ích."),
                bgcolor=ft.Colors.GREEN_600,
            ))
        else:
            self.page.open(ft.SnackBar(
                ft.Text("⚠️ Không có bài mới nào được thêm."),
                bgcolor=ft.Colors.ORANGE_600,
            ))

    # --- UI MAP ---
    def open_map_dialog(self, e):
        current_city = self.txt_city.value if hasattr(self, 'txt_city') else self.city
        location = current_city.replace(" ", "%20")
        map_img_url = "https://media.wired.com/photos/59269cd37034dc5f91bec0f1/191:100/w_1280,c_limit/GoogleMapTA.jpg"

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.MAP, color=ft.Colors.BLUE),
                ft.Text(f"Bản Đồ Di Chuyển - {current_city}", weight="bold")
            ]),
            content=ft.Container(
                width=600, height=350, border_radius=15, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
                content=ft.Stack([
                    ft.Image(src=map_img_url, fit=ft.ImageFit.COVER, expand=True, opacity=0.5),
                    ft.Container(
                        alignment=ft.alignment.center,
                        content=ft.Column([
                            ft.Icon(ft.Icons.LOCATION_ON, size=60, color=ft.Colors.RED),
                            ft.Text(f"Khu vực nhận diện:\n{current_city}", weight="bold", size=24, color=ft.Colors.BLACK87, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=10),
                            ft.Text("Tính năng nhúng bản đồ tương tác (WebView) không tương thích hoàn toàn trên thiết bị hiện hành.", color=ft.Colors.BLUE_GREY_800, size=12, text_align=ft.TextAlign.CENTER, width=500),
                            ft.Container(height=20),
                            elevated_button("Chuyển tới Google Maps Trình Duyệt", icon=ft.Icons.OPEN_IN_NEW, kind="secondary", on_click=lambda _: e.page.launch_url(f"https://www.google.com/maps/search/{location}"))
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                ])
            ),
            actions=[text_button("Đóng", on_click=lambda _: e.page.close(dialog), kind="surface")],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(dialog)

    def init_ui(self):
        image_dir = Path(self.music_dir) / "image_user"
        IMG_THOITIET = str(image_dir / "thoitiet.png")
        IMG_MUSIC = str(image_dir / "music.png")
        IMG_MAP = str(image_dir / "map.png")
        IMG_BG = str(image_dir / "backround.jpg")

        bg_image = ft.Image(src=IMG_BG, fit=ft.ImageFit.COVER, expand=True)
        bg_overlay = ft.Container(bgcolor=ft.Colors.BLACK54, expand=True, blur=10)

        self.txt_city = ft.Text(self.city, size=16, weight="bold", color=ft.Colors.WHITE)
        self.txt_temp = ft.Text("-- °C", size=32, weight="bold", color=ft.Colors.WHITE)
        self.txt_desc = ft.Text("Đang lấy dữ liệu thời tiết", color=ft.Colors.WHITE70, size=14)
        self.txt_weather_clock = ft.Text(time.strftime("%H:%M:%S"), size=14, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE)
        self.txt_weather_update = ft.Text("Sẵn sàng đồng bộ OpenWeather", color=ft.Colors.WHITE70, size=12, weight=ft.FontWeight.W_600)
        self.txt_feels_like = ft.Text("Cảm nhận --°C", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
        self.txt_humidity = ft.Text("Độ ẩm --%", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
        self.txt_wind = ft.Text("Gió -- km/h", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
        self.txt_precipitation = ft.Text("Mưa -- mm", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
        self.icon_weather = ft.Icon(ft.Icons.WB_SUNNY, color=ft.Colors.AMBER_400, size=45)

        weather_header = ft.Row([
            ft.Image(src=IMG_THOITIET, width=35, height=35),
            ft.Text("Thời Tiết", size=18, weight="bold", color=ft.Colors.WHITE)
        ], alignment=ft.MainAxisAlignment.CENTER)

        weather_box = ft.Container(
            bgcolor="#4A86BA", border_radius=15, padding=20, height=176,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK26),
            content=ft.Stack([
                ft.Container(
                    alignment=ft.alignment.top_left,
                    content=ft.Column([
                        self.txt_city,
                        self.txt_weather_update,
                    ], spacing=4),
                ),
                ft.Container(
                    alignment=ft.alignment.top_right,
                    content=self.txt_weather_clock,
                ),
                ft.Container(
                    alignment=ft.alignment.center,
                    content=ft.Column([
                        ft.Row([self.icon_weather, self.txt_temp], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                        self.txt_desc,
                        ft.Container(height=8),
                        ft.Row([
                            self.txt_feels_like,
                            self.txt_humidity,
                            self.txt_wind,
                            self.txt_precipitation,
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=14, wrap=True),
                    ], spacing=0, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ])
        )

        def build_yt_search_field():
            return ft.TextField(
                hint_text="Tìm kiếm nhạc, video trên YouTube...",
                prefix_icon=ft.Icons.SEARCH,
                border_radius=30,
                filled=True,
                bgcolor="#202020",
                color=ft.Colors.WHITE,
                text_style=ft.TextStyle(size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                hint_style=ft.TextStyle(size=13, color=ft.Colors.WHITE70),
                border_color="#303030",
                expand=True,
                content_padding=ft.padding.symmetric(horizontal=18, vertical=10),
                on_submit=self._do_youtube_search,
            )

        self.yt_search_field_home = build_yt_search_field()
        self.yt_search_field_player = build_yt_search_field()
        self.yt_status_text = ft.Text("", size=12, color=ft.Colors.GREEN_400)
        self.yt_home_grid = ft.GridView(
            expand=True,
            max_extent=320,
            child_aspect_ratio=1.2,
            spacing=14,
            run_spacing=16,
            padding=ft.padding.only(left=8, right=8, bottom=16),
            auto_scroll=False,
        )
        self.yt_sidebar_list = ft.ListView(
            expand=True,
            spacing=12,
            auto_scroll=False,
        )
        self.yt_embedded_stream = ""
        self.yt_embedded_pending_seek = 0.0
        self.yt_is_syncing_slider = False
        self.yt_slider_loop_running = False
        self.yt_progress_slider = ft.Slider(
            min=0, max=100, value=0,
            active_color="#FF0000",
            inactive_color=ft.Colors.WHITE24,
            on_change=self._on_yt_slider_change,
            on_change_end=self._on_yt_slider_change_end,
        )
        self.yt_time_current = ft.Text("0:00", size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600)
        self.yt_time_total = ft.Text("--:--", size=11, color=ft.Colors.WHITE70)
        self.yt_current_title = ft.Text(
            "Chọn một video YouTube để phát",
            size=15,
            weight=ft.FontWeight.W_700,
            color=ft.Colors.WHITE,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.yt_current_channel = ft.Text(
            "Video hiện tại sẽ hiển thị ở đây",
            size=11,
            color=ft.Colors.WHITE70,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.yt_current_hint = ft.Text(
            "Đề xuất sẽ cập nhật theo video bạn chọn",
            size=10,
            color=ft.Colors.WHITE54,
            italic=True,
        )
        self.yt_current_image = ft.Image(
            src="https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?q=80&w=1000&auto=format&fit=crop",
            fit=ft.ImageFit.COVER,
            width=float('inf'),
            height=float('inf'),
        )
        self.yt_embedded_video = ft.Video(
            playlist=[],
            autoplay=False,
            show_controls=True,
            aspect_ratio=16 / 9,
            fit=ft.ImageFit.COVER,
            visible=False,
            on_loaded=self.on_embedded_youtube_loaded,
            on_error=self.on_embedded_youtube_error,
            on_completed=self.on_embedded_youtube_completed,
        )
        self.yt_position_event_bound = False
        self.yt_back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=ft.Colors.WHITE,
            tooltip="Quay lại",
            on_click=self._on_yt_back,
            visible=False,
        )

        def build_yt_brand():
            return ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED, color="#FF0000", size=22),
                    ft.Text("YouTube", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("VN", size=10, color=ft.Colors.WHITE54),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        yt_brand_home = build_yt_brand()
        yt_brand_player = build_yt_brand()

        yt_topbar_content_home = [
            ft.Icon(ft.Icons.MENU, color=ft.Colors.WHITE, size=22),
            yt_brand_home,
            ft.Container(expand=True),
            ft.Container(width=520, content=self.yt_search_field_home),
            ft.Container(
                width=46,
                height=40,
                border_radius=20,
                bgcolor="#202020",
                ink=True,
                on_click=self._do_youtube_search,
                alignment=ft.alignment.center,
                content=ft.Icon(ft.Icons.SEARCH, color=ft.Colors.WHITE, size=20),
            ),
            ft.Container(expand=True),
            ft.Icon(ft.Icons.MIC, color=ft.Colors.WHITE, size=20),
            ft.Icon(ft.Icons.NOTIFICATIONS_NONE, color=ft.Colors.WHITE, size=20),
            ft.CircleAvatar(radius=14, bgcolor="#27272A"),
        ]

        yt_topbar_content_player = [
            ft.Icon(ft.Icons.MENU, color=ft.Colors.WHITE, size=22),
            yt_brand_player,
            ft.Container(expand=True),
            ft.Container(width=520, content=self.yt_search_field_player),
            ft.Container(
                width=46,
                height=40,
                border_radius=20,
                bgcolor="#202020",
                ink=True,
                on_click=self._do_youtube_search,
                alignment=ft.alignment.center,
                content=ft.Icon(ft.Icons.SEARCH, color=ft.Colors.WHITE, size=20),
            ),
            ft.Container(expand=True),
            ft.Icon(ft.Icons.MIC, color=ft.Colors.WHITE, size=20),
            ft.Icon(ft.Icons.NOTIFICATIONS_NONE, color=ft.Colors.WHITE, size=20),
            ft.CircleAvatar(radius=14, bgcolor="#27272A"),
        ]

        self.yt_topbar_home = ft.Container(
            bgcolor="#0F0F0F",
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            content=ft.Row(
                [yt_topbar_content_home[0], ft.Container(width=24), *yt_topbar_content_home[1:]],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.yt_topbar_player = ft.Container(
            bgcolor="#0F0F0F",
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            content=ft.Row(
                [yt_topbar_content_player[0], self.yt_back_button, *yt_topbar_content_player[1:]],
               spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        nav_items = [
            ("Trang chủ", ft.Icons.HOME),
            ("Shorts", ft.Icons.PLAY_ARROW),
            ("Kênh đăng ký", ft.Icons.SUBSCRIPTIONS),
            ("Video đã xem", ft.Icons.HISTORY),
            ("Danh sách phát", ft.Icons.VIDEO_LIBRARY),
            ("Xem sau", ft.Icons.WATCH_LATER),
        ]
        nav_list = ft.ListView(
            expand=True,
            spacing=6,
            controls=[
                ft.Container(
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    bgcolor="#1F1F1F" if index == 0 else "transparent",
                    content=ft.Row(
                        [
                            ft.Icon(icon, size=18, color=ft.Colors.WHITE),
                            ft.Text(label, color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.W_600),
                        ],
                        spacing=10,
                    ),
                )
                for index, (label, icon) in enumerate(nav_items)
            ],
        )

        category_labels = [
            "Tất cả", "Âm nhạc", "Danh sách kết hợp", "Trực tiếp",
            "Hoạt ảnh", "Đọc rap", "Bảng xếp hạng", "Mới tải lên gần đây",
        ]
        category_row = ft.Container(
            height=44,
            content=ft.ListView(
                horizontal=True,
                spacing=10,
                controls=[
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=14, vertical=8),
                        border_radius=18,
                        bgcolor="#FFFFFF" if index == 0 else "#2A2A2A",
                        content=ft.Text(label, size=11, color="#0F0F0F" if index == 0 else ft.Colors.WHITE),
                    )
                    for index, label in enumerate(category_labels)
                ],
            ),
        )

        self.yt_home_view = ft.Container(
            expand=True,
            bgcolor="#0F0F0F",
            content=ft.Column(
                [
                     self.yt_topbar_home,
                    ft.Row(
                        [
                            ft.Container(
                                width=220,
                                padding=ft.padding.only(left=8, right=8, top=8, bottom=8),
                                content=nav_list,
                            ),
                            ft.Container(
                                expand=True,
                                padding=ft.padding.only(left=10, right=10, top=8),
                                content=ft.Column(
                                    [
                                        category_row,
                                        ft.Container(height=8),
                                        self.yt_home_grid,
                                    ],
                                    expand=True,
                                ),
                            ),
                        ],
                        expand=True,
                    ),
                ],
                expand=True,
                spacing=0,
            ),
        )

        player_video = ft.Container(
            height=420,
            border_radius=16,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=ft.Colors.BLACK,
            content=ft.Stack(
                [
                    self.yt_current_image,
                    self.yt_embedded_video,
                ],
                expand=True,
            ),
        )

        player_controls = ft.Column(
            [
                ft.Row(
                    [
                        self.yt_time_current,
                        ft.Container(expand=True, content=self.yt_progress_slider),
                        self.yt_time_total,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                ft.Row(
                    [
                        icon_button(ft.Icons.SKIP_PREVIOUS, on_click=self.yt_prev_video, kind="surface", icon_size=18, tooltip="Video trước"),
                        icon_button(ft.Icons.REPLAY_10, on_click=lambda e: self.yt_seek_relative(-10), kind="surface", icon_size=18, tooltip="Tua -10s"),
                        icon_button(ft.Icons.FORWARD_10, on_click=lambda e: self.yt_seek_relative(10), kind="surface", icon_size=18, tooltip="Tua +10s"),
                        icon_button(ft.Icons.SKIP_NEXT, on_click=self.yt_next_video, kind="surface", icon_size=18, tooltip="Video sau"),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=6,
                ),
            ],
            spacing=8,
        )

        player_meta = ft.Column(
            [
                self.yt_current_title,
                self.yt_current_channel,
                self.yt_current_hint,
                player_controls,
            ],
            spacing=6,
        )

        player_sidebar = ft.Container(
            width=320,
            bgcolor="#121212",
            border_radius=14,
            padding=ft.padding.all(12),
            content=ft.Column(
                [
                    ft.Text("Tiếp theo", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    self.yt_status_text,
                    self.yt_sidebar_list,
                ],
                spacing=10,
                expand=True,
            ),
        )

        self.yt_player_view = ft.Container(
            expand=True,
            visible=False,
            bgcolor="#0F0F0F",
            content=ft.Column(
                [
                    self.yt_topbar_player,
                   ft.Container(
                        expand=True,
                        padding=ft.padding.all(12),
                        content=ft.Row(
                            [
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        [player_video, ft.Container(height=8), player_meta],
                                        spacing=10,
                                    ),
                                ),
                                player_sidebar,
                            ],
                            spacing=16,
                            expand=True,
                        ),
                    ),
                ],
                expand=True,
                spacing=0,
            ),
        )

        self.yt_view_stack = ft.Stack([self.yt_home_view, self.yt_player_view], expand=True)

        youtube_shell = ft.Container(
            bgcolor="#0F0F0F",
            border_radius=18,
            height=760,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(blur_radius=18, color=ft.Colors.BLACK45),
            content=self.yt_view_stack,

        )

        map_header = ft.Row([
            ft.Image(src=IMG_MAP, width=25, height=25),
            ft.Text("Bản Đồ", size=16, weight="bold", color=ft.Colors.WHITE)
        ], alignment=ft.MainAxisAlignment.CENTER)

        map_img_url = "https://media.wired.com/photos/59269cd37034dc5f91bec0f1/191:100/w_1280,c_limit/GoogleMapTA.jpg"
        
        map_box = ft.Container(
            height=160, border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK26),
            ink=True, on_click=self.open_map_dialog, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Stack([
                ft.Image(src=map_img_url, fit=ft.ImageFit.COVER, width=float('inf'), height=float('inf')),
                ft.Container(alignment=ft.alignment.center, content=ft.Icon(ft.Icons.LOCATION_ON, size=60, color=ft.Colors.GREEN_600))
            ])
        )

        # ÉP TRÀN VIỀN: SỬ DỤNG MARGIN ÂM (NẾU KHUNG CHA CÓ PADDING) VÀ EXPAND
        main_content = ft.Container(
            padding=ft.padding.only(left=40, right=40, top=30, bottom=20), 
            expand=True, # Ép tràn kích thước
            content=ft.Column([
                weather_header,
                weather_box,
                ft.Container(height=15),
                youtube_shell,
                ft.Container(height=15),
                ft.Row([

                    ft.Column([map_header, map_box], expand=1)
                ], spacing=20, alignment=ft.MainAxisAlignment.START),
            ], scroll=ft.ScrollMode.AUTO)
        )


        # STACK CŨNG ĐƯỢC ÉP MARGIN ÂM ĐỂ TRÀN TOÀN DIỆN
        self.controls = [
            ft.Stack([
                bg_image,
                bg_overlay,
                main_content
            ], expand=True)
        ]
        # Bắt buộc cho layout gốc
        self.expand = True 
        self.margin = ft.margin.all(-20)
        self._show_yt_view(self.yt_view_mode)

