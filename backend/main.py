import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("pymongo").setLevel(logging.WARNING)
from dotenv import load_dotenv
load_dotenv()  # Must be first
import uuid
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId
import asyncio
import os
from config import Config
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import Query
from config import Config
from database import (
    connect_to_mongo, close_mongo_connection, get_database, get_work_update_data,
    create_temp_work_update, get_temp_work_update, delete_temp_work_update,
    move_temp_to_permanent, cleanup_abandoned_temp_updates, get_database_stats,
    verify_ttl_index
)
from ai_service import AIFollowupService
from models import (
    GenerateQuestionsRequest, GenerateQuestionsResponse, 
    FollowupAnswersUpdate, AnalysisResponse, TestAIResponse, 
    ErrorResponse, WorkUpdate, WorkUpdateCreate, FollowupSession, SessionStatus, WorkStatus
)
from integration import (
    get_prohub_integration, authenticate_via_prohub_email, check_prohub_api_health,
    ProHubIntegrationError, is_valid_company_email, extract_name_from_email
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable to control the cleanup task
cleanup_task = None

async def scheduled_cleanup_task():
    """Background task that runs cleanup every hour (backup to TTL)"""
    while True:
        try:
            logger.info("Running scheduled manual cleanup (backup to TTL)...")
            
            # Verify TTL is working
            ttl_working = await verify_ttl_index()
            
            if ttl_working:
                logger.info("TTL index is active - automatic deletion is working")
                result = await cleanup_abandoned_temp_updates(25)  # Clean slightly older items as backup
            else:
                logger.warning("TTL index not found! Running manual cleanup more aggressively")
                result = await cleanup_abandoned_temp_updates(24)  # Regular cleanup
            
            deleted_temp = result.get("deleted_temp_updates", 0)
            deleted_sessions = result.get("deleted_sessions", 0)
            
            if deleted_temp > 0 or deleted_sessions > 0:
                cleanup_type = "backup" if ttl_working else "primary"
                logger.info(f"Scheduled {cleanup_type} cleanup: Removed {deleted_temp} temp updates and {deleted_sessions} sessions")
            else:
                status = "TTL working properly" if ttl_working else "No items found"
                logger.info(f"Scheduled cleanup: {status}")
                
        except Exception as e:
            logger.error(f"Error in scheduled cleanup: {e}")
        
        # Wait for 1 hour before next cleanup
        await asyncio.sleep(3600)  # 3600 seconds = 1 hour

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global cleanup_task
    
    # Startup
    try:
        Config.validate_config()
        await connect_to_mongo()
        
        # Verify TTL index is working
        ttl_status = await verify_ttl_index()
        if ttl_status:
            logger.info("✅ TTL index verified - automatic cleanup is active")
        else:
            logger.warning("⚠️ TTL index not found - relying on manual cleanup")
        
        # Test ProHub API connection
        prohub_health = await check_prohub_api_health()
        if prohub_health["status"] == "healthy":
            logger.info(f"✅ ProHub API connection verified - {prohub_health['trainees_count']} trainees found")
        else:
            logger.warning(f"⚠️ ProHub API connection issue: {prohub_health.get('error', 'Unknown error')}")
        
        # Start the background cleanup task (as backup to TTL)
        cleanup_task = asyncio.create_task(scheduled_cleanup_task())
        logger.info("Background cleanup task started (backup to TTL)")
        
        logger.info("Application started successfully with ProHub integration")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("Background cleanup task cancelled")
    
    await close_mongo_connection()
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Intern Management AI Service with ProHub Integration",
    description="AI-powered follow-up question generation and analysis for intern management with ProHub trainee authentication",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://prohub.slt.com.lk"],  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  
    allow_headers=["*"],
)

