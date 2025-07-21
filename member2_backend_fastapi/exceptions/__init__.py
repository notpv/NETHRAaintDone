# Custom exceptions for NETHRA
class NethraException(Exception):
    """Base exception for NETHRA"""
    pass

class AuthenticationError(NethraException):
    """Authentication related errors"""
    pass

class TrustCalculationError(NethraException):
    """Trust calculation errors"""
    pass

__all__ = [
    "NethraException",
    "AuthenticationError", 
    "TrustCalculationError"
]
