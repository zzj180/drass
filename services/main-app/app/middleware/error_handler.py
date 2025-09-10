from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Any
import traceback
import time

from app.core.logging import get_logger, log_error

logger = get_logger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handler middleware
    """
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", "")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except ValueError as e:
        log_error(logger, e, {"request_id": request_id, "path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad Request",
                "message": str(e),
                "request_id": request_id
            }
        )
        
    except PermissionError as e:
        log_error(logger, e, {"request_id": request_id, "path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "Forbidden",
                "message": "You don't have permission to access this resource",
                "request_id": request_id
            }
        )
        
    except FileNotFoundError as e:
        log_error(logger, e, {"request_id": request_id, "path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Not Found",
                "message": str(e),
                "request_id": request_id
            }
        )
        
    except TimeoutError as e:
        log_error(logger, e, {"request_id": request_id, "path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": "Gateway Timeout",
                "message": "Request timed out",
                "request_id": request_id
            }
        )
        
    except Exception as e:
        # Log the full traceback for debugging
        logger.error(
            f"Unhandled exception: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "traceback": traceback.format_exc()
                }
            }
        )
        
        # Return a generic error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "request_id": request_id
            }
        )