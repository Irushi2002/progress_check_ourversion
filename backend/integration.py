# import httpx
# import logging
# from typing import Optional, Dict, Any, List
# from datetime import datetime
# from config import Config  # Import Config

# logger = logging.getLogger(__name__)

# class ProHubIntegration:
#     """
#     Integration service for ProHub API to fetch trainee information
#     Handles authentication and caching for better performance
#     """
    
#     def __init__(self):
#         self.prohub_api_url = Config.PROHUB_API_URL  # Use Config
#         self.timeout = Config.PROHUB_API_TIMEOUT  # Use Config
#         self.cache_duration = Config.PROHUB_CACHE_DURATION  # Use Config
#         self._trainees_cache = None
#         self._cache_timestamp = None
        
#     async def fetch_all_trainees(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
#         """
#         Fetch all active trainees from ProHub API with caching
        
#         Args:
#             force_refresh: Force refresh cache even if not expired
            
#         Returns:
#             List of trainee dictionaries
#         """
#         try:
#             # Check cache first
#             if not force_refresh and self._is_cache_valid():
#                 logger.info("Using cached trainees data")
#                 return self._trainees_cache
            
#             logger.info("Fetching trainees from ProHub API...")
            
#             async with httpx.AsyncClient(timeout=self.timeout) as client:
#                 response = await client.get(self.prohub_api_url)
#                 response.raise_for_status()
                
#                 trainees_data = response.json()
                
#                 # Cache the data
#                 self._trainees_cache = trainees_data
#                 self._cache_timestamp = datetime.now()
                
#                 logger.info(f"Successfully fetched {len(trainees_data)} trainees from ProHub API")
#                 return trainees_data
                
#         except httpx.TimeoutException:
#             logger.error("ProHub API request timed out")
#             raise ProHubIntegrationError("ProHub API request timed out")
#         except httpx.HTTPStatusError as e:
#             logger.error(f"ProHub API returned error: {e.response.status_code}")
#             raise ProHubIntegrationError(f"ProHub API error: {e.response.status_code}")
#         except Exception as e:
#             logger.error(f"Failed to fetch trainees from ProHub API: {e}")
#             raise ProHubIntegrationError(f"Failed to fetch trainees: {str(e)}")
    
#     def _is_cache_valid(self) -> bool:
#         """Check if cached data is still valid"""
#         if not self._trainees_cache or not self._cache_timestamp:
#             return False
        
#         age = (datetime.now() - self._cache_timestamp).total_seconds()
#         return age < self.cache_duration
    
#     async def find_trainee_by_email(self, email: str) -> Optional[Dict[str, Any]]:
#         """
#         Find trainee by email address
        
#         Args:
#             email: Email address to search for
            
#         Returns:
#             Trainee dictionary if found, None otherwise
#         """
#         try:
#             trainees = await self.fetch_all_trainees()
            
#             # Search for trainee with matching email (case insensitive)
#             email_lower = email.lower().strip()
            
#             for trainee in trainees:
#                 trainee_email = trainee.get('email', '').lower().strip()
#                 if trainee_email == email_lower:
#                     logger.info(f"Found trainee: {trainee.get('name')} ({email})")
#                     return trainee
            
#             logger.warning(f"Trainee not found with email: {email}")
#             return None
            
#         except Exception as e:
#             logger.error(f"Error finding trainee by email {email}: {e}")
#             return None
    
#     async def find_trainee_by_id(self, trainee_id: str) -> Optional[Dict[str, Any]]:
#         """
#         Find trainee by ID
        
#         Args:
#             trainee_id: Trainee ID to search for
            
#         Returns:
#             Trainee dictionary if found, None otherwise
#         """
#         try:
#             trainees = await self.fetch_all_trainees()
            
#             for trainee in trainees:
#                 if str(trainee.get('id')) == str(trainee_id):
#                     return trainee
            
#             return None
            
#         except Exception as e:
#             logger.error(f"Error finding trainee by ID {trainee_id}: {e}")
#             return None
    
#     async def verify_trainee_active(self, email: str) -> bool:
#         """
#         Verify if trainee is active in ProHub system
        
#         Args:
#             email: Email address to verify
            
#         Returns:
#             True if trainee is active, False otherwise
#         """
#         trainee = await self.find_trainee_by_email(email)
#         if not trainee:
#             return False
        
