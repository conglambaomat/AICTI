"""Domain exceptions for DE-Forge validation and orchestration."""


class DeForgeError(Exception):
    """Base exception for DE-Forge domain errors."""


class ValidationGateError(DeForgeError):
    """Raised when a deterministic validation gate fails."""


class CitationVerificationError(ValidationGateError):
    """Raised when a citation quote or offset cannot be verified."""


class ProofObligationError(ValidationGateError):
    """Raised when required proof obligations are not proven."""
