import flet as ft
from datetime import date as date_cls, datetime, timedelta
from ..ui_styles import BORDER, DANGER, PRIMARY, SECONDARY, TEXT_PRIMARY, TEXT_SECONDARY, WARNING, glass_card, section_title

# Đường dẫn thư mục chứa icons
ICONS_DIR = r"src\GUI\Icons\Admin Dashboard"


def _normalize_session_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date_cls):
        return value
    if isinstance(value, str) and value:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value[:19], fmt).date()
            except Exception:
                continue
    return None

def load_dashboard_data():
    """Load số liệu từ SQL Server; fallback về 0 nếu DB offline."""
    total_drivers = 0
    total_sessions = 0
    total_alerts = 0
    logs = []
    daily_sessions = {}  # date_str -> count (7 ngày gần nhất)

    try:
        from src.DAL.tai_xe_dal import lay_tat_ca_tai_xe, lay_tat_ca_phien_lai
        total_drivers = len(lay_tat_ca_tai_xe())
        sessions = lay_tat_ca_phien_lai()
        total_sessions = len(sessions)
        total_alerts = sum(int(s.so_vi_pham or 0) for s in sessions)

        # Tạo log gần nhất từ 5 phiên lái đầu tiên
        for s in sessions[:5]:
            session_day = _normalize_session_date(getattr(s, "session_date", None))
            date_str = session_day.strftime("%d/%m/%Y") if session_day else str(getattr(s, "session_date", ""))
            logs.append({"user": s.username, "time": date_str})

        # Tính số phiên lái theo ngày cho biểu đồ (7 ngày gần nhất)
        today = datetime.today().date()
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            daily_sessions[d.strftime("%d/%m")] = 0
        for s in sessions:
            d = _normalize_session_date(getattr(s, "session_date", None))
            if d is None:
                continue
            key = d.strftime("%d/%m")
            if key in daily_sessions:
                daily_sessions[key] += 1

    except Exception as ex:
        print(f"[WARN] load_dashboard_data DB error: {ex}")

    return total_drivers, total_sessions, total_alerts, logs, daily_sessions

