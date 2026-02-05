"""
ArcFace Face Recognition System
================================
YOLOv8 + InsightFace (ArcFace) + AES-256 Encryption + Cosine Similarity

Tác giả: AI Assistant
Ngày: 2026-02-02
"""

import cv2
import numpy as np
import json
import base64
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from datetime import datetime
import sys
import os

# Context manager để tắt output (bao gồm cả C++ output nếu có thể)
class SuppressOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

# Cryptography
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

# ========== SILENT MODE - TẮT TẤT CẢ LOG ==========
SILENT_MODE = False  # Set to False để bật lại logging

def log_print(*args, **kwargs):
    """Print wrapper - chỉ print khi SILENT_MODE = False"""
    if not SILENT_MODE:
        print(*args, **kwargs)
# ==================================================

# ML/AI
# Global placeholders for Lazy Loading
YOLO = None
FaceAnalysis = None
cosine_similarity = None
HAS_MODELS = False
AI_LIBS_LOADED = False

def _load_ai_libs():
    """Lazy load heavy AI libraries"""
    global YOLO, FaceAnalysis, cosine_similarity, HAS_MODELS, AI_LIBS_LOADED
    
    if AI_LIBS_LOADED:
        return

    log_print("⏳ [SYSTEM] Loading AI libraries (Lazy Import)...")
    try:
        from ultralytics import YOLO as _YOLO
        import insightface
        from insightface.app import FaceAnalysis as _FaceAnalysis
        from sklearn.metrics.pairwise import cosine_similarity as _cosine_similarity
        
        # Suppress ONNX Runtime warnings
        try:
            import onnxruntime
            onnxruntime.set_default_logger_severity(3)
        except:
            pass
            
        YOLO = _YOLO
        FaceAnalysis = _FaceAnalysis
        cosine_similarity = _cosine_similarity
        HAS_MODELS = True
        AI_LIBS_LOADED = True
        log_print("✅ [SYSTEM] AI libraries loaded successfully")
    except ImportError as e:
        import traceback
        traceback.print_exc()
        HAS_MODELS = False
    except Exception as e:
        import traceback
        traceback.print_exc()
        HAS_MODELS = False

# Base interface
from src.BUS.ai_core.login_user.base_face_model import BaseFaceModel


# ============================================================================
# 1. YOLOV8 FACE DETECTOR
# ============================================================================

