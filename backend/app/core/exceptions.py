from typing import Optional, List, Any


class CarbonBaseException(Exception):
    def __init__(
        self, status_code: int, message: str, details: Optional[List[Any]] = None
    ):
        self.status_code = status_code
        self.message = message
        self.details = details or []
        super().__init__(message)


class AuthenticationError(CarbonBaseException):
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(status_code=401, message=message, details=details)


class AuthorizationError(CarbonBaseException):
    def __init__(
        self, message: str = "Permission denied", details: Optional[List[Any]] = None
    ):
        super().__init__(status_code=403, message=message, details=details)


class ResourceNotFoundError(CarbonBaseException):
    def __init__(
        self, message: str = "Resource not found", details: Optional[List[Any]] = None
    ):
        super().__init__(status_code=404, message=message, details=details)


class ValidationProcessingError(CarbonBaseException):
    def __init__(
        self, message: str = "Validation error", details: Optional[List[Any]] = None
    ):
        super().__init__(status_code=422, message=message, details=details)


class OCRProcessingError(CarbonBaseException):
    def __init__(
        self,
        message: str = "OCR processing failed",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(status_code=500, message=message, details=details)


class InvalidConsumptionError(CarbonBaseException):
    def __init__(
        self,
        message: str = "Invalid consumption amount",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(status_code=400, message=message, details=details)


class UnsupportedUtilityTypeError(CarbonBaseException):
    def __init__(
        self,
        message: str = "Unsupported utility type",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(status_code=400, message=message, details=details)


class UnitMismatchError(CarbonBaseException):
    def __init__(
        self,
        message: str = "Unit mismatch for utility type",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(status_code=400, message=message, details=details)


class RAGQdrantTimeoutError(CarbonBaseException):
    def __init__(
        self,
        message: str = "Qdrant connection timeout",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(status_code=500, message=message, details=details)


class RAGGeminiRateLimitError(CarbonBaseException):
    def __init__(
        self,
        message: str = "Gemini rate limit exceeded",
        details: Optional[List[Any]] = None,
    ):
        super().__init__(status_code=429, message=message, details=details)
