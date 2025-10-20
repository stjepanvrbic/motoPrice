# Testing Guide for motoPrice

This guide shows you how to run tests and use the project components for manual testing.

## Running Tests

### Run All Tests
```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run all tests (no coverage)
python -m pytest tests/ -v

# Run all tests (quiet mode)
python -m pytest tests/
```

### Run Specific Test Files
```bash
# Test a specific file
python -m pytest tests/testNormalizers.py -v

# Test multiple files
python -m pytest tests/testNormalizers.py tests/testValidators.py -v
```

### Run Specific Tests
```bash
# Run a specific test class
python -m pytest tests/testNormalizers.py::TestNormalizePrice -v

# Run a specific test method
python -m pytest tests/testNormalizers.py::TestNormalizePrice::testValidPrices -v
```

### Run Integration Tests
```bash
# Run only integration tests
python -m pytest tests/integration/ -v

# Run integration tests with marker
python -m pytest -m integration -v

# Run specific integration test
python -m pytest tests/integration/testCycleTraderIntegration.py::testCycleTraderRealScrape -v
```

### Useful Pytest Options
```bash
# Show print statements
python -m pytest tests/ -v -s

# Stop on first failure
python -m pytest tests/ -v -x

# Run last failed tests
python -m pytest tests/ -v --lf

# Show test durations
python -m pytest tests/ -v --durations=10

# Run tests in parallel (faster)
python -m pytest tests/ -v -n auto
```

## Manual Testing the Components

### 1. Data Normalization

#### Test Price Normalization
```python
from src.utils.normalizers import normalizePrice

# Test various formats
print(normalizePrice("$15,000"))  # 15000
print(normalizePrice("15k"))      # 15000
print(normalizePrice("$20,500 OBO"))  # 20500
print(normalizePrice("Call for price"))  # None
```

#### Test Mileage Normalization
```python
from src.utils.normalizers import normalizeMileage

print(normalizeMileage("5,000 mi"))  # 5000
print(normalizeMileage("5k miles"))  # 5000
print(normalizeMileage("12,345"))    # 12345
```

#### Test Title Parsing
```python
from src.utils.normalizers import parseTitle

result = parseTitle("2022 Ducati Panigale V4")
print(f"Year: {result.year}")   # 2022
print(f"Make: {result.make}")   # Ducati
print(f"Model: {result.model}") # Panigale V4
```

#### Test Location Parsing
```python
from src.utils.normalizers import parseLocation

result = parseLocation("Los Angeles, CA 90001")
print(f"City: {result.city}")     # Los Angeles
print(f"State: {result.state}")   # CA
print(f"ZIP: {result.zipCode}")   # 90001
```

#### Test Complete Normalization
```python
from src.utils.normalizers import normalizeListing

rawData = {
    "url": "https://example.com/listing/123",
    "source": "cycletrader",
    "title": "2022 Ducati Panigale V4",
    "price": "$18,500",
    "mileage": "1,200 mi",
    "location": "Los Angeles, CA 90001",
}

normalized = normalizeListing(rawData)
print(normalized)
```

### 2. Pydantic Validation

#### Test Valid Listing
```python
from src.utils.validators import NormalizedListing

listing = NormalizedListing(
    url="https://example.com/listing/123",
    source="cycletrader",
    year=2022,
    make="Ducati",
    model="Panigale V4",
    price=18500,
    mileage=1200,
    city="Los Angeles",
    state="CA",
    title="2022 Ducati Panigale V4",
)

print(listing.model_dump())
```

#### Test Invalid Listing (Validation Errors)
```python
from src.utils.validators import NormalizedListing
from pydantic import ValidationError

try:
    # This will fail - invalid URL
    listing = NormalizedListing(
        url="not-a-url",
        source="cycletrader",
        title="Test",
    )
except ValidationError as e:
    print(e)
```

### 3. Database Operations

#### Create a Motorcycle
```python
from src.database.connection import DatabaseManager
from src.database.operations import createMotorcycle

db = DatabaseManager()

with db.getSession() as session:
    moto = createMotorcycle(
        session=session,
        make="Ducati",
        model="Panigale V4",
        year=2022,
    )
    print(f"Created motorcycle: {moto.id}")
```

#### Create a Listing
```python
from src.database.connection import DatabaseManager
from src.database.operations import createListing, getOrCreateMotorcycle

db = DatabaseManager()

with db.getSession() as session:
    # Get or create motorcycle first
    moto = getOrCreateMotorcycle(
        session=session,
        make="Ducati",
        model="Panigale V4",
        year=2022,
    )

    # Create listing
    listing = createListing(
        session=session,
        url="https://example.com/listing/123",
        source="cycletrader",
        motorcycleId=moto.id,
        price=18500,
        mileage=1200,
        title="2022 Ducati Panigale V4",
    )
    print(f"Created listing: {listing.id}")
```

### 4. Web Scrapers

#### Test CycleTrader Scraper
```python
from src.scrapers.cycletrader import CycleTraderScraper

# Create scraper instance
scraper = CycleTraderScraper()

# Build search URL
url = scraper.buildSearchUrl(
    make="Ducati",
    model="Panigale V4",
    yearMin=2020,
    yearMax=2024,
)
print(f"Search URL: {url}")

# Scrape (requires browser)
# WARNING: This will open a browser window
with scraper:
    listings = scraper.scrape(
        make="Ducati",
        model="Panigale V4",
        maxPages=1,  # Just 1 page for testing
    )
    print(f"Found {len(listings)} listings")
    if listings:
        print(f"First listing: {listings[0]}")
```