#         # Check if trainee is active (assuming there's a status field)
#         # Adjust this based on actual ProHub API response structure
#         status = trainee.get('status', '').lower()
#         is_active = trainee.get('isActive', True)
        
#         return is_active and status in ['active', 'enrolled', '']
    
#     def extract_trainee_info(self, trainee_data: Dict[str, Any]) -> Dict[str, str]:
#         """
#         Extract relevant trainee information for your system
        
#         Args:
#             trainee_data: Raw trainee data from ProHub API
            
#         Returns:
#             Cleaned trainee info dictionary
#         """
#         return {
#             "intern_id": str(trainee_data.get('id', '')),
#             "email": trainee_data.get('email', '').strip(),
#             "name": trainee_data.get('name', '').strip(),
#             "department": trainee_data.get('department', ''),
#             "batch": trainee_data.get('batch', ''),
#             "status": trainee_data.get('status', 'active'),
#             "prohub_id": str(trainee_data.get('id', ''))
#         }
    
#     async def get_all_active_trainees_summary(self) -> Dict[str, Any]:
#         """
#         Get summary of all active trainees for admin purposes
        
#         Returns:
#             Summary dictionary with counts and basic info
#         """
#         try:
#             trainees = await self.fetch_all_trainees()
            
#             summary = {
#                 "total_trainees": len(trainees),
#                 "active_count": 0,
#                 "departments": {},
#                 "batches": {},
#                 "last_updated": self._cache_timestamp.isoformat() if self._cache_timestamp else None
#             }
            
#             for trainee in trainees:
#                 # Count active trainees
#                 if trainee.get('isActive', True):
#                     summary["active_count"] += 1
                
#                 # Count by department
#                 dept = trainee.get('department', 'Unknown')
#                 summary["departments"][dept] = summary["departments"].get(dept, 0) + 1
                
#                 # Count by batch
#                 batch = trainee.get('batch', 'Unknown')
#                 summary["batches"][batch] = summary["batches"].get(batch, 0) + 1
            
#             return summary
            
#         except Exception as e:
#             logger.error(f"Error getting trainees summary: {e}")
#             return {
#                 "error": str(e),
#                 "total_trainees": 0,
#                 "active_count": 0,
#                 "departments": {},
#                 "batches": {}
#             }


# class ProHubIntegrationError(Exception):
#     """Custom exception for ProHub integration errors"""
#     pass


# # Singleton instance for reuse across the application
# _prohub_integration = None

# def get_prohub_integration() -> ProHubIntegration:
#     """Get singleton instance of ProHub integration"""
#     global _prohub_integration
#     if _prohub_integration is None:
#         _prohub_integration = ProHubIntegration()
#     return _prohub_integration


# # Authentication middleware integration
# async def authenticate_via_prohub_email(email: str) -> Optional[Dict[str, str]]:
#     """
#     Authenticate user via ProHub API using email
#     This replaces manual intern ID entry
    
#     Args:
#         email: User's email from Google Auth
        
#     Returns:
#         User info dictionary if authenticated, None otherwise
#     """
#     try:
#         integration = get_prohub_integration()
        
#         # Find trainee in ProHub system
#         trainee = await integration.find_trainee_by_email(email)
        
#         if not trainee:
#             logger.warning(f"User not found in ProHub system: {email}")
#             return None
        
#         # Verify trainee is active
#         if not await integration.verify_trainee_active(email):
#             logger.warning(f"Inactive trainee attempted access: {email}")
#             return None
        
#         # Extract and return user info
#         user_info = integration.extract_trainee_info(trainee)
#         logger.info(f"ProHub authentication successful for: {user_info['name']} ({email})")
        
#         return user_info
        
#     except ProHubIntegrationError as e:
#         logger.error(f"ProHub integration error during auth for {email}: {e}")
#         return None
#     except Exception as e:
#         logger.error(f"Unexpected error during ProHub auth for {email}: {e}")
#         return None


# # Health check functions
# async def check_prohub_api_health() -> Dict[str, Any]:
#     """
#     Check ProHub API health and connectivity
    
#     Returns:
#         Health status dictionary
#     """
#     try:
#         integration = get_prohub_integration()
#         start_time = datetime.now()
        
#         # Try to fetch trainees (will use cache if available)
#         trainees = await integration.fetch_all_trainees()
        
#         response_time = (datetime.now() - start_time).total_seconds()
        
