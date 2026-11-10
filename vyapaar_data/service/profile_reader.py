"""Company symbol profile reader."""

from __future__ import annotations

from vyapaar_data.domain.profile import SymbolProfile
from vyapaar_data.ports.repositories import ProfileRepository


class LakehouseProfileReader:
    """Profile reader backed by a profile repository."""

    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    def get_profile(self, symbol: str) -> SymbolProfile | None:
        """Symbol profile for ``symbol`` (``None`` when unknown)."""
        rows = self.repository.query(symbol=symbol)
        return rows[0] if rows else None

    def get_profiles(
        self,
        symbols: list[str] | None = None,
        sector: str | None = None,
        industry: str | None = None,
    ) -> list[SymbolProfile]:
        """Symbol profiles, optionally filtered by symbol list / sector /
        industry."""
        if symbols is not None:
            seen: set[str] = set()
            profiles: list[SymbolProfile] = []
            for symbol in symbols:
                if symbol in seen:
                    continue
                seen.add(symbol)
                profile = self.get_profile(symbol)
                if profile is None:
                    continue
                if sector is not None and profile.sector != sector:
                    continue
                if industry is not None and profile.industry != industry:
                    continue
                profiles.append(profile)
            return profiles
        return self.repository.query(symbol=None, sector=sector, industry=industry)


__all__ = ["LakehouseProfileReader"]
