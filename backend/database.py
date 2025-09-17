from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING, ASCENDING
from config import Config
import logging
from datetime import datetime, timedelta
from bson import ObjectId

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

database = Database()

# Collection names
TEMP_WORK_UPDATES_COLLECTION = "temp_work_updates"

async def connect_to_mongo():
    """Create database connection"""
    try:
        database.client = AsyncIOMotorClient(Config.MONGODB_URL)
        database.database = database.client[Config.DATABASE_NAME]
        
        # Test the connection
        await database.client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes 
        await create_indexes()
        
        # Run existing data migration
        await migrate_existing_data()
        
        # Setup cleanup routine for temp collection with TTL
        await setup_ttl_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if database.client:
        database.client.close()
        logger.info("Disconnected from MongoDB")

async def setup_ttl_indexes():
    """Setup TTL index for automatic cleanup of temp work updates"""
    try:
        temp_collection = database.database[TEMP_WORK_UPDATES_COLLECTION]
        
        # Check if TTL index already exists
        existing_indexes = await temp_collection.list_indexes().to_list(length=None)
        
        # Look for existing TTL index
        ttl_index_exists = False
        regular_submittedAt_index_exists = False
        
        for index in existing_indexes:
            index_key = index.get('key', {})
            if 'submittedAt' in index_key:
                if 'expireAfterSeconds' in index:
                    ttl_index_exists = True
                    logger.info(f"TTL index already exists: {index['name']} (expires after {index['expireAfterSeconds']}s)")
                else:
                    regular_submittedAt_index_exists = True
                    regular_index_name = index['name']
        
        # If regular submittedAt index exists without TTL, drop it first
        if regular_submittedAt_index_exists and not ttl_index_exists:
            try:
                await temp_collection.drop_index("submittedAt_1")
                logger.info("Dropped regular submittedAt index to replace with TTL index")
            except Exception as e:
                logger.warning(f"Could not drop regular submittedAt index: {e}")
        
        # Create TTL index if it doesn't exist
        if not ttl_index_exists:
            await temp_collection.create_index(
                "submittedAt", 
                expireAfterSeconds=86400,  # 24 hours in seconds
                name="submittedAt_ttl_24h"
            )
            logger.info("TTL index created successfully - documents expire after 24 hours")
        
        # Verify TTL index is working
        await verify_ttl_index()
        
    except Exception as e:
        logger.error(f"Failed to setup TTL indexes: {e}")
        raise

async def verify_ttl_index():
    """Verify that TTL index is properly configured"""
    try:
        temp_collection = database.database[TEMP_WORK_UPDATES_COLLECTION]
        
        # Get all indexes to verify TTL setup
        indexes = await temp_collection.list_indexes().to_list(length=None)
        
        for index in indexes:
            if 'expireAfterSeconds' in index and 'submittedAt' in index.get('key', {}):
                expire_seconds = index['expireAfterSeconds']
                expire_hours = expire_seconds / 3600
                logger.info(f"✅ TTL index verified: {index['name']} - expires after {expire_hours} hours")
                return True
        
        logger.warning("❌ No TTL index found on submittedAt field")
        return False
        
    except Exception as e:
        logger.error(f"Failed to verify TTL index: {e}")
        return False

async def create_indexes():
    """Create necessary indexes (excluding TTL - handled separately)"""
    try:
        # Work updates indexes
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        await work_updates.create_index("userId")
        await work_updates.create_index([("userId", 1), ("submittedAt", DESCENDING)])
        await work_updates.create_index([("userId", 1), ("update_date", 1)], unique=True)  # Prevent duplicate dates
        
        # Index for tracking incomplete follow-ups
        await work_updates.create_index([("userId", 1), ("followupCompleted", 1)])
        await work_updates.create_index([("followupCompleted", 1), ("submittedAt", DESCENDING)])
        
        # Temporary work updates indexes (non-TTL indexes)
        temp_work_updates = database.database[TEMP_WORK_UPDATES_COLLECTION]
        await temp_work_updates.create_index("userId")
        await temp_work_updates.create_index([("userId", 1), ("update_date", 1)], unique=True)  # Prevent duplicate dates
        # Note: submittedAt TTL index is created in setup_ttl_indexes()
        await temp_work_updates.create_index([("submittedAt", 1), ("status", 1)])  # For cleanup queries
        
        # Followup sessions indexes  
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        await followup_sessions.create_index("userId")
        await followup_sessions.create_index([("userId", 1), ("status", 1)])
        await followup_sessions.create_index([("userId", 1), ("createdAt", DESCENDING)])
        await followup_sessions.create_index([("userId", 1), ("session_date", 1)], unique=True)  # Date-based sessions
        
        # Index for linking sessions to work updates
        await followup_sessions.create_index("workUpdateId")
        await followup_sessions.create_index("tempWorkUpdateId")  # For temp work update references
        await followup_sessions.create_index([("workUpdateId", 1), ("status", 1)])
        
        # Compound index for efficient pending session queries
        await followup_sessions.create_index([
            ("userId", 1), 
            ("status", 1), 
            ("createdAt", DESCENDING)
        ])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"Failed to create indexes: {e}")

