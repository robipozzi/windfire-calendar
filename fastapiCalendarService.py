from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloakAuth import KeycloakAuth, KeycloakAuthError
import uvicorn
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from service import calendarService
from log import loggingFactory
from contextlib import asynccontextmanager
from typing import Optional

SERVICE_NAME = "Windfire Calendar Service API"
# Startup is now managed by the lifespan context manager defined below.
@asynccontextmanager
async def lifespan(app):
    """
    Lifespan event handler to initialize Google Calendar authentication on startup
    """
    try:
        # The calendarService module automatically authenticates on import
        logger.info("Google Calendar service initialized successfully")
        logger.debug(f"Auth = {auth.__dict__}")
    except Exception as e:
        logger.error(f"Failed to initialize Google Calendar service: {str(e)}")
    yield
    # Add shutdown/cleanup logic here if needed

# Initialize FastAPI app
app = FastAPI(
    title=SERVICE_NAME,
    description="A secured REST API for Google Calendar operations",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# Initialize logger at the top so it's available everywhere
logger = loggingFactory.get_logger('calendar_api')

# Security
security = HTTPBearer()
auth = KeycloakAuth()

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

class KeycloakLoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class KeycloakTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    refresh_expires_in: Optional[int] = None
    scope: Optional[str] = None

################### KEYCLOAK AUTHENTICATION ENDPOINT INTEGRATION PLACEHOLDER ###################
# Authentication endpoint
@app.post("/auth", response_model=KeycloakTokenResponse)
async def keycloak_login(login_request: KeycloakLoginRequest):
    """
    Authenticate with Keycloak and receive tokens
    
    Args:
        login_request: Username and password
        
    Returns:
        Access token and refresh token
    """
    logger.info(f"Keycloak login attempt for user: {login_request.username}")
    try:
        # Authenticate with Keycloak
        token_response = auth.authenticate_with_password(
            login_request.username,
            login_request.password
        )
        
        logger.info(f"User {login_request.username} authenticated successfully with Keycloak")
        
        return KeycloakTokenResponse(
            access_token=token_response.get('access_token'),
            token_type="Bearer",
            expires_in=token_response.get('expires_in', 0),
            refresh_token=token_response.get('refresh_token'),
            refresh_expires_in=token_response.get('refresh_expires_in'),
            scope=token_response.get('scope')
        )
        
    except KeycloakAuthError as e:
        logger.warning(f"Keycloak authentication failed for user {login_request.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    except Exception as e:
        logger.error(f"Keycloak authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token_claims = auth.verify_token_locally(credentials.credentials)
        return token_claims
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
################### KEYCLOAK AUTHENTICATION ENDPOINT INTEGRATION PLACEHOLDER ###################

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
                description=event.get('description')
            )
            formatted_events.append(formatted_event)
        
        return UpcomingEventsResponse(events=formatted_events, count=len(formatted_events))
    except Exception as e:
        logger.error(f"Failed to get upcoming events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get upcoming events: {str(e)}")

# Initialize the calendar service authentication on startup
# @app.on_event("startup")
# async def startup_event():
#     """
#     Startup event handler to initialize Google Calendar authentication on startup
#     """
#     try:
#         # The calendarService module automatically authenticates on import
#         logger.info("Google Calendar service initialized successfully")
#     except Exception as e:
#         logger.error(f"Failed to initialize Google Calendar service: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)