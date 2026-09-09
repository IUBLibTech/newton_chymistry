import asyncio
import httpx
import logging
import time
from typing import Optional, Union, Dict
from urllib.parse import urlparse

logger = logging.getLogger("fastapi_reverse_proxy")


class HealthChecker:
    def __init__(self, targets: list[str] | list[dict], interval: int = 10, timeout: int = 10, httpx_client: httpx.AsyncClient | None = None):
        if not targets:
            raise ValueError("Targets list cannot be empty")
        if interval < 1:
            raise ValueError("Interval must be at least 1")
        if timeout < 1:
            raise ValueError("Timeout must be at least 1")

        self.interval = interval
        self.timeout = timeout
        
        # Determine and enforce strict type (no mixing)
        first_type = type(targets[0])
        if first_type not in (str, dict):
             raise TypeError("Targets must be a list of strings or a list of dictionaries")
        
        self.is_personalized = (first_type is dict)
        self._global_ping_path = "/"

        # Internal storage
        self._targets_map: Dict[str, str] = {}
        # Stores extra config like 'maxrequests' from the dictionary
        self.target_configs: Dict[str, Dict] = {}

        for idx, t in enumerate(targets):
            if not isinstance(t, first_type):
                raise TypeError(f"Mixed types in targets at index {idx}. Total list must be same type.")
            
            if self.is_personalized:
                if "host" not in t:
                    raise KeyError(f"Target dictionary at index {idx} missing required 'host' key")
                u = urlparse(t["host"])
                host = f"{u.scheme}://{u.netloc}"
                self._targets_map[host] = t.get("pingpath", "/")
                self.target_configs[host] = t
            else:
                u = urlparse(t)
                host = f"{u.scheme}://{u.netloc}"
                self._targets_map[host] = self._global_ping_path
                self.target_configs[host] = {}

        self.targets = list(self._targets_map.keys())
        # Stores latency in ms or False if down
        self.status: Dict[str, Union[float, bool]] = {host: 0.0 for host in self.targets}
        self.last_update: float = time.perf_counter()

        self._task: Optional[asyncio.Task] = None

        # Track if WE created the client so we know if we should close it
        self._owns_client = httpx_client is None
        self._client = httpx_client or httpx.AsyncClient(timeout=self.timeout)

    @property
    def ping_path(self) -> str:
        if self.is_personalized:
            raise RuntimeError("Global ping_path is not supported when using personalized hosts")
        return self._global_ping_path

    @ping_path.setter
    def ping_path(self, value: str):
        if self.is_personalized:
            raise RuntimeError("Global ping_path is not supported when using personalized hosts")
        self._global_ping_path = value
        # Update all targets in map since we are in global mode
        for host in self._targets_map:
            self._targets_map[host] = value

    def __del__(self):
        """
        Class-built function for deletion
        
        WARNING: This one is last resort! Consider using .destroy() before exiting instead !
        Complete GC of this class is NOT guaranteed
        """
        if hasattr(self, '_client') and self._client is not None:
            try:
                logger.warning("You did not call .destroy() . Attempting cleanup via __del__ ... \n(Don't forget to add .destroy() at the end of your program)")
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self.destroy())
            except RuntimeError:
                pass

    async def _check_target(self, host: str):
        path = self._targets_map[host]
        url = f"{host.rstrip('/')}/{path.lstrip('/')}"
        
        start_time = time.perf_counter()
        try:
            response = await self._client.head(url)
            if response.status_code < 400:
                latency = (time.perf_counter() - start_time) * 1000
                self.status[host] = latency
            else:
                self.status[host] = False
        except Exception:
            self.status[host] = False
            logger.warning(f"Target {host} is DOWN")

    async def _loop(self):
        """The background loop."""
        while True:
            await self.check_all()
            await asyncio.sleep(self.interval)

    async def start(self):
        """Start the background health check loop."""
        if not self._task:
            await self.check_all() # Perform a check right on start
            self._task = asyncio.create_task(self._loop())

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.destroy()

    async def stop(self):
        """Stop the background loop."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError: pass
            self._task = None

    async def destroy(self):
        """Stop the loop AND close the httpx client."""
        await self.stop()
        if self._owns_client and self._client:
            await self._client.aclose()
            self._client = None

    async def check_all(self):
        """Pings all targets and updates their status."""
        tasks = [self._check_target(host) for host in self.targets]
        await asyncio.gather(*tasks)
        self.last_update = time.perf_counter()

    def get_healthy_targets(self):
        return [h for h in self.targets if self.status.get(h) is not False]

    def get_response_times(self) -> Dict[str, float]:
        return {t: float(v) for t, v in self.status.items() if v is not False}

    def get_fastest(self) -> str | None:
        r = self.get_response_times()
        return min(r, key=lambda t: r[t]) if r else None

    def is_healthy(self, target: str) -> bool:
        u = urlparse(target)
        host = f"{u.scheme}://{u.netloc}"
        status = self.status.get(host)
        return status is not False and status is not None
