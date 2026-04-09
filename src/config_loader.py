"""
Utility for loading configuration from model_config.json
Được sử dụng bởi cả Admin và User modules để đảm bảo đồng bộ
"""

import os
import json

def get_camera_index():
    """
    Đọc camera index từ model_config.json
    Nếu không tìm thấy config hoặc lỗi, trả về 0 (default)
    
    Returns:
        int: Camera index (0, 1, 2, ...)
    """
    try:
        # Tìm file model_config.json từ GUI/data/
        # Hàm này gọi từ .py files khác nhau, nên tính path tuyệt đối
        current_file = os.path.abspath(__file__)  # src/config_loader.py
        project_root = os.path.dirname(os.path.dirname(current_file))  # giam_sat_lai_xe/
        config_path = os.path.join(project_root, "src", "GUI", "data", "model_config.json")
        
        print(f"\n🔍 [CONFIG_LOADER_TRACE] Calculating path:")
        print(f"   ├─ Current file: {current_file}")
        print(f"   ├─ Project root: {project_root}")
        print(f"   └─ Config path: {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                
            # Lấy camera index từ config
            camera_index = config_data.get("camera", {}).get("default_index", 0)
            print(f"✅ [CONFIG_LOADER] SUCCESS: Loaded camera index [{camera_index}]")
            print(f"   └─ From: {config_path}")
            print(f"\n📊 [CONFIG_LOADER] Full config: {json.dumps(config_data.get('camera', {}), indent=2)}\n")
            return int(camera_index)
        else:
            print(f"⚠️  [CONFIG_LOADER] Camera config NOT FOUND at {config_path}")
            print(f"   Using default camera index: 0\n")
            return 0
            
    except Exception as e:
        print(f"❌ [CONFIG_LOADER] ERROR loading camera config: {e}")
        print(f"   Using default camera index: 0\n")
        return 0


def get_model_config():
    """
    Đọc toàn bộ config từ model_config.json
    
    Returns:
        dict: Toàn bộ config data
    """
    try:
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(current_file))
        config_path = os.path.join(project_root, "src", "GUI", "data", "model_config.json")
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            print(f"✅ [CONFIG_LOADER] Loaded full config from {config_path}")
            return config_data
        else:
            print(f"⚠️  [CONFIG_LOADER] Config file not found at {config_path}")
            return {}
            
    except Exception as e:
        print(f"❌ [CONFIG_LOADER] Error loading config: {e}")
        return {}