async def get_current_intern(request: Request) -> dict:
    """
    Extract intern information from ProHub system via email authentication
    Accepts any email format - ProHub API validates if user is a trainee
    """
    try:
        # TEMPORARY DEVELOPMENT BYPASS - REMOVE IN PRODUCTION
        if Config.DEBUG:
            logger.warning("Using development auth bypass")
            return {
                "intern_id": "test_intern_123",
                "name": "Test Intern", 
                "email": "test@gmail.com",  # Accept any email format
                "department": "IT Development",
                "batch": "2024",
                "prohub_id": "test_intern_123"
            }
        
        # Method 1: Check X-User-Email header (from existing website Google Auth)
        user_email = request.headers.get("X-User-Email")
        
        # Method 2: Check Authorization header with email
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Email "):
            user_email = auth_header.replace("Email ", "")
        
        # Method 3: Check custom headers for testing
        if not user_email:
            user_email = request.headers.get("User-Email")
        
        # Method 4: Development/testing fallback
        if not user_email:
            test_email = request.headers.get("X-Test-Email")
            if test_email and Config.DEBUG:
                logger.warning(f"Using test email authentication: {test_email}")
                user_email = test_email
        
        if not user_email:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. User email not provided."
            )
        
        # Basic email format validation only (no domain restrictions)
        if not user_email or '@' not in user_email:
            raise HTTPException(
                status_code=401,
                detail="Invalid email format provided."
            )
        
        # REMOVED: Company domain validation - accept any email
        # The ProHub API will validate if the user is actually a trainee
        
        # Authenticate via ProHub API
        user_info = await authenticate_via_prohub_email(user_email)
        
        if not user_info:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed. User not found or inactive in ProHub system."
            )
        
        logger.info(f"ProHub authentication successful: {user_info['name']} ({user_email})")
        
        return user_info
        
    except HTTPException:
        raise
    except ProHubIntegrationError as e:
        logger.error(f"ProHub integration error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Authentication service temporarily unavailable. Please try again."
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Authentication system error. Please contact support."
        )

