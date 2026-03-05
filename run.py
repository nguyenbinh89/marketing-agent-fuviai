"""
FuviAI Marketing Agent — Quick start script
Chạy: python run.py
"""

import uvicorn
from backend.config.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
