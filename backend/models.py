from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum

class SessionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class WorkStatus(str, Enum):
    WORKING = "working"
    LEAVE = "leave"
    WFH = "wfh"  # Work from home

class WorkUpdateCreate(BaseModel):
    stack: str  # Task Stack (required)
    task: str   # Tasks Completed (required) - maps to 'description'
    progress: Optional[str] = "No challenges faced"  # Maps to 'challenges'
    blockers: Optional[str] = "No specific plans"    # Maps to 'plans'
    status: WorkStatus = WorkStatus.WORKING
    submittedAt: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator("stack", "task")
    def check_non_empty(cls, v):
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()

class WorkUpdate(WorkUpdateCreate):
    id: Optional[str] = Field(default=None, alias="_id")
    internId: Optional[str] = Field(default=None)  # Set from auth
    date: Optional[str] = Field(default=None)      # LogBook date field
    followupCompleted: Optional[bool] = Field(default=False)
    session_date_id: Optional[str] = Field(default=None)
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class FollowupSessionCreate(BaseModel):
    workUpdateId: Optional[str] = None
    questions: List[str]
    answers: Optional[List[str]] = Field(default_factory=list)
    status: SessionStatus = SessionStatus.PENDING
    createdAt: Optional[datetime] = Field(default_factory=datetime.utcnow)
    completedAt: Optional[datetime] = None
    session_date: Optional[str] = Field(default=None)

class FollowupSession(FollowupSessionCreate):
    id: Optional[str] = Field(alias="_id")
    internId: Optional[str] = Field(default=None)  # Set from auth
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class FollowupAnswersUpdate(BaseModel):
    answers: List[str]

class GenerateQuestionsRequest(BaseModel):
    pass  # No fields needed - get internId from auth

class GenerateQuestionsResponse(BaseModel):
    questions: List[str]
    sessionId: str

class TestAIResponse(BaseModel):
    success: bool
    message: str


class AnalysisResponse(BaseModel):
    analysis: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Any] = None
