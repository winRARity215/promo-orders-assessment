from __future__ import annotations

from typing import Any, Dict

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            "error": True,
            "message": "An error occurred.",
            "details": {}
        }
        
        if isinstance(exc, DjangoValidationError):
            custom_response_data["message"] = str(exc)
            if hasattr(exc, 'error_dict'):
                custom_response_data["details"] = exc.error_dict
            response.status_code = status.HTTP_400_BAD_REQUEST
        
        elif hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                custom_response_data["details"] = exc.detail
                custom_response_data["message"] = "Validation failed."
            elif isinstance(exc.detail, list):
                custom_response_data["message"] = "; ".join(str(item) for item in exc.detail)
            else:
                custom_response_data["message"] = str(exc.detail)
        
        else:
            custom_response_data["message"] = str(exc)
        
        response.data = custom_response_data
    
    return response


class BusinessLogicError(Exception):
    
    def __init__(self, message: str, code: str = "business_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(BusinessLogicError):
    
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message, "not_found")


class PermissionDeniedError(BusinessLogicError):
    
    def __init__(self, message: str = "Permission denied.") -> None:
        super().__init__(message, "permission_denied")
