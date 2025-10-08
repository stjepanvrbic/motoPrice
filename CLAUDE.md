# Project Context for Claude - Motorcycle Listing Evaluator

**Project Name:** motoPrice (Motorcycle Listing Evaluator)
**Last Updated:** October 8, 2025
**Current Status:** Planning complete, ready for implementation

---

## Project Overview

This is a backend-first system that evaluates motorcycle listings from various marketplaces (CycleTrader, Facebook Marketplace, eBay, etc.) and provides objective scoring based on price, mileage, condition, listing quality, and other factors. The goal is to help buyers identify good deals and avoid bad ones.

**Primary User:** Developer (stjepanvrbic) who is looking to buy a Ducati Panigale V4
**Primary Use Case:** Evaluate any motorcycle listing, with initial testing focused on Ducati Panigale V4

**End Goals:**
- Productize as web app, mobile app, and/or Chrome extension
- Build a robust backend first (scraping, database, scoring, analysis)
- Start with CLI tool, then add web interface later

---

## Coding Style & Conventions

### Naming Conventions
**CRITICAL:** User prefers camelCase for all naming.

- **Functions:** camelCase (e.g., `testPythonVersion`, `getListingData`)
- **Variables:** camelCase (e.g., `projectRoot`, `listingUrl`)
- **Filenames:** camelCase (e.g., `testEnvironment.py`, `cliMain.py`)
- **Classes:** PascalCase (e.g., `ListingAnalyzer`, `BaseScraper`)

**Configuration:**
- Pytest configured to recognize `test*` pattern (not just `test_*`)
- Ruff configured to ignore N802 and N806 (allows camelCase)

### Writing Style
User's style is **clear, concise, and direct**. No fluff.

**Do:**
- Write concise comments that explain what, not how
- Use direct language without epithets
- Be informational without being verbose
- Example: "Environment setup verification tests." (not "Tests to verify the development environment is set up correctly.")

**Don't:**
- Use emojis (unless explicitly requested)
- Use unnecessary adjectives ("powerful", "comprehensive", "robust")
- Use bold formatting excessively
- Add marketing language or superlatives

### Commit Messages
Format: Title paragraph, then detailed description.

**Title:**
- Concise summary of the change
- No emojis, no "feat:", "fix:" prefixes
- Example: "Project initialization and environment setup"

**Description:**
- Explain what was changed and what it does
- Audience is software engineers - they understand code
- No redundant words or epithets
- No phrases like "ensuring code quality is maintained" (obvious)
- Example: "Resolved dependency conflicts between pyproject.toml and requirements.txt - both now use psycopg v3 with binary support."

**Never include:**
- Claude-related information
- References to "Claude Code" or AI assistance
- Phrases like "foundation is solid and ready"

### Code Comments
- Brief and direct
- Focus on why, not what
- Example: "Can run git commands" (not "Verify we can run git commands")
- Example: "Key directories" (not "Check key directories")

## Key User Requirements & Preferences

### User Input Method
- User should be able to **paste a listing URL** and get an evaluation
- No manual data entry required (too much work)
- Tool should automatically scrape and analyze the listing

### Data Sources
- Must scrape data from the web to build our own database
- Primary sources: CycleTrader (structured), Facebook Marketplace (large inventory but less structured)
- Secondary sources: eBay Motors, Craigslist
- Database should include **everything we need**, not just prices
- Database must be **updated periodically** to stay current

### AI/ML Approach
- User is OK with API costs (already paying for Claude)
- User has access to VMs with powerful GPUs for local model inference
- **Phase 1:** Use OpenAI GPT-4 Vision API for simplicity and speed (MVP)
- **Phase 2:** Optionally migrate to local models (user finds this "fun")
- Both approaches should be explored, starting with APIs for faster MVP

### User Interface
- **Phase 1:** CLI tool (working product first, UI later)
- **Phase 2:** Web app
- **Future:** Chrome extension, mobile app, or all of the above

