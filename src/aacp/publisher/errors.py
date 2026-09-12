"""Publisher errors."""


class ProtocolInvalid(ValueError):
    """Envelope failed Core/schema validation."""


class TargetInvalid(ValueError):
    """Target binding invalid or inconsistent with envelope."""


class PublicationConflict(RuntimeError):
    """Same message_id already published with different semantic content."""


class PublishRetriesExceeded(RuntimeError):
    """CAS/reconcile loop exhausted without verified publication."""
