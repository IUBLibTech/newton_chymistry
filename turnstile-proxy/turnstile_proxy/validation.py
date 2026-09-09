import time

from fastapi import Request
from config_model import Action, Config
from client_tests import get_client_ip, get_debug_id
from hashlib import sha512
import requests
import logging

def validate_cookie(config: Config, request: Request, action: Action) -> Action:
    """Validate the cookies and indicate the next action"""

    if action in (Action.DENY, Action.PASS):
        # do nothing if we've already denied or passed them.
        return action

    debug_id = get_debug_id(request)

    # why these cookie names?  Security by obscurity, really.      
    access_cookie = request.cookies.get('_3fa', None)    
    if access_cookie is None:
        logging.info(f"[{debug_id}] Access cookie is missing, force check")
        return Action.CHECK
    
    # the cookie is:  cookie_id:timeout:turnstile_token:generated_cookie
    cookie_parts = access_cookie.split(':')
    if len(cookie_parts) != 3:
        logging.warning(f"[{debug_id}] Cookie is malformed: {access_cookie}, forcing check")
        return Action.CHECK

    timeout, turnstile_token, generated_cookie = cookie_parts
    if timeout == '' and generated_cookie == '':
        # this is a cookie that just came from the validation page.  We test
        # the cloudflare_token to make sure it's legitimate and if it is we
        # move on with our lives.  Since the token can only be used once 
        # if it's not legitimate we'll deny them?
        data = {'response': turnstile_token,
                'secret': config.turnstile.secret_key,
                'remoteip': str(get_client_ip(request))}
        logging.debug(f"[{debug_id}] Checking turnstile token {data}")                      
        try:
            response = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify',
                                    data=data, timeout=10)
            response.raise_for_status()
            res = response.json()
            if res['success']:
                logging.info(f"[{debug_id}] Challenge successful, update access cookie")
                return Action.UPDATE                    
            else:
                if 'timeout-or-duplicate' in res['error-codes']:
                    logging.warning(f"[{debug_id}] Turnstile token timeout or duplicate: {res}")
                    return Action.CHECK
                else:
                    logging.warning(f"[{debug_id}] Validation failed for some other reason {res}")
                    return Action.CHECK
        except requests.RequestException as e:                
            logging.error(f"[{debug_id}] Turnstile service error: {e}")
            # we had an error, just pass the content
            # NOTE: We're actually going to create a cookie that's valid even
            # though we really don't know for sure.  It'll expire in an hour
            # anyway in the event that we're wrong.
            return Action.UPDATE

    # At this point we have all of the access_cookie fields and we need to decide
    # whether or not it's a valid cookie -- which may mean forcing them to
    # revalidate if it isn't.
    test_cookie = compute_cookie(config, request, turnstile_token, timeout)
    if test_cookie != access_cookie:
        # the cookies don't match. Which means that someone has tampered with
        # them, or tried to use with with a different browser / IP.
        logging.warning(f"[{debug_id}] The access cookie supplied is invalid.  Forcing revalidation")
        #logging.debug(f"[{debug_id}] {generated_cookie} != {test_cookie}")
        return Action.CHECK
    
    # if the cookie has timed out we also want to force revalidation
    if float(timeout) < time.time():
        logging.info(f"[{debug_id}] The access cookie has expired.  Forcing revalidation")
        return Action.CHECK

    return Action.PASS    


def compute_cookie(config: Config, request: Request, token: str, timeout: str=None):
    """Compute a per-browser validation cookie in the
       form:  <timeout>:<turnstile_token>:<generated_cookie>"""    
    client_ip = str(get_client_ip(request))
    ua = request.headers.get('User-Agent', 'NO-UA')
    timeout = str(int(time.time() + config.cookie_timeout)) if timeout is None else timeout    
    payload = sha512(bytes(":".join(["Salty-salt to make things unpredictable", 
                                     token, client_ip, ua, timeout]), encoding='utf-8')).hexdigest()
    cookie = ':'.join([timeout, token, payload])
    #logging.debug(f"[{get_debug_id(request)}] Generated cookie using {token}, {client_ip}, {ua}, {timeout}")
    return cookie


def update_cookie(config: Config, request: Request, original_cookie: str):
    """Take a cookie from the client and update it with new information"""
    original_token = original_cookie.split(':')[1]
    #logging.debug(f"[{get_debug_id(request)}] Updating cookie using {original_token}")
    return compute_cookie(config, request, original_token)




