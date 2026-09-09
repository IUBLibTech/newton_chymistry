from ipaddress import IPv4Address, IPv4Network, ip_network
from crawlerdetect import CrawlerDetect
from fastapi import Request
import re
from config_model import Rule, Trit, Action
from functools import lru_cache
import socket
import json
from pathlib import Path
import logging
import urllib.request

def test_trit(expected: Trit, value: bool) -> Trit:
    if (expected == Trit.YES and value) or (expected == Trit.NO and not value):
        return Trit.YES
    else:
        return Trit.NO


# Address ranges we treat as our own infrastructure ("trusted proxies"), not
# as clients.  Only genuinely private / loopback / link-local ranges belong
# here -- NOT our institution's public ranges, which are real client
# addresses.  This mirrors the default trusted set that Rails'
# ActionDispatch::RemoteIp uses.
trusted_proxy_networks: list[IPv4Network] = [
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("127.0.0.0/8"),
    ip_network("169.254.0.0/16"),  # link-local
]


def _is_trusted_proxy(addr: IPv4Address) -> bool:
    return any(addr in net for net in trusted_proxy_networks)


def get_client_ip(request: Request) -> IPv4Address:
    """Return the real client address.

    Behind a multi-node ingress (Traefik/Kubernetes) the request reaches us via
    a chain of internal hops, and the closest hop's address changes from one
    request to the next.  Naively trusting X-Real-IP, the first X-Forwarded-For
    entry, or the raw TCP peer therefore yields an unstable address -- which
    breaks anything that keys off the client IP (e.g. the validation cookie,
    which then never matches and re-challenges the user on every request).

    We instead resolve the client the way Rails' ActionDispatch::RemoteIp does:
    collect the forwarded chain closest-hop-first, and return the first address
    that isn't one of our own private/loopback proxy hops.  Walking from the
    closest hop outward (rather than trusting the left-most, client-supplied
    entry) also means a spoofed X-Forwarded-For prefix can't win.
    """
    candidates: list[str] = []

    # X-Forwarded-For is "client, proxy1, proxy2, ..." -- left-most is the
    # original client, each hop appends the peer it saw.  Reverse it so we
    # evaluate the hop closest to us first.
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        candidates.extend(reversed([p.strip() for p in xff.split(',') if p.strip()]))

    # nginx-style single-value header, if an upstream set one.
    xri = request.headers.get('X-Real-IP')
    if xri:
        candidates.append(xri.strip())

    # the raw TCP peer, as a last resort.
    if request.client:
        candidates.append(request.client.host)

    first_valid: IPv4Address | None = None
    for raw in candidates:
        try:
            addr = IPv4Address(raw)
        except ValueError:
            # skip IPv6 hops and any garbage -- see IPv6 note below.
            continue
        if first_valid is None:
            first_valid = addr
        if not _is_trusted_proxy(addr):
            return addr

    # Every candidate was one of our own hops (or there were none): fall back to
    # the closest valid address rather than raising.
    if first_valid is not None:
        return first_valid
    raise ValueError("Could not determine a client IP from the request")


# DNS forward + reverse lookup is really expensive, so I'm going to cache most 
# recently used entries 
@lru_cache(maxsize=4096)
def lookup_ip(addr: IPv4Address) -> tuple[IPv4Address, str]:
    try:
        hostname = socket.gethostbyaddr(str(addr))[0]
        rev_addr = IPv4Address(socket.gethostbyname(hostname))
        return (rev_addr, hostname)
    except Exception:
        return (None, None)


crawler_detect = CrawlerDetect()

def is_crawler(mode: Trit, request: Request) -> Trit:
    """Check to see if this is a crawler.  If mode is 'dontcare' then return
       'dontcare', otherwise return 'yes' if the mode matches the crawler-ness
       and 'no' otherwise"""
    if mode == Trit.DONTCARE:
        return mode

    return test_trit(mode, crawler_detect.is_crawler(request.headers.get('User-Agent', '')))


# load the duckduckgo ip list.
duckduck_networks = []
duckduck_jsonfile = Path(__file__).parent / "duckduckbot.json"
if not duckduck_jsonfile.exists():
    urllib.request.urlretrieve("https://duckduckgo.com/duckduckbot.json", duckduck_jsonfile)

duckduck_data = json.loads(duckduck_jsonfile.read_text())
for x in duckduck_data['prefixes']:
    duckduck_networks.append(IPv4Network(x['ipv4Prefix'], strict=False))


