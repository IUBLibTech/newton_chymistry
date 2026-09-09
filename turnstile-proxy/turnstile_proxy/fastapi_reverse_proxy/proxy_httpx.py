import httpx
from fastapi import FastAPI, Request

class Proxy:
    def __init__(self, app: FastAPI):
        """Initializes the HTTP client and stores it in the app state."""
        self.__app = app # store the app as internal variable
        self.__app.state.http_proxy_client = httpx.AsyncClient()
        
    async def close(self):
        """Closes the HTTP client stored in the app state."""
        if hasattr(self.__app.state, "http_proxy_client"):
            await self.__app.state.http_proxy_client.aclose() # close it
            
    async def __aenter__(self): return self # __init__ on async with
        
    async def __aexit__(self, exc_type, exc_val, exc_tb): await self.close() # self-close on async with

async def create_httpx_client(app: FastAPI):
    """Initializes the HTTP client and stores it in the app state."""
    app.state.http_proxy_client = httpx.AsyncClient()

async def close_httpx_client(app: FastAPI):
    """Closes the HTTP client stored in the app state."""
    if hasattr(app.state, "http_proxy_client"):
        await app.state.http_proxy_client.aclose() # close it

async def get_httpx_client(req: Request) -> httpx.AsyncClient:
    """Retrieves the HTTP client from the app state."""
    return req.app.state.http_proxy_client