### Development Quality
- Must be **robust** - this is intended for production use
- Code should be thoroughly tested with comprehensive tests
- Tests must pass before any code is approved
- Database should support periodic updates

---

## Development Workflow

### Version Control & Git Workflow
**CRITICAL:** All work must be tracked in Git and pushed to GitHub.

1. **Repository Setup:**
   - Use Git for version control
   - Use GitHub for remote repository (via `gh` CLI)
   - Initialize repo at project start
   - Push to GitHub after initial setup

2. **Commit Strategy:**
   - **Commit after every accepted bite-sized task**
   - Commits should be granular and focused
   - Each commit represents one completed, tested, approved task
   - Write clear, descriptive commit messages
   - Example: "Add database models for motorcycles and listings"

3. **Source of Truth:**
   - **Git history is the source of truth** for project state
   - roadmap.md is a guide, not the definitive record
   - Use `git log` to see what's actually been done
   - Use GitHub for backup and collaboration

4. **Workflow Per Task:**
   - Implement → Test → Present → Review → Approve → **Commit & Push**
   - Never skip the commit step after approval
   - Push to GitHub regularly to ensure backup

### Code Review Process
The user wants a professional software engineering workflow with formal code reviews. For each task:

1. **Implementation Phase:**
   - Complete the task implementation
   - Write comprehensive, detailed tests
   - Ensure all tests pass

2. **Presentation Phase:**
   - Provide a description of the change (what and why)
   - Explain the changes file-by-file
   - Show test results (all tests must be passing)
   - Note any important decisions, trade-offs, or issues

3. **Review Phase:**
   - User reviews the code and tests
   - User may ask questions or request changes
   - User approves before moving to next task

4. **Approval & Commit Phase:**
   - Only move to next task after explicit approval
   - **Immediately create git commit for approved changes**
   - **Push to GitHub**
   - Update roadmap.md with completion status

### Testing Requirements
- **Construct detailed, thorough tests** for each component
- Tests must be passing before presenting for review
- Each piece should be **independently testable**
- Build and test individual pieces thoroughly before integration

### Progress Tracking
- Keep `roadmap.md` updated with progress
- Mark tasks as ✅ Completed, 🚧 In Progress, or ⏳ Pending
- Document interesting findings or important decisions in roadmap.md
- Note down anything important as we go

### Task Sizing Philosophy
The user emphasizes **bite-sized tasks** that:
- Can be tackled one by one
- Can be tested thoroughly in isolation
- Don't overload brain or context window
- Enable reliable execution
- Build confidence in robustness before integration

> "Having a detailed roadmap, and detailed smaller tasks also enables us to not overload my brain, and your context, and focus on tasks we can execute reliably."

---

## Technical Decisions

### Architecture
- **Language:** Python 3.11+
- **Database:** PostgreSQL (chosen for production scalability, JSON support, full-text search)
- **Web Scraping:** Playwright (dynamic sites), BeautifulSoup (static sites)
- **AI Provider:** OpenAI GPT-4 Vision (Phase 1), optional local models (Phase 2)
- **CLI Framework:** Click or Typer (TBD)
- **API Framework (future):** FastAPI

### Database Choice Rationale
- PostgreSQL over SQLite for production scalability
- JSON support for flexible listing data
- Full-text search capabilities
- Time-series features for price tracking
- Easy to migrate to cloud databases later

### Scraping Strategy
- Use respectful scraping (rate limiting, robots.txt compliance)
- Retry logic with exponential backoff
- User-agent rotation to avoid blocking
- Handle both static and dynamic content
- Deduplication by URL

### Scoring Algorithm
Composite score weighted as follows:
- Price vs Market: 40%
- Mileage Analysis: 20%
- Listing Quality: 15%
- AI Condition Assessment: 10%
- Red Flags Penalty: 10%
- Location Adjustment: 5%

Letter grades: A+ (95-100) to F (<50)

---

## Project Structure

