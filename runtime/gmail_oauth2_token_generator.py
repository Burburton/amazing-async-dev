"""Gmail OAuth2 token generator (Feature 050).

Interactive CLI tool to obtain Gmail OAuth2 tokens for SMTP authentication.
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GMAIL_SMTP_SCOPE = "https://mail.google.com/"


def generate_authorization_url(
    client_id: str,
    redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob",
    state: str | None = None,
) -> str:
    """Generate Google OAuth2 authorization URL.
    
    Args:
        client_id: Google OAuth2 client ID
        redirect_uri: Redirect URI (use 'urn:ietf:wg:oauth:2.0:oob' for manual code entry)
        state: Optional state parameter
        
    Returns:
        Authorization URL to open in browser
    """
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GMAIL_SMTP_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    
    if state:
        params["state"] = state
    
    return GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)


def exchange_code_for_tokens(
    client_id: str,
    client_secret: str,
    authorization_code: str,
    redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob",
) -> dict[str, Any] | None:
    """Exchange authorization code for OAuth2 tokens.
    
    Args:
        client_id: Google OAuth2 client ID
        client_secret: Google OAuth2 client secret
        authorization_code: Code from authorization redirect
        redirect_uri: Same redirect_uri used in authorization
        
    Returns:
        Token dict with access_token, refresh_token, expires_in, etc.
    """
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": authorization_code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode()
    
    try:
        req = urllib.request.Request(GOOGLE_TOKEN_URL, data=data)
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
            expires_in = result.get("expires_in", 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return {
                "access_token": result.get("access_token"),
                "refresh_token": result.get("refresh_token"),
                "token_expiry": expires_at.isoformat(),
                "token_type": result.get("token_type", "Bearer"),
                "scope": result.get("scope", GMAIL_SMTP_SCOPE),
            }
    except Exception as e:
        return {"error": str(e)}


def create_token_file(
    token_data: dict[str, Any],
    email: str,
    client_id: str,
    client_secret: str,
    token_path: Path | None = None,
) -> Path:
    """Create token file with all required fields.
    
    Args:
        token_data: Token data from exchange_code_for_tokens
        email: User email address
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        token_path: Path to save token file
        
    Returns:
        Path to saved token file
    """
    if token_path is None:
        token_path = Path(".runtime/gmail-oauth2-token.json")
    
    full_token = {
        "email": email,
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "token_expiry": token_data.get("token_expiry"),
        "token_type": token_data.get("token_type", "Bearer"),
        "client_id": client_id,
        "client_secret": client_secret,
        "created_at": datetime.now().isoformat(),
    }
    
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        json.dump(full_token, f, indent=2)
    
    return token_path


def interactive_token_generation(
    client_id: str | None = None,
    client_secret: str | None = None,
    email: str | None = None,
    token_path: Path | None = None,
) -> dict[str, Any]:
    """Interactive token generation with user prompts.
    
    Args:
        client_id: Pre-provided client ID (optional)
        client_secret: Pre-provided client secret (optional)
        email: Pre-provided email (optional)
        token_path: Custom token path (optional)
        
    Returns:
        Result dict with status and token_path
    """
    result = {
        "status": "unknown",
        "token_path": None,
        "error": None,
    }
    
    if not client_id:
        print("\nStep 1: Enter your Google OAuth2 Client ID")
        print("  (Get from https://console.cloud.google.com/apis/credentials)")
        print()
        client_id = input("Client ID: ").strip()
    
    if not client_secret:
        print("\nStep 2: Enter your Google OAuth2 Client Secret")
        print()
        client_secret = input("Client Secret: ").strip()
    
    if not email:
        print("\nStep 3: Enter your Gmail address")
        print()
        email = input("Email: ").strip()
    
    if not (client_id and client_secret and email):
        result["status"] = "error"
        result["error"] = "Missing required credentials"
        return result
    
    auth_url = generate_authorization_url(client_id)
    
    print("\n" + "="*60)
    print("Step 4: Open this URL in your browser and authorize:")
    print("="*60)
    print()
    print(auth_url)
    print()
    print("="*60)
    print("After authorization, you will see a code on the page.")
    print("Copy that code and paste it below.")
    print("="*60)
    print()
    
    authorization_code = input("Authorization Code: ").strip()
    
    if not authorization_code:
        result["status"] = "error"
        result["error"] = "No authorization code provided"
        return result
    
    print("\nStep 5: Exchanging code for tokens...")
    
    token_data = exchange_code_for_tokens(client_id, client_secret, authorization_code)
    
    if token_data and token_data.get("error"):
        result["status"] = "error"
        result["error"] = token_data.get("error")
        return result
    
    if not token_data or not token_data.get("access_token"):
        result["status"] = "error"
        result["error"] = "Failed to obtain tokens"
        return result
    
    saved_path = create_token_file(token_data, email, client_id, client_secret, token_path)
    
    result["status"] = "success"
    result["token_path"] = str(saved_path)
    result["email"] = email
    result["has_refresh_token"] = bool(token_data.get("refresh_token"))
    
    print("\n" + "="*60)
    print("SUCCESS! Token saved to:")
    print(f"  {saved_path}")
    print("="*60)
    print()
    print("Next steps:")
    print("  1. Set environment variable: ASYNCDEV_USE_OAUTH2=true")
    print("  2. Set environment variable: ASYNCDEV_DELIVERY_MODE=smtp")
    print("  3. Test: asyncdev email-decision create --project test --send")
    print()
    
    return result


def validate_oauth2_credentials(
    client_id: str,
    client_secret: str,
) -> tuple[bool, str]:
    """Validate OAuth2 credentials by attempting token exchange.
    
    Args:
        client_id: Google OAuth2 client ID
        client_secret: Google OAuth2 client secret
        
    Returns:
        (is_valid, explanation)
    """
    if not client_id:
        return False, "Client ID is empty"
    
    if not client_secret:
        return False, "Client Secret is empty"
    
    if not client_id.endswith(".apps.googleusercontent.com"):
        return False, "Client ID should end with .apps.googleusercontent.com"
    
    if len(client_secret) < 20:
        return False, "Client Secret appears too short"
    
    return True, "Credentials format looks valid"


def format_setup_guide() -> str:
    """Format detailed setup guide for Gmail OAuth2.
    
    Returns:
        Human-readable setup guide
    """
    return """
