"""Corporate action value objects: splits, bonuses, dividends, rights issues.

Zero-floats invariant: every ratio, per-share payout, and adjusted price is a
``decimal.Decimal``. Value objects are frozen, self-validating dataclasses that
compare by value.

Split/bonus encoding (Indian market convention): ``old_shares`` shares held
before the action become ``new_shares`` shares after the action.

* A "1:5 split" (face value Rs.10 -> Rs.2) is ``Split(old_shares=1, new_shares=5)``.
* A "1:1 bonus" (one bonus share per share held) is ``Bonus(old_shares=1, new_shares=2)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TypeAlias

from vyapaar_data._compat import D, to_decimal


class CorporateActionType(Enum):
    """Canonical classification of a corporate action."""

    SPLIT = "split"
    BONUS = "bonus"
    DIVIDEND = "dividend"
    RIGHTS = "rights"


def _positive_decimal(value: Decimal | int | str, field: str) -> Decimal:
    d = to_decimal(value)
    if d <= 0:
        raise ValueError(f"{field} must be positive, got {d}")
    return d


@dataclass(frozen=True, slots=True)
class Split:
    """A share split: ``old_shares`` held shares become ``new_shares``."""

    instrument: str
    ex_date: date
    old_shares: int
    new_shares: int
    action_type: CorporateActionType = CorporateActionType.SPLIT

    def __post_init__(self) -> None:
        if self.old_shares <= 0 or self.new_shares <= 0:
            raise ValueError("split share counts must be positive integers")
        if self.old_shares == self.new_shares:
            raise ValueError("split share counts must differ")

    @property
    def price_multiplier(self) -> Decimal:
        """Restate a pre-ex historical price to the post-split basis."""
        return D(self.old_shares) / D(self.new_shares)

    @property
    def quantity_multiplier(self) -> Decimal:
        """Restate historical holdings to the post-split share count."""
        return D(self.new_shares) / D(self.old_shares)

    def apply(self, price: Decimal) -> Decimal:
        return price * self.price_multiplier


@dataclass(frozen=True, slots=True)
class Bonus:
    """A bonus issue: ``old_shares`` held shares become ``new_shares`` total."""

    instrument: str
    ex_date: date
    old_shares: int
    new_shares: int
    action_type: CorporateActionType = CorporateActionType.BONUS

    def __post_init__(self) -> None:
        if self.old_shares <= 0 or self.new_shares <= self.old_shares:
            raise ValueError("bonus totals must be positive and exceed held shares")

    @property
    def price_multiplier(self) -> Decimal:
        return D(self.old_shares) / D(self.new_shares)

    @property
    def quantity_multiplier(self) -> Decimal:
        return D(self.new_shares) / D(self.old_shares)

    def apply(self, price: Decimal) -> Decimal:
        return price * self.price_multiplier


@dataclass(frozen=True, slots=True)
class Dividend:
    """A cash dividend per share, paid on the ex-date."""

    instrument: str
    ex_date: date
    per_share: Decimal
    currency: str = "INR"
    action_type: CorporateActionType = CorporateActionType.DIVIDEND

    def __post_init__(self) -> None:
        object.__setattr__(self, "per_share", _positive_decimal(self.per_share, "per_share"))
        if not self.currency:
            raise ValueError("currency must be non-empty")

    @property
    def price_adjustment(self) -> Decimal:
        """Amount to subtract from a pre-ex historical price."""
        return self.per_share

    def apply(self, price: Decimal) -> Decimal:
        return price - self.per_share


@dataclass(frozen=True, slots=True)
class Rights:
    """A rights issue: ``new_shares`` offered at ``issue_price`` per ``old_shares`` held."""

    instrument: str
    ex_date: date
    old_shares: int
    new_shares: int
    issue_price: Decimal
    action_type: CorporateActionType = CorporateActionType.RIGHTS

    def __post_init__(self) -> None:
        if self.old_shares <= 0 or self.new_shares <= 0:
            raise ValueError("rights share counts must be positive integers")
        object.__setattr__(self, "issue_price", _positive_decimal(self.issue_price, "issue_price"))

    def apply(self, price: Decimal) -> Decimal:
        """Theoretical ex-rights price: (P*old + issue*new) / (old + new)."""
        total = self.old_shares + self.new_shares
        return (price * D(self.old_shares) + self.issue_price * D(self.new_shares)) / D(total)


CorporateAction: TypeAlias = Split | Bonus | Dividend | Rights


@dataclass(frozen=True, slots=True)
class CorporateActionRecord:
    """Flat storage projection of a corporate action (durable wire shape)."""

    instrument: str
    action_type: CorporateActionType
    ex_date: date
    old_shares: int | None = None
    new_shares: int | None = None
    per_share: Decimal | None = None
    issue_price: Decimal | None = None
    currency: str = "INR"


def to_record(action: CorporateAction) -> CorporateActionRecord:
    """Project a typed value object onto its durable storage shape."""
    if isinstance(action, Split):
        return CorporateActionRecord(
            action.instrument,
            action.action_type,
            action.ex_date,
            action.old_shares,
            action.new_shares,
        )
    if isinstance(action, Bonus):
        return CorporateActionRecord(
            action.instrument,
            action.action_type,
            action.ex_date,
            action.old_shares,
            action.new_shares,
        )
    if isinstance(action, Dividend):
        return CorporateActionRecord(
            action.instrument,
            action.action_type,
            action.ex_date,
            per_share=action.per_share,
            currency=action.currency,
        )
    if isinstance(action, Rights):
        return CorporateActionRecord(
            action.instrument,
            action.action_type,
            action.ex_date,
            action.old_shares,
            action.new_shares,
            issue_price=action.issue_price,
        )
    raise TypeError(f"unsupported corporate action: {action!r}")


def from_record(record: CorporateActionRecord) -> CorporateAction:
    """Rebuild a typed value object from its durable storage shape."""
    t = record.action_type
    if t is CorporateActionType.SPLIT:
        if record.old_shares is None or record.new_shares is None:
            raise ValueError("split record requires old_shares and new_shares")
        return Split(record.instrument, record.ex_date, record.old_shares, record.new_shares)
    if t is CorporateActionType.BONUS:
        if record.old_shares is None or record.new_shares is None:
            raise ValueError("bonus record requires old_shares and new_shares")
        return Bonus(record.instrument, record.ex_date, record.old_shares, record.new_shares)
    if t is CorporateActionType.DIVIDEND:
        if record.per_share is None:
            raise ValueError("dividend record requires per_share")
        return Dividend(record.instrument, record.ex_date, record.per_share, record.currency)
    if t is CorporateActionType.RIGHTS:
        if record.old_shares is None or record.new_shares is None or record.issue_price is None:
            raise ValueError("rights record requires old_shares, new_shares and issue_price")
        return Rights(
            record.instrument,
            record.ex_date,
            record.old_shares,
            record.new_shares,
            record.issue_price,
        )
    raise ValueError(f"unsupported action type: {t}")
