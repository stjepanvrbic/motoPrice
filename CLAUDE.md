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
   - **STRICT WORKFLOW:** See "STRICT WORKFLOW - FOLLOW EXACTLY" section below
   - Branch → Implement → Test → Squash → Reviewer → PR → "Ship it!" → Merge → Update Roadmap
   - NEVER skip any step
   - NEVER work on main branch
   - NEVER present without reviewer approval
   - NEVER merge without "Ship it!"

## STRICT WORKFLOW - FOLLOW EXACTLY

### Step 1: Understand Current State
1. Read CLAUDE.md, spec.md, roadmap.md
2. Follow CLAUDE.md instructions STRICTLY
3. Find current position in roadmap.md (look for 🚧 In Progress or next ⏳ Pending task)
4. Read additional files for context if needed
5. Understand the current task's objectives, deliverables, and acceptance criteria

### Step 2: Create Branch and Implement
1. **CRITICAL: Create a new branch** for the current task
   - Branch name format: `task-X.Y-description` (e.g., `task-1.2-database-setup`)
   - NEVER work on main branch
2. Start implementing the task
3. **Full freedom during implementation:**
   - Write code, run commands, read files - NO permission needed
   - Add, commit, push to branch regularly
   - Commit often with descriptive messages
4. **BUT: Ask questions if unclear:**
   - If implementation details are unclear, ASK
   - If design choices are ambiguous, ASK
   - Don't make assumptions about requirements

### Step 3: Write Comprehensive Tests
1. When implementation is complete, write thorough tests
2. Target 100% test coverage (or as close as reasonably possible)
3. Test all functionality, edge cases, error conditions
4. Ensure ALL tests pass
5. Run tests multiple times to verify stability

### Step 4: Squash Commits
1. When implementation and tests are done and passing
2. Squash all commits in branch into ONE commit
3. Use descriptive commit message (see Commit Messages section)

### Step 5: Reviewer Agent Approval - CRITICAL
1. **MANDATORY: Launch reviewer sub-agent**
2. Reviewer checks EVERYTHING:
   - Code quality and alignment with spec.md
   - Test coverage and test quality
   - ALL roadmap.md deliverables completed
   - Manual testing where applicable
3. **Go back and forth with reviewer:**
   - Reviewer finds issues → fix them → reviewer checks again
   - Continue until reviewer approves
4. **NEVER skip this step**
5. **NEVER present to user without reviewer approval**

### Step 6: Create Pull Request
1. After reviewer approves, create pull request on GitHub
2. Use `gh pr create` command
3. PR title = first paragraph of commit message
4. PR body = remaining paragraphs of commit message
5. Ensure PR is visible on GitHub

### Step 7: Present to User
1. Tell user the PR is ready for review
2. Provide PR URL
3. Give summary of changes
4. **WAIT for user to say "Ship it!"**
5. **CRITICAL: Do NOT merge/commit to main until user says "Ship it!"**

### Step 8: After "Ship it!"
1. Merge PR to main
2. Update roadmap.md:
   - Mark task as ✅ Completed
   - Check off all deliverables
   - Update current task
3. Commit roadmap.md update

### Step 9: Repeat
Go back to Step 1 for next task

---

## CRITICAL RULES - NEVER VIOLATE

1. **NEVER work on main branch** - always create task branch
2. **NEVER present to user without reviewer approval first**
3. **NEVER merge to main without user saying "Ship it!"**
4. **ALWAYS squash commits before creating PR**
5. **ALWAYS use reviewer agent before creating PR**
6. **ALWAYS create PR on GitHub before presenting to user**
7. **ALWAYS update roadmap.md after "Ship it!"**

---

### Testing Requirements
- **Construct detailed, thorough tests** for each component
- Tests must be passing before presenting for review
- Each piece should be **independently testable**
- Build and test individual pieces thoroughly before integration
- **Target 100% test coverage** - aim for complete coverage, accept slightly less only if truly not feasible

