---
name: human-actions
description: >
  Use this skill whenever an agent needs to do something a human normally does:
  create an account on a web service, obtain an API key, register for an affiliate
  program, set up credentials, or manage authentication. This skill defines the
  COMPLETE protocol for automating account creation where possible and requesting
  human help where not possible. Trigger on: "create account", "register", "sign up",
  "get API key", "obtain credentials", "affiliate registration", "OAuth setup",
  "Gmail account", "save credentials", "credentials document".
---

# Human Actions Skill

## Philosophy
Every action a human does manually is a potential automation target.
This skill defines: what agents can do alone, what requires a human,
and how to request human help in the clearest possible way.

## Quick Reference

| Action | Can automate? | How |
|--------|--------------|-----|
| API key (most services) | Sometimes | HTTP registration flow |
| Gmail account | ❌ No | CAPTCHA + phone verification |
| YouTube channel | ❌ No | Requires Gmail |
| TikTok account | ❌ No | CAPTCHA + phone |
| Pexels API | ✅ Yes | Simple email form |
| Pixabay API | ✅ Yes | Simple email form |
| Affiliate programs | Partially | Register yes, verify email needs human |
| GitHub account | ❌ No | CAPTCHA |
| MongoDB Atlas | Partially | Create yes, email verify needs human |
| Gumroad | Partially | Basic setup possible |
| Notion | ✅ Yes | API available |

---

## Protocol A — Fully Automated Account Creation

For services with simple HTTP-based registration:

```python
import requests, json, secrets, string
from pathlib import Path
from datetime import datetime

def generate_password(length=16):
    """Generate a strong password. Never store plaintext — store reference."""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(chars) for _ in range(length))

def register_pexels(email: str, project_name: str = "VidFlow AI"):
    """Register for Pexels API automatically."""
    # Pexels requires form submission
    session = requests.Session()
    # 1. Get the registration page to extract CSRF token if needed
    # 2. Submit registration form
    # 3. Check for confirmation
    # Store result in credentials/accounts.json
    pass

def register_pixabay(email: str):
    """Register for Pixabay API automatically."""
    pass

def save_credentials(service: str, data: dict):
    """Save account credentials (never passwords in plaintext)."""
    creds_file = Path("credentials/accounts.json")
    creds_file.parent.mkdir(exist_ok=True)
    
    accounts = []
    if creds_file.exists():
        accounts = json.loads(creds_file.read_text())
    
    # Find and update existing or append new
    existing = next((a for a in accounts if a["service"] == service), None)
    if existing:
        existing.update(data)
        existing["last_updated"] = datetime.now().isoformat()
    else:
        data["service"] = service
        data["created_date"] = datetime.now().isoformat()
        accounts.append(data)
    
    creds_file.write_text(json.dumps(accounts, indent=2, ensure_ascii=False))
    
    # Update .env.example if there's a new API key variable
    if "api_key_env_var" in data:
        env_example = Path(".env.example")
        content = env_example.read_text() if env_example.exists() else ""
        var = data["api_key_env_var"]
        if var not in content:
            with env_example.open("a") as f:
                f.write(f"\n# {service}\n{var}=\n")
    
    print(f"✅ Credentials saved for {service}")
```

---

## Protocol B — Human-Required Registration

When automated registration is not possible:

```python
def request_human_registration(
    service: str,
    email_to_use: str,
    registration_url: str,
    form_fields: dict,
    env_variable_name: str,
    estimated_minutes: int,
    urgency: str = "IMPORTANT",  # BLOCKER | IMPORTANT | OPTIONAL
    why_needed: str = ""
):
    """
    Create a detailed request in NEEDS_FROM_HUMAN.md for manual registration.
    The request must be so clear that the human can do it in minimal time.
    """
    
    needs_file = Path("NEEDS_FROM_HUMAN.md")
    
    # Read existing content
    existing = needs_file.read_text() if needs_file.exists() else ""
    
    # Check if this request already exists
    if service in existing:
        return  # Already requested
    
    # Build the request in natural Spanish
    urgency_emoji = {"BLOCKER": "🚨", "IMPORTANT": "⚠️", "OPTIONAL": "💡"}[urgency]
    
    entry = f"""
## {urgency_emoji} Registrar cuenta en {service}
**Tiempo estimado:** {estimated_minutes} minutos
**Por qué se necesita:** {why_needed}

**Pasos exactos:**
1. Ve a: {registration_url}
2. Usa el email: `{email_to_use}`
"""
    
    for field, value in form_fields.items():
        entry += f"3. En el campo '{field}': escribe `{value}`\n"
    
    entry += f"""
**Cuando termines:**
- Copia la API key o token que te dieron
- Añádela a tu archivo .env como: `{env_variable_name}=TU_KEY_AQUI`

**El sistema continúa trabajando sin esto, pero {service} no estará disponible.**
"""
    
    # Append to needs file
    with needs_file.open("a") as f:
        f.write(entry)
    
    print(f"📝 Added registration request for {service} to NEEDS_FROM_HUMAN.md")
```

