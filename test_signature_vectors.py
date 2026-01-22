#!/usr/bin/env python3
"""
Generate test vectors for Last.fm API signature verification.
This ensures Rust implementation matches Python byte-for-byte.
"""

import hashlib


def sign_params(params: dict, api_secret: str) -> str:
    """Generate Last.fm API signature (Python implementation)."""
    # Sort and concatenate parameters (excluding 'format')
    sorted_items = sorted((k, v) for k, v in params.items() if k != 'format')
    signature_string = "".join(f"{k}{v}" for k, v in sorted_items) + api_secret
    return hashlib.md5(signature_string.encode('utf-8')).hexdigest()


# Test vector 1: Basic authentication
params1 = {
    'method': 'auth.getToken',
    'api_key': 'test_key',
}
sig1 = sign_params(params1, 'test_secret')
print("Test 1 - Basic auth:")
print(f"  Params: {params1}")
print(f"  Signature: {sig1}")
print()

# Test vector 2: With format parameter (should be excluded)
params2 = {
    'method': 'auth.getToken',
    'api_key': 'test_key',
    'format': 'json',
}
sig2 = sign_params(params2, 'test_secret')
print("Test 2 - With format (should match Test 1):")
print(f"  Params: {params2}")
print(f"  Signature: {sig2}")
print(f"  Matches Test 1: {sig1 == sig2}")
print()

# Test vector 3: Scrobble with session key
params3 = {
    'method': 'track.scrobble',
    'api_key': 'test_key',
    'sk': 'session_key_123',
    'artist': 'Artist Name',
    'track': 'Track Name',
    'timestamp': '1234567890',
}
sig3 = sign_params(params3, 'test_secret')
print("Test 3 - Scrobble:")
print(f"  Params: {params3}")
print(f"  Signature: {sig3}")
print()

# Test vector 4: Alphabetical ordering test
params4 = {
    'track': 'Test Track',
    'artist': 'Test Artist',
    'method': 'track.scrobble',
    'api_key': 'abc123',
}
sig4 = sign_params(params4, 'secret123')
print("Test 4 - Alphabetical ordering:")
print(f"  Params: {params4}")
print(f"  Signature: {sig4}")
print()

# Generate Rust test code
print("\n// Rust test code:\n")
print("""
#[test]
fn test_sign_params_basic() {
    let mut params = BTreeMap::new();
    params.insert("method".to_string(), "auth.getToken".to_string());
    params.insert("api_key".to_string(), "test_key".to_string());

    let api_secret = "test_secret";
    let signature = sign_params(&params, api_secret);

    assert_eq!(signature, \"""" + sig1 + """\");
}

#[test]
fn test_sign_params_excludes_format() {
    let mut params = BTreeMap::new();
    params.insert("method".to_string(), "auth.getToken".to_string());
    params.insert("api_key".to_string(), "test_key".to_string());
    params.insert("format".to_string(), "json".to_string());

    let api_secret = "test_secret";
    let signature = sign_params(&params, api_secret);

    assert_eq!(signature, \"""" + sig1 + """\");
}

#[test]
fn test_sign_params_scrobble() {
    let mut params = BTreeMap::new();
    params.insert("method".to_string(), "track.scrobble".to_string());
    params.insert("api_key".to_string(), "test_key".to_string());
    params.insert("sk".to_string(), "session_key_123".to_string());
    params.insert("artist".to_string(), "Artist Name".to_string());
    params.insert("track".to_string(), "Track Name".to_string());
    params.insert("timestamp".to_string(), "1234567890".to_string());

    let api_secret = "test_secret";
    let signature = sign_params(&params, api_secret);

    assert_eq!(signature, \"""" + sig3 + """\");
}

#[test]
fn test_sign_params_sorted_order() {
    let mut params = BTreeMap::new();
    params.insert("track".to_string(), "Test Track".to_string());
    params.insert("artist".to_string(), "Test Artist".to_string());
    params.insert("method".to_string(), "track.scrobble".to_string());
    params.insert("api_key".to_string(), "abc123".to_string());

    let api_secret = "secret123";
    let signature = sign_params(&params, api_secret);

    assert_eq!(signature, \"""" + sig4 + """\");
}
""")
