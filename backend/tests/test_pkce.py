"""Unit tests for PKCE utilities (RFC 7636)."""

import pytest

from app.services.auth.pkce import (
    generate_code_challenge,
    generate_code_verifier,
    verify_code_challenge,
)


class TestGenerateCodeVerifier:
    def test_returns_a_string(self):
        assert isinstance(generate_code_verifier(), str)

    def test_length_is_128_characters(self):
        assert len(generate_code_verifier()) == 128

    def test_no_base64_padding_characters(self):
        assert "=" not in generate_code_verifier()

    def test_produces_unique_values_on_each_call(self):
        assert generate_code_verifier() != generate_code_verifier()


class TestGenerateCodeChallenge:
    def test_returns_43_character_string(self):
        challenge = generate_code_challenge(generate_code_verifier())
        assert isinstance(challenge, str)
        assert len(challenge) == 43

    def test_no_base64_padding_characters(self):
        assert "=" not in generate_code_challenge(generate_code_verifier())

    def test_challenge_differs_from_verifier(self):
        verifier = generate_code_verifier()
        assert generate_code_challenge(verifier) != verifier

    def test_is_deterministic_for_same_verifier(self):
        verifier = generate_code_verifier()
        assert generate_code_challenge(verifier) == generate_code_challenge(verifier)

    def test_different_verifiers_produce_different_challenges(self):
        c1 = generate_code_challenge(generate_code_verifier())
        c2 = generate_code_challenge(generate_code_verifier())
        assert c1 != c2


class TestVerifyCodeChallenge:
    def test_returns_true_for_matching_verifier_and_challenge(self):
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier)
        assert verify_code_challenge(verifier, challenge) is True

    def test_returns_false_for_wrong_verifier(self):
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier)
        wrong_verifier = generate_code_verifier()
        assert verify_code_challenge(wrong_verifier, challenge) is False

    def test_returns_false_for_tampered_challenge(self):
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier)
        tampered = challenge[:-5] + "XXXXX"
        assert verify_code_challenge(verifier, tampered) is False

    def test_returns_false_for_empty_verifier(self):
        challenge = generate_code_challenge(generate_code_verifier())
        assert verify_code_challenge("", challenge) is False

    def test_returns_false_for_swapped_arguments(self):
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier)
        # Swapping verifier/challenge should never validate
        assert verify_code_challenge(challenge, verifier) is False
