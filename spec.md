# Motorcycle Listing Evaluator - Technical Specification

## Project Overview

A robust backend system that evaluates motorcycle listings by analyzing price, condition, mileage, and other factors to provide buyers with an objective assessment of listing quality. The system scrapes data from multiple marketplaces, builds a comprehensive database, and uses both rule-based algorithms and AI vision analysis to score listings.

**Primary Use Case:** Evaluate Ducati Panigale V4 listings (and any other motorcycle)

**End Goal:** Productize as web app, mobile app, and/or Chrome extension

## Architecture Overview

```
┌─────────────────┐
│   CLI Interface │  (Phase 1)
│  (Click/Typer)  │
└────────┬────────┘
         │
    ┌────▼─────────────────────────────────────┐
    │         Core Application Logic           │
    │  ┌──────────┐  ┌──────────┐  ┌────────┐ │
    │  │ Scrapers │  │ Analysis │  │ Scoring│ │
    │  └──────────┘  └──────────┘  └────────┘ │
    └────────┬──────────────┬──────────────────┘
             │              │
    ┌────────▼────────┐ ┌──▼──────────────┐
    │   PostgreSQL    │ │  OpenAI GPT-4   │
    │    Database     │ │  Vision API     │
    └─────────────────┘ └─────────────────┘
```

**Future Architecture:**
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Web App     │  │  Mobile App  │  │   Chrome     │
│  (React)     │  │  (React      │  │  Extension   │
│              │  │   Native)    │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └─────────────────┼──────────────────┘
                         │
                    ┌────▼────────┐
                    │   FastAPI   │
                    │  REST API   │
                    └─────────────┘
