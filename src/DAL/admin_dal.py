"""
admin_dal.py
CRUD cho bảng Admin_Accounts
"""
from __future__ import annotations
from typing import Optional
import pyodbc
from .db_connection import get_connection


def dang_nhap_admin(username: str, password: str) -> bool:
    """Xác thực admin. Trả về True nếu thành công."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        """
        DECLARE @r INT;
        EXEC sp_DangNhap_Admin @username=?, @password=?, @ket_qua=@r OUTPUT;
        SELECT @r;
        """,
        username, password,
    )
    row = cur.fetchone()
    conn.commit()
    return bool(row and row[0] == 1)


def lay_admin_theo_username(username: str) -> Optional[pyodbc.Row]:
    """Trả về row admin, None nếu không tìm thấy."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT admin_id, username, name, role, is_active FROM Admin_Accounts WHERE username=? AND is_active=1",
        username,
    )
    return cur.fetchone()


def lay_tat_ca_admin() -> list[pyodbc.Row]:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT admin_id, username, name, role, is_active, created_at FROM Admin_Accounts ORDER BY admin_id")
    return cur.fetchall()


def them_admin(username: str, password: str, name: str, role: str = "Admin") -> int:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        """
        INSERT INTO Admin_Accounts (username, password, name, role)
        OUTPUT INSERTED.admin_id
        VALUES (?, ?, ?, ?)
        """,
        username, password, name, role,
    )
    admin_id: int = cur.fetchone()[0]
    conn.commit()
    return admin_id


def cap_nhat_admin(username: str, password: Optional[str] = None, name: Optional[str] = None) -> bool:
    fields, params = [], []
    if password is not None: fields.append("password=?"); params.append(password)
    if name     is not None: fields.append("name=?");     params.append(name)
    if not fields:
        return False
    fields.append("updated_at=GETDATE()")
    params.append(username)
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        f"UPDATE Admin_Accounts SET {', '.join(fields)} WHERE username=?",
        *params,
    )
    conn.commit()
    return cur.rowcount > 0
