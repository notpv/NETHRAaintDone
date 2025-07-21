from .base_exceptions import NethraException

class TrustCalculationError(NethraException):
    """Trust score calculation failed"""
    pass

class ModelLoadError(TrustCalculationError):
    """AI model failed to load"""
    pass

class PreprocessingError(TrustCalculationError):
    """Data preprocessing failed"""
    pass

class ThresholdError(TrustCalculationError):
    """Threshold calculation failed"""
    pass
