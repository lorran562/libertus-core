#!/usr/bin/env python3
"""
GHOST - Global Hostile OSINT Surface Tracker
Version: 1.0.0
Author: LIBERTUS
License: MIT

Autonomous web attack surface reconnaissance engine.
Zero heavy dependencies. Pure Python + requests.

Usage:
    python3 ghost.py --domain example.com
    python3 ghost.py --domain example.com --output report
    python3 ghost.py --domain example.com --deep --threads 10
"""

import argparse
import concurrent.futures
import datetime
import json
import os
import re
import socket
import sys
import time
import urllib.parse
from typing import Dict, List, Optional, Set, Tuple

try:
    import requests
    requests.packages.urllib3.disable_warnings()
except ImportError:
    print("[!] requests not found. Install with: pip install requests")
    sys.exit(1)


# ─────────────────────────────────────────────
#  CONSTANTS & CONFIG
# ─────────────────────────────────────────────

VERSION = "1.0.0"
BANNER = r"""
  ██████  ██   ██  ██████  ███████ ████████
 ██       ██   ██ ██    ██ ██         ██
 ██   ███ ███████ ██    ██ ███████    ██
 ██    ██ ██   ██ ██    ██      ██    ██
  ██████  ██   ██  ██████  ███████    ██

 Global Hostile OSINT Surface Tracker v{version}
 by LIBERTUS — Autonomous Recon Engine
""".format(version=VERSION)

TIMEOUT = 8
USER_AGENT = "Mozilla/5.0 (compatible; GHOST/{} OSINT Surface Tracker)".format(VERSION)

# DNS Brute-force wordlist (curated for max coverage, minimal noise)
DNS_WORDLIST = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "webmail", "email",
    "api", "api2", "apiv2", "v1", "v2", "v3", "rest", "graphql",
    "admin", "administrator", "panel", "dashboard", "cpanel", "whm",
    "dev", "development", "staging", "stage", "test", "testing", "qa",
    "beta", "alpha", "preview", "demo", "sandbox",
    "app", "apps", "portal", "web", "static", "cdn", "assets",
    "media", "img", "images", "files", "upload", "uploads",
    "blog", "shop", "store", "ecommerce", "pay", "payment", "billing",
    "auth", "login", "sso", "oauth", "id", "identity", "accounts",
    "help", "support", "ticket", "status", "monitor",
    "vpn", "remote", "rdp", "ssh", "git", "gitlab", "github", "bitbucket",
    "jenkins", "jira", "confluence", "wiki", "docs", "doc",
    "db", "database", "mysql", "pgsql", "redis", "mongo",
    "backup", "bkp", "old", "legacy", "archive", "repo",
    "internal", "intranet", "corp", "private",
    "mx", "mx1", "mx2", "ns", "ns1", "ns2", "dns",
    "mobile", "m", "wap", "pwa",
    "secure", "ssl", "tls",
    "proxy", "gateway", "lb", "loadbalancer",
    "server", "server1", "server2", "host", "host1",
    "cloud", "aws", "azure", "gcp",
    "autodiscover", "exchange", "owa",
]

# Sensitive paths to probe
SENSITIVE_PATHS = {
    "critical": [
        "/.env",
        "/.env.local",
        "/.env.production",
        "/.git/HEAD",
        "/.git/config",
        "/config.php",
        "/config.json",
        "/wp-config.php",
        "/web.config",
        "/database.yml",
        "/settings.py",
        "/application.yml",
        "/credentials.json",
        "/secrets.json",
        "/id_rsa",
        "/.ssh/id_rsa",
        "/private.key",
        "/server.key",
    ],
    "high": [
        "/admin",
        "/admin/",
        "/administrator",
        "/wp-admin/",
        "/wp-login.php",
        "/phpmyadmin/",
        "/pma/",
        "/adminer.php",
        "/_cpanel/",
        "/panel/",
        "/dashboard/",
        "/manager/",
        "/console/",
        "/jenkins/",
        "/jira/",
        "/grafana/",
        "/kibana/",
    ],
    "medium": [
        "/api/",
        "/api/v1/",
        "/api/v2/",
        "/v1/",
        "/v2/",
        "/swagger/",
        "/swagger-ui.html",
        "/swagger-ui/",
        "/api-docs/",
        "/openapi.json",
        "/graphql",
        "/graphiql",
        "/__graphql",
        "/rest/",
        "/xmlrpc.php",
    ],
    "info": [
        "/robots.txt",
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/.well-known/security.txt",
        "/humans.txt",
        "/crossdomain.xml",
        "/clientaccesspolicy.xml",
        "/server-status",
        "/server-info",
        "/.htaccess",
        "/phpinfo.php",
        "/info.php",
        "/test.php",
        "/backup.zip",
        "/backup.tar.gz",
        "/dump.sql",
        "/db.sql",
        "/.DS_Store",
        "/Thumbs.db",
    ],
}

