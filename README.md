# 🎯 Lead Generation & Outreach Tool

A complete, production-ready Python system that finds small/local businesses,
detects those without websites or running NopCommerce, collects public contact
emails, and sends throttled, personalized outreach emails automatically.

---

## 📁 Project Structure

```
lead_gen/
├── main.py            # CLI entry point
├── config.py          # Configuration (loads .env)
├── database.py        # SQLite persistence layer
├── collector.py       # Google Maps Places API lead collection
├── analyzer.py        # NopCommerce / no-website detection
├── email_extractor.py # Email scraping from public web pages
├── mailer.py          # SMTP / SendGrid email sending with throttling
├── scheduler.py       # APScheduler automated pipeline
├── utils.py           # Logging, helpers
├── requirements.txt
├── .env.example       # Configuration template
└── README.md
```

---

## ⚙️ Setup

### 1. Prerequisites

- Python 3.11 or higher
- A Google Maps Platform account with the **Places API** enabled
- An SMTP-capable email account (Gmail recommended with an App Password)

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Description |
|---|---|
| `GOOGLE_MAPS_API_KEY` | Your Google Maps Platform API key |
| `SMTP_USER` | Your sender email address |
| `SMTP_PASSWORD` | Your email app password |
| `SENDER_NAME` | Your display name in outreach emails |
| `MAX_EMAILS_PER_HOUR` | Throttle limit (default: 10) |

> **Gmail tip**: Go to your Google Account → Security → App Passwords, and
> generate a password for "Mail". Use that as `SMTP_PASSWORD`.

### 4. Get a Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable the **Places API**
4. Create an API key under Credentials
5. Paste the key into `.env`

---

## 🚀 Usage

### Collect leads

```bash
python main.py collect --keyword "clothing stores" --location "London"
python main.py collect --keyword "restaurants" --location "Amsterdam" --max-results 50
```

### Analyze websites (NopCommerce / no-website detection)

```bash
python main.py analyze
python main.py analyze --limit 100
```

### Extract emails from websites

```bash
python main.py extract
python main.py extract --limit 30
```

### Send outreach emails

```bash
# Dry run (simulate without sending)
python main.py send_emails --dry-run

# Send up to 10 emails (respects hourly cap from .env)
python main.py send_emails --limit 10
```

### View statistics

```bash
python main.py stats
```

### Start automated scheduler

```bash
python main.py schedule
```

The scheduler runs the full pipeline automatically based on
`SCHEDULE_SEND_INTERVAL_HOURS` (default every 6 hours).

---

## 🔁 Full Example Workflow

```bash
# Step 1 – collect leads
python main.py collect --keyword "shoe shops" --location "Berlin" --max-results 40

# Step 2 – analyze each website
python main.py analyze --limit 40

# Step 3 – extract contact emails
python main.py extract --limit 40

# Step 4 – dry run to preview
python main.py send_emails --dry-run --limit 10

# Step 5 – send for real
python main.py send_emails --limit 10

# Step 6 – check results
python main.py stats
```

---

## 📧 Email Template

The default template reads from `.env` (`EMAIL_BODY_TEMPLATE`).
Supported placeholders:

| Placeholder | Value |
|---|---|
| `{business_name}` | Business name from Google Maps |
| `{sender_name}` | Your name from `SENDER_NAME` |

Default body:
```
Hi {business_name},

I came across your business and noticed it may not have a website,
or could benefit from a more modern online store.

I specialize in building fast, scalable eCommerce solutions.
I'd love to help you establish or improve your online presence.

Would you be open to a quick 15-minute chat?

Best regards,
{sender_name}
```

---

## 🗄️ Database Schema

| Table | Purpose |
|---|---|
| `leads` | Business records from Google Maps |
| `emails` | Extracted contact emails per lead |
| `outreach_log` | Record of every email sent/failed/simulated |

---

## ⚠️ Legal & Ethical Notes

- Only uses **official, allowed APIs** (Google Maps Places API)
- Only collects **publicly visible** email addresses
- Respects **rate limits** on all HTTP requests
- Built-in **hourly email throttle** to avoid spam
- Does **not** scrape Google search result pages
- Always include an **unsubscribe mechanism** in production use
- Review the **CAN-SPAM Act**, **GDPR**, and local regulations before sending

---

## 🛠️ Troubleshooting

| Issue | Fix |
|---|---|
| `GOOGLE_MAPS_API_KEY not set` | Add key to `.env` |
| `SMTP credentials not configured` | Set `SMTP_USER` and `SMTP_PASSWORD` |
| `Hourly cap reached` | Wait an hour or increase `MAX_EMAILS_PER_HOUR` |
| `No qualifying leads to email` | Run `collect`, `analyze`, `extract` first |
| Gmail authentication fails | Use an App Password, not your account password |