def is_search(mode: Trit, request: Request) -> Trit:
    """Check to see if this is a search engine.  If mode is 'dontcare' then return
       'dontcare', otherwise return 'yes' if the mode matches the search engine-ness
       and 'no' otherwise"""
    if mode == Trit.DONTCARE:
        return mode    

    # Support:  Google, Bing, DuckDuckGo, others?
    if 'User-Agent' in request.headers:
        ua = request.headers['User-Agent'].lower()
        addr = get_client_ip(request)
        if 'google' in ua:
            # Google says if you think it's them, do a dns lookup and check if
            # it's in google.com, googlebot.com, or googleusercontent.com and 
            # then a reverse DNS to check to make sure you get the same IP
            # back.            
            rev_addr, hostname = lookup_ip(addr)
            if hostname and any([hostname.endswith(x) for x in ('google.com', 'googlebot.com', 'googleusercontent.com')]) and addr == rev_addr:
                return Trit.YES
            else:
                return Trit.NO

        elif 'bingbot/' in ua:
            # Bing sez that you do the forward search and look for a name ending 
            # with search.msn.com and then verify the reverse lookup is the same
            # ip.            
            rev_addr, hostname = lookup_ip(addr)
            if hostname.endswith('search.msn.com') and addr == rev_addr:
                return Trit.YES
            else:
                return Trit.NO
        elif 'duckduckbot/' in ua:
            # Per https://duckduckgo.com/duckduckgo-help-pages/results/duckduckbot
            # we get the above prefix and it should come from one of the 341 IPs
            # listed at https://duckduckgo.com/duckduckbot.json            
            return test_trit(mode, any([addr in x for x in duckduck_networks]))
        else:
            return Trit.NO
    else:
        return Trit.NO


# Build a CIDR networks table for IU local networks
local_networks: list[IPv4Network] = []
for n in ["129.79.0.0/16", "134.68.0.0/16", "140.182.0.0/16",
          "140.182.0.0/19", "149.159.0.0/17", "149.159.0.0/19",
          "149.160.0.0/14", "149.160.0.0/16", "149.161.0.0/16",
          "149.161.128.0/17", "149.162.0.0/16", "149.163.0.0/16",
          "149.165.0.0/17", "149.166.0.0/16", "156.56.0.0/16",
          "198.49.177.0/24",
          "10.0.0.0/8", "192.168.0.0/16",  # private ranges
          "127.0.0.0/8"]:
    local_networks.append(ip_network(n, strict=False))
     
def is_local(mode: Trit, request: Request) -> Trit:
    """Check to see if this is a local client.  If mode is 'dontcare' then return
       'dontcare', otherwise return 'yes' if the mode matches the local client-ness
       and 'no' otherwise"""    
    if mode == Trit.DONTCARE:
        return mode  
    
    client: IPv4Address = get_client_ip(request)
    nets = [client in net for net in local_networks]    
    return test_trit(mode, any(nets))


def compile_rule(rule: Rule, debug: bool):
    """Build a function that's the representation of this rule so we don't
       have to do a bunch of checks on each request"""
    
    # compile everything
    if rule.pattern.startswith('~'):
        rule_re = re.compile(rule.pattern[1:], re.I)
    else:
        rule_re = re.compile('^' + re.escape(rule.pattern), re.I)

    if rule.with_query:
        pat_func = lambda request: rule_re.search(request.url.path + "?" + request.url.query)
    else:
        pat_func = lambda request: rule_re.search(request.url.path)

    # local, search_engine, crawler
    funcs = {}
    if rule.local != Trit.DONTCARE:
        funcs['local'] = lambda request: is_local(rule.local, request)        
    if rule.search_engine != Trit.DONTCARE:
        funcs['search_engine'] = lambda request: is_search(rule.search_engine, request)
    if rule.crawler != Trit.DONTCARE:
        funcs['crawler'] = lambda request: is_crawler(rule.crawler, request)

    if not debug:
        rfunc = list(funcs.values())
        rule._checkfunc = lambda request: rule.action if pat_func(request) and all([x(request) == Trit.YES for x in rfunc]) else Action.IGNORE
    else:
        def check_function(request):
            if rule.with_query:
                res = rule_re.search(request.url.path + "?" + request.url.query)
                logging.info(f"Check url {rule.pattern} with query is {res}: {request.url.path}?{request.url.query}")
            else:
                res = rule_re.search(request.url.path)
                logging.info(f"Check url {rule.pattern} is {res}: {request.url.path}")

            if res:
                res = []
                for k, v in funcs.items():
                    r = v(request)
                    res.append(r)
                    logging.info(f"Check {k}: {r}")
                if all([x == Trit.YES for x in res]):
                    logging.info(f"All tests were yes {res}, so using {rule.action}.")
                    return rule.action
                else:
                    logging.info(f"Some tests failed {res}: ignoring this check")
                    return Action.IGNORE
            else:
                return Action.IGNORE

        rule._checkfunc = check_function


def get_debug_id(request: Request):
    """Generate a debug ID that has all of the relevant information needed
       for debugging"""
    ip = get_client_ip(request)
    return f"{get_client_ip(request)}:{request.method}:{request.url}"