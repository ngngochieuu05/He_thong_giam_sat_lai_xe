# -*- coding: utf-8 -*-
"""
Telegram Link Page
Màn hình liên kết Telegram sau khi đăng ký thành công
"""

import flet as ft
import threading
import time
import webbrowser
from .control.ui_styles import elevated_button, text_button

# Initialize Telegram bot
try:
    from .. import bot_init
except:
    pass


class TelegramLinkPage:
    """
    Trang liên kết Telegram với token tự động
    Hiển thị token, instructions, và status checking
    """
    
    def __init__(self, page: ft.Page, username: str, on_complete_callback=None):
        """
        Args:
            page: Flet page
            username: Username đã đăng ký
            on_complete_callback: Callback khi hoàn thành liên kết
        """
        self.page = page
        self.username = username
        self.on_complete_callback = on_complete_callback
        
        self.page.title = "Liên Kết Telegram - SafeDrive"
        self.page.padding = 0
        self.page.bgcolor = "#0A0E27"
        
        # State
        self.token = ""
        self.is_checking = False
        self.check_thread = None
        
        # Import telegram_link_service
        try:
            import sys
            import os
            # Add oa_core to path
            oa_core_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "BUS", "oa_core"
            )
            if oa_core_path not in sys.path:
                sys.path.insert(0, oa_core_path)
            
            from telegram_link_service import (
                generate_link_token,
                check_bound,
                get_bot_info
            )
            self.generate_link_token = generate_link_token
            self.check_bound = check_bound
            self.get_bot_info = get_bot_info
            print(f"[TelegramLinkPage] Successfully imported telegram_link_service")
        except Exception as e:
            print(f"[TelegramLinkPage] Error importing telegram_link_service: {e}")
            self.generate_link_token = None
            self.check_bound = None
            self.get_bot_info = None
        
        # UI Components
        self.token_text = ft.Text(
            value="Đang tạo token...",
            size=24,
            weight=ft.FontWeight.BOLD,
            color="#4CAF50",
            selectable=True,
            text_align=ft.TextAlign.CENTER
        )
        
        self.status_text = ft.Text(
            value="⏳ Đang chờ bạn bấm Start trong Telegram...",
            size=16,
            color="#FBBF24",
            text_align=ft.TextAlign.START
        )
        
        self.copy_button = elevated_button("Sao chép Token", icon=ft.Icons.COPY, on_click=self._copy_token, kind="surface", height=45)
        
        self.open_bot_button = elevated_button("Mở bot và bắt đầu liên kết", icon=ft.Icons.TELEGRAM, on_click=self._open_telegram, kind="primary", height=50)
        
        self.check_status_button = elevated_button("Tôi đã bấm Start, kiểm tra lại", icon=ft.Icons.REFRESH, on_click=self._manual_check_status, kind="surface", height=45)
        
        # Build UI
        self._build_ui()
        
        # Generate token
        self._generate_token()
        
        # Start auto status check
        self._start_auto_check()
    
    def _build_ui(self):
        """Xây dựng giao diện"""
        
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Icon(name=ft.Icons.TELEGRAM, size=70, color="#4CAF50"),
                ft.Text(
                    "Liên Kết Telegram",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Bước cuối để nhận thông báo an toàn",
                    size=16,
                    color="#9CA3AF",
                    text_align=ft.TextAlign.CENTER
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=ft.padding.only(bottom=20),
        )
        
        # Token display card
        token_card = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Token của bạn",
                    size=14,
                    color="#9CA3AF",
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(
                    content=self.token_text,
                    bgcolor="#111827",
                    padding=15,
                    border_radius=10,
                    width=float("inf"),
                    alignment=ft.alignment.center,
                ),
                self.copy_button,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
            bgcolor="#1F2937",
            border_radius=15,
            padding=24,
            width=float("inf"),
        )
        
        # Instructions
        instructions = ft.Container(
            content=ft.Column([
                ft.Text(
                    "📱 Hướng dẫn liên kết",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color="white"
                ),
                ft.Divider(height=1, color="#374151"),
                ft.Row([
                    ft.Container(content=ft.Text("1", size=14, color="white", weight=ft.FontWeight.BOLD), width=28, height=28, bgcolor="#4CAF50", border_radius=14, alignment=ft.alignment.center),
                    ft.Text("Nhấn nút mở bot ở bên dưới", size=15, color="#D1D5DB")
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Container(content=ft.Text("2", size=14, color="white", weight=ft.FontWeight.BOLD), width=28, height=28, bgcolor="#4CAF50", border_radius=14, alignment=ft.alignment.center),
                    ft.Text("Telegram sẽ mở bot kèm sẵn token của tài khoản", size=15, color="#D1D5DB")
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Container(content=ft.Text("3", size=14, color="white", weight=ft.FontWeight.BOLD), width=28, height=28, bgcolor="#4CAF50", border_radius=14, alignment=ft.alignment.center),
                    ft.Text("Trong cửa sổ Telegram, chỉ cần bấm Start để xác nhận", size=15, color="#D1D5DB")
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Container(content=ft.Text("4", size=14, color="white", weight=ft.FontWeight.BOLD), width=28, height=28, bgcolor="#4CAF50", border_radius=14, alignment=ft.alignment.center),
                    ft.Text("Quay lại app và bấm kiểm tra lại, hoặc chờ app tự phát hiện liên kết", size=15, color="#D1D5DB")
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=16),
            bgcolor="#1F2937",
            border_radius=15,
            padding=24,
            width=float("inf"),
        )
        
        # Status indicator
        status_card = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color="#FBBF24", size=24),
                ft.Container(content=self.status_text, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
            bgcolor="#374151",
            border_radius=12,
            padding=16,
            width=float("inf"),
        )
        
        # Action buttons
        action_buttons = ft.Container(
            content=ft.Column([
                ft.Container(content=self.open_bot_button, width=float("inf")),
                ft.Container(content=self.check_status_button, width=float("inf")),
                ft.Text("Nếu đã mở bot nhưng trạng thái chưa đổi, hãy bấm Start trong Telegram rồi quay lại đây.", size=13, color="#9CA3AF", text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
            width=float("inf"),
        )
        
        # Main card container
        main_card = ft.Container(
            content=ft.Column([
                header,
                token_card,
                instructions,
                status_card,
                action_buttons,
            ], spacing=24, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=700,
            bgcolor="#111827",
            border_radius=20,
            padding=40,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.3, "black"),
                offset=ft.Offset(0, 10)
            ),
        )
        
        # Center horizontally and vertically on page
        layout = ft.Container(
            content=main_card,
            alignment=ft.alignment.top_center,
            padding=ft.padding.symmetric(vertical=40, horizontal=20),
            expand=True
        )

        self.page.clean()
        self.page.add(ft.Column([layout], scroll=ft.ScrollMode.AUTO, expand=True))
        self.page.update()
    
    def _generate_token(self):
        """Generate token từ backend"""
        if not self.generate_link_token:
            self.token_text.value = "Lỗi: Không thể tạo token"
            self.token_text.color = "#F44336"
            self.page.update()
            return
        
        try:
            self.token = self.generate_link_token(self.username)
            self.token_text.value = self.token
            self.token_text.color = "#4CAF50"
            print(f"[TelegramLinkPage] Generated token for {self.username}: {self.token}")
        except Exception as e:
            print(f"[TelegramLinkPage] Error generating token: {e}")
            self.token_text.value = "Lỗi khi tạo token"
            self.token_text.color = "#F44336"
        
        self.page.update()
    
    def _copy_token(self, e):
        """Sao chép token vào clipboard"""
        if self.token:
            self.page.set_clipboard(self.token)
            
            # Show feedback
            self.copy_button.text = "Đã sao chép!"
            self.copy_button.icon = ft.Icons.CHECK
            self.copy_button.bgcolor = "#10B981"
            self.page.update()
            
            # Reset after 2 seconds
            def reset_button():
                time.sleep(2)
                self.copy_button.text = "Sao chép Token"
                self.copy_button.icon = ft.Icons.COPY
                self.copy_button.bgcolor = "#374151"
                self.page.update()
            
            threading.Thread(target=reset_button, daemon=True).start()
    
    def _open_telegram(self, e):
        """Mở Telegram bot với deep link"""
        if not self.get_bot_info:
            print("[TelegramLinkPage] get_bot_info not available")
            return
        
        try:
            bot_info = self.get_bot_info()
            bot_url = bot_info.get("bot_url", "https://t.me/safedrive_alert_bot")
            
            # Create deep link with token
            deep_link = f"{bot_url}?start={self.token}"
            
            print(f"[TelegramLinkPage] Opening Telegram: {deep_link}")
            webbrowser.open(deep_link)
        except Exception as e:
            print(f"[TelegramLinkPage] Error opening Telegram: {e}")
    
    def _manual_check_status(self, e):
        """Manual check linking status"""
        self._check_link_status()
    
    def _check_link_status(self):
        """Kiểm tra trạng thái liên kết"""
        if not self.check_bound:
            return
        
        try:
            telegram_data = self.check_bound(self.username)
            
            if telegram_data:
                # Linked successfully!
                self.status_text.value = "✅ Đã liên kết thành công!"
                self.status_text.color = "#4CAF50"
                self.page.update()
                
                # Stop auto check
                self.is_checking = False
                
                # Show success dialog
                self._show_success_dialog()
            else:
                # Not linked yet
                self.status_text.value = "⏳ Đang chờ liên kết..."
                self.status_text.color = "#FFEB3B"
                self.page.update()
        except Exception as e:
            print(f"[TelegramLinkPage] Error checking status: {e}")
    
    def _start_auto_check(self):
        """Tự động kiểm tra status mỗi 3 giây"""
        self.is_checking = True
        
        def auto_check():
            while self.is_checking:
                self._check_link_status()
                time.sleep(3)
        
        self.check_thread = threading.Thread(target=auto_check, daemon=True)
        self.check_thread.start()
    
    def _show_success_dialog(self):
        """Hiển thị dialog thành công và redirect"""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("🎉 Liên kết thành công!", color="#4CAF50", size=20),
            content=ft.Text(
                "Tài khoản của bạn đã được liên kết với Telegram.\n\n"
                "Bạn sẽ nhận thông báo an toàn từ SafeDrive qua Telegram.",
                size=16
            ),
            actions=[
                text_button("Tiếp tục", on_click=lambda e: self._complete_linking(dialog), kind="primary"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        
        # Auto close after 3 seconds
        def auto_close():
            time.sleep(3)
            self._complete_linking(dialog)
        
        threading.Thread(target=auto_close, daemon=True).start()
    
    def _complete_linking(self, dialog):
        """Hoàn thành liên kết và chuyển màn"""
        try:
            dialog.open = False
            self.page.update()
        except:
            pass
        
        # Call callback
        if self.on_complete_callback:
            self.on_complete_callback()
    
    def cleanup(self):
        """Dọn dẹp khi rời khỏi page"""
        self.is_checking = False
        if self.check_thread:
            self.check_thread.join(timeout=1)


# ===== TEST =====
if __name__ == "__main__":
    def main(page: ft.Page):
        def on_complete():
            print("Linking completed!")
            page.clean()
            page.add(ft.Text("Đã hoàn thành liên kết!", size=30))
            page.update()
        
        TelegramLinkPage(page, "test_user", on_complete)
    
    ft.app(target=main)
