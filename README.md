# motoPrice

Motorcycle listing evaluator. Analyzes listings to identify good deals based on price, mileage, condition, and other factors.

## Overview

Scrapes motorcycle listings from multiple marketplaces (CycleTrader, Facebook Marketplace, eBay Motors), builds a database, and scores each listing using rule-based algorithms and AI vision analysis.

Current Status: Phase 1 - Foundation & Setup

## Features

Planned functionality:

- Automated scraping from multiple sources
- Market price analysis and comparison
- AI vision analysis for condition assessment
- Scoring algorithm (grades A+ to F)
- Red flag detection (salvage titles, accidents, scams)
- CLI interface (Phase 1)
- Web application (Phase 2+)

## Installation

Prerequisites:
- Python 3.11+
- PostgreSQL 15+
- Git

```bash
git clone https://github.com/stjepanvrbic/motoPrice.git
cd motoPrice

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
playwright install

cp config/.env.example .env
# Edit .env with database URL, API keys, etc.

alembic upgrade head
```

## Usage

Commands (planned - not yet implemented):

```bash
moto-eval scrape --source cycletrader --make ducati --model "panigale v4"
moto-eval analyze https://cycletrader.com/listing/...
moto-eval stats --make ducati --model "panigale v4" --year 2022
moto-eval update
```

## Project Structure

```
motoPrice/
├── src/              # Source code
│   ├── cli/         # CLI interface
│   ├── scrapers/    # Web scrapers
│   ├── database/    # Database models
│   ├── analysis/    # Analysis modules
│   ├── scoring/     # Scoring algorithms
│   └── utils/       # Utilities
├── tests/           # Test suite
├── config/          # Configuration
├── docs/            # Documentation
├── spec.md          # Technical specification
└── roadmap.md       # Development roadmap
```

## Development

Run tests:
```bash
pytest
pytest --cov=src --cov-report=html
```

Code quality:
```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

Pre-commit hooks run automatically before each commit.

## Scoring Algorithm

Composite score (0-100) weighted by:

- Price vs Market: 40%
- Mileage Analysis: 20%
- Listing Quality: 15%
- Condition (AI): 10%
- Red Flags: 10%
- Location: 5%

Letter grades from A+ (95-100) to F (<50).

## Documentation

- [spec.md](spec.md) - Technical specification
- [roadmap.md](roadmap.md) - Development roadmap

## Technology

- Python 3.11+
- PostgreSQL
- Playwright, BeautifulSoup4
- OpenAI GPT-4 Vision API
- Click, Rich
- Pytest

## License

MIT License - See LICENSE file.
