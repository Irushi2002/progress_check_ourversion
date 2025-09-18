import os
from dotenv import load_dotenv

load_dotenv()


# Get the API key
api_key = os.getenv("API_SECRET_KEY")

print(f"My API key is: {api_key}")
class Config:
    # MongoDB Configuration
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "intern_progress")
    
    # Google AI Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # ProHub API Configuration
    PROHUB_API_URL = os.getenv(
        "PROHUB_API_URL", 
        "https://prohub.slt.com.lk/ProhubTrainees/api/MainApi/AllActiveTrainees"
    )
    PROHUB_API_TIMEOUT = int(os.getenv("PROHUB_API_TIMEOUT", "30"))  # Seconds
    PROHUB_CACHE_DURATION = int(os.getenv("PROHUB_CACHE_DURATION", "300"))  # Seconds
    
    # Application Configuration
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Collections
    WORK_UPDATES_COLLECTION = "dailyrecords"  # Updated to match LogBook
    TEMP_WORK_UPDATES_COLLECTION = "temp_work_updates"
    FOLLOWUP_SESSIONS_COLLECTION = "followup_sessions"
    
    # AI Model Configuration
    GEMINI_MODEL = "gemini-2.0-flash"  
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        if not cls.PROHUB_API_URL:
            raise ValueError("PROHUB_API_URL environment variable is required")
        return True