async def setup_temp_collection():
    """Legacy function - now handled by setup_ttl_indexes()"""
    logger.info("setup_temp_collection() called - delegating to setup_ttl_indexes()")
    await setup_ttl_indexes()

async def migrate_existing_data():
    """Migrate existing work updates to include followupCompleted field"""
    try:
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        
        # Check if migration is needed
        sample_doc = await work_updates.find_one()
        if sample_doc and "followupCompleted" not in sample_doc:
            logger.info("Migrating existing work updates...")
            
            # Update all existing work updates
            result = await work_updates.update_many(
                {"followupCompleted": {"$exists": False}},
                {"$set": {"followupCompleted": True}}  # Assume old updates are complete
            )
            
            logger.info(f"Migrated {result.modified_count} existing work updates")
        else:
            logger.info("Work updates schema is up to date")
            
    except Exception as e:
        logger.warning(f"Failed to migrate data: {e}")

async def cleanup_orphaned_sessions():
    """Clean up follow-up sessions that don't have corresponding work updates"""
    try:
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        
        # Get all sessions with workUpdateId
        sessions_cursor = followup_sessions.find(
            {"workUpdateId": {"$exists": True}},
            {"workUpdateId": 1}
        )
        
        orphaned_count = 0
        async for session in sessions_cursor:
            work_update_id = session.get("workUpdateId")
            if work_update_id:
                # Check if work update exists
                work_update = await work_updates.find_one({"_id": ObjectId(work_update_id)})
                if not work_update:
                    # Remove orphaned session
                    await followup_sessions.delete_one({"_id": session["_id"]})
                    orphaned_count += 1
        
        if orphaned_count > 0:
            logger.info(f"Cleaned up {orphaned_count} orphaned follow-up sessions")
        else:
            logger.info("No orphaned sessions found")
            
    except Exception as e:
        logger.warning(f"Failed to cleanup orphaned sessions: {e}")