---

## Protocol C — Credentials Document Management

### Structure of credentials/accounts.json
```json
[
  {
    "service": "Pexels",
    "purpose": "Stock video footage for pipeline",
    "email": "tech@proyectovidflow.com",
    "username": "vidflow_ai",
    "created_date": "2025-04-13",
    "last_updated": "2025-04-13",
    "api_key_env_var": "PEXELS_API_KEY",
    "plan": "free",
    "limits": "200 req/hour",
    "notes": "Renew if 429 errors increase",
    "status": "active"
  }
]
```

### Never store in code or files
- Passwords in plaintext
- API keys in AGENT.md or SKILL.md files
- OAuth tokens (only reference to .env variable)
- Payment information

### Project email structure
Create `credentials/project_emails.md` (human fills this):
```
# Project Emails
# Fill these in — agents will use them for registrations

EMAIL_TECH=           # For APIs and technical services
EMAIL_MARKETING=      # For affiliate programs and newsletters
EMAIL_CONTENT=        # For content platforms
EMAIL_BACKUP=         # Backup email
```

---

## Protocol D — Affiliate Program Registration

Most affiliate programs require:
1. Email registration (often automated)
2. Website/channel URL (agent provides)
3. Description of how you'll promote (agent writes this)
4. Manual approval (1-7 days, nothing to do)

```python
def register_affiliate(
    program_name: str,
    registration_url: str,
    channel_url: str,
    promotion_method: str
):
    """
    Attempt automated registration for affiliate program.
    If not possible, creates detailed request in NEEDS_FROM_HUMAN.md.
    """
    
    # Standard promotion description for all channels
    promotion_desc = f"""
I run {channel_url}, a YouTube channel in the finance/psychology/AI niche with 
growing viewership. I promote relevant products through natural video mentions 
and description links. My audience is 20-40 years old, English-speaking, 
professionally oriented.
"""
    
    # Try automated approach first
    # If CAPTCHA or human verification required → request_human_registration()
    
    # After successful registration, track in:
    save_credentials(program_name, {
        "type": "affiliate",
        "registration_url": registration_url,
        "channel": channel_url,
        "status": "pending_approval",
        "promotion_method": promotion_method
    })
```

---

## Protocol E — OAuth Flow Setup

For YouTube API (required for video uploads):

```
One-time setup process (human required for first time):

1. Human goes to console.cloud.google.com
2. Creates project "VidFlow AI" 
3. Enables YouTube Data API v3
4. Creates OAuth 2.0 credentials (Desktop app type)
5. Downloads client_secret.json
6. Places it in credentials/youtube-[channel-name]-client.json
7. First time: run python scripts/setup_oauth.py --channel [channel-name]
   This opens a browser, human authorizes, token is saved automatically
8. After first auth: tokens refresh automatically (valid indefinitely)

Agent actions (no human needed after setup):
- Check if token exists and is valid
- Auto-refresh if expired (works silently)
- Only escalate if refresh_token is missing or account is suspended
```

---

## Usage Examples

### Agent-01 (Researcher) finding a new affiliate program:
```python
from skills.human_actions import request_human_registration

request_human_registration(
    service="Masterworks",
    email_to_use="EMAIL_MARKETING from credentials/project_emails.md",
    registration_url="masterworks.com/affiliate",
    form_fields={
        "First Name": "VidFlow",
        "Last Name": "AI",
        "Channel URL": "youtube.com/c/wealthfiles",
        "Monthly Views": "Growing — just started",
        "Promotion Method": "Natural video mentions + description links"
    },
    env_variable_name="MASTERWORKS_AFFILIATE_ID",
    estimated_minutes=10,
    urgency="IMPORTANT",
    why_needed="$50-100 CPA, perfect fit for Wealth Files audience"
)
```

### Agent-08 (Fixer) setting up a new API:
```python
from skills.human_actions import save_credentials

# After a new API key is configured:
save_credentials("NewsAPI", {
    "purpose": "Real-time news for content ideation",
    "email": "tech@project.com",
    "api_key_env_var": "NEWS_API_KEY",
    "plan": "free",
    "limits": "100 requests/day",
    "notes": "Use for morning trend research only"
})
```
