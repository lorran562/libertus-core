"""
scanner.py — Scanner Inteligente de Redes e Serviços
Wrapper do nmap com interpretação automática de resultados.
Identifica próximos passos para o Libertus executar.

Escreve em: /LIBERTUS/memory/feedback/
"""

import subprocess, re, json, datetime, shutil
from pathlib import Path
from typing import Dict, List, Optional


class Scanner:
    """
    Scanner inteligente que interpreta resultados e decide próximos passos.
    Uso exclusivo em redes autorizadas.
    """

    # Mapeamento de porta → vetor de ataque conhecido
    VETORES = {
        21:    ("FTP",    ["anonymous_login", "brute_force", "version_exploit"]),
        22:    ("SSH",    ["brute_force", "version_exploit", "key_auth_bypass"]),
        23:    ("Telnet", ["credenciais_texto_claro", "brute_force"]),
        25:    ("SMTP",   ["relay_aberto", "user_enum", "spoofing"]),
        53:    ("DNS",    ["zone_transfer", "cache_poison", "subdomain_enum"]),
        80:    ("HTTP",   ["web_scan", "dir_bruteforce", "vuln_scan"]),
        110:   ("POP3",   ["credenciais_texto_claro", "brute_force"]),
        135:   ("RPC",    ["ms_vulnerabilidades", "info_leak"]),
        139:   ("NetBIOS",["smb_enum", "null_session"]),
        443:   ("HTTPS",  ["ssl_analysis", "web_scan", "cert_info"]),
        445:   ("SMB",    ["eternalblue", "hash_capture", "share_enum"]),
        1433:  ("MSSQL",  ["brute_force", "xp_cmdshell", "sa_account"]),
        3306:  ("MySQL",  ["brute_force", "info_leak", "file_read"]),
        3389:  ("RDP",    ["bluekeep", "brute_force", "nla_bypass"]),
        5432:  ("PgSQL",  ["brute_force", "info_leak"]),
        5900:  ("VNC",    ["brute_force", "sem_autenticacao"]),
        6379:  ("Redis",  ["sem_autenticacao", "rce_via_config"]),
        8080:  ("HTTP-alt",["admin_panel", "proxy_abuse", "web_scan"]),
        27017: ("MongoDB", ["sem_autenticacao", "info_leak"]),
    }

    CVE_CRITICOS = {
        "OpenSSH 7.2":    "CVE-2016-6210 — user enumeration",
        "OpenSSH 8.0":    "CVE-2023-38408 — ssh-agent RCE",
        "Apache 2.4.49":  "CVE-2021-41773 — path traversal + RCE",
        "Apache 2.4.50":  "CVE-2021-42013 — path traversal + RCE",
        "vsftpd 2.3.4":   "CVE-2011-2523 — backdoor na porta 6200",
        "Samba 3.5.0":    "CVE-2017-7494 — SambaCry RCE",
        "ProFTPd 1.3.3c": "CVE-2010-4221 — buffer overflow RCE",
    }

    def __init__(self, root: Path = None):
        self.root       = root
        # Procurar nmap — snap instala em /snap/bin que pode não estar no PATH
        import os
        nmap_paths = [
            "/snap/bin/nmap",          # snap (Ubuntu)
            shutil.which("nmap"),       # PATH padrão
            "/usr/bin/nmap",
            "/usr/local/bin/nmap",
        ]
        self.nmap_path = next((p for p in nmap_paths if p and os.path.exists(p)), None)
        self.nmap_ok   = self.nmap_path is not None
        if self.nmap_ok:
            print(f"  nmap encontrado: {self.nmap_path}")
        self.dir_output = (root / "memory" / "feedback") if root else None
        if self.dir_output:
            self.dir_output.mkdir(parents=True, exist_ok=True)

    # ── API pública ───────────────────────────────────────────────────────

    def scan_rapido(self, alvo: str) -> Dict:
        """
        Scan inicial rápido: descobre hosts e portas abertas.
        Identifica vetores de ataque imediatamente.
        """
        if not self._validar_alvo(alvo):
            return {"erro": f"Alvo inválido ou não autorizado: {alvo}"}

        resultados = {
            "alvo":      alvo,
            "timestamp": datetime.datetime.now().isoformat(),
            "hosts":     [],
            "portas":    [],
            "vetores":   [],
            "proximos_passos": [],
        }

        # 1. Descoberta de hosts
        hosts = self._ping_sweep(alvo)
        resultados["hosts"] = hosts

        # 2. Scan de portas
        for host in hosts[:10]:
            portas = self._port_scan(host)
            resultados["portas"].extend(portas)
            vetores = self._mapear_vetores(portas)
            resultados["vetores"].extend(vetores)

        # 3. Próximos passos inteligentes
        resultados["proximos_passos"] = self._gerar_proximos_passos(resultados)

        self._salvar(resultados, "scan_rapido")
        return resultados

    def scan_completo(self, alvo: str) -> Dict:
        """
        Scan completo com detecção de versão, OS e scripts NSE.
        Identifica CVEs conhecidos.
        """
        if not self.nmap_ok:
            return {"erro": "nmap não instalado"}
        if not self._validar_alvo(alvo):
            return {"erro": "Alvo inválido"}

        cmd = [
            "nmap", "-sV", "-O", "--script=default,vuln",
            "-T4", "--open", "-oX", "-", alvo
        ]
        resultado_raw = self._executar_nmap(cmd)
        parsed        = self._parsear_xml(resultado_raw)
        cves          = self._detectar_cves(parsed)
        vetores       = self._mapear_vetores(parsed.get("portas", []))
        proximos      = self._gerar_proximos_passos({
            "portas": parsed.get("portas", []),
            "vetores": vetores,
        })

        resultado = {
            **parsed,
            "cves_detectados": cves,
            "vetores":         vetores,
            "proximos_passos": proximos,
            "timestamp":       datetime.datetime.now().isoformat(),
        }

        self._salvar(resultado, "scan_completo")
        return resultado

    def scan_web(self, url: str) -> Dict:
        """
        Scan focado em aplicação web.
        Detecta tecnologias, headers, portas relacionadas.
        """
        import urllib.request, ssl

        resultado = {
            "url":       url,
            "timestamp": datetime.datetime.now().isoformat(),
            "headers":   {},
            "tecnologias": [],
            "riscos":    [],
            "vetores":   [],
        }

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; Libertus/1.0)"
            })
            resp = urllib.request.urlopen(req, context=ctx, timeout=10)
            headers = dict(resp.headers)
            resultado["headers"] = headers
            resultado["status_code"] = resp.status

            # Detecta tecnologias
            resultado["tecnologias"] = self._detectar_tecnologias(headers, "")

            # Avalia headers de segurança
            resultado["riscos"] = self._avaliar_headers_seguranca(headers)

            # Vetores baseados em tecnologias
            resultado["vetores"] = self._vetores_web(resultado["tecnologias"])

        except Exception as e:
            resultado["erro"] = str(e)

        self._salvar(resultado, "scan_web")
        return resultado

    def interpretar(self, resultado: Dict) -> str:
        """
        Interpreta resultado de qualquer scan em linguagem natural.
        Retorna relatório acionável para o Libertus.
        """
        linhas = [
            f"=== INTERPRETAÇÃO DO SCAN ===",
            f"Alvo: {resultado.get('alvo', resultado.get('url', '?'))}",
            f"Data: {resultado.get('timestamp','?')[:16]}\n",
        ]

        # Portas
        portas = resultado.get("portas", [])
        if portas:
            linhas.append(f"PORTAS ABERTAS ({len(portas)}):")
            for p in portas[:15]:
                porta = p.get("porta", "?")
                servico = p.get("servico", "?")
                versao  = p.get("versao", "")
                linhas.append(f"  {porta}/tcp — {servico} {versao}")

        # CVEs
        cves = resultado.get("cves_detectados", [])
        if cves:
            linhas.append(f"\n⚠️  CVEs DETECTADOS ({len(cves)}):")
            for cve in cves:
                linhas.append(f"  {cve['servico']}: {cve['cve']}")

        # Vetores
        vetores = resultado.get("vetores", [])
        if vetores:
            linhas.append(f"\n🎯 VETORES DE ATAQUE ({len(vetores)}):")
            for v in vetores[:8]:
                linhas.append(f"  [{v['prioridade']}] {v['servico']} → {v['vetor']}")

        # Riscos de headers
        riscos = resultado.get("riscos", [])
        if riscos:
            linhas.append(f"\n🔓 HEADERS DE SEGURANÇA AUSENTES:")
            for r in riscos:
                linhas.append(f"  {r}")

        # Próximos passos
        proximos = resultado.get("proximos_passos", [])
        if proximos:
            linhas.append(f"\n📋 PRÓXIMOS PASSOS:")
            for i, p in enumerate(proximos[:5], 1):
                linhas.append(f"  {i}. {p}")

        return "\n".join(linhas)

    # ── Nmap wrappers ─────────────────────────────────────────────────────

    def _ping_sweep(self, rede: str) -> List[str]:
        """Descobre hosts ativos. Para domínios, retorna diretamente."""
        if not self.nmap_ok:
            return [rede]
        # Para domínios/hostnames, não fazer ping sweep — ir direto ao scan
        if not re.match(r"^\d+\.\d+\.\d+\.\d+", rede) and "/" not in rede:
            return [rede]
        try:
            r = subprocess.run(
                ["sudo", self.nmap_path or "nmap", "-sn", "-T4", rede],
                capture_output=True, text=True, timeout=60
            )
            hosts = re.findall(r"Nmap scan report for (?:[\w.-]+ \()?(\d+\.\d+\.\d+\.\d+)", r.stdout)
            return hosts if hosts else [rede]
        except Exception:
            return [rede]

    def _port_scan(self, host: str) -> List[Dict]:
        """Scan de portas — usa sudo nmap -sS (SYN scan completo)."""
        if not self.nmap_ok:
            return []
        try:
            # SYN scan com sudo — precisa de root mas é o mais preciso
            r = subprocess.run(
                ["sudo", self.nmap_path, "-sS", "-sV", "-T4", "--open",
                 "-p", "21,22,23,25,53,80,110,135,139,143,443,445,"
                       "3306,3389,5432,5900,6379,8080,8443,8888,27017",
                 host],
                capture_output=True, text=True, timeout=120
            )
            portas = self._parsear_portas_simples(r.stdout)
            if not portas:
                # Fallback: top 1000 portas
                r2 = subprocess.run(
                    ["sudo", self.nmap_path, "-sS", "-T4", "--top-ports", "1000", host],
                    capture_output=True, text=True, timeout=120
                )
                portas = self._parsear_portas_simples(r2.stdout)
            return portas
        except Exception as e:
            print(f"  ⚠️ port_scan erro: {e}")
            return []

    def _executar_nmap(self, cmd: List[str]) -> str:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return r.stdout
        except Exception as e:
            return str(e)

    # ── Parsing ───────────────────────────────────────────────────────────

    def _parsear_portas_simples(self, saida: str) -> List[Dict]:
        portas = []
        for linha in saida.split("\n"):
            m = re.match(r"(\d+)/tcp\s+open\s+(\S+)(?:\s+(.+))?", linha)
            if m:
                portas.append({
                    "porta":   int(m.group(1)),
                    "estado":  "open",
                    "servico": m.group(2),
                    "versao":  (m.group(3) or "").strip(),
                })
        return portas

    def _parsear_xml(self, xml: str) -> Dict:
        """Parse básico de XML do nmap."""
        resultado = {"portas": [], "os": ""}
        portas = re.findall(
            r'<port protocol="tcp" portid="(\d+)".*?<state state="open".*?'
            r'<service name="([^"]*)"(?:[^>]*version="([^"]*)")?',
            xml, re.DOTALL
        )
        for porta, servico, versao in portas:
            resultado["portas"].append({
                "porta":   int(porta),
                "servico": servico,
                "versao":  versao or "",
                "estado":  "open",
            })
        os_match = re.search(r'<osmatch name="([^"]+)"', xml)
        if os_match:
            resultado["os"] = os_match.group(1)
        return resultado

    # ── Inteligência ──────────────────────────────────────────────────────

    def _mapear_vetores(self, portas: List[Dict]) -> List[Dict]:
        """Mapeia portas abertas para vetores de ataque."""
        vetores = []
        for p in portas:
            num = p.get("porta", 0)
            if num in self.VETORES:
                servico, ataques = self.VETORES[num]
                for ataque in ataques:
                    vetores.append({
                        "porta":      num,
                        "servico":    servico,
                        "vetor":      ataque,
                        "prioridade": "ALTA" if num in [445, 22, 3389, 21] else "MEDIA",
                    })
        return sorted(vetores, key=lambda x: x["prioridade"])

    def _detectar_cves(self, parsed: Dict) -> List[Dict]:
        """Detecta CVEs baseado em versões detectadas."""
        cves = []
        for porta in parsed.get("portas", []):
            versao = porta.get("versao", "")
            for padrao, cve in self.CVE_CRITICOS.items():
                if padrao.lower() in versao.lower():
                    cves.append({
                        "porta":   porta["porta"],
                        "servico": porta["servico"],
                        "versao":  versao,
                        "cve":     cve,
                    })
        return cves

    def _gerar_proximos_passos(self, resultado: Dict) -> List[str]:
        """Gera lista priorizada de próximos passos."""
        passos = []
        portas = {p.get("porta") for p in resultado.get("portas", [])}
        vetores = resultado.get("vetores", [])

        if 445 in portas:
            passos.append("nmap --script smb-vuln* para verificar EternalBlue (MS17-010)")
        if 22 in portas:
            passos.append("hydra -l root -P rockyou.txt ssh://ALVO (se autorizado)")
        if 80 in portas or 443 in portas:
            passos.append("gobuster dir -u http://ALVO -w common.txt para descobrir endpoints")
            passos.append("nikto -h http://ALVO para scan de vulnerabilidades web")
        if 21 in portas:
            passos.append("ftp ALVO → tentar login anonymous:anonymous")
        if 3306 in portas:
            passos.append("nmap --script mysql-empty-password para verificar sem senha")
        if 6379 in portas:
            passos.append("redis-cli -h ALVO ping → verificar acesso sem autenticação")
        if 27017 in portas:
            passos.append("mongo ALVO --eval 'db.adminCommand({listDatabases:1})' → sem auth?")
        if not passos:
            passos.append("Scan mais agressivo: nmap -sV -sC -O --script=vuln ALVO")

        return passos

    def _detectar_tecnologias(self, headers: Dict, body: str) -> List[str]:
        """Detecta stack tecnológico via headers."""
        techs = []
        mapa = {
            "x-powered-by":    lambda v: v,
            "server":          lambda v: v,
            "x-generator":     lambda v: v,
            "x-aspnet-version": lambda _: "ASP.NET",
        }
        for header, extrator in mapa.items():
            if header in {h.lower() for h in headers}:
                val = next((v for k, v in headers.items()
                           if k.lower() == header), "")
                techs.append(extrator(val))
        return [t for t in techs if t]

    def _avaliar_headers_seguranca(self, headers: Dict) -> List[str]:
        """Detecta headers de segurança ausentes."""
        headers_lower = {k.lower() for k in headers}
        criticos = {
            "strict-transport-security": "HSTS ausente — suscetível a downgrade",
            "content-security-policy":   "CSP ausente — XSS mais fácil",
            "x-frame-options":           "X-Frame-Options ausente — clickjacking possível",
            "x-content-type-options":    "X-Content-Type-Options ausente — MIME sniffing",
            "referrer-policy":           "Referrer-Policy ausente — info leak",
        }
        return [msg for header, msg in criticos.items()
                if header not in headers_lower]

    def _vetores_web(self, tecnologias: List[str]) -> List[str]:
        """Sugere vetores baseado em tecnologias detectadas."""
        vetores = ["gobuster", "nikto", "sqlmap -u URL --forms"]
        for tech in tecnologias:
            tech_l = tech.lower()
            if "wordpress" in tech_l:
                vetores.append("wpscan --url URL --enumerate vp,vt,u")
            if "php" in tech_l:
                vetores.append("buscar file inclusion, phpinfo.php exposto")
            if "apache" in tech_l or "nginx" in tech_l:
                vetores.append("verificar versão contra CVEs conhecidos")
        return vetores

    def _validar_alvo(self, alvo: str) -> bool:
        """Valida que o alvo não é claramente externo sem autorização."""
        # Permite IPs privados e localhost para labs
        import ipaddress
        try:
            ip_str = re.match(r"(\d+\.\d+\.\d+\.\d+)", alvo)
            if ip_str:
                ip = ipaddress.ip_address(ip_str.group(1))
                return ip.is_private or ip.is_loopback
            # Para hostnames, assume autorizado (usuário é responsável)
            return True
        except Exception:
            return True

    def _salvar(self, dados: Dict, tipo: str):
        if not self.dir_output:
            return
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        arq = self.dir_output / f"{ts}_scanner_{tipo}.json"
        arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                       encoding="utf-8")