# Subdomain takeover fingerprints: service -> CNAME patterns + response signatures
TAKEOVER_SIGNATURES = {
    "GitHub Pages": {
        "cname_patterns": ["github.io", "github.com"],
        "body_signatures": ["There isn't a GitHub Pages site here"],
        "risk": "HIGH",
    },
    "Heroku": {
        "cname_patterns": ["herokudns.com", "herokussl.com", "herokuapp.com"],
        "body_signatures": ["No such app", "herokuapp.com"],
        "risk": "HIGH",
    },
    "Netlify": {
        "cname_patterns": ["netlify.com", "netlify.app"],
        "body_signatures": ["Not Found - Request ID"],
        "risk": "HIGH",
    },
    "Vercel": {
        "cname_patterns": ["vercel.app", "now.sh"],
        "body_signatures": ["The deployment you are looking for", "DEPLOYMENT_NOT_FOUND"],
        "risk": "HIGH",
    },
    "AWS S3": {
        "cname_patterns": ["s3.amazonaws.com", "s3-website"],
        "body_signatures": ["NoSuchBucket", "The specified bucket does not exist"],
        "risk": "CRITICAL",
    },
    "Azure": {
        "cname_patterns": ["azurewebsites.net", "cloudapp.net", "blob.core.windows.net"],
        "body_signatures": ["404 Web Site not found"],
        "risk": "HIGH",
    },
    "Fastly": {
        "cname_patterns": ["fastly.net"],
        "body_signatures": ["Fastly error: unknown domain"],
        "risk": "MEDIUM",
    },
    "Shopify": {
        "cname_patterns": ["myshopify.com"],
        "body_signatures": ["Sorry, this shop is currently unavailable"],
        "risk": "MEDIUM",
    },
    "Tumblr": {
        "cname_patterns": ["tumblr.com"],
        "body_signatures": ["Whatever you were looking for doesn't currently exist at this address"],
        "risk": "MEDIUM",
    },
    "WPEngine": {
        "cname_patterns": ["wpengine.com"],
        "body_signatures": ["The site you were looking for couldn't be found"],
        "risk": "MEDIUM",
    },
    "Pantheon": {
        "cname_patterns": ["pantheonsite.io"],
        "body_signatures": ["404 error unknown site"],
        "risk": "MEDIUM",
    },
    "Ghost": {
        "cname_patterns": ["ghost.io"],
        "body_signatures": ["The thing you were looking for is no longer here"],
        "risk": "MEDIUM",
    },
    "Surge.sh": {
        "cname_patterns": ["surge.sh"],
        "body_signatures": ["project not found"],
        "risk": "MEDIUM",
    },
    "Unbounce": {
        "cname_patterns": ["unbouncepages.com"],
        "body_signatures": ["The requested URL was not found on this server"],
        "risk": "MEDIUM",
    },
    "HubSpot": {
        "cname_patterns": ["hubspot.com", "hubspotpagebuilder.com"],
        "body_signatures": ["This page isn't available"],
        "risk": "LOW",
    },
    "Zendesk": {
        "cname_patterns": ["zendesk.com"],
        "body_signatures": ["Help Center Closed", "is not a valid subdomain"],
        "risk": "LOW",
    },
    "Intercom": {
        "cname_patterns": ["intercom.io"],
        "body_signatures": ["Uh oh. That page doesn"],
        "risk": "LOW",
    },
    "Desk.com": {
        "cname_patterns": ["desk.com"],
        "body_signatures": ["Sorry, We Couldn"],
        "risk": "LOW",
    },
    "Webflow": {
        "cname_patterns": ["webflow.io"],
        "body_signatures": ["The page you are looking for doesn"],
        "risk": "LOW",
    },
}

# Technology/framework detection patterns
TECH_FINGERPRINTS = {
    "WordPress": {
        "headers": [],
        "body": ["wp-content/", "wp-includes/", "wordpress"],
        "cookies": ["wordpress_", "wp-settings-"],
        "meta": ["WordPress"],
    },
    "Drupal": {
        "headers": ["X-Generator: Drupal", "X-Drupal"],
        "body": ["Drupal.settings", "/sites/default/files/"],
        "cookies": ["SESS", "Drupal"],
        "meta": ["Drupal"],
    },
    "Joomla": {
        "headers": [],
        "body": ["/components/com_", "Joomla!"],
        "cookies": [],
        "meta": ["Joomla"],
    },
    "Laravel": {
        "headers": [],
        "body": [],
        "cookies": ["laravel_session", "XSRF-TOKEN"],
        "meta": [],
    },
    "Django": {
        "headers": [],
        "body": [],
        "cookies": ["csrftoken", "sessionid"],
        "meta": [],
    },
    "Ruby on Rails": {
        "headers": ["X-Runtime"],
        "body": [],
        "cookies": ["_session_id"],
        "meta": [],
    },
    "ASP.NET": {
        "headers": ["X-Powered-By: ASP.NET", "X-AspNet-Version"],
        "body": ["__VIEWSTATE", "__EVENTVALIDATION"],
        "cookies": ["ASP.NET_SessionId"],
        "meta": [],
    },
    "PHP": {
        "headers": ["X-Powered-By: PHP"],
        "body": [],
        "cookies": ["PHPSESSID"],
        "meta": [],
    },
    "Node.js": {
        "headers": ["X-Powered-By: Express"],
        "body": [],
        "cookies": ["connect.sid"],
        "meta": [],
    },
    "React": {
        "headers": [],
        "body": ["react", "__NEXT_DATA__", "next/static"],
        "cookies": [],
        "meta": [],
    },
    "Angular": {
        "headers": [],
        "body": ["ng-version=", "angular.js", "ng-app"],
        "cookies": [],
        "meta": [],
    },
    "Vue.js": {
        "headers": [],
        "body": ["vue.js", "vue.min.js", "__vue__"],
        "cookies": [],
        "meta": [],
    },
    "jQuery": {
        "headers": [],
        "body": ["jquery.min.js", "jquery-", "/jquery/"],
        "cookies": [],
        "meta": [],
    },
    "Bootstrap": {
        "headers": [],
        "body": ["bootstrap.min.css", "bootstrap.css", "bootstrap.min.js"],
        "cookies": [],
        "meta": [],
    },
    "Nginx": {
        "headers": ["Server: nginx"],
        "body": ["nginx"],
        "cookies": [],
        "meta": [],
    },
    "Apache": {
        "headers": ["Server: Apache"],
        "body": [],
        "cookies": [],
        "meta": [],
    },
    "IIS": {
        "headers": ["Server: Microsoft-IIS", "X-Powered-By: ASP.NET"],
        "body": [],
        "cookies": [],
        "meta": [],
    },
    "Cloudflare": {
        "headers": ["CF-Ray", "cf-cache-status"],
        "body": [],
        "cookies": ["__cfduid", "__cf_bm"],
        "meta": [],
    },
    "AWS CloudFront": {
        "headers": ["X-Amz-Cf-Id", "Via: CloudFront"],
        "body": [],
        "cookies": [],
        "meta": [],
    },
    "Varnish": {
        "headers": ["X-Varnish", "Via: varnish"],
        "body": [],
        "cookies": [],
        "meta": [],
    },
    "GraphQL": {
        "headers": [],
        "body": ["__schema", "graphql", "GraphQL"],
        "cookies": [],
        "meta": [],
    },
    "Swagger/OpenAPI": {
        "headers": [],
        "body": ["swagger-ui", "swaggerUi", "Swagger UI", "openapi"],
        "cookies": [],
        "meta": [],
    },
}

