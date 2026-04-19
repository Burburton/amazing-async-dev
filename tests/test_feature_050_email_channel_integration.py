"""Tests for Feature 050 - Email Channel Integration in new-product."""

import pytest
from pathlib import Path
import yaml


class TestNewProductWithEmailChannel:
    def test_project_link_with_email_channel(self, tmp_path):
        product_dir = tmp_path / "test-product"
        product_dir.mkdir()
        
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "self_hosted",
            "email_channel": {
                "enabled": True,
                "sender": "noreply@example.com",
                "decision_inbox": "decisions@example.com",
            },
            "status": "active",
        }
        
        link_path = product_dir / "project-link.yaml"
        with open(link_path, "w") as f:
            yaml.dump(project_link, f)
        
        with open(link_path) as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["email_channel"]["enabled"] is True
        assert loaded["email_channel"]["sender"] == "noreply@example.com"
    
    def test_project_link_without_email_channel(self, tmp_path):
        product_dir = tmp_path / "test-product"
        product_dir.mkdir()
        
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "self_hosted",
            "status": "active",
        }
        
        link_path = product_dir / "project-link.yaml"
        with open(link_path, "w") as f:
            yaml.dump(project_link, f)
        
        with open(link_path) as f:
            loaded = yaml.safe_load(f)
        
        assert "email_channel" not in loaded
    
    def test_managed_external_with_email(self, tmp_path):
        product_dir = tmp_path / "test-product"
        product_dir.mkdir()
        
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "managed_external",
            "repo_url": "https://github.com/user/test-product",
            "email_channel": {
                "enabled": True,
                "sender": "noreply@product.com",
                "decision_inbox": "decisions@product.com",
            },
            "status": "active",
        }
        
        link_path = product_dir / "project-link.yaml"
        with open(link_path, "w") as f:
            yaml.dump(project_link, f)
        
        with open(link_path) as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["ownership_mode"] == "managed_external"
        assert loaded["email_channel"]["enabled"] is True


class TestProjectLinkLoaderWithEmail:
    def test_load_email_channel_config(self, tmp_path):
        from runtime.project_link_loader import load_project_link
        
        product_dir = tmp_path / "test-product"
        product_dir.mkdir()
        
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "self_hosted",
            "email_channel": {
                "enabled": True,
                "sender": "noreply@test.com",
                "decision_inbox": "inbox@test.com",
            },
            "status": "active",
        }
        
        link_path = product_dir / "project-link.yaml"
        with open(link_path, "w") as f:
            yaml.dump(project_link, f)
        
        context = load_project_link(product_dir)
        
        assert context is not None
        assert context.email_channel_enabled is True
        assert context.email_sender == "noreply@test.com"
        assert context.email_decision_inbox == "inbox@test.com"
    
    def test_email_disabled_by_default(self, tmp_path):
        from runtime.project_link_loader import load_project_link
        
        product_dir = tmp_path / "test-product"
        product_dir.mkdir()
        
        project_link = {
            "product_id": "test-product",
            "ownership_mode": "self_hosted",
            "status": "active",
        }
        
        link_path = product_dir / "project-link.yaml"
        with open(link_path, "w") as f:
            yaml.dump(project_link, f)
        
        context = load_project_link(product_dir)
        
        assert context is not None
        assert context.email_channel_enabled is False
        assert context.email_sender == ""
    
    def test_no_project_link_returns_none(self, tmp_path):
        from runtime.project_link_loader import load_project_link
        
        product_dir = tmp_path / "test-product"
        product_dir.mkdir()
        
        context = load_project_link(product_dir)
        
        assert context is None


class TestEmailChannelIntegration:
    def test_email_channel_summary_includes_email(self, tmp_path):
        from runtime.project_link_loader import get_project_link_summary
        
        product_dir = tmp_path / "test-product"
        product_dir.mkdir()
        
        project_link = {
            "product_id": "test-product",
            "email_channel": {"enabled": True, "sender": "test@test.com"},
            "status": "active",
        }
        
        link_path = product_dir / "project-link.yaml"
        with open(link_path, "w") as f:
            yaml.dump(project_link, f)
        
        summary = get_project_link_summary(product_dir)
        
        assert summary["email_enabled"] is True