### Progress Tracking
- **roadmap.md is automatically updated by the roadmap-update sub-agent**
- Sub-agent runs after every approved task commit
- Mark tasks as ✅ Completed, 🚧 In Progress, or ⏳ Pending
- Document interesting findings or important decisions in roadmap.md
- Note down anything important as we go
- **Never manually update roadmap.md - always use the sub-agent**

### Task Sizing Philosophy
The user emphasizes **bite-sized tasks** that:
- Can be tackled one by one
- Can be tested thoroughly in isolation
- Don't overload brain or context window
- Enable reliable execution
- Build confidence in robustness before integration

> "Having a detailed roadmap, and detailed smaller tasks also enables us to not overload my brain, and your context, and focus on tasks we can execute reliably."

---

## Sub-Agents

### Reviewer Agent
**Purpose:** Review and approve all code changes before presenting to user.

**When to Run:**
- **MANDATORY before every pull request to user**
- After implementation is complete and all tests pass
- Before creating the pull request on GitHub
- This is a STRICT requirement - NEVER present to user without reviewer approval

**What the Reviewer Does:**
1. **Review the Change Thoroughly:**
   - Go through all code changes in detail
   - Understand how changes fit with existing codebase
   - Verify alignment with design requirements in spec.md
   - Check for software engineering best practices
   - Ensure adequate test coverage (target 100%)
   - Verify tests are well-written and comprehensive

2. **Test Changes:**
   - Run all automated tests and verify they pass
   - Perform manual testing when applicable
   - Test edge cases and error conditions
   - Verify the code actually works as intended

3. **Check Roadmap Completeness:**
   - Read roadmap.md for current task
   - Verify ALL deliverables are completed
   - Verify ALL acceptance criteria are met
   - Check that nothing is missing or incomplete

4. **Go Back and Forth with Main Agent:**
   - If issues found: report them to main agent
   - Main agent fixes issues
   - Reviewer checks again
   - Continue until reviewer is satisfied

5. **Approve Only When Perfect:**
   - Only approve when ALL tasks are done to satisfaction
   - Only approve when tests are comprehensive and passing
   - Only approve when code quality is high
   - Once approved, hand off to main agent to create PR

**How to Invoke:**
```
Use Task tool with subagent_type="general-purpose"
Prompt: "You are the reviewer agent. Review the changes in branch X thoroughly:
- Check all code against spec.md requirements
- Verify test coverage is near 100%
- Test the changes manually
- Check roadmap.md task deliverables are complete
- Report any issues or approve if perfect"
```

**Critical Rules:**
- **NEVER present to user without reviewer approval**
- **Go back and forth with reviewer until approved**
- **Reviewer must check EVERYTHING before approval**
- **Only create PR after reviewer approves**

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
   - Look at "Current Task" field at top of roadmap.md
   - Check git log to see what was last committed
   - Review notes in "Notes & Decisions Log" section

2. **Verify last task completion:**
   - If there's a 🚧 In Progress task, it may not have been completed
   - Check if roadmap-update agent was run after last commit
   - If not, run it now to verify and update status

3. **Ask the user:**
   - Confirm what task to work on next
   - Check if priorities have changed
   - Ask about any new requirements

4. **Follow the strict workflow:**
   - Implement → Test → Present → Review → Approve → Commit → **Roadmap Update Agent** → Next Task
   - Never skip the roadmap update step
   - Document any important decisions

---

## Common Pitfalls to Avoid - READ THIS

1. **NEVER work on main branch** - Always create a task branch first
2. **NEVER commit to main directly** - All changes go through PR process
3. **NEVER present to user without reviewer approval** - Reviewer MUST approve first
4. **NEVER merge without "Ship it!"** - Only merge after user explicitly says "Ship it!"
5. **NEVER skip the reviewer agent** - It's mandatory before every PR
6. **NEVER skip creating a PR on GitHub** - User reviews on GitHub, not in chat
7. **NEVER skip squashing commits** - One clean commit per task
8. **NEVER skip updating roadmap.md** - Update after every "Ship it!"
9. **Don't skip testing** - 100% coverage target
10. **Don't make assumptions** - Ask if requirements unclear

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
