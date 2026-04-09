"""
Base Face Recognition Model Interface

Tất cả các model nhận diện khuôn mặt (ArcFace, FaceNet, DeepFace) 
phải kế thừa class này để đảm bảo tính nhất quán.
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Tuple, Optional

class BaseFaceModel(ABC):
    """Interface chung cho tất cả face recognition models"""
    
    def __init__(self, config: Dict):
        """
        Khởi tạo model với cấu hình

        Args:
            config (Dict): Cấu hình từ UI {
                'confidence_threshold': float (0.0-1.0),
                'min_face_size': int (pixels),
                'cosine_threshold': float (0.0-1.0)
            }
        """
        self.config = config
        self.confidence_threshold = config.get('confidence_threshold', 0.75)
        self.min_face_size = config.get('min_face_size', 40)
        self.cosine_threshold = config.get('cosine_threshold', 0.75)
        
        print(f"✅ [BASE] Initialized {self.__class__.__name__}")
        print(f"   ├─ Confidence: {self.confidence_threshold}")
        print(f"   ├─ Min Face Size: {self.min_face_size}px")
        print(f"   └─ Cosine Threshold: {self.cosine_threshold}")
    
    @abstractmethod
    def register_face(self, image_path: str, user_data: Dict) -> bool:
        """
        Đăng ký khuôn mặt mới vào hệ thống
        
        Args:
            image_path: Đường dẫn ảnh khuôn mặt
            user_data: Dict chứa username, password, name, etc.
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def verify_face(self, image_path: str, username: str, password: str) -> Tuple[bool, float]:
        """
        Xác thực khuôn mặt với tài khoản đã đăng ký
        
        Args:
            image_path: Đường dẫn ảnh hiện tại
            username: Tên đăng nhập
            password: Mật khẩu (để giải mã ảnh)
            
        Returns:
            Tuple[bool, float]: (khớp?, độ tương đồng)
        """
        pass
    
    @abstractmethod
    def extract_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """
        Trích xuất embedding vector từ ảnh khuôn mặt
        
        Args:
            image_path: Đường dẫn ảnh
            
        Returns:
            np.ndarray: Embedding vector hoặc None nếu thất bại
        """
        pass
    
    def update_config(self, config: Dict):
        """
        Cập nhật cấu hình model (từ UI sliders)
        
        Args:
            config: Dict cấu hình mới
        """
        self.config.update(config)
        self.confidence_threshold = config.get('confidence_threshold', self.confidence_threshold)
        self.min_face_size = config.get('min_face_size', self.min_face_size)
        self.cosine_threshold = config.get('cosine_threshold', self.cosine_threshold)
        
        print(f"🔄 [CONFIG] Updated {self.__class__.__name__} config:")
        print(f"   ├─ Confidence: {self.confidence_threshold}")
        print(f"   ├─ Min Face Size: {self.min_face_size}px")
        print(f"   └─ Cosine Threshold: {self.cosine_threshold}")
