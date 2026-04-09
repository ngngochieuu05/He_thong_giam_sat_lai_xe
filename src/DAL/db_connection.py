"""
db_connection.py
Kết nối tới SQL Server He_Thong_Giam_Sat_Lai_Xe_LGBT
Server  : LAPTOP-GNCAN9C4\\SQLEXPRESS
Auth    : Windows Authentication (Trusted_Connection)
"""
import threading
import pyodbc

# ──────────────────────────────────────────────
# Cấu hình kết nối
# ──────────────────────────────────────────────
_DB_SERVER = r"LAPTOP-GNCAN9C4\SQLEXPRESS"
_DB_NAME   = "He_Thong_Giam_Sat_Lai_Xe_LGBT"
_DB_DRIVER = "ODBC Driver 18 for SQL Server"

_CONN_STRING = (
    f"DRIVER={{{_DB_DRIVER}}};"
    f"SERVER={_DB_SERVER};"
    f"DATABASE={_DB_NAME};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
    "Encrypt=yes;"
)

_local = threading.local()


def get_connection() -> pyodbc.Connection:
    """
    Trả về kết nối theo thread-local.
    Tự động tái kết nối nếu bị mất.
    """
    conn: pyodbc.Connection | None = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.cursor().execute("SELECT 1")
            return conn
        except pyodbc.Error:
            pass  # kết nối bị đóng → tạo lại bên dưới
    conn = pyodbc.connect(_CONN_STRING, autocommit=False)
    _local.conn = conn
    return conn


def close_connection() -> None:
    """Đóng kết nối của thread hiện tại (gọi khi kết thúc app)."""
    conn: pyodbc.Connection | None = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except pyodbc.Error:
            pass
        _local.conn = None


def test_connection() -> bool:
    """
    Kiểm tra kết nối.  
    Trả về True nếu thành công, False nếu lỗi.
    """
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT DB_NAME() AS db, @@SERVERNAME AS srv")
        row = cur.fetchone()
        print(f"[DB] ✅ Connected  →  Server: {row.srv}  |  DB: {row.db}")
        return True
    except pyodbc.Error as exc:
        print(f"[DB] ❌ Connection failed: {exc}")
        return False
