
import cv2
import numpy as np
import os
import json
import base64
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from .base_face_model import BaseFaceModel

# Import InsightFace
try:
    from insightface.app import FaceAnalysis as _FaceAnalysis
    HAS_INSIGHTFACE = True
except ImportError:
    HAS_INSIGHTFACE = False
    print("⚠️ [IMPORT] insightface not found. Face recognition will use fallback!")

# Load Haar Cascade một lần duy nhất
_FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

def crop_face_from_image(img: np.ndarray, padding: float = 0.2) -> Optional[np.ndarray]:
    """
    Phát hiện và crop khuôn mặt từ ảnh.
    Nếu không tìm thấy mặt → trả về None.
    Sử dụng multiple attempts với parameters khác nhau.
    """
    # PREPROCESSING: Cải thiện contrast/brightness để detection tốt hơn
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) để tăng contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # ATTEMPT 1: Chặt (minNeighbors=3) - Để phát hiện các khuôn mặt rõ ràng
    faces = _FACE_CASCADE.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=3,
        minSize=(40, 40)
    )
    
    print(f"🔍 [CROP_DEBUG] ATTEMPT 1 (minNeighbors=3, minSize=40): Found {len(faces)} faces")
    
    # ATTEMPT 2: Nếu không tìm được, thử lỏng hơn (minNeighbors=2)
    if len(faces) == 0:
        print("⚠️ [CROP] minNeighbors=3 không phát hiện, thử minNeighbors=2...")
        faces = _FACE_CASCADE.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=2,
            minSize=(30, 30)
        )
        print(f"🔍 [CROP_DEBUG] ATTEMPT 2 (minNeighbors=2, minSize=30): Found {len(faces)} faces")
    
    # ATTEMPT 3: Vẫn không tìm được, thử rất lỏng (minNeighbors=1)
    if len(faces) == 0:
        print("⚠️ [CROP] minNeighbors=2 không phát hiện, thử minNeighbors=1...")
        faces = _FACE_CASCADE.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=1,
            minSize=(20, 20)
        )
        print(f"🔍 [CROP_DEBUG] ATTEMPT 3 (minNeighbors=1, minSize=20): Found {len(faces)} faces")
    
    # ATTEMPT 4: Cuối cùng, thử với scale factor nhỏ hơn
    if len(faces) == 0:
        print("⚠️ [CROP] Tất cả attempts thất bại, thử scale factor 1.02...")
        faces = _FACE_CASCADE.detectMultiScale(
            gray,
            scaleFactor=1.02,
            minNeighbors=1,
            minSize=(15, 15)
        )
        print(f"🔍 [CROP_DEBUG] ATTEMPT 4 (scaleFactor=1.02): Found {len(faces)} faces")
    
    if len(faces) == 0:
        print("⚠️ [CROP] Không phát hiện khuôn mặt trong ảnh sau 4 lần thử")
        print(f"   ├─ Input image shape: {img.shape}")
        print(f"   └─ Gray image stats: min={gray.min()}, max={gray.max()}, mean={gray.mean():.1f}")
        return None

    # Lấy khuôn mặt lớn nhất
    (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
    h_img, w_img = img.shape[:2]

    # IMPROVE: Consistent padding - không quá lớn để tránh background noise
    # Reduce padding từ 0.2 → 0.15 để focus hơn vào mặt
    padding = 0.15
    pad_x = int(w * padding)
    pad_y = int(h * padding)
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(w_img, x + w + pad_x)
    y2 = min(h_img, y + h + pad_y)

    face_crop = img[y1:y2, x1:x2]
    
    # IMPROVE: Resize to fixed size (128x128) để consistency
    # Nếu crop size khác nhau → embedding khác
    # Normalize size → embeddings consistent hơn
    face_crop_normalized = cv2.resize(face_crop, (128, 128))
    
    print(f"✅ [CROP] Đã crop khuôn mặt: ({x1},{y1})-({x2},{y2}), size={face_crop.shape}")
    print(f"   └─ Normalized to (128, 128)")
    return face_crop_normalized


class ArcFaceEmbedding:
    """Trích xuất embedding 512D bằng InsightFace API"""
    
    def __init__(self, model_name: str = 'buffalo_sc'):
        """Khởi tạo InsightFace model"""
        self.app = None
        self.use_insightface = False
        
        if HAS_INSIGHTFACE:
            try:
                # Không dùng allowed_modules=['recognition'] vì sẽ bỏ qua detection
                # → app.prepare(det_size=...) sẽ ném AttributeError (message rỗng)
                # → app.get() không tìm được embedding
                self.app = _FaceAnalysis(
                    name=model_name,
                    providers=['CPUExecutionProvider']
                )
                # det_size=(640,640) để detection hoạt động đúng
                self.app.prepare(ctx_id=0, det_size=(640, 640))
                self.use_insightface = True
                print(f"✅ [InsightFace] Model '{model_name}' loaded successfully")
            except Exception as e:
                print(f"⚠️ [InsightFace] Load failed: {type(e).__name__}: {e}, using fallback")
        else:
            print("⚠️ [InsightFace] Library not available, using fallback")

    def extract_embedding_simple(self, face_image: np.ndarray) -> np.ndarray:
        """
        Fallback: Extract discriminative embedding từ face image
        ENHANCED: Local patches + Texture + Multi-scale features
        """
        try:
            # Convert to grayscale
            if len(face_image.shape) == 3:
                gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_image
            
            # Ensure size
            gray = cv2.resize(gray, (128, 128))
            
            features = []
            
            # ========== FEATURE SET 1: MULTI-SCALE PYRAMIDS ==========
            # Scale pyramid: 32, 48, 64, 128 để capture multi-level info
            for size in [32, 48, 64, 128]:
                resized = cv2.resize(gray, (size, size))
                features.append(resized.flatten().astype(np.float32))
            
            # ========== FEATURE SET 2: HISTOGRAMS ==========
            for size in [32, 64, 128]:
                resized = cv2.resize(gray, (size, size))
                hist = cv2.calcHist([resized], [0], None, [64], [0, 256]).flatten().astype(np.float32)
                features.append(hist)
            
            # ========== FEATURE SET 3: EDGE MAPS ==========
            # Sobel edges (high discriminative power for facial features)
            for ksize in [3, 5]:
                sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=ksize)
                sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=ksize)
                sobel_mag = np.sqrt(sobel_x**2 + sobel_y**2 + 1e-6)
                sobel_resized = cv2.resize(sobel_mag, (32, 32)).flatten().astype(np.float32)
                features.append(sobel_resized)
            
            # ========== FEATURE SET 4: LOCAL BINARY PATTERNS (LBP-like) ==========
            # Simple LBP: compare each pixel with neighbors
            h, w = gray.shape
            lbp = np.zeros((h-2, w-2), dtype=np.uint8)
            for i in range(1, h-1):
                for j in range(1, w-1):
                    center = gray[i, j]
                    neighbors = [
                        gray[i-1, j-1], gray[i-1, j], gray[i-1, j+1],
                        gray[i, j-1],               gray[i, j+1],
                        gray[i+1, j-1], gray[i+1, j], gray[i+1, j+1]
                    ]
                    lbp_code = 0
                    for k, neighbor in enumerate(neighbors):
                        if neighbor >= center:
                            lbp_code |= (1 << k)
                    lbp[i-1, j-1] = lbp_code
            
            lbp_hist = cv2.calcHist([lbp], [0], None, [256], [0, 256]).flatten().astype(np.float32)
            features.append(lbp_hist)
            
            # ========== FEATURE SET 5: LAPLACIAN (curvature) ==========
            laplacian = cv2.Laplacian(gray, cv2.CV_32F)
            lap_resized = cv2.resize(laplacian, (32, 32)).flatten().astype(np.float32)
            features.append(lap_resized)
            
            # ========== FEATURE SET 6: LOCAL PATCHES ==========
            # Divide image into 4x4 grid and extract stats from each patch
            patch_size = 32  # 128/4 = 32
            patches = []
            for i in range(0, 128, patch_size):
                for j in range(0, 128, patch_size):
                    patch = gray[i:i+patch_size, j:j+patch_size]
                    patches.extend([
                        patch.mean(),
                        patch.std() + 1e-6,
                        np.percentile(patch, 25),
                        np.percentile(patch, 75)
                    ])
            features.append(np.array(patches, dtype=np.float32))
            
            # Combine all features
            embedding = np.concatenate(features)
            
            # Truncate/pad to exactly 512D
            if len(embedding) > 512:
                # Keep most diverse features (pyramid + edges + patches)
                embedding = embedding[:512]
            elif len(embedding) < 512:
                # Pad with mean value
                pad_size = 512 - len(embedding)
                pad_val = np.full(pad_size, gray.mean() / 255.0, dtype=np.float32)
                embedding = np.concatenate([embedding, pad_val])
            
            # L2 normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 1e-6:
                embedding = embedding / norm
            
            return embedding
            
        except Exception as e:
            print(f"❌ [SIMPLE] Enhanced embedding failed: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(512, dtype=np.float32)

    def _extract_from_full_image(self, img: np.ndarray) -> Optional[np.ndarray]:
        """Truyền ảnh GỐC (full frame) vào InsightFace để tự detect + extract embedding.
        Trả về embedding 512D đã normalize, hoặc None nếu không tìm thấy mặt."""
        if not (self.use_insightface and self.app is not None):
            return None
        try:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = self.app.get(img_rgb)
            if faces:
                emb = faces[0].embedding.astype(np.float32)
                norm = np.linalg.norm(emb)
                if norm > 1e-6:
                    emb = emb / norm
                return emb
            else:
                print("⚠️ [InsightFace] Không phát hiện mặt trong ảnh gốc, dùng fallback")
                return None
        except Exception as e:
            print(f"⚠️ [InsightFace] Inference failed: {type(e).__name__}: {e}, dùng fallback")
            return None

    def extract_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Trích xuất embedding 512D từ face crop (fallback path).
        Chỉ dùng khi _extract_from_full_image() đã thất bại."""
        return self.extract_embedding_simple(face_image)

    def compare_embeddings(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """So sánh Cosine Similarity"""
        if emb1 is None or emb2 is None: return 0.0
        dot_product = np.dot(emb1.flatten(), emb2.flatten())
        norm_a = np.linalg.norm(emb1)
        norm_b = np.linalg.norm(emb2)
        if norm_a < 1e-6 or norm_b < 1e-6: return 0.0
        return float(dot_product / (norm_a * norm_b))


class ArcFaceModel(BaseFaceModel):
    """Lớp bọc chính cho hệ thống - Kết hợp AI và quản lý dữ liệu JSON"""
    
    def __init__(self, config: Dict = None):
        if config is None:
            config = {
                'confidence_threshold': 0.55,
                'min_face_size': 30,
                'cosine_threshold': 0.55
            }
        super().__init__(config)
        _insightface_model_name = config.get('model_name', 'buffalo_sc') if config else 'buffalo_sc'
        # normalize legacy value
        if _insightface_model_name not in ('buffalo_sc', 'buffalo_l', 'buffalo_s'):
            _insightface_model_name = 'buffalo_sc'
        self.arcface = ArcFaceEmbedding(model_name=_insightface_model_name)
        
        # Load YOLO face detector từ config model_path nếu có
        self.yolo_detector = None
        _model_path = config.get('model_path', '') if config else ''
        if _model_path and os.path.exists(_model_path) and _model_path.endswith('.pt'):
            try:
                from ultralytics import YOLO
                self.yolo_detector = YOLO(_model_path)
                print(f"✅ [ArcFaceModel] YOLO face detector loaded: {os.path.basename(_model_path)}")
            except Exception as _e:
                print(f"⚠️ [ArcFaceModel] Không load được YOLO model: {_e}")
                self.yolo_detector = None

        print(f"🤖 [ArcFaceModel] AI Engine ready. Threshold: {self.cosine_threshold}")

    def _crop_face_yolo(self, img: np.ndarray) -> Optional[np.ndarray]:
        """Dùng YOLO để detect và crop khuôn mặt (thay thế Haar cascade)"""
        try:
            results = self.yolo_detector(img, verbose=False, conf=0.25)
            best_box = None
            best_area = 0
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    area = (x2 - x1) * (y2 - y1)
                    if area > best_area:
                        best_area = area
                        best_box = (x1, y1, x2, y2)
            if best_box:
                x1, y1, x2, y2 = best_box
                h_img, w_img = img.shape[:2]
                # Thêm padding nhỏ
                pad = int(min(x2-x1, y2-y1) * 0.1)
                x1, y1 = max(0, x1-pad), max(0, y1-pad)
                x2, y2 = min(w_img, x2+pad), min(h_img, y2+pad)
                face_crop = img[y1:y2, x1:x2]
                face_crop = cv2.resize(face_crop, (128, 128))
                print(f"✅ [YOLO_DETECT] Crop khuôn mặt: ({x1},{y1})-({x2},{y2})")
                return face_crop
            else:
                print("⚠️ [YOLO_DETECT] Không tìm thấy khuôn mặt")
                return None
        except Exception as e:
            print(f"❌ [YOLO_DETECT] Lỗi: {e}")
            return None

    def extract_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """Trích xuất embedding từ file ảnh.
        Ưu tiên InsightFace trên ảnh gốc, fallback sang YOLO crop + histogram."""
        if not os.path.exists(image_path):
            print(f"❌ [AI] File not found: {image_path}")
            return None
        
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ [AI] Cannot read image: {image_path}")
            return None
        
        # 1. Ưu tiên: InsightFace nhận ảnh GỐC (tự detect + embed)
        emb = self.arcface._extract_from_full_image(img)
        if emb is not None:
            return emb
        
        # 2. Fallback: YOLO crop → histogram embedding
        if self.yolo_detector is not None:
            face_img = self._crop_face_yolo(img)
        else:
            face_img = crop_face_from_image(img)
        if face_img is None:
            print("⚠️ [EXTRACT] Crop failed, dùng full frame")
            face_img = cv2.resize(img, (224, 224))
        return self.arcface.extract_embedding(face_img)

    def extract_embedding_from_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Trích xuất embedding trực tiếp từ frame camera.
        Ưu tiên InsightFace trên frame gốc, fallback sang Haar crop + histogram."""
        if frame is None or frame.size == 0:
            return None
        
        # 1. Ưu tiên: InsightFace nhận frame GỐC
        emb = self.arcface._extract_from_full_image(frame)
        if emb is not None:
            return emb
        
        # 2. Fallback: Haar crop → histogram embedding
        face_img = crop_face_from_image(frame)
        if face_img is None:
            print("❌ [AI] Không tìm thấy khuôn mặt trong frame")
            return None
        return self.arcface.extract_embedding(face_img)

    def register_face(self, image_path: str, user_data: Dict) -> bool:
        """
        Đăng ký khuôn mặt theo DB, sau đó đồng bộ lại accounts.json.
        """
        embedding = self.extract_embedding(image_path)
        if embedding is None:
            print(f"❌ [REGISTER] Không thể trích xuất embedding từ ảnh: {image_path}")
            return False

        try:
            emb_bytes = embedding.astype(np.float32).tobytes()
            emb_base64 = base64.b64encode(emb_bytes).decode('utf-8')
            username = user_data.get('username')
            from src.DAL import (
                cap_nhat_tai_xe,
                export_accounts_to_json,
                get_driver_account_from_db,
                them_tai_xe,
            )

            existing_user = get_driver_account_from_db(username)
            if existing_user:
                cap_nhat_tai_xe(
                    username,
                    name=user_data.get('name'),
                    password=user_data.get('password'),
                    phone=user_data.get('phone'),
                    face_data=emb_base64,
                    goi_dich_vu=user_data.get('goi_dich_vu', 'Free'),
                )
            else:
                them_tai_xe(
                    user_data.get('driver_id', ''),
                    username,
                    user_data.get('name', username),
                    user_data.get('password', ''),
                    user_data.get('phone'),
                    emb_base64,
                    user_data.get('goi_dich_vu', 'Free'),
                )

            export_accounts_to_json()
            
            print(f"✅ [REGISTER] Successfully registered face for {username}")
            return True

        except Exception as e:
            print(f"❌ [REGISTER] Error: {e}")
            return False

    def verify_face(self, image_path: str, username: str, password: str = "") -> Tuple[bool, float]:
        """
        Xác thực khuôn mặt với dữ liệu đã lưu trong DB.
        """
        current_embedding = self.extract_embedding(image_path)
        if current_embedding is None:
            print(f"❌ [VERIFY] Could not extract embedding from {image_path}")
            return False, 0.0
        
        try:
            from src.DAL import get_driver_account_from_db

            account = get_driver_account_from_db(username)
            emb_base64 = account.get('face_data') if account else None
            if not emb_base64:
                print(f"⚠️ [VERIFY] No face data found for user {username}")
                return False, 0.0

            emb_bytes = base64.b64decode(emb_base64)
            stored_embedding = np.frombuffer(emb_bytes, dtype=np.float32)

            similarity = self.arcface.compare_embeddings(current_embedding, stored_embedding)
            matched = similarity >= self.cosine_threshold
            
            status = "✅ MATCH" if matched else "❌ NO MATCH"
            print(f"    {status} | {username}: {similarity:.4f} (threshold: {self.cosine_threshold:.4f})")
            
            return matched, float(similarity)

        except Exception as e:
            print(f"❌ [VERIFY] Error: {e}")
            import traceback
            traceback.print_exc()
            return False, 0.0

    def verify_face_from_data(self, image_path: str, face_data_b64: str) -> Tuple[bool, float]:
        """So sánh khuôn mặt với embedding đã lưu (chuỗi base64, lấy từ DB hoặc JSON phẳng)."""
        current_embedding = self.extract_embedding(image_path)
        if current_embedding is None:
            return False, 0.0
        try:
            emb_bytes = base64.b64decode(face_data_b64)
            stored_embedding = np.frombuffer(emb_bytes, dtype=np.float32)
            similarity = self.arcface.compare_embeddings(current_embedding, stored_embedding)
            matched = similarity >= self.cosine_threshold
            status = "✅ MATCH" if matched else "❌ NO MATCH"
            print(f"    {status} | similarity: {similarity:.4f} (threshold: {self.cosine_threshold:.4f})")
            return matched, float(similarity)
        except Exception as e:
            print(f"❌ [VERIFY_DATA] Error: {e}")
            return False, 0.0