```

## Tech Stack

### Backend (Phase 1 - Current Focus)
- **Language:** Python 3.11+
- **Web Scraping:**
  - `playwright` - Handle dynamic sites (Facebook Marketplace)
  - `beautifulsoup4` - Parse static HTML (CycleTrader, eBay)
  - `requests` - HTTP client with header rotation
  - `fake-useragent` - User-agent rotation
- **Database:**
  - PostgreSQL 15+ (production-ready, scalable)
  - `SQLAlchemy` - ORM
  - `Alembic` - Database migrations
- **AI/ML:**
  - OpenAI GPT-4 Vision API (Phase 1)
  - Local models optional (Phase 2): LLaVA, CLIP
- **CLI Framework:**
  - `click` or `typer` - Modern CLI interface
  - `rich` - Beautiful terminal output
- **Testing:**
  - `pytest` - Testing framework
  - `pytest-asyncio` - Async test support
  - `pytest-cov` - Coverage reports
- **Utilities:**
  - `pydantic` - Data validation
  - `python-dotenv` - Environment management
  - `loguru` - Structured logging

### Future Stack (Phase 2+)
- **API:** FastAPI (async, modern, OpenAPI docs)
- **Frontend:** React + TypeScript
- **Mobile:** React Native
- **Deployment:** Docker, AWS/GCP

## Database Schema

### Table: `motorcycles`
Reference data for motorcycle specifications.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| make | VARCHAR(100) | Manufacturer (Ducati, Honda, etc.) |
| model | VARCHAR(100) | Model name (Panigale V4, CBR1000RR) |
| year | INTEGER | Model year |
| displacement_cc | INTEGER | Engine size in cc |
| category | VARCHAR(50) | Sport, Cruiser, Touring, etc. |
| msrp | DECIMAL(10,2) | Original MSRP |
| specs | JSONB | Additional specs (weight, HP, etc.) |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

### Table: `listings`
Scraped motorcycle listings.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| motorcycle_id | INTEGER REFERENCES motorcycles(id) | Link to motorcycle reference |
| source | VARCHAR(50) | CycleTrader, Facebook, eBay, etc. |
| url | TEXT UNIQUE | Original listing URL |
| title | TEXT | Listing title |
| price | DECIMAL(10,2) | Listed price |
| mileage | INTEGER | Odometer reading |
| year | INTEGER | Year (denormalized for queries) |
| location_city | VARCHAR(100) | City |
| location_state | VARCHAR(50) | State |
| location_zip | VARCHAR(10) | ZIP code |
| description | TEXT | Full listing description |
| seller_type | VARCHAR(50) | Private, Dealer, etc. |
| title_status | VARCHAR(50) | Clean, Salvage, Rebuilt |
| condition | VARCHAR(50) | Excellent, Good, Fair, Poor |
| modifications | TEXT | Aftermarket parts mentioned |
| is_active | BOOLEAN | Still available? |
| scraped_at | TIMESTAMP | When scraped |
| updated_at | TIMESTAMP | Last update |
| metadata | JSONB | Additional unstructured data |

### Table: `images`
Listing images and AI analysis results.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| listing_id | INTEGER REFERENCES listings(id) | Parent listing |
| url | TEXT | Image URL |
| position | INTEGER | Order in listing |
| ai_analysis | JSONB | GPT-4 Vision analysis results |
| analyzed_at | TIMESTAMP | When analyzed |
| created_at | TIMESTAMP | Record creation |

### Table: `price_history`
Historical price tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| motorcycle_id | INTEGER REFERENCES motorcycles(id) | Which bike |
| avg_price | DECIMAL(10,2) | Average price |
| median_price | DECIMAL(10,2) | Median price |
| min_price | DECIMAL(10,2) | Minimum price |
| max_price | DECIMAL(10,2) | Maximum price |
| sample_size | INTEGER | Number of listings |
| date | DATE | Date of snapshot |
| created_at | TIMESTAMP | Record creation |

### Table: `evaluations`
Listing evaluation scores and breakdown.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| listing_id | INTEGER REFERENCES listings(id) | Evaluated listing |
| overall_score | DECIMAL(5,2) | 0-100 composite score |
| letter_grade | VARCHAR(2) | A+, A, A-, B+, etc. |
| price_score | DECIMAL(5,2) | Price component (0-100) |
| mileage_score | DECIMAL(5,2) | Mileage component (0-100) |
| quality_score | DECIMAL(5,2) | Listing quality (0-100) |
| condition_score | DECIMAL(5,2) | AI-assessed condition (0-100) |
| red_flags | JSONB | Array of detected issues |
| recommendations | TEXT | Generated recommendations |
| comparable_listings | JSONB | Similar listings for comparison |
| evaluated_at | TIMESTAMP | When evaluated |

## Scoring Algorithm

### Composite Score Calculation
```
Overall Score = (Price Score × 0.40) +
                (Mileage Score × 0.20) +
                (Quality Score × 0.15) +
                (Condition Score × 0.10) +
                (Red Flags Penalty × 0.10) +
                (Location Score × 0.05)