def TrangChu():
    """Trang chủ cho Admin."""
    total_drivers, total_sessions, total_alerts, recent_logs, daily_sessions = load_dashboard_data()

    def create_card(icon_path, title, subtitle, fallback_icon=ft.Icons.INFO, accent=PRIMARY):
        return glass_card(
            expand=True,
            height=108,
            padding=14,
            content=ft.Row([
                ft.Container(
                    width=56,
                    height=56,
                    border_radius=16,
                    bgcolor=ft.Colors.with_opacity(0.16, accent),
                    alignment=ft.alignment.center,
                    content=ft.Image(
                        src=icon_path,
                        width=34,
                        height=34,
                        fit=ft.ImageFit.CONTAIN,
                        error_content=ft.Icon(fallback_icon, size=28, color=accent),
                    ),
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(title, weight=ft.FontWeight.BOLD, size=13, no_wrap=False, color=TEXT_PRIMARY),
                    ft.Text(subtitle, size=11, color=TEXT_SECONDARY),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2, expand=True)
            ])
        )

    card_drivers = create_card(fr"{ICONS_DIR}\driver (1).png", "Tổng số tài xế", f"{total_drivers} Nhân sự", ft.Icons.PEOPLE, PRIMARY)
    card_sessions = create_card(fr"{ICONS_DIR}\sport-car.png", "Phiên lái xe", f"{total_sessions} Phiên", ft.Icons.DIRECTIONS_CAR, SECONDARY)
    card_active = create_card(fr"{ICONS_DIR}\play-button (3).png", "Đang hoạt động", "Hệ thống Online", ft.Icons.PLAY_CIRCLE, WARNING)

    top_cards_row = ft.Row([card_drivers, card_sessions, card_active], spacing=12, expand=True)

    card_alerts = glass_card(
        width=280,
        height=108,
        padding=14,
        content=ft.Row([
            ft.Container(
                width=56,
                height=56,
                border_radius=16,
                bgcolor=ft.Colors.with_opacity(0.16, DANGER),
                alignment=ft.alignment.center,
                content=ft.Image(
                    src=fr"{ICONS_DIR}\warning (1).png",
                    width=34,
                    height=34,
                    fit=ft.ImageFit.CONTAIN,
                    error_content=ft.Icon(ft.Icons.WARNING, size=28, color=DANGER),
                ),
            ),
            ft.Container(width=10),
            ft.Column([
                ft.Text("Cảnh báo", weight=ft.FontWeight.BOLD, size=13, color=TEXT_PRIMARY),
                ft.Text(f"{total_alerts} Vi phạm", size=11, color=TEXT_SECONDARY),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=2, expand=True)
        ])
    )

    # --- Biểu đồ ---
    day_labels = list(daily_sessions.keys())
    day_counts = list(daily_sessions.values())
    max_val = max(day_counts) if any(day_counts) else 10

    chart_section = glass_card(
        expand=True,
        padding=20,
        content=ft.Column([
            section_title("Phiên lái 7 ngày gần nhất", ft.Icons.BAR_CHART_ROUNDED, SECONDARY),
            ft.BarChart(
                bar_groups=[
                    ft.BarChartGroup(x=i, bar_rods=[
                        ft.BarChartRod(
                            from_y=0, to_y=float(day_counts[i]), width=24,
                            color=PRIMARY,
                            tooltip=f"{day_labels[i]}: {day_counts[i]} phiên"
                        )
                    ]) for i in range(len(day_labels))
                ],
                border=ft.border.all(0, ft.Colors.TRANSPARENT),
                left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("Phiên", color=TEXT_SECONDARY, size=12)),
                bottom_axis=ft.ChartAxis(labels=[
                    ft.ChartAxisLabel(value=i, label=ft.Text(day_labels[i], size=10, color=TEXT_SECONDARY))
                    for i in range(len(day_labels))
                ]),
                horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.with_opacity(0.16, ft.Colors.WHITE), width=1, dash_pattern=[3, 3]),
                tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
                max_y=max(max_val + 2, 10), expand=True,
            )
        ])
    )

    # --- Hoạt động gần đây ---
    log_controls = []
    for log in recent_logs:
        log_controls.append(
            glass_card(
                padding=12,
                bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
                border_color=ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
                content=ft.Row([
                    ft.Container(
                        width=38,
                        height=38,
                        border_radius=12,
                        bgcolor=ft.Colors.with_opacity(0.16, PRIMARY),
                        alignment=ft.alignment.center,
                        content=ft.Image(
                            src=fr"{ICONS_DIR}\sport-car.png",
                            width=20,
                            height=20,
                            fit=ft.ImageFit.CONTAIN,
                            error_content=ft.Icon(ft.Icons.DIRECTIONS_CAR, color=PRIMARY, size=20),
                        ),
                    ),
                    ft.Column([
                        ft.Text(f"Tài xế {log['user']}", size=13, weight="bold", color=TEXT_PRIMARY),
                        ft.Text(f"{log['time']}", size=10, color=TEXT_SECONDARY),
                    ], spacing=3, expand=True),
                ], spacing=12)
            )
        )
    if not log_controls:
        log_controls.append(ft.Text("Chưa có hoạt động nào.", size=12, color=TEXT_SECONDARY))

    recent_activity = glass_card(
        width=280,
        padding=15,
        content=ft.Column([
            section_title("Hoạt động gần đây", ft.Icons.ACCESS_TIME_FILLED, PRIMARY),
            ft.Divider(color=BORDER),
            *log_controls
        ])
    )

    right_col = ft.Column([
        card_alerts,
        ft.Container(height=15),
        recent_activity
    ], width=250)

    return ft.Column([
        ft.Text("Bảng điều khiển", size=30, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Text("Theo dõi tài xế, phiên lái và cảnh báo theo cùng ngôn ngữ giao diện với user.", size=13, color=TEXT_SECONDARY),
        ft.Container(height=20),
        ft.Row([
            ft.Column([
                top_cards_row,
                ft.Container(height=20),
                chart_section
            ], expand=True),
            ft.Container(width=20),
            right_col
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
    ], expand=True, scroll=ft.ScrollMode.AUTO)