# CVE correlation: tech/version patterns -> known critical CVEs
CVE_SIGNATURES = {
    "WordPress 4.": {"cves": ["CVE-2019-8942", "CVE-2018-20152"], "severity": "HIGH"},
    "WordPress 5.0": {"cves": ["CVE-2019-8942"], "severity": "HIGH"},
    "WordPress 5.1": {"cves": ["CVE-2019-9787"], "severity": "HIGH"},
    "WordPress 5.2": {"cves": ["CVE-2019-16218"], "severity": "MEDIUM"},
    "WordPress 5.6": {"cves": ["CVE-2021-29447"], "severity": "HIGH"},
    "PHP/5.": {"cves": ["CVE-2019-11043", "CVE-2018-19518", "CVE-2019-9641"], "severity": "CRITICAL"},
    "PHP/7.0": {"cves": ["CVE-2019-11043"], "severity": "CRITICAL"},
    "PHP/7.1": {"cves": ["CVE-2019-11043"], "severity": "CRITICAL"},
    "PHP/7.2": {"cves": ["CVE-2019-11043"], "severity": "CRITICAL"},
    "Apache/2.2": {"cves": ["CVE-2017-7679", "CVE-2017-9798"], "severity": "CRITICAL"},
    "Apache/2.4.4": {"cves": ["CVE-2021-41773", "CVE-2021-42013"], "severity": "CRITICAL"},
    "Apache/2.4.49": {"cves": ["CVE-2021-41773"], "severity": "CRITICAL"},
    "nginx/1.1": {"cves": ["CVE-2013-2028"], "severity": "HIGH"},
    "nginx/1.0": {"cves": ["CVE-2013-2028"], "severity": "HIGH"},
    "OpenSSL/1.0": {"cves": ["CVE-2014-0160", "CVE-2016-2107"], "severity": "CRITICAL"},
    "OpenSSL/1.1.0": {"cves": ["CVE-2019-1559"], "severity": "MEDIUM"},
    "ASP.NET MVC 3.": {"cves": ["CVE-2021-31204"], "severity": "MEDIUM"},
    "Joomla! 3.": {"cves": ["CVE-2023-23752"], "severity": "CRITICAL"},
    "Drupal 7.": {"cves": ["CVE-2018-7600", "CVE-2019-6340"], "severity": "CRITICAL"},
    "Drupal 8.": {"cves": ["CVE-2019-6340", "CVE-2020-13671"], "severity": "HIGH"},
}

# Score weights per finding type
SCORE_WEIGHTS = {
    # Infrastructure
    "subdomain_active": 2,
    "subdomain_dead_takeover": 25,
    "open_port_admin": 15,
    # Credentials / Secrets
    "env_file_exposed": 50,
    "git_exposed": 45,
    "config_exposed": 40,
    "private_key_exposed": 50,
    "api_key_in_response": 45,
    # Abandoned assets
    "bucket_exposed": 35,
    "takeover_vulnerable": 30,
    "admin_panel_exposed": 25,
    "swagger_exposed": 20,
    "graphql_exposed": 15,
    # Versions/CVEs
    "cve_critical": 30,
    "cve_high": 20,
    "cve_medium": 10,
    "version_in_header": 10,
    # Info disclosure
    "sensitive_file": 15,
    "server_header": 5,
    "directory_listing": 20,
    "phpinfo": 30,
    "debug_mode": 25,
}


# ─────────────────────────────────────────────
#  UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def banner():
    print(BANNER)


def log(msg, level="INFO", color=True):
    colors = {
        "INFO":    "\033[94m",   # blue
        "OK":      "\033[92m",   # green
        "WARN":    "\033[93m",   # yellow
        "ERROR":   "\033[91m",   # red
        "CRITICAL":"\033[95m",   # magenta
        "FIND":    "\033[96m",   # cyan
        "SECTION": "\033[1;97m", # bold white
    }
    reset = "\033[0m"
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    prefix = colors.get(level, "") if color else ""
    suffix = reset if color else ""

    symbols = {
        "INFO": "[*]",
        "OK": "[+]",
        "WARN": "[!]",
        "ERROR": "[-]",
        "CRITICAL": "[!!]",
        "FIND": "[>]",
        "SECTION": "\n[===]",
    }
    sym = symbols.get(level, "[*]")
    print(f"{prefix}{sym} {ts} {msg}{suffix}")


def http_get(url, timeout=TIMEOUT, follow_redirects=True, retries=2):
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(retries):
        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                verify=False,
                allow_redirects=follow_redirects,
            )
            return resp
        except requests.exceptions.SSLError:
            try:
                resp = requests.get(
                    url.replace("https://", "http://"),
                    headers=headers,
                    timeout=timeout,
                    verify=False,
                    allow_redirects=follow_redirects,
                )
                return resp
            except Exception:
                return None
        except requests.exceptions.ConnectionError:
            return None
        except requests.exceptions.Timeout:
            return None
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(0.5)
    return None


def dns_resolve(hostname):
    try:
        results = socket.getaddrinfo(hostname, None)
        ips = list(set([r[4][0] for r in results]))
        return ips
    except socket.gaierror:
        return []
    except Exception:
        return []


def dns_cname(hostname):
    """Try to get CNAME via dig or fallback."""
    try:
        import subprocess
        result = subprocess.run(
            ["dig", "+short", "CNAME", hostname],
            capture_output=True, text=True, timeout=5
        )
        cname = result.stdout.strip().rstrip(".")
        return cname if cname else None
    except Exception:
        return None


def extract_title(html):
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()[:120]
    return None


