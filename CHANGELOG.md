# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-30

### Added

#### Core System (Features 001-007)
- ProductBrief and FeatureSpec schemas with YAML templates
- Day loop CLI: `plan-day`, `run-day`, `review-night`, `resume-next-day`
- Execution modes: External tool, Live API, Mock
- SQLite-based state persistence with file fallback
- Archive system for completed features
- Issue capture, triage, and promotion workflow

#### State & Recovery (Features 008-012)
- SQLite state store with execution logging
- Recovery data adapter with latest pointer management
- Workspace snapshot system
- Artifact router for cross-repository state

#### Archive & History (Features 013-018)
- Feature completion flow (`complete-feature mark`)
- Feature archive with query and summary
- Continuation evaluator for day loop transitions
- Project memory artifacts

#### Feedback & Policy (Features 019-021)
- Issue capture with triage system
- Feedback promotion from issues
- Auto-continue policy with safety evaluation
- Decision channel with email-first async decisions

#### Integration (Feature 022)
- Advisor starter pack consumption
- Starter pack schema validation
- ProductContext import from external advisors

#### Operator Surfaces (Features 023-036+)
- Recovery Console for execution recovery
- Decision Inbox for decision management
- Session Start with mandatory blocking check
- Execution Observer with severity tracking
- Verification Console for verification state
- Acceptance Console for acceptance validation
- Evidence Summary for rolled-up project/feature view

#### Platform Phase 4 (Feature 081)
- Unified platform shell with drill-down navigation
- Cross-surface links for navigating between operator surfaces
- Blocking state dashboard
- Unified recovery dashboard
- Operator home with status, attention, and recovery views

#### Email System (Feature 080+)
- Decision request emails with execution context
- Day-end summary emails with project progress
- Option analysis (effort/risk/time estimates)
- Recommendation confidence and reasoning
- Enhanced plain text formatting

### Changed

- CLI commands now support `--project` parameter for all day loop operations
- Improved execution intent alignment in run-day
- Resume-next-day with better planning mode inference
- Review-night with enriched operator pack and doctor integration

### Fixed

- Planning mode inference for continue_work scenarios
- Execution observer severity classification
- Acceptance recovery flow integration

### Documentation

- Quick start guide (3-minute first run)
- Verification guide for initialization
- Operating model documentation
- Architecture overview
- Terminology guide
- Examples directory with single-feature day loop
- **CLI reference** - Complete command reference (695 lines)
- **User quick-start (Chinese)** - Simplified Chinese quick-start guide
- **Troubleshooting guide** - Common errors and solutions
- **API reference** - Developer API documentation

## [0.0.1] - 2026-04-11

### Added

- Initial project structure
- Basic CLI scaffold
- README with project overview
