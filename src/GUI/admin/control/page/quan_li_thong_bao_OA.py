import flet as ft

def QuanLiThongBao(page_title):
    # 1. Cấu hình kết nối (Zalo OA / Telegram)
    api_config_card = ft.Container(
        bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
        content=ft.Column([
            ft.Text("Cấu Hình Kênh Thông Báo", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.TextField(label="Zalo OA ID", prefix_icon=ft.Icons.CHAT),
            ft.TextField(label="Zalo Secret Key", password=True, can_reveal_password=True, prefix_icon=ft.Icons.KEY),
            ft.TextField(label="Telegram Bot Token", password=True, can_reveal_password=True, prefix_icon=ft.Icons.TELEGRAM),
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton("Kiểm tra kết nối", icon=ft.Icons.WIFI_TETHERING, color=ft.Colors.BLUE),
                ft.ElevatedButton("Lưu", icon=ft.Icons.SAVE, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ], alignment=ft.MainAxisAlignment.END)
        ])
    )

    # 2. Lịch sử gửi thông báo
    log_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Thời gian")),
            ft.DataColumn(ft.Text("Người nhận")),
            ft.DataColumn(ft.Text("Kênh")),
            ft.DataColumn(ft.Text("Nội dung")),
            ft.DataColumn(ft.Text("Trạng thái")),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("25/01 10:30")),
                ft.DataCell(ft.Text("Nguyễn Văn A")),
                ft.DataCell(ft.Icon(ft.Icons.TELEGRAM, color=ft.Colors.BLUE)),
                ft.DataCell(ft.Text("Cảnh báo: Ngủ gật (Mức 3)")),
                ft.DataCell(ft.Text("Thành công", color="green")),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("25/01 09:15")),
                ft.DataCell(ft.Text("Trần Thị B")),
                ft.DataCell(ft.Image(src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Icon_of_Zalo.svg/1200px-Icon_of_Zalo.svg.png", width=20, height=20)),
                ft.DataCell(ft.Text("Nhắc nhở: Phiên lái > 4h")),
                ft.DataCell(ft.Text("Thất bại", color="red")),
            ]),
        ],
        border=ft.border.all(1, ft.Colors.GREY_200),
        heading_row_color=ft.Colors.GREY_100,
    )

    log_card = ft.Container(
        bgcolor=ft.Colors.WHITE, border_radius=15, padding=20, expand=True,
        content=ft.Column([
            ft.Row([
                ft.Text("Lịch Sử Gửi Tin", size=18, weight=ft.FontWeight.BOLD),
                ft.OutlinedButton("Xóa Log", icon=ft.Icons.DELETE_SWEEP, style=ft.ButtonStyle(color=ft.Colors.RED))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Container(content=log_table, padding=0, expand=True) # Scrollable if needed
        ])
    )

    return ft.Column([
        ft.Text("Quản Lý Thông Báo & Dữ Liệu", size=24, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.Container(content=api_config_card, width=400),
            ft.Container(content=log_card, expand=True)
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
    ], expand=True)