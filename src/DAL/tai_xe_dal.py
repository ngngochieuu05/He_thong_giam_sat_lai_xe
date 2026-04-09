"""
tai_xe_dal.py
CRUD cho bảng: Tai_Xe, Dang_Nhap_Lich_Su, Phien_Lai,
               Tong_Ket_Tai_Xe, Telegram_Lien_Ket
"""
from __future__ import annotations
from typing import Optional
import pyodbc
from .db_connection import get_connection


# ══════════════════════════════════════════════
# Tai_Xe
# ══════════════════════════════════════════════

def lay_tai_xe_theo_username(username: str) -> Optional[pyodbc.Row]:
    """Trả về row Tai_Xe (kèm telegram + thống kê), None nếu không tồn tại."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("EXEC sp_LayThongTin_TaiXe @username=?", username)
    return cur.fetchone()


def lay_tat_ca_tai_xe() -> list[pyodbc.Row]:
    """Danh sách toàn bộ tài xế (dùng trang Admin)."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("EXEC sp_LayDanhSach_TaiXe")
    return cur.fetchall()


def them_tai_xe(
    driver_id: str,
    username:  str,
    name:      str,
    password:  str,
    phone:     Optional[str] = None,
    face_data: Optional[str] = None,
    goi_dich_vu: str = "Free",
) -> int:
    """
    Thêm tài xế mới.  
    Trả về tai_xe_id vừa tạo.
    Tự động khởi tạo bản ghi Tong_Ket_Tai_Xe.
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        """
        INSERT INTO Tai_Xe (driver_id, username, name, password, phone, face_data, goi_dich_vu)
        OUTPUT INSERTED.tai_xe_id
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        driver_id, username, name, password, phone, face_data, goi_dich_vu,
    )
    tai_xe_id: int = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO Tong_Ket_Tai_Xe (tai_xe_id) VALUES (?)",
        tai_xe_id,
    )
    conn.commit()
    return tai_xe_id


def cap_nhat_tai_xe(
    username:   str,
    name:       Optional[str]  = None,
    password:   Optional[str]  = None,
    phone:      Optional[str]  = None,
    face_data:  Optional[str]  = None,
    avatar:     Optional[str]  = None,
    goi_dich_vu: Optional[str] = None,
) -> bool:
    """Cập nhật thông tin tài xế theo username."""
    fields, params = [], []
    if name        is not None: fields.append("name=?");        params.append(name)
    if password    is not None: fields.append("password=?");    params.append(password)
    if phone       is not None: fields.append("phone=?");       params.append(phone)
    if face_data   is not None: fields.append("face_data=?");   params.append(face_data)
    if avatar      is not None: fields.append("avatar=?");      params.append(avatar)
    if goi_dich_vu is not None: fields.append("goi_dich_vu=?"); params.append(goi_dich_vu)
    if not fields:
        return False

    fields.append("updated_at=GETDATE()")
    params.append(username)
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        f"UPDATE Tai_Xe SET {', '.join(fields)} WHERE username=? AND is_active=1",
        *params,
    )
    conn.commit()
    return cur.rowcount > 0


def xoa_tai_xe(driver_id: str) -> bool:
    """Vô hiệu hoá tài xế (soft delete)."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE Tai_Xe SET is_active=0, updated_at=GETDATE() WHERE driver_id=?",
        driver_id,
    )
    conn.commit()
    return cur.rowcount > 0


def xoa_tai_xe_theo_rang_buoc(driver_id: str) -> dict[str, object]:
    """
    X??a t??i x??? theo quy t???c nghi???p v???.

    - Lu??n v??? hi???u ho?? (soft delete), d?? t??i x??? ???? c?? phi??n l??i hay ch??a.
    - D??? li???u DB lu??n ???????c gi??? l???i ????? ?????ng b??? v?? th???ng k??.

    Tr??? v???:
        {
            "success": bool,
            "mode": "soft" | "not_found",
            "session_count": int,
            "driver_id": str,
            "username": str,
            "message": str,
        }
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT tai_xe_id, username FROM Tai_Xe WHERE driver_id=?",
        driver_id,
    )
    driver_row = cur.fetchone()
    if not driver_row:
        return {
            "success": False,
            "mode": "not_found",
            "session_count": 0,
            "driver_id": driver_id,
            "username": "",
            "message": "Kh??ng t??m th???y t??i x??? trong c?? s??? d??? li???u.",
        }

    tai_xe_id = int(driver_row[0])
    username = str(driver_row[1])

    cur.execute(
        "SELECT COUNT(1) FROM Phien_Lai WHERE tai_xe_id=?",
        tai_xe_id,
    )
    session_count = int((cur.fetchone() or (0,))[0])

    cur.execute(
        "UPDATE Tai_Xe SET is_active=0, updated_at=GETDATE() WHERE tai_xe_id=?",
        tai_xe_id,
    )
    conn.commit()

    return {
        "success": cur.rowcount > 0,
        "mode": "soft",
        "session_count": session_count,
        "driver_id": driver_id,
        "username": username,
        "message": "T??i x??? ???? b??? v??? hi???u ho?? tr??n h??? th???ng. D??? li???u DB ???????c gi??? l???i.",
    }


