import cv2
import base64
import threading
import time
import json
import os
import tempfile
import numpy as np
from pathlib import Path
from .sleep_detector import SleepDetector

# Sound playback
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except:
    HAS_PYGAME = False
    print("⚠️  [AUDIO] pygame not available, trying winsound")
    try:
        import winsound
        HAS_WINSOUND = True
    except:
        HAS_WINSOUND = False

class CameraManager:
    def __init__(self, update_callback, alert_callback=None, camera_index=0):
        """
        Quản lý camera cho giao diện người dùng chính (Driver Dashboard).
        :param update_callback: Hàm callback nhận chuỗi base64 image để cập nhật UI
        :param alert_callback: Hàm callback nhận thông báo cảnh báo (msg, img_path=None)
        :param camera_index: Chỉ số camera (0: default)
        """
        print(f"\n🎬 [CAMERA_MANAGER_INIT] Creating CameraManager with camera_index={camera_index}")
        self.camera_index = camera_index
        self.update_callback = update_callback
        self.alert_callback = alert_callback # Callback thông báo
        self.cap = None
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # AI Detection
        self.is_ai_active = False
        self.last_alert_time = 0 
        self.ALERT_COOLDOWN = 3.0 
        self.eye_closed_start_time = None 
        self.is_sleeping_alert_sent = False # Cờ đánh dấu đã gửi cảnh báo ngủ gật chưa
        self.eye_open_start_time = None # Thời điểm mở mắt lại
        self.is_sound_playing = False # Cờ phát âm thanh
        self.sound_path = os.path.abspath("src/GUI/data/sound/sound_drive/nhac-chuong-bao-thuc-may-thuc-day-cho-tao-tu-sena.mp3")
        # Realtime tuning
        self.target_fps = 20
        self.display_interval = 1.0 / max(1, self.target_fps)
        self.ai_interval = 0.2  # Run AI ~5 fps to keep UI realtime
        self._last_display_time = 0.0
        self._last_ai_time = 0.0
        self._last_detections = []
        self._last_ai_result_time = 0.0
        self._consecutive_read_failures = 0
        self._max_read_failures = 25
        self.output_width = 960
        self.output_height = 540
        self.jpeg_quality = 82
        self.enable_sharpen = True
        self._sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        
        # Đọc model path và thresholds từ model_config.json
        self.conf_threshold = 0.15  # default
        self.iou_threshold = 0.45   # default
        _model_path = ""
        try:
            _curr = os.path.abspath(__file__)
            # laucher_user -> ai_core -> BUS -> src -> project_root
            _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_curr)))))
            _cfg_path = os.path.join(_root, "src", "GUI", "data", "model_config.json")
            with open(_cfg_path, "r", encoding="utf-8") as _f:
                _cfg = json.load(_f)
            _dcfg = _cfg.get("drowsiness_detection", {})
            _model_path = _dcfg.get("model_path", "")
            self.conf_threshold = _dcfg.get("confidence_threshold", 0.15)
            self.iou_threshold = _dcfg.get("iou_threshold", 0.45)
            print(f"✅ [CAMERA_MANAGER] Config: model={os.path.basename(_model_path) if _model_path else 'chưa chọn'}, conf={self.conf_threshold}, iou={self.iou_threshold}")
        except Exception as _e:
            print(f"⚠️ [CAMERA_MANAGER] Không đọc được model_config.json: {_e}")
            _model_path = ""

        # Ngưỡng cảnh báo riêng để giảm false-positive (cao hơn ngưỡng hiển thị bbox).
        try:
            self.alert_conf_threshold = max(0.45, float(self.conf_threshold))
        except Exception:
            self.alert_conf_threshold = 0.45

        if _model_path:
            # If the path is absolute, use it directly. Otherwise, join with root.
            if not os.path.isabs(_model_path):
                _model_path = os.path.join(_root, _model_path)

        if _model_path and os.path.exists(_model_path):
            try:
                self.sleep_detector = SleepDetector(_model_path)
            except Exception as e:
                print(f"❌ [CAMERA_MANAGER] Lỗi init SleepDetector: {e}")
                self.sleep_detector = None
        else:
            if _model_path:
                print(f"⚠️ [CAMERA_MANAGER] File model không tồn tại: {_model_path}")
            else:
                print(f"⚠️ [CAMERA_MANAGER] Chưa cấu hình model ngủ gật. Vào Admin > Quản lý Model để thêm.")
            self.sleep_detector = None

    def start(self):
        """Khởi động luồng đọc camera"""
        if self.is_running:
            return
        
        try:
            print(f"\n▶️  [CAMERA_MANAGER_START] Attempting to open camera with index: {self.camera_index}")
            self.cap = self._open_capture()
            if not self.cap.isOpened():
                print(f"❌ [CAMERA] FAILED: Không thể mở camera {self.camera_index}")
                print(f"   └─ Kiểm tra xem camera {self.camera_index} có tồn tại không?")
                return
            else:
                print(f"✅ [CAMERA] SUCCESS: Mở camera {self.camera_index} thành công!\n")

            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            print("✅ [CAMERA] Đã khởi động camera dashboard")
        except Exception as e:
            print(f"❌ [CAMERA] Lỗi khởi động: {e}")

    def stop(self):
        """Dừng camera và giải phóng tài nguyên"""
        self.is_running = False
        self.stop_alert_sound()  # Tắt âm thanh khi dừng camera
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        with self.lock:
            if self.cap:
                self.cap.release()
                self.cap = None
        print("🛑 [CAMERA] Đã dừng camera dashboard")

    def _open_capture(self):
        # Use CAP_DSHOW for Windows to properly open camera by index.
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        try:
            # Prefer MJPG to reduce USB bandwidth pressure and avoid random freeze on some webcams.
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        except Exception:
            pass
        try:
            # Capture at native 16:9 to improve clarity. Rendering step keeps aspect ratio.
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        return cap

    def _reopen_capture(self):
        with self.lock:
            try:
                if self.cap:
                    self.cap.release()
            except Exception:
                pass
            self.cap = self._open_capture()
            opened = bool(self.cap and self.cap.isOpened())
        if opened:
            self._consecutive_read_failures = 0
            print("🔁 [CAMERA] Đã tự động mở lại camera sau khi mất frame.")
        else:
            print("❌ [CAMERA] Tự động mở lại camera thất bại.")
        return opened

    def toggle_ai(self, active: bool):
        """Bật/Tắt chế độ nhận diện buồn ngủ"""
        self.is_ai_active = active
        status = "BẬT" if active else "TẮT"
        print(f"🤖 [AI CORE] Chế độ giám sát: {status}")
    
    def set_sound_path(self, path: str):
        """Cập nhật đường dẫn nhạc chuông cảnh báo"""
        if path and os.path.exists(path):
            self.sound_path = path
            print(f"🎵 [AUDIO] Đã cập nhật nhạc chuông: {os.path.basename(path)}")
            # Nếu đang phát thì reload
            if self.is_sound_playing:
                try:
                    if HAS_PYGAME:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(self.sound_path)
                        pygame.mixer.music.play(-1)
                except Exception as e:
                    print(f"❌ [AUDIO] Lỗi reload nhạc: {e}")
        else:
            print(f"⚠️ [AUDIO] File nhạc không tồn tại: {path}")
    
    def play_alert_sound(self):
        """Phát âm thanh cảnh báo"""
        if self.is_sound_playing or not os.path.exists(self.sound_path):
            return
        
        try:
            self.is_sound_playing = True
            if HAS_PYGAME:
                pygame.mixer.music.load(self.sound_path)
                pygame.mixer.music.play(-1)  # Loop forever
                print(f"🔊 [AUDIO] Phát âm thanh từ {self.sound_path}")
            elif HAS_WINSOUND:
                import winsound
                winsound.PlaySound(self.sound_path, winsound.SND_ASYNC | winsound.SND_LOOP)
                print(f"🔊 [AUDIO] Phát âm thanh (winsound) từ {self.sound_path}")
        except Exception as e:
            print(f"❌ [AUDIO] Lỗi phát âm: {e}")
            self.is_sound_playing = False
    
    def stop_alert_sound(self):
        """Tắt âm thanh cảnh báo"""
        if not self.is_sound_playing:
            return
        
        try:
            self.is_sound_playing = False
            if HAS_PYGAME:
                pygame.mixer.music.stop()
                print(f"⏹️  [AUDIO] Đã tắt âm thanh")
            elif HAS_WINSOUND:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
                print(f"⏹️  [AUDIO] Đã tắt âm thanh (winsound)")
        except Exception as e:
            print(f"❌ [AUDIO] Lỗi tắt âm: {e}")

    def _capture_loop(self):
        """Vòng lặp đọc frame liên tục"""
        callback_error_count = 0
        MAX_CALLBACK_ERRORS = 10
        while self.is_running:
            try:
                now = time.time()
                with self.lock:
                    if not self.cap or not self.cap.isOpened():
                        break
                    ret, frame = self.cap.read()

                if not ret:
                    self._consecutive_read_failures += 1
                    if self._consecutive_read_failures >= self._max_read_failures:
                        if not self._reopen_capture():
                            time.sleep(0.25)
                    else:
                        time.sleep(0.03)
                    continue
                self._consecutive_read_failures = 0

                if frame is None or frame.size == 0:
                    time.sleep(0.1)
                    continue

                # Lật ảnh ngang (Mirror effect)
                frame = cv2.flip(frame, 1)
                display_frame = frame

                # AI Processing
                is_drowsy = False
                if self.is_ai_active and self.sleep_detector and (now - self._last_ai_time >= self.ai_interval):
                    try:
                        self._last_ai_time = now
                        frame, detections, _raw_is_drowsy = self.sleep_detector.predict(
                            frame, conf=self.conf_threshold, iou=self.iou_threshold
                        )
                        self._last_detections = detections or []
                        # Chỉ cảnh báo khi detection buồn ngủ có độ tin cậy đủ cao.
                        drowsy_hits = [
                            det for det in self._last_detections
                            if self._is_drowsy_detection(det) and float(det.get("conf", 0.0) or 0.0) >= self.alert_conf_threshold
                        ]
                        is_drowsy = len(drowsy_hits) > 0
                        self._last_ai_result_time = now
                        display_frame = frame
                    except Exception as ai_ex:
                        print(f"❌ [AI] Lỗi khi predict buồn ngủ: {ai_ex}")

                    # ================= ALERT LOGIC =================
                    if is_drowsy:
                        if self.eye_closed_start_time is None:
                            self.eye_closed_start_time = time.time()
                        duration = time.time() - self.eye_closed_start_time
                        if duration >= 1.5 and not self.is_sleeping_alert_sent:
                            self.is_sleeping_alert_sent = True
                            self.eye_open_start_time = None
                            img_path = None
                            try:
                                temp_dir = tempfile.gettempdir()
                                timestamp = int(time.time())
                                img_path = os.path.join(temp_dir, f"alert_drowsy_{timestamp}.jpg")
                                # Ảnh gửi Telegram phải giữ nguyên bbox để có bằng chứng rõ ràng.
                                evidence_frame = frame.copy()
                                if self._last_detections:
                                    evidence_frame = self._draw_detections(evidence_frame, self._last_detections)
                                cv2.imwrite(img_path, evidence_frame)
                            except Exception as e:
                                print(f"❌ [CAMERA] Failed to save evidence image: {e}")
                                img_path = None
                            if self.alert_callback:
                                self.alert_callback(f"⚠️ CẢNH BÁO: ĐANG NGỦ GẬT!", img_path=img_path)
                                print(f"⚠️ [ALERT] Start sleeping event detected. Evidence saved to {img_path}")
                            self.play_alert_sound()
                    else:
                        # Nếu chưa từng kích hoạt cảnh báo thì reset timer ngay,
                        # tránh cộng dồn thời gian "nhắm mắt" rời rạc gây báo động sai.
                        if not self.is_sleeping_alert_sent:
                            self.eye_closed_start_time = None
                            self.eye_open_start_time = None
                        else:
                            if self.eye_open_start_time is None:
                                self.eye_open_start_time = time.time()
                            eye_open_duration = time.time() - self.eye_open_start_time
                            if eye_open_duration >= 3.0:
                                if self.eye_closed_start_time:
                                    total_duration = time.time() - self.eye_closed_start_time
                                    msg = f"✅ Đã tỉnh giấc! Tổng thời gian ngủ: {total_duration:.1f}s"
                                    if self.alert_callback:
                                        self.alert_callback(msg, type="info")
                                    print(f"✅ [ALERT] End sleeping event. Total: {total_duration:.2f}s")
                                self.stop_alert_sound()
                                self.eye_closed_start_time = None
                                self.eye_open_start_time = None
                                self.is_sleeping_alert_sent = False
                    # ===============================================

                if not self.is_ai_active:
                    self._last_detections = []
                    self._last_ai_result_time = 0.0

                # Vẽ bbox liên tục trên mọi frame bằng cache kết quả AI gần nhất
                # để tránh hiện tượng nhấp nháy khi AI inference chạy theo chu kỳ.
                if self._last_detections and (now - self._last_ai_result_time <= max(0.5, self.ai_interval * 3)):
                    display_frame = self._draw_detections(display_frame, self._last_detections)

                if now - self._last_display_time < self.display_interval:
                    time.sleep(0.001)
                    continue
                self._last_display_time = now

                try:
                    display_frame = self._prepare_display_frame(display_frame)
                except Exception:
                    pass

                try:
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(self.jpeg_quality)]
                    _, buffer = cv2.imencode('.jpg', display_frame, encode_param)
                    b64_img = base64.b64encode(buffer).decode('utf-8')
                except Exception as e:
                    print(f"⚠️ [CAMERA] Lỗi encode frame: {e}")
                    continue

                try:
                    if self.update_callback:
                        self.update_callback(b64_img)
                    callback_error_count = 0
                except Exception as e:
                    callback_error_count += 1
                    print(f"⚠️ [CAMERA] Lỗi update_callback (lần {callback_error_count}): {e}")
                    if callback_error_count >= MAX_CALLBACK_ERRORS:
                        print(f"🛑 [CAMERA] callback lỗi quá nhiều, tự động reset camera!")
                        self.stop()
                        time.sleep(1)
                        self.start()
                        return

                time.sleep(0.01)
            except Exception as loop_ex:
                print(f"❌ [CAMERA_LOOP] Lỗi không mong muốn: {loop_ex}")
                time.sleep(0.1)

    def _prepare_display_frame(self, frame):
        if frame is None:
            return frame
        target_w, target_h = int(self.output_width), int(self.output_height)
        h, w = frame.shape[:2]
        if h <= 0 or w <= 0 or target_w <= 0 or target_h <= 0:
            return frame

        # Keep aspect ratio to avoid stretch; letterbox/pillarbox if needed.
        scale = min(target_w / float(w), target_h / float(h))
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)

        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        x = (target_w - new_w) // 2
        y = (target_h - new_h) // 2
        canvas[y:y + new_h, x:x + new_w] = resized

        if self.enable_sharpen:
            try:
                canvas = cv2.filter2D(canvas, -1, self._sharpen_kernel)
            except Exception:
                pass
        return canvas

    def _is_drowsy_detection(self, det):
        if not isinstance(det, dict):
            return False
        name = str(det.get("name", "")).lower()
        return any(k in name for k in ("close", "closed", "sleep", "drowsy", "eye_close"))

    def _draw_detections(self, frame, detections):
        if frame is None or not detections:
            return frame
        try:
            for det in detections:
                bbox = det.get("bbox") if isinstance(det, dict) else None
                if not bbox:
                    continue
                # YOLO trả về [[x1, y1, x2, y2]]
                if isinstance(bbox, list) and bbox and isinstance(bbox[0], (list, tuple)):
                    coords = bbox[0]
                else:
                    coords = bbox
                if not isinstance(coords, (list, tuple)) or len(coords) < 4:
                    continue
                x1, y1, x2, y2 = [int(float(v)) for v in coords[:4]]
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = max(x1 + 1, x2)
                y2 = max(y1 + 1, y2)

                name = str(det.get("name", "object"))
                conf = float(det.get("conf", 0.0))
                label = f"{name} {conf:.2f}"
                is_drowsy_cls = self._is_drowsy_detection(det)
                color = (0, 0, 255) if is_drowsy_cls else (0, 220, 0)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                ty = max(16, y1 - 6)
                cv2.rectangle(frame, (x1, ty - th - 8), (x1 + tw + 8, ty), color, -1)
                cv2.putText(frame, label, (x1 + 4, ty - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        except Exception as draw_ex:
            print(f"⚠️ [CAMERA] Lỗi vẽ bbox: {draw_ex}")
        return frame
