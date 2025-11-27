import json
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from nacl.signing import VerifyKey
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError

class SignatureAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify cryptographic signatures on state-changing requests.
    Requires headers:
    - X-Pubkey: Hex encoded Ed25519 public key
    - X-Signature: Hex encoded signature
    - X-Timestamp: Unix timestamp (seconds)
    """
    
    def __init__(self, app, protected_paths: list[str] = None):
        super().__init__(app)
        self.protected_paths = protected_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Check if path is protected
        # We only protect state-changing methods (POST, PUT, DELETE) on specific paths
        if request.method not in ["POST", "PUT", "DELETE"]:
            return await call_next(request)
            
        is_protected = False
        for path in self.protected_paths:
            if request.url.path.startswith(path):
                is_protected = True
                break
        
        if not is_protected:
            return await call_next(request)

        # 2. Extract Headers
        pubkey_hex = request.headers.get("X-Pubkey")
        signature_hex = request.headers.get("X-Signature")
        timestamp_str = request.headers.get("X-Timestamp")

        # DEV BYPASS REMOVED: Strict Auth Enforced
        # client_host = request.client.host
        if not all([pubkey_hex, signature_hex, timestamp_str]):
            # if client_host in ["127.0.0.1", "localhost", "::1"]:
            #     print(f"⚠️  AUTH BYPASS: Allowing unsigned request from {client_host}")
            #     return await call_next(request)
            
            return JSONResponse(
                status_code=401, 
                content={"detail": "Missing authentication headers (X-Pubkey, X-Signature, X-Timestamp)"}
            )

        # 3. Verify Timestamp (Replay Protection)
        try:
            timestamp = int(timestamp_str)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 60: # 60 seconds window
                return JSONResponse(
                    status_code=401, 
                    content={"detail": "Request timestamp expired (Replay Protection)"}
                )
        except ValueError:
            return JSONResponse(
                status_code=401, 
                content={"detail": "Invalid timestamp format"}
            )

        # 4. Verify Signature
        try:
            # Read body (we need to consume it to verify, then make it available again)
            body_bytes = await request.body()
            try:
                body_json = json.loads(body_bytes)
                # Canonicalize exactly like the client does (no spaces!)
                body_str = json.dumps(body_json, sort_keys=True, separators=(',', ':'))
            except json.JSONDecodeError:
                # If not JSON, use raw body string? 
                # For now, we assume all our protected endpoints consume JSON.
                body_str = body_bytes.decode('utf-8')

            # Reconstruct payload
            # Format: METHOD:PATH:TIMESTAMP:BODY
            payload = f"{request.method}:{request.url.path}:{timestamp}:{body_str}"
            
            # DEBUG: Print payload for troubleshooting
            print(f"🔐 Auth Debug:")
            print(f"   Payload: {payload}")
            print(f"   Signature: {signature_hex}")
            print(f"   Pubkey: {pubkey_hex}")

            # Verify
            verify_key = VerifyKey(pubkey_hex, encoder=HexEncoder)
            verify_key.verify(payload.encode('utf-8'), bytes.fromhex(signature_hex))
            
        except (BadSignatureError, ValueError) as e:
             return JSONResponse(
                status_code=401, 
                content={"detail": f"Invalid signature: {str(e)}"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500, 
                content={"detail": f"Authentication error: {str(e)}"}
            )

        # 5. Proceed
        return await call_next(request)
