class AuthenticationError(Exception):
    pass


class ResourceNotAvailable(Exception):
    def __init__(self, message):

        super().__init__(message)


class NotFoundError(Exception):
    def __init__(self, message):

        super().__init__(message)