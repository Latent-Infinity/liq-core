"""Result data models for data operations in the LIQ Stack.

These models provide structured results for fetch and update operations,
replacing untyped dictionaries with validated, immutable dataclasses.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Result of a single symbol fetch operation.

    Attributes:
        symbol: The symbol that was fetched
        success: Whether the fetch succeeded
        count: Number of rows fetched (only present on success)
        error: Error message (only present on failure)

    Example:
        # Success case
        result = FetchResult(symbol="EUR_USD", success=True, count=5000)

        # Failure case
        result = FetchResult(symbol="EUR_USD", success=False, error="API rate limit")
    """

    symbol: str
    success: bool
    count: int | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        """Validate result consistency."""
        if self.success and self.count is None:
            raise ValueError("count is required when success=True")
        if not self.success and self.error is None:
            raise ValueError("error is required when success=False")


@dataclass(frozen=True, slots=True)
class UpdateResult:
    """Result of a single symbol update operation.

    Attributes:
        symbol: The symbol that was updated
        success: Whether the update succeeded
        gaps_filled: Number of gaps that were backfilled (only present on success)
        total_rows: Total rows after update (only present on success)
        error: Error message (only present on failure)

    Example:
        # Success case
        result = UpdateResult(
            symbol="EUR_USD",
            success=True,
            gaps_filled=3,
            total_rows=50000
        )

        # Failure case
        result = UpdateResult(symbol="EUR_USD", success=False, error="No data found")
    """

    symbol: str
    success: bool
    gaps_filled: int | None = None
    total_rows: int | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        """Validate result consistency."""
        if self.success:
            if self.gaps_filled is None:
                raise ValueError("gaps_filled is required when success=True")
            if self.total_rows is None:
                raise ValueError("total_rows is required when success=True")
        if not self.success and self.error is None:
            raise ValueError("error is required when success=False")


@dataclass(frozen=True, slots=True)
class BatchResult:
    """Aggregated result of a batch operation.

    Provides a summary of multiple fetch or update operations along with
    individual results for each symbol.

    Attributes:
        total: Total number of symbols processed
        succeeded: Number of successful operations
        failed: Number of failed operations
        results: List of individual results

    Example:
        batch = BatchResult(
            total=3,
            succeeded=2,
            failed=1,
            results=[
                FetchResult("EUR_USD", True, count=5000),
                FetchResult("GBP_USD", True, count=4500),
                FetchResult("JPY_USD", False, error="Not found"),
            ]
        )
    """

    total: int
    succeeded: int
    failed: int
    results: list[FetchResult] | list[UpdateResult]

    def __post_init__(self) -> None:
        """Validate batch totals."""
        if self.total != self.succeeded + self.failed:
            raise ValueError("total must equal succeeded + failed")
        if len(self.results) != self.total:
            raise ValueError("results length must equal total")

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.total == 0:
            return 0.0
        return self.succeeded / self.total * 100

    def get_failures(self) -> list[FetchResult] | list[UpdateResult]:
        """Return only failed results."""
        return [r for r in self.results if not r.success]

    def get_successes(self) -> list[FetchResult] | list[UpdateResult]:
        """Return only successful results."""
        return [r for r in self.results if r.success]
