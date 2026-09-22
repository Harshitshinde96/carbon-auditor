from fastapi.responses import JSONResponse
from fastapi import status
from app.models.response_models import ErrorResponse

def error_response(message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> JSONResponse:
    """
    Helper function to generate standardized error responses.
    """
    content = ErrorResponse(
        success=False,
        error=message
    ).model_dump()
    return JSONResponse(status_code=status_code, content=content)
