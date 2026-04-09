from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .db_connection import get_connection


_ROOT = Path(__file__).resolve().parents[2]
ACCOUNTS_JSON_PATH = _ROOT / "src" / "GUI" / "data" / "accounts.json"


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {
        column[0]: value
        for column, value in zip(row.cursor_description, tuple(row))
    }


def _decorate_driver_record(record: dict[str, Any]) -> dict[str, Any]:
    plan = record.get("goi_dich_vu") or "Free"
    record["plan"] = plan
    telegram_chat_id = record.get("telegram_chat_id")
    telegram_username = record.get("telegram_username")
    if telegram_chat_id or telegram_username:
        record["telegram_data"] = {
            "chat_id": telegram_chat_id,
            "telegram_username": telegram_username,
        }
    return record


def get_all_admin_accounts_from_db(include_inactive: bool = False) -> list[dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT username, password, name, role, is_active
        FROM Admin_Accounts
    """
    if not include_inactive:
        query += " WHERE is_active=1"
    query += " ORDER BY username"
    cur.execute(query)
    return [_decorate_driver_record(_row_to_dict(row)) for row in cur.fetchall()]


def get_all_driver_accounts_from_db(include_inactive: bool = False) -> list[dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    query = """
         SELECT tx.tai_xe_id, tx.driver_id, tx.username, tx.name, tx.password, tx.phone,
             tx.created_at,
               tx.face_data, tx.avatar, tx.goi_dich_vu, tx.is_active,
               COALESCE(tlk.chat_id, tx.telegram_chat_id) AS telegram_chat_id, tlk.telegram_username
        FROM Tai_Xe tx
        LEFT JOIN Telegram_Lien_Ket tlk
            ON tlk.tai_xe_id = tx.tai_xe_id AND tlk.is_active = 1
    """
    if not include_inactive:
        query += " WHERE tx.is_active=1"
    query += " ORDER BY tx.tai_xe_id"
    cur.execute(query)
    return [_row_to_dict(row) for row in cur.fetchall()]


def get_driver_account_from_db(username: str) -> dict[str, Any] | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
         SELECT tx.tai_xe_id, tx.driver_id, tx.username, tx.name, tx.password, tx.phone,
             tx.created_at,
               tx.face_data, tx.avatar, tx.goi_dich_vu, tx.is_active,
               COALESCE(tlk.chat_id, tx.telegram_chat_id) AS telegram_chat_id, tlk.telegram_username
        FROM Tai_Xe tx
        LEFT JOIN Telegram_Lien_Ket tlk
            ON tlk.tai_xe_id = tx.tai_xe_id AND tlk.is_active = 1
        WHERE tx.username=? AND tx.is_active=1
        """,
        username,
    )
    row = cur.fetchone()
    return _decorate_driver_record(_row_to_dict(row)) if row else None


def generate_next_driver_id() -> str:
    drivers = get_all_driver_accounts_from_db(include_inactive=True)
    max_number = 0
    for driver in drivers:
        driver_id = str(driver.get("driver_id") or "")
        if driver_id.startswith("TX"):
            try:
                max_number = max(max_number, int(driver_id[2:]))
            except ValueError:
                continue
    return f"TX{max_number + 1:03d}"


def _normalize_admin_account(row: dict[str, Any]) -> dict[str, Any]:
    account = {
        "is_active": row.get("is_active", 1),
        "username": row.get("username", ""),
        "password": row.get("password", ""),
        "name": row.get("name") or row.get("username", ""),
        "role": row.get("role") or "Admin",
    }
    return account


def _normalize_driver_account(row: dict[str, Any]) -> dict[str, Any]:
    account = {
        "is_active": row.get("is_active", 1),
        "driver_id": row.get("driver_id") or "",
        "username": row.get("username", ""),
        "name": row.get("name") or row.get("username", ""),
        "password": row.get("password", ""),
        "goi_dich_vu": row.get("goi_dich_vu") or "Free",
        "plan": row.get("plan") or row.get("goi_dich_vu") or "Free",
    }

    optional_fields = [
        "phone",
        "face_data",
        "avatar",
        "telegram_chat_id",
        "telegram_username",
    ]
    for field in optional_fields:
        value = row.get(field)
        if value not in (None, ""):
            account[field] = value

    if account.get("telegram_chat_id") or account.get("telegram_username"):
        account["telegram_data"] = {
            "chat_id": account.get("telegram_chat_id"),
            "telegram_username": account.get("telegram_username"),
        }

    if row.get("telegram_data"):
        account["telegram_data"] = row["telegram_data"]

    return account


def build_accounts_payload() -> dict[str, list[dict[str, Any]]]:
    admins = [_normalize_admin_account(row) for row in get_all_admin_accounts_from_db()]
    drivers = [_normalize_driver_account(row) for row in get_all_driver_accounts_from_db()]
    return {
        "admin_accounts": admins,
        "user_accounts": drivers,
    }


def export_accounts_to_json(path: str | Path | None = None) -> dict[str, list[dict[str, Any]]]:
    payload = build_accounts_payload()
    output_path = Path(path) if path else ACCOUNTS_JSON_PATH
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
