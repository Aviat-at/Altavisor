"""
Domain exceptions for the people module.

All exceptions inherit from PeopleModuleError so callers can catch the
base class when they don't need to distinguish between sub-types.
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


class CategoryNotFoundError(PeopleModuleError):
    """Raised when a PersonCategory record does not exist."""


class CategoryInactiveError(PeopleModuleError):
    """Raised when an operation requires an active category but it is inactive."""


class CategorySystemProtectedError(PeopleModuleError):
    """
    Raised when a write operation targets a system-defined category.
    System categories cannot be renamed, re-slugged, or deactivated via the API.
    """


class DuplicateCategoryAssignmentError(PeopleModuleError):
    """
    Raised when:
    - assign_category is called and an active assignment already exists, or
    - remove_category is called but no active assignment exists.
    """


class AddressNotFoundError(PeopleModuleError):
    """Raised when a PersonAddress record does not exist for the given person."""


class OrganizationRelationNotFoundError(PeopleModuleError):
    """Raised when an OrganizationPersonRelation record does not exist."""


class OrganizationRelationConflictError(PeopleModuleError):
    """
    Raised when link_person_to_organization would create a duplicate active
    relation for the same (person, organization_id, organization_type, role).
    """


class MergePersonError(PeopleModuleError):
    """
    Raised by the merge_persons service placeholder.
    Full merge is intentionally deferred — see services.merge_persons for
    the documented implementation contract.
    """
