import flet as ft

def ThongKePage():
    # 1. Bộ lọc thời gian (Header)
    filter_section = ft.Container(
        padding=10, bgcolor=ft.Colors.WHITE, border_radius=10,
        content=ft.Row([
            ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.GREY),
            ft.Text("Thống kê từ:", size=16),
            ft.Dropdown(
                width=150, 
                options=[ft.dropdown.Option("7 ngày qua"), ft.dropdown.Option("Tháng này"), ft.dropdown.Option("Năm nay")],
                value="7 ngày qua"
            ),
            ft.ElevatedButton("Xuất Báo Cáo", icon=ft.Icons.DOWNLOAD, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    )

    # 2. Biểu đồ tròn: Tỷ lệ các loại vi phạm (PieChart)
    pie_chart = ft.PieChart(
        sections=[
            ft.PieChartSection(40, title="Buồn ngủ", color=ft.Colors.BLUE, radius=50),
            ft.PieChartSection(30, title="Nghe ĐT", color=ft.Colors.RED, radius=50),
            ft.PieChartSection(15, title="Không dây", color=ft.Colors.ORANGE, radius=50),
            ft.PieChartSection(15, title="Hút thuốc", color=ft.Colors.GREY, radius=50),
        ],
        sections_space=2,
        center_space_radius=40,
        expand=True
    )
    
    card_pie = ft.Container(
        expand=True, bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
        content=ft.Column([
            ft.Row([
                ft.Row([ft.Container(width=10, height=10, bgcolor=ft.Colors.BLUE), ft.Text("Buồn ngủ")]),
                ft.Row([ft.Container(width=10, height=10, bgcolor=ft.Colors.RED), ft.Text("Nghe ĐT")]),
            ], alignment=ft.MainAxisAlignment.CENTER)
        ])
    )

    # 3. Biểu đồ cột: Số giờ lái xe trung bình (BarChart)
    bar_chart = ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(x=0, bar_rods=[ft.BarChartRod(from_y=0, to_y=8, width=20, color=ft.Colors.AMBER, tooltip="T2", border_radius=5)]),
            ft.BarChartGroup(x=1, bar_rods=[ft.BarChartRod(from_y=0, to_y=10, width=20, color=ft.Colors.AMBER, tooltip="T3", border_radius=5)]),
            ft.BarChartGroup(x=2, bar_rods=[ft.BarChartRod(from_y=0, to_y=12, width=20, color=ft.Colors.RED, tooltip="T4 (Cao)", border_radius=5)]),
            ft.BarChartGroup(x=3, bar_rods=[ft.BarChartRod(from_y=0, to_y=7, width=20, color=ft.Colors.AMBER, tooltip="T5", border_radius=5)]),
            ft.BarChartGroup(x=4, bar_rods=[ft.BarChartRod(from_y=0, to_y=9, width=20, color=ft.Colors.AMBER, tooltip="T6", border_radius=5)]),
        ],
        border=ft.border.all(1, ft.Colors.GREY_300),
        left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("Giờ")),
        bottom_axis=ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(value=0, label=ft.Text("T2")),
                ft.ChartAxisLabel(value=1, label=ft.Text("T3")),
                ft.ChartAxisLabel(value=2, label=ft.Text("T4")),
                ft.ChartAxisLabel(value=3, label=ft.Text("T5")),
                ft.ChartAxisLabel(value=4, label=ft.Text("T6")),
            ],
        ),
        horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_100, width=1, dash_pattern=[3, 3]),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
        expand=True
    )

    card_bar = ft.Container(
        expand=True, bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
        content=ft.Column([
            ft.Text("Giờ Lái Xe Trung Bình", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(content=bar_chart, height=200)
        ])
    )

    return ft.Column([
        ft.Text("Báo Cáo & Thống Kê", size=24, weight=ft.FontWeight.BOLD),
        filter_section,
        ft.Container(height=10),
        ft.Row([card_pie, card_bar], expand=True, spacing=20)
    ], expand=True, scroll=ft.ScrollMode.AUTO)