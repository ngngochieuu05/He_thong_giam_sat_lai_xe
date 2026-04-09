import flet as ft
import os
from ..ui_styles import BORDER, PRIMARY, SECONDARY, SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, glass_card, section_title

ICONS_DIR = r"src\GUI\Icons\Driving"

def _load_sessions():
    sessions = []
    try:
        from src.DAL.tai_xe_dal import lay_tat_ca_phien_lai
        rows = lay_tat_ca_phien_lai()
        for idx, s in enumerate(rows):
            dur = int(s.duration_minutes or 0)
            h, m = divmod(dur, 60)
            date_val = s.session_date
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime("%d/%m/%Y")
            else:
                date_str = str(date_val)[:10] if date_val else ""
            sessions.append({
                "session_id":   f"#S{s.phien_lai_id}",
                "username":     s.username,
                "name":         s.name or s.username,
                "phone":        getattr(s, 'phone', '') or "",
                "date":         date_str,
                "duration_min": dur,
                "duration_str": f"{h}h{m:02d}p" if h > 0 else f"{m}p",
                "alerts":       int(s.so_vi_pham or 0),
                "score":        int(s.diem_an_toan or 100),
                "plate":        "",
                "status":       "Kết thúc",
            })
    except Exception as ex:
        print(f"[WARN] load_sessions DB error: {ex}")
    return sessions


# ── Màu chung cho filter bar ──────────────────────────────────────────────────
_WH     = ft.Colors.WHITE
_WH60   = ft.Colors.WHITE60
_WH30   = ft.Colors.with_opacity(0.15, ft.Colors.WHITE)
_BORDER = ft.Colors.WHITE54

_FIELD_STYLE = dict(
    border_radius=8,
    bgcolor=_WH30,
    color=_WH,
    hint_style=ft.TextStyle(color=_WH60),
    border_color=_BORDER,
    focused_border_color=_WH,
    cursor_color=_WH,
    text_style=ft.TextStyle(color=_WH),
)


