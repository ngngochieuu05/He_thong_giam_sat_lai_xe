import flet as ft

def TrangChu():
    # 1. Các thẻ thống kê (Cards)
    def create_card(icon, title, subtitle, bg_icon_color):
            return ft.Container(
                width=220, height=100, bgcolor=ft.Colors.WHITE, border_radius=15, padding=15,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
                content=ft.Row([
                    ft.Container(
                        width=50, height=50, border_radius=25, bgcolor=bg_icon_color,
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon, color=ft.Colors.BLACK, size=24)
                    ),
                ft.Column([
                    ft.Text(title, weight=ft.FontWeight.BOLD, size=14),
                    ft.Text(subtitle, size=12, color=ft.Colors.GREY)
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)
            ])
        )

    row_cards = ft.Row([
        create_card(ft.Icons.PEOPLE, "Tổng số tài xế", "150 Nhân sự", ft.Colors.GREEN_200),
        create_card(ft.Icons.DIRECTIONS_CAR, "Phiên lái xe", "45 Đang chạy", ft.Colors.ORANGE_200),
        create_card(ft.Icons.PLAY_CIRCLE, "Đang hoạt động", "Server Online", ft.Colors.RED_200),
        create_card(ft.Icons.WARNING, "Cảnh báo", "3 Vi phạm", ft.Colors.RED_400),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # 2. Biểu đồ (Giả lập bằng Image hoặc Container màu vì Flet chart cần nhiều code config)
    # Ở đây tôi dùng BarChart của Flet để giống hình
    chart_section = ft.Container(
            expand=True, bgcolor=ft.Colors.GREY_300, border_radius=15, padding=20,
            content=ft.Column([
                ft.Text("DOANH SỐ ĐÔNG Á", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.BarChart(
                    bar_groups=[
                        ft.BarChartGroup(
                            x=0,
                            bar_rods=[
                                ft.BarChartRod(from_y=0, to_y=10, width=20, color=ft.Colors.GREEN_400, tooltip="Quý 1: 10"),
                                ft.BarChartRod(from_y=0, to_y=20, width=20, color=ft.Colors.BLUE_400, tooltip="Quý 1: 20"),
                            ],
                        ),
                        ft.BarChartGroup(
                            x=1,
                            bar_rods=[
                                ft.BarChartRod(from_y=0, to_y=40, width=20, color=ft.Colors.GREEN_400, tooltip="Quý 2: 40"),
                                ft.BarChartRod(from_y=0, to_y=50, width=20, color=ft.Colors.BLUE_400, tooltip="Quý 2: 50"),
                            ],
                        ),
                        ft.BarChartGroup(
                            x=2,
                            bar_rods=[
                                ft.BarChartRod(from_y=0, to_y=25, width=20, color=ft.Colors.GREEN_400, tooltip="Quý 3: 25"),
                                ft.BarChartRod(from_y=0, to_y=30, width=20, color=ft.Colors.BLUE_400, tooltip="Quý 3: 30"),
                            ],
                        ),
                        ft.BarChartGroup(
                            x=3,
                            bar_rods=[
                                ft.BarChartRod(from_y=0, to_y=50, width=20, color=ft.Colors.GREEN_400, tooltip="Quý 4: 50"),
                                ft.BarChartRod(from_y=0, to_y=60, width=20, color=ft.Colors.BLUE_400, tooltip="Quý 4: 60"),
                            ],
                        ),
                    ],
                    border=ft.border.all(1, ft.Colors.GREY_500),
                    left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("Doanh số")),
                    bottom_axis=ft.ChartAxis(labels=[
                        ft.ChartAxisLabel(value=0, label=ft.Text("Quý 1")),
                        ft.ChartAxisLabel(value=1, label=ft.Text("Quý 2")),
                        ft.ChartAxisLabel(value=2, label=ft.Text("Quý 3")),
                        ft.ChartAxisLabel(value=3, label=ft.Text("Quý 4")),
                    ]),
                    horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_400, width=1, dash_pattern=[3, 3]),
                    tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
                max_y=80, expand=True
            )
        ])
    )

    # 3. Hoạt động gần đây (Sidebar phải của dashboard)
    recent_activity = ft.Container(
        width=250, bgcolor=ft.Colors.WHITE, border_radius=15, padding=15,
        content=ft.Column([
        ft.Text("Hoạt động gần đây", weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.ListTile(leading=ft.Icon(ft.Icons.DIRECTIONS_CAR), title=ft.Text("Tài xế A bắt đầu", size=12)),
            ft.ListTile(leading=ft.Icon(ft.Icons.CHECK_CIRCLE), title=ft.Text("Tài xế B kết thúc", size=12)),
            ft.ListTile(leading=ft.Icon(ft.Icons.NOTIFICATIONS), title=ft.Text("Có 1 thông báo mới", size=12)),
        ])
    )

    # Layout chính của Trang Chủ
    return ft.Column([
        ft.Text("Bảng điều khiển", size=30, weight=ft.FontWeight.BOLD),
        ft.Container(height=20),
        row_cards,
        ft.Container(height=20),
        ft.Row([chart_section, recent_activity], expand=True, spacing=20)
    ], expand=True, scroll=ft.ScrollMode.AUTO)