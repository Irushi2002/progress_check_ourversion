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

# async def create_indexes():
#     """Create necessary indexes for ProHub integration (using internId instead of userId)"""
#     try:
#         # Work updates indexes
#         work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
#         await work_updates.create_index("internId")
#         await work_updates.create_index([("internId", 1), ("submittedAt", DESCENDING)])
#         await work_updates.create_index([("internId", 1), ("update_date", 1)], unique=True)
        
#         # Index for tracking incomplete follow-ups
#         await work_updates.create_index([("internId", 1), ("followupCompleted", 1)])
#         await work_updates.create_index([("followupCompleted", 1), ("submittedAt", DESCENDING)])
        
#         # Temporary work updates indexes (non-TTL indexes)
#         temp_work_updates = database.database[TEMP_WORK_UPDATES_COLLECTION]
#         await temp_work_updates.create_index("internId")
#         await temp_work_updates.create_index([("internId", 1), ("update_date", 1)], unique=True)
#         await temp_work_updates.create_index([("submittedAt", 1), ("status", 1)])
        
#         # Followup sessions indexes using internId
#         followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
#         await followup_sessions.create_index("internId")
#         await followup_sessions.create_index([("internId", 1), ("status", 1)])
#         await followup_sessions.create_index([("internId", 1), ("createdAt", DESCENDING)])
#         await followup_sessions.create_index([("internId", 1), ("session_date", 1)], unique=True)
        
#         # Index for linking sessions to work updates
#         await followup_sessions.create_index("workUpdateId")
#         await followup_sessions.create_index("tempWorkUpdateId")
#         await followup_sessions.create_index([("workUpdateId", 1), ("status", 1)])
        
#         # Compound index for efficient pending session queries
#         await followup_sessions.create_index([
#             ("internId", 1), 
#             ("status", 1), 
#             ("createdAt", DESCENDING)
#         ])
        
#         logger.info("Database indexes created successfully (ProHub integration)")
        
#     except Exception as e:
#         logger.warning(f"Failed to create indexes: {e}")

async def create_indexes():
    """Create necessary indexes for ProHub integration (using internId instead of userId)"""
    try:
        # Work updates indexes
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        await work_updates.create_index("internId")
        await work_updates.create_index([("internId", 1), ("submittedAt", DESCENDING)])
        await work_updates.create_index([("internId", 1), ("update_date", 1)], unique=True)
        
        # Index for tracking incomplete follow-ups
        await work_updates.create_index([("internId", 1), ("followupCompleted", 1)])
        await work_updates.create_index([("followupCompleted", 1), ("submittedAt", DESCENDING)])
        
        # Temporary work updates indexes (non-TTL indexes)
        temp_work_updates = database.database[TEMP_WORK_UPDATES_COLLECTION]
        await temp_work_updates.create_index("internId")
        await temp_work_updates.create_index([("internId", 1), ("update_date", 1)], unique=True)
        await temp_work_updates.create_index([("submittedAt", 1), ("status", 1)])
        
        # Followup sessions indexes using internId
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        # IMPORTANT: Drop old userId-based indexes first
        try:
            existing_indexes = await followup_sessions.list_indexes().to_list(length=None)
            for index in existing_indexes:
                index_name = index.get('name', '')
                if 'userId' in index_name:
                    logger.info(f"Dropping old userId-based index: {index_name}")
                    await followup_sessions.drop_index(index_name)
        except Exception as e:
            logger.warning(f"Could not drop old indexes (may not exist): {e}")
        
        # Create new internId-based indexes
        await followup_sessions.create_index("internId")
        await followup_sessions.create_index([("internId", 1), ("status", 1)])
        await followup_sessions.create_index([("internId", 1), ("createdAt", DESCENDING)])
        
        # FIXED: Create unique index with internId instead of userId
        await followup_sessions.create_index([("internId", 1), ("session_date", 1)], unique=True, name="internId_session_date_unique")
        
        # Index for linking sessions to work updates
        await followup_sessions.create_index("workUpdateId")
        await followup_sessions.create_index("tempWorkUpdateId")
        await followup_sessions.create_index([("workUpdateId", 1), ("status", 1)])
        
        # Compound index for efficient pending session queries
        await followup_sessions.create_index([
            ("internId", 1), 
            ("status", 1), 
            ("createdAt", DESCENDING)
        ])
        
        logger.info("Database indexes created successfully (ProHub integration with internId)")
        
    except Exception as e:
        logger.warning(f"Failed to create indexes: {e}")


