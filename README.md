# motoPrice - Motorcycle Listing Evaluator

A powerful tool to evaluate motorcycle listings and identify great deals based on price, mileage, condition, and other factors.

## Overview

motoPrice scrapes motorcycle listings from multiple marketplaces (CycleTrader, Facebook Marketplace, eBay Motors, etc.), builds a comprehensive database, and uses both rule-based algorithms and AI vision analysis to provide objective scoring for each listing.

**Current Status:** Phase 1 - Foundation & Setup ⏳

## Features (Planned)

- 🔍 **Automated Scraping** - Collect listings from multiple sources
- 📊 **Market Analysis** - Compare prices against market averages
- 🤖 **AI Vision** - Analyze photos for condition and damage
- 📈 **Scoring Algorithm** - Grade listings from A+ to F
- 🚩 **Red Flag Detection** - Identify salvage titles, accidents, scams
- 💰 **Deal Finder** - Spot underpriced listings
- 📱 **CLI Interface** - Easy command-line tool (Phase 1)
- 🌐 **Web App** - Browser-based interface (Phase 2+)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/motoPrice.git
cd motoPrice

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up Playwright browsers
playwright install

# Configure environment
cp config/.env.example .env
# Edit .env with your settings (database URL, API keys, etc.)

# Run database migrations
alembic upgrade head
```

### Usage

```bash
# Scrape listings
moto-eval scrape --source cycletrader --make ducati --model "panigale v4"

# Analyze a specific listing
moto-eval analyze https://cycletrader.com/listing/...

# View market statistics
moto-eval stats --make ducati --model "panigale v4" --year 2022

# Update database
moto-eval update
```

## Project Structure

```
motoPrice/
├── src/                # Source code
│   ├── cli/           # CLI interface
│   ├── scrapers/      # Web scrapers
│   ├── database/      # Database models
│   ├── analysis/      # Analysis modules
│   ├── scoring/       # Scoring algorithms
│   └── utils/         # Utilities
├── tests/             # Test suite
├── config/            # Configuration
├── docs/              # Documentation
├── spec.md            # Technical specification
├── roadmap.md         # Development roadmap
└── CLAUDE.md          # Project context
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_scrapers/test_cycletrader.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Scoring Algorithm

Listings are evaluated using a composite score (0-100) based on:

- **Price vs Market (40%)** - Comparison to similar listings
- **Mileage Analysis (20%)** - Expected vs actual mileage
- **Listing Quality (15%)** - Photos, description detail
- **Condition (10%)** - AI-assessed condition from photos
- **Red Flags (10%)** - Title status, accidents, anomalies
- **Location (5%)** - Regional price variations

Letter grades: **A+ (95-100)** to **F (<50)**

## Documentation

- [Technical Specification](spec.md) - Complete architecture and design
- [Development Roadmap](roadmap.md) - Detailed implementation plan
- [Project Context](CLAUDE.md) - Context for developers

## Technology Stack

- **Language:** Python 3.11+
- **Database:** PostgreSQL
- **Web Scraping:** Playwright, BeautifulSoup4
- **AI:** OpenAI GPT-4 Vision API
- **CLI:** Click/Typer + Rich
- **Testing:** Pytest

## Roadmap

### Phase 1: Foundation & Setup (In Progress)
- [x] Project initialization
- [ ] Database setup
- [ ] Configuration management

### Phase 2: Web Scraping
- [ ] Base scraper framework
- [ ] CycleTrader scraper
- [ ] Facebook Marketplace scraper

### Phase 3: Data Processing
- [ ] Data normalization
- [ ] Database pipeline
- [ ] Image handling

[See full roadmap](roadmap.md)

## Contributing

This is currently a personal project. Contributions, issues, and feature requests are welcome!

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with Claude Code - Anthropic's official CLI for Claude AI

---

**Note:** This project is in active development. Features and documentation may change frequently.
