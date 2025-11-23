import os
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi import HTTPException
from fastapi import FastAPI
#from slowapi import Limiter
#from slowapi.util import get_remote_address
from config.settings import settings
from apiRouter import api
from middlewares import https_enforcement_middleware
# Initialize logger at the top so it's available everywhere 
from logger.loggerFactory import logger_factory
logger = logger_factory.get_logger('main')

# ========== START - VARIABLES SECTION ========== #
SERVICE_NAME = settings.get('APP_NAME')
# HTTPs enforcement and allowed hosts from config
ENFORCE_HTTPS = settings.get('ENFORCE_HTTPS')
ALLOWED_HOSTS = settings.get('ALLOWED_HOSTS').split(',')
# ========== END - VARIABLES SECTION ========== #

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to initialize Windfire Calendar on startup
    """
    try:
        logger.info("Windfire Calendar service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Windfire Calendar service: {str(e)}")
    yield
    # Add shutdown/cleanup logic here if needed

def initiate_app():
    global ENFORCE_HTTPS
    logger.debug("Windfire Calendar initiate_app() called...")
    
    app = FastAPI(
        title=SERVICE_NAME,
        summary="A secured REST API for Google Calendar operations",
        version="1.0.0",
        lifespan=lifespan,
        redirect_slashes=False
    )
    
    origins=ALLOWED_HOSTS
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # tweak this to see the most efficient size
    app.add_middleware(GZipMiddleware, minimum_size=100)

    ######################################################################
    ################### START - TLS/SSL Configurations ###################
    ######################################################################
    # Log security configuration on startup
    logger.debug(f"ENFORCE_HTTPS set to: {ENFORCE_HTTPS}")
    if ENFORCE_HTTPS == True:
        logger.info("🔒 HTTPS enforcement enabled - all HTTP requests will be redirected to HTTPS")
    else:
        logger.warning("⚠️  HTTPS enforcement disabled - API accessible via HTTP (not recommended for production)")

    # Custom HTTPS enforcement middleware
    @app.middleware("http")
    async def custom_https_middleware(request: Request, call_next):
        return await https_enforcement_middleware(request, call_next)

    # Add trusted host middleware if configured
    if ALLOWED_HOSTS and ALLOWED_HOSTS != ['*']:
        logger.info(f"🛡️  Trusted hosts configured: {ALLOWED_HOSTS}")
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=ALLOWED_HOSTS)
    ######################################################################
    ################### END - TLS/SSL Configurations ###################
    ######################################################################

    #app.add_middleware(BaseHTTPMiddleware, dispatch=log_request_middleware)

    #limiter = Limiter(key_func=get_remote_address)
    #app.state.limiter = limiter

    app.include_router(api)
    return app

app = initiate_app()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "path": request.url.path,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "path": request.url.path,
        },
    )

@app.get("/", tags=["Root"])
async def root():
    return RedirectResponse("/docs")

#################################
##### Main program function #####
#################################
def main():
    global ENFORCE_HTTPS
    logger.info(f"Starting {SERVICE_NAME} server...")
    host=settings.get('API_HOST')
    port=settings.get('API_PORT')
    
    # Get SSL configuration from settings
    ssl_keyfile = settings.get('SSL_KEYFILE')
    ssl_certfile = settings.get('SSL_CERTFILE')
    
    # Determine if SSL is configured
    use_ssl = ssl_keyfile and ssl_certfile

    if ENFORCE_HTTPS and use_ssl:
        if not os.path.exists(ssl_keyfile):
            logger.error(f"SSL key file not found: {ssl_keyfile}")
            exit(1)
        if not os.path.exists(ssl_certfile):
            logger.error(f"SSL certificate file not found: {ssl_certfile}")
            exit(1)
        
        port=settings.get('API_PORT_SECURE')
        logger.info(f"🔒 Starting server with HTTPS on {host}:{port}")
        logger.info(f"   SSL Key: {ssl_keyfile}")
        logger.info(f"   SSL Cert: {ssl_certfile}")
        # Start Uvicorn with SSL
        uvicorn.run(app, host=host, port=port, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)
    else:
        if ENFORCE_HTTPS:
            logger.warning("⚠️  ENFORCE_HTTPS is enabled but no SSL certificates configured!")
            logger.warning("   Set SSL_KEYFILE and SSL_CERTFILE environment variables")
            logger.warning("   or disable ENFORCE_HTTPS for development")
        
        logger.info(f"🌐 Starting server with HTTP on {host}:{port}")
        logger.warning("⚠️  Running without TLS/SSL - not recommended for production")
        # Start Uvicorn without SSL 
        uvicorn.run(app, host=host, port=port)

################### MAIN PROGRAM EXECUTION ###################
if __name__ == "__main__":
    main()