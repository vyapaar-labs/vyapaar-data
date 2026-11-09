"""Vectorized multi-field screener over a universe of instruments.

Evaluates :class:`~vyapaar_data.ports.data_feeds.ScreenQuery` conditions against
per-instrument candle history, supporting comparison operators (``gt``, ``lt``,
``gte``, ``lte``, ``eq``) and cross-over operators (``crosses_above``,
``crosses_below``) against either a literal :class:`decimal.Decimal` or another
field.

Matched instruments can be ordered by a field's last value and capped with a
limit, matching the ``order_by``/``limit`` surface of :class:`ScreenQuery`.
"""

from __future__ import annotations

from decimal import Decimal

import polars as pl

from vyapaar_data.ports.data_feeds import (
    ComparisonOp,
    MarketReader,
    ReferenceExporter,
    ScreenCondition,
    ScreenQuery,
    ScreenResult,
    ScreenValue,
)


class VectorizedScreener:
    """Vectorized screener backed by a :class:`MarketReader`."""

    def __init__(
        self,
        reader: MarketReader,
        exporter: ReferenceExporter | None = None,
    ) -> None:
        self.reader = reader
        self.exporter = exporter

    def execute_screen(self, query: ScreenQuery) -> ScreenResult:
        """Evaluate ``query`` conditions across ``query.universe``."""
        scored: list[tuple[str, Decimal | None]] = []
        frames: dict[str, pl.DataFrame] = {}

        for instrument in query.universe:
            candles = self.reader.get_candles(instrument)
            if candles.is_empty():
                continue
            passed = True
            for condition in query.conditions:
                if not self._eval_condition(candles, condition):
                    passed = False
                    break
            if not passed:
                continue

            score: Decimal | None = None
            if query.order_by:
                order_field = query.order_by.split()[0]
                if order_field in candles.columns:
                    column = candles[order_field]
                    if len(column):
                        last = column.to_list()[-1]
                        if last is not None:
                            score = Decimal(str(last))
            scored.append((instrument, score))
            frames[instrument] = candles

        descending = bool(query.order_by) and query.order_by.strip().upper().endswith("DESC")
        scored.sort(
            key=lambda item: (
                item[1] is None,
                item[1] if item[1] is not None else Decimal("0"),
            ),
            reverse=descending,
        )
        if query.limit is not None:
            scored = scored[: query.limit]

        matches = [instrument for instrument, _ in scored]
        reference: str | None = None
        if matches and self.exporter is not None:
            combined = pl.concat([frames[m] for m in matches]) if frames else pl.DataFrame()
            reference = self.exporter.export(f"screen_{len(matches)}", combined)

        return ScreenResult(instruments=matches, rows=len(matches), reference=reference)

    # ------------------------------------------------------------------ #
    # Condition evaluation
    # ------------------------------------------------------------------ #
    def _eval_condition(self, candles: pl.DataFrame, condition: ScreenCondition) -> bool:
        if condition.field not in candles.columns:
            return False
        series = candles[condition.field]
        if len(series) == 0:
            return False

        if condition.operator == ComparisonOp.CROSSES_ABOVE:
            return self._crosses(series, condition.value, candles, above=True)
        if condition.operator == ComparisonOp.CROSSES_BELOW:
            return self._crosses(series, condition.value, candles, above=False)

        threshold = self._resolve_scalar(candles, condition.value)
        if threshold is None:
            return False
        last = series.to_list()[-1]
        if last is None:
            return False
        return self._compare(Decimal(str(last)), threshold, condition.operator)

    def _crosses(
        self,
        series: pl.Series,
        value: ScreenValue,
        candles: pl.DataFrame,
        *,
        above: bool,
    ) -> bool:
        if len(series) < 2:
            return False
        current = Decimal(str(series.to_list()[-1]))
        previous = Decimal(str(series.to_list()[-2]))

        if value.field is not None and value.field in candles.columns:
            ref = candles[value.field].to_list()
            if len(ref) < 2:
                return False
            current_ref = Decimal(str(ref[-1]))
            previous_ref = Decimal(str(ref[-2]))
            if above:
                return previous <= previous_ref and current > current_ref
            return previous >= previous_ref and current < current_ref

        threshold = self._resolve_scalar(candles, value)
        if threshold is None:
            return False
        if above:
            return previous <= threshold and current > threshold
        return previous >= threshold and current < threshold

    def _resolve_scalar(self, candles: pl.DataFrame, value: ScreenValue) -> Decimal | None:
        if value.literal is not None:
            return Decimal(str(value.literal))
        if value.field is not None and value.field in candles.columns:
            column = candles[value.field]
            if len(column):
                last = column.to_list()[-1]
                if last is not None:
                    return Decimal(str(last))
        return None

    @staticmethod
    def _compare(left: Decimal, right: Decimal, op: ComparisonOp) -> bool:
        if op == ComparisonOp.GT:
            return left > right
        if op == ComparisonOp.LT:
            return left < right
        if op == ComparisonOp.GTE:
            return left >= right
        if op == ComparisonOp.LTE:
            return left <= right
        if op == ComparisonOp.EQ:
            return left == right
        return False


__all__ = ["VectorizedScreener"]
