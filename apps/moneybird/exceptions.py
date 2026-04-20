class MoneybirdAPIException(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response
    
    def __str__(self):
        return super().__str__()
    
class TokensNotPresentException(Exception):
    def __init__(self, message):
        super().__init__(message)

class MoneybirdNotFoundException(MoneybirdAPIException):
    def __init__(self, message, response):
        super().__init__(message, response)
        self.response = response

class MoneybirdBadRequestException(MoneybirdAPIException):
    def __init__(self, message, response):
        super().__init__(message, response)
        self.response = response

class MoneybirdAccountLimitReachedException(MoneybirdAPIException):
    def __init__(self, message, response):
        super().__init__(message, response)
        self.response = response

class MoneybirdNotAuthenticatedException(MoneybirdAPIException):
    def __init__(self, message, response):
        super().__init__(message, response)
        self.response = response

class MoneybirdRateLimitExceededException(MoneybirdAPIException):
    def __init__(self, message, response):
        super().__init__(message, response)
        self.response = response
    
class MoneybirdInternalServerErrorException(MoneybirdAPIException):
    def __init__(self, message, response):
        super().__init__(message, response)
        self.response = response
    