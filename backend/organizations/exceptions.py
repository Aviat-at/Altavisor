"""
Domain exceptions for the organizations module.

All exceptions are plain Python exceptions (not DRF exceptions).
Views catch these and translate them to HTTP responses.
"""


class OrganizationNotFoundError(Exception):
    pass


class OrganizationInactiveError(Exception):
    pass


class DuplicateOrganizationError(Exception):
    pass


class MergeOrganizationError(Exception):
    pass


class MembershipNotFoundError(Exception):
    pass


class MembershipConflictError(Exception):
    pass