#         return {
#             "status": "healthy",
#             "api_url": integration.prohub_api_url,
#             "response_time_seconds": response_time,
#             "trainees_count": len(trainees),
#             "cache_valid": integration._is_cache_valid(),
#             "last_cache_update": integration._cache_timestamp.isoformat() if integration._cache_timestamp else None,
#             "timestamp": datetime.now().isoformat()
#         }
        
#     except Exception as e:
#         return {
#             "status": "unhealthy",
#             "error": str(e),
#             "api_url": integration.prohub_api_url,
#             "response_time_seconds": None,
#             "trainees_count": 0,
#             "cache_valid": False,
#             "timestamp": datetime.now().isoformat()
#         }


# # Utility functions for email validation
# def is_valid_company_email(email: str, allowed_domains: List[str] = None) -> bool:
#     """
#     Validate if email is from allowed company domains
    
#     Args:
#         email: Email to validate
#         allowed_domains: List of allowed domains (e.g., ['company.com', 'company.lk'])
        
#     Returns:
#         True if email is from allowed domain
#     """
#     if not email or '@' not in email:
#         return False
    
#     if not allowed_domains:
#         # Default allowed domains - adjust based on your company
#         allowed_domains = ['slt.com.lk', 'mobitel.lk', 'company.com']
    
#     domain = email.split('@')[1].lower()
#     return domain in [d.lower() for d in allowed_domains]


# def extract_name_from_email(email: str) -> str:
#     """
#     Extract a display name from email address
    
#     Args:
#         email: Email address
        
#     Returns:
#         Display name
#     """
#     if "@" in email:
#         local_part = email.split("@")[0]
#         # Convert dots/underscores to spaces and title case
#         name = local_part.replace(".", " ").replace("_", " ").title()
#         return name
#     return "Trainee"


import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import Config  # Import Config

logger = logging.getLogger(__name__)