#### Test Facebook Scraper
```python
from src.scrapers.facebook import FacebookMarketplaceScraper

scraper = FacebookMarketplaceScraper()

# Build search URL
url = scraper.buildSearchUrl(
    query="Ducati Panigale V4",
    minPrice=10000,
    maxPrice=30000,
)
print(f"Search URL: {url}")

# Note: Facebook scraping may require auth
# See integration tests for more details
```

### 5. Complete Pipeline Test

#### Scrape → Normalize → Validate → Store
```python
from src.scrapers.cycletrader import CycleTraderScraper
from src.utils.normalizers import normalizeListing
from src.utils.validators import NormalizedListing
from src.database.connection import DatabaseManager
from src.database.operations import getOrCreateMotorcycle, createListing

# 1. Scrape data
scraper = CycleTraderScraper()
with scraper:
    rawListings = scraper.scrape(
        make="Ducati",
        model="Panigale V4",
        maxPages=1,
    )

# 2. Normalize and validate
db = DatabaseManager()
validatedListings = []

for raw in rawListings:
    try:
        # Normalize
        normalized = normalizeListing(raw)

        # Validate
        validated = NormalizedListing(**normalized)
        validatedListings.append(validated)
    except Exception as e:
        print(f"Validation failed for {raw.get('url')}: {e}")

# 3. Store in database
with db.getSession() as session:
    for listing in validatedListings:
        # Get or create motorcycle
        moto = getOrCreateMotorcycle(
            session=session,
            make=listing.make or "Unknown",
            model=listing.model or "Unknown",
            year=listing.year,
        )

        # Create listing
        dbListing = createListing(
            session=session,
            url=listing.url,
            source=listing.source,
            motorcycleId=moto.id,
            price=listing.price,
            mileage=listing.mileage,
            title=listing.title,
        )
        print(f"Stored listing: {dbListing.id}")

print(f"Successfully stored {len(validatedListings)} listings")
```

## Python Interactive Shell

You can also test interactively using Python shell:

```bash
# Start Python shell
python

# Then import and test:
>>> from src.utils.normalizers import normalizePrice, parseTitle
>>> normalizePrice("$15,000")
15000
>>> result = parseTitle("2022 Ducati Panigale V4")
>>> result.year
2022
>>> result.make
'Ducati'
```

## IPython for Better Interactive Testing

Install IPython for a better REPL experience:

```bash
pip install ipython

# Start IPython
ipython

# Now you have auto-completion, syntax highlighting, etc.
In [1]: from src.utils.normalizers import *
In [2]: normalizePrice("$15k")
Out[2]: 15000
```

## Jupyter Notebook for Testing

You can also create Jupyter notebooks for interactive testing:

```bash
# Install Jupyter
pip install jupyter

# Start Jupyter
jupyter notebook

# Create a new notebook and test components
```

## Common Testing Scenarios

### Test Data Normalization Accuracy
```bash
# Run normalization tests with verbose output
python -m pytest tests/testNormalizers.py::TestParseTitle::testFullTitles -v -s
```

### Test Database Integration
```bash
# Run database tests
python -m pytest tests/testDatabase.py -v
```

### Test Real Web Scraping
```bash
# Run CycleTrader integration test (requires browser)
python -m pytest tests/integration/testCycleTraderIntegration.py::testCycleTraderRealScrape -v -s

# Run all integration tests
python -m pytest tests/integration/ -v -s
```

### Debug a Failing Test
```bash
# Run with Python debugger
python -m pytest tests/testNormalizers.py::TestNormalizePrice::testValidPrices --pdb

# Show full error traceback
python -m pytest tests/testNormalizers.py -v --tb=long
```

## Coverage Reports

### Generate HTML Coverage Report
```bash
# Run tests with HTML coverage report
python -m pytest tests/ --cov=src --cov-report=html

# Open the report in browser
open htmlcov/index.html
```

### Check Coverage for Specific Module
```bash
# Coverage for normalizers only
python -m pytest tests/testNormalizers.py --cov=src.utils.normalizers --cov-report=term-missing
```

## Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Run pre-commit manually
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run pytest --all-files
```

## Tips

1. **Start small**: Test individual functions before testing complete pipelines
2. **Use integration tests sparingly**: They're slower and can be flaky (especially Facebook)
3. **Mock external dependencies**: For unit tests, mock browser/network calls
4. **Check coverage**: Aim for 80%+ coverage on new code
5. **Run tests before committing**: Pre-commit hooks will catch issues

## Troubleshooting

### Tests Fail with "ModuleNotFoundError"
```bash
# Make sure you're in the project root
cd /path/to/motoPrice

# Make sure dependencies are installed
pip install -r requirements.txt
```

### Browser Tests Fail
```bash
# Install Playwright browsers
python -m playwright install chromium

# Or install all browsers
python -m playwright install
```

### Database Tests Fail
```bash
# Check PostgreSQL is running
psql -l

# Check database connection in config
cat config/config.yaml
```
