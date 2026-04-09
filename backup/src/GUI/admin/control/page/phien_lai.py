import flet as ft

def PhienLaiPage():
    return ft.Container(
            alignment=ft.alignment.center,
            expand=True,
            content=ft.Column([
                ft.Text("Quản Lý Phiên Lái", size=30, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                ft.Text("Giao diện đang được phát triển...", size=16, color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
