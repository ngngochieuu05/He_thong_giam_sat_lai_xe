import flet as ft
from datetime import datetime, timedelta
from ..ui_styles import (
    BORDER,
    PRIMARY,
    SECONDARY,
    SURFACE,
    SURFACE_STRONG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    elevated_button,
    glass_card,
    input_style,
    section_title,
)

def _load_thong_ke():
    """Load thống kê từ DB, trả về (total_sessions, total_alerts, sessions_by_weekday[7])."""
    total_sessions = 0
    total_alerts = 0
    weekday_counts = [0] * 7  # T2=0..CN=6

    try:
        from src.DAL.tai_xe_dal import lay_tat_ca_phien_lai
        rows = lay_tat_ca_phien_lai()
        total_sessions = len(rows)
        for s in rows:
            total_alerts += int(s.so_vi_pham or 0)
            date_val = s.session_date
            try:
                if hasattr(date_val, 'weekday'):
                    wd = date_val.weekday()  # 0=Mon .. 6=Sun
                elif isinstance(date_val, str) and date_val:
                    wd = datetime.strptime(date_val[:10], "%Y-%m-%d").weekday()
                else:
                    continue
                weekday_counts[wd] += 1
            except Exception:
                pass
    except Exception as ex:
        print(f"[WARN] thong_ke load error: {ex}")

    return total_sessions, total_alerts, weekday_counts


def ThongKePage():
    total_sessions, total_alerts, weekday_counts = _load_thong_ke()
    safe_sessions = max(total_sessions - total_alerts, 0)
    day_names = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    max_wd = max(weekday_counts) if any(weekday_counts) else 10
    field_style = input_style()
    dropdown_style = {
        key: value
        for key, value in field_style.items()
        if key not in {"cursor_color", "hint_style"}
    }

    filter_section = glass_card(
        ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CALENDAR_MONTH, color=SECONDARY, size=22),
                        ft.Text("Thống kê từ:", size=15, color=TEXT_SECONDARY, weight=ft.FontWeight.W_600),
                    ],
                    spacing=10,
                ),
                ft.Dropdown(
                    width=180,
                    options=[ft.dropdown.Option("7 ngày qua"), ft.dropdown.Option("Tháng này"), ft.dropdown.Option("Năm nay")],
                    value="7 ngày qua",
                    **dropdown_style,
                ),
                elevated_button("Xuất Báo Cáo", icon=ft.Icons.DOWNLOAD, kind="primary"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=16,
    )

    # 2. Biểu đồ tròn: Tỷ lệ phiên an toàn / vi phạm
    pie_sections = []
    if total_sessions > 0:
        pie_sections = [
            ft.PieChartSection(
                max(safe_sessions, 0.01),
                title=f"An toàn\n{safe_sessions}",
                color=ft.Colors.GREEN_400, radius=60
            ),
            ft.PieChartSection(
                max(total_alerts, 0.01),
                title=f"Vi phạm\n{total_alerts}",
                color=ft.Colors.RED_400, radius=60
            ),
        ]
    else:
        pie_sections = [ft.PieChartSection(1, title="Chưa có dữ liệu", color=ft.Colors.GREY_300, radius=60)]

    pie_chart = ft.PieChart(
        sections=pie_sections,
        sections_space=2,
        center_space_radius=40,
        expand=True
    )
    card_pie = glass_card(
        ft.Column([
            section_title("Tỷ lệ vi phạm / an toàn", ft.Icons.PIE_CHART, PRIMARY),
            ft.Text(f"Tổng phiên lái: {total_sessions}  |  Vi phạm: {total_alerts}", size=13, color=TEXT_SECONDARY),
            ft.Container(content=pie_chart, height=220),
            ft.Row([
                ft.Row([ft.Container(width=12, height=12, bgcolor=ft.Colors.GREEN_400, border_radius=3), ft.Text("An toàn", color=TEXT_SECONDARY)]),
                ft.Row([ft.Container(width=12, height=12, bgcolor=ft.Colors.RED_400, border_radius=3), ft.Text("Vi phạm", color=TEXT_SECONDARY)]),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ]),
        expand=True,
        bgcolor=SURFACE_STRONG,
    )

    # 3. Biểu đồ cột: Số phiên lái theo ngày trong tuần
    bar_chart = ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(x=i, bar_rods=[
                ft.BarChartRod(
                    from_y=0, to_y=float(weekday_counts[i]), width=24,
                    color=ft.Colors.RED_400 if weekday_counts[i] == max(weekday_counts) else ft.Colors.AMBER,
                    tooltip=f"{day_names[i]}: {weekday_counts[i]} phiên",
                    border_radius=5
                )
            ]) for i in range(7)
        ],
        border=ft.border.all(1, BORDER),
        left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("Phiên", color=TEXT_SECONDARY), title_size=36),
        bottom_axis=ft.ChartAxis(
            labels=[ft.ChartAxisLabel(value=i, label=ft.Text(day_names[i], color=TEXT_SECONDARY)) for i in range(7)],
        ),
        horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.with_opacity(0.16, ft.Colors.WHITE), width=1, dash_pattern=[3, 3]),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
        max_y=max(max_wd + 2, 10),
        expand=True
    )

    card_bar = glass_card(
        ft.Column([
            section_title("Phiên lái theo ngày trong tuần", ft.Icons.INSERT_CHART_OUTLINED, SECONDARY),
            ft.Container(content=bar_chart, height=220)
        ]),
        expand=True,
        bgcolor=SURFACE_STRONG,
    )

    return ft.Column([
        ft.Column([
            ft.Text("Báo Cáo & Thống Kê", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Nền đã chuyển sang glass card để đồng bộ với dashboard và không còn các mảng trắng đặc.", size=13, color=TEXT_SECONDARY),
        ], spacing=4),
        filter_section,
        ft.Container(height=10),
        ft.Row([card_pie, card_bar], expand=True, spacing=20)
    ], expand=True, scroll=ft.ScrollMode.AUTO)