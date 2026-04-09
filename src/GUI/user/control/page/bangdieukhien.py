import flet as ft
import json
import os
import threading
import time
from datetime import datetime, timedelta

# Đường dẫn dữ liệu
JSON_FILE = "src/GUI/data/accounts.json"
DASHBOARD_DATA_FILE = "src/GUI/data/dashboard_data.json"

class BangDieuKhienPage(ft.Stack):
    """Trang Bảng Điều Khiển (Dashboard) cho tài xế"""

    def __init__(self, user_account=None, switch_page_callback=None):
        # Đổi thành Stack và ép lề âm để tràn viền hoàn toàn
        super().__init__(expand=True)
        self.margin = ft.margin.all(-20)
        
        self.user_account = user_account or {}
        self.username = self.user_account.get("username", "user01")
        self.switch_page_callback = switch_page_callback
        self.running = False

        # --- MÀU SẮC THEME HIỆN ĐẠI DÀNH CHO BACKGROUND ---
        self.PRIMARY = "#4CAF50"
        self.PRIMARY_DARK = "#2E7D32"
        self.PRIMARY_LIGHT = "#81C784"
        
        # Bảng màu cho text trên nền đen
        self.TEXT_PRIMARY = ft.Colors.WHITE
        self.TEXT_SECONDARY = ft.Colors.WHITE70
        
        # Dùng màu nền nửa trong suốt để tạo hiệu ứng kính (Glassmorphism)
        self.CARD_BG = ft.Colors.with_opacity(0.15, ft.Colors.WHITE)
        
        self.ACCENT_BLUE = "#64B5F6"
        self.ACCENT_ORANGE = "#FFB74D"
        self.ACCENT_RED = "#E57373"
        self.ACCENT_PURPLE = "#BA68C8"

        # --- DỮ LIỆU DASHBOARD ---
        self.dashboard_data = self._load_dashboard_data()

        # --- UI REFERENCES ---
        self.clock_text = ft.Text("", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        self.date_text = ft.Text("", size=14, color=ft.Colors.WHITE70)
        self.greeting_text = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

        # --- INIT ---
        self.init_ui()

    def did_mount(self):
        super().did_mount()
        self.running = True
        threading.Thread(target=self._start_clock, daemon=True).start()

    def will_unmount(self):
        super().will_unmount()
        self.running = False

    # ============================================================
    # DATA LAYER
    # ============================================================
    def _load_dashboard_data(self):
        """Đọc dữ liệu dashboard từ file JSON"""
        default_data = {
            "users": {}
        }

        if os.path.exists(DASHBOARD_DATA_FILE):
            try:
                with open(DASHBOARD_DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Lỗi đọc dashboard data: {e}")

        return default_data

    def _save_dashboard_data(self):
        """Lưu dữ liệu dashboard"""
        try:
            os.makedirs(os.path.dirname(DASHBOARD_DATA_FILE), exist_ok=True)
            with open(DASHBOARD_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.dashboard_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Lỗi lưu dashboard data: {e}")

    def _get_user_data(self):
        """Lấy dữ liệu dashboard của user hiện tại"""
        if self.username not in self.dashboard_data.get("users", {}):
            self.dashboard_data.setdefault("users", {})[self.username] = {
                "login_history": [],
                "driving_sessions": [],
                "total_km": 0,
                "total_alerts": 0,
                "safety_score": 100,
            }
        return self.dashboard_data["users"][self.username]

    def _record_login(self):
        """Ghi nhận lần đăng nhập mới"""
        user_data = self._get_user_data()
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        login_time = now.strftime("%H:%M:%S")

        # Thêm vào lịch sử đăng nhập
        login_entry = {"date": today_str, "time": login_time}
        user_data.setdefault("login_history", []).append(login_entry)

        # Giới hạn 100 bản ghi gần nhất
        if len(user_data["login_history"]) > 100:
            user_data["login_history"] = user_data["login_history"][-100:]

        self._save_dashboard_data()

    def _get_today_logins(self):
        """Đếm số lần đăng nhập hôm nay"""
        user_data = self._get_user_data()
        today_str = datetime.now().strftime("%Y-%m-%d")
        count = sum(1 for entry in user_data.get("login_history", [])
                    if entry.get("date") == today_str)
        return count

    def _get_today_driving_time(self):
        """Tính tổng thời gian lái xe hôm nay (phút)"""
        user_data = self._get_user_data()
        today_str = datetime.now().strftime("%Y-%m-%d")
        total_minutes = sum(
            s.get("duration_minutes", 0)
            for s in user_data.get("driving_sessions", [])
            if s.get("date") == today_str
        )
        return total_minutes

    def _get_weekly_stats(self):
        """Thống kê 7 ngày gần đây"""
        user_data = self._get_user_data()
        today = datetime.now().date()
        weekly = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            day_label = d.strftime("%a")
            logins = sum(1 for entry in user_data.get("login_history", [])
                         if entry.get("date") == d_str)
            minutes = sum(
                s.get("duration_minutes", 0)
                for s in user_data.get("driving_sessions", [])
                if s.get("date") == d_str
            )
            weekly.append({"day": day_label, "date": d_str, "logins": logins, "minutes": minutes})
        return weekly

    def _get_safety_score(self):
        """Lấy điểm an toàn"""
        user_data = self._get_user_data()
        return user_data.get("safety_score", 100)

    def _get_today_alerts(self):
        """Lấy tổng số cảnh báo hôm nay"""
        user_data = self._get_user_data()
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_alerts = user_data.get("daily_alerts", {})
        return daily_alerts.get(today_str, 0)

    def _get_total_km(self):
        """Lấy tổng km đã đi"""
        user_data = self._get_user_data()
        return user_data.get("total_km", 0)

    # ============================================================
    # CLOCK & GREETING
    # ============================================================
    def _start_clock(self):
        """Khởi động đồng hồ realtime"""
        days_vi = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        while self.running:
            try:
                now = datetime.now()
                self.clock_text.value = now.strftime("%H:%M:%S")

                day_name = days_vi[now.weekday()]
                self.date_text.value = f"{day_name}, {now.strftime('%d/%m/%Y')}"

                hour = now.hour
                name = self.user_account.get("name", "Tài xế")
                if hour < 12:
                    greeting = f"☀️ Chào buổi sáng, {name}!"
                elif hour < 18:
                    greeting = f"🌤️ Chào buổi chiều, {name}!"
                else:
                    greeting = f"🌙 Chào buổi tối, {name}!"
                self.greeting_text.value = greeting

                if getattr(self, "page", None):
                    self.clock_text.update()
                    self.date_text.update()
                    self.greeting_text.update()
            except Exception:
                pass
            time.sleep(1)

    # ============================================================
    # UI BUILDER
    # ============================================================
    def _create_stat_card(self, icon, icon_color, title, value, subtitle=""):
        """Tạo thẻ thống kê"""
        card_content = ft.Container(
            padding=20,
            border_radius=20,
            bgcolor=self.CARD_BG,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=ft.Colors.WHITE, size=22),
                        width=44, height=44,
                        bgcolor=icon_color,
                        border_radius=12,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(expand=True),
                ]),
                ft.Container(height=12),
                ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
                ft.Text(title, size=13, color=self.TEXT_SECONDARY),
                ft.Text(subtitle, size=11, color=ft.Colors.WHITE54) if subtitle else ft.Container(),
            ], spacing=2)
        )
        return card_content

    def _create_activity_item(self, time_str, activity, icon, color):
        """Tạo mục hoạt động gần đây"""
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=ft.Colors.WHITE, size=18),
                    width=36, height=36,
                    bgcolor=color,
                    border_radius=10,
                    alignment=ft.alignment.center,
                ),
                ft.Column([
                    ft.Text(activity, size=13, weight=ft.FontWeight.W_600, color=self.TEXT_PRIMARY),
                    ft.Text(time_str, size=11, color=self.TEXT_SECONDARY),
                ], spacing=2, expand=True),
            ], spacing=12)
        )

    def _create_weekly_chart(self):
        """Tạo biểu đồ hoạt động 7 ngày"""
        weekly = self._get_weekly_stats()
        max_logins = max((w["logins"] for w in weekly), default=1)
        if max_logins == 0:
            max_logins = 1
        chart_height = 120

        bars = []
        for w in weekly:
            bar_height = max((w["logins"] / max_logins) * chart_height, 6)
            is_today = w["date"] == datetime.now().strftime("%Y-%m-%d")

            bars.append(
                ft.Column([
                    ft.Text(str(w["logins"]), size=10, weight=ft.FontWeight.BOLD,
                            color=self.PRIMARY if is_today else self.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(
                        width=30, height=bar_height,
                        border_radius=ft.border_radius.only(top_left=6, top_right=6),
                        bgcolor=self.PRIMARY if is_today else ft.Colors.with_opacity(0.3, self.PRIMARY),
                        animate=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
                    ),
                    ft.Text(w["day"], size=10, color=self.PRIMARY if is_today else self.TEXT_SECONDARY,
                            weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.END, spacing=4, width=45)
            )

        return ft.Container(
            padding=20,
            border_radius=20,
            bgcolor=self.CARD_BG,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.BAR_CHART_ROUNDED, color=self.PRIMARY, size=22),
                    ft.Text("Hoạt động 7 ngày gần đây", size=15, weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=12),
                ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ])
        )

    def _get_monthly_stats(self):
        """Thống kê 30 ngày qua"""
        user_data = self._get_user_data()
        today = datetime.now().date()
        monthly = []
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            day_label = d.strftime("%d")
            minutes = sum(
                s.get("duration_minutes", 0)
                for s in user_data.get("driving_sessions", [])
                if s.get("date") == d_str
            )
            monthly.append({"day": day_label, "date": d_str, "minutes": minutes})
        return monthly

    def _create_monthly_chart(self):
        """Tạo biểu đồ dạng cột thống kê thời gian lái xe 30 ngày qua"""
        monthly = self._get_monthly_stats()
        
        max_minutes = max((w["minutes"] for w in monthly), default=1)
        if max_minutes == 0:
            max_minutes = 10 
            
        chart_groups = []
        x_labels = []
        for index, item in enumerate(monthly):
            is_today = item["date"] == datetime.now().strftime("%Y-%m-%d")
            color = self.ACCENT_BLUE if is_today else ft.Colors.with_opacity(0.6, self.PRIMARY)
            
            chart_groups.append(
                ft.BarChartGroup(
                    x=index,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=item["minutes"],
                            width=12,
                            color=color,
                            tooltip=f"Ngày {item['day']} : {item['minutes']} phút",
                            border_radius=ft.border_radius.only(top_left=4, top_right=4)
                        )
                    ]
                )
            )
            
            if index % 5 == 0 or is_today:
                x_labels.append(
                    ft.ChartAxisLabel(
                        value=index,
                        label=ft.Container(
                            ft.Text(item["day"], size=10, color=self.TEXT_SECONDARY, weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL),
                            padding=ft.padding.only(top=5)
                        )
                    )
                )

        import math
        ceil_max = math.ceil(max_minutes / 10.0) * 10
        if ceil_max == 0: ceil_max = 10

        chart = ft.BarChart(
            bar_groups=chart_groups,
            border=ft.border.all(0, ft.Colors.TRANSPARENT),
            left_axis=ft.ChartAxis(
                labels_size=35,
                title=ft.Text("Phút", size=12, color=self.TEXT_SECONDARY),
                title_size=20,
                labels_interval=ceil_max/5 if ceil_max > 5 else 1
            ),
            bottom_axis=ft.ChartAxis(
                labels=x_labels, 
                labels_size=25,
                title=ft.Text("Ngày trong tháng", size=12, color=self.TEXT_SECONDARY),
                title_size=20,
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE), width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
            max_y=ceil_max,
            interactive=True,
            expand=True,
        )

        return ft.Container(
            padding=20,
            border_radius=20,
            bgcolor=self.CARD_BG,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            height=300,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.BAR_CHART_ROUNDED, color=self.ACCENT_BLUE, size=22),
                    ft.Text("Thời Gian Lái Xe (30 Ngày Qua)", size=15, weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=12),
                ft.Container(
                    content=chart,
                    expand=True,
                )
            ])
        )

    def _create_safety_gauge(self):
        """Tạo thẻ điểm an toàn"""
        score = self._get_safety_score()

        if score >= 80:
            score_color = self.PRIMARY
            comment = "Xuất sắc! Hãy duy trì phong độ."
            emoji = "🛡️"
        elif score >= 60:
            score_color = self.ACCENT_ORANGE
            comment = "Khá tốt, cần cải thiện thêm."
            emoji = "⚠️"
        else:
            score_color = self.ACCENT_RED
            comment = "Cần chú ý an toàn hơn!"
            emoji = "🚨"

        return ft.Container(
            padding=24,
            border_radius=20,
            bgcolor=self.CARD_BG,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SHIELD, color=score_color, size=22),
                    ft.Text("Điểm An Toàn", size=15, weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=16),
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"{score}", size=48, weight=ft.FontWeight.BOLD, color=score_color),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(width=8),
                    ft.Column([
                        ft.Text(f"{emoji} /100 điểm", size=14, color=self.TEXT_SECONDARY),
                        ft.Container(height=4),
                        ft.ProgressBar(
                            value=score / 100,
                            width=180, height=8,
                            color=score_color,
                            bgcolor=ft.Colors.with_opacity(0.15, score_color),
                            border_radius=4,
                        ),
                        ft.Container(height=4),
                        ft.Text(comment, size=12, color=self.TEXT_SECONDARY, italic=True),
                    ], spacing=0, expand=True),
                ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ])
        )

    def _create_quick_actions(self):
        """Tạo khu vực hành động nhanh"""
        def create_action_btn(icon, label, color, target_page):
            def on_action_click(e):
                if self.switch_page_callback:
                    self.switch_page_callback(target_page)
                    
            return ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(icon, color=ft.Colors.WHITE, size=24),
                        width=52, height=52,
                        bgcolor=color,
                        border_radius=14,
                        alignment=ft.alignment.center,
                        shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.4, color), offset=ft.Offset(0, 3)),
                    ),
                    ft.Text(label, size=11, color=self.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER,
                            weight=ft.FontWeight.W_500),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                on_click=on_action_click,
                ink=True,
                border_radius=12,
                padding=8,
            )

        return ft.Container(
            padding=20,
            border_radius=20,
            bgcolor=self.CARD_BG,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.FLASH_ON, color=self.ACCENT_ORANGE, size=22),
                    ft.Text("Truy Cập Nhanh", size=15, weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=12),
                ft.Row([
                    create_action_btn(ft.Icons.DIRECTIONS_CAR, "Bắt đầu\nlái xe", self.PRIMARY, "session"),
                    create_action_btn(ft.Icons.DASHBOARD_CUSTOMIZE, "Tiện ích\n", self.ACCENT_BLUE, "utilities"),
                    create_action_btn(ft.Icons.SETTINGS, "Cài đặt\nhệ thống", self.ACCENT_ORANGE, "settings"),
                    create_action_btn(ft.Icons.PERSON, "Hồ sơ\ncá nhân", self.ACCENT_PURPLE, "profile"),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ])
        )

    def _create_recent_activity(self):
        """Tạo danh sách hoạt động gần đây"""
        user_data = self._get_user_data()
        login_history = user_data.get("login_history", [])

        recent_logins = login_history[-5:][::-1]

        activity_items = []
        for entry in recent_logins:
            time_str = f"{entry.get('date', '')} lúc {entry.get('time', '')}"
            activity_items.append(
                self._create_activity_item(
                    time_str,
                    "Đăng nhập hệ thống",
                    ft.Icons.LOGIN,
                    self.PRIMARY
                )
            )

        if not activity_items:
            activity_items.append(
                ft.Container(
                    padding=20,
                    alignment=ft.alignment.center,
                    content=ft.Column([
                        ft.Icon(ft.Icons.INBOX, size=40, color=ft.Colors.WHITE54),
                        ft.Text("Chưa có hoạt động nào", color=self.TEXT_SECONDARY, size=13),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                )
            )

        return ft.Container(
            padding=20,
            border_radius=20,
            bgcolor=self.CARD_BG,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ACCESS_TIME, color=self.ACCENT_BLUE, size=22),
                    ft.Text("Hoạt Động Gần Đây", size=15, weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=12),
                ft.Column(activity_items, spacing=8),
            ])
        )

    def _create_system_status(self):
        """Tạo thẻ trạng thái hệ thống"""
        def status_row(label, status, is_ok=True):
            return ft.Row([
                ft.Container(
                    width=10, height=10,
                    bgcolor=self.PRIMARY if is_ok else self.ACCENT_RED,
                    border_radius=5,
                ),
                ft.Text(label, size=13, color=self.TEXT_PRIMARY, expand=True),
                ft.Text(
                    status, size=12, weight=ft.FontWeight.BOLD,
                    color=self.PRIMARY if is_ok else self.ACCENT_RED
                ),
            ], spacing=10)

        tele_data = self.user_account.get("telegram_data", {})
        has_telegram = bool(tele_data.get("chat_id"))

        return ft.Container(
            padding=20,
            border_radius=20,
            bgcolor=self.CARD_BG,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.MONITOR_HEART, color=self.ACCENT_RED, size=22),
                    ft.Text("Trạng Thái Hệ Thống", size=15, weight=ft.FontWeight.BOLD, color=self.TEXT_PRIMARY),
                ], spacing=8),
                ft.Container(height=12),
                status_row("Camera AI", "Sẵn sàng", True),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                status_row("Telegram", "Đã kết nối" if has_telegram else "Chưa kết nối", has_telegram),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                status_row("Model AI", "YOLOv8n", True),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                status_row("Gói dịch vụ", self.user_account.get("plan", "Free"), True),
            ], spacing=8)
        )

    # ============================================================
    # MAIN UI
    # ============================================================
    def init_ui(self):
        # --- LỚP NỀN BACKGROUND TRÀN VIỀN ---
        IMG_BG = r"E:\code\AppGS_v2\giam_sat_lai_xe\src\GUI\data\image_user\backround.jpg"
        
        bg_image = ft.Image(
            src=IMG_BG,
            fit=ft.ImageFit.COVER,
            expand=True
        )
        
        # Làm mờ nền giúp các Glassmorphism Cards nổi bật
        bg_overlay = ft.Container(
            bgcolor=ft.Colors.BLACK54, 
            expand=True,
            blur=10 
        )
        
        today_logins = self._get_today_logins()
        today_driving = self._get_today_driving_time()
        today_alerts = self._get_today_alerts()
        total_km = self._get_total_km()

        hours = today_driving // 60
        mins = today_driving % 60
        driving_display = f"{hours}h {mins}m" if hours > 0 else f"{mins} phút"

        # --- HEADER: Lời chào ---
        header_section = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK45, offset=ft.Offset(0, 10)),
            content=ft.Row([
                ft.Column([
                    self.greeting_text,
                    ft.Container(height=4),
                    ft.Row([
                        ft.Icon(ft.Icons.BADGE, color=ft.Colors.WHITE54, size=16),
                        ft.Text(
                            f"ID: {self.user_account.get('driver_id', 'N/A')}  •  {self.user_account.get('plan', 'Free').upper()}",
                            size=13, color=ft.Colors.WHITE70
                        ),
                    ], spacing=6),
                ], spacing=2, expand=True),
                ft.Column([
                    self.clock_text,
                    self.date_text,
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # --- STAT CARDS ---
        stat_cards = ft.Row([
            ft.Container(
                expand=True,
                content=self._create_stat_card(
                    ft.Icons.LOGIN, self.PRIMARY,
                    "Đăng nhập hôm nay", str(today_logins),
                    "Số lần truy cập"
                ),
            ),
            ft.Container(
                expand=True,
                content=self._create_stat_card(
                    ft.Icons.TIMER, self.ACCENT_BLUE,
                    "Thời gian lái hôm nay", driving_display,
                    "Tổng thời gian"
                ),
            ),
            ft.Container(
                expand=True,
                content=self._create_stat_card(
                    ft.Icons.WARNING_AMBER_ROUNDED, self.ACCENT_ORANGE,
                    "Cảnh báo hôm nay", str(today_alerts),
                    "Số lần cảnh báo",
                ),
            ),
            ft.Container(
                expand=True,
                content=self._create_stat_card(
                    ft.Icons.ROUTE, self.ACCENT_PURPLE,
                    "Quãng đường", f"{total_km} km",
                    "Tổng km đã đi",
                ),
            ),
        ], spacing=16) # Tăng spacing một chút cho dễ nhìn trên nền đen

        # --- MAIN CONTENT (2 cột) ---
        left_column = ft.Column([
            self._create_weekly_chart(),
            self._create_safety_gauge(),
            self._create_quick_actions(),
        ], spacing=16, expand=True)

        right_column = ft.Column([
            self._create_recent_activity(),
            self._create_system_status(),
        ], spacing=16, expand=True)

        main_content = ft.Column([
            self._create_monthly_chart(),
            ft.Container(height=8),
            ft.Row([
                left_column,
                right_column,
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START)
        ])

        # --- CUỘN NỘI DUNG (SCROLLABLE LAYER) ---
        scrollable_content = ft.Container(
            padding=ft.padding.only(left=40, right=40, top=30, bottom=20),
            expand=True,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.DASHBOARD_ROUNDED, color=self.PRIMARY, size=30),
                    ft.Text("Bảng Điều Khiển", size=28, weight=ft.FontWeight.W_900, color=self.TEXT_PRIMARY),
                ], spacing=10),
                ft.Container(height=10),
                header_section,
                ft.Container(height=15),
                stat_cards,
                ft.Container(height=15),
                main_content,
                ft.Container(height=20),
            ], spacing=0, scroll=ft.ScrollMode.AUTO)
        )

        # --- GHÉP VÀO STACK ---
        self.controls = [
            bg_image,
            bg_overlay,
            scrollable_content
        ]