```

### Component Scoring Details

#### 1. Price Score (40% weight)
- Calculate market average for make/model/year/mileage range
- Score based on deviation from average:
  - 20%+ below market: 100 points
  - 10-20% below: 90 points
  - 5-10% below: 80 points
  - Within 5%: 70 points
  - 5-10% above: 60 points
  - 10-20% above: 40 points
  - 20%+ above: 20 points

#### 2. Mileage Score (20% weight)
- Calculate expected mileage range for year (assume ~3,000 mi/year for sportbikes)
- Score based on actual vs expected:
  - Significantly under expected: 100 points
  - Under expected: 85 points
  - Average range: 70 points
  - Above expected: 50 points
  - Significantly above: 30 points

#### 3. Quality Score (15% weight)
- Photo count (0-10 scale)
- Description length/detail (0-10 scale)
- Mentions of service records (+10 points)
- Professional photos (+5 points)

#### 4. Condition Score (10% weight)
- AI vision analysis of images:
  - No visible damage: 100 points
  - Minor cosmetic issues: 80 points
  - Moderate wear: 60 points
  - Significant damage: 30 points
  - Major damage: 10 points

#### 5. Red Flags Penalty (10% weight)
- Salvage title: -40 points
- Rebuilt title: -25 points
- Accident mentioned: -20 points
- Inconsistent information: -15 points
- Suspiciously low price: -30 points
- Poor photo quality: -10 points

#### 6. Location Score (5% weight)
- Regional price variations
- Seasonal adjustments

### Letter Grade Mapping
- **A+ (95-100):** Exceptional deal
- **A (90-94):** Excellent deal
- **A- (85-89):** Very good deal
- **B+ (80-84):** Good deal
- **B (75-79):** Fair deal
- **B- (70-74):** Slightly below average
- **C+ (65-69):** Below average
- **C (60-64):** Poor deal
- **C- (55-59):** Very poor deal
- **D (50-54):** Bad deal
- **F (<50):** Avoid

## Data Sources

### Primary Sources (Phase 1)
1. **CycleTrader** (cycletrader.com)
   - Structured data
   - Professional dealers + private sellers
   - Good photo quality
   - Reliable specifications

2. **Facebook Marketplace** (facebook.com/marketplace)
   - Largest inventory
   - Mostly private sellers
   - Less structured data
   - Variable photo quality

### Secondary Sources (Phase 2)
3. **eBay Motors** (ebay.com/motors)
4. **Craigslist** (craigslist.org)
5. **Bring a Trailer** (bringatrailer.com) - High-end market

### Price Reference Sources
- KBB Motorcycle Values (if API available)
- NADA Guides
- Internal historical database

## Features

### Phase 1: MVP CLI Tool

#### Command: `moto-eval scrape`
Populate database with listings.
```bash
moto-eval scrape --source cycletrader --make ducati --model "panigale v4"
moto-eval scrape --source facebook --make ducati --model "panigale v4" --location "San Francisco, CA"
moto-eval scrape --all  # Scrape all configured sources
```

#### Command: `moto-eval analyze <url>`
Evaluate a specific listing.
```bash
moto-eval analyze https://cycletrader.com/listing/...
```

**Output:**
```
═══════════════════════════════════════════════════════
  MOTORCYCLE LISTING EVALUATION
═══════════════════════════════════════════════════════

2022 Ducati Panigale V4 S
$24,500 • 3,200 miles • San Francisco, CA

OVERALL GRADE: A- (87/100)
─────────────────────────────────────────────────────

SCORE BREAKDOWN:
  💰 Price Score:         92/100  (12% below market)
  🛣️  Mileage Score:      85/100  (Average for year)
  📸 Listing Quality:    78/100  (8 photos, detailed)
  🔧 Condition:          90/100  (Excellent condition)
  ⚠️  Red Flags:         -5/100  (Minor: No service records)
  📍 Location:           72/100  (Average for region)

MARKET COMPARISON:
  Market Average: $27,800 (42 comparable listings)
  This Listing:   $24,500 (12% below average)
  Market Range:   $22,000 - $32,000

COMPARABLE LISTINGS:
  1. 2022 Panigale V4 S • 2,800 mi • $26,500 • Los Angeles
  2. 2022 Panigale V4   • 4,100 mi • $23,900 • Oakland
  3. 2021 Panigale V4 S • 5,200 mi • $24,000 • Sacramento

RECOMMENDATIONS:
  ✓ Good deal - price below market average
  ✓ Low mileage for year
  ⚠ Request service records before purchase
  ⚠ Verify clean title in person

