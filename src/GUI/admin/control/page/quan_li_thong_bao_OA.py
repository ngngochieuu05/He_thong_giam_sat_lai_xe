import flet as ft
import os
import json
import threading
from datetime import datetime
from ..ui_styles import (
    BORDER,
    DANGER,
    PRIMARY,
    SECONDARY,
    SURFACE,
    SURFACE_STRONG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    elevated_button,
    glass_card,
    input_style,
    section_title,
    text_button,
)

# Import ThongBaoService từ BUS layer
from src.BUS.oa_core.sua_thong_bao.tuy_chinh_thong_bao import ThongBaoService

# Import hàm export để đồng bộ DB → JSON sau mỗi lưu
def _bg_export():
    """Chạy export_db_to_json trong background thread để không block UI."""
    try:
        from src.DAL.sync_json_to_db import export_db_to_json
        export_db_to_json()
    except Exception as _e:
        print(f"[EXPORT] Lỗi đồng bộ: {_e}")

# ===== KHỞI TẠO SERVICE =====
thong_bao_service = ThongBaoService()

# ===== CẤU HÌNH TELEGRAM =====
TELEGRAM_BOT_TOKEN = thong_bao_service.get_default_token()
DEFAULT_CHAT_ID = thong_bao_service.get_default_chat_id()


