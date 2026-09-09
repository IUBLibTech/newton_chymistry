#!/bin/env python3
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from contextlib import asynccontextmanager
from fastapi_reverse_proxy import Proxy, proxy_pass
from config_model import Action, Config
import yaml
import argparse
import uvicorn
from client_tests import compile_rule, get_client_ip, get_debug_id
from validation import update_cookie, validate_cookie
import sys
import os
from string import Template
import signal
import logging.handlers


def _log_to_stdout() -> bool:
    """When running under a container/orchestrator (e.g. Kubernetes) logs must go
       to stdout/stderr so `kubectl logs` can see them; TimedRotatingFileHandler
       writes to files inside the container where they're invisible.  Opt in with
       TURNSTILE_LOG_TO_STDOUT=1.  Defaults off so file logging is preserved for
       single-host deployments."""
    return os.environ.get("TURNSTILE_LOG_TO_STDOUT", "").strip().lower() in ("1", "true", "yes", "on")

def sighup_handler(sig, frame):
    logging.info("Caught SIGHUP - disconnecting from terminal")
    sys.stderr.close()
    sys.stdout.close()
    sys.stdin.close()

# from the sample at: https://github.com/tfsantos05/fastapi-reverse-proxy/blob/main/examples/01_simple_proxy.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    # init the httpx connection pool via the proxy manager
    async with Proxy(app):
        yield

app = FastAPI(lifespan=lifespan)

@app.api_route("/{path:path}", methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD'])
async def gateway(request: Request, path: str):
    """This is the reverse proxy itself."""
    debug_id = get_debug_id(request)
    for rule in config.rules:        
        if (action := rule._checkfunc(request)) != Action.IGNORE:               
            logging.debug(f"[{debug_id}] rule matches {rule} -> {action}")                  
            break
    else:        
        logging.debug(f"[{debug_id}] No rules matched for {request.url.path} -> {config.default_action}")
        action = config.default_action
    
    
    # check the cookie and update our action if necesary.
    new_action = validate_cookie(config, request, action)
    if new_action != action:
        logging.debug(f"[{debug_id}] action has changed from {action} -> {new_action}")
        action = new_action

    if action == Action.DENY:
        # Send back the deny page        
        logging.debug(f"[{debug_id}] Sending deny page")
        content = (Path(__file__).parent / "deny.html").read_text()        
        content = Template(content).safe_substitute(remote_ip=str(get_client_ip(request)),
                                                    user_agent=request.headers.get(request.headers['User-Agent'], 'No user agent specified'),
                                                    request_url=str(request.url))
        return HTMLResponse(content, 401)
    
    elif action == Action.CHECK:
        # send the check page
        logging.debug(f"[{debug_id}] Sending verify page")        
        content = (Path(__file__).parent / "verify.html").read_text()
        content = Template(content).safe_substitute(site_key=config.turnstile.site_key)
        return HTMLResponse(content, 200)
    
    elif action in (Action.UPDATE, Action.PASS):
        # proxy the resource, possibly updating the cookie     
        logging.info(f"[{debug_id}] Proxying content")      
        res: StreamingResponse = await proxy_pass(request, config.backend,                                 
                                                  timeout=config.timeout,
                                                  override_host=request.headers['host'])
        if action == Action.UPDATE:
            logging.debug(f"[{debug_id}] Updating the cookie")
            res.set_cookie('_3fa', update_cookie(config, request, request.cookies['_3fa']),
                           domain=request.headers.get('host', None))
        return res
    
    else:
        # WTF?
        logging.error(f"[{debug_id}] Unknown action: {action}")
        return HTMLResponse("Unknown action", 500)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Configuration file")
    parser.add_argument("--debug", action="store_true", help="Turn on debug logging")
    parser.add_argument("--debug_tests", action="store_true", help="Debug the test functions")
    parser.add_argument("--nohup", action="store_true", help="Ignore SIGHUP")
    parser.add_argument("--testport", type=int, help="Override configured port for testing")
    args = parser.parse_args()

    config: Config = Config(**yaml.safe_load(Path(args.config).read_text()))

    log_to_stdout = _log_to_stdout()

    if log_to_stdout:
        app_log_handler = logging.StreamHandler(sys.stdout)
    else:
        app_log_handler = logging.handlers.TimedRotatingFileHandler(Path(__file__).parent / "logs/application.log",
                                                                    when="midnight")
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        #filename=Path(__file__).parent / "logs/application.log",
                        handlers=[app_log_handler],
                        format="%(asctime)s | %(levelname)-8s | "
                            "%(module)s:%(funcName)s:%(lineno)d - %(message)s")

    if args.nohup:
        # Install the sighup handler
        logging.info("Process will ignore SIGHUP")
        signal.signal(signal.SIGHUP, sighup_handler)


    # compile all of the rules into inline functions.
    for r in config.rules:
        compile_rule(r, args.debug_tests)
        
    # reconfigure obnoxious uvicorn's logging
    log_config = uvicorn.config.LOGGING_CONFIG
    if not log_to_stdout:
        log_config["handlers"]["file"] = {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "filename": Path(__file__).parent / "logs/uvicorn.log",
            "formatter": "default",

        }
        log_config["loggers"]["uvicorn"]["handlers"] = ["file"]
        log_config["handlers"]["access"] = {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "filename": Path(__file__).parent / "logs/access.log",
            "formatter": "access",
        }
        log_config["loggers"]["uvicorn.access"]["handlers"] = ["access"]
    # else: leave uvicorn's default handlers, which already write to stdout/stderr.

    uvicorn.run(app, 
                host=str(config.host), 
                port=config.port if not args.testport else args.testport, 
                log_level=logging.DEBUG if args.debug else logging.INFO)
