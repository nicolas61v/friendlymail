"""
Custom exceptions for Gmail integration
"""

class GmailServiceError(Exception):
    """Base exception for Gmail service errors"""
    pass

class OAuthError(GmailServiceError):
    """OAuth authentication errors"""
    def __init__(self, message, error_type=None, error_description=None):
        super().__init__(message)
        self.error_type = error_type
        self.error_description = error_description

class TokenExpiredError(OAuthError):
    """Access token has expired"""
    pass

class RefreshTokenInvalidError(OAuthError):
    """Refresh token is invalid or expired"""
    pass

class GmailAPIError(GmailServiceError):
    """Gmail API specific errors"""
    def __init__(self, message, status_code=None, error_details=None):
        super().__init__(message)
        self.status_code = status_code
        self.error_details = error_details

class QuotaExceededError(GmailAPIError):
    """Gmail API quota exceeded"""
    pass

class PermissionError(GmailAPIError):
    """Insufficient permissions for Gmail API"""
    pass