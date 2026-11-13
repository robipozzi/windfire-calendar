from models.calendarModels import EventCountRequest, EventCountResponse, UpcomingEventsResponse, CalendarEvent
from services.calendarService import calendarSrv
from fastapi import HTTPException, Depends # pyright: ignore[reportMissingImports]
from fastapi.routing import APIRouter # pyright: ignore[reportMissingImports]
from datetime import date
from config.settings import settings
from commons import verify_token
# Initialize logger at the top so it's available everywhere 
from logger.loggerFactory import logger_factory
logger = logger_factory.get_logger('calendarRouters')

SERVICE_NAME = settings.get('APP_NAME')
router = APIRouter(prefix="/calendar", tags=["Calendar APIs"])

# Calendar endpoints
@router.post("/events/count/year", response_model=EventCountResponse)
async def count_events_by_year(
    request: EventCountRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Count calendar events for a specific year
    """
    logger.info("====> /v1/calendar/events/count/year endpoint called <====")
    if not request.year:
        raise HTTPException(status_code=400, detail="Year is required for this endpoint")
    
    try:
        # Raises ValueError for a future year (end date before 1 January) or a year outside 1-9999
        count = calendarSrv.countCalendarEventsYear(request.event_title, request.year)
    except ValueError as e:
        logger.warning(f"Invalid year {request.year}: {e}")
        raise HTTPException(status_code=400, detail="Invalid year, expected a year between 1 and the current year")
    except Exception:
        logger.exception("Failed to count events")
        raise HTTPException(status_code=500, detail="Failed to count events")
    if count is None:
        logger.error("Failed to count events: Google Calendar returned no result")
        raise HTTPException(status_code=500, detail="Failed to count events")

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

@router.post("/events/count/today", response_model=EventCountResponse)
async def count_events_to_today(
    request: EventCountRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Count calendar events from start date to today
    """
    logger.info("====> /v1/calendar/events/count/today endpoint called <====")
    if not request.start_date:
        raise HTTPException(status_code=400, detail="Start date is required for this endpoint")
    
    try:
        # Raises ValueError when start_date is after today
        count = calendarSrv.countCalendarEventsToday(request.event_title, request.start_date)
    except ValueError as e:
        logger.warning(f"Invalid start_date {request.start_date}: {e}")
        raise HTTPException(status_code=400, detail="Invalid start_date, expected a date on or before today")
    except Exception:
        logger.exception("Failed to count events")
        raise HTTPException(status_code=500, detail="Failed to count events")
    if count is None:
        logger.error("Failed to count events: Google Calendar returned no result")
        raise HTTPException(status_code=500, detail="Failed to count events")

    return EventCountResponse(
        event_title=request.event_title,
        count=count,
        start_date=request.start_date.isoformat(),
        end_date=date.today().isoformat()
    )

@router.post("/events/count/range", response_model=EventCountResponse)
async def count_events_by_range(
    request: EventCountRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Count calendar events within a date range
    """
    logger.info("====> /v1/calendar/events/count/range endpoint called <====")
    if not request.start_date or not request.end_date:
        raise HTTPException(status_code=400, detail="Both start_date and end_date are required for this endpoint")
    
    if request.start_date > request.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")
    
    try:
        # Raises ValueError when end_date is before start_date (already rejected above)
        count = calendarSrv.countCalendarEvents(request.event_title, request.start_date, request.end_date)
    except ValueError as e:
        logger.warning(f"Invalid date range {request.start_date} -> {request.end_date}: {e}")
        raise HTTPException(status_code=400, detail="Invalid date range, start_date must be before or equal to end_date")
    except Exception:
        logger.exception("Failed to count events")
        raise HTTPException(status_code=500, detail="Failed to count events")
    if count is None:
        logger.error("Failed to count events: Google Calendar returned no result")
        raise HTTPException(status_code=500, detail="Failed to count events")

    return EventCountResponse(
        event_title=request.event_title,
        count=count,
        start_date=request.start_date.isoformat(),
        end_date=request.end_date.isoformat()
    )

@router.get("/events/upcoming", response_model=UpcomingEventsResponse)
async def get_upcoming_events(current_user: dict = Depends(verify_token)):
    """
    Get the next 10 upcoming calendar events
    """
    logger.info("====> /v1/calendar/events/upcoming endpoint called <====")
    try:
        events = calendarSrv.getUpcomingEvents()
        
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
    except Exception:
        logger.exception("Failed to get upcoming events")
        raise HTTPException(status_code=500, detail="Failed to get upcoming events")
