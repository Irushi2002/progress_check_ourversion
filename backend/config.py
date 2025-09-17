
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB Configuration
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "intern_progress")
    
    # Google AI Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Application Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Collections
    WORK_UPDATES_COLLECTION = "work_updates"
    TEMP_WORK_UPDATES_COLLECTION = "temp_work_updates"  
    FOLLOWUP_SESSIONS_COLLECTION = "followup_sessions"
    
    # AI Model Configuration
    GEMINI_MODEL = "gemini-2.0-flash"
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        return True