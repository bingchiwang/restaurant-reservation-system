class FeatureDisabledError(PermissionError):
    """Raised when a feature (reservations, ordering, pre-ordering, or store) is disabled by backend settings."""
    pass
