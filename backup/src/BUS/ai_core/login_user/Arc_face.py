
import cv2
import numpy as np
import os
import json
import base64
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from .base_face_model import BaseFaceModel

# Import onnxruntime
try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False
    print("❌ [IMPORT] onnxruntime not found. Face recognition will be disabled!")

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
    """Trích xuất embedding 512D bằng ONNX Runtime (ArcFace ResNet50)"""
    
    def __init__(self):
        """Khởi tạo ONNX model"""
        models_dir = os.path.abspath("models/ai_assets")
        os.makedirs(models_dir, exist_ok=True)
        self.model_path = os.path.join(models_dir, "arcface_resnet50.onnx")
        
        self.session = None
        self.use_onnx = False
        
        if not os.path.exists(self.model_path):
            print(f"⚠️ [AI CORE] Model ONNX không tìm thấy tại: {self.model_path}")
        else:
            file_size = os.path.getsize(self.model_path)
            if file_size < 1000000:  # Model file should be > 1MB
                print(f"⚠️ [AI CORE] Model ONNX file size {file_size} bytes (< 1MB) - CORRUPT!")
        
        try:
            if HAS_ONNX and os.path.exists(self.model_path):
                file_size = os.path.getsize(self.model_path)
                if file_size > 1000000:  # Check if file is valid (> 1MB)
                    # Ưu tiên dùng CPU để ổn định nhất trên Windows
                    self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
                    self.use_onnx = True
                    print("✅ [ONNX] ArcFace model loaded successfully via ONNX Runtime")
                else:
                    print(f"❌ [ONNX] Model file corrupted (size={file_size}), using fallback")
        except Exception as e:
            print(f"❌ [ONNX] Error loading ONNX: {e}, fallback to simple embedding")

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
            
            print(f"📊 [SIMPLE] Total features: {len(embedding)}D")
            
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
            
            print(f"✅ [SIMPLE] Extracted enhanced embedding: shape={embedding.shape}, norm={np.linalg.norm(embedding):.6f}")
            return embedding
            
        except Exception as e:
            print(f"❌ [SIMPLE] Enhanced embedding failed: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(512, dtype=np.float32)

    def extract_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Trích xuất và chuẩn hóa embedding 512D"""
        # If ONNX not available, use simple fallback
        if not self.use_onnx or self.session is None:
            print("⚠️ [ONNX] ONNX not available, using simple feature extraction")
            return self.extract_embedding_simple(face_image)

        try:
            # Preprocessing 112x112
            img = cv2.resize(face_image, (112, 112))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = img.astype(np.float32)
            img = (img - 127.5) / 128.0
            img = np.transpose(img, (2, 0, 1))
            img = np.expand_dims(img, axis=0)
            
            # Inference
            input_name = self.session.get_inputs()[0].name
            output_name = self.session.get_outputs()[0].name
            embeddings = self.session.run([output_name], {input_name: img})[0]
            
            # Post-processing & L2 Norm
            embedding = embeddings[0].flatten()
            norm = np.linalg.norm(embedding)
            if norm > 1e-6:
                embedding = embedding / norm
                
            return embedding
        except Exception as e:
            print(f"❌ [ONNX] Extraction failed: {e}, fallback to simple")
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
        self.arcface = ArcFaceEmbedding()
        
        # Adjust threshold nếu dùng fallback embedding
        if not self.arcface.use_onnx:
            print(f"⚠️ [ArcFaceModel] ONNX not available, using fallback embedding")
            # IMPROVED: Use 0.45 for better discrimination (not too high/low)
            # Same-person: typically 0.6-0.9
            # Different-person: typically 0.1-0.3
            # Threshold 0.45 gives good balance
            print(f"   Adjusting cosine_threshold from {self.cosine_threshold} → 0.45 (fallback)")
            self.cosine_threshold = 0.45
        
        print(f"🤖 [ArcFaceModel] AI Engine ready. Threshold: {self.cosine_threshold}")

    def extract_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """Trích xuất embedding từ file ảnh - tự động crop mặt trước"""
        if not os.path.exists(image_path):
            print(f"❌ [AI] File not found: {image_path}")
            return None
        
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ [AI] Cannot read image: {image_path}")
            return None
        
        print(f"📸 [EXTRACT] Loaded image shape: {img.shape}, dtype: {img.dtype}")
        
        # Crop khuôn mặt trước khi extract
        face_img = crop_face_from_image(img)
        if face_img is None:
            # FALLBACK: Thử normalize brightness/contrast để detection tốt hơn
            print("⚠️ [EXTRACT] First attempt failed, trying image normalization...")
            
            # Convert to float và normalize
            img_float = img.astype(np.float32) / 255.0
            img_normalized = np.clip(img_float * 1.15, 0, 1) * 255  # Tăng brightness 15%
            img_normalized = img_normalized.astype(np.uint8)
            
            print(f"   ├─ Normalized image stats: min={img_normalized.min()}, max={img_normalized.max()}")
            face_img = crop_face_from_image(img_normalized)
            
            if face_img is None:
                # FALLBACK 2: Nếu vẫn không detect được, dùng toàn bộ image
                # Resize lại cho fitting vào model (112x112)
                print(f"⚠️ [EXTRACT] Crop failed, using full frame as fallback (will resize to 112x112)")
                face_img = cv2.resize(img, (224, 224))  # Resize to 224x224 first for better quality
                print(f"✅ [EXTRACT] Using fallback: full frame resized to {face_img.shape}")
        
        return self.arcface.extract_embedding(face_img)

    def extract_embedding_from_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Trích xuất embedding trực tiếp từ numpy array (frame camera) - tự động crop mặt"""
        if frame is None or frame.size == 0:
            return None
        
        # Crop khuôn mặt trước khi extract
        face_img = crop_face_from_image(frame)
        if face_img is None:
            print(f"❌ [AI] Không tìm thấy khuôn mặt trong frame")
            return None
            
        return self.arcface.extract_embedding(face_img)

    def register_face(self, image_path: str, user_data: Dict) -> bool:
        """
        Đăng ký khuôn mặt mới vào file accounts.json
        Tự động crop khuôn mặt trước khi extract embedding.
        """
        embedding = self.extract_embedding(image_path)
        if embedding is None:
            print(f"❌ [REGISTER] Không thể trích xuất embedding từ ảnh: {image_path}")
            return False

        try:
            # 1. Đọc file accounts.json
            accounts_path = os.path.abspath("src/GUI/data/accounts.json")
            if not os.path.exists(accounts_path):
                data = {"admin_accounts": [], "user_accounts": []}
            else:
                with open(accounts_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

            # 2. Encode embedding sang base64 để lưu vào JSON
            # Chuyển numpy array sang bytes -> base64
            emb_bytes = embedding.astype(np.float32).tobytes()
            emb_base64 = base64.b64encode(emb_bytes).decode('utf-8')

            # 3. Cập nhật hoặc thêm user
            username = user_data.get('username')
            found = False
            for user in data['user_accounts']:
                if user['username'] == username:
                    user.update(user_data)
                    user['face_data'] = {"encrypted_image": emb_base64}
                    found = True
                    break
            
            if not found:
                user_data['face_data'] = {"encrypted_image": emb_base64}
                data['user_accounts'].append(user_data)

            # 4. Lưu lại file
            with open(accounts_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ [REGISTER] Successfully registered face for {username}")
            return True

        except Exception as e:
            print(f"❌ [REGISTER] Error: {e}")
            return False

    def verify_face(self, image_path: str, username: str, password: str = "") -> Tuple[bool, float]:
        """
        Xác thực khuôn mặt với dữ liệu trong accounts.json
        """
        # 1. Trích xuất embedding từ ảnh hiện tại
        current_embedding = self.extract_embedding(image_path)
        if current_embedding is None:
            print(f"❌ [VERIFY] Could not extract embedding from {image_path}")
            return False, 0.0
        
        print(f"✅ [VERIFY] Extracted current embedding: shape={current_embedding.shape}, dtype={current_embedding.dtype}")

        try:
            # 2. Đọc file accounts.json
            accounts_path = os.path.abspath("src/GUI/data/accounts.json")
            if not os.path.exists(accounts_path):
                print(f"❌ [VERIFY] accounts.json not found")
                return False, 0.0
                
            with open(accounts_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 3. Tìm user và lấy stored embedding
            stored_embedding = None
            for user in data.get('user_accounts', []):
                if user['username'] == username:
                    face_data = user.get('face_data', {})
                    emb_base64 = face_data.get('encrypted_image')
                    if emb_base64:
                        # Decode base64 -> bytes -> numpy array
                        emb_bytes = base64.b64decode(emb_base64)
                        stored_embedding = np.frombuffer(emb_bytes, dtype=np.float32)
                        print(f"✅ [VERIFY] Loaded stored embedding: shape={stored_embedding.shape}, dtype={stored_embedding.dtype}")
                    break
            
            if stored_embedding is None:
                print(f"⚠️ [VERIFY] No face data found for user {username}")
                return False, 0.0

            # 4. So sánh
            similarity = self.arcface.compare_embeddings(current_embedding, stored_embedding)
            matched = similarity >= self.cosine_threshold
            
            status = "✅ MATCH" if matched else "❌ NO MATCH"
            print(f"    {status} | {username}: {similarity:.4f} (threshold: {self.cosine_threshold:.4f})")
            print(f"    └─ Current embedding norm: {np.linalg.norm(current_embedding):.6f}")
            print(f"    └─ Stored embedding norm: {np.linalg.norm(stored_embedding):.6f}")
            
            return matched, float(similarity)

        except Exception as e:
            print(f"❌ [VERIFY] Error: {e}")
            import traceback
            traceback.print_exc()
            return False, 0.0
