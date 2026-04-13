from dataclasses import dataclass


@dataclass
class DomainError(Exception):
    code: str
    message: str


class ValidationDomainError(DomainError):
    pass


class PermissionDomainError(DomainError):
    pass


class NotFoundDomainError(DomainError):
    pass


class AuthenticationDomainError(DomainError):
    pass
