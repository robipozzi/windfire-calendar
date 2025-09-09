from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from service import calendarService
import os
import jwt
from jwt.exceptions import InvalidTokenError
from log import loggingFactory

SERVICE_NAME = "Windfire Calendar Service API"
# Initialize FastAPI app
app = FastAPI(
    title=SERVICE_NAME,
    description="A secured REST API for Google Calendar operations",
    version="1.0.0"
)

# Initialize logger at the top so it's available everywhere
logger = loggingFactory.get_logger('calendar_api')

# Security
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

# Pydantic models for request/response
class EventCountRequest(BaseModel):
    event_title: str = Field(..., description="Title of the events to count")
    year: Optional[int] = Field(None, description="Year to count events for")
    start_date: Optional[date] = Field(None, description="Start date for counting events")
    end_date: Optional[date] = Field(None, description="End date for counting events")

class EventCountResponse(BaseModel):
    event_title: str
    count: int
    start_date: str
    end_date: str

class CalendarEvent(BaseModel):
    id: str
    summary: str
    start: dict
    end: dict
    description: Optional[str] = None

class UpcomingEventsResponse(BaseModel):
    events: List[CalendarEvent]
    count: int

class AuthToken(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Mock user database (replace with real authentication in production)
USERS_DB = {
    "admin": {
        "username": "admin",
        "password": "secure_password_123",  # In production, use hashed passwords
        "scopes": ["calendar:read"]
    }
}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token and return user info
    """
    logger.debug(f"====> START - verify_token called <====")
    logger.debug(f"*** Reading token: {credentials.credentials}")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        logger.debug(f"*** Decoded JWT payload: {payload}")
        logger.debug(f"*** Decoded JWT username: {username}")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = USERS_DB.get(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.debug(f"====> END - verify_token called <====")
        return user
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def authenticate_user(username: str, password: str):
    """
    Authenticate user credentials
    """
    logger.debug(f"====> START - authenticate_user called <====")
    user = USERS_DB.get(username)
    if not user or user["password"] != password:
        logger.debug(f"====> END - authenticate_user called <====")
        return False
    logger.debug(f"====> END - authenticate_user called <====")
    return user

def create_access_token(data: dict):
    """
    Create JWT access token
    """
    logger.debug(f"====> START - create_access_token called <====")
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"====> END - create_access_token called <====")
    return encoded_jwt

# Authentication endpoint
@app.post("/auth/token", response_model=TokenResponse)
async def login(auth_data: AuthToken):
    """
    Authenticate and receive JWT token
    """
    logger.debug(f"====> START - /auth/token endpoint called <====")
    user = authenticate_user(auth_data.username, auth_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    logger.debug(f"====> END - /auth/token endpoint called <====")
    return {"access_token": access_token, "token_type": "bearer"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    logger.debug(f"====> /health endpoint called <====")
    return {"status": "healthy", "service": SERVICE_NAME}

# Calendar endpoints
@app.post("/calendar/events/count/year", response_model=EventCountResponse)
async def count_events_by_year(
    request: EventCountRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Count calendar events for a specific year
    """
    if not request.year:
        raise HTTPException(status_code=400, detail="Year is required for this endpoint")
    
    try:
        count = calendarService.countCalendarEventsYear(request.event_title, request.year)
        
        # Determine date range for response
        start_date = date(request.year, 1, 1)
        if request.year == date.today().year:
            end_date = date.today()
        else:
            end_date = date(request.year, 12, 31)
        
        return EventCountResponse(
            event_title=request.event_title,
            count=count,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to count events: {str(e)}")

@app.post("/calendar/events/count/today", response_model=EventCountResponse)
async def count_events_to_today(
    request: EventCountRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Count calendar events from start date to today
    """
    if not request.start_date:
        raise HTTPException(status_code=400, detail="Start date is required for this endpoint")
    
    try:
        count = calendarService.countCalendarEventsToday(request.event_title, request.start_date)
        end_date = date.today()
        
        return EventCountResponse(
            event_title=request.event_title,
            count=count,
            start_date=request.start_date.isoformat(),
            end_date=end_date.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to count events: {str(e)}")

@app.post("/calendar/events/count/range", response_model=EventCountResponse)
async def count_events_by_range(
    request: EventCountRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Count calendar events within a date range
    """
    if not request.start_date or not request.end_date:
        raise HTTPException(status_code=400, detail="Both start_date and end_date are required for this endpoint")
    
    if request.start_date > request.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")
    
    try:
        count = calendarService.countCalendarEvents(request.event_title, request.start_date, request.end_date)
        
        return EventCountResponse(
            event_title=request.event_title,
            count=count,
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to count events: {str(e)}")

@app.get("/calendar/events/upcoming", response_model=UpcomingEventsResponse)
async def get_upcoming_events(current_user: dict = Depends(verify_token)):
    """
    Get the next 10 upcoming calendar events
    """
    logger.debug("====> START - /calendar/events/upcoming endpoint called <====")
    try:
        events = calendarService.getUpcomingEvents()
        
        if not events:
            return UpcomingEventsResponse(events=[], count=0)
        
        # Convert events to our response format
        formatted_events = []
        for event in events:
            formatted_event = CalendarEvent(
                id=event.get('id', ''),
                summary=event.get('summary', 'No Title'),
                start=event.get('start', {}),
                end=event.get('end', {}),
                description=event.get('description', None)
            )
            formatted_events.append(formatted_event)
        logger.debug("====> END - /calendar/events/upcoming endpoint called <====")
        return UpcomingEventsResponse(
            events=formatted_events,
            count=len(formatted_events)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get upcoming events: {str(e)}")

# Initialize the calendar service authentication on startup
@app.on_event("startup")
async def startup_event():
    """
    Initialize Google Calendar authentication on startup
    """
    try:
        # The calendarService module automatically authenticates on import
        logger.info("Google Calendar service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Google Calendar service: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)