class PhienLaiPage(ft.Column):
    """Trang Phiên Lái – hỗ trợ lọc theo trạng thái và ngày."""

    def __init__(self):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self._all_sessions = _load_sessions()

        # ── Stat cards ────────────────────────────────────────────────────────
        total_min  = sum(s["duration_min"] for s in self._all_sessions)
        tot_h, tot_m = divmod(total_min, 60)
        self._stat_row = ft.Row([
            self._stat_card(
                fr"{ICONS_DIR}\sport-car.png",
                "Tổng số phiên lái", f"{len(self._all_sessions)} Phiên",
                ft.Icons.DIRECTIONS_CAR
            ),
            self._stat_card(
                fr"{ICONS_DIR}\chronometer.png",
                "Tổng thời gian", f"{tot_h}h{tot_m:02d}p",
                ft.Icons.TIMER
            ),
        ], spacing=15)

        # ── Filter controls ───────────────────────────────────────────────────
        self._dd_status = ft.Dropdown(
            width=180, border_radius=8,
            bgcolor=SURFACE, color=TEXT_PRIMARY,
            border_color=BORDER, focused_border_color=PRIMARY,
            options=[
                ft.dropdown.Option("Tất cả trạng thái"),
                ft.dropdown.Option("Đang lái xe"),
                ft.dropdown.Option("Chờ khách"),
                ft.dropdown.Option("Kết thúc"),
            ],
            value="Tất cả trạng thái",
        )
        self._tf_from = ft.TextField(
            hint_text="Từ ngày (dd/mm/yyyy)",
            width=160,
            border_radius=14,
            bgcolor=SURFACE,
            color=TEXT_PRIMARY,
            hint_style=ft.TextStyle(color=TEXT_SECONDARY),
            border_color=BORDER,
            focused_border_color=PRIMARY,
            cursor_color=TEXT_PRIMARY,
            text_style=ft.TextStyle(color=TEXT_PRIMARY),
        )
        self._tf_to = ft.TextField(
            hint_text="Đến ngày (dd/mm/yyyy)",
            width=160,
            border_radius=14,
            bgcolor=SURFACE,
            color=TEXT_PRIMARY,
            hint_style=ft.TextStyle(color=TEXT_SECONDARY),
            border_color=BORDER,
            focused_border_color=PRIMARY,
            cursor_color=TEXT_PRIMARY,
            text_style=ft.TextStyle(color=TEXT_PRIMARY),
        )

        self._filter_btn = ft.Container(
            content=ft.Icon(ft.Icons.SEARCH, color=_WH, size=22),
            bgcolor=ft.Colors.BLUE_700, border_radius=8, padding=10,
            ink=True, tooltip="Lọc", on_click=self._apply_filter
        )
        self._reset_btn = ft.Container(
            content=ft.Icon(ft.Icons.REFRESH, color=_WH, size=20),
            bgcolor=ft.Colors.with_opacity(0.25, _WH), border_radius=8, padding=10,
            ink=True, tooltip="Xóa bộ lọc", on_click=self._reset_filter
        )

        filter_bar = ft.Row([
            self._dd_status,
            ft.Container(width=10),
            self._tf_from,
            ft.Container(width=6),
            ft.Text("→", size=14, color=_WH),
            ft.Container(width=6),
            self._tf_to,
            ft.Container(width=10),
            self._filter_btn,
            ft.Container(width=6),
            self._reset_btn,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # ── Bảng ─────────────────────────────────────────────────────────────
        self._table_headers = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border_radius=ft.border_radius.only(top_left=18, top_right=18),
            content=ft.Row([
                ft.Text("Mã phiên", weight="bold", size=13, expand=2, color=TEXT_PRIMARY),
                ft.Text("Tài xế", weight="bold", size=13, expand=3, color=TEXT_PRIMARY),
                ft.Text("Xe", weight="bold", size=13, expand=2, color=TEXT_PRIMARY),
                ft.Text("Thời gian lái", weight="bold", size=13, expand=2, color=TEXT_PRIMARY),
                ft.Text("Trạng thái", weight="bold", size=13, expand=2, color=TEXT_PRIMARY),
            ])
        )
        self._data_rows = ft.ListView(expand=True, spacing=0)
        self._table = glass_card(
            expand=True,
            radius=18,
            padding=0,
            content=ft.Column([self._table_headers, self._data_rows], spacing=0)
        )

        # ── Lắp vào Column ────────────────────────────────────────────────────
        self.controls = [
            section_title("Quản lý phiên lái", ft.Icons.TIME_TO_LEAVE_ROUNDED, SECONDARY),
            ft.Text("Theo dõi phiên lái bằng giao diện kính tối đồng bộ với phần user.", size=13, color=TEXT_SECONDARY),
            ft.Container(height=10),
            self._stat_row,
            ft.Container(height=15),
            filter_bar,
            ft.Container(height=10),
            self._table,
        ]

        self._render_rows(self._all_sessions)

    # ─────────────────────────────────────────────────────────────────────────
    # UI helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _stat_card(self, icon_path, title, subtitle, fallback):
        return glass_card(
            expand=True,
            height=92,
            padding=15,
            radius=18,
            content=ft.Row([
                ft.Container(
                    width=56,
                    height=56,
                    border_radius=16,
                    bgcolor=ft.Colors.with_opacity(0.16, SECONDARY),
                    alignment=ft.alignment.center,
                    content=ft.Image(src=icon_path, width=34, height=34, fit=ft.ImageFit.CONTAIN,
                         error_content=ft.Icon(fallback, size=28, color=SECONDARY)),
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(title, weight=ft.FontWeight.BOLD, size=14, color=TEXT_PRIMARY),
                    ft.Text(subtitle, size=12, color=TEXT_SECONDARY),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2, expand=True)
            ])
        )

    @staticmethod
    def _status_badge(status):
        color_map = {
            "Đang lái xe": ("#E8F5E9", "#2E7D32"),
            "Chờ khách"  : ("#FFF3E0", "#E65100"),
            "Kết thúc"   : ("#FCE4EC", "#C62828"),
        }
        bg, fg = color_map.get(status, ("#F5F5F5", "#616161"))
        return ft.Container(
            content=ft.Text(status, size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
            bgcolor=ft.Colors.with_opacity(0.22, PRIMARY if status == "Đang lái xe" else SECONDARY if status == "Chờ khách" else ft.Colors.WHITE),
            border_radius=20,
            border=ft.border.all(1, ft.Colors.with_opacity(0.16, ft.Colors.WHITE)),
            padding=ft.padding.symmetric(horizontal=12, vertical=6)
        )

    def _render_rows(self, sessions):
        self._data_rows.controls.clear()
        for s in sessions:
            driver_txt = s["name"] or s["username"]
            if s["phone"]:
                driver_txt += f"\n{s['phone']}"
            plate = s["plate"] or "—"

            self._data_rows.controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20, vertical=14),
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                    border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))),
                    content=ft.Row([
                        ft.Text(s["session_id"], expand=2, size=13, weight="bold",
                                color=TEXT_PRIMARY),
                        ft.Text(driver_txt, expand=3, size=13, color=TEXT_PRIMARY),
                        ft.Row([
                            ft.Image(src=fr"{ICONS_DIR}\car.png", width=24, height=24,
                                     fit=ft.ImageFit.CONTAIN,
                                     error_content=ft.Icon(ft.Icons.DIRECTIONS_CAR,
                                                           size=18, color=SECONDARY)),
                            ft.Container(width=4),
                            ft.Text(plate, size=13, color=TEXT_SECONDARY),
                        ], expand=2),
                        ft.Text(s["duration_str"], expand=2, size=13, color=TEXT_SECONDARY),
                        ft.Container(expand=2, content=self._status_badge(s["status"])),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                )
            )

        if not self._data_rows.controls:
            self._data_rows.controls.append(
                ft.Container(
                    padding=30, alignment=ft.alignment.center,
                    content=ft.Text("Không tìm thấy phiên lái nào.", size=14,
                                    color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER)
                )
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Filter logic
    # ─────────────────────────────────────────────────────────────────────────
    def _apply_filter(self, e):
        status_filter = self._dd_status.value or "Tất cả trạng thái"
        date_from     = (self._tf_from.value or "").strip()
        date_to       = (self._tf_to.value   or "").strip()

        filtered = self._all_sessions[:]

        # Lọc trạng thái
        if status_filter != "Tất cả trạng thái":
            filtered = [s for s in filtered if s["status"] == status_filter]

        # Lọc ngày (so sánh chuỗi dd/mm/yyyy)
        def parse_date(d):
            try:
                from datetime import datetime
                return datetime.strptime(d, "%d/%m/%Y")
            except: return None

        if date_from:
            dt_from = parse_date(date_from)
            if dt_from:
                filtered = [s for s in filtered if parse_date(s["date"]) and parse_date(s["date"]) >= dt_from]

        if date_to:
            dt_to = parse_date(date_to)
            if dt_to:
                filtered = [s for s in filtered if parse_date(s["date"]) and parse_date(s["date"]) <= dt_to]

        self._render_rows(filtered)
        try:
            self._data_rows.update()
        except: pass

    def _reset_filter(self, e):
        self._dd_status.value    = "Tất cả trạng thái"
        self._tf_from.value      = ""
        self._tf_to.value        = ""
        self._render_rows(self._all_sessions)
        try:
            self._dd_status.update()
            self._tf_from.update()
            self._tf_to.update()
            self._data_rows.update()
        except: pass
