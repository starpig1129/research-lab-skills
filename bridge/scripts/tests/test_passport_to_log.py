"""Tests for passport_to_log.py — Material Passport → research-log bridge."""
import textwrap
from datetime import date
import pytest
import yaml

# Import will fail until passport_to_log.py is created — that's expected (TDD).
from bridge.scripts.passport_to_log import (
    parse_passport,
    extract_latest_stage,
    draft_log_entry,
    PassportParseError,
)

MINIMAL_PASSPORT = textwrap.dedent("""\
    material_passport:
      version: "9"
      paper_slug: test_paper
      stages:
        - stage: 1
          name: RESEARCH
          status: PASS
          completed_at: "2026-06-10"
          deliverables:
            - Research Question Brief
            - Methodology Blueprint
""")

MULTI_STAGE_PASSPORT = textwrap.dedent("""\
    material_passport:
      version: "9"
      paper_slug: my_hei_paper
      stages:
        - stage: 1
          name: RESEARCH
          status: PASS
          completed_at: "2026-06-08"
          deliverables:
            - Research Question Brief
        - stage: 2
          name: WRITE
          status: PASS
          completed_at: "2026-06-10"
          deliverables:
            - Full Draft
            - Bilingual Abstract
        - stage: 2.5
          name: INTEGRITY CHECK
          status: PENDING
          completed_at: null
          deliverables: []
""")

IN_PROGRESS_PASSPORT = textwrap.dedent("""\
    material_passport:
      version: "9"
      paper_slug: in_progress
      stages:
        - stage: 1
          name: RESEARCH
          status: IN_PROGRESS
          completed_at: null
          deliverables: []
""")


class TestParsePassport:
    def test_parses_valid_yaml(self):
        result = parse_passport(MINIMAL_PASSPORT)
        assert result["version"] == "9"
        assert result["paper_slug"] == "test_paper"
        assert len(result["stages"]) == 1

    def test_raises_on_missing_material_passport_key(self):
        with pytest.raises(PassportParseError, match="material_passport"):
            parse_passport("stages: []")

    def test_raises_on_invalid_yaml(self):
        with pytest.raises(PassportParseError):
            parse_passport("{bad: yaml: :")

    def test_raises_on_missing_stages(self):
        with pytest.raises(PassportParseError, match="stages"):
            parse_passport("material_passport:\n  version: '9'\n")


class TestExtractLatestStage:
    def test_returns_latest_completed_stage(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        assert stage["stage"] == 2
        assert stage["name"] == "WRITE"
        assert stage["status"] == "PASS"

    def test_returns_in_progress_stage_if_no_completed(self):
        passport = parse_passport(IN_PROGRESS_PASSPORT)
        stage = extract_latest_stage(passport)
        assert stage["stage"] == 1
        assert stage["status"] == "IN_PROGRESS"

    def test_prefers_latest_by_stage_number(self):
        passport = parse_passport(MINIMAL_PASSPORT)
        stage = extract_latest_stage(passport)
        assert stage["stage"] == 1

    def test_returns_pending_if_no_pass_or_in_progress(self):
        passport_yaml = textwrap.dedent("""\
            material_passport:
              version: "9"
              paper_slug: p
              stages:
                - stage: 2.5
                  name: INTEGRITY CHECK
                  status: PENDING
                  completed_at: null
                  deliverables: []
        """)
        passport = parse_passport(passport_yaml)
        stage = extract_latest_stage(passport)
        assert stage["name"] == "INTEGRITY CHECK"


class TestDraftLogEntry:
    def test_draft_contains_required_frontmatter_fields(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "date: 2026-06-10" in draft
        assert "mode: publish" in draft
        assert "experiment: publish-my_hei_paper-stage2" in draft

    def test_draft_contains_stage_name_in_goal(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "WRITE" in draft
        assert "Stage 2" in draft

    def test_draft_lists_deliverables(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "Full Draft" in draft
        assert "Bilingual Abstract" in draft

    def test_draft_shows_pass_status(self):
        passport = parse_passport(MULTI_STAGE_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "PASS" in draft

    def test_draft_has_next_steps_placeholder(self):
        passport = parse_passport(MINIMAL_PASSPORT)
        stage = extract_latest_stage(passport)
        draft = draft_log_entry(passport, stage, today=date(2026, 6, 10))

        assert "Next Steps" in draft
        assert "{{NEXT_STEPS}}" in draft
