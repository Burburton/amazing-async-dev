"""Tests for audit_trail_store module (Feature 047)."""

import tempfile
from pathlib import Path

import pytest

from runtime.audit_trail_store import (
    AuditTrailStore,
    reconstruct_audit_trail,
    detect_missing_links,
    format_audit_summary,
    CHAIN_TYPES,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestAuditTrailStore:
    def test_store_creates_audit_path(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        assert store.audit_path.exists()

    def test_generate_audit_id_format(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        audit_id = store.generate_audit_id()
        assert audit_id.startswith("audit-")
        # Format: audit-YYYYMMDD-NNN = 6 + 8 + 1 + 3 = 18 chars
        assert len(audit_id) >= 15

    def test_record_outbound_request(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        audit = store.record_outbound_request(
            request_id="dr-001",
            project_id="test-project",
            channel="mock_file",
            artifact_path=".runtime/email-outbox/dr-001.md",
        )
        
        assert audit["audit_id"].startswith("audit-")
        assert audit["chain_type"] == "decision_request_chain"
        assert audit["outbound_request_id"] == "dr-001"
        assert audit["outbound_channel"] == "mock_file"

    def test_record_outbound_report(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        audit = store.record_outbound_report(
            report_id="sr-001",
            project_id="test-project",
            channel="mock_file",
            artifact_path=".runtime/email-outbox/sr-001.md",
        )
        
        assert audit["chain_type"] == "status_report_chain"
        assert audit["outbound_report_id"] == "sr-001"

    def test_record_inbound_reply(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        store.record_outbound_request(
            request_id="dr-001",
            project_id="test",
            channel="mock_file",
        )
        
        audit = store.record_inbound_reply(
            request_id="dr-001",
            reply_raw="DECISION A",
            parsed_command="DECISION",
            parsed_argument="A",
            validation_status="valid",
        )
        
        assert audit is not None
        assert audit["inbound_reply_raw"] == "DECISION A"
        assert audit["inbound_parsed_command"] == "DECISION"
        assert audit["inbound_validation_status"] == "valid"

    def test_record_inbound_reply_no_request(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_inbound_reply(
            request_id="dr-nonexistent",
            reply_raw="DECISION A",
        )
        
        assert audit is None

    def test_record_decision_applied(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        store.record_outbound_request(
            request_id="dr-001",
            project_id="test",
            channel="mock_file",
        )
        
        store.record_inbound_reply(
            request_id="dr-001",
            reply_raw="DECISION A",
            parsed_command="DECISION",
            parsed_argument="A",
        )
        
        audit = store.record_decision_applied(
            request_id="dr-001",
            applied_action="select_option",
            runstate_before={"current_phase": "blocked", "decisions_needed": [{"decision": "test"}]},
            runstate_after={"current_phase": "planning", "decisions_needed": []},
            continuation_phase="planning",
        )
        
        assert audit is not None
        assert audit["decision_applied_action"] == "select_option"
        assert audit["decision_continuation_phase"] == "planning"
        assert audit["decision_runstate_before"]["phase"] == "blocked"
        assert audit["decision_runstate_after"]["phase"] == "planning"

    def test_find_audit_by_request_id(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        store.record_outbound_request(
            request_id="dr-001",
            project_id="test",
            channel="mock_file",
        )
        
        audit = store.find_audit_by_request_id("dr-001")
        
        assert audit is not None
        assert audit["outbound_request_id"] == "dr-001"

    def test_find_audit_by_report_id(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        store.record_outbound_report(
            report_id="sr-001",
            project_id="test",
            channel="mock_file",
        )
        
        audit = store.find_audit_by_report_id("sr-001")
        
        assert audit is not None
        assert audit["outbound_report_id"] == "sr-001"

    def test_list_audits(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        store.record_outbound_request("dr-001", "test", "mock")
        store.record_outbound_request("dr-002", "test", "mock")
        store.record_outbound_report("sr-001", "test", "mock")
        
        audits = store.list_audits()
        assert len(audits) == 3
        
        decision_audits = store.list_audits(chain_type="decision_request_chain")
        assert len(decision_audits) == 2
        
        report_audits = store.list_audits(chain_type="status_report_chain")
        assert len(report_audits) == 1


class TestReconstructAuditTrail:
    def test_reconstruct_decision_chain(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_request("dr-001", "test", "mock")
        store.record_inbound_reply("dr-001", "DECISION A", "DECISION", "A", "valid")
        store.record_decision_applied("dr-001", "select_option")
        
        loaded = store.load_audit(audit["audit_id"])
        trail = reconstruct_audit_trail(loaded)
        
        assert trail["chain_type"] == "decision_request_chain"
        assert len(trail["stages"]) == 3
        assert trail["stages"][0]["stage"] == "request_sent"
        assert trail["stages"][1]["stage"] == "reply_received"
        assert trail["stages"][2]["stage"] == "decision_applied"

    def test_reconstruct_report_chain(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_report("sr-001", "test", "mock")
        
        loaded = store.load_audit(audit["audit_id"])
        trail = reconstruct_audit_trail(loaded)
        
        assert trail["chain_type"] == "status_report_chain"
        assert len(trail["stages"]) == 1
        assert trail["stages"][0]["stage"] == "report_sent"

    def test_reconstruct_empty_audit(self):
        trail = reconstruct_audit_trail({})
        
        assert trail["stages"] == []
        assert trail["complete"] == False


class TestDetectMissingLinks:
    def test_no_missing_links_complete_chain(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_request("dr-001", "test", "mock")
        store.record_inbound_reply("dr-001", "DECISION A", "DECISION", "A", "valid")
        store.record_decision_applied("dr-001", "select_option")
        
        loaded = store.load_audit(audit["audit_id"])
        missing = detect_missing_links(loaded)
        
        assert missing["missing_links_detected"] == False

    def test_missing_reply_for_old_request(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_request("dr-001", "test", "mock")
        
        loaded = store.load_audit(audit["audit_id"])
        loaded["outbound_sent_at"] = "2026-04-01T10:00:00"
        
        missing = detect_missing_links(loaded)
        
        assert missing["missing_links_detected"] == True
        assert len(missing["missing_links_details"]) > 0

    def test_missing_decision_application(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_request("dr-001", "test", "mock")
        store.record_inbound_reply("dr-001", "DECISION A", "DECISION", "A", "valid")
        
        loaded = store.load_audit(audit["audit_id"])
        missing = detect_missing_links(loaded)
        
        assert missing["missing_links_detected"] == True
        assert any(d["stage"] == "decision_applied" for d in missing["missing_links_details"])


class TestFormatAuditSummary:
    def test_format_includes_chain_type(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_request("dr-001", "test-project", "mock")
        
        summary = format_audit_summary(audit)
        
        assert "decision_request_chain" in summary
        assert "dr-001" in summary
        assert "test-project" in summary

    def test_format_includes_stages(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_request("dr-001", "test", "mock")
        store.record_inbound_reply("dr-001", "DECISION A", "DECISION", "A")
        store.record_decision_applied("dr-001", "select")
        
        loaded = store.load_audit(audit["audit_id"])
        summary = format_audit_summary(loaded)
        
        assert "request_sent" in summary
        assert "reply_received" in summary
        assert "decision_applied" in summary

    def test_format_shows_missing_links(self):
        audit = {
            "audit_id": "audit-001",
            "chain_type": "decision_request_chain",
            "outbound_request_id": "dr-001",
            "outbound_sent_at": "2026-04-01T10:00:00",
        }
        
        missing = detect_missing_links(audit)
        audit.update(missing)
        
        summary = format_audit_summary(audit)
        
        assert "Missing Links" in summary


class TestChainTypes:
    def test_all_chain_types_defined(self):
        assert "decision_request_chain" in CHAIN_TYPES
        assert "status_report_chain" in CHAIN_TYPES


class TestEndToEndAuditLoop:
    def test_full_decision_loop_auditable(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_request(
            request_id="dr-20260416-001",
            project_id="amazing-async-dev",
            channel="mock_file",
            artifact_path=".runtime/email-outbox/dr-001.md",
        )
        
        audit = store.record_inbound_reply(
            request_id="dr-20260416-001",
            reply_raw="DECISION A",
            parsed_command="DECISION",
            parsed_argument="A",
            validation_status="valid",
        )
        
        audit = store.record_decision_applied(
            request_id="dr-20260416-001",
            applied_action="select_option",
            runstate_before={"current_phase": "blocked", "decisions_needed": [{"decision": "test"}]},
            runstate_after={"current_phase": "planning", "decisions_needed": []},
            continuation_phase="planning",
        )
        
        trail = reconstruct_audit_trail(audit)
        missing = detect_missing_links(audit)
        
        assert len(trail["stages"]) == 3
        assert missing["missing_links_detected"] == False
        
        summary = format_audit_summary(audit)
        assert "dr-20260416-001" in summary
        assert "DECISION A" in summary
        assert "select_option" in summary

    def test_report_chain_auditable(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_report(
            report_id="sr-20260416-001",
            project_id="amazing-async-dev",
            channel="mock_file",
            artifact_path=".runtime/email-outbox/sr-001.md",
        )
        
        trail = reconstruct_audit_trail(audit)
        
        assert len(trail["stages"]) == 1
        assert trail["stages"][0]["stage"] == "report_sent"

    def test_auditor_can_reconstruct_what_happened(self, temp_dir):
        store = AuditTrailStore(temp_dir)
        
        audit = store.record_outbound_request("dr-001", "test", "mock", ".runtime/outbox")
        store.record_inbound_reply("dr-001", "DECISION A", "DECISION", "A", "valid")
        store.record_decision_applied("dr-001", "proceed", {"current_phase": "blocked"}, {"current_phase": "executing"}, "executing")
        
        loaded = store.load_audit(audit["audit_id"])
        summary = format_audit_summary(loaded)
        
        assert "Request sent" in summary or "request_sent" in summary.lower()
        assert "Reply received" in summary or "reply_received" in summary.lower()
        assert "Decision applied" in summary or "decision_applied" in summary.lower()
        assert "proceed" in summary