# Alternative: Manual index cleanup script
async def cleanup_old_indexes():
    """Manually clean up old userId-based indexes"""
    try:
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        # List all indexes
        existing_indexes = await followup_sessions.list_indexes().to_list(length=None)
        
        logger.info("Current indexes in followup_sessions:")
        for index in existing_indexes:
            logger.info(f"  - {index.get('name')}: {index.get('key')}")
        
        # Drop problematic indexes
        indexes_to_drop = []
        for index in existing_indexes:
            index_name = index.get('name', '')
            if 'userId' in index_name:
                indexes_to_drop.append(index_name)
        
        for index_name in indexes_to_drop:
            if index_name != '_id_':  # Never drop the _id index
                logger.info(f"Dropping old index: {index_name}")
                await followup_sessions.drop_index(index_name)
        
        logger.info("Old userId-based indexes cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Failed to cleanup old indexes: {e}")
        raise

async def migrate_existing_data():
    """Migrate existing work updates to include followupCompleted field and update userId to internId"""
    try:
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        
        # Check if migration is needed
        sample_doc = await work_updates.find_one()
        if sample_doc and "followupCompleted" not in sample_doc:
            logger.info("Migrating existing work updates...")
            
            # Update all existing work updates
            result = await work_updates.update_many(
                {"followupCompleted": {"$exists": False}},
                {"$set": {"followupCompleted": True}}
            )
            
            logger.info(f"Migrated {result.modified_count} existing work updates")
        
        # Migrate userId to internId if needed
        old_user_field_count = await work_updates.count_documents({"userId": {"$exists": True}})
        if old_user_field_count > 0:
            logger.info(f"Migrating {old_user_field_count} documents from userId to internId...")
            
            # Rename userId field to internId
            await work_updates.update_many(
                {"userId": {"$exists": True}},
                {"$rename": {"userId": "internId"}}
            )
            
            logger.info("Migrated userId to internId fields")
        
        # Do the same for temp collection
        temp_collection = database.database[TEMP_WORK_UPDATES_COLLECTION]
        temp_old_user_count = await temp_collection.count_documents({"userId": {"$exists": True}})
        if temp_old_user_count > 0:
            logger.info(f"Migrating {temp_old_user_count} temp documents from userId to internId...")
            await temp_collection.update_many(
                {"userId": {"$exists": True}},
                {"$rename": {"userId": "internId"}}
            )
        
        # Do the same for followup sessions
        sessions_collection = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        sessions_old_user_count = await sessions_collection.count_documents({"userId": {"$exists": True}})
        if sessions_old_user_count > 0:
            logger.info(f"Migrating {sessions_old_user_count} session documents from userId to internId...")
            await sessions_collection.update_many(
                {"userId": {"$exists": True}},
                {"$rename": {"userId": "internId"}}
            )
        
        logger.info("Data migration completed successfully")
        
    except Exception as e:
        logger.warning(f"Failed to migrate data: {e}")

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
        # Keep original status instead of always setting to "completed"
        permanent_update["completedAt"] = datetime.now()
        
        # Check for existing permanent update (override logic)
        # FIXED: Use internId instead of userId
        existing_permanent = await work_updates_collection.find_one({
            "internId": permanent_update["internId"],  # Changed from "userId"
            "update_date": permanent_update["update_date"]
        })
        
        if existing_permanent:
            # Override existing permanent work update
            await work_updates_collection.replace_one(
                {"_id": existing_permanent["_id"]},
                permanent_update
            )
            permanent_id = str(existing_permanent["_id"])
            logger.info(f"Updated existing permanent record: {permanent_id}")
        else:
            # Create new permanent work update
            result = await work_updates_collection.insert_one(permanent_update)
            permanent_id = str(result.inserted_id)
            logger.info(f"Created new permanent record: {permanent_id}")
        
        # Delete temp work update (TTL will also handle this, but immediate cleanup is better)
        delete_result = await temp_collection.delete_one({"_id": ObjectId(temp_id)})
        
        if delete_result.deleted_count > 0:
            logger.info(f"Moved temp work update {temp_id} to permanent {permanent_id}")
        else:
            logger.warning(f"Temp work update {temp_id} might have already been deleted by TTL")
        
        return permanent_id
    
    except Exception as e:
        logger.error(f"Failed to move temp to permanent: {e}")
        raise
    
