# -*- coding: utf-8 -*-
"""
Bot Initializer
Auto-starts Telegram bot when GUI loads
"""

# Import to trigger bot auto-start
try:
    import sys
    import os
    from src.BUS.oa_core.sua_thong_bao import tuy_chinh_thong_bao

    print("[BotInit] Telegram bot initialization triggered")
    
except Exception as e:
    print(f"[BotInit] Warning: Failed to initialize Telegram bot: {e}")
