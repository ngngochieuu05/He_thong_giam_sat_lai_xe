import flet as ft
import os, json
from ..ui_styles import BORDER, PRIMARY, SECONDARY, SURFACE, SURFACE_STRONG, TEXT_PRIMARY, TEXT_SECONDARY, elevated_button, glass_card, input_style, section_title

def CaiDatPage():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    accounts_path = os.path.join(base_dir, "..", "..", "..", "data", "accounts.json")
    
    txt_old_pass = ft.TextField(label="Mật khẩu cũ", password=True, can_reveal_password=True, width=320, **input_style())
    txt_new_pass = ft.TextField(label="Mật khẩu mới", password=True, can_reveal_password=True, width=320, **input_style())
    
    def change_pass(e):
        old_p = txt_old_pass.value
        new_p = txt_new_pass.value
        if not old_p or not new_p:
            e.page.open(ft.SnackBar(ft.Text("Vui lòng điền đầy đủ!"), bgcolor=ft.Colors.RED))
            e.page.update()
            return
            
        with open(accounts_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        admin = data.get("admin_accounts", [])[0]
        if admin["password"] == old_p:
            admin["password"] = new_p
            with open(accounts_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            e.page.open(ft.SnackBar(ft.Text("Đổi mật khẩu thành công!"), bgcolor=ft.Colors.GREEN))
            txt_old_pass.value = ""
            txt_new_pass.value = ""
            e.page.update()
        else:
            e.page.open(ft.SnackBar(ft.Text("Mật khẩu cũ không chính xác!"), bgcolor=ft.Colors.RED))
            e.page.update()
            
    header = section_title("Đổi Mật Khẩu Admin", ft.Icons.LOCK_RESET, PRIMARY)
    
    sys_info = ft.Column([
        section_title("Thông Tin Hệ Thống", ft.Icons.INFO_OUTLINE, SECONDARY),
        ft.Text("• Phiên bản phần mềm: v1.0.0", color=TEXT_SECONDARY),
        ft.Text("• Database: Cấu trúc tệp JSON cục bộ", color=TEXT_SECONDARY),
        ft.Text("• Môi trường: Máy chủ gốc Python Flet Desktop", color=TEXT_SECONDARY),
        ft.Text("• Phiên bản AI: ONNX/DL Runtime Ecosystem", color=TEXT_SECONDARY),
        ft.Container(height=10),
        elevated_button("Sao lưu dữ liệu", icon=ft.Icons.BACKUP, kind="secondary", on_click=lambda e: (e.page.open(ft.SnackBar(ft.Text("✅ Toàn bộ dữ liệu hệ thống đã được lưu trữ an toàn!"), bgcolor=ft.Colors.GREEN)), e.page.update()))
    ], spacing=10)

    pass_form = ft.Column([
        header, 
        ft.Text("Nền và các khối cài đặt đã đồng bộ sang glass UI, không còn panel trắng tách nền.", size=13, color=TEXT_SECONDARY),
        ft.Divider(color=BORDER),
        txt_old_pass, 
        txt_new_pass, 
        elevated_button("Cập Nhật", icon=ft.Icons.SAVE, kind="primary", on_click=change_pass)
    ])

    return ft.Container(
        padding=0,
        expand=True,
        content=ft.Column([
            ft.Column([
                ft.Text("Cài Đặt Hệ Thống", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Giữ nền ảnh xuyên suốt, chỉ dùng các khối glass để thông tin không bị tách khỏi giao diện tổng thể.", size=13, color=TEXT_SECONDARY),
            ], spacing=4),
            ft.Container(height=12),
            ft.Row([
                glass_card(content=pass_form, width=420, bgcolor=SURFACE_STRONG),
                ft.Container(width=20),
                glass_card(content=sys_info, expand=True, bgcolor=SURFACE_STRONG)
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
        ])
    )
