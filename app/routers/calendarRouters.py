from fastapi.routing import APIRouter
from fastapi import HTTPException, Depends
from models.calendarModels import EventCountResponse,EventCountRequest, UpcomingEventsResponse, CalendarEvent
from services.calendarService import calendarSrv
from config.settings import settings
# Initialize logger at the top so it's available everywhere 
from logger.loggerFactory import logger_factory
logger = logger_factory.get_logger('calendarRouters')

SERVICE_NAME = settings.get('APP_NAME')
router = APIRouter(prefix="/calendar", tags=["Calendar APIs"])

# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    logger.info("====> /health endpoint called <====")
    return {"status": "healthy", "service": SERVICE_NAME}