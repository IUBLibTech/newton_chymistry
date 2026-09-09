from fastapi import Request, WebSocket, Response, HTTPException
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from url_normalize import url_normalize
import httpx
import websockets
import asyncio
import logging
import inspect
from typing import Optional
from .proxy_httpx import get_httpx_client
from urllib.parse import urlparse

logger = logging.getLogger("fastapi_reverse_proxy")

# Hop-by-hop headers that should typically not be forwarded by a proxy
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/TE
EXCLUDED_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", 
    "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"
}

def url_normalize_ws(url:str):
    u = urlparse(url)
    return url_normalize(url.replace(u.scheme, "http", 1)).replace("http", u.scheme, 1)

async def handle_proxy_exception(e: Exception):
    """Maps internal exceptions to FastAPI HTTPExceptions for the client."""
    if isinstance(e, httpx.ConnectTimeout):
        raise HTTPException(status_code=504, detail="Gateway Timeout")
    if isinstance(e, (httpx.ConnectError, httpx.RemoteProtocolError)):
        raise HTTPException(status_code=502, detail="Bad Gateway")
    if isinstance(e, httpx.ReadTimeout):
        raise HTTPException(status_code=504, detail="Upstream Read Timeout")
    # Re-raise other exceptions (like CancelledError or internal bugs) to avoid masking
    raise e
    
async def proxy_pass(
    request: Request, 
    host: str,
    path: Optional[str] = None,
    timeout: float = 60.0, 
    forward_query: bool = True,
    additional_headers: Optional[dict] = None,
    override_headers: Optional[dict] = None,
    override_body: Optional[bytes] = None,
    method: Optional[str] = None,
    override_host: Optional[str] = None
):
    """
    Forwards incoming HTTP requests to the target service using streaming.
    - host: The host itself (without ending slash)
    - path: The path w/ beggining slash (by default copies requests's path)
    - forward_query: If True, automatically appends the request's query string.
    - additional_headers: Headers to add to the upstream request.
    - override_headers: Use these headers instead of original request headers.
    - override_body: Use this body instead of streaming the request body.
    - method: HTTP method to use (e.g., 'POST'). Defaults to original request method.
    """
    
    if path is None: path = request.url.path # set to path
    
    # normalize host + path
    url = url_normalize(host + path, default_scheme="http")
    
    if forward_query and request.url.query:
        url = f"{url}?{request.url.query}" if "?" not in url else f"{url}&{request.url.query}"
        
    # normalize again
    url = url_normalize(url ,default_scheme="http")
    
    # Determine method
    final_method = method or request.method

    # Resolve headers
    if override_headers is not None:
        headers = dict(override_headers)
    else:
        headers = dict(request.headers)
        # Identify the client's real IP and forward it
        client_host = request.client.host if request.client else "unknown"
        headers["X-Real-IP"] = client_host
        if "X-Forwarded-For" in headers:
            headers["X-Forwarded-For"] = f"{headers['X-Forwarded-For']}, {client_host}"
        else:
            headers["X-Forwarded-For"] = client_host
        
        headers["X-Forwarded-Proto"] = request.url.scheme
        headers["X-Forwarded-Host"] = headers.get("host", request.url.netloc)
    
    # Apply additional headers
    if additional_headers:
        headers.update(additional_headers)
    
    # Let httpx handle the host header and connection management
    if override_host:
        headers['host'] = override_host
    else:
        headers.pop("host", None)
    headers.pop("connection", None)

    client = None
    try:
        client = await get_httpx_client(request)
        is_global_client = True
    except Exception:
        # Fallback for testing or standalone usage
        client = httpx.AsyncClient()
        is_global_client = False

    try:
        # Prepare content
        if override_body is not None:
            content = override_body
        else:
            # Stream the request body to the target (efficient for large uploads)
            async def request_generator():
                async for chunk in request.stream():
                    yield chunk
            content = request_generator() if final_method in ("POST", "PUT", "PATCH", "DELETE") else None

        # Create the upstream request
        rp_req = client.build_request(
            method=final_method,
            url=url,
            headers=headers,
            content=content,
            timeout=timeout
        )

        # Send the request and stream the response
        rp_resp = await client.send(rp_req, stream=True)

        try:
            # Filter response headers
            resp_headers = {}
            for k, v in rp_resp.headers.items():
                if k.lower() in EXCLUDED_HEADERS:
                    continue
                if k.lower() == "content-encoding":
                    continue
                if k.lower() == "content-length":
                    continue
                resp_headers[k] = v
            
            resp_headers["X-Accel-Buffering"] = "no"
            resp_headers["Cache-Control"] = "no-cache"

            async def cleanup():
                await rp_resp.aclose()
                if not is_global_client:
                    await client.aclose()

            return StreamingResponse(
                rp_resp.aiter_bytes(),
                status_code=rp_resp.status_code,
                headers=resp_headers,
                background=BackgroundTask(cleanup)
            )
        except BaseException as e:
            # If we fail here, the ownership hasn't passed to StreamingResponse yet
            await rp_resp.aclose()
            raise e
            
    except BaseException as e:
        # Catch EVERY exception (including CancelledError) for local client cleanup
        if not is_global_client and client:
            await client.aclose()
        
        # Transform httpx errors into proper HTTP responses
        if not isinstance(e, asyncio.CancelledError):
            await handle_proxy_exception(e)
            
        raise e