```
motoPrice/
├── src/                    # Source code
│   ├── cli/               # CLI interface
│   ├── scrapers/          # Web scrapers
│   ├── database/          # DB models and operations
│   ├── analysis/          # Analysis modules
│   ├── scoring/           # Scoring algorithms
│   └── utils/             # Utilities (config, logging, etc.)
├── tests/                 # Test suite
├── config/                # Configuration files
├── data/                  # Local data storage
├── docs/                  # Documentation
├── spec.md                # Technical specification
├── roadmap.md             # Development roadmap
├── CLAUDE.md              # This file
└── README.md              # User-facing documentation
```

---

## Current Phase: Phase 1 - Foundation & Setup

**Next Task:** Task 1.1 - Project Initialization

### What's Been Done
- ✅ Brainstorming and requirements gathering
- ✅ Technical specification written (spec.md)
- ✅ Detailed roadmap created (roadmap.md)
- ✅ Project context documented (CLAUDE.md)

### What's Next
- Begin Task 1.1: Project Initialization
  - Create directory structure
  - Set up Python virtual environment
  - Create requirements.txt
  - Initialize project metadata
  - Set up .gitignore and README

---

## Important Context for New Claude Instances

### User Expectations
1. **Professional workflow** - Treat this like a software engineering job
2. **Thorough testing** - Tests are mandatory and must pass
3. **Bite-sized progress** - Small, testable tasks over large changes
4. **Code review approval** - Don't proceed without approval
5. **Robust implementation** - This is for production, not a prototype

### User's Technical Background
- Comfortable with Python, databases, web scraping, ML
- Has access to GPU VMs for local model inference
- Interested in exploring both API and local model approaches
- Values clean, maintainable code

### User's Goals
1. **Immediate:** Find good deals on Ducati Panigale V4 motorcycles
2. **Short-term:** Build a working CLI tool for evaluating any motorcycle
3. **Long-term:** Productize as web/mobile app or browser extension

### Communication Style
- User appreciates concise, direct communication
- User wants explanations of changes, not just code dumps
- User will ask questions if something is unclear
- User approves explicitly before moving forward

---

## Key Files Reference

- **spec.md** - Complete technical specification (architecture, database schema, features)
- **roadmap.md** - Detailed execution roadmap (9 phases, bite-sized tasks)
- **CLAUDE.md** - This file (project context, user preferences, workflow)

---

## Resuming Work

If resuming work after a break:

1. **Check current status:**
   - Read roadmap.md to see current phase and task
   - Look for 🚧 In Progress tasks
   - Review notes in "Notes & Decisions Log" section

2. **Understand the last task:**
   - What was being worked on?
   - Was it completed and approved?
   - Are there any blockers noted?

3. **Ask the user:**
   - Confirm what task to work on next
   - Check if priorities have changed
   - Ask about any new requirements

4. **Follow the workflow:**
   - Implement → Test → Present → Review → Approve
   - Update roadmap.md with progress
   - Document any important decisions

---

## Common Pitfalls to Avoid

1. **Don't skip testing** - User requires comprehensive tests
2. **Don't batch completions** - Mark tasks complete immediately when done
3. **Don't proceed without approval** - Wait for explicit user approval
4. **Don't make assumptions** - Ask if requirements are unclear
5. **Don't create large changes** - Break into bite-sized tasks
6. **Don't forget to update roadmap.md** - Keep progress tracking current
7. **Don't forget to commit** - ALWAYS commit and push after approval
8. **Don't make large commits** - One commit per bite-sized task

---

## Success Criteria for MVP

The MVP (Phases 1-9) is considered successful when:
- ✅ Successfully scrape 500+ Ducati Panigale V4 listings
- ✅ Analyze listings with <10 second latency
- ✅ 90%+ accuracy in data extraction
- ✅ All tests passing with 80%+ coverage
- ✅ Zero critical bugs
- ✅ Complete documentation

---

**Remember:** This is a production-quality project with a professional workflow. Take time to build things right, test thoroughly, and communicate clearly with the user.
