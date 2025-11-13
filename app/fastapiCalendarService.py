import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from service import calendarService
from contextlib import asynccontextmanager
from typing import Optional
# Import the AuthClient instance from the client package
from client.authClient import authClient

# Initialize logger at the top so it's available everywhere
from logger.loggingFactory import logger_factory
logger = logger_factory.get_logger('calendar_api')

# Load configuration 
from config.config_reader import config

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

#######################################################################
################### START - Security Configurations ###################
#######################################################################
# Instantiates FastAPI’s HTTPBearer dependency 
# It extracts a Bearer token from the Authorization header of incoming requests. 
security = HTTPBearer()
# HTTPs enforcement and allowed hosts from config
ENFORCE_HTTPS = config.get('ENFORCE_HTTPS')
ALLOWED_HOSTS = config.get('ALLOWED_HOSTS').split(',')

# Custom HTTPS enforcement middleware
@app.middleware("http")
async def https_enforcement_middleware(request: Request, call_next):
    """
    Custom middleware to enforce HTTPS with exceptions for health checks
    """
    logger.debug(f"Custom middleware to enforce HTTPS with exceptions for health checks")
    # Skip HTTPS check for health endpoint (useful for load balancers)
    if request.url.path == "/health":
        logger.debug("Health check endpoint accessed, skipping HTTPS enforcement")
        response = await call_next(request)
        return response
    
    # Check if HTTPS enforcement is enabled
    if ENFORCE_HTTPS == True:
        # Check if request is HTTPS
        # Note: When behind a proxy/load balancer, check X-Forwarded-Proto header
        logger.debug(f"ENFORCE_HTTPS is {ENFORCE_HTTPS}. Checking if request is HTTPS ...")
        is_https = (
            request.url.scheme == "https" or
            request.headers.get("x-forwarded-proto") == "https" or
            request.headers.get("x-forwarded-ssl") == "on"
        )
        
        if not is_https:
            # Redirect HTTP to HTTPS
            logger.debug(f"Request is not HTTPS, redirecting HTTP to HTTPS")
            https_url = str(request.url).replace("http://", "https://", 1)
            logger.warning(f"🔒 Redirecting HTTP to HTTPS: {request.url.path}")
            return RedirectResponse(url=https_url, status_code=307)
    
    response = await call_next(request)
    
    # Add security headers to all responses
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

# Add trusted host middleware if configured
if ALLOWED_HOSTS and ALLOWED_HOSTS != ['*']:
    logger.info(f"🛡️  Trusted hosts configured: {ALLOWED_HOSTS}")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

# Log security configuration on startup
logger.debug(f"ENFORCE_HTTPS set to: {ENFORCE_HTTPS}")
if ENFORCE_HTTPS == True:
    logger.info("🔒 HTTPS enforcement enabled - all HTTP requests will be redirected to HTTPS")
else:
    logger.warning("⚠️  HTTPS enforcement disabled - API accessible via HTTP (not recommended for production)")
#####################################################################
################### END - Security Configurations ###################
#####################################################################

#################################################################################
################### START - AUTHENTICATION TOKEN VERIFICATION ###################
#################################################################################
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify token by calling the external verification endpoint
    token = credentials.credentials
    service = config.get("KEYCLOAK_SERVICE")
    logger.info("Delegating token verification to authClient module ...")
    logger.debug("Calling client.authClient.verify() ...")
    isTokenValid = authClient.verify(token, service=service, method="remote")

    if not isTokenValid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Token verified successfully for service: {service}")
    return token
###############################################################################
################### END - AUTHENTICATION TOKEN VERIFICATION ###################
###############################################################################

#####################################################################################
################### START - ENDPOINTS AND REQUEST/RESPONSE MODELS ###################
#####################################################################################
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
###################################################################################
################### END - ENDPOINTS AND REQUEST/RESPONSE MODELS ###################
###################################################################################

################### MAIN PROGRAM EXECUTION ###################
if __name__ == "__main__":
    logger.info("Starting Windfire Calendar FastAPI server...")
    # Get SSL configuration from environment variables
    ssl_keyfile = config.get('SSL_KEYFILE')
    ssl_certfile = config.get('SSL_CERTFILE')
    host=config.get('API_HOST')
    port = int(config.get('API_PORT'))
    
    # Determine if SSL is configured
    use_ssl = ssl_keyfile and ssl_certfile

    if use_ssl:
        if not os.path.exists(ssl_keyfile):
            logger.error(f"SSL key file not found: {ssl_keyfile}")
            exit(1)
        if not os.path.exists(ssl_certfile):
            logger.error(f"SSL certificate file not found: {ssl_certfile}")
            exit(1)
        
        logger.info(f"🔒 Starting server with HTTPS on {host}:{port}")
        logger.info(f"   SSL Key: {ssl_keyfile}")
        logger.info(f"   SSL Cert: {ssl_certfile}")
        
        uvicorn.run(app, host=host, port=port, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)
    else:
        if ENFORCE_HTTPS:
            logger.warning("⚠️  ENFORCE_HTTPS is enabled but no SSL certificates configured!")
            logger.warning("   Set SSL_KEYFILE and SSL_CERTFILE environment variables")
            logger.warning("   or disable ENFORCE_HTTPS for development")
        
        logger.info(f"🌐 Starting server with HTTP on {host}:{port}")
        logger.warning("⚠️  Running without SSL - not recommended for production")
        
        uvicorn.run(app, host=host, port=port)