class YOLOv8FaceDetector:
    """Phát hiện khuôn mặt bằng YOLOv8"""
    
    def __init__(self, confidence_threshold: float = 0.75, min_face_size: int = 40):
        """
        Args:
            confidence_threshold: Ngưỡng độ tin cậy (0.0-1.0)
            min_face_size: Kích thước khuôn mặt tối thiểu (pixels)
        """
        # Ensure libs are loaded
        _load_ai_libs()
        
        self.confidence_threshold = confidence_threshold
        self.min_face_size = min_face_size
        
        # Load YOLOv8 model (sử dụng pretrained hoặc custom)
        # Note: Có thể cần model custom trained cho face detection
        try:
            self.model = YOLO('yolov8n.pt')  # YOLOv8 nano
            log_print(f"✅ [YOLOv8] Model loaded successfully")
        except Exception as e:
            pass
            self.model = None
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Phát hiện khuôn mặt trong ảnh
        
        Args:
            image: Ảnh đầu vào (BGR format)
            
        Returns:
            List[Dict]: [{'bbox': [x, y, w, h], 'confidence': float}]
        """
        if self.model is None:
            pass
            return []
        
        try:
            results = self.model(image, conf=self.confidence_threshold, verbose=False)
            faces = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    w, h = x2 - x1, y2 - y1
                    
                    # Kiểm tra kích thước tối thiểu
                    if w >= self.min_face_size and h >= self.min_face_size:
                        faces.append({
                            'bbox': [int(x1), int(y1), int(w), int(h)],
                            'confidence': conf
                        })
            
            # Log only if faces found (reduce spam)
            if len(faces) > 0:
                pass
            return faces
            
        except Exception as e:
            pass
            return []
    
    def crop_face(self, image: np.ndarray, bbox: List[int]) -> np.ndarray:
        """
        Cắt khuôn mặt từ ảnh
        
        Args:
            image: Ảnh gốc
            bbox: [x, y, w, h]
            
        Returns:
            Ảnh khuôn mặt đã cắt
        """
        x, y, w, h = bbox
        return image[y:y+h, x:x+w]


# ============================================================================
# 2. ARCFACE EMBEDDING EXTRACTOR
# ============================================================================

class ArcFaceEmbedding:
    """Trích xuất embedding 512D bằng InsightFace ArcFace"""
    
    def __init__(self):
        """Khởi tạo ArcFace model"""
        # Ensure libs are loaded
        _load_ai_libs()

        if not HAS_MODELS or FaceAnalysis is None:
            log_print("❌ [InsightFace] Libraries not installed or import failed")
            self.app = None
            return
            
        try:
            # Revert SuppressOutput as it breaks InsightFace logic
            self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            log_print("✅ [InsightFace] Model ArcFace embedding đã khởi tạo")
        except Exception as e:
            print(f"❌ [InsightFace] Init failed: {e}")
            self.app = None
    
    def extract_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Trích xuất embedding 512D
        
        Args:
            face_image: Ảnh khuôn mặt (BGR)
            
        Returns:
            np.ndarray(512,) hoặc None nếu thất bại
        """
        if self.app is None:
            pass
            return None
        
        try:
            # InsightFace cần RGB
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            faces = self.app.get(face_rgb)
            
            if len(faces) == 0:
                print(f"⚠️ [InsightFace] Không tìm thấy khuôn mặt trong crop image (Shape: {face_rgb.shape})")
                return None
            
            # Lấy embedding của khuôn mặt đầu tiên
            embedding = faces[0].embedding
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            # Removed log to reduce spam
            return embedding
            
        except Exception as e:
            pass
            return None
    
    def compare_embeddings(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        So sánh 2 embeddings bằng cosine similarity
        
        Args:
            emb1, emb2: Embeddings 512D
            
        Returns:
            float: Độ tương đồng (0.0-1.0)
        """
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        pass
        return float(similarity)


# ============================================================================
# 3. FACE ENCRYPTION (AES-256)
# ============================================================================

class FaceEncryption:
    """Mã hóa/giải mã ảnh khuôn mặt bằng AES-256"""
    
    def __init__(self):
        self.key_length = 32  # AES-256
        self.salt_length = 16
        self.iterations = 100000  # PBKDF2 iterations
    
    def encrypt_image(self, image: np.ndarray, password: str) -> Dict:
        """
        Mã hóa ảnh khuôn mặt
        
        Args:
            image: Ảnh (numpy array)
            password: Mật khẩu user
            
        Returns:
            Dict: {
                'encrypted_data': str (Base64),
                'salt': str (Base64),
                'iv': str (Base64),
                'shape': tuple
            }
        """
        try:
            # Serialize ảnh
            image_bytes = image.tobytes()
            
            # Tạo salt và derive key
            salt = get_random_bytes(self.salt_length)
            key = PBKDF2(password, salt, dkLen=self.key_length, count=self.iterations)
            
            # Tạo IV và cipher
            iv = get_random_bytes(AES.block_size)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # Padding
            pad_length = AES.block_size - len(image_bytes) % AES.block_size
            padded_data = image_bytes + bytes([pad_length] * pad_length)
            
            # Mã hóa
            encrypted = cipher.encrypt(padded_data)
            
            result = {
                'encrypted_data': base64.b64encode(encrypted).decode('utf-8'),
                'salt': base64.b64encode(salt).decode('utf-8'),
                'iv': base64.b64encode(iv).decode('utf-8'),
                'shape': image.shape
            }
            
            return result
            
        except Exception as e:
            pass
            return None
    
    def decrypt_image(self, encrypted_data: str, salt: str, iv: str, 
                     shape: tuple, password: str) -> Optional[np.ndarray]:
        """
        Giải mã ảnh khuôn mặt
        
        Args:
            encrypted_data: Dữ liệu mã hóa (Base64)
            salt: Salt (Base64)
            iv: IV (Base64)
            shape: Kích thước ảnh gốc
            password: Mật khẩu user
            
        Returns:
            np.ndarray: Ảnh đã giải mã hoặc None nếu sai password
        """
        try:
            # Decode Base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            salt_bytes = base64.b64decode(salt)
            iv_bytes = base64.b64decode(iv)
            
            # Derive key
            key = PBKDF2(password, salt_bytes, dkLen=self.key_length, count=self.iterations)
            
            # Decrypt
            cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
            decrypted = cipher.decrypt(encrypted_bytes)
            
            # Remove padding
            pad_length = decrypted[-1]
            unpadded = decrypted[:-pad_length]
            
            # Reshape
            image = np.frombuffer(unpadded, dtype=np.uint8).reshape(shape)
            
            pass
            return image
            
        except Exception as e:
            pass
            return None


# ============================================================================
# 4. MAIN ARCFACE MODEL
# ============================================================================

class ArcFaceModel(BaseFaceModel):
    """
    Hệ thống nhận diện khuôn mặt hoàn chỉnh
    YOLOv8 → ArcFace → AES → Cosine Similarity
    """
    
    def __init__(self, config: Dict):
        """
        Args:
            config: {
                'confidence_threshold': float,
                'min_face_size': int,
                'cosine_threshold': float
            }
        """
        super().__init__(config)
        
        # Khởi tạo các components
        self.yolo = YOLOv8FaceDetector(
            self.confidence_threshold, 
            self.min_face_size
        )
        self.arcface = ArcFaceEmbedding()
        self.encryption = FaceEncryption()
        
        # Database path
        self.accounts_file = Path("src/GUI/data/accounts.json")
        
        log_print("✅ [SYSTEM] Face Recognition System fully initialized")
    
    def register_face(self, image_path: str, user_data: Dict) -> bool:
        """
        Đăng ký khuôn mặt mới
        
        Luồng: Load Image → YOLO Detect → Crop → ArcFace Extract → AES Encrypt → Save JSON
        
        Args:
            image_path: Đường dẫn ảnh khuôn mặt
            user_data: {'username', 'password', 'name', etc.}
            
        Returns:
            bool: Thành công hay không
        """
        pass
        
        try:
            # 1. Load image
            image = cv2.imread(image_path)
            if image is None:
                pass
                return False
            
            # 2. Detect face
            faces = self.yolo.detect_faces(image)
            if len(faces) == 0:
                pass
                return False
            
            # Lấy khuôn mặt lớn nhất
            face_data = max(faces, key=lambda f: f['bbox'][2] * f['bbox'][3])
            face_crop = self.yolo.crop_face(image, face_data['bbox'])
            
            # 3. Extract embedding
            embedding = self.arcface.extract_embedding(face_crop)
            if embedding is None:
                pass
                return False
            
            # 4. Encrypt face image
            encrypted = self.encryption.encrypt_image(face_crop, user_data['password'])
            if encrypted is None:
                pass
                return False
            
            # 5. Encrypt embedding
            emb_bytes = embedding.tobytes()
            emb_encrypted = self.encryption.encrypt_image(
                np.frombuffer(emb_bytes, dtype=np.uint8).reshape(-1),
                user_data['password']
            )
            
            # 6. Save to JSON
            face_entry = {
                'encrypted_image': encrypted['encrypted_data'],
                'salt': encrypted['salt'],
                'iv': encrypted['iv'],
                'shape': encrypted['shape'],
                'embedding_encrypted': emb_encrypted['encrypted_data'],
                'embedding_salt': emb_encrypted['salt'],
                'embedding_iv': emb_encrypted['iv'],
                'registered_at': datetime.now().isoformat(),
                'model': 'ArcFace'
            }
            
            # Add to user_data
            user_data['face_data'] = face_entry
            
            # Save to accounts.json
            if self._save_user_account(user_data):
                pass
                return True
            else:
                pass
                return False
                
        except Exception as e:
            pass
            return False
    
    def verify_face(self, image_path: str, username: str, password: str) -> Tuple[bool, float]:
        """
        Xác thực khuôn mặt
        
        Luồng: Load Image → YOLO → ArcFace → Load Encrypted Embedding → 
               Decrypt → Cosine Similarity → Match?
        
        Args:
            image_path: Ảnh hiện tại
            username: Tên đăng nhập
            password: Mật khẩu
            
        Returns:
            (matched, similarity_score)
        """
        pass
        
        try:
            # 1. Load image
            image = cv2.imread(image_path)
            if image is None:
                pass
                return False, 0.0
            
            # 2. Detect and extract embedding from current image
            faces = self.yolo.detect_faces(image)
            if len(faces) == 0:
                pass
                return False, 0.0
            
            face_crop = self.yolo.crop_face(image, faces[0]['bbox'])
            current_embedding = self.arcface.extract_embedding(face_crop)
            
            if current_embedding is None:
                pass
                return False, 0.0
            
            # 3. Load user data from JSON
            user_data = self._load_user_account(username)
            if user_data is None or 'face_data' not in user_data:
                pass
                return False, 0.0
            
            face_data = user_data['face_data']
            
            # 4. Decrypt stored embedding
            emb_encrypted_bytes = base64.b64decode(face_data['embedding_encrypted'])
            emb_salt = face_data['embedding_salt']
            emb_iv = face_data['embedding_iv']
            
            # Tạo shape cho embedding (512 floats = 2048 bytes)
            emb_shape = (2048,)
            
            emb_decrypted = self.encryption.decrypt_image(
                face_data['embedding_encrypted'],
                emb_salt,
                emb_iv,
                emb_shape,
                password
            )
            
            if emb_decrypted is None:
                pass
                return False, 0.0
            
            # Convert back to float32 embedding
            stored_embedding = np.frombuffer(emb_decrypted.tobytes(), dtype=np.float32)
            
            # 5. Compare embeddings
            similarity = self.arcface.compare_embeddings(current_embedding, stored_embedding)
            
            # 6. Check threshold
            matched = similarity >= self.cosine_threshold
            
            if matched:
                pass
            else:
                pass
            
            return matched, similarity
            
        except Exception as e:
            pass
            return False, 0.0
    
    def extract_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """
        Trích xuất embedding từ ảnh
        
        Args:
            image_path: Đường dẫn ảnh
            
        Returns:
            Embedding 512D hoặc None
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            faces = self.yolo.detect_faces(image)
            if len(faces) == 0:
                return None
            
            face_crop = self.yolo.crop_face(image, faces[0]['bbox'])
            return self.arcface.extract_embedding(face_crop)
            
        except Exception as e:
            pass
            return None
    
    # ========== HELPER FUNCTIONS ==========
    
    def _save_user_account(self, user_data: Dict) -> bool:
        """Lưu tài khoản vào accounts.json"""
        try:
            # Load existing data
            if self.accounts_file.exists():
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"admin_accounts": [], "user_accounts": []}
            
            # Check if user exists
            for i, user in enumerate(data['user_accounts']):
                if user['username'] == user_data['username']:
                    data['user_accounts'][i] = user_data
                    pass
                    break
            else:
                data['user_accounts'].append(user_data)
                pass
            
            # Save
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            pass
            return False
    
    def _load_user_account(self, username: str) -> Optional[Dict]:
        """Load tài khoản từ accounts.json"""
        try:
            if not self.accounts_file.exists():
                return None
            
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for user in data.get('user_accounts', []):
                if user['username'] == username:
                    return user
            
            return None
            
        except Exception as e:
            pass
            return None


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    pass
    pass
    pass
    
    # Test configuration
    config = {
        'confidence_threshold': 0.75,
        'min_face_size': 40,
        'cosine_threshold': 0.75
    }
    
    model = ArcFaceModel(config)
    pass
    pass
    pass
    pass