def lay_face_data(username: str) -> Optional[str]:
    """Trả về chuỗi face_data đã mã hóa của tài xế."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT face_data FROM Tai_Xe WHERE username=? AND is_active=1",
        username,
    )
    row = cur.fetchone()
    return row[0] if row else None


def cap_nhat_face_data(username: str, face_data: str) -> bool:
    """Lưu/cập nhật face_data cho tài xế."""
    return cap_nhat_tai_xe(username, face_data=face_data)


# ══════════════════════════════════════════════
# Đăng nhập
# ══════════════════════════════════════════════

def dang_nhap_tai_xe(username: str, password: str) -> bool:
    """
    Xác thực tài xế + ghi lịch sử đăng nhập.  
    Trả về True nếu thành công.
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "DECLARE @r INT; EXEC sp_DangNhap_TaiXe @username=?, @password=?, @ket_qua=@r OUTPUT; SELECT @r",
        username, password,
    )
    row = cur.fetchone()
    conn.commit()
    return bool(row and row[0] == 1)


def ghi_lich_su_dang_nhap(username: str) -> None:
    """Ghi thêm bản ghi đăng nhập cho tài xế đã được xác thực."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        """
        INSERT INTO Dang_Nhap_Lich_Su (tai_xe_id, login_date, login_time)
        SELECT tai_xe_id, CAST(GETDATE() AS DATE), CAST(GETDATE() AS TIME)
        FROM   Tai_Xe WHERE username=?
        """,
        username,
    )
    conn.commit()


# ══════════════════════════════════════════════
# Phiên lái
# ══════════════════════════════════════════════

def them_phien_lai(
    username:         str,
    session_date:     str,   # 'YYYY-MM-DD'
    duration_minutes: int,
    so_vi_pham:       int,
) -> None:
    """Thêm phiên lái và cập nhật tổng kết."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "EXEC sp_Them_PhienLai @username=?, @session_date=?, @duration_minutes=?, @so_vi_pham=?",
        username, session_date, duration_minutes, so_vi_pham,
    )
    conn.commit()


def lay_tat_ca_phien_lai() -> list[pyodbc.Row]:
    """Toàn bộ phiên lái kèm số điện thoại (dùng trang Admin)."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
            tx.username,
            tx.name,
            ISNULL(tx.phone, '') AS phone,
            pl.session_date,
            pl.duration_minutes,
            pl.so_vi_pham,
            tkt.diem_an_toan,
            pl.phien_lai_id
        FROM   Phien_Lai pl
        JOIN   Tai_Xe tx ON tx.tai_xe_id = pl.tai_xe_id
        LEFT JOIN Tong_Ket_Tai_Xe tkt ON tkt.tai_xe_id = pl.tai_xe_id
        ORDER BY pl.session_date DESC, pl.phien_lai_id DESC
    """)
    return cur.fetchall()


def lay_lich_su_tai_xe(username: str) -> tuple[list, list]:
    """
    Lịch sử đăng nhập và phiên lái của tài xế.  
    Trả về (login_rows, session_rows).
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("EXEC sp_LichSu_TaiXe @username=?", username)
    login_rows = cur.fetchall()
    cur.nextset()
    session_rows = cur.fetchall()
    return login_rows, session_rows


# ══════════════════════════════════════════════
# Tổng kết & cảnh báo
# ══════════════════════════════════════════════

def ghi_canh_bao(username: str, alert_date: Optional[str] = None) -> None:
    """Tăng bộ đếm cảnh báo ngủ gật cho tài xế."""
    conn = get_connection()
    cur  = conn.cursor()
    if alert_date:
        cur.execute(
            "EXEC sp_Ghi_CanhBao @username=?, @alert_date=?",
            username, alert_date,
        )
    else:
        cur.execute("EXEC sp_Ghi_CanhBao @username=?", username)
    conn.commit()


def lay_dashboard_tai_xe(username: str) -> tuple:
    """
    Số liệu dashboard chi tiết.  
    Trả về (tong_ket_row, today_logins, today_drive_minutes, today_alerts).
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("EXEC sp_Dashboard_TaiXe @username=?", username)
    tong_ket     = cur.fetchone()
    cur.nextset();  today_logins      = (cur.fetchone() or (0,))[0]
    cur.nextset();  today_drive_min   = (cur.fetchone() or (0,))[0]
    cur.nextset();  today_alerts      = (cur.fetchone() or (0,))[0]
    return tong_ket, today_logins, today_drive_min, today_alerts


# ══════════════════════════════════════════════
# Telegram liên kết
# ══════════════════════════════════════════════

def lien_ket_telegram(
    username:          str,
    chat_id:           str,
    telegram_username: Optional[str] = None,
) -> int:
    """
    Liên kết Telegram.
    Trả về: 1=thành công, -1=đã liên kết, 0=không tìm thấy tài xế.
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        """
        DECLARE @r INT;
        EXEC sp_LienKet_Telegram
            @username=?, @chat_id=?, @telegram_username=?, @ket_qua=@r OUTPUT;
        SELECT @r;
        """,
        username, chat_id, telegram_username,
    )
    row = cur.fetchone()
    conn.commit()
    return int(row[0]) if row else 0
