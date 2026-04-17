"""Gmail OAuth2 authentication helpers for SMTP (Feature 050).

Provides XOAUTH2 authentication for Gmail SMTP without requiring plaintext password.
"""

import base64
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

GOOGLE_OAUTH2_SCOPES = [
    "https://mail.google.com/",
]


def build_xoauth2_auth_string(email: str, access_token: str) -> str:
    """Build XOAUTH2 authentication string for Gmail SMTP.
    
    Args:
        email: User email address
        access_token: OAuth2 access token
        
    Returns:
        Base64 encoded auth string for AUTH XOAUTH2 command
    """
    auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")


def create_oauth2_config_from_env() -> dict[str, Any]:
    """Create OAuth2 config from environment variables.
    
    Returns:
        OAuth2 config dict with email, access_token, refresh_token, etc.
    """
    return {
        "email": os.getenv("ASYNCDEV_GMAIL_EMAIL", ""),
        "access_token": os.getenv("ASYNCDEV_GMAIL_ACCESS_TOKEN", ""),
        "refresh_token": os.getenv("ASYNCDEV_GMAIL_REFRESH_TOKEN", ""),
        "client_id": os.getenv("ASYNCDEV_GMAIL_CLIENT_ID", ""),
        "client_secret": os.getenv("ASYNCDEV_GMAIL_CLIENT_SECRET", ""),
        "token_expiry": os.getenv("ASYNCDEV_GMAIL_TOKEN_EXPIRY", ""),
    }


def load_oauth2_token_file(token_path: Path) -> dict[str, Any] | None:
    """Load OAuth2 token from JSON file.
    
    Args:
        token_path: Path to token JSON file
        
    Returns:
        Token dict or None if not found
    """
    if not token_path.exists():
        return None
    
    with open(token_path) as f:
        return json.load(f)


def save_oauth2_token_file(token_path: Path, token_data: dict[str, Any]) -> None:
    """Save OAuth2 token to JSON file.
    
    Args:
        token_path: Path to token JSON file
        token_data: Token data dict
    """
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)


def is_token_expired(token_data: dict[str, Any]) -> bool:
    """Check if OAuth2 token is expired.
    
    Args:
        token_data: Token data dict
        
    Returns:
        True if expired or no expiry info
    """
    expiry = token_data.get("token_expiry") or token_data.get("expires_at")
    if not expiry:
        return True
    
    if isinstance(expiry, int):
        expiry_dt = datetime.fromtimestamp(expiry)
    else:
        expiry_dt = datetime.fromisoformat(expiry)
    
    return datetime.now() >= expiry_dt - timedelta(minutes=5)


