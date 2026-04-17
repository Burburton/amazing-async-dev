"""Tests for gmail_oauth2 module."""

import base64
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from runtime.gmail_oauth2 import (
    build_xoauth2_auth_string,
    create_oauth2_config_from_env,
    load_oauth2_token_file,
    save_oauth2_token_file,
    is_token_expired,
    refresh_oauth2_token,
    get_valid_access_token,
    is_gmail_oauth2_configured,
    format_oauth2_setup_instructions,
    GmailOAuth2Config,
    GMAIL_SMTP_HOST,
    GMAIL_SMTP_PORT,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def valid_token_data():
    return {
        "email": "test@gmail.com",
        "access_token": "ya29.test_token",
        "refresh_token": "1/test_refresh",
        "token_expiry": (datetime.now() + timedelta(hours=1)).isoformat(),
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
    }


@pytest.fixture
def expired_token_data():
    return {
        "email": "test@gmail.com",
        "access_token": "ya29.expired_token",
        "refresh_token": "1/test_refresh",
        "token_expiry": (datetime.now() - timedelta(hours=1)).isoformat(),
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
    }


class TestBuildXoauth2AuthString:
    def test_auth_string_format(self):
        auth_string = build_xoauth2_auth_string("test@gmail.com", "ya29.token")
        
        decoded = base64.b64decode(auth_string).decode("utf-8")
        assert "user=test@gmail.com" in decoded
        assert "auth=Bearer ya29.token" in decoded

    def test_auth_string_structure(self):
        auth_string = build_xoauth2_auth_string("user@example.com", "access_token")
        decoded = base64.b64decode(auth_string).decode("utf-8")
        
        assert decoded.startswith("user=")
        assert "\x01auth=Bearer " in decoded
        assert decoded.endswith("\x01\x01")

    def test_auth_string_is_base64(self):
        auth_string = build_xoauth2_auth_string("test@gmail.com", "token")
        
        assert isinstance(auth_string, str)
        assert auth_string.isascii()


class TestCreateOauth2ConfigFromEnv:
    def test_loads_from_env(self):
        os.environ["ASYNCDEV_GMAIL_EMAIL"] = "env@gmail.com"
        os.environ["ASYNCDEV_GMAIL_ACCESS_TOKEN"] = "env_token"
        
        config = create_oauth2_config_from_env()
        
        assert config["email"] == "env@gmail.com"
        assert config["access_token"] == "env_token"
        
        del os.environ["ASYNCDEV_GMAIL_EMAIL"]
        del os.environ["ASYNCDEV_GMAIL_ACCESS_TOKEN"]

    def test_empty_env_returns_empty_config(self):
        os.environ.pop("ASYNCDEV_GMAIL_EMAIL", None)
        os.environ.pop("ASYNCDEV_GMAIL_ACCESS_TOKEN", None)
        
        config = create_oauth2_config_from_env()
        
        assert config["email"] == ""
        assert config["access_token"] == ""


class TestLoadSaveOauth2TokenFile:
    def test_save_and_load(self, temp_dir, valid_token_data):
        token_path = temp_dir / "token.json"
        
        save_oauth2_token_file(token_path, valid_token_data)
        loaded = load_oauth2_token_file(token_path)
        
        assert loaded["email"] == valid_token_data["email"]
        assert loaded["access_token"] == valid_token_data["access_token"]

    def test_load_nonexistent_file(self, temp_dir):
        token_path = temp_dir / "nonexistent.json"
        
        loaded = load_oauth2_token_file(token_path)
        
        assert loaded is None

    def test_save_creates_parent_dirs(self, temp_dir, valid_token_data):
        token_path = temp_dir / "subdir" / "token.json"
        
        save_oauth2_token_file(token_path, valid_token_data)
        
        assert token_path.exists()


class TestIsTokenExpired:
    def test_valid_token_not_expired(self, valid_token_data):
        assert is_token_expired(valid_token_data) == False

    def test_expired_token_is_expired(self, expired_token_data):
        assert is_token_expired(expired_token_data) == True

    def test_no_expiry_is_expired(self):
        token_data = {"access_token": "token"}
        
        assert is_token_expired(token_data) == True

    def test_almost_expired_returns_true(self):
        expiry = datetime.now() + timedelta(minutes=4)
        token_data = {"token_expiry": expiry.isoformat()}
        
        assert is_token_expired(token_data) == True


class TestGetValidAccessToken:
    def test_returns_valid_token(self, temp_dir, valid_token_data):
        token_path = temp_dir / "token.json"
        save_oauth2_token_file(token_path, valid_token_data)
        
        access_token, email = get_valid_access_token(token_path)
        
        assert access_token == valid_token_data["access_token"]
        assert email == valid_token_data["email"]

    def test_returns_none_for_expired_without_refresh(self, temp_dir):
        expired = {
            "email": "test@gmail.com",
            "access_token": "expired",
            "token_expiry": (datetime.now() - timedelta(hours=1)).isoformat(),
        }
        token_path = temp_dir / "token.json"
        save_oauth2_token_file(token_path, expired)
        
        access_token, email = get_valid_access_token(token_path)
        
        assert access_token == "expired"

    def test_returns_none_for_no_token(self, temp_dir):
        token_path = temp_dir / "empty.json"
        save_oauth2_token_file(token_path, {})
        
        access_token, email = get_valid_access_token(token_path)
        
        assert access_token is None


class TestIsGmailOauth2Configured:
    def test_configured_with_valid_token(self, temp_dir, valid_token_data):
        token_path = temp_dir / "token.json"
        save_oauth2_token_file(token_path, valid_token_data)
        
        assert is_gmail_oauth2_configured(token_path) == True

    def test_not_configured_without_token(self, temp_dir):
        token_path = temp_dir / "nonexistent.json"
        
        assert is_gmail_oauth2_configured(token_path) == False


class TestFormatOauth2SetupInstructions:
    def test_instructions_exist(self):
        instructions = format_oauth2_setup_instructions()
        
        assert "Google Cloud Console" in instructions
        assert "ASYNCDEV_GMAIL_EMAIL" in instructions
        assert "oauth2-token.json" in instructions

    def test_instructions_contain_steps(self):
        instructions = format_oauth2_setup_instructions()
        
        assert "Step 1" in instructions
        assert "Step 2" in instructions
        assert "Step 3" in instructions


class TestGmailOauth2Config:
    def test_load_from_file(self, temp_dir, valid_token_data):
        token_path = temp_dir / "token.json"
        save_oauth2_token_file(token_path, valid_token_data)
        
        config = GmailOAuth2Config(token_path)
        loaded = config.load()
        
        assert loaded["email"] == valid_token_data["email"]

    def test_is_configured(self, temp_dir, valid_token_data):
        token_path = temp_dir / "token.json"
        save_oauth2_token_file(token_path, valid_token_data)
        
        config = GmailOAuth2Config(token_path)
        
        assert config.is_configured() == True

    def test_not_configured_without_file(self, temp_dir):
        token_path = temp_dir / "nonexistent.json"
        
        config = GmailOAuth2Config(token_path)
        
        assert config.is_configured() == False

    def test_get_auth_string(self, temp_dir, valid_token_data):
        token_path = temp_dir / "token.json"
        save_oauth2_token_file(token_path, valid_token_data)
        
        config = GmailOAuth2Config(token_path)
        auth_string = config.get_auth_string()
        
        assert auth_string is not None
        decoded = base64.b64decode(auth_string).decode("utf-8")
        assert valid_token_data["email"] in decoded

    def test_get_email(self, temp_dir, valid_token_data):
        token_path = temp_dir / "token.json"
        save_oauth2_token_file(token_path, valid_token_data)
        
        config = GmailOAuth2Config(token_path)
        email = config.get_email()
        
        assert email == valid_token_data["email"]

    def test_get_access_token(self, temp_dir, valid_token_data):
        token_path = temp_dir / "token.json"
        save_oauth2_token_file(token_path, valid_token_data)
        
        config = GmailOAuth2Config(token_path)
        token = config.get_access_token()
        
        assert token == valid_token_data["access_token"]

    def test_save(self, temp_dir):
        token_path = temp_dir / "new_token.json"
        config = GmailOAuth2Config(token_path)
        
        config.save({
            "email": "saved@gmail.com",
            "access_token": "saved_token",
        })
        
        assert token_path.exists()
        loaded = load_oauth2_token_file(token_path)
        assert loaded["email"] == "saved@gmail.com"


class TestGmailConstants:
    def test_smtp_host(self):
        assert GMAIL_SMTP_HOST == "smtp.gmail.com"

    def test_smtp_port(self):
        assert GMAIL_SMTP_PORT == 587


class TestEmailConfigOAuth2Integration:
    def test_email_config_oauth2_fields(self):
        from runtime.email_sender import EmailConfig
        
        config = EmailConfig()
        
        assert hasattr(config, "use_oauth2")
        assert hasattr(config, "oauth2_token_path")
        assert hasattr(config, "is_oauth2_configured")
        assert hasattr(config, "can_send_email")

    def test_email_config_oauth2_disabled_by_default(self):
        from runtime.email_sender import EmailConfig
        
        config = EmailConfig()
        
        assert config.use_oauth2 == False

    def test_email_config_can_enable_oauth2(self, temp_dir, valid_token_data):
        from runtime.email_sender import EmailConfig
        
        token_path = temp_dir / "token.json"
        save_oauth2_token_file(token_path, valid_token_data)
        
        os.environ["ASYNCDEV_USE_OAUTH2"] = "true"
        os.environ["ASYNCDEV_OAUTH2_TOKEN_PATH"] = str(token_path)
        
        config = EmailConfig()
        
        assert config.use_oauth2 == True
        
        del os.environ["ASYNCDEV_USE_OAUTH2"]
        del os.environ["ASYNCDEV_OAUTH2_TOKEN_PATH"]