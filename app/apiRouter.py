from fastapi import APIRouter
# Initialize logger at the top so it's available everywhere 
from logger.loggerFactory import logger_factory
logger = logger_factory.get_logger('apiRouter')

api = APIRouter(prefix="/v1")
api_v2 = APIRouter(prefix="/v2")

# include routes to a root route
from routers.calendarRouters import router as calendarRouters
logger.debug("Including routers...")
api.include_router(calendarRouters)