class ProHubIntegration:
    """
    Integration service for ProHub API to fetch trainee information
    Handles authentication and caching for better performance
    """
    
    def __init__(self):
        self.prohub_api_url = Config.PROHUB_API_URL  # Use Config
        self.timeout = Config.PROHUB_API_TIMEOUT  # Use Config
        self.cache_duration = Config.PROHUB_CACHE_DURATION  # Use Config
        self._trainees_cache = None
        self._cache_timestamp = None
        
    async def fetch_all_trainees(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch all active trainees from ProHub API with caching
        
        Args:
            force_refresh: Force refresh cache even if not expired
            
        Returns:
            List of trainee dictionaries
        """
        try:
            # Check cache first
            if not force_refresh and self._is_cache_valid():
                logger.info("Using cached trainees data")
                return self._trainees_cache
            
            logger.info("Fetching trainees from ProHub API...")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 🔥 FIX: Change from GET to POST request
                # The ProHub API expects POST, not GET
                # headers = {
                #     'Content-Type': 'application/json',
                #     'Accept': 'application/json'
                # }
                headers = {
                       'Content-Type': 'application/json',
                       'Accept': 'application/json',
                       'Authorization': f'Bearer {Config.PROHUB_API_KEY}'
                  }
                
                # Try POST request first (most likely correct)
                try:
                    response = await client.post(
                        self.prohub_api_url,
                        headers=headers,
                        json={}  # Empty JSON payload for POST
                    )
                    response.raise_for_status()
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 405:
                        # If POST still fails with 405, try GET with proper headers
                        logger.info("POST failed with 405, trying GET with headers...")
                        response = await client.get(
                            self.prohub_api_url,
                            headers=headers
                        )
                        response.raise_for_status()
                    else:
                        raise
                
                trainees_data = response.json()
                
                # Handle different response structures
                if isinstance(trainees_data, dict):
                    # If response is wrapped in an object, extract the array
                    if 'data' in trainees_data:
                        trainees_data = trainees_data['data']
                    elif 'trainees' in trainees_data:
                        trainees_data = trainees_data['trainees']
                    elif 'result' in trainees_data:
                        trainees_data = trainees_data['result']
                    else:
                        # If it's a dict but not wrapped, convert to array
                        trainees_data = [trainees_data]
                
                # Ensure we have a list
                if not isinstance(trainees_data, list):
                    trainees_data = []
                
                # Cache the data
                self._trainees_cache = trainees_data
                self._cache_timestamp = datetime.now()
                
                logger.info(f"Successfully fetched {len(trainees_data)} trainees from ProHub API")
                return trainees_data
                
        except httpx.TimeoutException:
            logger.error("ProHub API request timed out")
            raise ProHubIntegrationError("ProHub API request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"ProHub API returned error: {e.response.status_code} - {e.response.text}")
            raise ProHubIntegrationError(f"ProHub API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Failed to fetch trainees from ProHub API: {e}")
            raise ProHubIntegrationError(f"Failed to fetch trainees: {str(e)}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self._trainees_cache or not self._cache_timestamp:
            return False
        
        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self.cache_duration
    
    async def find_trainee_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find trainee by email address
        
        Args:
            email: Email address to search for
            
        Returns:
            Trainee dictionary if found, None otherwise
        """
        try:
            trainees = await self.fetch_all_trainees()
            
            # Search for trainee with matching email (case insensitive)
            email_lower = email.lower().strip()
            
            for trainee in trainees:
                # Handle different email field names from ProHub API
                trainee_email = ""
                for email_field in ['email', 'Email', 'emailAddress', 'mail']:
                    if email_field in trainee:
                        trainee_email = trainee.get(email_field, '').lower().strip()
                        break
                
                if trainee_email == email_lower:
                    logger.info(f"Found trainee: {trainee.get('name', trainee.get('Name', 'Unknown'))} ({email})")
                    return trainee
            
            logger.warning(f"Trainee not found with email: {email}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding trainee by email {email}: {e}")
            return None
    
    async def find_trainee_by_id(self, trainee_id: str) -> Optional[Dict[str, Any]]:
        """
        Find trainee by ID
        
        Args:
            trainee_id: Trainee ID to search for
            
        Returns:
            Trainee dictionary if found, None otherwise
        """
        try:
            trainees = await self.fetch_all_trainees()
            
            for trainee in trainees:
                # Handle different ID field names
                for id_field in ['id', 'Id', 'ID', 'traineeId', 'TraineeId']:
                    if id_field in trainee and str(trainee.get(id_field)) == str(trainee_id):
                        return trainee
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding trainee by ID {trainee_id}: {e}")
            return None
    
    async def verify_trainee_active(self, email: str) -> bool:
        """
        Verify if trainee is active in ProHub system
        
        Args:
            email: Email address to verify
            
        Returns:
            True if trainee is active, False otherwise
        """
        trainee = await self.find_trainee_by_email(email)
        if not trainee:
            return False
        
        # Check various status fields (ProHub might use different field names)
        status_fields = ['status', 'Status', 'isActive', 'IsActive', 'active', 'Active']
        
        for field in status_fields:
            if field in trainee:
                value = trainee.get(field)
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ['active', 'enrolled', 'true', '1', 'yes']
        
        # If no status field found, assume active
        return True
    
    def extract_trainee_info(self, trainee_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract relevant trainee information for your system
        
        Args:
            trainee_data: Raw trainee data from ProHub API
            
        Returns:
            Cleaned trainee info dictionary
        """
        # Handle different field name variations from ProHub API
        intern_id = ""
        for id_field in ['id', 'Id', 'ID', 'traineeId', 'TraineeId']:
            if id_field in trainee_data:
                intern_id = str(trainee_data.get(id_field, ''))
                break
        
        email = ""
        for email_field in ['email', 'Email', 'emailAddress', 'mail']:
            if email_field in trainee_data:
                email = trainee_data.get(email_field, '').strip()
                break
        
        name = ""
        for name_field in ['name', 'Name', 'fullName', 'FullName', 'trainee_name']:
            if name_field in trainee_data:
                name = trainee_data.get(name_field, '').strip()
                break
        
        return {
            "intern_id": intern_id,
            "email": email,
            "name": name or extract_name_from_email(email),
            "department": trainee_data.get('department', trainee_data.get('Department', '')),
            "batch": trainee_data.get('batch', trainee_data.get('Batch', '')),
            "status": trainee_data.get('status', trainee_data.get('Status', 'active')),
            "prohub_id": intern_id
        }
    
    async def get_all_active_trainees_summary(self) -> Dict[str, Any]:
        """
        Get summary of all active trainees for admin purposes
        
        Returns:
            Summary dictionary with counts and basic info
        """
        try:
            trainees = await self.fetch_all_trainees()
            
            summary = {
                "total_trainees": len(trainees),
                "active_count": 0,
                "departments": {},
                "batches": {},
                "last_updated": self._cache_timestamp.isoformat() if self._cache_timestamp else None
            }
            
            for trainee in trainees:
                # Count active trainees
                if self._is_trainee_active(trainee):
                    summary["active_count"] += 1
                
                # Count by department
                dept = trainee.get('department', trainee.get('Department', 'Unknown'))
                summary["departments"][dept] = summary["departments"].get(dept, 0) + 1
                
                # Count by batch
                batch = trainee.get('batch', trainee.get('Batch', 'Unknown'))
                summary["batches"][batch] = summary["batches"].get(batch, 0) + 1
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting trainees summary: {e}")
            return {
                "error": str(e),
                "total_trainees": 0,
                "active_count": 0,
                "departments": {},
                "batches": {}
            }
    
    def _is_trainee_active(self, trainee: Dict[str, Any]) -> bool:
        """Helper method to check if a single trainee is active"""
        status_fields = ['status', 'Status', 'isActive', 'IsActive', 'active', 'Active']
        
        for field in status_fields:
            if field in trainee:
                value = trainee.get(field)
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ['active', 'enrolled', 'true', '1', 'yes']
        
        return True  # Default to active if no status field


class ProHubIntegrationError(Exception):
    """Custom exception for ProHub integration errors"""
    pass


# Singleton instance for reuse across the application
_prohub_integration = None

def get_prohub_integration() -> ProHubIntegration:
    """Get singleton instance of ProHub integration"""
    global _prohub_integration
    if _prohub_integration is None:
        _prohub_integration = ProHubIntegration()
    return _prohub_integration


# Authentication middleware integration
async def authenticate_via_prohub_email(email: str) -> Optional[Dict[str, str]]:
    """
    Authenticate user via ProHub API using email
    This replaces manual intern ID entry
    
    Args:
        email: User's email from Google Auth
        
    Returns:
        User info dictionary if authenticated, None otherwise
    """
    try:
        integration = get_prohub_integration()
        
        # Find trainee in ProHub system
        trainee = await integration.find_trainee_by_email(email)
        
        if not trainee:
            logger.warning(f"User not found in ProHub system: {email}")
            return None
        
        # Verify trainee is active
        if not await integration.verify_trainee_active(email):
            logger.warning(f"Inactive trainee attempted access: {email}")
            return None
        
        # Extract and return user info
        user_info = integration.extract_trainee_info(trainee)
        logger.info(f"ProHub authentication successful for: {user_info['name']} ({email})")
        
        return user_info
        
    except ProHubIntegrationError as e:
        logger.error(f"ProHub integration error during auth for {email}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during ProHub auth for {email}: {e}")
        return None


# Health check functions
async def check_prohub_api_health() -> Dict[str, Any]:
    """
    Check ProHub API health and connectivity
    
    Returns:
        Health status dictionary
    """
    try:
        integration = get_prohub_integration()
        start_time = datetime.now()
        
        # Try to fetch trainees (will use cache if available)
        trainees = await integration.fetch_all_trainees()
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "healthy",
            "api_url": integration.prohub_api_url,
            "response_time_seconds": response_time,
            "trainees_count": len(trainees),
            "cache_valid": integration._is_cache_valid(),
            "last_cache_update": integration._cache_timestamp.isoformat() if integration._cache_timestamp else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "api_url": getattr(get_prohub_integration(), 'prohub_api_url', 'Unknown'),
            "response_time_seconds": None,
            "trainees_count": 0,
            "cache_valid": False,
            "timestamp": datetime.now().isoformat()
        }


# Utility functions for email validation
def is_valid_company_email(email: str, allowed_domains: List[str] = None) -> bool:
    """
    Validate if email is from allowed company domains
    
    Args:
        email: Email to validate
        allowed_domains: List of allowed domains (e.g., ['company.com', 'company.lk'])
        
    Returns:
        True if email is from allowed domain
    """
    if not email or '@' not in email:
        return False
    
    if not allowed_domains:
        # Default allowed domains - adjust based on your company
        allowed_domains = ['slt.com.lk', 'mobitel.lk', 'company.com']
    
    domain = email.split('@')[1].lower()
    return domain in [d.lower() for d in allowed_domains]


def extract_name_from_email(email: str) -> str:
    """
    Extract a display name from email address
    
    Args:
        email: Email address
        
    Returns:
        Display name
    """
    if "@" in email:
        local_part = email.split("@")[0]
        # Convert dots/underscores to spaces and title case
        name = local_part.replace(".", " ").replace("_", " ").title()
        return name
    return "Trainee"