"""
reconhecimento.py — OSINT e Reconhecimento Automatizado
Coleta passiva de informações sobre alvos.

Uso exclusivo em alvos autorizados.
Escreve em: /LIBERTUS/memory/feedback/
"""

import subprocess, re, json, datetime, socket, ssl
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request


class Reconhecimento:
    """OSINT automatizado para fase de reconhecimento."""

    def __init__(self, root: Path = None):
        self.root = root
        self.dir_output = (root / "memory" / "feedback") if root else None
        if self.dir_output:
            self.dir_output.mkdir(parents=True, exist_ok=True)

    # ── API pública ───────────────────────────────────────────────────────

    def analisar_dominio(self, dominio: str) -> Dict:
        """
        Reconhecimento completo de um domínio.
        Executa: whois, DNS, subdomínios, certificado SSL, emails.
        """
        resultado = {
            "dominio":     dominio,
            "timestamp":   datetime.datetime.now().isoformat(),
            "dns":         self._dns_enum(dominio),
            "ssl":         self._analisar_ssl(dominio),
            "subdominos":  self._subdominios_passivos(dominio),
            "emails":      self._buscar_emails(dominio),
            "tecnologias": self._fingerprint_web(dominio),
            "exposicoes":  [],
        }

        # Detecta exposições
        resultado["exposicoes"] = self._detectar_exposicoes(resultado)

        self._salvar(resultado, f"recon_{dominio}")
        return resultado

    def analisar_ip(self, ip: str) -> Dict:
        """Reconhecimento de um IP específico."""
        resultado = {
            "ip":        ip,
            "timestamp": datetime.datetime.now().isoformat(),
            "rdns":      self._rdns(ip),
            "asn":       self._asn_info(ip),
            "geo":       self._geoip(ip),
            "portas_comuns": self._check_portas_comuns(ip),
        }
        self._salvar(resultado, f"recon_ip_{ip}")
        return resultado

    def zone_transfer(self, dominio: str) -> Dict:
        """
        Tenta zone transfer (AXFR) em todos os nameservers.
        Se bem-sucedido, revela toda a infraestrutura DNS.
        """
        resultado = {
            "dominio":     dominio,
            "nameservers": [],
            "axfr_resultado": {},
            "vulneravel":  False,
        }

        # Descobre nameservers
        ns = self._get_nameservers(dominio)
        resultado["nameservers"] = ns

        # Tenta AXFR em cada NS
        for nameserver in ns:
            axfr = self._tentar_axfr(dominio, nameserver)
            if axfr:
                resultado["axfr_resultado"][nameserver] = axfr
                resultado["vulneravel"] = True

        return resultado

    def google_dorks(self, dominio: str) -> List[str]:
        """
        Gera Google Dorks para o domínio.
        Use manualmente no browser — não automatiza buscas no Google.
        """
        dorks = [
            f'site:{dominio} filetype:pdf',
            f'site:{dominio} filetype:xls OR filetype:xlsx',
            f'site:{dominio} "index of"',
            f'site:{dominio} inurl:admin',
            f'site:{dominio} inurl:login',
            f'site:{dominio} inurl:config',
            f'site:{dominio} "DB_PASSWORD" OR "DB_USER"',
            f'site:{dominio} inurl:.env',
            f'site:{dominio} inurl:backup',
            f'site:{dominio} intitle:"Index of"',
            f'site:github.com {dominio} password OR secret OR token',
            f'site:pastebin.com {dominio}',
            f'"{dominio}" email filetype:txt',
            f'inurl:"{dominio}" "phpMyAdmin"',
        ]
        return dorks

    def shodan_search(self, query: str, api_key: str = "") -> Dict:
        """
        Busca no Shodan via API.
        Requer SHODAN_API_KEY configurada.
        """
        import os
        key = api_key or os.environ.get("SHODAN_API_KEY", "")
        if not key:
            return {"erro": "Configure SHODAN_API_KEY no ambiente"}

        try:
            url = f"https://api.shodan.io/shodan/host/search?key={key}&query={query}"
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=15)
            dados = json.loads(resp.read())
            resultados = []
            for item in dados.get("matches", [])[:20]:
                resultados.append({
                    "ip":       item.get("ip_str"),
                    "porta":    item.get("port"),
                    "org":      item.get("org"),
                    "pais":     item.get("location", {}).get("country_name"),
                    "produto":  item.get("product", ""),
                    "versao":   item.get("version", ""),
                    "banner":   item.get("data", "")[:200],
                })
            return {
                "query":    query,
                "total":    dados.get("total", 0),
                "resultados": resultados,
            }
        except Exception as e:
            return {"erro": str(e)}

    def gerar_relatorio(self, resultado: Dict) -> str:
        """Gera relatório legível do reconhecimento."""
        linhas = [
            f"=== RECONHECIMENTO: {resultado.get('dominio', resultado.get('ip','?'))} ===",
            f"Data: {resultado.get('timestamp','?')[:16]}\n",
        ]

        dns = resultado.get("dns", {})
        if dns:
            linhas.append("DNS:")
            for tipo, vals in dns.items():
                if vals:
                    linhas.append(f"  {tipo}: {', '.join(str(v) for v in vals[:5])}")

        ssl_info = resultado.get("ssl", {})
        if ssl_info and not ssl_info.get("erro"):
            linhas.append(f"\nSSL:")
            linhas.append(f"  Emitido para: {ssl_info.get('subject','?')}")
            linhas.append(f"  Expira: {ssl_info.get('not_after','?')}")
            linhas.append(f"  SANs: {', '.join(ssl_info.get('san',[][:5]))}")

        subs = resultado.get("subdominos", [])
        if subs:
            linhas.append(f"\nSubdomínios ({len(subs)}):")
            for s in subs[:10]:
                linhas.append(f"  {s}")

        emails = resultado.get("emails", [])
        if emails:
            linhas.append(f"\nEmails encontrados:")
            for e in emails[:10]:
                linhas.append(f"  {e}")

        exposicoes = resultado.get("exposicoes", [])
        if exposicoes:
            linhas.append(f"\n⚠️  EXPOSIÇÕES DETECTADAS:")
            for exp in exposicoes:
                linhas.append(f"  {exp}")

        return "\n".join(linhas)

    # ── Internos ──────────────────────────────────────────────────────────

    def _dns_enum(self, dominio: str) -> Dict:
        """Enumeração completa de registros DNS."""
        registros = {}
        tipos = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]

        for tipo in tipos:
            try:
                r = subprocess.run(
                    ["dig", "+short", tipo, dominio],
                    capture_output=True, text=True, timeout=10
                )
                vals = [v.strip() for v in r.stdout.strip().split("\n") if v.strip()]
                if vals:
                    registros[tipo] = vals
            except Exception:
                try:
                    # Fallback: socket para A records
                    if tipo == "A":
                        ip = socket.gethostbyname(dominio)
                        registros["A"] = [ip]
                except Exception:
                    pass

        return registros

    def _analisar_ssl(self, dominio: str) -> Dict:
        """Analisa certificado SSL — revela subdomínios via SANs."""
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((dominio, 443), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=dominio) as ssock:
                    cert = ssock.getpeercert()

            san = []
            for tipo, valor in cert.get("subjectAltName", []):
                if tipo == "DNS":
                    san.append(valor)

            subject = dict(x[0] for x in cert.get("subject", []))
            return {
                "subject":   subject.get("commonName", ""),
                "issuer":    dict(x[0] for x in cert.get("issuer", [])).get("organizationName",""),
                "not_before": cert.get("notBefore",""),
                "not_after":  cert.get("notAfter",""),
                "san":       san,
                "versao_ssl": ssock.version(),
            }
        except Exception as e:
            return {"erro": str(e)}

    def _subdominios_passivos(self, dominio: str) -> List[str]:
        """Descobre subdomínios via Certificate Transparency (crt.sh)."""
        subs = set()
        try:
            url = f"https://crt.sh/?q=%.{dominio}&output=json"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0"
            })
            resp = urllib.request.urlopen(req, timeout=15)
            dados = json.loads(resp.read())
            for entry in dados:
                nome = entry.get("name_value", "")
                for sub in nome.split("\n"):
                    sub = sub.strip().lstrip("*.")
                    if sub.endswith(dominio) and sub != dominio:
                        subs.add(sub)
        except Exception:
            pass

        # Complementa com wordlist básica
        comuns = ["www", "mail", "ftp", "admin", "api", "dev",
                  "staging", "vpn", "smtp", "webmail", "ns1", "ns2"]
        for sub in comuns:
            fqdn = f"{sub}.{dominio}"
            try:
                socket.gethostbyname(fqdn)
                subs.add(fqdn)
            except Exception:
                pass

        return sorted(subs)

    def _buscar_emails(self, dominio: str) -> List[str]:
        """
        Busca emails relacionados ao domínio.
        Verifica registros TXT e heurísticas comuns.
        """
        emails = set()

        # SPF/DMARC podem revelar serviços de email
        try:
            r = subprocess.run(
                ["dig", "+short", "TXT", dominio],
                capture_output=True, text=True, timeout=10
            )
            # Formatos comuns de email em headers
            found = re.findall(r"[\w.+-]+@[\w.-]+\." + dominio.split(".")[-1], r.stdout)
            emails.update(found)
        except Exception:
            pass

        # Padrões comuns de email corporativo
        formatos = [f"admin@{dominio}", f"security@{dominio}",
                    f"contact@{dominio}", f"info@{dominio}"]
        return list(emails) + [f for f in formatos if f not in emails][:3]

    def _fingerprint_web(self, dominio: str) -> Dict:
        """Detecta tecnologias web via headers e resposta."""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            url = f"https://{dominio}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, context=ctx, timeout=10)
            headers = dict(resp.headers)

            techs = {}
            for h, v in headers.items():
                h_l = h.lower()
                if h_l in ("server", "x-powered-by", "x-generator"):
                    techs[h_l] = v

            return {"headers": techs, "status": resp.status}
        except Exception as e:
            return {"erro": str(e)}

    def _detectar_exposicoes(self, resultado: Dict) -> List[str]:
        """Detecta exposições baseado nos dados coletados."""
        exposicoes = []

        ssl = resultado.get("ssl", {})
        san = ssl.get("san", [])
        if len(san) > 10:
            exposicoes.append(f"Certificado revela {len(san)} subdomínios via SANs")

        subs = resultado.get("subdominos", [])
        interessantes = ["dev.", "staging.", "test.", "admin.", "internal.", "vpn."]
        for sub in subs:
            for p in interessantes:
                if p in sub:
                    exposicoes.append(f"Subdomínio sensível encontrado: {sub}")
                    break

        techs = resultado.get("tecnologias", {})
        headers = techs.get("headers", {})
        if "server" in headers and "/" in headers["server"]:
            exposicoes.append(f"Versão do servidor exposta: {headers['server']}")

        return exposicoes

    def _get_nameservers(self, dominio: str) -> List[str]:
        try:
            r = subprocess.run(
                ["dig", "+short", "NS", dominio],
                capture_output=True, text=True, timeout=10
            )
            return [ns.rstrip(".") for ns in r.stdout.strip().split("\n") if ns.strip()]
        except Exception:
            return []

    def _tentar_axfr(self, dominio: str, nameserver: str) -> List[str]:
        try:
            r = subprocess.run(
                ["dig", "axfr", f"@{nameserver}", dominio],
                capture_output=True, text=True, timeout=30
            )
            if "Transfer failed" not in r.stdout and len(r.stdout) > 200:
                return r.stdout.split("\n")[:50]
        except Exception:
            pass
        return []

    def _rdns(self, ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ""

    def _asn_info(self, ip: str) -> Dict:
        try:
            url = f"https://ipinfo.io/{ip}/json"
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=10)
            dados = json.loads(resp.read())
            return {
                "org":      dados.get("org",""),
                "pais":     dados.get("country",""),
                "cidade":   dados.get("city",""),
                "hostname": dados.get("hostname",""),
            }
        except Exception:
            return {}

    def _geoip(self, ip: str) -> Dict:
        return self._asn_info(ip)

    def _check_portas_comuns(self, ip: str) -> List[int]:
        """Verifica portas comuns abertas via socket."""
        abertas = []
        portas = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445,
                  1433, 3306, 3389, 5432, 5900, 6379, 8080, 27017]
        for porta in portas:
            try:
                with socket.create_connection((ip, porta), timeout=1):
                    abertas.append(porta)
            except Exception:
                pass
        return abertas

    def _salvar(self, dados: Dict, nome: str):
        if not self.dir_output:
            return
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        arq = self.dir_output / f"{ts}_{nome}.json"
        arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                       encoding="utf-8")
