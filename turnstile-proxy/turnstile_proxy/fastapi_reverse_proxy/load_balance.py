from .health_check import HealthChecker
from fastapi import Request, Response, WebSocket
from urllib.parse import urlparse
from typing import Dict, Optional
import asyncio, logging
from url_normalize import url_normalize

logger = logging.getLogger("fastapi_reverse_proxy")

class LoadBalancer:
    """
    Dual-mode Load Balancer.
    - Round-robin: if passed a list of strings.
    - Health-based: if passed a HealthChecker object.
    
    Includes request limits that reset every health-check interval.
    """
    
    def __init__(self, servers: list | HealthChecker):
        self.servers = servers
        self.__index = 0
        self.__healthMode: bool = isinstance(servers, HealthChecker)
        
        # Local request tracking
        self._request_counts: Dict[str, int] = {}
        self._last_health_update: float = 0.0
        
        # Limits: host -> max_requests
        self._limits_map: Dict[str, Optional[int]] = {}
        self._global_max_requests: Optional[int] = None
        
        if self.__healthMode:
             # Populate initial limits if targets were dictionaries (Manual mode)
             for host in self.servers.targets:
                 # Check 'maxrequests' in the target_configs from the health checker
                 config = self.servers.target_configs.get(host, {})
                 self._limits_map[host] = config.get("maxrequests")
                 
    @property
    def max_requests(self) -> Optional[int]:
        if self.__healthMode and self.servers.is_personalized:
             raise RuntimeError("Global max_requests is not supported when using personalized hosts")
        return self._global_max_requests

    @max_requests.setter
    def max_requests(self, value: Optional[int]):
        if self.__healthMode and self.servers.is_personalized:
             raise RuntimeError("Global max_requests is not supported when using personalized hosts")
        self._global_max_requests = value
        # Update current limits map since we are in global/auto mode
        if self.__healthMode:
            for host in self._limits_map:
                self._limits_map[host] = value

    def _get_best_healthy(self) -> str | None:
        """Returns the fastest healthy host that hasn't hit its request limit."""
        # Detect if HealthChecker performed a new check and reset counts
        if self.servers.last_update > self._last_health_update:
            self._request_counts = {h: 0 for h in self.servers.targets}
            self._last_health_update = self.servers.last_update
        
        # Get healthy hosts with their latencies
        r = self.servers.get_response_times()
        
        # Filter out those over their limit
        available = {}
        for host, latency in r.items():
            # Use specific limit from _limits_map OR the global one if it's not set per-host
            limit = self._limits_map.get(host) if self.servers.is_personalized else self._global_max_requests
            
            if limit is None or self._request_counts.get(host, 0) < limit:
                available[host] = latency
        
        if not available:
            return None
        
        return min(available, key=lambda t: available[t])
    def peek(self) -> str | None:
        if self.__healthMode:
            return self._get_best_healthy()
        else:
            if not self.servers: return None
            return self.servers[self.__index]
    
    def get(self) -> str | None:
        if self.__healthMode:
            best = self._get_best_healthy()
            if best:
                self._request_counts[best] = self._request_counts.get(best, 0) + 1
            return best
        else:
            if not self.servers: return None
            try:
                return self.servers[self.__index]
            finally:
                self.__index = (self.__index + 1) % len(self.servers)
        
    def get_all(self) -> list:
        if self.__healthMode: return self.servers.targets
        else: return self.servers

    def set_index(self, index: int) -> None:
        if self.__healthMode:
            raise RuntimeError("set_index() is not supported in health mode")
        if index < 0 or (self.servers and index >= len(self.servers)):
            raise IndexError("Index out of range")
        self.__index = index

    async def proxy_pass(
        self, 
        req: Request, 
        path: str, 
        timeout: float = 60.0, 
        forward_query: bool = True,
        additional_headers: Optional[dict] = None,
        override_headers: Optional[dict] = None,
        override_body: Optional[bytes] = None,
        method: Optional[str] = None
    ):
        from .proxy_pass import proxy_pass as _proxy_pass  # Late import
        
        target = self.get()
        if not target:
            return Response("Service Unavailable: No healthy backends available or all over limit", status_code=503)
            
        #u = urlparse(target)
        #origin = f"{u.scheme}://{u.netloc}"
        # Smart pathing: combine origin and user-provided path
        #dest_url = f"{origin.rstrip('/')}/{path.lstrip('/')}"
        
        return await _proxy_pass(
            request=req, 
            host=url_normalize(target, default_scheme="http"),
            path=path,
            timeout=timeout, 
            forward_query=forward_query,
            additional_headers=additional_headers,
            override_headers=override_headers,
            override_body=override_body,
            method=method
        )

    async def proxy_pass_websocket(
        self, 
        websocket: WebSocket, 
        path: Optional[str] = None, 
        subprotocols: list[str] | None = None, 
        forward_query: bool = True,
        additional_headers: Optional[dict] = None,
        override_headers: Optional[dict] = None
    ):
        from .proxy_pass import proxy_pass_websocket as _proxy_pass_ws  # Late import
        
        target = self.get()
        if not target:
            await websocket.close(code=1011)
            return

        u = urlparse(target)
        origin = f"{u.scheme}://{u.netloc}"
        

        return await _proxy_pass_ws(
            websocket, 
            host=origin,
            path=path,
            subprotocols=subprotocols, 
            forward_query=forward_query,
            additional_headers=additional_headers,
            override_headers=override_headers
        )

