class ValidationError(ValueError):
    def __init__(self, message: str, error_code: int = -1):
        super().__init__("Validation failed: [{}] {}".format(error_code, message))
        self.error_code = error_code