def QuanLiThongBao(page_title):
    # Biến local để lưu chat_id (không dùng global)
    current_chat_id = DEFAULT_CHAT_ID

    # Đường dẫn tới model_config.json
    _cfg_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "model_config.json"
    ))

    def _read_model_config():
        try:
            with open(_cfg_path, "r", encoding="utf-8") as _f:
                return json.load(_f)
        except Exception:
            return {}

    def _write_model_config(cfg: dict):
        try:
            with open(_cfg_path, "w", encoding="utf-8") as _f:
                json.dump(cfg, _f, ensure_ascii=False, indent=2)
            return True
        except Exception as _e:
            print(f"❌ [GEMINI_CFG] Write failed: {_e}")
            return False
    
    # Biến để lưu reference đến các control
    field_style = input_style()
    status_text = ft.Text("", size=14, color=TEXT_SECONDARY)

    # ===== GEMINI API KEY =====
    _init_cfg = _read_model_config()
    _init_groq_key = _init_cfg.get("ai_api", {}).get("groq_api_key", "")

    gemini_status_text = ft.Text("", size=13)
    gemini_key_field = ft.TextField(
        label="ChatBox API Key",
        value=_init_groq_key,
        prefix_icon=ft.Icons.VPN_KEY,
        password=True,
        can_reveal_password=True,
        hint_text="AIza...",
        expand=True,
        **field_style,
    )

    def on_save_gemini_key(e):
        new_key = gemini_key_field.value.strip()
        cfg = _read_model_config()
        cfg.setdefault("ai_api", {})["groq_api_key"] = new_key
        if _write_model_config(cfg):
            gemini_status_text.value = "✅ Đã lưu Groq API Key!"
            gemini_status_text.color = PRIMARY
            threading.Thread(target=_bg_export, daemon=True).start()
        else:
            gemini_status_text.value = "❌ Lưu thất bại!"
            gemini_status_text.color = DANGER
        gemini_status_text.update()

    gemini_config_card = glass_card(
        ft.Column([
            section_title("Cấu Hình Groq AI (Chatbox)", ft.Icons.SMART_TOY, SECONDARY),
            ft.Divider(color=BORDER),
            ft.Text(
                "🔑 Key được sử dụng cho chatbox trợ lý AI của tài xế.",
                size=13, color=TEXT_SECONDARY
            ),
            ft.Container(height=6),
            gemini_key_field,
            ft.Container(height=8),
            ft.Row([
                elevated_button("Lưu API Key", icon=ft.Icons.SAVE, kind="secondary", on_click=on_save_gemini_key),
            ], alignment=ft.MainAxisAlignment.END),
            gemini_status_text,
        ]),
        bgcolor=SURFACE_STRONG,
    )
    # ===== END GEMINI =====

    # ===== YOUTUBE API KEY =====
    _init_yt_key = _init_cfg.get("ai_api", {}).get("youtube_api_key", "")

    youtube_status_text = ft.Text("", size=13)
    youtube_key_field = ft.TextField(
        label="YouTube Data API v3 Key",
        value=_init_yt_key,
        prefix_icon=ft.Icons.PLAY_CIRCLE,
        password=True,
        can_reveal_password=True,
        hint_text="AIzaSy...",
        expand=True,
        **field_style,
    )

    def on_save_youtube_key(e):
        new_key = youtube_key_field.value.strip()
        cfg = _read_model_config()
        cfg.setdefault("ai_api", {})["youtube_api_key"] = new_key
        if _write_model_config(cfg):
            youtube_status_text.value = "✅ Đã lưu YouTube API Key!"
            youtube_status_text.color = PRIMARY
            threading.Thread(target=_bg_export, daemon=True).start()
        else:
            youtube_status_text.value = "❌ Lưu thất bại!"
            youtube_status_text.color = DANGER
        youtube_status_text.update()

    youtube_config_card = glass_card(
        ft.Column([
            section_title("Cấu Hình YouTube API", ft.Icons.PLAY_CIRCLE_FILLED, "#FF0000"),
            ft.Divider(color=BORDER),
            ft.Text(
                "🔑 Key YouTube Data API v3 — cho phép tài xế tìm kiếm nhạc & video YouTube trong tiện ích.",
                size=13, color=TEXT_SECONDARY
            ),
            ft.Text(
                "📌 Lấy key miễn phí tại: console.cloud.google.com → YouTube Data API v3",
                size=11, color=TEXT_SECONDARY, italic=True,
            ),
            ft.Container(height=6),
            youtube_key_field,
            ft.Container(height=8),
            ft.Row([
                elevated_button("Lưu API Key", icon=ft.Icons.SAVE, kind="secondary", on_click=on_save_youtube_key),
            ], alignment=ft.MainAxisAlignment.END),
            youtube_status_text,
        ]),
        bgcolor=SURFACE_STRONG,
    )
    # ===== END YOUTUBE =====
    
    # Chat ID field - cho phép chỉnh sửa
    chat_id_field = ft.TextField(
        label="Chat ID", 
        value=current_chat_id,
        prefix_icon=ft.Icons.CHAT,
        on_change=lambda e: update_chat_id(e.control.value),
        **field_style,
    )
    
    def update_chat_id(new_id: str):
        """Cập nhật Chat ID khi người dùng thay đổi"""
        nonlocal current_chat_id
        if new_id.strip():
            current_chat_id = new_id.strip()
    
    message_input = ft.TextField(
        label="Nội dung tin nhắn", 
        prefix_icon=ft.Icons.MESSAGE,
        multiline=True,
        min_lines=3,
        max_lines=5,
        value="🚨 <b>Cảnh báo!</b>\nHệ thống phát hiện tài xế có dấu hiệu buồn ngủ.",
        **field_style,
    )
    
    # Tạo DataTable cho log
    log_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Thời gian", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Nội dung", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Trạng thái", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
        border=ft.border.all(1, BORDER),
        border_radius=16,
        vertical_lines=ft.border.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        heading_row_color=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
    )
    
    def load_logs_from_json():
        """Load log từ thong_bao_log.json và hiển thị lên DataTable"""
        logs = thong_bao_service.load_log()
        log_table.rows.clear()
        
        # Lấy tối đa 20 log để hiển thị
        for log in logs[:20]:
            time_str = log.get("time", "N/A")
            content = log.get("content", "")
            status = log.get("status", "")
            
            if status == "success":
                status_text_log = ft.Text("✓ Thành công", color=PRIMARY)
            else:
                status_text_log = ft.Text("✗ Thất bại", color=DANGER)
            
            log_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(time_str, color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text(content[:50] + "..." if len(content) > 50 else content, color=TEXT_SECONDARY)),
                ft.DataCell(status_text_log),
            ]))
    
    def add_log_to_table(content: str, success: bool):
        """Thêm log vào bảng hiển thị"""
        time_str = datetime.now().strftime("%d/%m %H:%M:%S")
        status_text_log = ft.Text("✓ Thành công", color=PRIMARY) if success else ft.Text("✗ Thất bại", color=DANGER)
        
        log_table.rows.insert(0, ft.DataRow(cells=[
            ft.DataCell(ft.Text(time_str, color=TEXT_SECONDARY)),
            ft.DataCell(ft.Text(content[:50] + "..." if len(content) > 50 else content, color=TEXT_SECONDARY)),
            ft.DataCell(status_text_log),
        ]))
        
        # Giữ tối đa 20 log trên UI
        if len(log_table.rows) > 20:
            log_table.rows.pop()
        
        log_table.update()
    
    def on_test_connection(e):
        """Xử lý kiểm tra kết nối - dùng ThongBaoService"""
        status_text.value = "⏳ Đang kiểm tra kết nối..."
        status_text.color = ft.Colors.ORANGE
        status_text.update()
        
        # Sử dụng ThongBaoService.test_connection()
        result = thong_bao_service.test_connection(TELEGRAM_BOT_TOKEN)
        
        if result.get("ok"):
            bot_info = result.get("result", {})
            bot_name = bot_info.get("first_name", "Unknown")
            bot_username = bot_info.get("username", "Unknown")
            status_text.value = f"✅ Kết nối thành công!\nBot: {bot_name} (@{bot_username})"
            status_text.color = PRIMARY
        else:
            error = result.get("error", result.get("description", "Lỗi không xác định"))
            status_text.value = f"❌ Kết nối thất bại: {error}"
            status_text.color = DANGER
        
        status_text.update()
    
    def on_send_message(e):
        """Xử lý gửi tin nhắn - dùng ThongBaoService"""
        msg = message_input.value.strip()
        if not msg:
            status_text.value = "⚠️ Vui lòng nhập nội dung tin nhắn!"
            status_text.color = ft.Colors.ORANGE
            status_text.update()
            return
        
        status_text.value = "⏳ Đang gửi tin nhắn..."
        status_text.color = ft.Colors.ORANGE
        status_text.update()
        
        # Sử dụng ThongBaoService.send_message()
        result = thong_bao_service.send_message(TELEGRAM_BOT_TOKEN, current_chat_id, msg)
        
        if result.get("ok"):
            status_text.value = "✅ Gửi tin nhắn thành công!"
            status_text.color = PRIMARY
            add_log_to_table(msg, True)
        else:
            error = result.get("error", result.get("description", "Lỗi không xác định"))
            status_text.value = f"❌ Gửi thất bại: {error}"
            status_text.color = DANGER
            add_log_to_table(msg, False)
        
        status_text.update()
    
    def on_send_test_alert(e):
        """Gửi cảnh báo test nhanh - dùng ThongBaoService"""
        test_msg = f"""🚨 <b>CẢNH BÁO HỆ THỐNG</b>

⚠️ <b>Loại:</b> Phát hiện buồn ngủ
👤 <b>Tài xế:</b> Nguyễn Văn A
🚗 <b>Biển số:</b> 30A-12345
📍 <b>Vị trí:</b> Quốc lộ 1A, Km 52
⏰ <b>Thời gian:</b> {datetime.now().strftime("%H:%M:%S %d/%m/%Y")}

<i>Đây là tin nhắn test từ Hệ thống Giám sát Lái xe</i>"""
        
        status_text.value = "⏳ Đang gửi cảnh báo test..."
        status_text.color = ft.Colors.ORANGE
        status_text.update()
        
        # Sử dụng ThongBaoService.send_message()
        result = thong_bao_service.send_message(TELEGRAM_BOT_TOKEN, current_chat_id, test_msg)
        
        if result.get("ok"):
            status_text.value = "✅ Gửi cảnh báo test thành công!"
            status_text.color = PRIMARY
            add_log_to_table("Cảnh báo test", True)
        else:
            error = result.get("error", result.get("description", "Lỗi không xác định"))
            status_text.value = f"❌ Gửi thất bại: {error}"
            status_text.color = DANGER
            add_log_to_table("Cảnh báo test", False)
        
        status_text.update()
    
    def on_clear_log(e):
        """Xóa toàn bộ log"""
        thong_bao_service.clear_log()
        log_table.rows.clear()
        log_table.update()
        status_text.value = "🗑️ Đã xóa lịch sử!"
        status_text.color = ft.Colors.BLUE
        status_text.update()
    
    def on_reload_log(e):
        """Reload log từ file JSON"""
        load_logs_from_json()
        log_table.update()
        status_text.value = "🔄 Đã tải lại log!"
        status_text.color = ft.Colors.BLUE
        status_text.update()

    # Load log từ JSON khi khởi tạo
    load_logs_from_json()

    # ===== UI COMPONENTS =====
    
    # 1. Card cấu hình Telegram
    api_config_card = glass_card(
        ft.Column([
            section_title("Cấu Hình Telegram", ft.Icons.TELEGRAM, SECONDARY),
            ft.Divider(color=BORDER),
            # Bot Token - ẨN HOÀN TOÀN dưới dạng password
            ft.TextField(
                label="Bot Token", 
                value="••••••••••••••••••••••••••••••••••••••••••••",
                prefix_icon=ft.Icons.KEY,
                password=True,
                can_reveal_password=False,
                read_only=True,
                **field_style,
            ),
            # Chat ID - CHO PHÉP CHỈNH SỬA
            chat_id_field,
            ft.Container(height=10),
            ft.Row([
                elevated_button("Kiểm tra kết nối", icon=ft.Icons.WIFI_TETHERING, kind="secondary", on_click=on_test_connection),
            ], alignment=ft.MainAxisAlignment.END),
            ft.Container(height=10),
            status_text,
        ]),
        bgcolor=SURFACE_STRONG,
    )
    
    # 2. Card gửi tin nhắn
    send_message_card = glass_card(
        ft.Column([
            section_title("Gửi Thông Báo", ft.Icons.SEND, PRIMARY),
            ft.Divider(color=BORDER),
            message_input,
            ft.Container(height=10),
            ft.Row([
                elevated_button("Gửi Cảnh Báo Test", icon=ft.Icons.WARNING_AMBER, kind="warning", on_click=on_send_test_alert),
                elevated_button("Gửi Tin Nhắn", icon=ft.Icons.SEND, kind="primary", on_click=on_send_message),
            ], alignment=ft.MainAxisAlignment.END, spacing=10),
        ]),
        bgcolor=SURFACE_STRONG,
    )

    # 3. Card lịch sử gửi
    log_card = glass_card(
        ft.Column([
            ft.Row([
                section_title("Lịch Sử Gửi Tin", ft.Icons.HISTORY, SECONDARY),
                ft.Container(expand=True),
                text_button("Tải lại", icon=ft.Icons.REFRESH, on_click=on_reload_log, kind="surface"),
                text_button("Xóa Log", icon=ft.Icons.DELETE_SWEEP, on_click=on_clear_log, kind="surface")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color=BORDER),
            ft.Container(
                content=log_table, 
                padding=0, 
                expand=True,
            )
        ], expand=True),
        expand=True,
        bgcolor=SURFACE_STRONG,
    )

    # ===== LAYOUT CHÍNH =====
    return ft.Container(
        expand=True,
        content=ft.Column([
            ft.Column([
                ft.Text("Quản Lý Thông Báo & Dữ Liệu", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Nền trang giữ ảnh phía sau và toàn bộ khối trắng đã đổi sang glass card đồng bộ với giao diện mới.", size=13, color=TEXT_SECONDARY),
            ], spacing=4),
            ft.Container(height=10),
            ft.Row([
                ft.Column([
                    api_config_card,
                    ft.Container(height=15),
                    gemini_config_card,
                    ft.Container(height=15),
                    youtube_config_card,
                    ft.Container(height=15),
                    send_message_card,
                ], width=420),
                ft.Container(content=log_card, expand=True),
            ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START, spacing=20),
            ft.Container(height=12),
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
    )