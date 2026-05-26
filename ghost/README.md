# GHOST — Global Hostile OSINT Surface Tracker

```
  ██████  ██   ██  ██████  ███████ ████████
 ██       ██   ██ ██    ██ ██         ██
 ██   ███ ███████ ██    ██ ███████    ██
 ██    ██ ██   ██ ██    ██      ██    ██
  ██████  ██   ██  ██████  ███████    ██

 Global Hostile OSINT Surface Tracker v1.0.0
 by LIBERTUS — Autonomous Recon Engine
```

**Autonomus web attack surface reconnaissance. One command. Full picture.**

---

## What It Does

GHOST takes a root domain and automatically:

- Discovers all subdomains via Certificate Transparency logs + DNS brute-force
- Retrieves historical URLs from the Wayback Machine
- Fingerprints every live host: stack, CMS, framework, headers, cookies
- Correlates discovered versions with known CVEs
- Detects abandoned assets: subdomain takeovers, exposed buckets, admin panels, secrets
- Calculates an exposure score 0-100 with risk breakdown by category
- Outputs a structured JSON report + client-ready Markdown report

---

## Requirements

```
Python 3.7+
requests library
dig (optional, for CNAME resolution — usually pre-installed)
```

Install dependencies:
```bash
pip install requests
```

Or use the project venv:
```bash
pip install -r requirements.txt
```

---

## Installation

```bash
git clone <repo>
cd ghost
pip install requests
python3 ghost.py --help
```

---

## Usage

Basic scan:
```bash
python3 ghost.py --domain example.com
```

Save reports to a specific prefix:
```bash
python3 ghost.py --domain target.com.br --output reports/target_2025
```

More threads for faster scanning:
```bash
python3 ghost.py --domain example.com --threads 20
```

Full options:
```
usage: ghost.py [-h] --domain DOMAIN [--output OUTPUT] [--threads THREADS] [--deep]

options:
  -h, --help            show this help message and exit
  --domain DOMAIN, -d DOMAIN
                        Target root domain
  --output OUTPUT, -o OUTPUT
                        Output file prefix (default: ghost_<domain>_<timestamp>)
  --threads THREADS, -t THREADS
                        Threads (default: 10)
  --deep                Deep scan (more paths, extended wordlist)
  --version             show version and exit
```

---

## Safe Test Targets

These domains are explicitly authorized for security testing:

```bash
python3 ghost.py --domain scanme.nmap.org
python3 ghost.py --domain testphp.vulnweb.com
python3 ghost.py --domain zero.webappsecurity.com
```

**IMPORTANT:** Only scan domains you own or have explicit written authorization to test.
Unauthorized scanning may violate the Computer Fraud and Abuse Act (CFAA) and similar laws.

---

## Output

GHOST generates two files:

### JSON Report (`ghost_<domain>_<timestamp>.json`)
Structured data for programmatic integration:
```json
{
  "meta": { "tool": "GHOST", "version": "1.0.0", "domain": "...", "scan_time": "..." },
  "score": {
    "total": 72,
    "risk_level": "HIGH",
    "breakdown": { "credentials": 50, "abandoned_assets": 30, ... }
  },
  "surface": {
    "all_subdomains": [...],
    "wayback_sample": [...]
  },
  "fingerprints": {
    "api.example.com": {
      "status_code": 200, "server": "nginx/1.18.0",
      "technologies": ["Nginx", "PHP", "Laravel"],
      "cve_matches": [...]
    }
  },
  "findings": [ ... sorted by severity ... ]
}
```

### Markdown Report (`ghost_<domain>_<timestamp>.md`)
Client-ready report with:
- Executive summary table
- Risk score with category breakdown
- Critical findings with detail
- CVE correlation table
- All discovered hosts
- Historical URL sample
- Remediation recommendations

---

## Architecture

```
GHOST
├── SurfaceExpander       — CT logs, DNS brute-force, Wayback Machine
├── FingerprintEngine     — HTTP fingerprinting, tech detection, CVE matching
├── AbandonedAssetDetector — Takeover detection, sensitive path probing, bucket check
├── ExposureScorer        — Weighted scoring, risk breakdown
└── ReportGenerator       — JSON + Markdown output
```

### Detection Coverage

| Category | What GHOST Finds |
|----------|-----------------|
| Subdomains | CT logs, DNS brute-force (100+ words) |
| Historical | Wayback Machine URLs and endpoints |
| Technologies | 20+ frameworks/CMS/servers (WordPress, Laravel, Django, Rails, ASP.NET, PHP, Nginx, Apache, Cloudflare...) |
| CVEs | 20+ version/pattern correlations (PHP 5.x, Apache 2.4.49, Drupal 7, Joomla 3, OpenSSL...) |
| Sensitive Paths | 50+ paths across 4 severity tiers |
| Takeover Services | 18 cloud services (GitHub Pages, Heroku, Netlify, Vercel, AWS S3, Azure, Fastly, Shopify...) |
| Cloud Storage | S3, GCS, Azure Blob, DO Spaces, Backblaze B2 |

### Exposure Score Weights

| Finding Type | Score Impact |
|-------------|-------------|
| .env file exposed | +50 |
| Private key exposed | +50 |
| .git/HEAD exposed | +45 |
| Config file exposed | +40 |
| Subdomain takeover confirmed | +30 |
| CVE Critical match | +30 |
| Admin panel exposed | +25 |
| CVE High match | +20 |
| Swagger/API exposed | +20 |
| Sensitive file exposed | +15 |
| CVE Medium match | +10 |
| Version in header | +10 |

---

## Ethics & Legal

GHOST is built for:
- Authorized penetration testing
- Bug bounty programs (within scope)
- Security assessments of systems you own or have written permission to test
- Red team engagements

GHOST is passive-first:
- Phase 1 (Surface Expansion) is 100% passive — queries public APIs only (crt.sh, Wayback Machine)
- Phase 2-3 makes direct HTTP requests to discovered hosts — only do this with authorization

The authors are not responsible for misuse.

---

## Integration with SHIELD

GHOST is the recon engine powering LIBERTUS SHIELD — a managed security platform:

- Automated weekly attack surface monitoring
- Real-time alerts on new subdomains and critical findings
- Score trending over time
- Executive dashboards for non-technical stakeholders

See IDEIA.md for the full vision and monetization model.

---

## Contributing

This is an internal LIBERTUS tool. Contributions by invitation.

Core principles:
- No heavy dependencies (no Scrapy, no Selenium, no Nmap Python lib)
- Passive first, active only with intent
- Findings must be actionable, not noise
- Reports must be readable by a CISO, not just a pentester

---

## License

MIT License — use freely, credit LIBERTUS.

---

*Built by LIBERTUS. Because the best security is knowing what the attacker already knows.*
