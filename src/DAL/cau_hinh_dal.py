"""
cau_hinh_dal.py
CRUD cho bảng Cau_Hinh_He_Thong (system configuration key-value store)
"""
from __future__ import annotations
from typing import Optional
import pyodbc
from .db_connection import get_connection


def lay_gia_tri(config_key: str) -> Optional[str]:
    """Trả về config_value theo key, None nếu không tìm thấy."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT config_value FROM Cau_Hinh_He_Thong WHERE config_key=?",
        config_key,
    )
    row = cur.fetchone()
    return row[0] if row else None


def lay_tat_ca_cau_hinh() -> dict[str, str]:
    """Trả về toàn bộ cấu hình dưới dạng dict {key: value}."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT config_key, config_value FROM Cau_Hinh_He_Thong")
    return {row[0]: row[1] for row in cur.fetchall()}


def dat_gia_tri(config_key: str, config_value: str, description: Optional[str] = None) -> None:
    """Upsert một cặp key-value."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        """
        MERGE Cau_Hinh_He_Thong AS T
        USING (SELECT ? AS k) AS S ON T.config_key = S.k
        WHEN MATCHED THEN
            UPDATE SET config_value=?, description=COALESCE(?, description), updated_at=GETDATE()
        WHEN NOT MATCHED THEN
            INSERT (config_key, config_value, description)
            VALUES (?, ?, ?);
        """,
        config_key, config_value, description,
        config_key, config_value, description,
    )
    conn.commit()


def cap_nhat_nhieu(data: dict[str, str]) -> None:
    """Cập nhật nhiều key-value một lần (batch upsert)."""
    conn = get_connection()
    cur  = conn.cursor()
    for key, value in data.items():
        cur.execute(
            """
            MERGE Cau_Hinh_He_Thong AS T
            USING (SELECT ? AS k) AS S ON T.config_key = S.k
            WHEN MATCHED     THEN UPDATE SET config_value=?, updated_at=GETDATE()
            WHEN NOT MATCHED THEN INSERT (config_key, config_value) VALUES (?, ?);
            """,
            key, value, key, value,
        )
    conn.commit()
