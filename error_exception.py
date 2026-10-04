class InvalidIdentifierError(ValueError):
    """Raised when an identifier fails regular expression format validation."""
    pass


class InvalidRecordError(ValueError):
    """Raised when a CSV row is missing required fields or fails domain rules."""
    pass