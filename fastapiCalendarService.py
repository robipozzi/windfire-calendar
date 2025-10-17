from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import httpx
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from service import calendarService
import os
import jwt
from jwt.exceptions import InvalidTokenError
#from jwt.algorithms import RSAAlgorithm
from jwt.algorithms import Algorithm
from log import loggingFactory
from contextlib import asynccontextmanager
import requests
from typing import Optional, Dict, Any
import json

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
    lifespan=lifespan
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

def verify_token_OLD(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
# @app.post("/auth", response_model=TokenResponse)
# async def login(auth_data: AuthToken):
#     """
#     Authenticate and receive JWT token
#     """
#     logger.debug(f"====> START - /auth endpoint called <====")
#     user = authenticate_user(auth_data.username, auth_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     
#     access_token = create_access_token(data={"sub": user["username"]})
#     logger.debug(f"====> END - /auth/token endpoint called <====")
#     return {"access_token": access_token, "token_type": "bearer"}

################### KEYCLOAK INTEGRATION PLACEHOLDER ###################
# This is a placeholder for Keycloak integration. In a production
# environment, you would replace the mock authentication and JWT
# handling with actual Keycloak token validation and user management.
########################################################################
class KeycloakAuthRequest(BaseModel):
    username: str
    password: str

class KeycloakTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: Optional[str] = None

def introspect_token(token: str) -> Dict[str, Any]:
        """
        Introspect a token to check its validity and get claims
        
        Args:
            token: Token to introspect
            
        Returns:
            Dict with token information and validity
            
        Raises:
            Exception: If introspection fails or Keycloak is misconfigured
        """
        logger.info("Introspecting token")
        client_id = os.getenv("KEYCLOAK_CLIENT_ID")
        client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET", None)
        keycloak_url = os.getenv("KEYCLOAK_URL")
        realm = os.getenv("KEYCLOAK_REALM")
        jwks_endpoint = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"
        

        if not keycloak_url or not realm:
            logger.error("Keycloak URL or realm not configured")
            raise Exception("Keycloak configuration missing (KEYCLOAK_URL or KEYCLOAK_REALM)")

        # Build payload; use client authentication via HTTP Basic when a client secret is provided.
        payload = {
            'token': token
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        auth = None

        if client_secret:
            # Use HTTP Basic auth per Keycloak best practices for token introspection
            auth = (client_id, client_secret)
        else:
            # For public clients (no secret), include client_id in the form data
            if client_id:
                payload['client_id'] = client_id

        try:
            introspect_endpoint = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token/introspect"
        
            session = requests.Session()
            response = session.post(
                introspect_endpoint,
                data=payload,
                headers=headers,
                auth=auth,
                timeout=10
            )

            # Explicitly handle forbidden/unauthorized responses for clearer logging
            if response.status_code in (401, 403):
                logger.error(f"Token introspection returned {response.status_code}: {response.text}")
                raise Exception(f"Token introspection failed: {response.status_code} {response.text}")

            response.raise_for_status()
            
            introspection = response.json()
            is_active = introspection.get('active', False)
            logger.info(f"Token introspection - Active: {is_active}")
            return introspection
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Token introspection failed: {str(e)}")
            raise
    
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        logger.debug(f"====> START - verify_token called <====")
        
        token_info = introspect_token(credentials.credentials)
        if not token_info.get('active'):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return token_info
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    
# =======================================
def verify_token_locally(token: str = Depends(security)) -> Dict[str, Any]:
        """
        Verify token locally using public keys (no introspection endpoint needed)
        This is the most reliable method as it doesn't require special client permissions
        
        Args:
            token: JWT token to verify
            
        Returns:
            Dict with decoded token claims
            
        Raises:
            KeycloakAuthError: If verification fails
        """
        logger.info("Verifying token locally using public keys")
        
        try:
            # Get unverified header to find kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                raise Exception("Token has no 'kid' in header")
            
            # Get public keys from Keycloak
            jwks = get_public_keys()
            
            # Find the matching public key
            public_key_data = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    public_key_data = key
                    break
            
            if not public_key_data:
                raise Exception(f"Public key with kid '{kid}' not found")
            
            # Convert JWK to PEM format
            #public_key = RSAAlgorithm.from_jwk(json.dumps(public_key_data))
            public_key = Algorithm.from_jwk(json.dumps(public_key_data))
            
            # Decode and verify token
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                options={"verify_signature": True}
            )
            
            logger.info(f"Token verified successfully for user: {decoded_token.get('preferred_username')}")
            return decoded_token
            
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise Exception("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise Exception(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise Exception(f"Token verification error: {str(e)}")
    
def get_public_keys(self) -> Dict[str, Any]:
    """
    Get public keys for token verification (JWKS)
        
    Returns:
        Dict with public keys
            
    Raises:
        KeycloakAuthError: If retrieval fails
    """
    logger.info("Fetching public keys (JWKS)")
    client_id = os.getenv("KEYCLOAK_CLIENT_ID")
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET", None)
    keycloak_url = os.getenv("KEYCLOAK_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    jwks_endpoint = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"
        
    try:
        session = requests.Session()
        response = session.get(
            jwks_endpoint,
            timeout=10
        )
        response.raise_for_status()
            
        keys = response.json()
        logger.info(f"Retrieved {len(keys.get('keys', []))} public keys")
        return keys
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch public keys: {str(e)}")
        raise Exception(f"Failed to fetch public keys: {str(e)}")
# =======================================

@app.post("/auth", response_model=KeycloakTokenResponse)
async def keycloak_login(auth_data: KeycloakAuthRequest, request: Request):
    """
    Authenticate user against Keycloak and return access token
    """
    logger.debug(f"====> START - /auth endpoint called <====")
    keycloak_url = os.getenv("KEYCLOAK_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    client_id = os.getenv("KEYCLOAK_CLIENT_ID")
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET", None)
    logger.debug(f"keycloak_url: {keycloak_url}, realm: {realm}, client_id: {client_id}")

    token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
    logger.debug(f"Keycloak token URL: {token_url}")
    data = {
        "grant_type": "password",
        "client_id": client_id,
        "username": auth_data.username,
        "password": auth_data.password,
    }
    if client_secret:
        data["client_secret"] = client_secret

    #logger.debug(f"Authentication data: {data}")

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            logger.error(f"Keycloak authentication failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Keycloak authentication failed"
            )
        token_data = response.json()
        return KeycloakTokenResponse(
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in"),
            token_type=token_data.get("token_type")
        )
################### KEYCLOAK INTEGRATION PLACEHOLDER ###################

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
    current_user: dict = Depends(verify_token_locally)
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