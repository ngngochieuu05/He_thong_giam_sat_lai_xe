import cv2
import base64
import threading
import time
import os
import tempfile
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
        
        try:
            model_path = os.path.abspath("models/trained_modek_Run/best.pt")
            self.sleep_detector = SleepDetector(model_path)
        except Exception as e:
            print(f"Lỗi init SleepDetector: {e}")
            self.sleep_detector = None

    def start(self):
        """Khởi động luồng đọc camera"""
        if self.is_running:
            return
        
        try:
            print(f"\n▶️  [CAMERA_MANAGER_START] Attempting to open camera with index: {self.camera_index}")
            # Use CAP_DSHOW for Windows to properly open camera by index
            # Without this, cv2 may silently fallback to index 0 if index 1 not available
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
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
        while self.is_running:
            with self.lock:
                if not self.cap or not self.cap.isOpened():
                    break
                ret, frame = self.cap.read()

            if not ret:
                time.sleep(0.1)
                continue

            # Lật ảnh ngang (Mirror effect)
            frame = cv2.flip(frame, 1)

            # AI Processing
            is_drowsy = False
            if self.is_ai_active and self.sleep_detector:
                frame, detections, is_drowsy = self.sleep_detector.predict(frame)
                
                # ================= ALERT LOGIC =================
                if is_drowsy:
                    # Bắt đầu đếm thời gian
                    if self.eye_closed_start_time is None:
                        self.eye_closed_start_time = time.time()
                    
                    duration = time.time() - self.eye_closed_start_time
                    
                    # Nếu nhắm mắt >= 1.5s VÀ chưa báo động lần nào trong đợt này
                    if duration >= 1.5 and not self.is_sleeping_alert_sent:
                        self.is_sleeping_alert_sent = True # Đã báo, không spam nữa
                        self.eye_open_start_time = None  # Reset bộ đếm mở mắt
                        
                        # CAPTURE EVIDENCE IMAGE
                        img_path = None
                        try:
                            # Tạo tên file unique
                            temp_dir = tempfile.gettempdir()
                            timestamp = int(time.time())
                            img_path = os.path.join(temp_dir, f"alert_drowsy_{timestamp}.jpg")
                            
                            # Lưu ảnh frame hiện tại (đã có bbox)
                            cv2.imwrite(img_path, frame)
                        except Exception as e:
                            print(f"❌ [CAMERA] Failed to save evidence image: {e}")
                            img_path = None
                        
                        if self.alert_callback:
                            # Truyền thêm tham số img_path
                            self.alert_callback(f"⚠️ CẢNH BÁO: ĐANG NGỦ GẬT!", img_path=img_path)
                            print(f"⚠️ [ALERT] Start sleeping event detected. Evidence saved to {img_path}")
                        
                        # PHÁT ÂM THANH CẢNH BÁO
                        self.play_alert_sound()
                            
                else:
                    # Người dùng mở mắt lại
                    if self.is_sleeping_alert_sent:
                        # Bắt đầu đếm thời gian mở mắt
                        if self.eye_open_start_time is None:
                            self.eye_open_start_time = time.time()
                        
                        # Kiểm tra nếu mở mắt >= 3 giây thì tắt âm thanh
                        eye_open_duration = time.time() - self.eye_open_start_time
                        if eye_open_duration >= 3.0:
                            # Kết thúc đợt ngủ gật -> Tính tổng thời gian
                            if self.eye_closed_start_time:
                                total_duration = time.time() - self.eye_closed_start_time
                                msg = f"✅ Đã tỉnh giấc! Tổng thời gian ngủ: {total_duration:.1f}s"
                                if self.alert_callback:
                                    self.alert_callback(msg, type="info")
                                print(f"✅ [ALERT] End sleeping event. Total: {total_duration:.2f}s")
                            
                            # DỪNG ÂM THANH
                            self.stop_alert_sound()
                            
                            # Reset trạng thái
                            self.eye_closed_start_time = None
                            self.eye_open_start_time = None
                            self.is_sleeping_alert_sent = False
                # ===============================================

            try:
                # Encode sang JPEG -> Base64
                _, buffer = cv2.imencode('.jpg', frame)
                b64_img = base64.b64encode(buffer).decode('utf-8')
                
                # Gọi callback cập nhật UI
                if self.update_callback:
                    self.update_callback(b64_img)
            
            except Exception as e:
                msg = str(e)
                if "UI_CLOSED" in msg or "socket" in msg.lower() or "closed" in msg.lower():
                    # Stop loop silently if UI is closed
                    break
                print(f"⚠️ [CAMERA] Lỗi xử lý frame: {e}")
            
            # Giới hạn FPS (~30fps)
            time.sleep(0.03)
