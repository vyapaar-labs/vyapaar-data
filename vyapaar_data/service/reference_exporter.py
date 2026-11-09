"""Ephemeral in-memory reference store emitting ``$vyapaar/ref/<uuid>`` URIs.

Holds Polars DataFrames (and, by extension, Arrow-backed data) keyed by a
``$vyapaar/ref/<reference_id>`` handle so downstream quantitative engines can
dereference large time-series without re-serializing them.
"""

from __future__ import annotations

import polars as pl


class InMemoryReferenceExporter:
    """In-memory Arrow/Polars reference cache keyed by ``$vyapaar/ref/<uuid>``."""

    def __init__(self) -> None:
        self._store: dict[str, pl.DataFrame] = {}

    def export(self, reference_id: str, frame: pl.DataFrame) -> str:
        """Persist ``frame`` under ``reference_id`` and return its ref URI."""
        uri = f"$vyapaar/ref/{reference_id}"
        self._store[uri] = frame.clone()
        return uri

    def resolve(self, reference_uri: str) -> pl.DataFrame:
        """Rehydrate a previously exported frame by its ref URI."""
        if reference_uri not in self._store:
            raise KeyError(f"unknown reference: {reference_uri}")
        return self._store[reference_uri]

    def __contains__(self, reference_uri: str) -> bool:
        return reference_uri in self._store


__all__ = ["InMemoryReferenceExporter"]
