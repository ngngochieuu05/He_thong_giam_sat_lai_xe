import flet as ft
import cv2
import threading
import time
import json
import os
from ..ui_styles import (
    BORDER,
    DANGER,
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

def QuanLiModel(page_title, page):
    field_style = input_style()
    dropdown_style = {
        key: value
        for key, value in field_style.items()
        if key not in {"cursor_color", "hint_style"}
    }
    
    # =================== PHÁT HIỆN CAMERA CÓ SẴN ===================
    def get_available_cameras():
        """Phát hiện tất cả camera có sẵn trên hệ thống - kiểm tra thực tế bằng cách đọc frame"""
        available_cameras = []
        # Kiểm tra tối đa 5 camera
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Dùng CAP_DSHOW cho Windows để nhanh hơn
            if cap.isOpened():
                # Thử đọc frame để xác nhận camera thực sự hoạt động
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Chỉ thêm vào danh sách nếu đọc được frame thực tế
                    backend_name = cap.getBackendName()
                    camera_name = f"Camera {i}"
                    if backend_name:
                        camera_name = f"Camera {i} ({backend_name})"
                    available_cameras.append({"index": i, "name": camera_name})
                cap.release()
        
        # Nếu không tìm thấy camera nào, trả về danh sách rỗng
        if not available_cameras:
            available_cameras = [{"index": -1, "name": "Không tìm thấy camera"}]
        
        return available_cameras
    
    cameras = get_available_cameras()
    
    # =================== MODEL NHẬN DIỆN SINH TRẮC HỌC ===================
    # Global model instance
    current_face_model = None
    
    biometric_models = ["ArcFace (v2.1)", "FaceNet (v1.0)", "DeepFace (v1.5)"]
    
    def on_model_select(e):
        """Callback khi admin chọn model"""
        nonlocal current_face_model
        
        model_name = e.control.value
        print(f"\n{'='*70}")
        print(f"🔄 [MODEL SELECT] Admin đang chọn: {model_name}")
        print(f"{'='*70}")
        
        # Lấy config từ UI và thêm model_path từ loaded_config
        face_config = loaded_config.get("face_recognition", {})
        config = {
            'confidence_threshold': float(bio_threshold.value),
            'min_face_size': int(bio_min_face_size.value),
            'cosine_threshold': float(bio_cosine_threshold.value),
            'model_path': face_config.get('model_path', 'yolov8n.pt')
        }
        
        print(f"📋 [CONFIG] Using model_path: {config['model_path']}")
        
        try:
            if "ArcFace" in model_name:
                from src.BUS.ai_core.login_user.Arc_face import ArcFaceModel
                current_face_model = ArcFaceModel(config)
                print(f"✅ [SUCCESS] Loaded ArcFace model với config:")
                print(f"   ├─ Model Path: {config['model_path']}")
                print(f"   ├─ Confidence: {config['confidence_threshold']}")
                print(f"   ├─ Min Face Size: {config['min_face_size']}px")
                print(f"   └─ Cosine Threshold: {config['cosine_threshold']}")
                
            elif "FaceNet" in model_name:
                print(f"⚠️  [WARNING] FaceNet chưa được triển khai")
                print(f"   Thành viên nhóm sẽ tạo src/BUS/ai_core/FaceNet.py")
                
            elif "DeepFace" in model_name:
                print(f"⚠️  [WARNING] DeepFace chưa được triển khai")
                print(f"   Thành viên nhóm sẽ tạo src/BUS/ai_core/DeepFace.py")
                
        except Exception as ex:
            print(f"❌ [ERROR] Không thể load model: {ex}")
            import traceback
            traceback.print_exc()
            current_face_model = None
    
    selected_biometric = ft.Dropdown(
        label="Chọn Model Sinh Trắc Học",
        width=300,
        options=[ft.dropdown.Option(m) for m in biometric_models],
        value=biometric_models[0],
        on_change=on_model_select,
        **dropdown_style,
    )
    
    bio_file_path = ft.Text("Chưa chọn file", size=12, color=TEXT_SECONDARY, italic=True)
    
    def pick_bio_model(e: ft.FilePickerResultEvent):
        print(f"🔵 [DEBUG] Bio file picker called")
        if e.files:
            print(f"✅ [SUCCESS] Selected file: {e.files[0].path}")
            bio_file_path.value = e.files[0].path
            bio_file_path.italic = False
            bio_file_path.color = PRIMARY
            bio_file_path.update()
        else:
            print(f"⚠️  [WARNING] No file selected")
    
    bio_file_picker = ft.FilePicker(on_result=pick_bio_model)
    print(f"🔵 [DEBUG] Adding bio_file_picker to page.overlay")
    page.overlay.append(bio_file_picker)
    page.update()  # CRITICAL: Update page to register the file picker
    print(f"✅ [SUCCESS] bio_file_picker added and page updated")
    
    # Load config from model_config.json - USE ABSOLUTE PATH FOR CONSISTENCY
    # quan_li_model_pt.py path: src/GUI/admin/control/page/quan_li_model_pt.py
    # Need to go up 6 levels to reach giam_sat_lai_xe
    current_file = os.path.abspath(__file__)  # Full path to quan_li_model_pt.py
    # count: page -> control -> admin -> GUI -> src -> giam_sat_lai_xe
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))))
    config_path = os.path.join(project_root, "src", "GUI", "data", "model_config.json")
    print(f"📂 [CONFIG_PATH] Loading from: {config_path}")
    
    loaded_config = {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
            face_config = loaded_config.get("face_recognition", {})
            print(f"✅ [CONFIG] Loaded model_config.json")
            print(f"   ├─ Confidence: {face_config.get('confidence_threshold', 0.75)}")
            print(f"   ├─ Min Face Size: {face_config.get('min_face_size', 40)}")
            print(f"   └─ Cosine Threshold: {face_config.get('cosine_threshold', 0.75)}")
    except Exception as e:
        print(f"⚠️  [CONFIG] Could not load config: {e}, using defaults")
        loaded_config = {
            "face_recognition": {
                "confidence_threshold": 0.75,
                "min_face_size": 40,
                "cosine_threshold": 0.75
            }
        }
    
    face_config = loaded_config.get("face_recognition", {})
    default_confidence = face_config.get('confidence_threshold', 0.75)
    default_min_face = face_config.get('min_face_size', 40)
    default_cosine = face_config.get('cosine_threshold', 0.75)
    
    # Cập nhật dropdown biometric theo config đã load
    _saved_bio_model_name = face_config.get('model_name', biometric_models[0])
    if _saved_bio_model_name in biometric_models:
        selected_biometric.value = _saved_bio_model_name
    
    bio_threshold = ft.Text(f"{default_confidence:.2f}", weight="bold", color=PRIMARY)
    bio_min_face_size = ft.Text(f"{default_min_face}", weight="bold", color=PRIMARY)
    bio_cosine_threshold = ft.Text(f"{default_cosine:.2f}", weight="bold", color=PRIMARY)
    
    def update_bio_threshold(e):
        bio_threshold.value = f"{e.control.value:.2f}"
        bio_threshold.update()
        if current_face_model:
            current_face_model.confidence_threshold = e.control.value
            print(f"🔄 [CONFIG UPDATE] Confidence threshold: {e.control.value:.2f}")
    
    def update_bio_min_face(e):
        bio_min_face_size.value = f"{int(e.control.value)}"
        bio_min_face_size.update()
        if current_face_model:
            current_face_model.min_face_size = int(e.control.value)
            print(f"🔄 [CONFIG UPDATE] Min face size: {int(e.control.value)}px")
    
    def update_bio_cosine_threshold(e):
        bio_cosine_threshold.value = f"{e.control.value:.2f}"
        bio_cosine_threshold.update()
        if current_face_model:
            current_face_model.cosine_threshold = e.control.value
            print(f"🔄 [CONFIG UPDATE] Cosine threshold: {e.control.value:.2f}")
    
    def save_config(e):
        """Lưu cấu hình hiện tại vào model_config.json"""
        try:
            # Đọc config hiện tại
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # Giữ lại path cũ nếu không chọn file mới
            old_bio_path = config_data.get("face_recognition", {}).get("model_path", "")
            effective_bio_path = bio_file_path.value if bio_file_path.value != "Chưa chọn file" else old_bio_path
            
            # Cập nhật face_recognition settings (bao gồm file path)
            config_data["face_recognition"] = {
                "model_name": selected_biometric.value,
                "model_path": effective_bio_path,
                "confidence_threshold": float(bio_threshold.value),
                "min_face_size": int(bio_min_face_size.value),
                "cosine_threshold": float(bio_cosine_threshold.value)
            }
            
            # Ghi lại file
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ [SAVE] Biometric configuration saved to model_config.json")
            print(f"   ├─ Model: {selected_biometric.value}")
            print(f"   ├─ Model Path: {bio_file_path.value}")
            print(f"   ├─ Confidence: {bio_threshold.value}")
            print(f"   ├─ Min Face Size: {bio_min_face_size.value}")
            print(f"   └─ Cosine Threshold: {bio_cosine_threshold.value}")
            
            # Show success message
            page.open(ft.SnackBar(
                content=ft.Text("✅ Đã lưu cấu hình sinh trắc học!"),
                bgcolor=ft.Colors.GREEN_700
            ))
            
        except Exception as ex:
            print(f"❌ [SAVE ERROR] {ex}")
            import traceback
            traceback.print_exc()
            page.open(ft.SnackBar(
                content=ft.Text(f"❌ Lỗi lưu cấu hình: {ex}"),
                bgcolor=ft.Colors.RED_700
            ))
    
    def test_biometric_model(e):
        """Test model sinh trắc học và log ra terminal"""
        print(f"\n{'='*70}")
        print(f"🧪 [TEST] Starting Biometric Model Test")
        print(f"{'='*70}")
        
        if not current_face_model:
            print(f"❌ [TEST ERROR] No model loaded! Please select a model first.")
            page.open(ft.SnackBar(
                content=ft.Text("❌ Chưa load model! Hãy chọn model trước."),
                bgcolor=ft.Colors.RED_700
            ))
            return
        
        print(f"📋 [TEST] Model Configuration:")
        print(f"   ├─ Model Name: {selected_biometric.value}")
        print(f"   ├─ Model Path: {bio_file_path.value}")
        print(f"   ├─ Confidence Threshold: {bio_threshold.value}")
        print(f"   ├─ Min Face Size: {bio_min_face_size.value}px")
        print(f"   └─ Cosine Threshold: {bio_cosine_threshold.value}")
        
        print(f"\n✅ [TEST] Model is loaded and ready")
        print(f"   Model Type: {type(current_face_model).__name__}")
        
        # Show success
        page.open(ft.SnackBar(
            content=ft.Text("✅ Model test completed! Check terminal for details."),
            bgcolor=ft.Colors.GREEN_700
        ))
        
        print(f"{'='*70}\n")
    
    biometric_config_card = glass_card(
        ft.Column([
            section_title("Model Nhận Diện Sinh Trắc Học", ft.Icons.LOCK, SECONDARY),
            ft.Divider(color=BORDER),
            selected_biometric,
            ft.Container(height=10),
            elevated_button(
                "Browse File (.pt)",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: bio_file_picker.pick_files(
                    allowed_extensions=["pt"],
                    dialog_title="Chọn Model Sinh Trắc Học (.pt)"
                ),
                kind="secondary",
            ),
            ft.Container(height=5),
            bio_file_path,
            ft.Container(height=10),
            ft.Text("Tham Số Model:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Row([
                ft.Text("Ngưỡng Độ Tin Cậy: ", color=TEXT_SECONDARY), bio_threshold
            ]),
            ft.Slider(min=0.3, max=1.0, divisions=70, value=default_confidence, on_change=update_bio_threshold),
            
            ft.Row([
                ft.Text("Kích Thước Khuôn Mặt Tối Thiểu (px): ", color=TEXT_SECONDARY), bio_min_face_size
            ]),
            ft.Slider(min=20, max=100, divisions=80, value=default_min_face, on_change=update_bio_min_face),
            
            ft.Row([
                ft.Text("Ngưỡng Cosine Similarity: ", color=TEXT_SECONDARY), bio_cosine_threshold
            ]),
            ft.Slider(min=0.2, max=1.0, divisions=80, value=default_cosine, on_change=update_bio_cosine_threshold),
            
            ft.Container(height=10),
            ft.Row([
                elevated_button("Lưu Cấu Hình", icon=ft.Icons.SAVE, kind="secondary", on_click=save_config),
                elevated_button("Test Model", icon=ft.Icons.PLAY_ARROW, kind="primary", on_click=test_biometric_model)
            ])
        ]),
        bgcolor=SURFACE_STRONG,
    )

    # =================== MODEL NHẬN DIỆN NGỦ GẬT ===================
    drowsy_config = loaded_config.get("drowsiness_detection", {})
    _saved_drowsy_model_path = drowsy_config.get("model_path", "")
    _default_drowsy_conf = drowsy_config.get('confidence_threshold', 0.50)
    _default_drowsy_iou = drowsy_config.get('iou_threshold', 0.45)

    # Hiển thị model đang được lưu (hoặc cảnh báo chưa chọn)
    _saved_path_display = _saved_drowsy_model_path if _saved_drowsy_model_path else "⚠️ Chưa chọn model"
    _saved_path_color = PRIMARY if _saved_drowsy_model_path else DANGER
    saved_drowsy_label = ft.Text(
        _saved_path_display, size=12, italic=not bool(_saved_drowsy_model_path),
        color=_saved_path_color, overflow=ft.TextOverflow.ELLIPSIS
    )

    drowsy_file_path = ft.Text("Chưa chọn file mới", size=12, color=TEXT_SECONDARY, italic=True)
    
    def pick_drowsy_model(e: ft.FilePickerResultEvent):
        print(f"🟠 [DEBUG] Drowsy file picker called")
        if e.files:
            print(f"✅ [SUCCESS] Selected file: {e.files[0].path}")
            drowsy_file_path.value = e.files[0].path
            drowsy_file_path.italic = False
            drowsy_file_path.color = PRIMARY
            drowsy_file_path.update()
        else:
            print(f"⚠️  [WARNING] No file selected")
    drowsy_file_picker = ft.FilePicker(on_result=pick_drowsy_model)
    print(f"🟠 [DEBUG] Adding drowsy_file_picker to page.overlay")
    page.overlay.append(drowsy_file_picker)
    page.update()  # CRITICAL: Update page to register the file picker
    print(f"✅ [SUCCESS] drowsy_file_picker added and page updated")
    
    drowsy_conf = ft.Text(f"{_default_drowsy_conf:.2f}", weight="bold", color="#FFC56D")
    drowsy_iou = ft.Text(f"{_default_drowsy_iou:.2f}", weight="bold", color="#FFC56D")
    
    def update_drowsy_conf(e):
        drowsy_conf.value = f"{e.control.value:.2f}"
        drowsy_conf.update()
    
    def update_drowsy_iou(e):
        drowsy_iou.value = f"{e.control.value:.2f}"
        drowsy_iou.update()
    
    def save_drowsy_config(e):
        """Lưu cấu hình ngủ gật vào model_config.json"""
        try:
            # Đọc config hiện tại
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # Giữ lại path cũ nếu không chọn file mới
            old_drowsy_path = config_data.get("drowsiness_detection", {}).get("model_path", "")
            new_path = drowsy_file_path.value
            effective_drowsy_path = new_path if (new_path and new_path != "Chưa chọn file mới") else old_drowsy_path
            
            # Cập nhật drowsiness_detection settings
            config_data["drowsiness_detection"] = {
                "model_path": effective_drowsy_path,
                "confidence_threshold": float(drowsy_conf.value),
                "iou_threshold": float(drowsy_iou.value)
            }
            
            # Ghi lại file
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Cập nhật label hiển thị
            if effective_drowsy_path:
                saved_drowsy_label.value = effective_drowsy_path
                saved_drowsy_label.color = PRIMARY
                saved_drowsy_label.italic = False
            else:
                saved_drowsy_label.value = "⚠️ Chưa chọn model"
                saved_drowsy_label.color = DANGER
                saved_drowsy_label.italic = True
            saved_drowsy_label.update()

            print(f"✅ [SAVE] Drowsiness detection configuration saved to model_config.json")
            print(f"   ├─ Model Path: {effective_drowsy_path}")
            print(f"   ├─ Confidence: {drowsy_conf.value}")
            print(f"   └─ IoU Threshold: {drowsy_iou.value}")
            
            # Show success message
            page.open(ft.SnackBar(
                content=ft.Text("✅ Đã lưu cấu hình ngủ gật!"),
                bgcolor=ft.Colors.ORANGE_700
            ))
            
        except Exception as ex:
            print(f"❌ [SAVE ERROR] {ex}")
            import traceback
            traceback.print_exc()
            page.open(ft.SnackBar(
                content=ft.Text(f"❌ Lỗi lưu cấu hình: {ex}"),
                bgcolor=ft.Colors.RED_700
            ))
    
    def test_drowsy_model(e):
        """Test model ngủ gật và log ra terminal"""
        print(f"\n{'='*70}")
        print(f"😴 [TEST] Starting Drowsiness Detection Model Test")
        print(f"{'='*70}")
        
        print(f"📋 [TEST] Model Configuration:")
        print(f"   ├─ Model Path: {drowsy_file_path.value}")
        print(f"   ├─ Confidence Threshold: {drowsy_conf.value}")
        print(f"   └─ IoU Threshold: {drowsy_iou.value}")
        
        if drowsy_file_path.value == "Chưa chọn file mới":
            print(f"\n⚠️  [TEST WARNING] No model file selected")
        else:
            print(f"\n✅ [TEST] Model configuration logged successfully")
        
        # Show success
        page.open(ft.SnackBar(
            content=ft.Text("✅ Model test completed! Check terminal for details."),
            bgcolor=ft.Colors.ORANGE_700
        ))
        
        print(f"{'='*70}\n")
    
    drowsiness_config_card = glass_card(
        ft.Column([
            section_title("Model Nhận Diện Ngủ Gật", ft.Icons.NIGHTLIGHT_ROUND, "#FFC56D"),
            ft.Divider(color=BORDER),
            ft.Text("Model hiện tại:", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            saved_drowsy_label,
            ft.Container(height=10),
            elevated_button(
                "Browse File (.pt)",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: drowsy_file_picker.pick_files(
                    allowed_extensions=["pt"],
                    dialog_title="Chọn Model Ngủ Gật (.pt)"
                ),
                kind="warning",
            ),
            ft.Container(height=5),
            drowsy_file_path,
            ft.Container(height=10),
            ft.Text("Tham Số Model:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Row([
                ft.Text("Ngưỡng Tin Cậy (Confidence): ", color=TEXT_SECONDARY), drowsy_conf
            ]),
            ft.Slider(min=0, max=1, divisions=100, value=_default_drowsy_conf, on_change=update_drowsy_conf),
            
            ft.Row([
                ft.Text("Ngưỡng IoU (NMS): ", color=TEXT_SECONDARY), drowsy_iou
            ]),
            ft.Slider(min=0, max=1, divisions=100, value=_default_drowsy_iou, on_change=update_drowsy_iou),
            
            ft.Container(height=10),
            ft.Row([
                elevated_button("Lưu Cấu Hình", icon=ft.Icons.SAVE, kind="warning", on_click=save_drowsy_config),
                elevated_button("Test Model", icon=ft.Icons.PLAY_ARROW, kind="primary", on_click=test_drowsy_model)
            ])
        ]),
        bgcolor=SURFACE_STRONG,
    )
    
    # =================== CẤU HÌNH CAMERA ===================
    selected_camera_index = ft.Ref[ft.Dropdown]()
    selected_camera_dropdown = ft.Dropdown(
        ref=selected_camera_index,
        label="Chọn Camera",
        width=300,
        options=[ft.dropdown.Option(key=str(cam["index"]), text=cam["name"]) for cam in cameras],
        value=str(loaded_config.get("camera", {}).get("default_index", cameras[0]["index"] if cameras else 0)),
        **dropdown_style,
    )
    
    camera_status = ft.Text("Chưa test", size=12, color=TEXT_SECONDARY, italic=True)
    
    # Hàm log ra terminal
    def add_log(message, log_type="info"):
        """In log ra terminal thay vì hiển thị trong UI"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Chọn prefix theo loại log
        if log_type == "success":
            prefix = "✅ [SUCCESS]"
        elif log_type == "error":
            prefix = "❌ [ERROR]"
        elif log_type == "warning":
            prefix = "⚠️  [WARNING]"
        else:  # info
            prefix = "ℹ️  [INFO]"
        
        print(f"{prefix} [{timestamp}] {message}")
    
    
    is_testing = False
    test_thread = None
    
    def test_camera(e):
        nonlocal is_testing, test_thread
        
        camera_idx = int(selected_camera_dropdown.value)
        
        # Kiểm tra nếu không có camera
        if camera_idx == -1:
            camera_status.value = "❌ Không có camera nào được phát hiện"
            camera_status.color = ft.Colors.RED
            camera_status.italic = False
            add_log("Không tìm thấy camera nào trong hệ thống", "error")
            add_log("Vui lòng kết nối camera và nhấn 'Refresh Cameras'", "warning")
            
            camera_status.update()
            return
        
        camera_status.value = f"🔄 Đang test Camera {camera_idx} (bật 1s để kiểm tra LED)..."
        camera_status.color = ft.Colors.ORANGE
        camera_status.update()
        add_log(f"Bắt đầu test Camera {camera_idx}...", "info")
        add_log(f"💡 Hãy quan sát LED trên camera để xác nhận camera hoạt động!", "warning")
        
        # Thử mở camera với DSHOW backend (Windows)
        cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)
        
        if cap.isOpened():
            add_log(f"✅ Mở camera {camera_idx} thành công", "success")
            
            # Để LED sáng 1 giây
            for i in range(3, 0, -1):
                camera_status.value = f"💡 LED sáng trong {i} giây..."
                camera_status.color = ft.Colors.BLUE
                camera_status.update()
                add_log(f"LED đang sáng: {i}s...", "info")
                time.sleep(1)
            
            # Thử đọc frame để xác nhận camera thực sự hoạt động
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # Camera thực sự hoạt động
                camera_status.value = f"✅ Camera {camera_idx} hoạt động tốt!"
                camera_status.color = ft.Colors.GREEN
                camera_status.italic = False
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                add_log(f"✅ Camera {camera_idx} hoạt động tốt!", "success")
                add_log(f"Resolution: {width}x{height}, FPS: {fps}", "success")
                add_log(f"💡 LED camera {camera_idx} sáng - Camera hoạt động bình thường!", "success")
            else:
                # Camera mở được nhưng không đọc được frame
                camera_status.value = f"❌ Camera {camera_idx} không phản hồi"
                camera_status.color = ft.Colors.RED
                
                add_log(f"Camera {camera_idx} mở được nhưng không đọc được frame", "error")
                add_log("Camera có thể đang được sử dụng bởi ứng dụng khác", "warning")
                add_log("🔧 Thử: Đóng các ứng dụng khác đang sử dụng camera và test lại", "warning")
            
            cap.release()
            add_log(f"Camera {camera_idx} đã đóng", "info")
        else:
            camera_status.value = f"❌ Không thể mở Camera {camera_idx}"
            camera_status.color = ft.Colors.RED
            
            add_log(f"Không thể mở Camera {camera_idx}", "error")
            add_log("Vui lòng kiểm tra kết nối camera và driver", "warning")
            add_log("🔧 Try: Cháy trực tiếp driver camera từ Device Manager", "warning")
        
        camera_status.update()
    
    camera_count_text = ft.Text(f"📊 Tổng số camera phát hiện: {len(cameras) if cameras and cameras[0]['index'] != -1 else 0}", size=13, color=TEXT_SECONDARY)
    
    def refresh_cameras(e):
        """Quét lại danh sách camera"""
        nonlocal cameras
        
        # Hiển thị loading
        camera_status.value = "🔄 Đang quét camera..."
        camera_status.color = ft.Colors.BLUE
        camera_status.update()
        add_log("Bắt đầu quét camera trong hệ thống...", "info")
        
        # Quét lại
        cameras = get_available_cameras()
        
        # Cập nhật dropdown
        selected_camera_dropdown.options = [ft.dropdown.Option(key=str(cam["index"]), text=cam["name"]) for cam in cameras]
        # Load saved camera index from config instead of always using first camera
        saved_camera_idx = loaded_config.get("camera", {}).get("default_index", cameras[0]["index"] if cameras else "-1")
        selected_camera_dropdown.value = str(saved_camera_idx)
        print(f"🎥 [CAMERA_INIT] Dropdown set to saved camera index: {saved_camera_idx}")
        selected_camera_dropdown.update()
        
        # Cập nhật số lượng
        camera_count_text.value = f"📊 Tổng số camera phát hiện: {len(cameras) if cameras and cameras[0]['index'] != -1 else 0}"
        camera_count_text.update()
        
        # Thông báo kết quả
        if cameras and cameras[0]["index"] != -1:
            camera_status.value = f"✅ Tìm thấy {len(cameras)} camera"
            camera_status.color = ft.Colors.GREEN
            add_log(f"Tìm thấy {len(cameras)} camera trong hệ thống", "success")
            for cam in cameras:
                add_log(f"  → {cam['name']}", "info")
        else:
            camera_status.value = "❌ Không tìm thấy camera nào"
            camera_status.color = ft.Colors.RED
            add_log("Không tìm thấy camera nào", "error")
        camera_status.update()
    
    def save_camera_config(e):
        """Lưu cấu hình camera vào model_config.json"""
        try:
            print(f"\n💾 [SAVE_CAMERA_CONFIG] Starting save process...")
            print(f"   📂 Config path: {config_path}")
            
            # Đọc config hiện tại
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # Cập nhật camera settings
            camera_idx = int(selected_camera_dropdown.value)
            if camera_idx == -1:
                raise ValueError("Không có camera nào được chọn. Vui lòng chọn camera hợp lệ.")
            
            config_data["camera"] = {
                "default_index": camera_idx,
                "resolution_width": 640,
                "resolution_height": 480,
                "fps": 30
            }
            
            # Ghi lại file
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ [SAVE] Camera configuration saved to model_config.json")
            print(f"   ├─ Camera Index: {camera_idx}")
            print(f"   ├─ Resolution: 640x480")
            print(f"   ├─ FPS: 30")
            print(f"   └─ File path: {config_path}\\n")
            
            # Show success message
            page.open(ft.SnackBar(
                content=ft.Text(f"✅ Đã lưu cấu hình camera (Index: {camera_idx})!"),
                bgcolor=ft.Colors.GREEN_700
            ))
            add_log(f"Cấu hình camera được lưu thành công (Index: {camera_idx})", "success")
            
        except ValueError as ve:
            print(f"❌ [SAVE ERROR] {ve}")
            page.open(ft.SnackBar(
                content=ft.Text(f"❌ Lỗi: {ve}"),
                bgcolor=ft.Colors.RED_700
            ))
            add_log(str(ve), "error")
        except Exception as ex:
            print(f"❌ [SAVE ERROR] {ex}")
            import traceback
            traceback.print_exc()
            page.open(ft.SnackBar(
                content=ft.Text(f"❌ Lỗi lưu cấu hình: {ex}"),
                bgcolor=ft.Colors.RED_700
            ))
            add_log(f"Lỗi lưu cấu hình: {ex}", "error")
    
    camera_config_card = glass_card(
        ft.Column([
            section_title("Cấu Hình Camera", ft.Icons.VIDEOCAM_OUTLINED, SECONDARY),
            ft.Divider(color=BORDER),
            selected_camera_dropdown,
            ft.Container(height=10),
            camera_count_text,
            ft.Container(height=10),
            ft.Row([
                elevated_button(
                    "Test Camera",
                    icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                    on_click=test_camera,
                    kind="secondary",
                ),
                elevated_button(
                    "Refresh Cameras", 
                    icon=ft.Icons.REFRESH, 
                    on_click=refresh_cameras, 
                    kind="surface",
                )
            ]),
            ft.Container(height=10),
            camera_status,
            ft.Container(height=5),
            ft.Text("* Log sẽ hiển thị trong terminal/console", size=11, color=TEXT_SECONDARY, italic=True),
            ft.Container(height=10),
            elevated_button("Lưu Cấu Hình", icon=ft.Icons.SAVE, kind="primary", on_click=save_camera_config)
        ]),
        bgcolor=SURFACE_STRONG,
    )
    
    # =================== KHO LƯU TRỮ MODEL ===================
    model_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Loại Model", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Tên File", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Version", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ngày Upload", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Accuracy", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Kích thước", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Trạng thái", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Hành động", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Icon(ft.Icons.FACE, color=SECONDARY)),
                ft.DataCell(ft.Text("facenet_model.h5", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("v1.0.0", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("20/01/2026", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("98.5%", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("25 MB", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Container(content=ft.Text("Active", color="white", size=10), bgcolor="blue", padding=5, border_radius=5)),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Tải xuống"),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Cấu hình"),
                ])),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Icon(ft.Icons.REMOVE_RED_EYE, color="#FFC56D")),
                ft.DataCell(ft.Text("yolov8n_drowsy.pt", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("v1.0.0", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("18/01/2026", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("92.5%", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("12 MB", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Container(content=ft.Text("Active", color="white", size=10), bgcolor="orange", padding=5, border_radius=5)),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Tải xuống"),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Cấu hình"),
                ])),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Icon(ft.Icons.REMOVE_RED_EYE, color="#FFC56D")),
                ft.DataCell(ft.Text("yolov11_drowsy.pt", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("v2.0.0 (Beta)", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("25/01/2026", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("94.1%", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("15 MB", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text("Backup", color=TEXT_SECONDARY)),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.UPLOAD, tooltip="Kích hoạt", icon_color="green"),
                    ft.IconButton(ft.Icons.DELETE, icon_color="red", tooltip="Xóa"),
                ])),
            ]),
        ],
        border=ft.border.all(1, BORDER),
        border_radius=10,
        vertical_lines=ft.border.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        heading_row_color=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
    )

    list_card = glass_card(
        ft.Column([
            ft.Row([
                section_title("Kho Lưu Trữ Model", ft.Icons.INVENTORY_2_OUTLINED, PRIMARY),
                ft.Row([
                    elevated_button("Upload Model Sinh Trắc", icon=ft.Icons.UPLOAD_FILE, kind="secondary"),
                    elevated_button("Upload Model Ngủ Gật", icon=ft.Icons.UPLOAD_FILE, kind="warning"),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color=BORDER),
            ft.Container(content=model_table, expand=True, padding=0)
        ]),
        expand=True,
        bgcolor=SURFACE_STRONG,
    )

    return ft.Column([
        ft.Column([
            ft.Text(page_title, size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Các khối model, camera và kho lưu trữ đã đổi sang kính mờ để nền ảnh chạy xuyên suốt tới viền nội dung.", size=13, color=TEXT_SECONDARY),
        ], spacing=4),
        ft.Container(height=10),
        # Hàng 1: 2 Model Cards (rộng hơn)
        ft.Row([
            ft.Container(content=biometric_config_card, expand=True),
            ft.Container(width=15),
            ft.Container(content=drowsiness_config_card, expand=True),
        ]),
        ft.Container(height=15),
        # Hàng 2: Camera Card ở bên trái
        ft.Row([
            ft.Container(content=camera_config_card, width=500),
        ]),
        ft.Container(height=20),
        # Phần kho lưu trữ
        ft.Container(content=list_card, expand=True)
    ], expand=True, scroll=ft.ScrollMode.AUTO)