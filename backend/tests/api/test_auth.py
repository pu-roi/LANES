import pytest
from fastapi.testclient import TestClient

def test_login_rate_limiting(client: TestClient):
    """
    Test that the slowapi rate limiter kicks in after 5 requests to the login endpoint.
    """
    # The endpoint is /api/v1/auth/login/access-token
    # Since we don't have the router prefix in this isolated scope, we need the full path
    
    endpoint = "/api/v1/auth/login/access-token"
    
    # We will send 6 requests. The first 5 might fail with 400 or 403 (invalid credentials), 
    # but the 6th must fail with 429 Too Many Requests.
    
    status_codes = []
    for _ in range(6):
        response = client.post(
            endpoint, 
            data={"username": "testuser", "password": "wrongpassword"},
            # slowapi needs the client IP
            headers={"X-Forwarded-For": "127.0.0.1"}
        )
        status_codes.append(response.status_code)
    
    # The 6th request should be rate-limited (429)
    assert status_codes[-1] == 429
    assert "Too Many Requests" in response.text or response.status_code == 429