async def cleanup_abandoned_temp_updates(hours_old: int = 24):
    """Clean up temporary work updates older than specified hours and their associated sessions"""
    try:
        temp_collection = database.database[TEMP_WORK_UPDATES_COLLECTION]
        followup_sessions = database.database[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        
        # Find abandoned temp updates
        abandoned_cursor = temp_collection.find({
            "submittedAt": {"$lt": cutoff_time},
            "status": "pending_followup"
        })
        
        abandoned_count = 0
        deleted_sessions_count = 0
        
        async for temp_update in abandoned_cursor:
            temp_id = str(temp_update["_id"])
            
            # Clean up any associated sessions
            session_delete_result = await followup_sessions.delete_many({
                "$or": [
                    {"tempWorkUpdateId": temp_id},
                    {"workUpdateId": temp_id}
                ]
            })
            
            deleted_sessions_count += session_delete_result.deleted_count
            
            # Delete the temp update
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

def get_database():
    """Get database instance"""
    return database.database

def get_temp_collection():
    """Get temporary work updates collection"""
    return database.database[TEMP_WORK_UPDATES_COLLECTION]

async def create_temp_work_update(work_update_data: dict) -> str:
    """Create temporary work update with internId support"""
    try:
        temp_collection = get_temp_collection()
        
        # Check for existing temp update for same intern and date
        existing_temp = await temp_collection.find_one({
            "internId": work_update_data["internId"],
            "date": work_update_data["date"]
        })
        
        if existing_temp:
            # Replace existing temp update
            await temp_collection.replace_one(
                {"_id": existing_temp["_id"]},
                work_update_data
            )
            logger.info(f"Replaced existing temp work update for intern {work_update_data['internId']}")
            return str(existing_temp["_id"])
        else:
            # Create new temp update
            result = await temp_collection.insert_one(work_update_data)
            logger.info(f"Created new temp work update for intern {work_update_data['internId']}: {result.inserted_id}")
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
        logger.info(f"Deleted temp work update {temp_id}: {result.deleted_count > 0}")
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Failed to delete temp work update: {e}")
        return False

async def get_work_update_data(intern_id: str, work_update_id: str = None):
    """Get work update data including challenges and plans for AI processing (updated for ProHub)"""
    try:
        work_updates = database.database[Config.WORK_UPDATES_COLLECTION]
        temp_work_updates = database.database[TEMP_WORK_UPDATES_COLLECTION]
        
        if work_update_id:
            # Try permanent collection first
            work_update = await work_updates.find_one({"_id": ObjectId(work_update_id)})
            
            # If not found, try temp collection
            if not work_update:
                work_update = await temp_work_updates.find_one({"_id": ObjectId(work_update_id)})
        else:
            # Get latest work update for intern (check both collections)
            permanent_update = await work_updates.find_one(
                {"internId": intern_id},
                sort=[("submittedAt", DESCENDING)]
            )
            
            temp_update = await temp_work_updates.find_one(
                {"internId": intern_id},
                sort=[("submittedAt", DESCENDING)]
            )
            
            # Choose the most recent one
            if permanent_update and temp_update:
                perm_time = permanent_update.get("submittedAt", datetime.min)
                temp_time = temp_update.get("submittedAt", datetime.min)
                work_update = temp_update if temp_time > perm_time else permanent_update
            else:
                work_update = permanent_update or temp_update
        
        if not work_update:
            return None
        
        # Extract relevant data for AI processing (map LogBook fields)
        data = {
            "description": work_update.get("task", ""),  # Map task to description
            "challenges": work_update.get("progress", ""),  # Map progress to challenges
            "plans": work_update.get("blockers", ""),  # Map blockers to plans
            "user_id": work_update.get("internId"),  # Use internId instead of userId
            "submitted_at": work_update.get("submittedAt")
        }
        
        return data
        
    except Exception as e:
        logger.error(f"Failed to get work update data: {e}")
        return None