"""Object store adapters."""

from atlas_persistence.object_store.local import document_storage_path, write_document_bytes

__all__ = ["document_storage_path", "write_document_bytes"]
