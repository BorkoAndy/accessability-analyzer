import os
import json

def check_auth(handler):
    """
    Checks if the request is authorized.
    Verification is active only if APP_PASSWORD env var is set.
    """
    app_password = os.environ.get("APP_PASSWORD")
    
    # If no password is set in env, we allow access
    if not app_password:
        return True

    # Check X-API-Key header
    auth_header = handler.headers.get("X-API-Key")
    if auth_header == app_password:
        return True
    
    # Also check Authorization header for flexibility
    authorization = handler.headers.get("Authorization")
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        if token == app_password:
            return True

    # Not authorized
    handler.send_response(401)
    for k, v in _cors_headers().items():
        handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(json.dumps({"error": "Unauthorized: Invalid password"}).encode())
    return False

def _cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-API-Key, Authorization",
    }
