# Facebook Authentication Setup

Facebook Marketplace requires authentication to scrape listings. This guide shows you how to set up authentication for the motoPrice scraper.

## Why Authentication is Required

Facebook Marketplace is a logged-in experience. Without authentication:
- No search results are returned
- Listing details cannot be accessed
- Tests will fail

**This is NOT optional** - the scraper will not work without proper authentication.

## Authentication Methods

The scraper supports 3 methods of authentication (tried in order):

1. **Saved Session** (recommended - fastest, most reliable)
2. **Session Cookies** (good for automation)
3. **Email/Password** (fallback, may trigger 2FA)

### Method 1: Saved Session (Recommended)

The first time you authenticate with email/password, the scraper automatically saves your session to `.facebook_session.json`. On subsequent runs, it will reuse this session without requiring login.

**Advantages:**
- Fast (no login required)
- Reliable (no 2FA prompts)
- Automatic (just log in once)

**Setup:**
1. Add your Facebook credentials to `.env` (see Method 3)
2. Run the scraper once - it will log in and save the session
3. Future runs will use the saved session automatically

The session file is automatically added to `.gitignore` and will not be committed.

### Method 2: Session Cookies (For Automation)

If you want to avoid email/password login entirely, you can provide session cookies directly.

**Setup:**

1. Log into Facebook in your browser
2. Open browser Developer Tools (F12 or Right Click → Inspect)
3. Go to Application → Cookies → https://www.facebook.com
4. Copy these cookie values:
   - `c_user`
   - `xs`
   - `fr` (optional)

5. Add to your `.env` file as JSON:
```bash
FACEBOOK_COOKIES_JSON={"c_user": "your_user_id_here", "xs": "your_xs_token_here"}
```

**Example:**
```bash
FACEBOOK_COOKIES_JSON={"c_user": "100012345678901", "xs": "1%3A2abc...xyz%3D"}
```

### Method 3: Email/Password (Fallback)

**Setup:**

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Facebook credentials:
```bash
FACEBOOK_EMAIL=your-email@example.com
FACEBOOK_PASSWORD=your-password-here
```

3. Run the scraper - it will log in automatically

**Important:**
- Use your actual Facebook email and password
- If you have 2FA enabled, you'll need to complete it in the browser window
- The scraper will wait up to 2 minutes for you to complete 2FA
- After successful login, the session is saved for future use

## Two-Factor Authentication (2FA)

If your Facebook account has 2FA enabled:

1. The scraper will detect the 2FA prompt
2. A browser window will open
3. Complete the 2FA verification in the browser
4. The scraper will wait up to 2 minutes
5. Once verified, the session is saved for future use

**Note:** You only need to do this once - the saved session will work on subsequent runs.

## Security Best Practices

1. **Never commit `.env` file** - it's in `.gitignore` for a reason
2. **Never commit `.facebook_session.json`** - also in `.gitignore`
3. **Use app-specific password** if possible (see Facebook Security Settings)
4. **Rotate credentials regularly**
5. **Don't share your session file** - it's equivalent to your password

## Troubleshooting

### "Facebook authentication required" Error

**Problem:** No credentials found

**Solution:** Add `FACEBOOK_EMAIL` and `FACEBOOK_PASSWORD` to `.env` file

### "Facebook login failed. Check your credentials."

**Problem:** Wrong email/password

**Solution:**
- Double-check your credentials in `.env`
- Try logging in manually at facebook.com to verify they work
- Check for typos

### "CAPTCHA verification timeout"

**Problem:** Didn't solve CAPTCHA in time

**Solution:**
- Facebook may show CAPTCHA on first login from new location/device
- The scraper waits up to 3 minutes for you to solve it
- Solve the CAPTCHA in the browser window that opens
- Once completed, login will continue automatically
- After successful login, session is saved and CAPTCHA won't be needed again

### "2FA verification timeout"

**Problem:** Didn't complete 2FA in time

**Solution:**
- Run the scraper again
- Complete 2FA quickly (within 2 minutes)
- Once done, session is saved and won't be needed again

### Session Expired

**Problem:** Saved session no longer works

**Solution:**
- Delete `.facebook_session.json`
- Run scraper again to create new session
- The scraper will automatically re-authenticate

### Tests Still Skip

**Problem:** Integration tests are skipping

**Solution:**
- Make sure `.env` has `FACEBOOK_EMAIL` and `FACEBOOK_PASSWORD`
- Try running integration tests with `-s` flag to see login process:
  ```bash
  python -m pytest tests/integration/testFacebookIntegration.py -v -s
  ```
- Check logs for authentication errors

## Verifying Authentication Works

### Quick Test

```python
from src.scrapers.facebook import FacebookMarketplaceScraper

# This will test authentication
with FacebookMarketplaceScraper() as scraper:
    results = scraper.search(query="motorcycle", maxPages=1)
    print(f"Found {len(results)} listings")
    if results:
        print(f"First listing: {results[0].get('title')}")
```

If this prints listings, authentication is working!

### Run Integration Tests

```bash
# Run all Facebook integration tests
python -m pytest tests/integration/testFacebookIntegration.py -v

# Run with output to see authentication process
python -m pytest tests/integration/testFacebookIntegration.py -v -s
```

All tests should **PASS** (not skip) when auth is configured.

## How Authentication Works Internally

1. Scraper checks for saved session file (`.facebook_session.json`)
2. If found, loads cookies and verifies they still work
3. If not found or expired, checks for `FACEBOOK_COOKIES_JSON` env var
4. If not found, falls back to email/password login
5. After successful login, saves session for future use

The authentication happens automatically when you call `search()` or `scrapeListingDetails()`.

## Example .env File

```bash
# Database Connection
DATABASE_URL=postgresql://user:password@localhost:5432/motoprice

# OpenAI API Key
OPENAI_API_KEY=sk-...

# Facebook Authentication
FACEBOOK_EMAIL=your.email@example.com
FACEBOOK_PASSWORD=your_password_here

# Alternative: Session Cookies (choose either this OR email/password)
# FACEBOOK_COOKIES_JSON={"c_user": "100012345678901", "xs": "1%3A2abc...xyz%3D"}
```

## Common Questions

**Q: Do I need to log in every time?**
A: No, the session is saved after first login.

**Q: How long does the session last?**
A: Typically 30-90 days, but Facebook can invalidate it anytime.

**Q: Can I use a fake account?**
A: Not recommended - Facebook detects and bans fake accounts.

**Q: Will this get my account banned?**
A: We use realistic browser fingerprints and human-like behavior to minimize risk, but scraping violates Facebook's ToS. Use at your own risk.

**Q: Can I scrape without a Facebook account?**
A: No, authentication is required for Facebook Marketplace.

## Next Steps

Once authentication is configured:

1. Run integration tests to verify: `python -m pytest tests/integration/testFacebookIntegration.py -v`
2. Try manual scraping (see TESTING.md)
3. Build your complete scraping pipeline

For more testing examples, see [TESTING.md](../TESTING.md).
