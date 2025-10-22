"""
Price analysis module for motorcycle listings.

Calculates market statistics, percentiles, and price scores to help identify
good deals vs overpriced listings.
"""

import statistics
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Listing, Motorcycle
from src.utils.logger import getLogger

logger = getLogger(__name__)


@dataclass
class MarketStats:
    """Market statistics for a specific motorcycle make/model/year."""

    make: str
    model: str
    year: int
    sampleSize: int
    average: float
    median: float
    percentile25: float
    percentile75: float
    minimum: float
    maximum: float
    standardDeviation: float


@dataclass
class PriceAnalysis:
    """Price analysis result for a specific listing."""

    listingPrice: float
    marketAverage: float
    marketMedian: float
    percentile25: float
    percentile75: float
    deviationFromAverage: float  # Percentage
    deviationFromMedian: float  # Percentage
    priceScore: float  # 0-100
    interpretation: str  # Human-readable interpretation
    sampleSize: int


class PriceAnalyzer:
    """
    Analyzes motorcycle listing prices against market data.

    Calculates market statistics and scores listings based on
    how they compare to similar motorcycles.
    """

    def __init__(self, session: Session):
        """
        Initialize price analyzer.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def getMarketStats(
        self,
        make: str,
        model: str,
        year: int,
        mileageRange: tuple[int, int] | None = None,
        maxAge: int = 365,
    ) -> MarketStats | None:
        """
        Calculate market statistics for a motorcycle.

        Args:
            make: Motorcycle make (e.g., "Ducati")
            model: Motorcycle model (e.g., "Panigale V4")
            year: Model year
            mileageRange: Optional (min, max) mileage range to filter by
            maxAge: Only include listings updated within this many days

        Returns:
            MarketStats object or None if insufficient data
        """
        # Build query for similar motorcycles
        query = (
            select(Listing.price)
            .join(Motorcycle)
            .where(Motorcycle.make == make)
            .where(Motorcycle.model == model)
            .where(Motorcycle.year == year)
            .where(Listing.price.isnot(None))
            .where(Listing.price > 0)
            .where(Listing.isActive == True)  # noqa: E712
        )

        # Filter by mileage range if provided
        if mileageRange:
            minMileage, maxMileage = mileageRange
            query = query.where(Listing.mileage >= minMileage).where(Listing.mileage <= maxMileage)

        # Execute query and get prices
        result = self.session.execute(query)
        prices = [float(row[0]) for row in result]

        # Need at least 5 data points for meaningful statistics
        if len(prices) < 5:
            logger.warning(
                f"Insufficient data for {year} {make} {model}: only {len(prices)} listings"
            )
            return None

        # Calculate statistics
        prices.sort()
        return MarketStats(
            make=make,
            model=model,
            year=year,
            sampleSize=len(prices),
            average=statistics.mean(prices),
            median=statistics.median(prices),
            percentile25=statistics.quantiles(prices, n=4)[0],
            percentile75=statistics.quantiles(prices, n=4)[2],
            minimum=min(prices),
            maximum=max(prices),
            standardDeviation=statistics.stdev(prices) if len(prices) > 1 else 0.0,
        )

    def analyzeListing(
        self,
        listingPrice: float,
        make: str,
        model: str,
        year: int,
        mileage: int | None = None,
    ) -> PriceAnalysis | None:
        """
        Analyze a listing's price against market data.

        Args:
            listingPrice: Price of the listing being analyzed
            make: Motorcycle make
            model: Motorcycle model
            year: Model year
            mileage: Optional mileage to use for mileage-adjusted comparison

        Returns:
            PriceAnalysis object or None if insufficient market data
        """
        # Determine mileage range for comparison
        mileageRange = None
        if mileage is not None:
            # ±5000 miles for similar comparisons
            mileageRange = (max(0, mileage - 5000), mileage + 5000)

        # Get market statistics
        stats = self.getMarketStats(make, model, year, mileageRange)
        if not stats:
            return None

        # Calculate deviations
        deviationFromAverage = ((listingPrice - stats.average) / stats.average) * 100
        deviationFromMedian = ((listingPrice - stats.median) / stats.median) * 100

        # Calculate price score (0-100)
        priceScore = self._calculatePriceScore(deviationFromAverage)

        # Generate interpretation
        interpretation = self._interpretScore(priceScore, deviationFromAverage)

        return PriceAnalysis(
            listingPrice=listingPrice,
            marketAverage=stats.average,
            marketMedian=stats.median,
            percentile25=stats.percentile25,
            percentile75=stats.percentile75,
            deviationFromAverage=deviationFromAverage,
            deviationFromMedian=deviationFromMedian,
            priceScore=priceScore,
            interpretation=interpretation,
            sampleSize=stats.sampleSize,
        )

    def _calculatePriceScore(self, deviationPercent: float) -> float:
        """
        Calculate price score based on deviation from market average.

        Score ranges from 0-100 based on how the price compares to market:
        - 20%+ below market: 100 points
        - 10-20% below: 90 points
        - 5-10% below: 80 points
        - Within ±5%: 70 points
        - 5-10% above: 60 points
        - 10-20% above: 40 points
        - 20%+ above: 20 points

        Args:
            deviationPercent: Percentage deviation from average (negative = below market)

        Returns:
            Score from 0-100
        """
        if deviationPercent <= -20:
            return 100.0
        elif deviationPercent < -10:
            # Linearly interpolate between 90-100 for -20% to -10%
            return 90.0 + ((-deviationPercent - 10) / 10) * 10
        elif deviationPercent < -5:
            # Linearly interpolate between 80-90 for -10% to -5%
            return 80.0 + ((-deviationPercent - 5) / 5) * 10
        elif deviationPercent <= 5:
            # Within ±5% of average
            return 70.0
        elif deviationPercent < 10:
            # Linearly interpolate between 60-70 for 5% to 10%
            return 70.0 - ((deviationPercent - 5) / 5) * 10
        elif deviationPercent < 20:
            # Linearly interpolate between 40-60 for 10% to 20%
            return 60.0 - ((deviationPercent - 10) / 10) * 20
        else:
            # 20%+ above market
            return max(0.0, 20.0 - ((deviationPercent - 20) * 0.5))

    def _interpretScore(self, score: float, deviation: float) -> str:
        """
        Generate human-readable interpretation of price score.

        Args:
            score: Price score (0-100)
            deviation: Deviation from average as percentage

        Returns:
            Human-readable interpretation string
        """
        absDeviation = abs(deviation)

        if score >= 95:
            return f"Exceptional price - {absDeviation:.1f}% below market average"
        elif score >= 85:
            return f"Excellent price - {absDeviation:.1f}% below market average"
        elif score >= 75:
            return f"Good price - {absDeviation:.1f}% below market average"
        elif score >= 65:
            return "Fair price - close to market average"
        elif score >= 50:
            return f"Above average price - {absDeviation:.1f}% over market"
        elif score >= 30:
            return f"High price - {absDeviation:.1f}% over market"
        else:
            return f"Very high price - {absDeviation:.1f}% over market"


def analyzePriceForListing(session: Session, listingId: int) -> PriceAnalysis | None:
    """
    Convenience function to analyze price for a listing by ID.

    Args:
        session: Database session
        listingId: Listing ID to analyze

    Returns:
        PriceAnalysis object or None
    """
    listing = session.get(Listing, listingId)
    if not listing or not listing.price or not listing.motorcycle:
        return None

    analyzer = PriceAnalyzer(session)
    return analyzer.analyzeListing(
        listingPrice=float(listing.price),
        make=listing.motorcycle.make,
        model=listing.motorcycle.model,
        year=listing.motorcycle.year,
        mileage=listing.mileage,
    )
