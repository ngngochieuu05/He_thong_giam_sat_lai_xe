import flet as ft

def QuanLiModel(page_title, page):
    # =================== MODEL NHẬN DIỆN SINH TRẮC HỌC ===================
    # Danh sách model sinh trắc học
    biometric_models = ["FaceNet (v1.0)", "ArcFace (v2.1)", "DeepFace (v1.5)"]
    selected_biometric = ft.Dropdown(
        label="Chọn Model Sinh Trắc Học",
        width=300,
        options=[ft.dropdown.Option(m) for m in biometric_models],
        value=biometric_models[0]
    )
    
    # File picker cho model sinh trắc
    bio_file_path = ft.Text("Chưa chọn file", size=12, color=ft.Colors.GREY, italic=True)
    
    def pick_bio_model(e: ft.FilePickerResultEvent):
        if e.files:
            bio_file_path.value = e.files[0].path
            bio_file_path.italic = False
            bio_file_path.color = ft.Colors.GREEN
            bio_file_path.update()
    
    bio_file_picker = ft.FilePicker(on_result=pick_bio_model)
    page.overlay.append(bio_file_picker)
    
    # Tham số model sinh trắc học
    bio_threshold = ft.Text("0.75", weight="bold", color=ft.Colors.BLUE)
    bio_min_face_size = ft.Text("40", weight="bold", color=ft.Colors.BLUE)
    
    def update_bio_threshold(e):
        bio_threshold.value = f"{e.control.value:.2f}"
        bio_threshold.update()
    
    def update_bio_min_face(e):
        bio_min_face_size.value = f"{int(e.control.value)}"
        bio_min_face_size.update()
    
    biometric_config_card = ft.Container(
        bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
        content=ft.Column([
            ft.Text("🔐 Model Nhận Diện Sinh Trắc Học", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
            ft.Divider(),
            selected_biometric,
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton(
                    "Chọn File Model (.pt)",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda _: bio_file_picker.pick_files(
                        allowed_extensions=["pt"],
                        dialog_title="Chọn Model Sinh Trắc Học (.pt)"
                    )
                ),
            ]),
            bio_file_path,
            ft.Container(height=10),
            ft.Text("Tham Số Model:", size=14, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("Ngưỡng Độ Tin Cậy: "), bio_threshold
            ]),
            ft.Slider(min=0.5, max=1.0, divisions=50, value=0.75, on_change=update_bio_threshold),
            
            ft.Row([
                ft.Text("Kích Thước Khuôn Mặt Tối Thiểu (px): "), bio_min_face_size
            ]),
            ft.Slider(min=20, max=100, divisions=80, value=40, on_change=update_bio_min_face),
            
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton("Lưu Cấu Hình", icon=ft.Icons.SAVE, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                ft.ElevatedButton("Test Model", icon=ft.Icons.PLAY_ARROW, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
            ])
        ])
    )

    # =================== MODEL NHẬN DIỆN NGỦ GẬT ===================
    # Danh sách model ngủ gật
    drowsiness_models = ["YOLOv8n-Drowsy (v1.0)", "YOLOv11-Drowsy (v2.0)", "Custom-CNN (v1.2)"]
    selected_drowsiness = ft.Dropdown(
        label="Chọn Model Nhận Diện Ngủ Gật",
        width=300,
        options=[ft.dropdown.Option(m) for m in drowsiness_models],
        value=drowsiness_models[0]
    )
    
    # File picker cho model ngủ gật
    drowsy_file_path = ft.Text("Chưa chọn file", size=12, color=ft.Colors.GREY, italic=True)
    
    def pick_drowsy_model(e: ft.FilePickerResultEvent):
        if e.files:
            drowsy_file_path.value = e.files[0].path
            drowsy_file_path.italic = False
            drowsy_file_path.color = ft.Colors.GREEN
            drowsy_file_path.update()
    
    drowsy_file_picker = ft.FilePicker(on_result=pick_drowsy_model)
    page.overlay.append(drowsy_file_picker)
    
    # Tham số model ngủ gật
    drowsy_conf = ft.Text("0.50", weight="bold", color=ft.Colors.ORANGE)
    drowsy_iou = ft.Text("0.45", weight="bold", color=ft.Colors.ORANGE)
    
    def update_drowsy_conf(e):
        drowsy_conf.value = f"{e.control.value:.2f}"
        drowsy_conf.update()
    
    def update_drowsy_iou(e):
        drowsy_iou.value = f"{e.control.value:.2f}"
        drowsy_iou.update()
    
    drowsiness_config_card = ft.Container(
        bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
        content=ft.Column([
            ft.Text("😴 Model Nhận Diện Ngủ Gật", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
            ft.Divider(),
            selected_drowsiness,
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton(
                    "Chọn File Model (.pt)",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda _: drowsy_file_picker.pick_files(
                        allowed_extensions=["pt"],
                        dialog_title="Chọn Model Ngủ Gật (.pt)"
                    )
                ),
            ]),
            drowsy_file_path,
            ft.Container(height=10),
            ft.Text("Tham Số Model:", size=14, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("Ngưỡng Tin Cậy (Confidence): "), drowsy_conf
            ]),
            ft.Slider(min=0, max=1, divisions=100, value=0.50, on_change=update_drowsy_conf),
            
            ft.Row([
                ft.Text("Ngưỡng IoU (NMS): "), drowsy_iou
            ]),
            ft.Slider(min=0, max=1, divisions=100, value=0.45, on_change=update_drowsy_iou),
            
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton("Lưu Cấu Hình", icon=ft.Icons.SAVE, bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE),
                ft.ElevatedButton("Test Model", icon=ft.Icons.PLAY_ARROW, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
            ])
        ])
    )
    # =================== KHO LƯU TRỮ MODEL ===================
    # 2. Danh sách Model Versions (chung cho cả 2 loại)
    model_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Loại Model")),
            ft.DataColumn(ft.Text("Tên File")),
            ft.DataColumn(ft.Text("Version")),
            ft.DataColumn(ft.Text("Ngày Upload")),
            ft.DataColumn(ft.Text("Accuracy")),
            ft.DataColumn(ft.Text("Kích thước")),
            ft.DataColumn(ft.Text("Trạng thái")),
            ft.DataColumn(ft.Text("Hành động")),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Icon(ft.Icons.FACE, color=ft.Colors.BLUE)),
                ft.DataCell(ft.Text("facenet_model.h5")),
                ft.DataCell(ft.Text("v1.0.0")),
                ft.DataCell(ft.Text("20/01/2026")),
                ft.DataCell(ft.Text("98.5%")),
                ft.DataCell(ft.Text("25 MB")),
                ft.DataCell(ft.Container(content=ft.Text("Active", color="white", size=10), bgcolor="blue", padding=5, border_radius=5)),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Tải xuống"),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Cấu hình"),
                ])),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Icon(ft.Icons.REMOVE_RED_EYE, color=ft.Colors.ORANGE)),
                ft.DataCell(ft.Text("yolov8n_drowsy.pt")),
                ft.DataCell(ft.Text("v1.0.0")),
                ft.DataCell(ft.Text("18/01/2026")),
                ft.DataCell(ft.Text("92.5%")),
                ft.DataCell(ft.Text("12 MB")),
                ft.DataCell(ft.Container(content=ft.Text("Active", color="white", size=10), bgcolor="orange", padding=5, border_radius=5)),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Tải xuống"),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Cấu hình"),
                ])),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Icon(ft.Icons.REMOVE_RED_EYE, color=ft.Colors.ORANGE)),
                ft.DataCell(ft.Text("yolov11_drowsy.pt")),
                ft.DataCell(ft.Text("v2.0.0 (Beta)")),
                ft.DataCell(ft.Text("25/01/2026")),
                ft.DataCell(ft.Text("94.1%")),
                ft.DataCell(ft.Text("15 MB")),
                ft.DataCell(ft.Text("Backup")),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.UPLOAD, tooltip="Kích hoạt", icon_color="green"),
                    ft.IconButton(ft.Icons.DELETE, icon_color="red", tooltip="Xóa"),
                ])),
            ]),
        ],
        border=ft.border.all(1, ft.Colors.GREY_200),
        border_radius=10,
        vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_100),
        heading_row_color=ft.Colors.GREY_50,
    )

    list_card = ft.Container(
        bgcolor=ft.Colors.WHITE, border_radius=15, padding=20, expand=True,
        content=ft.Column([
            ft.Row([
                ft.Text("📦 Kho Lưu Trữ Model", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.ElevatedButton("Upload Model Sinh Trắc", icon=ft.Icons.UPLOAD_FILE, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                    ft.ElevatedButton("Upload Model Ngủ Gật", icon=ft.Icons.UPLOAD_FILE, bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Container(content=model_table, expand=True, padding=0)
        ])
    )

    return ft.Column([
        ft.Text("⚙️ " + page_title, size=24, weight=ft.FontWeight.BOLD),
        ft.Container(height=10),
        # Phần cấu hình 2 model song song
        ft.Row([
            ft.Container(content=biometric_config_card, expand=True),
            ft.Container(width=20),
            ft.Container(content=drowsiness_config_card, expand=True),
        ], expand=False),
        ft.Container(height=20),
        # Phần kho lưu trữ
        ft.Container(content=list_card, expand=True)
    ], expand=True, scroll=ft.ScrollMode.AUTO)