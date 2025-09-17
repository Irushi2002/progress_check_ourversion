import google.generativeai as genai
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any, Optional
import logging
import re
import math
from dateutil import parser
from pymongo import DESCENDING

from config import Config
from database import get_database
from models import SessionStatus

logger = logging.getLogger(__name__)

class AIFollowupService:
    def __init__(self):
        "Initialize AI service with Gemini model"
        if not Config.GOOGLE_API_KEY:
            raise ValueError("Google API key is required")
            
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        self.db = get_database()
        
    async def generate_followup_questions(self, user_id: str, work_update_data: Optional[Dict[str, Any]] = None) -> List[str]:
        "Generate follow-up questions based on current work update and history"
        try:
            logger.info(f"Starting AI question generation for user: {user_id}")
            
            # Get user's recent work updates (last 7 days) for context
            week_ago = datetime.now() - timedelta(days=7)
            
            # Query BOTH permanent AND temporary collections
            work_updates_collection = self.db[Config.WORK_UPDATES_COLLECTION]
            temp_updates_collection = self.db[Config.TEMP_WORK_UPDATES_COLLECTION]
            
            # Get permanent work updates
            permanent_cursor = work_updates_collection.find({"userId": user_id})
            permanent_updates = await permanent_cursor.to_list(None)
            
            # Get temporary work updates  
            temp_cursor = temp_updates_collection.find({"userId": user_id})
            temp_updates = await temp_cursor.to_list(None)
            
            # Combine both collections
            all_work_updates = permanent_updates + temp_updates
            
            # Filter and sort in memory
            filtered_docs = []
            for doc in all_work_updates:
                timestamp = self._extract_timestamp(doc)
                if timestamp and timestamp > week_ago:
                    filtered_docs.append(doc)
            
            # Sort by timestamp (newest first) and limit to 10
            filtered_docs.sort(key=lambda x: self._extract_timestamp(x) or datetime.min, reverse=True)
            recent_docs = filtered_docs[:10]
            
            logger.info(f"Found {len(recent_docs)} work updates in last 7 days (out of {len(all_work_updates)} total from both collections)")
            
            # Build context from current work update and history
            current_context = self._build_current_work_context(work_update_data) if work_update_data else ""
            history_context = self._build_work_history_context(recent_docs) if recent_docs else ""
            
            # Generate AI prompt
            prompt = self._build_ai_prompt(current_context, history_context, recent_docs)
            
            logger.info("Sending request to Gemini AI...")
            response = self.model.generate_content(prompt)
            
            if response.text and response.text.strip():
                logger.info(f"Received AI response: {response.text[:100]}...")
                questions = self._parse_questions_from_response(response.text)
                
                if len(questions) >= 3:
                    logger.info(f"Successfully generated {len(questions)} AI questions")
                    return questions
                else:
                    logger.warning(f"AI generated only {len(questions)} questions, falling back to defaults")
                    return self._get_default_questions()
            else:
                logger.error("AI response was null or empty, using default questions")
                return self._get_default_questions()
                
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return self._get_default_questions()
    
    def _extract_timestamp(self, doc: Dict[str, Any]) -> Optional[datetime]:
        "Extract timestamp from document"
        timestamp = None
        if 'submittedAt' in doc:
            timestamp = doc['submittedAt']
        elif 'timestamp' in doc:
            timestamp = doc['timestamp']
        elif 'date' in doc:
            date_field = doc['date']
            if isinstance(date_field, datetime):
                timestamp = date_field
            elif isinstance(date_field, str):
                try:
                    timestamp = parser.parse(date_field)
                except Exception as e:
                    logger.warning(f"Error parsing date string: {date_field}")
        return timestamp
    
    def _build_current_work_context(self, work_data: Dict[str, Any]) -> str:
        "Build context string from current work update"
        context_lines = ["CURRENT WORK UPDATE:"]
        
        # Work description (required)
        description = work_data.get('description', '').strip()
        if description:
            context_lines.append(f"Work Description: {description}")
        
        # Challenges (optional)
        challenges = work_data.get('challenges', '').strip() if work_data.get('challenges') else None
        if challenges:
            context_lines.append(f"Challenges Today: {challenges}")
        
       
        
        context_lines.append("---")
        return '\n'.join(context_lines)
    
    def _build_work_history_context(self, docs: List[Dict[str, Any]]) -> str:
        "Build context string from work update history"
        context_lines = ["RECENT WORK HISTORY:"]
        
        for i, doc in enumerate(docs):
            date_time = self._extract_timestamp(doc)
            description = doc.get('description', '').strip()
            challenges = doc.get('challenges', '').strip() if doc.get('challenges') else None
            plans = doc.get('plans', '').strip() if doc.get('plans') else None
            
            date_str = date_time.strftime('%Y-%m-%d') if date_time else 'Unknown'
            
            context_lines.append(f"Date: {date_str}")
            if description:
                context_lines.append(f"Work: {description}")
            if challenges:
                context_lines.append(f"Challenges: {challenges}")
            if plans:
                context_lines.append(f"Plans: {plans}")
            context_lines.append("---")
        
        return '\n'.join(context_lines)
    
    def _build_ai_prompt(self, current_context: str, history_context: str, recent_docs: List[Dict[str, Any]]) -> str:
        "Build AI prompt for question generation"
        
        # Extract data for the prompt template
        today_work_update = current_context
        yesterday_plans = self._extract_yesterday_plans_from_recent_docs(recent_docs)
        current_challenges = self._extract_current_challenges(current_context)
        seven_day_history = history_context

 



        prompt = f"""You're helping a supervisor create simple, easy-to-answer follow-up questions for an intern's daily work update.

**Today's Work:** {today_work_update}
**What They Planned (from yesterday):** {yesterday_plans}
**Current Challenges:** {current_challenges}
**Recent Work History:** {seven_day_history}

Generate exactly 3 simple questions that:
1. Are easy to answer with 1-2 sentences
2. Sound friendly and conversational to understand progress without being demanding
3. Focus on today's work specifically 
4. When says they completed a task,ask them to describe the steps they followed in a general but specific-enough way, so we can understand how the work was approached and verify it was actually done
7. If {yesterday_plans} exists verify {today_work_update} matches {yesterday_plans} naturally .


Avoid questions about:
- Feelings or emotions
- Complex technical details
- Long explanations

Format your response as:
1. [First simple question] 
2. [Second simple question]
3. [Third simple question]"""

        return prompt
        
 
    
    def _extract_yesterday_plans_from_recent_docs(self, recent_docs: List[Dict[str, Any]]) -> str:
        """Extract yesterday's plans from the most recent work update that has plans"""
        if not recent_docs:
            return "No previous plans found"
        
        yesterday = datetime.now().date() - timedelta(days=1)
        
        # First, try to find plans from exactly yesterday
        for doc in recent_docs:
            timestamp = self._extract_timestamp(doc)
            if timestamp and timestamp.date() == yesterday:
                plans = doc.get('plans', '').strip()
                if plans:
                    logger.info(f"Found yesterday's plans from {timestamp.date()}: {plans[:50]}...")
                    return plans
        
        # If no plans found for yesterday, get the most recent plans available
        # (excluding today's entry if it exists)
        today = datetime.now().date()
        
        for doc in recent_docs:
            timestamp = self._extract_timestamp(doc)
            # Skip today's entries
            if timestamp and timestamp.date() == today:
                continue
                
            plans = doc.get('plans', '').strip()
            if plans:
                date_str = timestamp.strftime('%Y-%m-%d') if timestamp else 'Unknown date'
                logger.info(f"Found most recent plans from {date_str}: {plans[:50]}...")
                return plans
        
        logger.info("No previous plans found in recent work updates")
        return "No previous plans found"
    
    def _extract_yesterday_plans_from_history(self, history_context: str) -> str:
        """DEPRECATED: Extract yesterday's plans from history context string - kept for backward compatibility"""
        # This method is now deprecated and replaced by _extract_yesterday_plans_from_recent_docs
        # But keeping it in case it's called elsewhere
        return self._extract_yesterday_plans_from_recent_docs([])
    
    def _extract_current_challenges(self, current_context: str) -> str:
        """Extract current challenges from current work context"""
        lines = current_context.split('\n')
        challenges = "No challenges mentioned"
        
        for line in lines:
            if line.strip().startswith('Challenges Today:'):
                challenges = line.replace('Challenges Today:', '').strip()
                break
        
        return challenges
    
    def _extract_tomorrow_plans(self, current_context: str) -> str:
        """Extract tomorrow's plans from current work context"""
        lines = current_context.split('\n')
        plans = "No plans mentioned"
        
        for line in lines:
            if line.strip().startswith('Plans for Tomorrow:'):
                plans = line.replace('Plans for Tomorrow:', '').strip()
                break
        
        return plans
    
    def _parse_questions_from_response(self, response: str) -> List[str]:
        questions = []
        logger.info("Parsing AI response for questions...")
        logger.info(f"Full AI response: {response}")
        
        # Split by lines
        lines = response.split('\n')
        
        # Method 1: Look for "Question Text" patterns
        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith('**Question Text**'):
                # Extract text after the colon
                question = trimmed.split(':', 1)[-1].strip()
                if question and len(question) > 10:
                    questions.append(question)
                    logger.info(f"Parsed structured question {len(questions)}: {question[:50]}...")
        
        # Method 2: Look for numbered questions if structured format didn't work
        if len(questions) < 3:
            logger.info("Structured format parsing yielded few results, trying numbered format...")
            questions = []  # Reset
            
            for line in lines:
                trimmed = line.strip()
                # Look for lines that start with numbers (1., 2., etc.) or (1), (2), etc.
                if re.match(r'^\d+[.\)]\s*', trimmed):
                    # Remove the number and clean up the question
                    question = re.sub(r'^\d+[.\)]\s*', '', trimmed).strip()
                    # Remove any markdown formatting
                    question = re.sub(r'\*\*.*?\*\*:\s*', '', question)
                    if question and len(question) > 10:
                        questions.append(question)
                        logger.info(f"Parsed numbered question {len(questions)}: {question[:50]}...")
        
        # Method 3: Look for question patterns anywhere in the text
        if len(questions) < 3:
            logger.info("Numbered format parsing yielded few results, trying pattern matching...")
            questions = []  
            
            
            for line in lines:
                trimmed = line.strip()
                # Skip empty lines and headers
                if not trimmed or trimmed.startswith('#') or trimmed.startswith('**') and not trimmed.endswith('?'):
                    continue
                
                # Look for actual questions
                if '?' in trimmed and len(trimmed) > 15:
                    # Clean up the question
                    question = re.sub(r'^\d+[.\)]\s*', '', trimmed)
                    question = re.sub(r'\*\*.*?\*\*:\s*', '', question)
                    question = question.strip()
                    
                    if question and not any(q.lower() in question.lower() for q in questions):
                        questions.append(question)
                        logger.info(f"Parsed pattern question {len(questions)}: {question[:50]}...")
                        
                        if len(questions) >= 3:
                            break
        
        logger.info(f"Total questions parsed: {len(questions)}")
        
        # Ensure exactly 3 questions
        if len(questions) > 3:
            questions = questions[:3]
            logger.info("Trimmed to 3 questions")
        elif len(questions) < 3:
            logger.warning(f"Only {len(questions)} questions parsed after all methods, filling with defaults")
            # Fill with default questions if we don't have enough
            defaults = self._get_default_questions()
            while len(questions) < 3 and len(questions) < len(defaults):
                questions.append(defaults[len(questions)])
        
        return questions
    
    def _get_default_questions(self) -> List[str]:
        """Default questions when AI generation fails"""
        return [
            "What technical challenges did you face this week that you'd like help with?",
            "Have you encountered any bugs or issues that are taking longer than expected to resolve?",
            "What new skills or concepts have you learned recently that you'd like to discuss?"
        ]
    
    async def save_followup_session(self, user_id: str, questions: List[str]) -> str:
        """Save follow-up session to MongoDB"""
        logger.info(f"Called save_followup_session with userId: {user_id}")
        
        try:
            #formatted_date = datetime.now().strftime('%Y-%m-%d')
            #session_id = f"{user_id}_{formatted_date}"
            session_id = f"{user_id}_{uuid.uuid4().hex}"
            
            followup_collection = self.db[Config.FOLLOWUP_SESSIONS_COLLECTION]
            
            session_doc = {
                "_id": session_id,
                "userId": user_id,
                "questions": questions,
                "answers": [""] * len(questions),
                "status": SessionStatus.PENDING,
                "createdAt": datetime.now(),
                "completedAt": None
            }
            
            await followup_collection.replace_one(
                {"_id": session_id}, 
                session_doc, 
                upsert=True
            )
            
            logger.info(f"Follow-up session saved with ID: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to save follow-up session: {e}")
            raise Exception(f"Failed to save follow-up session: {e}")
    
    async def update_followup_answers(self, session_id: str, answers: List[str]) -> None:
        """Update answers for a follow-up session"""
        try:
            followup_collection = self.db[Config.FOLLOWUP_SESSIONS_COLLECTION]
            
            update_doc = {
                "answers": answers,
                "status": SessionStatus.COMPLETED,
                "completedAt": datetime.now()
            }
            
            result = await followup_collection.update_one(
                {"_id": session_id},
                {"$set": update_doc}
            )
            
            if result.modified_count == 0:
                raise Exception(f"Session {session_id} not found")
            
            logger.info(f"Follow-up answers updated for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to update follow-up answers: {e}")
            raise Exception(f"Failed to update follow-up answers: {e}")
    
    async def get_pending_followup_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get pending follow-up session for user"""
        try:
            followup_collection = self.db[Config.FOLLOWUP_SESSIONS_COLLECTION]
            
            cursor = followup_collection.find(
                {
                    "userId": user_id,
                    "status": SessionStatus.PENDING
                }
            ).sort("createdAt", DESCENDING).limit(1)
            
            sessions = await cursor.to_list(1)
            
            if sessions:
                session = sessions[0]
                session_id = session["_id"]
                logger.info(f"Found pending session: {session_id}")
                
                result = {"sessionId": session_id}
                result.update(session)
                return result
            
            logger.info(f"No pending sessions found for user: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting pending follow-up session: {e}")
            return None
    

    
    async def test_ai_connection(self) -> bool:
        """Test method to check if AI is working"""
        try:
            prompt = 'Generate a simple test response: "AI is working"'
            response = self.model.generate_content(prompt)
            logger.info(f"AI Test Response: {response.text}")
            return response.text is not None and response.text.strip()
        except Exception as e:
            logger.error(f"AI Test Failed: {e}")
            return False