═══════════════════════════════════════════════════════
```

#### Command: `moto-eval stats`
Show market statistics.
```bash
moto-eval stats --make ducati --model "panigale v4" --year 2022
```

#### Command: `moto-eval update`
Refresh database (cron-able).
```bash
moto-eval update --days 7  # Re-scrape listings from last 7 days
```

### Phase 2: Web API (Future)

REST API endpoints:
- `POST /api/evaluate` - Evaluate a listing URL
- `GET /api/stats/{make}/{model}` - Market statistics
- `GET /api/listings` - Browse listings with filters
- `POST /api/scrape` - Trigger scrape job (authenticated)

### Phase 3: Frontend (Future)

- **Web App:** React dashboard for browsing and evaluating
- **Chrome Extension:** Overlay score on listing pages
- **Mobile App:** Browse listings and get notifications for deals

## Development Workflow

### Code Review Process
For each task:
1. **Implementation** - Complete the task with thorough testing
2. **Presentation** - Provide description, changes breakdown, test results
3. **Review** - User reviews and approves or requests changes
4. **Approval** - Move to next task only after approval

### Testing Requirements
- Unit tests for all modules
- Integration tests for pipelines
- All tests must pass before code review
- Minimum 80% code coverage

### Documentation Requirements
- Inline code documentation
- API documentation (docstrings)
- Architecture documentation (this file)
- User documentation (README)

## Project Structure

```
motoPrice/
├── src/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py              # CLI entry point
│   │   ├── commands/
│   │   │   ├── scrape.py
│   │   │   ├── analyze.py
│   │   │   ├── stats.py
│   │   │   └── update.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseScraper class
│   │   ├── cycletrader.py
│   │   ├── facebook.py
│   │   └── ebay.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── connection.py        # DB connection manager
│   │   └── migrations/          # Alembic migrations
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── price_analyzer.py
│   │   ├── mileage_analyzer.py
│   │   ├── quality_analyzer.py
│   │   ├── ai_vision.py
│   │   └── red_flags.py
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── scorer.py            # Composite scoring
│   │   └── comparator.py        # Find similar listings
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # Configuration management
│       ├── logger.py            # Logging setup
│       └── validators.py        # Data validation
├── tests/
│   ├── __init__.py
│   ├── test_scrapers/
│   ├── test_analysis/
│   ├── test_scoring/
│   └── fixtures/
├── config/
│   ├── config.yaml              # Default configuration
│   └── .env.example             # Environment variables template
├── data/                        # Local data storage
├── docs/                        # Additional documentation
├── alembic.ini                  # Alembic configuration
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata
├── pytest.ini                   # Pytest configuration
├── .gitignore
├── README.md
├── spec.md                      # This file
├── roadmap.md                   # Development roadmap
└── CLAUDE.md                    # Project context for Claude
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/motoprice

# OpenAI
OPENAI_API_KEY=sk-...

# Scraping
USER_AGENT_ROTATION=true
REQUEST_DELAY_MS=1000
MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/motoprice.log
```

### config.yaml
```yaml
database:
  pool_size: 10
  max_overflow: 20

scraping:
  sources:
    - cycletrader
    - facebook
  delay_between_requests: 1.0
  timeout: 30
  max_retries: 3

scoring:
  weights:
    price: 0.40
    mileage: 0.20
    quality: 0.15
    condition: 0.10
    red_flags: 0.10
    location: 0.05

ai:
  provider: openai
  model: gpt-4-vision-preview
  cache_results: true
```

## Performance Targets

- Scrape 100 listings in < 5 minutes
- Analyze single listing in < 10 seconds
- Database query response < 500ms
- Support 10,000+ listings in database

## Future Enhancements

### Phase 4+
- Real-time price alerts via email/SMS
- Machine learning price prediction model
- VIN decoding and history checks
- Automated listing monitoring
- Price negotiation suggestions
- Financing calculator integration
- Insurance quote integration

## Security & Privacy

- No storage of user credentials
- API keys in environment variables only
- Respectful scraping (rate limiting, robots.txt)
- GDPR compliance for user data (future)
- Secure API authentication (future)

## Success Metrics

### MVP Success Criteria
- Successfully scrape 500+ Ducati Panigale V4 listings
- Analyze listings with <10 second latency
- 90%+ accuracy in data extraction
- All tests passing with 80%+ coverage
- Zero critical bugs

### Product Success Criteria (Future)
- 10,000+ active users
- 100,000+ listings in database
- <1% error rate
- 99.9% uptime
