"""
Domain exceptions for the party module.

All exceptions inherit from PartyModuleError so callers can catch the
base class when they don't need to distinguish between sub-types.
"""


class PartyModuleError(Exception):
    """Base exception for all party-module errors."""


class PartyNotFoundError(PartyModuleError):
    """Raised when a Party record does not exist."""


class PartyInactiveError(PartyModuleError):
    """Raised when an operation is attempted on a deactivated Party."""


class CategoryNotFoundError(PartyModuleError):
    """Raised when a PartyCategory record does not exist."""


class CategoryInactiveError(PartyModuleError):
    """Raised when an operation requires an active category but it is inactive."""


class CategorySystemProtectedError(PartyModuleError):
    """
    Raised when a write operation targets a system-defined category.
    System categories cannot be renamed, re-slugged, or deactivated via the API.
    """


class DuplicateCategoryAssignmentError(PartyModuleError):
    """
    Raised when:
    - assign_category_to_party is called and an active assignment already exists, or
    - remove_category_from_party is called but no active assignment exists.
    """


class AddressNotFoundError(PartyModuleError):
    """Raised when a PartyAddress record does not exist for the given party."""


class RelationshipNotFoundError(PartyModuleError):
    """Raised when a PartyRelationship record does not exist."""


class RelationshipConflictError(PartyModuleError):
    """
    Raised when link_parties would create a duplicate active relationship
    for the same (from_party, to_party, role) combination.
    """


class MergePartyError(PartyModuleError):
    """
    Raised by the merge_parties service placeholder (HTTP 501).
    Full merge is intentionally deferred — see services.merge_parties for
    the documented implementation contract.
    """