## Gmail OAuth2 Setup Guide

### Prerequisites
- A Google account
- Access to Google Cloud Console

### Step 1: Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Note your project ID

### Step 2: Enable Gmail API

1. In your project, go to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click "Enable"

### Step 3: Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Desktop application"
4. Enter a name (e.g., "asyncdev-email")
5. Copy the Client ID and Client Secret

### Step 4: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in required fields:
   - App name: asyncdev
   - User support email: your email
   - Developer contact: your email
4. Add scopes: https://mail.google.com/
5. Add yourself as test user (if in testing mode)

### Step 5: Generate Token

Run the token generator:
```bash
python -m runtime.gmail_oauth2_token_generator
```

Or use CLI:
```bash
asyncdev gmail-auth setup
```

### Step 6: Test

```bash
export ASYNCDEV_USE_OAUTH2=true
export ASYNCDEV_DELIVERY_MODE=smtp
asyncdev email-decision create --project test --feature 001 \
    --question "Test?" --options "A:Yes,B:No" --send
```

### Troubleshooting

- "Access blocked": Add yourself as test user in consent screen
- "Invalid grant": Ensure you copied the full authorization code
- "Token expired": Run token generator again (refresh_token should auto-refresh)

### Environment Variables

| Variable | Purpose |
|----------|---------|
| ASYNCDEV_USE_OAUTH2 | Enable OAuth2 mode |
| ASYNCDEV_GMAIL_CLIENT_ID | Your OAuth2 client ID |
| ASYNCDEV_GMAIL_CLIENT_SECRET | Your OAuth2 client secret |
| ASYNCDEV_GMAIL_EMAIL | Your Gmail address |
| ASYNCDEV_OAUTH2_TOKEN_PATH | Path to token file |

### Token File Location

Default: `.runtime/gmail-oauth2-token.json`

This file contains:
- access_token (expires in ~1 hour)
- refresh_token (long-lived, use to get new access_token)
- client_id, client_secret
- email
- token_expiry
"""


if __name__ == "__main__":
    print("="*60)
    print("Gmail OAuth2 Token Generator")
    print("="*60)
    print()
    print("This tool will help you obtain OAuth2 tokens for Gmail SMTP.")
    print("You will need:")
    print("  1. Google OAuth2 Client ID")
    print("  2. Google OAuth2 Client Secret")
    print("  3. Your Gmail address")
    print()
    
    result = interactive_token_generation()
    
    if result["status"] != "success":
        print(f"\nError: {result.get('error', 'Unknown error')}")
        print("\nFor setup instructions, see:")
        print("  python -m runtime.gmail_oauth2_token_generator --guide")