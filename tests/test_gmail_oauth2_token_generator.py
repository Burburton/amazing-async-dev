"""Tests for gmail_oauth2_token_generator module."""

import tempfile
from pathlib import Path

import pytest

from runtime.gmail_oauth2_token_generator import (
    generate_authorization_url,
    exchange_code_for_tokens,
    create_token_file,
    validate_oauth2_credentials,
    format_setup_guide,
    GOOGLE_AUTH_URL,
    GMAIL_SMTP_SCOPE,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestGenerateAuthorizationUrl:
    def test_url_contains_google_auth(self):
        url = generate_authorization_url("test_client_id")
        
        assert url.startswith(GOOGLE_AUTH_URL)

    def test_url_contains_client_id(self):
        url = generate_authorization_url("my_client_id")
        
        assert "client_id=my_client_id" in url

    def test_url_contains_scope(self):
        import urllib.parse
        
        url = generate_authorization_url("test")
        
        decoded = urllib.parse.unquote(url)
        assert GMAIL_SMTP_SCOPE in decoded

    def test_url_contains_access_type_offline(self):
        url = generate_authorization_url("test")
        
        assert "access_type=offline" in url

    def test_url_contains_prompt_consent(self):
        url = generate_authorization_url("test")
        
        assert "prompt=consent" in url

    def test_url_contains_response_type_code(self):
        url = generate_authorization_url("test")
        
        assert "response_type=code" in url

    def test_url_with_state(self):
        url = generate_authorization_url("test", state="random_state")
        
        assert "state=random_state" in url


class TestExchangeCodeForTokens:
    def test_returns_error_on_invalid_code(self):
        result = exchange_code_for_tokens("client", "secret", "invalid_code")
        
        assert result is not None
        assert result.get("error") is not None

    def test_returns_dict(self):
        result = exchange_code_for_tokens("client", "secret", "code")
        
        assert isinstance(result, dict)


class TestCreateTokenFile:
    def test_creates_file(self, temp_dir):
        token_data = {
            "access_token": "ya29.test",
            "refresh_token": "1/refresh",
            "token_expiry": "2026-04-17T12:00:00",
        }
        
        path = create_token_file(
            token_data,
            "test@gmail.com",
            "client_id",
            "client_secret",
            temp_dir / "token.json",
        )
        
        assert path.exists()

    def test_file_contains_email(self, temp_dir):
        import json
        
        token_data = {"access_token": "test"}
        path = create_token_file(
            token_data,
            "user@gmail.com",
            "client",
            "secret",
            temp_dir / "token.json",
        )
        
        with open(path) as f:
            data = json.load(f)
        
        assert data["email"] == "user@gmail.com"

    def test_file_contains_client_credentials(self, temp_dir):
        import json
        
        token_data = {"access_token": "test"}
        path = create_token_file(
            token_data,
            "user@gmail.com",
            "my_client_id",
            "my_secret",
            temp_dir / "token.json",
        )
        
        with open(path) as f:
            data = json.load(f)
        
        assert data["client_id"] == "my_client_id"
        assert data["client_secret"] == "my_secret"

    def test_creates_parent_dirs(self, temp_dir):
        token_data = {"access_token": "test"}
        path = temp_dir / "subdir" / "nested" / "token.json"
        
        create_token_file(token_data, "user@gmail.com", "client", "secret", path)
        
        assert path.exists()

    def test_default_path(self, temp_dir):
        token_data = {"access_token": "test"}
        
        path = create_token_file(
            token_data,
            "user@gmail.com",
            "client",
            "secret",
        )
        
        assert path.name == "gmail-oauth2-token.json"


class TestValidateOAuth2Credentials:
    def test_valid_credentials(self):
        is_valid, explanation = validate_oauth2_credentials(
            "12345.apps.googleusercontent.com",
            "GOCSPX-test_secret_key",
        )
        
        assert is_valid == True

    def test_empty_client_id(self):
        is_valid, explanation = validate_oauth2_credentials("", "secret")
        
        assert is_valid == False
        assert "empty" in explanation.lower()

    def test_empty_client_secret(self):
        is_valid, explanation = validate_oauth2_credentials("client", "")
        
        assert is_valid == False
        assert "empty" in explanation.lower()

    def test_invalid_client_id_format(self):
        is_valid, explanation = validate_oauth2_credentials("invalid_id", "secret")
        
        assert is_valid == False
        assert "googleusercontent.com" in explanation

    def test_short_client_secret(self):
        is_valid, explanation = validate_oauth2_credentials(
            "12345.apps.googleusercontent.com",
            "short",
        )
        
        assert is_valid == False
        assert "short" in explanation.lower()


class TestFormatSetupGuide:
    def test_guide_exists(self):
        guide = format_setup_guide()
        
        assert len(guide) > 100

    def test_guide_contains_steps(self):
        guide = format_setup_guide()
        
        assert "Step 1" in guide
        assert "Step 2" in guide
        assert "Step 3" in guide

    def test_guide_contains_google_cloud_console(self):
        guide = format_setup_guide()
        
        assert "console.cloud.google.com" in guide

    def test_guide_contains_env_variables(self):
        guide = format_setup_guide()
        
        assert "ASYNCDEV_GMAIL_CLIENT_ID" in guide
        assert "ASYNCDEV_GMAIL_CLIENT_SECRET" in guide

    def test_guide_contains_test_instructions(self):
        guide = format_setup_guide()
        
        assert "asyncdev email-decision" in guide


class TestConstants:
    def test_google_auth_url(self):
        assert GOOGLE_AUTH_URL == "https://accounts.google.com/o/oauth2/v2/auth"

    def test_gmail_scope(self):
        assert GMAIL_SMTP_SCOPE == "https://mail.google.com/"