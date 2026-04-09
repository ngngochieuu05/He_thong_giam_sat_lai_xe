# DAL – Data Access Layer
# Kết nối & thao tác với SQL Server He_Thong_Giam_Sat_Lai_Xe_LGBT
# Server: LAPTOP-GNCAN9C4\SQLEXPRESS  |  DB: He_Thong_Giam_Sat_Lai_Xe_LGBT
from .db_connection  import get_connection, close_connection, test_connection
from .admin_dal      import (dang_nhap_admin, lay_admin_theo_username,
                              lay_tat_ca_admin, them_admin, cap_nhat_admin)
from .accounts_sync  import (get_all_admin_accounts_from_db,
                              get_all_driver_accounts_from_db,
                              get_driver_account_from_db,
                              generate_next_driver_id,
                              build_accounts_payload,
                              export_accounts_to_json)
from .tai_xe_dal     import (lay_tai_xe_theo_username, lay_tat_ca_tai_xe,
                              them_tai_xe, cap_nhat_tai_xe, xoa_tai_xe,
                              xoa_tai_xe_theo_rang_buoc,
                              lay_face_data, cap_nhat_face_data,
                              dang_nhap_tai_xe, ghi_lich_su_dang_nhap,
                              them_phien_lai, lay_tat_ca_phien_lai,
                              lay_lich_su_tai_xe, ghi_canh_bao,
                              lay_dashboard_tai_xe, lien_ket_telegram)
from .thong_bao_dal  import (luu_thong_bao_log, lay_thong_bao_logs,
                              xoa_thong_bao_logs, them_telegram_token,
                              kiem_tra_token, danh_dau_da_dung_token)
from .cau_hinh_dal   import (lay_gia_tri, lay_tat_ca_cau_hinh,
                              dat_gia_tri, cap_nhat_nhieu)
