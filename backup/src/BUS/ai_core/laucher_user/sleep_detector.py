import cv2
import numpy as np
from ultralytics import YOLO
import os

class SleepDetector:
    def __init__(self, model_path):
        """
        AI Detector for drowsiness detection using YOLOv8
        :param model_path: Path to the trained .pt model
        """
        self.model_path = model_path
        self.model = None
        self.is_loaded = False
        
        # Load model immediately if path exists
        if os.path.exists(model_path):
            self.load_model()
        else:
            print(f"❌ [AI CORE] Model not found: {model_path}")

    def load_model(self):
        try:
            print(f"🔄 [AI CORE] Loading model from: {self.model_path}")
            self.model = YOLO(self.model_path)
            self.is_loaded = True
            print("✅ [AI CORE] Sleep detection model loaded successfully")
        except Exception as e:
            print(f"❌ [AI CORE] Error loading model: {e}")
            self.is_loaded = False

    def predict(self, frame, conf=0.15):
        """
        Run inference on a single frame
        :param frame: Input image (BGR)
        :param conf: Confidence threshold (lower = more sensitive)
        :return: annotated_frame, detections, is_drowsy
        """
        if not self.is_loaded or self.model is None:
            return frame, [], False

        try:
            # Run inference with lower confidence threshold
            results = self.model(frame, verbose=False, conf=conf)
            
            # Draw detections
            annotated_frame = results[0].plot() 
            
            detections = []
            is_drowsy = False
            
            # Get class names dict
            names = self.model.names
            
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls)
                    cls_name = names[cls_id] if names else str(cls_id)
                    conf_score = float(box.conf)
                    
                    detections.append({
                        "class": cls_id,
                        "name": cls_name,
                        "conf": conf_score,
                        "bbox": box.xyxy.tolist()
                    })
                    
                    # Logic nhận diện nhắm mắt/buồn ngủ
                    # Kiểm tra nếu tên class chứa "close" hoặc "sleep" hoặc "drowsy"
                    # Thêm "closed" để chắc chắn
                    keys = ["close", "closed", "sleep", "drowsy", "eye_close"]
                    if any(k in cls_name.lower() for k in keys):
                        is_drowsy = True

            return annotated_frame, detections, is_drowsy
            
        except Exception as e:
            print(f"⚠️ [AI CORE] Inference error: {e}")
            return frame, [], False
