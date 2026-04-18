"""
Domain exceptions for the people module.

Person-specific exceptions are defined here. Exceptions that moved to
party.exceptions are re-exported under their original names so that views
can import everything from a single location without changing import paths.
"""


class PeopleModuleError(Exception):
    """Base exception for all people-module errors."""


class PersonNotFoundError(PeopleModuleError):
    """Raised when a Person record does not exist."""


class PersonInactiveError(PeopleModuleError):
    """Raised when an operation is attempted on a deactivated Person."""


class DuplicatePersonError(PeopleModuleError):
    """
    Raised when create_person or update_person detects likely duplicates.

    Attributes:
        candidates: list of dicts with keys "person" (Person instance)
                    and "reason" (str: "email_match" | "name_match" | "phone_match")
    """

    def __init__(self, message: str, candidates: list = None):
        super().__init__(message)
        self.candidates = candidates or []


class MergePersonError(PeopleModuleError):
    """
    Raised by the merge_persons service placeholder.
    Full merge is intentionally deferred — see services.merge_persons for
    the documented implementation contract.
    """


# ─── Re-exports from party.exceptions ─────────────────────────────────────────
# Views import these from .exceptions; re-exporting here avoids touching views.

from party.exceptions import (  # noqa: E402, F401
    AddressNotFoundError,
    CategoryInactiveError,
    CategoryNotFoundError,
    CategorySystemProtectedError,
    DuplicateCategoryAssignmentError,
    RelationshipConflictError as OrganizationRelationConflictError,
    RelationshipNotFoundError as OrganizationRelationNotFoundError,
)