def refresh_oauth2_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> dict[str, Any] | None:
    """Refresh OAuth2 access token using refresh token.
    
    Args:
        client_id: Google OAuth2 client ID
        client_secret: Google OAuth2 client secret
        refresh_token: OAuth2 refresh token
        
    Returns:
        New token data dict or None on failure
    """
    import urllib.request
    import urllib.parse
    
    token_url = "https://oauth2.googleapis.com/token"
    
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    
    try:
        req = urllib.request.Request(token_url, data=data)
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
            expires_in = result.get("expires_in", 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return {
                "access_token": result.get("access_token"),
                "refresh_token": refresh_token,
                "token_expiry": expires_at.isoformat(),
                "token_type": result.get("token_type", "Bearer"),
            }
    except Exception:
        return None


def get_valid_access_token(
    token_path: Path | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> tuple[str | None, str | None]:
    """Get valid OAuth2 access token, refreshing if needed.
    
    Args:
        token_path: Path to token file
        client_id: OAuth2 client ID (for refresh)
        client_secret: OAuth2 client secret (for refresh)
        
    Returns:
        (access_token, email) or (None, None) if not available
    """
    token_data = None
    
    if token_path:
        token_data = load_oauth2_token_file(token_path)
    
    if not token_data:
        token_data = create_oauth2_config_from_env()
    
    if not token_data.get("access_token"):
        return None, None
    
    email = token_data.get("email")
    access_token = token_data.get("access_token")
    
    if is_token_expired(token_data):
        refresh_token = token_data.get("refresh_token")
        client_id = client_id or token_data.get("client_id") or os.getenv("ASYNCDEV_GMAIL_CLIENT_ID")
        client_secret = client_secret or token_data.get("client_secret") or os.getenv("ASYNCDEV_GMAIL_CLIENT_SECRET")
        
        if refresh_token and client_id and client_secret:
            new_token = refresh_oauth2_token(client_id, client_secret, refresh_token)
            if new_token:
                new_token["email"] = email
                access_token = new_token.get("access_token")
                
                if token_path:
                    save_oauth2_token_file(token_path, new_token)
    
    return access_token, email


def is_gmail_oauth2_configured(
    token_path: Path | None = None,
) -> bool:
    """Check if Gmail OAuth2 is properly configured.
    
    Args:
        token_path: Path to token file
        
    Returns:
        True if OAuth2 config available
    """
    access_token, email = get_valid_access_token(token_path)
    return bool(access_token and email)


def format_oauth2_setup_instructions() -> str:
    """Format setup instructions for Gmail OAuth2.
    
    Returns:
        Human-readable setup instructions
    """
    return """
## Gmail OAuth2 Setup Instructions

### Step 1: Create Google OAuth2 Credentials

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Gmail API for the project
4. Go to Credentials → Create Credentials → OAuth client ID
5. Choose "Desktop application"
6. Copy Client ID and Client Secret

### Step 2: Generate OAuth2 Token

Run the token generator script:
```bash
python -m runtime.gmail_oauth2_token_generator
```

Or manually:
1. Construct authorization URL with your client_id
2. Open URL in browser, authorize
3. Extract authorization code from redirect
4. Exchange code for tokens

### Step 3: Configure Environment Variables

```bash
ASYNCDEV_GMAIL_EMAIL=your-email@gmail.com
ASYNCDEV_GMAIL_ACCESS_TOKEN=<from step 2>
ASYNCDEV_GMAIL_REFRESH_TOKEN=<from step 2>
ASYNCDEV_GMAIL_CLIENT_ID=<from step 1>
ASYNCDEV_GMAIL_CLIENT_SECRET=<from step 1>
```

### Step 4: Or Save to Token File

Create `.runtime/gmail-oauth2-token.json`:
```json
{
  "email": "your-email@gmail.com",
  "access_token": "...",
  "refresh_token": "...",
  "token_expiry": "2026-04-17T12:00:00",
  "client_id": "...",
  "client_secret": "..."
}
```

### Alternative: Use Existing Token

If you have tokens from another application (e.g. oauth2l):
```bash
oauth2l fetch --scope=https://mail.google.com/ --client_id=YOUR_ID --client_secret=YOUR_SECRET
```

Copy the access_token to ASYNCDEV_GMAIL_ACCESS_TOKEN.
"""


class GmailOAuth2Config:
    """Gmail OAuth2 configuration manager."""
    
    DEFAULT_TOKEN_PATH = Path(".runtime/gmail-oauth2-token.json")
    
    def __init__(
        self,
        token_path: Path | None = None,
        use_env: bool = True,
    ) -> None:
        self.token_path = token_path or self.DEFAULT_TOKEN_PATH
        self.use_env = use_env
        self._token_data: dict[str, Any] | None = None
    
    def load(self) -> dict[str, Any]:
        """Load OAuth2 config from file and/or environment."""
        if self._token_data:
            return self._token_data
        
        token_data = {}
        
        if self.token_path.exists():
            token_data = load_oauth2_token_file(self.token_path) or {}
        
        if self.use_env:
            env_config = create_oauth2_config_from_env()
            for key, value in env_config.items():
                if value and not token_data.get(key):
                    token_data[key] = value
        
        self._token_data = token_data
        return token_data
    
    def get_access_token(self) -> str | None:
        """Get valid access token."""
        token_data = self.load()
        
        if is_token_expired(token_data):
            self.refresh()
            token_data = self.load()
        
        return token_data.get("access_token")
    
    def get_email(self) -> str | None:
        """Get email address."""
        token_data = self.load()
        return token_data.get("email")
    
    def refresh(self) -> bool:
        """Refresh access token."""
        token_data = self.load()
        
        refresh_token = token_data.get("refresh_token")
        client_id = token_data.get("client_id")
        client_secret = token_data.get("client_secret")
        
        if not (refresh_token and client_id and client_secret):
            return False
        
        new_token = refresh_oauth2_token(client_id, client_secret, refresh_token)
        if not new_token:
            return False
        
        new_token["email"] = token_data.get("email")
        new_token["client_id"] = client_id
        new_token["client_secret"] = client_secret
        
        self._token_data = new_token
        save_oauth2_token_file(self.token_path, new_token)
        
        return True
    
    def is_configured(self) -> bool:
        """Check if OAuth2 is configured."""
        access_token = self.get_access_token()
        email = self.get_email()
        return bool(access_token and email)
    
    def save(self, token_data: dict[str, Any]) -> None:
        """Save token data."""
        self._token_data = token_data
        save_oauth2_token_file(self.token_path, token_data)
    
    def get_auth_string(self) -> str | None:
        """Get XOAUTH2 auth string for SMTP."""
        access_token = self.get_access_token()
        email = self.get_email()
        
        if not (access_token and email):
            return None
        
        return build_xoauth2_auth_string(email, access_token)