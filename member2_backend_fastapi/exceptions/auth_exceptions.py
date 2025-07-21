from .base_exceptions import NethraException

class AuthenticationError(NethraException):
    """Authentication failed"""
    pass

class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Invalid username/password"""
    pass

class AccountLockedError(AuthenticationError):
    """Account is locked due to failed attempts"""
    pass
