"""PKCE (Proof Key for Public Clients) utilities for OAuth2 Authorization Code flow.

PKCE prevents authorization code interception attacks by requiring the client to
prove it's the same entity that requested the authorization code.

The flow:
1. Client generates code_verifier (random 43-128 char string)
2. Client calculates code_challenge = BASE64URL(SHA256(code_verifier))
3. Client sends code_challenge to authorization server
4. Authorization server stores code_challenge
5. Client exchanges code + code_verifier with server
6. Server validates: BASE64URL(SHA256(code_verifier)) == stored code_challenge
7. If match, attacker who intercepted code cannot forge valid code_verifier

Security: Without code_verifier, attacker with intercepted code could exchange it.
With PKCE, attacker needs the code_verifier which was never transmitted.
"""

import secrets
import hashlib
import base64
from typing import Tuple


def generate_code_verifier() -> str:
    """
    Generate a cryptographically secure code verifier for PKCE.

    The code_verifier is a random string that the client will keep secret.
    It must be between 43-128 characters of unreserved characters.

    Unreserved characters: [A-Z] [a-z] [0-9] - . _ ~

    Returns:
        A random 128-character code verifier (maximum length for security)

    Example:
        >>> verifier = generate_code_verifier()
        >>> len(verifier)
        128
        >>> all(c.isalnum() or c in '-._~' for c in verifier)
        True
    """
    # Generate 96 random bytes and base64url encode
    # This gives us a 128-character string (96 bytes * 4/3 = 128 chars in base64)
    random_bytes = secrets.token_bytes(96)
    # base64url encoding: standard base64 but replace +/ with -_ and remove padding
    code_verifier = base64.urlsafe_b64encode(random_bytes).decode("utf-8")
    # Remove padding (= characters) as per PKCE spec
    return code_verifier.rstrip("=")


def generate_code_challenge(code_verifier: str) -> str:
    """
    Generate a code challenge from a code verifier using SHA256.

    This is the "S256" (SHA256) method from PKCE spec (RFC 7636).
    The code_verifier is hashed with SHA256, then base64url encoded.

    The challenge is what the client sends to the server during /authorize request.
    The server stores it and later validates the verifier against it.

    Args:
        code_verifier: The code verifier string (43-128 characters)

    Returns:
        A 43-character base64url-encoded SHA256 hash of the verifier

    Example:
        >>> verifier = generate_code_verifier()
        >>> challenge = generate_code_challenge(verifier)
        >>> len(challenge)
        43
        >>> verifier != challenge  # Challenge doesn't reveal verifier
        True
    """
    # 1. Hash the verifier with SHA256
    #    SHA256 always produces 32 bytes (256 bits)
    code_verifier_bytes = code_verifier.encode("utf-8")
    hash_digest = hashlib.sha256(code_verifier_bytes).digest()

    # 2. Base64url encode the hash
    #    32 bytes encodes to 43 characters (32 * 4/3 = 42.67 ≈ 43 with padding)
    code_challenge = base64.urlsafe_b64encode(hash_digest).decode("utf-8")

    # 3. Remove padding as per PKCE spec
    return code_challenge.rstrip("=")


def verify_code_challenge(code_verifier: str, code_challenge: str) -> bool:
    """
    Verify that a code verifier matches a previously stored code challenge.

    This is called on the server during the /token endpoint when the client
    exchanges the authorization code.

    Security: Attacker who intercepted the code cannot produce a valid
    code_verifier because they would need to reverse-engineer the original
    verifier from the challenge, which is cryptographically impossible with SHA256.

    Args:
        code_verifier: The verifier provided by the client in /token request
        code_challenge: The challenge stored by the server from /authorize request

    Returns:
        True if the verifier matches the challenge, False otherwise

    Example:
        >>> verifier = generate_code_verifier()
        >>> challenge = generate_code_challenge(verifier)
        >>> verify_code_challenge(verifier, challenge)
        True
        >>> verify_code_challenge("wrong_verifier", challenge)
        False
    """
    # Generate what the challenge should be from the provided verifier
    computed_challenge = generate_code_challenge(code_verifier)
    # Compare in constant time to prevent timing attacks
    # (attacker shouldn't be able to guess verifier by measuring response time)
    return secrets.compare_digest(computed_challenge, code_challenge)


# Example usage (for testing/learning):
if __name__ == "__main__":
    # This demonstrates the PKCE flow
    print("=== PKCE Flow Demonstration ===\n")

    # Step 1: Client generates verifier
    verifier = generate_code_verifier()
    print(f"1. Generated code_verifier (length {len(verifier)}):")
    print(f"   {verifier[:50]}...")
    print(f"   (This is kept secret by the client)\n")

    # Step 2: Client calculates challenge
    challenge = generate_code_challenge(verifier)
    print(f"2. Generated code_challenge (length {len(challenge)}):")
    print(f"   {challenge}")
    print(f"   (This is sent to the server)\n")

    # Step 3: Server stores challenge
    print("3. Server stores challenge with authorization code\n")

    # Step 4: Client later sends verifier with authorization code
    print("4. Client exchanges authorization code + code_verifier\n")

    # Step 5: Server validates
    is_valid = verify_code_challenge(verifier, challenge)
    print(f"5. Server validates: verify_code_challenge(verifier, challenge)")
    print(f"   Result: {is_valid}\n")

    # Show attack prevention
    print("=== Attack Prevention ===\n")
    wrong_verifier = generate_code_verifier()
    is_valid_wrong = verify_code_challenge(wrong_verifier, challenge)
    print(f"If attacker tries different verifier:")
    print(f"   verify_code_challenge(wrong_verifier, challenge) = {is_valid_wrong}")
    print(f"   ✓ Attack prevented!")
