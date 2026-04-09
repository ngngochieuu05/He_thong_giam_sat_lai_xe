# -*- coding: utf-8 -*-
"""
Telegram Link Service
Quản lý liên kết tài khoản với Telegram thông qua token
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
import threading

# ===== PATH CONFIG =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Data dir chuyển sang GUI/data để đồng bộ với DB và admin UI
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "..", "src", "GUI", "data"))
TOKEN_FILE_PATH = os.path.join(DATA_DIR, "telegram_tokens.json")
ACCOUNTS_FILE_PATH = os.path.join(DATA_DIR, "accounts.json")

# ===== CONSTANTS =====
TOKEN_EXPIRY_HOURS = 24

# Thread lock cho file operations
_file_lock = threading.Lock()


def _ensure_data_dir():
    """Đảm bảo thư mục data tồn tại"""
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_tokens() -> Dict:
    """
    Load danh sách tokens từ file
    Returns:
        Dict với structure: {"tokens": {token: {username, created_at, expires_at}}}
    """
    _ensure_data_dir()
    
    try:
        if os.path.exists(TOKEN_FILE_PATH):
            with open(TOKEN_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            return {"tokens": {}}
    except Exception as e:
        print(f"[TelegramLinkService] Error loading tokens: {e}")
        return {"tokens": {}}


def _save_tokens(tokens_data: Dict) -> bool:
    """
    Lưu danh sách tokens vào file
    Args:
        tokens_data: Dict chứa tokens
    Returns:
        True nếu thành công
    """
    _ensure_data_dir()
    
    try:
        with open(TOKEN_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(tokens_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[TelegramLinkService] Error saving tokens: {e}")
        return False


def _load_accounts() -> Dict:
    """
    Load danh sách accounts từ file
    Returns:
        Dict với structure: {"user_accounts": [...], "admin_accounts": [...]}
    """
    try:
        if os.path.exists(ACCOUNTS_FILE_PATH):
            with open(ACCOUNTS_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            print(f"[TelegramLinkService] Accounts file not found: {ACCOUNTS_FILE_PATH}")
            return {"user_accounts": [], "admin_accounts": []}
    except Exception as e:
        print(f"[TelegramLinkService] Error loading accounts: {e}")
        return {"user_accounts": [], "admin_accounts": []}


def _save_accounts(accounts_data: Dict) -> bool:
    """
    Lưu danh sách accounts vào file
    Args:
        accounts_data: Dict chứa accounts
    Returns:
        True nếu thành công
    """
    try:
        with open(ACCOUNTS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(accounts_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[TelegramLinkService] Error saving accounts: {e}")
        return False


# ==================== TOKEN MANAGEMENT ====================

def generate_link_token(username: str) -> str:
    """
    Tạo token duy nhất cho user để liên kết Telegram
    
    Args:
        username: Username của user cần tạo token
        
    Returns:
        Token string (UUID format)
    """
    with _file_lock:
        # Generate UUID token
        token = str(uuid.uuid4())
        
        # Load existing tokens
        tokens_data = _load_tokens()
        
        # Xóa token cũ của user này (nếu có)
        tokens_to_remove = []
        for t, info in tokens_data["tokens"].items():
            if info.get("username") == username:
                tokens_to_remove.append(t)
        
        for t in tokens_to_remove:
            del tokens_data["tokens"][t]
        
        # Tạo token mới
        now = datetime.now()
        expires = now + timedelta(hours=TOKEN_EXPIRY_HOURS)
        
        tokens_data["tokens"][token] = {
            "username": username,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "expires_at": expires.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save
        _save_tokens(tokens_data)
        
        print(f"[TelegramLinkService] Generated token for user: {username}")
        return token


def validate_token(token: str) -> Optional[str]:
    """
    Validate token và trả về username nếu hợp lệ
    
    Args:
        token: Token cần validate
        
    Returns:
        Username nếu token hợp lệ, None nếu không hợp lệ hoặc hết hạn
    """
    with _file_lock:
        tokens_data = _load_tokens()
        
        if token not in tokens_data["tokens"]:
            print(f"[TelegramLinkService] Token not found: {token}")
            return None
        
        token_info = tokens_data["tokens"][token]
        expires_at_str = token_info.get("expires_at")
        
        if not expires_at_str:
            print(f"[TelegramLinkService] Token missing expiry: {token}")
            return None
        
        # Check expiry
        try:
            expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expires_at:
                print(f"[TelegramLinkService] Token expired: {token}")
                # Remove expired token
                del tokens_data["tokens"][token]
                _save_tokens(tokens_data)
                return None
        except Exception as e:
            print(f"[TelegramLinkService] Error parsing expiry date: {e}")
            return None
        
        username = token_info.get("username")
        print(f"[TelegramLinkService] Token validated for user: {username}")
        
        # Remove token after successful validation (one-time use)
        del tokens_data["tokens"][token]
        _save_tokens(tokens_data)
        
        return username


def cleanup_expired_tokens():
    """
    Xóa các token đã hết hạn
    """
    with _file_lock:
        tokens_data = _load_tokens()
        now = datetime.now()
        
        tokens_to_remove = []
        for token, info in tokens_data["tokens"].items():
            expires_at_str = info.get("expires_at")
            if expires_at_str:
                try:
                    expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
                    if now > expires_at:
                        tokens_to_remove.append(token)
                except Exception:
                    tokens_to_remove.append(token)
        
        for token in tokens_to_remove:
            del tokens_data["tokens"][token]
        
        if tokens_to_remove:
            _save_tokens(tokens_data)
            print(f"[TelegramLinkService] Cleaned up {len(tokens_to_remove)} expired tokens")


# ==================== USER BINDING ====================

def bind_telegram(username: str, chat_id: str, telegram_username: str = "") -> bool:
    """
    Liên kết Telegram chat_id với user account
    
    Args:
        username: Username của user
        chat_id: Telegram chat_id
        telegram_username: Telegram username (optional)
        
    Returns:
        True nếu liên kết thành công
    """
    with _file_lock:
        accounts_data = _load_accounts()
        
        # Tìm user account
        user_found = False
        for user in accounts_data.get("user_accounts", []):
            if user.get("username") == username:
                user_found = True
                
                # Check if already linked
                if "telegram_data" in user and user["telegram_data"].get("chat_id"):
                    print(f"[TelegramLinkService] User already linked: {username}")
                    return False
                
                # Add telegram_data
                user["telegram_data"] = {
                    "chat_id": chat_id,
                    "telegram_username": telegram_username,
                    "linked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Save
                if _save_accounts(accounts_data):
                    try:
                        from src.DAL.tai_xe_dal import lien_ket_telegram
                        from src.DAL.accounts_sync import export_accounts_to_json
                        lien_ket_telegram(username, chat_id, telegram_username or None)
                        export_accounts_to_json()
                    except Exception as e:
                        print(f"[TelegramLinkService] DB sync failed: {e}")
                    print(f"[TelegramLinkService] Successfully linked user {username} with chat_id {chat_id}")
                    return True
                else:
                    print(f"[TelegramLinkService] Failed to save account data for user: {username}")
                    return False
        
        if not user_found:
            print(f"[TelegramLinkService] User not found: {username}")
        
        return False


def check_bound(username: str) -> Optional[Dict]:
    """
    Kiểm tra xem user đã liên kết Telegram chưa
    
    Args:
        username: Username cần kiểm tra
        
    Returns:
        Dict chứa telegram_data nếu đã liên kết, None nếu chưa
    """
    accounts_data = _load_accounts()
    
    for user in accounts_data.get("user_accounts", []):
        if user.get("username") == username:
            telegram_data = user.get("telegram_data")
            if telegram_data and telegram_data.get("chat_id"):
                return telegram_data
            return None

    try:
        from src.DAL.accounts_sync import get_driver_account_from_db
        db_user = get_driver_account_from_db(username)
        if db_user:
            telegram_data = db_user.get("telegram_data")
            if telegram_data and telegram_data.get("chat_id"):
                return telegram_data
    except Exception as e:
        print(f"[TelegramLinkService] DB check failed: {e}")

    return None


def get_chat_id_by_username(username: str) -> Optional[str]:
    """
    Lấy chat_id của user
    
    Args:
        username: Username
        
    Returns:
        chat_id nếu đã liên kết, None nếu chưa
    """
    telegram_data = check_bound(username)
    if telegram_data:
        return telegram_data.get("chat_id")
    return None


# ==================== BOT CONFIGURATION ====================

def get_bot_info() -> Dict:
    """
    Lấy thông tin bot từ API.json
    
    Returns:
        Dict chứa bot_token, bot_name, bot_url
    """
    try:
        # Load from API.json
        api_config_path = os.path.join(DATA_DIR, "API.json")
        
        if os.path.exists(api_config_path):
            with open(api_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            telegram_config = config.get("telegram", {})
            bot_token = telegram_config.get("bot_token", "")
            
            # Bot name is hardcoded as per requirements
            bot_name = "safedrive_alert_bot"
            bot_url = f"https://t.me/{bot_name}"
            
            return {
                "bot_token": bot_token,
                "bot_name": bot_name,
                "bot_url": bot_url
            }
        else:
            print(f"[TelegramLinkService] API.json not found at {api_config_path}")
            return {
                "bot_token": "",
                "bot_name": "safedrive_alert_bot",
                "bot_url": "https://t.me/safedrive_alert_bot"
            }
    except Exception as e:
        print(f"[TelegramLinkService] Error loading bot info: {e}")
        return {
            "bot_token": "",
            "bot_name": "safedrive_alert_bot",
            "bot_url": "https://t.me/safedrive_alert_bot"
        }


# ===== STARTUP CLEANUP =====
# Cleanup expired tokens on module import
try:
    cleanup_expired_tokens()
except Exception as e:
    print(f"[TelegramLinkService] Error during startup cleanup: {e}")


# ===== TEST =====
if __name__ == "__main__":
    print("=== Telegram Link Service Test ===")
    
    # Test token generation
    test_username = "test_user"
    token = generate_link_token(test_username)
    print(f"Generated token: {token}")
    
    # Test token validation
    validated_username = validate_token(token)
    print(f"Validated username: {validated_username}")
    
    # Test binding
    success = bind_telegram(test_username, "123456789", "@test_telegram")
    print(f"Binding success: {success}")
    
    # Test check bound
    telegram_data = check_bound(test_username)
    print(f"Telegram data: {telegram_data}")
    
    # Test bot info
    bot_info = get_bot_info()
    print(f"Bot info: {bot_info}")
