\# Progress Check AI



\## Description

Intern progress tracking application with AI features



\## Structure

\- `frontend/` - Frontend application  

\- `backend/` - Backend API/services



\## Setup Instructions



\### Frontend

```bash

cd frontend

npm install

npm start


### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

##test with real user
##use valid email
#workupdate
curl -X POST http://127.0.0.1:8000/api/work-updates -H "Content-Type: application/json" -H "X-User-Email: real.trainee@gmail.com" -d "{\"status\":\"working\",\"stack\":\"React\",\"task\":\"Testing API\",\"progress\":\"Testing\",\"blockers\":\"None\"}"

#response
{
"message": "Work update saved temporarily for [Real Name]. Complete AI follow-up within 24 hours to finalize in LogB
"tempWorkUpdateId": "some-generated-id",
"redirectToFollowup": true,
"isOnLeave": false,
"ttl_expiry": "24 hours from now",
"internInfo": {
"name": "Real Trainee Name",
"email": "real.trainee@gmail.com",
"department": "IT"
}
}


#startfollowups
curl -X POST "http://127.0.0.1:8000/api/followups/start?temp_work_update_id=some-generated-id" -H "X-User-Email: real.trainee@gmail.com"

#response
{
"message": "AI follow-up session started for [Real Name]",
"sessionId": "intern_id_uuid",
"questions": [
"What specific challenges did you face today?",
"How did you overcome any obstacles?",
"What are your plans for tomorrow?"
],
"reminder": "Complete within 24 hours before auto-deletion",
"internInfo": {
"name": "Real Trainee Name",
"email": "real.trainee@gmail.com"
}
}


#completefollowups
curl -X PUT http://127.0.0.1:8000/api/followup/sessionId/complete -H "Content-Type: application/json" -H "X-User-Email: real.trainee@gmail.com" -d "{\"answers\":[\"Answer 1\",\"Answer 2\",\"Answer 3\"]}"
#response
{
"message": "AI follow-up completed successfully for [Real Name]. Work update saved to LogBook system.",
"sessionId": "session-id",
"dailyRecordId": "mongodb-record-id",
"workUpdateCompleted": true,
"note": "Work update moved to LogBook DailyRecord collection",
"internInfo": {
"name": "Real Trainee Name",
"email": "real.trainee@gmail.com"
}
}
