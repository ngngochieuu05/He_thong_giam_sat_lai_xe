"""
sync_json_to_db.py
══════════════════════════════════════════════════════════════════
Đồng bộ dữ liệu từ tất cả file .json vào SQL Server.

Chạy một lần:
    (venv) python -m src.DAL.sync_json_to_db
hoặc từ thư mục giam_sat_lai_xe:
    (venv) python src/DAL/sync_json_to_db.py

Các file JSON được xử lý:
  1. src/GUI/data/accounts.json          → Admin_Accounts, Tai_Xe, Tong_Ket_Tai_Xe
  2. src/GUI/data/model_config.json      → Cau_Hinh_He_Thong
  3. src/GUI/data/API.json               → Cau_Hinh_He_Thong
  4. src/GUI/data/thong_bao_log.json     → Thong_Bao_Log
  5. src/GUI/data/telegram_tokens.json   → Telegram_Tokens
  Tất cả JSON đã chuyển về src/GUI/data/ làm nguồn duy nhất.
══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations
import json
import pathlib
import sys
import pyodbc

# ── đảm bảo import được khi chạy trực tiếp ──
_ROOT = pathlib.Path(__file__).resolve().parents[2]   # giam_sat_lai_xe/
sys.path.insert(0, str(_ROOT))

from src.DAL.db_connection import get_connection, test_connection  # noqa: E402

# ── đường dẫn gốc đến các file json ──
_SRC = _ROOT / "src"
_GUI_DATA      = _SRC / "GUI/data"
_ACCOUNTS_JSON = _GUI_DATA / "accounts.json"
_MODEL_CFG_JSON= _GUI_DATA / "model_config.json"
_API_JSON      = _GUI_DATA / "API.json"
_LOG_JSON      = _GUI_DATA / "thong_bao_log.json"
_TOKENS_JSON   = _GUI_DATA / "telegram_tokens.json"


# ════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════

def _read_json(path: pathlib.Path) -> dict | list | None:
    if not path.exists():
        print(f"  [SKIP] Không tìm thấy: {path}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _ensure_columns(conn: pyodbc.Connection) -> None:
    """
    Thêm cột phone, face_data, role vào bảng nếu chưa tồn tại.
    DB đã tồn tại sẵn, chỉ ALTER TABLE nếu cần.
    """
    cur = conn.cursor()
    migrations = [
        ("Tai_Xe",         "phone",     "NVARCHAR(30)  NULL"),
        ("Tai_Xe",         "face_data", "NVARCHAR(MAX) NULL"),
        ("Admin_Accounts", "role",      "NVARCHAR(50)  NOT NULL DEFAULT 'Admin'"),
    ]
    for table, col, dtype in migrations:
        cur.execute(
            """
            IF NOT EXISTS (
                SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME=? AND COLUMN_NAME=?
            )
            BEGIN
                EXEC('ALTER TABLE [' + ? + '] ADD [' + ? + '] ' + ?)
            END
            """,
            table, col, table, col, dtype,
        )
    # Đảm bảo seed row youtube_api_key tồn tại
    cur.execute(
        """
        IF NOT EXISTS (SELECT 1 FROM Cau_Hinh_He_Thong WHERE config_key='youtube_api_key')
            INSERT INTO Cau_Hinh_He_Thong (config_key, config_value, description)
            VALUES ('youtube_api_key', '', 'YouTube Data API v3 key')
        """
    )
    conn.commit()
    print("[MIGRATE] Kiểm tra / thêm cột xong.")


# ════════════════════════════════════════════
# 1. accounts.json → Admin_Accounts + Tai_Xe
# ════════════════════════════════════════════

def _sync_accounts(conn: pyodbc.Connection) -> None:
    data = _read_json(_ACCOUNTS_JSON)
    if data is None:
        return
    cur = conn.cursor()

    # ── admin accounts ──
    for adm in data.get("admin_accounts", []):
        cur.execute(
            "SELECT COUNT(1) FROM Admin_Accounts WHERE username=?",
            adm["username"],
        )
        if cur.fetchone()[0] == 0:
            cur.execute(
                """
                INSERT INTO Admin_Accounts (username, password, name, role)
                VALUES (?, ?, ?, ?)
                """,
                adm["username"],
                adm["password"],
                adm.get("name", adm["username"]),
                adm.get("role", "Admin"),
            )
            print(f"  [Admin] Thêm: {adm['username']}")
        else:
            cur.execute(
                "UPDATE Admin_Accounts SET password=?, name=?, updated_at=GETDATE() WHERE username=?",
                adm["password"],
                adm.get("name", adm["username"]),
                adm["username"],
            )
            print(f"  [Admin] Cập nhật: {adm['username']}")

    # ── user (driver) accounts ──
    for u in data.get("user_accounts", []):
        face_data = None
        fd = u.get("face_data")
        if isinstance(fd, str):
            face_data = fd.strip() or None
        elif isinstance(fd, dict):
            face_data = (fd.get("encrypted_image") or "").strip() or None

        cur.execute(
            "SELECT tai_xe_id FROM Tai_Xe WHERE username=? OR driver_id=?",
            u["username"], u.get("driver_id", ""),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                """
                INSERT INTO Tai_Xe
                    (driver_id, username, name, password, phone, face_data, goi_dich_vu)
                OUTPUT INSERTED.tai_xe_id
                VALUES (?, ?, ?, ?, ?, ?, 'Free')
                """,
                u.get("driver_id", ""),
                u["username"],
                u.get("name", u["username"]),
                u.get("password", ""),
                u.get("phone"),
                face_data,
            )
            tai_xe_id = cur.fetchone()[0]
            # tạo bản ghi tổng kết nếu chưa có
            cur.execute(
                "IF NOT EXISTS (SELECT 1 FROM Tong_Ket_Tai_Xe WHERE tai_xe_id=?) "
                "INSERT INTO Tong_Ket_Tai_Xe (tai_xe_id) VALUES (?)",
                tai_xe_id, tai_xe_id,
            )
            print(f"  [TaiXe] Thêm: {u['username']} ({u.get('driver_id','')})")
        else:
            tai_xe_id = row[0]
            if face_data is None:
                cur.execute(
                    """
                    UPDATE Tai_Xe
                    SET    name=?, password=?, phone=?, updated_at=GETDATE()
                    WHERE  tai_xe_id=?
                    """,
                    u.get("name", u["username"]),
                    u.get("password", ""),
                    u.get("phone"),
                    tai_xe_id,
                )
            else:
                cur.execute(
                    """
                    UPDATE Tai_Xe
                    SET    name=?, password=?, phone=?, face_data=?, updated_at=GETDATE()
                    WHERE  tai_xe_id=?
                    """,
                    u.get("name", u["username"]),
                    u.get("password", ""),
                    u.get("phone"),
                    face_data,
                    tai_xe_id,
                )
            print(f"  [TaiXe] Cập nhật: {u['username']}")

    conn.commit()
    print("[SYNC] accounts.json ✅")


# ════════════════════════════════════════════
# 2. model_config.json → Cau_Hinh_He_Thong
# ════════════════════════════════════════════

def _sync_model_config(conn: pyodbc.Connection) -> None:
    data = _read_json(_MODEL_CFG_JSON)
    if data is None:
        return
    cur = conn.cursor()

    def _upsert(key: str, value: str, desc: str = "") -> None:
        cur.execute(
            """
            MERGE Cau_Hinh_He_Thong AS T
            USING (SELECT ? AS k) AS S ON T.config_key = S.k
            WHEN MATCHED THEN
                UPDATE SET config_value=?, updated_at=GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (config_key, config_value, description) VALUES (?, ?, ?);
            """,
            key, value, key, value, desc,
        )

    # face_recognition
    fr = data.get("face_recognition", {})
    _upsert("face_model_name",        str(fr.get("model_name", "")),        "Tên model nhận diện khuôn mặt")
    _upsert("face_model_path",        str(fr.get("model_path", "")),        "Đường dẫn model nhận diện khuôn mặt")
    _upsert("face_confidence",        str(fr.get("confidence_threshold", 0.75)), "Ngưỡng confidence nhận diện")
    _upsert("face_cosine_threshold",  str(fr.get("cosine_threshold", 0.5)), "Ngưỡng cosine similarity")
    _upsert("face_min_face_size",     str(fr.get("min_face_size", 60)),      "Kích thước khuôn mặt tối thiểu (px)")

    # drowsiness_detection
    dd = data.get("drowsiness_detection", {})
    _upsert("drowsy_model_name",  str(dd.get("model_name", "")),             "Tên model phát hiện ngủ gật")
    _upsert("drowsy_model_path",  str(dd.get("model_path", "")),             "Đường dẫn model ngủ gật")
    _upsert("drowsy_confidence",  str(dd.get("confidence_threshold", 0.5)),  "Ngưỡng confidence ngủ gật")
    _upsert("drowsy_iou",         str(dd.get("iou_threshold", 0.5)),         "Ngưỡng IOU")

    # camera
    cam = data.get("camera", {})
    _upsert("camera_default_index",    str(cam.get("default_index", 0)),    "Camera mặc định")
    _upsert("camera_width",            str(cam.get("resolution_width", 640)), "Độ phân giải ngang")
    _upsert("camera_height",           str(cam.get("resolution_height", 480)), "Độ phân giải dọc")
    _upsert("camera_fps",              str(cam.get("fps", 30)),              "FPS camera")

    # ai_api
    ai = data.get("ai_api", {})
    if ai.get("groq_api_key"):
        _upsert("groq_api_key",     str(ai["groq_api_key"]),     "Groq API key")
    if ai.get("weather_api_key"):
        _upsert("weather_api_key",  str(ai["weather_api_key"]),  "OpenWeather API key")
    if ai.get("city"):
        _upsert("weather_city",     str(ai["city"]),             "Thành phố mặc định thời tiết")
    if ai.get("youtube_api_key"):
        _upsert("youtube_api_key",  str(ai["youtube_api_key"]),  "YouTube Data API v3 key")

    conn.commit()
    print("[SYNC] model_config.json ✅")


# ════════════════════════════════════════════
# 3. API.json → Cau_Hinh_He_Thong
# ════════════════════════════════════════════

def _sync_api_json(conn: pyodbc.Connection) -> None:
    data = _read_json(_API_JSON)
    if data is None:
        return
    cur = conn.cursor()

    def _upsert(key: str, value: str, desc: str = "") -> None:
        cur.execute(
            """
            MERGE Cau_Hinh_He_Thong AS T
            USING (SELECT ? AS k) AS S ON T.config_key = S.k
            WHEN MATCHED THEN
                UPDATE SET config_value=?, updated_at=GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (config_key, config_value, description) VALUES (?, ?, ?);
            """,
            key, value, key, value, desc,
        )

    tele = data.get("telegram", {})
    if tele.get("bot_token"):
        _upsert("telegram_bot_token", tele["bot_token"], "Telegram bot token")
    if tele.get("chat_id"):
        _upsert("telegram_chat_id",   tele["chat_id"],   "Telegram chat ID mặc định")

    conn.commit()
    print("[SYNC] API.json ✅")


# ════════════════════════════════════════════
# 4. thong_bao_log.json → Thong_Bao_Log
# ════════════════════════════════════════════

def _sync_thong_bao_log(conn: pyodbc.Connection) -> None:
    data = _read_json(_LOG_JSON)
    if data is None:
        return
    cur = conn.cursor()

    # Đếm bản ghi hiện có để tránh import lại
    cur.execute("SELECT COUNT(1) FROM Thong_Bao_Log")
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"  [SKIP] Thong_Bao_Log đã có {existing} bản ghi, bỏ qua.")
        return

    logs = data.get("logs", [])
    inserted = 0
    for log in logs:
        cur.execute(
            """
            INSERT INTO Thong_Bao_Log (log_time, chat_id, content, trang_thai, error_message)
            VALUES (?, ?, ?, ?, ?)
            """,
            log.get("time", ""),
            log.get("chat_id", ""),
            log.get("content", ""),
            "success" if log.get("status") == "success" else "fail",
            log.get("error") or None,
        )
        inserted += 1

    conn.commit()
    print(f"[SYNC] thong_bao_log.json ✅  ({inserted} bản ghi)")


# ════════════════════════════════════════════
# 5. telegram_tokens.json → Telegram_Tokens
# ════════════════════════════════════════════

def _sync_telegram_tokens(conn: pyodbc.Connection) -> None:
    data = _read_json(_TOKENS_JSON)
    if data is None:
        return
    tokens = data.get("tokens", {})
    if not tokens:
        print("  [SKIP] telegram_tokens.json trống.")
        return
    cur = conn.cursor()
    inserted = 0
    for token, info in tokens.items():
        cur.execute("SELECT COUNT(1) FROM Telegram_Tokens WHERE token=?", token)
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO Telegram_Tokens (token, username, expires_at) VALUES (?, ?, ?)",
                token,
                info.get("username", ""),
                info.get("expires_at", "2099-01-01 00:00:00"),
            )
            inserted += 1
    conn.commit()
    print(f"[SYNC] telegram_tokens.json ✅  ({inserted} token mới)")


# ════════════════════════════════════════════
# 6. Dọn cấu hình music_library cũ
# ════════════════════════════════════════════

def _remove_music_library_config(conn: pyodbc.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM Cau_Hinh_He_Thong WHERE config_key='music_library'")
    conn.commit()
    print("[CLEANUP] Đã xóa cấu hình music_library khỏi DB nếu còn tồn tại")


# ════════════════════════════════════════════
# Entry point
# ════════════════════════════════════════════

def run_sync() -> None:
    print("=" * 60)
    print("   ĐỒNG BỘ DỮ LIỆU JSON → SQL SERVER")
    print("=" * 60)

    if not test_connection():
        print("[ERROR] Không kết nối được DB. Dừng đồng bộ.")
        return

    conn = get_connection()

    print("\n[1/7] Kiểm tra / bổ sung cột DB...")
    _ensure_columns(conn)

    print("\n[2/7] accounts.json...")
    _sync_accounts(conn)

    print("\n[3/7] model_config.json...")
    _sync_model_config(conn)

    print("\n[4/7] API.json...")
    _sync_api_json(conn)

    print("\n[5/7] thong_bao_log.json...")
    _sync_thong_bao_log(conn)

    print("\n[6/7] telegram_tokens.json...")
    _sync_telegram_tokens(conn)

    print("\n[7/7] Dọn cấu hình nhạc cũ...")
    _remove_music_library_config(conn)

    print("\n" + "=" * 60)
    print("   ✅ ĐỒNG BỘ HOÀN TẤT")
    print("=" * 60)


# ════════════════════════════════════════════
# Export DB → JSON (nguồn sự thật từ DB ra lại file)
# ════════════════════════════════════════════

def export_db_to_json() -> None:
    """
    Đọc dữ liệu từ DB và ghi ra các file JSON trong GUI/data.
    Gọi sau mỗi lần lưu cấu hình từ admin để giữ JSON đồng bộ với DB.
    """
    if not test_connection():
        return
    conn = get_connection()
    cur  = conn.cursor()

    # (1) API.json ← Cau_Hinh_He_Thong
    cur.execute(
        "SELECT config_key, config_value FROM Cau_Hinh_He_Thong "
        "WHERE config_key IN ('telegram_bot_token','telegram_chat_id')"
    )
    cfg_rows = {r[0]: (r[1] or "") for r in cur.fetchall()}
    api_data = {
        "telegram": {
            "bot_token": cfg_rows.get("telegram_bot_token", ""),
            "chat_id":   cfg_rows.get("telegram_chat_id",   ""),
        }
    }
    _GUI_DATA.mkdir(parents=True, exist_ok=True)
    with open(_API_JSON, "w", encoding="utf-8") as f:
        json.dump(api_data, f, ensure_ascii=False, indent=4)

    # (2) model_config.json ← Cau_Hinh_He_Thong
    key_map = [
        "face_model_name", "face_model_path", "face_confidence",
        "face_cosine_threshold", "face_min_face_size",
        "drowsy_model_name", "drowsy_model_path", "drowsy_confidence", "drowsy_iou",
        "camera_default_index", "camera_width", "camera_height", "camera_fps",
        "groq_api_key", "weather_api_key", "weather_city", "youtube_api_key",
    ]
    cur.execute(
        f"SELECT config_key, config_value FROM Cau_Hinh_He_Thong WHERE config_key IN ({','.join(['?']*len(key_map))})",
        *key_map,
    )
    cfg = {r[0]: (r[1] or "") for r in cur.fetchall()}
    if _MODEL_CFG_JSON.exists():
        with open(_MODEL_CFG_JSON, "r", encoding="utf-8") as f:
            model_cfg = json.load(f)
    else:
        model_cfg = {}
    ai_api = model_cfg.setdefault("ai_api", {})
    if cfg.get("groq_api_key"):    ai_api["groq_api_key"]    = cfg["groq_api_key"]
    if cfg.get("weather_api_key"): ai_api["weather_api_key"] = cfg["weather_api_key"]
    if cfg.get("weather_city"):    ai_api["city"]            = cfg["weather_city"]
    if cfg.get("youtube_api_key"): ai_api["youtube_api_key"] = cfg["youtube_api_key"]
    with open(_MODEL_CFG_JSON, "w", encoding="utf-8") as f:
        json.dump(model_cfg, f, ensure_ascii=False, indent=2)

    # (3) thong_bao_log.json ← Thong_Bao_Log (200 mới nhất)
    cur.execute(
        "SELECT TOP 200 log_time, chat_id, content, trang_thai, error_message "
        "FROM Thong_Bao_Log ORDER BY log_id DESC"
    )
    logs = [
        {"time": r[0], "chat_id": r[1], "content": r[2],
         "status": r[3], "error": r[4] or ""}
        for r in cur.fetchall()
    ]
    with open(_LOG_JSON, "w", encoding="utf-8") as f:
        json.dump({"logs": logs}, f, ensure_ascii=False, indent=2)

    # (4) telegram_tokens.json ← Telegram_Tokens (chưa dùng)
    cur.execute(
        "SELECT token, username, expires_at FROM Telegram_Tokens "
        "WHERE is_used=0 AND expires_at > GETDATE()"
    )
    tokens = {r[0]: {"username": r[1], "expires_at": str(r[2])} for r in cur.fetchall()}
    with open(_TOKENS_JSON, "w", encoding="utf-8") as f:
        json.dump({"tokens": tokens}, f, ensure_ascii=False, indent=2)

    print("[EXPORT] DB → JSON hoàn tất")


if __name__ == "__main__":
    run_sync()