def extract_meta_generator(html):
    match = re.search(
        r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    match = re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']generator["\']',
        html, re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return None


def clean_domain(domain):
    domain = domain.lower().strip()
    domain = re.sub(r"^https?://", "", domain)
    domain = re.sub(r"/.*$", "", domain)
    domain = domain.lstrip("*").lstrip(".")
    return domain


def is_valid_subdomain(subdomain, base_domain):
    subdomain = subdomain.lower().strip()
    if not subdomain.endswith(base_domain):
        return False
    if subdomain == base_domain:
        return False
    return True


# ─────────────────────────────────────────────
#  MODULE 1: SURFACE EXPANSION
# ─────────────────────────────────────────────

class SurfaceExpander:
    def __init__(self, domain: str, threads: int = 10):
        self.domain = domain
        self.threads = threads
        self.subdomains: Set[str] = set()
        self.ct_subdomains: Set[str] = set()
        self.wayback_urls: List[str] = []
        self.dns_found: Set[str] = set()

    def expand(self) -> Dict:
        log("Starting surface expansion...", "SECTION")

        ct = self._crtsh_lookup()
        dns = self._dns_bruteforce()
        wayback = self._wayback_lookup()

        all_subs = ct.union(dns)
        log(f"Total unique subdomains found: {len(all_subs)}", "OK")

        return {
            "ct_subdomains": sorted(list(ct)),
            "dns_bruteforce": sorted(list(dns)),
            "wayback_urls": wayback[:200],  # cap at 200
            "all_subdomains": sorted(list(all_subs)),
        }

    def _crtsh_lookup(self) -> Set[str]:
        log(f"Querying Certificate Transparency (crt.sh) for {self.domain}...", "INFO")
        found = set()
        try:
            url = f"https://crt.sh/?q=%.{self.domain}&output=json"
            resp = http_get(url, timeout=15)
            if not resp or resp.status_code != 200:
                log("crt.sh query failed or no results", "WARN")
                return found
            data = resp.json()
            for entry in data:
                name = entry.get("name_value", "")
                for sub in name.split("\n"):
                    sub = clean_domain(sub)
                    if is_valid_subdomain(sub, self.domain):
                        found.add(sub)
            log(f"CT logs: {len(found)} subdomains discovered", "OK")
        except Exception as e:
            log(f"crt.sh error: {e}", "WARN")
        self.ct_subdomains = found
        return found

    def _dns_bruteforce(self) -> Set[str]:
        log(f"DNS brute-force ({len(DNS_WORDLIST)} words, {self.threads} threads)...", "INFO")
        found = set()

        def check_sub(word):
            fqdn = f"{word}.{self.domain}"
            ips = dns_resolve(fqdn)
            if ips:
                return fqdn
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as ex:
            futures = {ex.submit(check_sub, w): w for w in DNS_WORDLIST}
            for f in concurrent.futures.as_completed(futures):
                result = f.result()
                if result:
                    found.add(result)

        log(f"DNS brute-force: {len(found)} subdomains resolved", "OK")
        self.dns_found = found
        return found

    def _wayback_lookup(self) -> List[str]:
        log(f"Querying Wayback Machine for historical URLs of {self.domain}...", "INFO")
        urls = []
        try:
            api_url = (
                f"http://web.archive.org/cdx/search/cdx"
                f"?url=*.{self.domain}/*&output=json&fl=original&collapse=urlkey&limit=500"
            )
            resp = http_get(api_url, timeout=20)
            if resp and resp.status_code == 200:
                data = resp.json()
                for row in data[1:]:  # skip header
                    if row:
                        urls.append(row[0])
                log(f"Wayback Machine: {len(urls)} historical URLs found", "OK")
            else:
                log("Wayback Machine query returned no results", "WARN")
        except Exception as e:
            log(f"Wayback Machine error: {e}", "WARN")
        self.wayback_urls = urls
        return urls


# ─────────────────────────────────────────────
#  MODULE 2: FINGERPRINTING ENGINE
# ─────────────────────────────────────────────

class FingerprintEngine:
    def __init__(self, threads: int = 10):
        self.threads = threads

    def fingerprint_all(self, subdomains: List[str]) -> Dict:
        log(f"Fingerprinting {len(subdomains)} hosts ({self.threads} threads)...", "SECTION")
        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as ex:
            futures = {ex.submit(self.fingerprint_host, sub): sub for sub in subdomains}
            for f in concurrent.futures.as_completed(futures):
                sub = futures[f]
                try:
                    result = f.result()
                    if result:
                        results[sub] = result
                        status = result.get("status_code", "?")
                        title = result.get("title", "")[:50]
                        tech = ", ".join(result.get("technologies", [])[:3])
                        log(f"{sub} [{status}] {title} | {tech}", "FIND")
                except Exception as e:
                    pass

        return results

    def fingerprint_host(self, hostname: str) -> Optional[Dict]:
        ips = dns_resolve(hostname)
        if not ips:
            return None

        result = {
            "hostname": hostname,
            "ips": ips,
            "alive": False,
            "status_code": None,
            "title": None,
            "technologies": [],
            "headers": {},
            "cookies": [],
            "server": None,
            "cve_matches": [],
            "cname": None,
        }

        cname = dns_cname(hostname)
        if cname:
            result["cname"] = cname

        for scheme in ["https", "http"]:
            url = f"{scheme}://{hostname}"
            resp = http_get(url, timeout=TIMEOUT)
            if resp is not None:
                result["alive"] = True
                result["status_code"] = resp.status_code
                result["final_url"] = resp.url

                # Headers (filtered)
                interesting_headers = [
                    "Server", "X-Powered-By", "X-Generator", "X-Framework",
                    "X-AspNet-Version", "X-Runtime", "Via", "CF-Ray",
                    "X-Amz-Cf-Id", "X-Varnish",
                ]
                for h in interesting_headers:
                    val = resp.headers.get(h)
                    if val:
                        result["headers"][h] = val

                result["server"] = resp.headers.get("Server", "")

                # Cookies
                for cookie in resp.cookies:
                    result["cookies"].append(cookie.name)

                # Body analysis
                try:
                    html = resp.text
                    result["title"] = extract_title(html)
                    result["meta_generator"] = extract_meta_generator(html)
                    result["technologies"] = self._detect_technologies(
                        resp.headers, html, list(resp.cookies)
                    )
                    result["cve_matches"] = self._check_cves(resp.headers, html)
                except Exception:
                    pass

                break

        return result

    def _detect_technologies(self, headers, body, cookies) -> List[str]:
        detected = []
        header_str = " ".join([f"{k}: {v}" for k, v in headers.items()])
        cookie_names = [c for c in cookies] if cookies else []

        for tech, sigs in TECH_FINGERPRINTS.items():
            matched = False
            for h_sig in sigs.get("headers", []):
                if h_sig.lower() in header_str.lower():
                    matched = True
                    break
            if not matched:
                for b_sig in sigs.get("body", []):
                    if b_sig.lower() in body.lower():
                        matched = True
                        break
            if not matched:
                for c_sig in sigs.get("cookies", []):
                    for cookie in cookie_names:
                        if c_sig.lower() in cookie.lower():
                            matched = True
                            break

            if matched:
                detected.append(tech)

        return detected

    def _check_cves(self, headers, body) -> List[Dict]:
        matches = []
        header_str = " ".join([f"{k}: {v}" for k, v in headers.items()])
        combined = header_str + " " + body[:5000]

        for pattern, cve_data in CVE_SIGNATURES.items():
            if pattern.lower() in combined.lower():
                matches.append({
                    "pattern": pattern,
                    "cves": cve_data["cves"],
                    "severity": cve_data["severity"],
                })

        return matches


# ─────────────────────────────────────────────
#  MODULE 3: ABANDONED ASSET DETECTOR
# ─────────────────────────────────────────────

class AbandonedAssetDetector:
    def __init__(self, threads: int = 8):
        self.threads = threads
        self.findings: List[Dict] = []

    def detect(self, fingerprint_results: Dict, all_subdomains: List[str]) -> List[Dict]:
        log("Scanning for abandoned assets and vulnerabilities...", "SECTION")

        # Check subdomain takeover candidates
        self._check_takeovers(fingerprint_results, all_subdomains)

        # Check sensitive paths on alive hosts
        alive_hosts = {
            sub: data for sub, data in fingerprint_results.items()
            if data and data.get("alive")
        }
        self._check_sensitive_paths(alive_hosts)

        # Check cloud storage exposure
        self._check_cloud_buckets(fingerprint_results)

        log(f"Asset detection complete: {len(self.findings)} findings", "OK")
        return self.findings

    def _check_takeovers(self, fingerprint_results, all_subdomains):
        log("Checking subdomain takeover candidates...", "INFO")

        # Subdomains in CT but not resolving
        for sub in all_subdomains:
            ips = dns_resolve(sub)
            if not ips:
                # Dead subdomain — potential takeover if had CNAME
                cname = dns_cname(sub)
                if cname:
                    for service, sigs in TAKEOVER_SIGNATURES.items():
                        for pattern in sigs["cname_patterns"]:
                            if pattern in cname:
                                self.findings.append({
                                    "type": "subdomain_takeover_candidate",
                                    "severity": sigs["risk"],
                                    "host": sub,
                                    "cname": cname,
                                    "service": service,
                                    "description": (
                                        f"{sub} has CNAME -> {cname} ({service}) "
                                        f"but does not resolve. Possible takeover."
                                    ),
                                    "score_impact": SCORE_WEIGHTS["takeover_vulnerable"],
                                })
                                log(f"TAKEOVER CANDIDATE: {sub} -> {cname} ({service})", "CRITICAL")

        # Alive hosts with takeover signatures in body
        for sub, data in fingerprint_results.items():
            if not data or not data.get("alive"):
                continue
            cname = data.get("cname", "")
            if not cname:
                continue
            for service, sigs in TAKEOVER_SIGNATURES.items():
                for pattern in sigs["cname_patterns"]:
                    if pattern in (cname or ""):
                        # Has CNAME to known service — check body for error signature
                        url = f"https://{sub}"
                        resp = http_get(url)
                        if resp:
                            body = resp.text.lower()
                            for body_sig in sigs["body_signatures"]:
                                if body_sig.lower() in body:
                                    self.findings.append({
                                        "type": "subdomain_takeover_confirmed",
                                        "severity": "CRITICAL",
                                        "host": sub,
                                        "cname": cname,
                                        "service": service,
                                        "description": (
                                            f"CONFIRMED takeover: {sub} -> {cname} "
                                            f"shows '{body_sig}'"
                                        ),
                                        "score_impact": SCORE_WEIGHTS["subdomain_dead_takeover"],
                                    })
                                    log(f"CONFIRMED TAKEOVER: {sub} [{service}]", "CRITICAL")

    def _check_sensitive_paths(self, alive_hosts: Dict):
        log(f"Probing sensitive paths on {len(alive_hosts)} alive hosts...", "INFO")

        def probe_host_paths(hostname_data):
            hostname, data = hostname_data
            host_findings = []
            base_url = data.get("final_url", f"https://{hostname}").rstrip("/")
            # Normalize to origin
            parsed = urllib.parse.urlparse(base_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            for severity, paths in SENSITIVE_PATHS.items():
                for path in paths:
                    url = base_url + path
                    resp = http_get(url, follow_redirects=False)
                    if resp is None:
                        continue

                    # We consider 200 or 403 (exists but forbidden) as interesting
                    if resp.status_code in [200, 206]:
                        body_preview = resp.text[:500] if resp.text else ""
                        finding_type = self._classify_sensitive_path(path, body_preview)

                        # Additional validation: check it's not a generic 200
                        content_length = len(resp.content)
                        if content_length < 10:
                            continue

                        host_findings.append({
                            "type": finding_type,
                            "severity": severity.upper(),
                            "host": hostname,
                            "url": url,
                            "status_code": resp.status_code,
                            "content_length": content_length,
                            "preview": body_preview[:200],
                            "description": f"Sensitive path exposed: {path}",
                            "score_impact": SCORE_WEIGHTS.get(finding_type, SCORE_WEIGHTS["sensitive_file"]),
                        })
                        log(f"EXPOSED: {url} [{resp.status_code}] ({content_length} bytes)", "FIND")

                    elif resp.status_code == 403:
                        # Forbidden but exists — lower severity
                        if severity == "critical":
                            host_findings.append({
                                "type": "path_forbidden",
                                "severity": "MEDIUM",
                                "host": hostname,
                                "url": url,
                                "status_code": 403,
                                "description": f"Path exists but forbidden: {path}",
                                "score_impact": 5,
                            })

            return host_findings

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as ex:
            futures = [ex.submit(probe_host_paths, item) for item in alive_hosts.items()]
            for f in concurrent.futures.as_completed(futures):
                try:
                    findings = f.result()
                    self.findings.extend(findings)
                except Exception:
                    pass

    def _classify_sensitive_path(self, path: str, body: str) -> str:
        path_lower = path.lower()
        body_lower = body.lower()

        if ".env" in path_lower:
            if any(k in body_lower for k in ["api_key", "secret", "password", "token", "db_"]):
                return "env_file_exposed"
            return "sensitive_file"
        elif ".git" in path_lower:
            if "ref:" in body_lower or "object" in body_lower:
                return "git_exposed"
            return "sensitive_file"
        elif "config" in path_lower or "settings" in path_lower:
            return "config_exposed"
        elif "id_rsa" in path_lower or "private.key" in path_lower:
            return "private_key_exposed"
        elif "phpinfo" in path_lower or ("phpinfo" in body_lower and "php version" in body_lower):
            return "phpinfo"
        elif path_lower in ["/admin", "/admin/", "/administrator", "/wp-admin/", "/panel/"]:
            return "admin_panel_exposed"
        elif "swagger" in path_lower or "api-docs" in path_lower or "openapi" in path_lower:
            return "swagger_exposed"
        elif "graphql" in path_lower:
            return "graphql_exposed"
        else:
            return "sensitive_file"

    def _check_cloud_buckets(self, fingerprint_results: Dict):
        log("Checking cloud storage exposure via CNAME resolution...", "INFO")
        for hostname, data in fingerprint_results.items():
            if not data:
                continue
            cname = data.get("cname", "") or ""
            ips = data.get("ips", [])

            bucket_patterns = {
                "S3": ["s3.amazonaws.com", "s3-website"],
                "GCS": ["storage.googleapis.com"],
                "Azure Blob": ["blob.core.windows.net"],
                "DigitalOcean Spaces": ["digitaloceanspaces.com"],
                "Backblaze B2": ["backblazeb2.com"],
            }

            for provider, patterns in bucket_patterns.items():
                for pattern in patterns:
                    if pattern in cname:
                        resp = http_get(f"https://{hostname}")
                        if resp:
                            body = resp.text
                            if resp.status_code == 200 and (
                                "ListBucketResult" in body or
                                "Contents" in body or
                                "<Key>" in body
                            ):
                                self.findings.append({
                                    "type": "bucket_exposed",
                                    "severity": "CRITICAL",
                                    "host": hostname,
                                    "provider": provider,
                                    "cname": cname,
                                    "description": f"Cloud storage bucket is publicly listed: {provider}",
                                    "score_impact": SCORE_WEIGHTS["bucket_exposed"],
                                })
                                log(f"BUCKET EXPOSED: {hostname} ({provider})", "CRITICAL")
                            elif resp.status_code in [403]:
                                # Exists but private — note it
                                self.findings.append({
                                    "type": "bucket_private",
                                    "severity": "LOW",
                                    "host": hostname,
                                    "provider": provider,
                                    "description": f"Cloud storage bucket exists but private: {provider}",
                                    "score_impact": 2,
                                })


# ─────────────────────────────────────────────
#  MODULE 4: EXPOSURE SCORER
# ─────────────────────────────────────────────

class ExposureScorer:
    def __init__(self):
        self.categories = {
            "infrastructure": 0,
            "credentials": 0,
            "abandoned_assets": 0,
            "vulnerable_versions": 0,
            "information_disclosure": 0,
        }

    def calculate(
        self,
        fingerprint_results: Dict,
        findings: List[Dict],
        surface_data: Dict,
    ) -> Dict:
        log("Calculating exposure score...", "SECTION")

        raw_score = 0
        category_scores = dict(self.categories)

        # Score from findings
        for f in findings:
            impact = f.get("score_impact", 5)
            severity = f.get("severity", "LOW")
            ftype = f.get("type", "")

            raw_score += impact

            if ftype in ["env_file_exposed", "git_exposed", "config_exposed",
                         "private_key_exposed", "api_key_in_response"]:
                category_scores["credentials"] += impact
            elif ftype in ["takeover_vulnerable", "subdomain_takeover_candidate",
                           "subdomain_takeover_confirmed", "bucket_exposed", "admin_panel_exposed"]:
                category_scores["abandoned_assets"] += impact
            elif ftype in ["sensitive_file", "phpinfo", "swagger_exposed",
                           "graphql_exposed", "path_forbidden"]:
                category_scores["information_disclosure"] += impact
            else:
                category_scores["infrastructure"] += impact

        # Score from fingerprint data (CVEs, version exposure)
        for hostname, data in fingerprint_results.items():
            if not data or not data.get("alive"):
                continue

            # Version in headers = information disclosure
            server = data.get("server", "") or ""
            if re.search(r"\d+\.\d+", server):
                raw_score += SCORE_WEIGHTS["version_in_header"]
                category_scores["information_disclosure"] += SCORE_WEIGHTS["version_in_header"]

            x_powered = data.get("headers", {}).get("X-Powered-By", "") or ""
            if re.search(r"\d+\.\d+", x_powered):
                raw_score += SCORE_WEIGHTS["version_in_header"]
                category_scores["information_disclosure"] += SCORE_WEIGHTS["version_in_header"]

            # CVE matches
            for cve_match in data.get("cve_matches", []):
                sev = cve_match["severity"]
                if sev == "CRITICAL":
                    impact = SCORE_WEIGHTS["cve_critical"]
                elif sev == "HIGH":
                    impact = SCORE_WEIGHTS["cve_high"]
                else:
                    impact = SCORE_WEIGHTS["cve_medium"]
                raw_score += impact
                category_scores["vulnerable_versions"] += impact

        # Surface score: more exposed subdomains = higher base risk
        alive_count = sum(
            1 for d in fingerprint_results.values()
            if d and d.get("alive")
        )
        raw_score += alive_count * SCORE_WEIGHTS["subdomain_active"]
        category_scores["infrastructure"] += alive_count * SCORE_WEIGHTS["subdomain_active"]

        # Normalize to 0-100
        final_score = min(100, raw_score)

        risk_level = (
            "CRITICAL" if final_score >= 80 else
            "HIGH" if final_score >= 60 else
            "MEDIUM" if final_score >= 40 else
            "LOW" if final_score >= 20 else
            "MINIMAL"
        )

        # Normalize category scores to 100
        for cat in category_scores:
            category_scores[cat] = min(100, category_scores[cat])

        score_data = {
            "total": final_score,
            "risk_level": risk_level,
            "raw_score": raw_score,
            "breakdown": category_scores,
            "alive_subdomains": alive_count,
            "total_subdomains": len(surface_data.get("all_subdomains", [])),
            "total_findings": len(findings),
            "critical_findings": sum(1 for f in findings if f.get("severity") == "CRITICAL"),
            "high_findings": sum(1 for f in findings if f.get("severity") == "HIGH"),
            "medium_findings": sum(1 for f in findings if f.get("severity") == "MEDIUM"),
            "low_findings": sum(1 for f in findings if f.get("severity") == "LOW"),
        }

        color = "\033[91m" if risk_level in ["CRITICAL", "HIGH"] else "\033[93m" if risk_level == "MEDIUM" else "\033[92m"
        reset = "\033[0m"
        log(f"EXPOSURE SCORE: {color}{final_score}/100 [{risk_level}]{reset}", "OK")
        log(f"Breakdown: " + " | ".join([f"{k}: {v}" for k, v in category_scores.items()]), "INFO")

        return score_data


# ─────────────────────────────────────────────
#  MODULE 5: REPORT GENERATOR
# ─────────────────────────────────────────────

class ReportGenerator:
    def __init__(self, domain: str, output_prefix: str = None):
        self.domain = domain
        self.timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        self.output_prefix = output_prefix or f"ghost_{domain}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def generate(
        self,
        surface_data: Dict,
        fingerprint_results: Dict,
        findings: List[Dict],
        score: Dict,
    ) -> Tuple[str, str]:
        report_data = {
            "meta": {
                "tool": "GHOST - Global Hostile OSINT Surface Tracker",
                "version": VERSION,
                "domain": self.domain,
                "scan_time": self.timestamp,
                "by": "LIBERTUS",
            },
            "score": score,
            "surface": {
                "ct_subdomains_count": len(surface_data.get("ct_subdomains", [])),
                "dns_bruteforce_count": len(surface_data.get("dns_bruteforce", [])),
                "total_subdomains": len(surface_data.get("all_subdomains", [])),
                "wayback_urls_count": len(surface_data.get("wayback_urls", [])),
                "all_subdomains": surface_data.get("all_subdomains", []),
                "wayback_sample": surface_data.get("wayback_urls", [])[:20],
            },
            "fingerprints": {
                host: {
                    k: v for k, v in data.items()
                    if k not in ["cookies"]
                }
                for host, data in fingerprint_results.items()
                if data and data.get("alive")
            },
            "findings": sorted(findings, key=lambda x: {
                "CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3
            }.get(x.get("severity", "LOW"), 4)),
        }

        # JSON report
        json_path = self.output_prefix + ".json"
        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        log(f"JSON report saved: {json_path}", "OK")

        # Markdown report
        md_path = self.output_prefix + ".md"
        md = self._build_markdown(report_data)
        with open(md_path, "w") as f:
            f.write(md)
        log(f"Markdown report saved: {md_path}", "OK")

        return json_path, md_path

    def _build_markdown(self, data: Dict) -> str:
        d = data
        score = d["score"]
        surface = d["surface"]
        findings = d["findings"]
        meta = d["meta"]

        risk_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "MINIMAL": "⚪",
        }.get(score["risk_level"], "⚪")

        lines = [
            "# GHOST Attack Surface Report",
            "",
            f"**Target:** `{meta['domain']}`  ",
            f"**Scan Date:** {meta['scan_time']}  ",
            f"**Tool:** {meta['tool']} v{meta['version']}  ",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| **Exposure Score** | {risk_emoji} **{score['total']}/100** [{score['risk_level']}] |",
            f"| Total Subdomains Found | {surface['total_subdomains']} |",
            f"| Alive Hosts | {score['alive_subdomains']} |",
            f"| Historical URLs (Wayback) | {surface['wayback_urls_count']} |",
            f"| Total Findings | {score['total_findings']} |",
            f"| Critical | 🔴 {score['critical_findings']} |",
            f"| High | 🟠 {score['high_findings']} |",
            f"| Medium | 🟡 {score['medium_findings']} |",
            f"| Low | 🟢 {score['low_findings']} |",
            "",
            "## Risk Breakdown",
            "",
            "| Category | Score |",
            "|----------|-------|",
        ]

        for cat, val in score["breakdown"].items():
            bar = "█" * (val // 10) + "░" * (10 - val // 10)
            lines.append(f"| {cat.replace('_', ' ').title()} | {bar} {val}/100 |")

        lines += [
            "",
            "---",
            "",
            "## Critical Findings",
            "",
        ]

        critical_findings = [f for f in findings if f.get("severity") in ["CRITICAL", "HIGH"]]
        if critical_findings:
            for i, f in enumerate(critical_findings, 1):
                sev = f.get("severity", "?")
                icon = "🔴" if sev == "CRITICAL" else "🟠"
                lines.append(f"### {i}. {icon} [{sev}] {f.get('type', '').replace('_', ' ').upper()}")
                lines.append("")
                lines.append(f"- **Host:** `{f.get('host', 'N/A')}`")
                if f.get("url"):
                    lines.append(f"- **URL:** `{f.get('url')}`")
                if f.get("cname"):
                    lines.append(f"- **CNAME:** `{f.get('cname')}`")
                if f.get("service"):
                    lines.append(f"- **Service:** {f.get('service')}")
                lines.append(f"- **Description:** {f.get('description', '')}")
                if f.get("preview"):
                    lines.append(f"- **Preview:** ```{f.get('preview')[:150]}```")
                lines.append("")
        else:
            lines.append("No critical/high findings. Good posture!")
            lines.append("")

        # All other findings
        other = [f for f in findings if f.get("severity") in ["MEDIUM", "LOW"]]
        if other:
            lines += ["---", "", "## Other Findings", ""]
            lines.append("| Severity | Type | Host | URL |")
            lines.append("|----------|------|------|-----|")
            for f in other:
                sev = f.get("severity", "?")
                icon = "🟡" if sev == "MEDIUM" else "🟢"
                ftype = f.get("type", "").replace("_", " ")
                host = f.get("host", "-")
                url = f.get("url", "-")
                lines.append(f"| {icon} {sev} | {ftype} | `{host}` | `{url}` |")
            lines.append("")

        # Alive hosts
        lines += ["---", "", "## Discovered Attack Surface", "", "### Alive Hosts", ""]
        lines.append("| Host | IP | Status | Server | Technologies |")
        lines.append("|------|----|--------|--------|--------------|")

        for host, fp in d["fingerprints"].items():
            ips = ", ".join(fp.get("ips", [])[:2])
            status = fp.get("status_code", "-")
            server = fp.get("server", "-") or "-"
            techs = ", ".join(fp.get("technologies", [])[:4]) or "-"
            lines.append(f"| `{host}` | {ips} | {status} | {server} | {techs} |")

        lines.append("")

        # CVE Matches
        cve_hosts = {
            h: d for h, d in d["fingerprints"].items()
            if d.get("cve_matches")
        }
        if cve_hosts:
            lines += ["---", "", "## CVE Correlation", ""]
            for host, fp in cve_hosts.items():
                lines.append(f"### `{host}`")
                for cve_match in fp["cve_matches"]:
                    lines.append(f"- Pattern: `{cve_match['pattern']}`")
                    lines.append(f"  - Severity: **{cve_match['severity']}**")
                    lines.append(f"  - CVEs: {', '.join(cve_match['cves'])}")
                lines.append("")

        # Subdomains
        lines += ["---", "", "## All Discovered Subdomains", ""]
        for sub in surface["all_subdomains"]:
            lines.append(f"- `{sub}`")
        lines.append("")

        # Wayback sample
        if surface["wayback_sample"]:
            lines += ["---", "", "## Historical URLs Sample (Wayback Machine)", ""]
            for url in surface["wayback_sample"][:15]:
                lines.append(f"- {url}")
            lines.append("")
            if surface["wayback_urls_count"] > 15:
                lines.append(f"*...and {surface['wayback_urls_count'] - 15} more in JSON report*")
                lines.append("")

        lines += [
            "---",
            "",
            "## Remediation Recommendations",
            "",
            "1. **Subdomain Takeovers:** Remove dangling DNS records pointing to decommissioned services",
            "2. **Exposed Secrets:** Rotate all credentials found in exposed files immediately",
            "3. **Admin Panels:** Restrict access via IP allowlist + MFA",
            "4. **API Endpoints:** Implement authentication on all public API paths",
            "5. **Version Headers:** Remove or obfuscate Server/X-Powered-By headers",
            "6. **Cloud Storage:** Audit bucket ACLs and disable public listing",
            "7. **CVEs:** Update software versions to eliminate known vulnerabilities",
            "",
            "---",
            "",
            f"*Report generated by GHOST v{VERSION} | LIBERTUS*",
            "",
        ]

        return "\n".join(lines)


# ─────────────────────────────────────────────
#  MAIN ORCHESTRATOR
# ─────────────────────────────────────────────

class GhostScanner:
    def __init__(self, domain: str, output: str = None, threads: int = 10, deep: bool = False):
        self.domain = clean_domain(domain)
        self.output = output
        self.threads = threads
        self.deep = deep
        self.start_time = time.time()

    def run(self):
        banner()
        log(f"Target: {self.domain}", "SECTION")
        log(f"Threads: {self.threads} | Deep: {self.deep}", "INFO")
        log("This is passive reconnaissance. Minimal footprint.", "INFO")
        print()

        # Phase 1: Surface expansion
        expander = SurfaceExpander(self.domain, threads=self.threads)
        surface_data = expander.expand()

        all_subs = surface_data["all_subdomains"]
        if not all_subs:
            log("No subdomains found. Proceeding with root domain only.", "WARN")
            all_subs = [self.domain]

        # Add root domain
        if self.domain not in all_subs:
            all_subs = [self.domain] + all_subs

        # Phase 2: Fingerprinting
        fp_engine = FingerprintEngine(threads=self.threads)
        fingerprint_results = fp_engine.fingerprint_all(all_subs)

        # Phase 3: Abandoned asset detection
        detector = AbandonedAssetDetector(threads=self.threads)
        findings = detector.detect(fingerprint_results, all_subs)

        # Add fingerprint CVE findings to main findings list
        for hostname, data in fingerprint_results.items():
            if not data:
                continue
            for cve_match in data.get("cve_matches", []):
                sev = cve_match["severity"]
                findings.append({
                    "type": f"cve_{sev.lower()}",
                    "severity": sev,
                    "host": hostname,
                    "cves": cve_match["cves"],
                    "pattern": cve_match["pattern"],
                    "description": f"Version pattern '{cve_match['pattern']}' matches {', '.join(cve_match['cves'])}",
                    "score_impact": SCORE_WEIGHTS.get(f"cve_{sev.lower()}", 10),
                })
            # Version in headers
            server = data.get("server", "") or ""
            x_powered = data.get("headers", {}).get("X-Powered-By", "") or ""
            for h_val in [server, x_powered]:
                if h_val and re.search(r"\d+\.\d+", h_val):
                    findings.append({
                        "type": "version_in_header",
                        "severity": "LOW",
                        "host": hostname,
                        "value": h_val,
                        "description": f"Version disclosed in HTTP header: {h_val}",
                        "score_impact": SCORE_WEIGHTS["version_in_header"],
                    })
                    break

        # Phase 4: Score
        scorer = ExposureScorer()
        score = scorer.calculate(fingerprint_results, findings, surface_data)

        # Phase 5: Report
        reporter = ReportGenerator(self.domain, output_prefix=self.output)
        json_path, md_path = reporter.generate(
            surface_data, fingerprint_results, findings, score
        )

        elapsed = time.time() - self.start_time

        # Final summary
        print()
        log("=" * 60, "SECTION")
        log(f"SCAN COMPLETE in {elapsed:.1f}s", "OK")
        log(f"Domain: {self.domain}", "INFO")
        log(f"Subdomains discovered: {len(surface_data['all_subdomains'])}", "INFO")
        log(f"Alive hosts: {score['alive_subdomains']}", "INFO")
        log(f"Findings: {score['total_findings']} ({score['critical_findings']} critical, {score['high_findings']} high)", "INFO")
        log(f"Exposure Score: {score['total']}/100 [{score['risk_level']}]", "FIND")
        log(f"JSON: {json_path}", "OK")
        log(f"Markdown: {md_path}", "OK")

        return {
            "score": score,
            "findings": findings,
            "surface": surface_data,
        }


# ─────────────────────────────────────────────
#  CLI ENTRYPOINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GHOST - Global Hostile OSINT Surface Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ghost.py --domain example.com
  python3 ghost.py --domain target.com.br --output reports/target
  python3 ghost.py --domain scanme.nmap.org --threads 15 --deep

Safe test targets (authorized):
  scanme.nmap.org
  testphp.vulnweb.com
  zero.webappsecurity.com
        """,
    )
    parser.add_argument("--domain", "-d", required=True, help="Target root domain")
    parser.add_argument("--output", "-o", help="Output file prefix (default: ghost_<domain>_<ts>)")
    parser.add_argument("--threads", "-t", type=int, default=10, help="Threads (default: 10)")
    parser.add_argument("--deep", action="store_true", help="Deep scan (more paths, more wordlist)")
    parser.add_argument("--version", action="version", version=f"GHOST v{VERSION}")

    args = parser.parse_args()

    scanner = GhostScanner(
        domain=args.domain,
        output=args.output,
        threads=args.threads,
        deep=args.deep,
    )

    try:
        scanner.run()
    except KeyboardInterrupt:
        print("\n[!] Scan interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
