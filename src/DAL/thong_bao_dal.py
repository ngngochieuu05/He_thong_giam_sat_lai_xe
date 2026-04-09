"""
thong_bao_dal.py
CRUD cho bảng: Thong_Bao_Log, Telegram_Tokens
"""
from __future__ import annotations
from typing import Optional
import pyodbc
from .db_connection import get_connection


# ══════════════════════════════════════════════
# Thong_Bao_Log
# ══════════════════════════════════════════════

def luu_thong_bao_log(
    log_time:      str,
    chat_id:       str,
    content:       str,
    trang_thai:    str,                  # 'success' | 'fail'
    error_message: Optional[str] = None,
) -> None:
    """Ghi log thông báo Telegram (giữ tối đa 700 bản ghi)."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "EXEC sp_Luu_ThongBaoLog @log_time=?, @chat_id=?, @content=?, @trang_thai=?, @error_message=?",
        log_time, chat_id, content, trang_thai, error_message,
    )
    conn.commit()


def lay_thong_bao_logs(limit: int = 200) -> list[pyodbc.Row]:
    """Lấy *limit* bản ghi log mới nhất."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        f"SELECT TOP {int(limit)} log_id, log_time, chat_id, content, trang_thai, error_message, created_at "
        "FROM Thong_Bao_Log ORDER BY log_id DESC",
    )
    return cur.fetchall()


def xoa_thong_bao_logs() -> int:
    """Xóa toàn bộ log. Trả về số bản ghi đã xóa."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM Thong_Bao_Log")
    count = cur.rowcount
    conn.commit()
    return count


# ══════════════════════════════════════════════
# Telegram_Tokens
# ══════════════════════════════════════════════

def them_telegram_token(
    token:      str,
    username:   str,
    expires_at: str,         # ISO datetime string 'YYYY-MM-DD HH:MM:SS'
) -> None:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO Telegram_Tokens (token, username, expires_at) VALUES (?, ?, ?)",
        token, username, expires_at,
    )
    conn.commit()


def kiem_tra_token(token: str) -> Optional[pyodbc.Row]:
    """Trả về row nếu token hợp lệ & chưa dùng & chưa hết hạn."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        """
        SELECT token_id, username, expires_at
        FROM   Telegram_Tokens
        WHERE  token=? AND is_used=0 AND expires_at > GETDATE()
        """,
        token,
    )
    return cur.fetchone()


def danh_dau_da_dung_token(token: str) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE Telegram_Tokens SET is_used=1 WHERE token=?", token)
    conn.commit()
    return cur.rowcount > 0
