from fastapi import HTTPException, status, Depends # pyright: ignore[reportMissingImports]
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # pyright: ignore[reportMissingImports]
from config.settings import settings
# Import the AuthClient instance from the client package
from client.authClient import authClient, AuthServerError
# Initialize logger at the top so it's available everywhere 
from logger.loggerFactory import logger_factory
logger = logger_factory.get_logger('commons')

#################################################################################
################### START - AUTHENTICATION TOKEN VERIFICATION ###################
#################################################################################
# Instantiates FastAPI’s HTTPBearer dependency 
# It extracts a Bearer token from the Authorization header of incoming requests. 
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify token by calling the external verification endpoint
    token = credentials.credentials
    service = settings.get("WINDFIRE_SECURITY_SERVICE")
    logger.info("Delegating token verification to authClient module ...")
    logger.debug("Calling client.authClient.verify_or_raise() ...")
    try:
        isTokenValid = authClient.verify_or_raise(token, service=service)
    except AuthServerError as e:
        # The token was not checked: don't blame it, and keep the cause out of the response
        logger.error(f"Token could not be verified: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

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