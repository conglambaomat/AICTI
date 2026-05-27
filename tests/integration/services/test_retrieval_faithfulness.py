"""Integration tests for retrieval faithfulness validation.

Tests citation mismatch detection and unsupported claim rejection as hard gates.
"""

from de_forge.services.static_validation import validate_retrieval_faithfulness


class TestCitationMismatch:
    """Test citation mismatch detection (quote must match chunk text offsets)."""

    def test_valid_citation_passes(self):
        """Valid citation with matching quote and offsets should pass."""
        evidence = {
            "chunk_id": "chunk-001",
            "quote": "The actor used encoded PowerShell commands",
            "char_start": 104,
            "char_end": 146,
            "supports": "encoded PowerShell execution",
        }
        chunks = {
            "chunk-001": {
                "text": "In the attack campaign, The actor used encoded PowerShell commands to download payloads from remote servers.",
                "start_offset": 80,
            }
        }

        result = validate_retrieval_faithfulness([evidence], chunks)

        assert result["valid"] is True
        assert result["errors"] == []

    def test_quote_not_in_chunk_fails(self):
        """Citation with quote not found in chunk text should fail."""
        evidence = {
            "chunk_id": "chunk-001",
            "quote": "The actor used encoded Bash commands",
            "char_start": 100,
            "char_end": 137,
            "supports": "encoded Bash execution",
        }
        chunks = {
            "chunk-001": {
                "text": "The actor used encoded PowerShell commands to download payloads.",
                "start_offset": 100,
            }
        }

        result = validate_retrieval_faithfulness([evidence], chunks)

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "citation mismatch" in result["errors"][0].lower()
        assert "chunk-001" in result["errors"][0]

    def test_offset_mismatch_fails(self):
        """Citation with incorrect offsets should fail."""
        evidence = {
            "chunk_id": "chunk-001",
            "quote": "encoded PowerShell commands",
            "char_start": 50,  # Wrong offset
            "char_end": 77,
            "supports": "encoded PowerShell execution",
        }
        chunks = {
            "chunk-001": {
                "text": "The actor used encoded PowerShell commands to download payloads.",
                "start_offset": 100,
            }
        }

        result = validate_retrieval_faithfulness([evidence], chunks)

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "offset mismatch" in result["errors"][0].lower()

    def test_missing_chunk_id_fails(self):
        """Citation referencing non-existent chunk should fail."""
        evidence = {
            "chunk_id": "chunk-999",
            "quote": "some text",
            "char_start": 0,
            "char_end": 9,
            "supports": "something",
        }
        chunks = {
            "chunk-001": {
                "text": "The actor used encoded PowerShell commands.",
                "start_offset": 100,
            }
        }

        result = validate_retrieval_faithfulness([evidence], chunks)

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "chunk-999" in result["errors"][0]
        assert "not found" in result["errors"][0].lower()


class TestUnsupportedClaimRejection:
    """Test unsupported claim rejection (claims without evidence citations)."""

    def test_all_claims_supported_passes(self):
        """DetectionSpec with all claims backed by evidence should pass."""
        evidence = [
            {
                "chunk_id": "chunk-001",
                "quote": "The actor used encoded PowerShell commands",
                "char_start": 104,
                "char_end": 146,
                "supports": "encoded PowerShell execution",
            }
        ]
        chunks = {
            "chunk-001": {
                "text": "In the attack campaign, The actor used encoded PowerShell commands to download payloads.",
                "start_offset": 80,
            }
        }
        claims = ["encoded PowerShell execution"]

        result = validate_retrieval_faithfulness(evidence, chunks, required_claims=claims)

        assert result["valid"] is True
        assert result["errors"] == []

    def test_unsupported_claim_fails(self):
        """DetectionSpec with claim not backed by evidence should fail."""
        evidence = [
            {
                "chunk_id": "chunk-001",
                "quote": "The actor used encoded PowerShell commands",
                "char_start": 104,
                "char_end": 146,
                "supports": "encoded PowerShell execution",
            }
        ]
        chunks = {
            "chunk-001": {
                "text": "In the attack campaign, The actor used encoded PowerShell commands to download payloads.",
                "start_offset": 80,
            }
        }
        claims = ["encoded PowerShell execution", "lateral movement via SMB"]

        result = validate_retrieval_faithfulness(evidence, chunks, required_claims=claims)

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "unsupported claim" in result["errors"][0].lower()
        assert "lateral movement via SMB" in result["errors"][0]

    def test_empty_evidence_with_claims_fails(self):
        """DetectionSpec with claims but no evidence should fail."""
        evidence: list[dict[str, object]] = []
        chunks: dict[str, dict[str, object]] = {}
        claims = ["some behavior"]

        result = validate_retrieval_faithfulness(evidence, chunks, required_claims=claims)

        assert result["valid"] is False
        assert len(result["errors"]) >= 1
        assert "unsupported claim" in result["errors"][0].lower()


class TestMultipleErrors:
    """Test handling of multiple validation errors."""

    def test_multiple_citation_errors_reported(self):
        """Multiple citation mismatches should all be reported."""
        evidence = [
            {
                "chunk_id": "chunk-001",
                "quote": "wrong quote 1",
                "char_start": 0,
                "char_end": 13,
                "supports": "behavior 1",
            },
            {
                "chunk_id": "chunk-002",
                "quote": "wrong quote 2",
                "char_start": 0,
                "char_end": 13,
                "supports": "behavior 2",
            },
        ]
        chunks = {
            "chunk-001": {"text": "correct text 1", "start_offset": 0},
            "chunk-002": {"text": "correct text 2", "start_offset": 0},
        }

        result = validate_retrieval_faithfulness(evidence, chunks)

        assert result["valid"] is False
        assert len(result["errors"]) == 2