# Dependency to get AI service
async def get_ai_service() -> AIFollowupService:
    """Get AI service instance"""
    try:
        return AIFollowupService()
    except Exception as e:
        logger.error(f"Failed to initialize AI service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI service initialization failed: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint with ProHub integration info"""
    ttl_status = await verify_ttl_index()
    prohub_health = await check_prohub_api_health()
    
    return {
        "message": "Intern Management AI Service with ProHub Integration",
        "version": "2.0.0",
        "status": "running",
        "integration": "ProHub API + Google Auth",
        "authentication": "ProHub trainee verification",
        "prohub_api_status": prohub_health["status"],
        "trainees_available": prohub_health.get("trainees_count", 0),
        "ttl_cleanup": "active" if ttl_status else "manual_only",
        "cleanup_task_status": "running" if cleanup_task and not cleanup_task.done() else "stopped"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with ProHub integration status"""
    try:
        db = get_database()
        # Test database connection
        await db.command("ping")
        
        # Check TTL status
        ttl_working = await verify_ttl_index()
        
        # Check ProHub API health
        prohub_health = await check_prohub_api_health()
        
        return {
            "status": "healthy",
            "database": "connected",
            "ttl_index": "active" if ttl_working else "not_found",
            "automatic_cleanup": "enabled" if ttl_working else "disabled",
            "cleanup_task_running": cleanup_task and not cleanup_task.done(),
            "prohub_integration": prohub_health["status"],
            "prohub_trainees_count": prohub_health.get("trainees_count", 0),
            "prohub_response_time": prohub_health.get("response_time_seconds"),
            "authentication": "ProHub API integration ready",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "ttl_index": "unknown",
            "cleanup_task_running": False,
            "prohub_integration": "error",
            "authentication": "error",
            "timestamp": datetime.now().isoformat()
        }

# ProHub API endpoints
@app.get("/api/prohub/health")
async def prohub_health_check():
    """Check ProHub API connectivity and status"""
    return await check_prohub_api_health()

@app.get("/api/prohub/trainees/summary")
async def get_trainees_summary(current_intern: dict = Depends(get_current_intern)):
    """Get summary of all trainees (requires authentication)"""
    try:
        integration = get_prohub_integration()
        summary = await integration.get_all_active_trainees_summary()
        
        return {
            "message": "Trainees summary retrieved successfully",
            "summary": summary,
            "requested_by": current_intern["name"]
        }
    except Exception as e:
        logger.error(f"Error getting trainees summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trainees summary: {str(e)}"
        )

@app.post("/api/prohub/refresh-cache")
async def refresh_prohub_cache(current_intern: dict = Depends(get_current_intern)):
    """Force refresh ProHub trainees cache"""
    try:
        integration = get_prohub_integration()
        trainees = await integration.fetch_all_trainees(force_refresh=True)
        
        return {
            "message": "ProHub cache refreshed successfully",
            "trainees_count": len(trainees),
            "refreshed_by": current_intern["name"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error refreshing ProHub cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh cache: {str(e)}"
        )

@app.post("/api/work-updates")
async def create_work_update(
    work_update: WorkUpdateCreate,
    current_intern: dict = Depends(get_current_intern)
):
    """Create work update with ProHub-authenticated user"""
    try:
        # Get intern ID from ProHub authentication
        intern_id = current_intern["intern_id"]
        
        # Validate work status and task description
        if work_update.status in [WorkStatus.WORKING, WorkStatus.WFH]:
            if not work_update.task or not work_update.task.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Task description is required when status is 'working' or 'wfh'"
                )
        
        db = get_database()
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        if work_update.status == WorkStatus.LEAVE:
            # ON LEAVE: Save directly to LogBook's DailyRecord collection
            daily_records = db["dailyrecords"]  # LogBook collection name
            
            record_dict = {
                "date": today_date,
                "stack": work_update.stack,
                "task": work_update.task or "On Leave",
                "progress": "On Leave",
                "blockers": "On Leave",
                "status": "leave"
            }

            # FIXED: Handle ObjectId properly
            try:
                # Check if intern_id is already a valid ObjectId format
                if len(intern_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in intern_id):
                    record_dict["internId"] = ObjectId(intern_id)
                    date_based_query = {"internId": ObjectId(intern_id), "date": today_date}
                else:
                    # For development/testing, use string format
                    record_dict["internId"] = intern_id
                    date_based_query = {"internId": intern_id, "date": today_date}
                    logger.warning(f"Using string intern_id instead of ObjectId: {intern_id}")
            except Exception as e:
                # Fallback to string format
                record_dict["internId"] = intern_id
                date_based_query = {"internId": intern_id, "date": today_date}
                logger.warning(f"Could not convert intern_id to ObjectId, using string: {e}")

            existing_record = await daily_records.find_one(date_based_query)

            if existing_record:
                await daily_records.replace_one({"_id": existing_record["_id"]}, record_dict)
                record_id = str(existing_record["_id"])
                is_override = True
            else:
                result = await daily_records.insert_one(record_dict)
                record_id = str(result.inserted_id)
                is_override = False

            logger.info(f"LEAVE record saved to LogBook for intern {intern_id}: {record_id}")
            
            return {
                "message": f"Leave status saved successfully for {current_intern['name']}",
                "recordId": record_id,
                "isOverride": is_override,
                "redirectToFollowup": False,
                "isOnLeave": True,
                "internInfo": {
                    "name": current_intern["name"],
                    "email": current_intern["email"],
                    "department": current_intern.get("department", "")
                }
            }
        
        else:
            # WORKING/WFH: Save to TEMPORARY collection (pending follow-up)
            update_dict = {
                "internId": intern_id,  # Keep as string for temp collection
                "date": today_date,
                "stack": work_update.stack,
                "task": work_update.task,
                "progress": work_update.progress,
                "blockers": work_update.blockers,
                "status": work_update.status,
                "submittedAt": datetime.now(),
                "followupCompleted": False,
                "temp_status": "pending_followup"
            }

            # Use database function to create temp work update
            temp_work_update_id = await create_temp_work_update(update_dict)
            
            logger.info(f"WORKING/WFH record saved to temp collection for intern {intern_id} (TTL: 24h): {temp_work_update_id}")
            
            return {
                "message": f"Work update saved temporarily for {current_intern['name']}. Complete AI follow-up within 24 hours to finalize in LogBook.",
                "tempWorkUpdateId": temp_work_update_id,  
                "redirectToFollowup": True,
                "isOnLeave": False,
                "ttl_expiry": "24 hours from now",
                "internInfo": {
                    "name": current_intern["name"],
                    "email": current_intern["email"],
                    "department": current_intern.get("department", "")
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating work update: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create work update: {str(e)}"
        )

# Start follow-up session using TEMP work update (with ProHub auth)
# @app.post("/api/followups/start")
# async def start_followup_session(
#     temp_work_update_id: str,
#     current_intern: dict = Depends(get_current_intern),
#     ai_service: AIFollowupService = Depends(get_ai_service)
# ):
#     """Start follow-up session using temporary work update data"""
#     try:
#         db = get_database()
#         followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]
#         intern_id = current_intern["intern_id"]

#         # Get TEMPORARY work update data
#         temp_work_update = await get_temp_work_update(temp_work_update_id)
#         if not temp_work_update:
#             raise HTTPException(
#                 status_code=404, 
#                 detail="Temporary work update not found (may have been auto-deleted after 24h)"
#             )

#         # Verify the temp work update belongs to the authenticated intern
#         if str(temp_work_update.get("internId")) != str(intern_id):
#             raise HTTPException(
#                 status_code=403,
#                 detail="Access denied - work update belongs to different intern"
#             )

#         today_date = datetime.now().strftime('%Y-%m-%d')
#         session_date_id = f"{intern_id}_{uuid.uuid4().hex}"

#         # Generate questions using temp data
#         ai_input_data = {
#             "description": temp_work_update.get("task"),  # Map task to description
#             "challenges": temp_work_update.get("progress", ""),
#             "plans": temp_work_update.get("blockers", ""),
#             "user_id": intern_id
#         }
#         questions = await ai_service.generate_followup_questions(intern_id, work_update_data=ai_input_data)

#         session_doc = {
#             "_id": session_date_id,
#             "internId": intern_id,
#             "tempWorkUpdateId": temp_work_update_id, 
#             "session_date": today_date,
#             "questions": questions,
#             "answers": [""] * len(questions),
#             "status": SessionStatus.PENDING,
#             "createdAt": datetime.now(),
#             "completedAt": None
#         }
#         await followup_collection.replace_one({"_id": session_date_id}, session_doc, upsert=True)

#         logger.info(f"Follow-up session started for intern {intern_id} with temp work update: {temp_work_update_id}")

#         return {
#             "message": f"AI follow-up session started for {current_intern['name']}",
#             "sessionId": session_date_id,
#             "questions": questions,
#             "reminder": "Complete within 24 hours before auto-deletion",
#             "internInfo": {
#                 "name": current_intern["name"],
#                 "email": current_intern["email"]
#             }
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error starting follow-up session: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to start follow-up session: {str(e)}"
#         ) 
@app.post("/api/followups/start")
async def start_followup_session(
    temp_work_update_id: str = Query(..., description="Temporary work update ID"),
    current_intern: dict = Depends(get_current_intern),
    ai_service: AIFollowupService = Depends(get_ai_service)
):
    """Start follow-up session using temporary work update data"""
    try:
        db = get_database()
        followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]
        intern_id = current_intern["intern_id"]
        
        logger.info(f"Starting follow-up session for intern {intern_id} with temp update {temp_work_update_id}")

        # Get TEMPORARY work update data
        temp_work_update = await get_temp_work_update(temp_work_update_id)
        if not temp_work_update:
            raise HTTPException(
                status_code=404, 
                detail="Temporary work update not found (may have been auto-deleted after 24h)"
            )

        # Verify the temp work update belongs to the authenticated intern
        if str(temp_work_update.get("internId")) != str(intern_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied - work update belongs to different intern"
            )

        today_date = datetime.now().strftime('%Y-%m-%d')
        session_date_id = f"{intern_id}_{uuid.uuid4().hex}"

        # Generate questions using temp data
        ai_input_data = {
            "description": temp_work_update.get("task", ""),  # Map task to description
            "challenges": temp_work_update.get("progress", ""),
            "plans": temp_work_update.get("blockers", ""),
            "user_id": intern_id
        }
        
        logger.info(f"Generating AI questions with data: {ai_input_data}")
        questions = await ai_service.generate_followup_questions(intern_id, work_update_data=ai_input_data)

        session_doc = {
            "_id": session_date_id,
            "internId": intern_id,
            "tempWorkUpdateId": temp_work_update_id, 
            "session_date": today_date,
            "questions": questions,
            "answers": [""] * len(questions),
            "status": SessionStatus.PENDING,
            "createdAt": datetime.now(),
            "completedAt": None
        }
        
        await followup_collection.replace_one({"_id": session_date_id}, session_doc, upsert=True)

        logger.info(f"Follow-up session created: {session_date_id}")

        return {
            "message": f"AI follow-up session started for {current_intern['name']}",
            "sessionId": session_date_id,
            "questions": questions,
            "reminder": "Complete within 24 hours before auto-deletion",
            "internInfo": {
                "name": current_intern["name"],
                "email": current_intern["email"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting follow-up session: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start follow-up session: {str(e)}"
        )


@app.put("/api/followup/{session_id}/complete")
async def complete_followup_session(
    session_id: str,
    answers_update: FollowupAnswersUpdate,
    current_intern: dict = Depends(get_current_intern)
):
    """Complete follow-up session and move temp work update to LogBook's DailyRecord collection"""
    try:
        # Validate all answers provided
        if not answers_update.answers or len(answers_update.answers) != 3:
            raise HTTPException(
                status_code=400,
                detail="All 3 questions must be answered"
            )
        
        # Check if any answer is empty
        if any(not answer.strip() for answer in answers_update.answers):
            raise HTTPException(
                status_code=400,
                detail="All questions must have non-empty answers"
            )
        
        db = get_database()
        followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]
        daily_records = db["dailyrecords"]  # LogBook collection
        intern_id = current_intern["intern_id"]
        
        # Get the follow-up session and verify ownership
        session = await followup_collection.find_one({"_id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Follow-up session not found")

        if str(session.get("internId")) != str(intern_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied - session belongs to different intern"
            )

        # Get the temporary work update
        temp_work_update = await get_temp_work_update(session["tempWorkUpdateId"])
        if not temp_work_update:
            raise HTTPException(
                status_code=404, 
                detail="Temporary work update not found (may have been auto-deleted due to TTL expiry)"
            )

        # Complete the follow-up session
        session_update = {
            "answers": answers_update.answers,
            "status": SessionStatus.COMPLETED,
            "completedAt": datetime.now()
        }
        
        await followup_collection.update_one(
            {"_id": session_id},
            {"$set": session_update}
        )

        # FIXED: Handle ObjectId properly for LogBook compatibility
        # Create the daily record document
        daily_record = {
            "date": temp_work_update["date"],
            "stack": temp_work_update["stack"],
            "task": temp_work_update["task"],
            "progress": temp_work_update.get("progress", "No challenges faced"),
            "blockers": temp_work_update.get("blockers", "No specific plans"),
            "status": temp_work_update["status"]
        }

        # FIXED: Only add ObjectId if intern_id is a valid ObjectId format
        try:
            # Check if intern_id is already a valid ObjectId or can be converted
            if len(intern_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in intern_id):
                daily_record["internId"] = ObjectId(intern_id)
            else:
                # For development/testing, use string format
                daily_record["internId"] = intern_id
                logger.warning(f"Using string intern_id instead of ObjectId: {intern_id}")
        except Exception as e:
            # Fallback to string format
            daily_record["internId"] = intern_id
            logger.warning(f"Could not convert intern_id to ObjectId, using string: {e}")

        # Check for existing record (override logic)
        existing_record = await daily_records.find_one({
            "internId": daily_record["internId"],  # Use the same format as we stored
            "date": temp_work_update["date"]
        })
        
        if existing_record:
            await daily_records.replace_one({"_id": existing_record["_id"]}, daily_record)
            final_record_id = str(existing_record["_id"])
            logger.info(f"Updated existing LogBook record for intern {intern_id}: {final_record_id}")
        else:
            result = await daily_records.insert_one(daily_record)
            final_record_id = str(result.inserted_id)
            logger.info(f"Created new LogBook record for intern {intern_id}: {final_record_id}")

        # Update session with final record ID
        await followup_collection.update_one(
            {"_id": session_id},
            {"$set": {"dailyRecordId": final_record_id}}
        )

        # Delete temp work update
        await delete_temp_work_update(session["tempWorkUpdateId"])

        logger.info(f"AI follow-up completed for intern {intern_id}, LogBook record finalized: {final_record_id}")
        
        return {
            "message": f"AI follow-up completed successfully for {current_intern['name']}. Work update saved to LogBook system.",
            "sessionId": session_id,
            "dailyRecordId": final_record_id,
            "workUpdateCompleted": True,
            "note": "Work update moved to LogBook DailyRecord collection",
            "internInfo": {
                "name": current_intern["name"],
                "email": current_intern["email"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete follow-up: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete follow-up: {str(e)}"
        )

@app.get("/stats")
async def get_stats():
    """Get database statistics including ProHub integration status"""
    try:
        stats = await get_database_stats()
        
        # Add cleanup task status to stats
        ttl_status = await verify_ttl_index()
        
        # Add ProHub integration status
        prohub_health = await check_prohub_api_health()
        
        if stats:
            stats["cleanup_system"] = {
                "ttl_index_active": ttl_status,
                "manual_task_running": cleanup_task and not cleanup_task.done(),
                "cleanup_frequency": "Every 1 hour (backup to TTL)",
                "automatic_deletion": "24 hours via TTL index" if ttl_status else "Manual only"
            }
            stats["integration"] = {
                "prohub_api_status": prohub_health["status"],
                "prohub_trainees_count": prohub_health.get("trainees_count", 0),
                "prohub_response_time": prohub_health.get("response_time_seconds"),
                "daily_records_collection": "dailyrecords",
                "authentication": "ProHub API + Google OAuth",
                "cache_valid": prohub_health.get("cache_valid", False)
            }
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )

# Get specific follow-up session (with ProHub auth)
@app.get("/api/followup/session/{session_id}")
async def get_followup_session(
    session_id: str,
    current_intern: dict = Depends(get_current_intern)
):
    """Get specific follow-up session details"""
    try:
        db = get_database()
        followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]
        intern_id = current_intern["intern_id"]
        
        # Ensure user can only access their own sessions
        session = await followup_collection.find_one({
            "_id": session_id,
            "internId": intern_id
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        
        # Convert ObjectId to string for JSON serialization
        session["sessionId"] = session["_id"]
        if "_id" in session:
            del session["_id"]
        
        # Add intern info to response
        session["internInfo"] = {
            "name": current_intern["name"],
            "email": current_intern["email"]
        }
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )

@app.get("/api/followup-sessions")
async def get_followup_sessions(
    current_intern: dict = Depends(get_current_intern),
    limit: int = 150,
    skip: int = 0
):
    """Get follow-up sessions for authenticated intern"""
    try:
        db = get_database()
        followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]
        intern_id = current_intern["intern_id"]
        
        cursor = followup_collection.find(
            {"internId": intern_id}
        ).sort("createdAt", -1).skip(skip).limit(limit)
        
        sessions = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for session in sessions:
            if "_id" in session:
                session["id"] = str(session["_id"])
                session["sessionId"] = session["_id"]
                del session["_id"]
        
        return {
            "sessions": sessions,
            "count": len(sessions),
            "intern_id": intern_id,
            "intern_email": current_intern["email"],
            "intern_name": current_intern["name"]
        }
        
    except Exception as e:
        logger.error(f"Error getting followup sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get followup sessions: {str(e)}"
        )

# New endpoint to check TTL and cleanup system status
@app.get("/api/cleanup/status")
async def get_cleanup_status():
    """Get detailed status of the TTL and cleanup system"""
    ttl_active = await verify_ttl_index()
    
    return {
        "ttl_index": {
            "active": ttl_active,
            "expiry_time": "24 hours",
            "status": "Automatic deletion enabled" if ttl_active else "TTL index not found"
        },
        "manual_cleanup": {
            "task_running": cleanup_task and not cleanup_task.done(),
            "frequency": "Every 1 hour",
            "purpose": "Backup to TTL + Session cleanup",
            "age_threshold": "24+ hours"
        },
        "recommendation": "TTL handles most cleanup automatically" if ttl_active else "Relying on manual cleanup only"
    }

# Manual cleanup endpoint (backup to automatic TTL)
@app.delete("/api/temp-work-updates/cleanup")
async def cleanup_abandoned_temp_updates_endpoint():
    """Manually trigger cleanup of temporary work updates (backup to TTL)"""
    try:
        ttl_active = await verify_ttl_index()
        result = await cleanup_abandoned_temp_updates(24)
        
        deleted_temp = result.get("deleted_temp_updates", 0)
        deleted_sessions = result.get("deleted_sessions", 0)
        
        return {
            "message": f"Manual cleanup completed. Cleaned up {deleted_temp} temp updates and {deleted_sessions} sessions",
            "deleted_temp_updates": deleted_temp,
            "deleted_sessions": deleted_sessions,
            "ttl_status": "active" if ttl_active else "inactive",
            "note": "TTL index handles most cleanup automatically" if ttl_active else "Manual cleanup is primary method"
        }
        
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup: {str(e)}"
        )

# Auth configuration endpoint for frontend
@app.get("/api/auth/config")
async def get_auth_config():
    """Get authentication configuration for frontend integration"""
    prohub_health = await check_prohub_api_health()
    
    return {
        "auth_method": "prohub_email",
        "required_headers": ["X-User-Email", "User-Email"],
        "alternative_headers": ["Authorization: Email {email}"],
        "prohub_api_status": prohub_health["status"],
        "trainees_available": prohub_health.get("trainees_count", 0),
        "integration_status": "ProHub API + Google OAuth",
        "email_validation": "Company domain required",
        "test_mode_available": Config.DEBUG
    }

# Testing endpoint for development
@app.post("/api/auth/test")
async def test_auth(request: Request):
    """Test endpoint to verify authentication works (development only)"""
    if not Config.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        current_intern = await get_current_intern(request)
        return {
            "message": "Authentication test successful",
            "intern_info": current_intern,
            "headers_received": dict(request.headers),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException as e:
        return {
            "message": "Authentication test failed",
            "error": e.detail,
            "status_code": e.status_code,
            "headers_received": dict(request.headers),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/ai/test")
async def test_ai_endpoint(current_intern: dict = Depends(get_current_intern)):
    """Test AI service functionality"""
    try:
        ai_service = await get_ai_service()
        
        # Test AI connection
        ai_working = await ai_service.test_ai_connection()
        
        return {
            "message": "AI service test endpoint",
            "ai_status": "working" if ai_working else "failed",
            "model": Config.GEMINI_MODEL,
            "tested_by": current_intern["name"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"AI test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI test failed: {str(e)}"
        )

# Add favicon endpoint to prevent 404s
@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint to prevent 404 errors"""
    return {"message": "No favicon configured"}

# Alternative AI test without auth (for development)
@app.get("/api/ai/test/simple")
async def simple_ai_test():
    """Simple AI test without authentication (for development)"""
    try:
        ai_service = await get_ai_service()
        ai_working = await ai_service.test_ai_connection()
        
        return {
            "message": "Simple AI test",
            "ai_status": "working" if ai_working else "failed",
            "model": Config.GEMINI_MODEL,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Simple AI test failed: {e}")
        return {
            "message": "AI test failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(ProHubIntegrationError)
async def prohub_exception_handler(request, exc: ProHubIntegrationError):
    """Handle ProHub integration exceptions"""
    logger.error(f"ProHub integration error: {exc}")
    return JSONResponse(
        status_code=503,
        content={
            "error": "PROHUB_INTEGRATION_ERROR",
            "message": "ProHub system temporarily unavailable",
            "details": str(exc) if Config.DEBUG else None,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR", 
            "message": "An internal error occurred",
            "details": str(exc) if Config.DEBUG else None,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=Config.DEBUG,
        log_level="info"
    )