async def cleanup_abandoned_temp_updates(hours_old: int = 24):
    """Clean up temporary work updates older than specified hours and their associated sessions"""
    try:
        temp_collection = database.database[TEMP_WORK_UPDATES_COLLECTION]
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        
        # Find abandoned temp updates (TTL should handle most, but this is backup)
        abandoned_cursor = temp_collection.find({
            "submittedAt": {"$lt": cutoff_time},
            "status": "pending_followup"
        })
        
        abandoned_count = 0
        deleted_sessions_count = 0
        
        async for temp_update in abandoned_cursor:
            temp_id = str(temp_update["_id"])
            
            # Clean up any associated sessions (both pending and completed)
            session_delete_result = await followup_sessions.delete_many({
                "$or": [
                    {"tempWorkUpdateId": temp_id},
                    {"workUpdateId": temp_id}  # In case it was mistakenly set
                ]
            })
            
            deleted_sessions_count += session_delete_result.deleted_count
            
            # Delete the temp update (backup to TTL)
            await temp_collection.delete_one({"_id": temp_update["_id"]})
            abandoned_count += 1
        
        if abandoned_count > 0:
            logger.info(f"Manual cleanup: {abandoned_count} abandoned temp updates, {deleted_sessions_count} sessions")
        else:
            logger.info("Manual cleanup: No abandoned temporary updates found (TTL working properly)")
        
        return {
            "deleted_temp_updates": abandoned_count,
            "deleted_sessions": deleted_sessions_count,
            "note": "TTL index handles most deletions automatically"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup abandoned temp updates: {e}")
        return {
            "deleted_temp_updates": 0,
            "deleted_sessions": 0,
            "error": str(e)
        }

async def get_database_stats():
    """Get database statistics for monitoring"""
    try:
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        temp_work_updates = database.database[TEMP_WORK_UPDATES_COLLECTION]
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        # Count work updates
        total_work_updates = await work_updates.count_documents({})
        completed_followups = await work_updates.count_documents({"followupCompleted": True})
        incomplete_followups = await work_updates.count_documents({"followupCompleted": False})
        
        # Count temporary work updates
        total_temp_updates = await temp_work_updates.count_documents({})
        pending_temp_updates = await temp_work_updates.count_documents({"status": "pending_followup"})
        
        # Count sessions
        total_sessions = await followup_sessions.count_documents({})
        pending_sessions = await followup_sessions.count_documents({"status": "pending"})
        completed_sessions = await followup_sessions.count_documents({"status": "completed"})
        
        # Check TTL index status
        ttl_status = await verify_ttl_index()
        
        stats = {
            "work_updates": {
                "total": total_work_updates,
                "completed_followups": completed_followups,
                "incomplete_followups": incomplete_followups
            },
            "temp_work_updates": {
                "total": total_temp_updates,
                "pending": pending_temp_updates
            },
            "followup_sessions": {
                "total": total_sessions,
                "pending": pending_sessions,
                "completed": completed_sessions
            },
            "ttl_index": {
                "active": ttl_status,
                "cleanup_interval": "24 hours",
                "status": "Automatic deletion enabled" if ttl_status else "TTL index not found"
            }
        }
        
        logger.info(f"Database Stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return None

async def ensure_data_consistency():
    """Ensure data consistency between work updates and follow-up sessions"""
    try:
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        inconsistency_count = 0
        
        # Find work updates marked as complete but without completed sessions
        work_updates_cursor = work_updates.find({"followupCompleted": True})
        async for work_update in work_updates_cursor:
            work_update_id = str(work_update["_id"])
            
            # Check if there's a completed session for this work update
            completed_session = await followup_sessions.find_one({
                "workUpdateId": work_update_id,
                "status": "completed"
            })
            
            if not completed_session:
                # Mark work update as incomplete
                await work_updates.update_one(
                    {"_id": work_update["_id"]},
                    {"$set": {"followupCompleted": False}}
                )
                inconsistency_count += 1
        
        # Find completed sessions but work updates marked as incomplete
        completed_sessions_cursor = followup_sessions.find({"status": "completed"})
        async for session in completed_sessions_cursor:
            work_update_id = session.get("workUpdateId")
            if work_update_id:
                try:
                    # Check work update status
                    work_update = await work_updates.find_one({"_id": ObjectId(work_update_id)})
                    if work_update and not work_update.get("followupCompleted", False):
                        # Mark work update as complete
                        await work_updates.update_one(
                            {"_id": ObjectId(work_update_id)},
                            {"$set": {"followupCompleted": True}}
                        )
                        inconsistency_count += 1
                except:
                    # Invalid ObjectId, skip
                    continue
        
        if inconsistency_count > 0:
            logger.info(f"Fixed {inconsistency_count} data consistency issues")
        else:
            logger.info("Data consistency verified")
            
    except Exception as e:
        logger.warning(f"Failed to check data consistency: {e}")

def get_database():
    """Get database instance"""
    return database.database

def get_temp_collection():
    """Get temporary work updates collection"""
    return database.database[TEMP_WORK_UPDATES_COLLECTION]

async def create_temp_work_update(work_update_data: dict) -> str:
    """Create temporary work update"""
    try:
        temp_collection = get_temp_collection()
        
        # Check for existing temp update for same user and date
        existing_temp = await temp_collection.find_one({
            "userId": work_update_data["userId"],
            "update_date": work_update_data["update_date"]
        })
        
        if existing_temp:
            # Replace existing temp update
            await temp_collection.replace_one(
                {"_id": existing_temp["_id"]},
                work_update_data
            )
            return str(existing_temp["_id"])
        else:
            # Create new temp update
            result = await temp_collection.insert_one(work_update_data)
            return str(result.inserted_id)
            
    except Exception as e:
        logger.error(f"Failed to create temp work update: {e}")
        raise

async def get_temp_work_update(temp_id: str) -> dict:
    """Get temporary work update by ID"""
    try:
        temp_collection = get_temp_collection()
        return await temp_collection.find_one({"_id": ObjectId(temp_id)})
    except Exception as e:
        logger.error(f"Failed to get temp work update: {e}")
        return None

async def delete_temp_work_update(temp_id: str) -> bool:
    """Delete temporary work update"""
    try:
        temp_collection = get_temp_collection()
        result = await temp_collection.delete_one({"_id": ObjectId(temp_id)})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Failed to delete temp work update: {e}")
        return False

async def move_temp_to_permanent(temp_id: str, additional_data: dict = None) -> str:
    """Move temporary work update to permanent collection"""
    try:
        temp_collection = get_temp_collection()
        work_updates_collection = database.database[Config.WORK_UPDATES_COLLECTION]
        
        # Get temp work update
        temp_update = await temp_collection.find_one({"_id": ObjectId(temp_id)})
        if not temp_update:
            raise ValueError("Temporary work update not found")
        
        # Prepare permanent document
        permanent_update = temp_update.copy()
        del permanent_update["_id"]  # Remove temp ID
        
        # Add additional data if provided
        if additional_data:
            permanent_update.update(additional_data)
        
        # Set completion status
        permanent_update["followupCompleted"] = True
        permanent_update["status"] = "completed"
        permanent_update["completedAt"] = datetime.now()
        
        # Check for existing permanent update (override logic)
        existing_permanent = await work_updates_collection.find_one({
            "userId": permanent_update["userId"],
            "update_date": permanent_update["update_date"]
        })
        
        if existing_permanent:
            # Override existing permanent work update
            await work_updates_collection.replace_one(
                {"_id": existing_permanent["_id"]},
                permanent_update
            )
            permanent_id = str(existing_permanent["_id"])
        else:
            # Create new permanent work update
            result = await work_updates_collection.insert_one(permanent_update)
            permanent_id = str(result.inserted_id)
        
        # Delete temp work update (TTL will also handle this, but immediate cleanup is better)
        await temp_collection.delete_one({"_id": ObjectId(temp_id)})
        
        logger.info(f"Moved temp work update {temp_id} to permanent {permanent_id}")
        return permanent_id
        
    except Exception as e:
        logger.error(f"Failed to move temp to permanent: {e}")
        raise

async def get_work_update_with_session(work_update_id: str):
    """Get work update along with its associated follow-up session"""
    try:
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        # Get work update
        work_update = await work_updates.find_one({"_id": ObjectId(work_update_id)})
        if not work_update:
            return None
        
        # Get associated session
        session = await followup_sessions.find_one({"workUpdateId": work_update_id})
        
        # Convert ObjectIds to strings
        if work_update.get("_id"):
            work_update["id"] = str(work_update["_id"])
            del work_update["_id"]
        
        if session:
            if session.get("_id"):
                session["sessionId"] = session["_id"]
                del session["_id"]
        
        return {
            "work_update": work_update,
            "followup_session": session
        }
        
    except Exception as e:
        logger.error(f"Failed to get work update with session: {e}")
        return None

async def get_user_incomplete_work_updates_with_sessions(user_id: str):
    """Get incomplete work updates along with their pending sessions"""
    try:
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        # Get incomplete work updates
        cursor = work_updates.find(
            {"userId": user_id, "followupCompleted": False}
        ).sort("submittedAt", DESCENDING)
        
        incomplete_updates = await cursor.to_list(length=10)
        
        # Get associated pending sessions
        for update in incomplete_updates:
            update_id = str(update["_id"])
            update["id"] = update_id
            del update["_id"]
            
            # Find associated session
            session = await followup_sessions.find_one({
                "workUpdateId": update_id,
                "status": "pending"
            })
            
            if session:
                session["sessionId"] = session["_id"]
                del session["_id"]
                update["pending_session"] = session
            else:
                update["pending_session"] = None
        
        return incomplete_updates
        
    except Exception as e:
        logger.error(f"Failed to get incomplete updates with sessions: {e}")
        return []

async def get_work_update_data(user_id: str, work_update_id: str = None):
    """Get work update data including challenges and plans for AI processing"""
    try:
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        
        if work_update_id:
            # Get specific work update
            work_update = await work_updates.find_one({"_id": ObjectId(work_update_id)})
        else:
            # Get latest work update for user
            work_update = await work_updates.find_one(
                {"userId": user_id},
                sort=[("submittedAt", DESCENDING)]
            )
        
        if not work_update:
            return None
        
        # Extract relevant data for AI processing
        data = {
            "description": work_update.get("description", ""),
            "challenges": work_update.get("challenges"),
            "plans": work_update.get("plans"),
            "user_id": work_update.get("userId"),
            "submitted_at": work_update.get("submittedAt")
        }
        
        return data
        
    except Exception as e:
        logger.error(f"Failed to get work update data: {e}")
        return None