async def proxy_pass_websocket(
    websocket: WebSocket, 
    host: str,
    path: Optional[str] = None,
    subprotocols: Optional[list[str]] = None, 
    forward_query: bool = True,
    additional_headers: Optional[dict] = None,
    override_headers: Optional[dict] = None,
    timeout: float = 10.0
):
    """
    Forwards incoming WebSocket connections to the target service.
    - host: The host itself (without ending slash)
    - path: The path with beggining slash (by default copies requests's path)
    - forward_query: If True, automatically appends the request's query string.
    - timeout: Time to wait for the connection handshake (open_timeout).
    """
    
    if path is None: path = websocket.url.path
    url = url_normalize_ws(host + path)
    
    if forward_query and websocket.url.query:
        url = f"{url}?{websocket.url.query}" if "?" not in url else f"{url}&{websocket.url.query}"

    # Ensure we use ws:// or wss://
    if url.startswith("http://"):
        url = url.replace("http://", "ws://", 1)
    elif url.startswith("https://"):
        url = url.replace("https://", "wss://", 1)

    # Resolve headers
    if override_headers is not None:
        headers = dict(override_headers)
    else:
        client_host = websocket.client.host if websocket.client else "unknown"
        headers = {
            "X-Real-IP": client_host,
            "X-Forwarded-For": client_host,
            "X-Forwarded-Proto": websocket.url.scheme,
            "X-Forwarded-Host": websocket.headers.get("host", websocket.url.netloc)
        }
    
    if additional_headers:
        headers.update(additional_headers)

    # Use subprotocols from scope if not provided explicitly
    supported_subprotocols = subprotocols or websocket.scope.get("subprotocols")

    try:
        # Determine the correct header parameter name for this version of websockets
        # Modern (12.0+): additional_headers, Legacy: extra_headers
        _params = inspect.signature(websockets.connect).parameters
        header_param = "additional_headers" if "additional_headers" in _params else "extra_headers"
        
        connect_kwargs = {
            header_param: headers,
            "subprotocols": supported_subprotocols,
            "open_timeout": timeout
        }

        async with websockets.connect(url, **connect_kwargs) as target_ws:
            # Accept once we know the negotiated subprotocol
            await websocket.accept(subprotocol=target_ws.subprotocol)
            await _handle_ws_bidirectional(websocket, target_ws)

    except BaseException as e:
        if not isinstance(e, asyncio.CancelledError):
            # If the connection fails before accept(), we can raise a proper 502
            if not websocket.client.connected: # Roughly checking if handshake finished
                logger.error(f"WebSocket Connection Error: {e}")
                # This is a bit tricky in WS, but if we haven't accepted yet, we can raise
                try:
                    raise HTTPException(status_code=502, detail="Bad Gateway: WebSocket connection failed")
                except RuntimeError: # If already accepted, we can't raise HTTPException
                    pass
            else:
                logger.error(f"WebSocket Proxy Error: {e}")
        raise e
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


async def _handle_ws_bidirectional(websocket: WebSocket, target_ws):
    """Internal helper to manage bidirectional WS traffic with clean cancellation."""
    async def client_to_target():
        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.receive":
                    if "text" in message:
                        await target_ws.send(message["text"])
                    elif "bytes" in message:
                        await target_ws.send(message["bytes"])
                elif message["type"] == "websocket.disconnect":
                    break
        except (Exception, asyncio.CancelledError):
            # Exit loop on error or cancellation
            pass

    async def target_to_client():
        try:
            while True:
                message = await target_ws.recv()
                if isinstance(message, str):
                    await websocket.send_text(message)
                else:
                    await websocket.send_bytes(message)
        except (Exception, asyncio.CancelledError, websockets.ConnectionClosed):
            # Exit loop on error, closure, or cancellation
            pass

    # Wrap in tasks for cancellation
    tasks = [
        asyncio.create_task(client_to_target()),
        asyncio.create_task(target_to_client())
    ]
    
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        # Ensure all tasks are gathered and exceptions (including CancelledError) are handled
        await asyncio.gather(*tasks, return_exceptions=True)
