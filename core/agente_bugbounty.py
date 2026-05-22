"""
LIBERTUS — Agente Bug Bounty
==============================
Loop autônomo de treinamento e execução em bug bounty.

Funciona em dois modos:

MODO TREINO (sem alvo real):
  - Pesquisa técnicas novas na web
  - Estuda CVEs recentes
  - Pratica em alvos de laboratório (testphp.vulnweb.com, scanme.nmap.org)
  - Salva tudo como conhecimento permanente

MODO PRODUÇÃO (com alvo autorizado):
  - Recebe escopo do programa de bug bounty
  - Executa reconhecimento, scan, análise
  - Gera relatório no formato da plataforma
  - Salva descobertas

O daemon chama ciclo_treino() a cada 6 horas automaticamente.
"""

import json
import time
import subprocess
import os
from pathlib import Path
from datetime import datetime


LIBERTUS_ROOT = Path(__file__).parent.parent.resolve()

# Alvos de laboratório sempre autorizados para treino
ALVOS_LAB = [
    {"host": "scanme.nmap.org",                              "tipo": "rede",    "descricao": "Alvo oficial do Nmap"},
    {"host": "testphp.vulnweb.com",                          "tipo": "web",     "descricao": "Alvo oficial Acunetix — SQLi"},
    {"host": "testasp.vulnweb.com",                          "tipo": "web",     "descricao": "Alvo oficial Acunetix — ASP"},
    {"host": "demo.testfire.net",                            "tipo": "web",     "descricao": "IBM AltoroMutual — banco demo"},
    {"host": "juice-shop.herokuapp.com",                     "tipo": "web",     "descricao": "OWASP Juice Shop"},
]

# CVEs recentes para estudar
TOPICOS_ESTUDO = [
    "CVE 2025 critical RCE vulnerabilities",
    "SQL injection bypass techniques 2025",
    "XSS filter evasion modern browsers",
    "SSRF exploitation cloud environments",
    "JWT token vulnerabilities exploitation",
    "OAuth2 security misconfigurations",
    "API security testing methodology",
    "subdomain takeover techniques",
    "HTTP request smuggling attacks",
    "CORS misconfiguration exploitation",
]


class AgenteBugBounty:

    def __init__(self, supabase_client=None, groq_client=None, buscador=None):
        self.sb       = supabase_client
        self.groq     = groq_client
        self.buscador = buscador
        self.nmap     = "/snap/bin/nmap"
        self.sqlmap   = "/snap/bin/sqlmap"

    # ──────────────────────────────────────────────────────────────
    # CICLO DE TREINO — roda autonomamente
    # ──────────────────────────────────────────────────────────────
    def ciclo_treino(self) -> dict:
        """
        Ciclo completo de treino autônomo.
        Chamado pelo daemon a cada 6 horas.
        """
        resultado = {
            "topicos_estudados": 0,
            "scans_realizados": 0,
            "vulnerabilidades_encontradas": 0,
            "conhecimento_salvo": 0
        }

        print(f"\n  🎯 AGENTE BUG BOUNTY — Ciclo de treino {datetime.now().strftime('%H:%M')}")

        # 1. Estudar técnica nova
        import random
        topico = random.choice(TOPICOS_ESTUDO)
        conhecimento = self._estudar_topico(topico)
        if conhecimento:
            resultado["topicos_estudados"] += 1
            resultado["conhecimento_salvo"] += 1

        # 2. Praticar em alvo de lab
        alvo = random.choice(ALVOS_LAB)
        vulns = self._praticar_em_lab(alvo)
        resultado["scans_realizados"] += 1
        resultado["vulnerabilidades_encontradas"] += len(vulns)

        # 3. Analisar e salvar aprendizado
        if vulns:
            self._salvar_descoberta(alvo, vulns)
            resultado["conhecimento_salvo"] += 1

        print(f"  ✅ Treino: {resultado['topicos_estudados']} tópicos, {resultado['vulnerabilidades_encontradas']} vulns")
        return resultado

    # ──────────────────────────────────────────────────────────────
    # ESTUDAR TÓPICO
    # ──────────────────────────────────────────────────────────────
    def _estudar_topico(self, topico: str) -> str:
        """Pesquisa técnica de pentest e salva como conhecimento."""
        print(f"  📚 Estudando: {topico}")

        conhecimento = ""
        if self.buscador:
            try:
                conhecimento = self.buscador._buscar_web(topico)
            except Exception:
                pass

        if not conhecimento and self.groq:
            try:
                conhecimento = self.groq.conversar(
                    f"Explique de forma técnica e prática: {topico}. "
                    f"Inclua exemplos reais, ferramentas e como detectar/explorar.",
                    ""
                )
            except Exception:
                pass

        if conhecimento and self.sb:
            try:
                self.sb.post("libertus_memoria", {
                    "tipo": "conhecimento",
                    "titulo": f"[BugBounty] {topico[:80]}",
                    "conteudo": conhecimento[:2000],
                    "tags": ["bugbounty", "pentest", "treino"],
                    "projeto": "SHIELD",
                    "peso_vivo": 8.0,
                    "decaimento_ativo": False
                })
                print(f"  💾 Salvo: {topico[:50]}")
            except Exception as e:
                print(f"  ⚠️ Erro salvar: {e}")

        return conhecimento

    # ──────────────────────────────────────────────────────────────
    # PRATICAR EM LAB
    # ──────────────────────────────────────────────────────────────
    def _praticar_em_lab(self, alvo: dict) -> list:
        """Executa testes em alvo de laboratório autorizado."""
        host = alvo["host"]
        tipo = alvo["tipo"]
        vulns = []

        print(f"  🔍 Praticando em: {host} ({tipo})")

        if tipo == "rede":
            vulns = self._scan_rede(host)
        elif tipo == "web":
            vulns = self._scan_web(host)

        return vulns

    def _scan_rede(self, host: str) -> list:
        """Scan nmap no alvo."""
        vulns = []
        try:
            env = os.environ.copy()
            env["PATH"] = f"/snap/bin:{env.get('PATH','')}"

            r = subprocess.run(
                [self.nmap, "-sT", "-sV", "-T4", "--top-ports", "100", host],
                capture_output=True, text=True, timeout=120, env=env
            )

            if r.returncode == 0 and r.stdout:
                # Parsear portas abertas
                import re
                portas = re.findall(r"(\d+)/tcp\s+open\s+(\S+)(?:\s+(.+))?", r.stdout)

                for porta, servico, versao in portas:
                    vuln = {
                        "tipo": "porta_aberta",
                        "host": host,
                        "porta": int(porta),
                        "servico": servico,
                        "versao": versao.strip() if versao else "",
                        "severidade": self._avaliar_severidade(servico, versao or "")
                    }
                    vulns.append(vuln)
                    print(f"    🔓 {porta}/{servico} {versao or ''}")

        except Exception as e:
            print(f"  ⚠️ Scan rede erro: {e}")

        return vulns

    def _scan_web(self, host: str) -> list:
        """Análise básica de aplicação web."""
        vulns = []
        try:
            import urllib.request
            url = f"http://{host}"

            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 LIBERTUS-BugBounty"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                headers = dict(resp.headers)
                status  = resp.status

            # Verificar headers de segurança ausentes
            headers_seguranca = {
                "X-Frame-Options":          "Clickjacking protection",
                "X-Content-Type-Options":   "MIME sniffing protection",
                "Content-Security-Policy":  "XSS protection",
                "Strict-Transport-Security":"HSTS",
                "X-XSS-Protection":        "XSS filter",
            }
            headers_lower = {k.lower(): v for k, v in headers.items()}

            for header, descricao in headers_seguranca.items():
                if header.lower() not in headers_lower:
                    vulns.append({
                        "tipo": "header_ausente",
                        "host": host,
                        "header": header,
                        "descricao": descricao,
                        "severidade": "baixa"
                    })
                    print(f"    ⚠️ Header ausente: {header}")

        except Exception as e:
            print(f"  ⚠️ Scan web erro: {e}")

        return vulns

    def _avaliar_severidade(self, servico: str, versao: str) -> str:
        """Avalia severidade de uma porta/serviço."""
        alto_risco = ["ftp", "telnet", "rsh", "rlogin", "vnc"]
        medio_risco = ["ssh", "smtp", "rdp", "smb", "netbios"]

        servico_lower = servico.lower()
        if any(s in servico_lower for s in alto_risco):
            return "alta"
        elif any(s in servico_lower for s in medio_risco):
            return "media"
        return "baixa"

    # ──────────────────────────────────────────────────────────────
    # MODO PRODUÇÃO — bug bounty real
    # ──────────────────────────────────────────────────────────────
    def executar_programa(self, escopo: list, plataforma: str = "intigriti") -> dict:
        """
        Executa em programa real de bug bounty.
        escopo = lista de domínios/IPs autorizados.
        """
        resultado = {
            "plataforma": plataforma,
            "alvos_testados": 0,
            "vulnerabilidades": [],
            "relatorio": ""
        }

        print(f"\n  🎯 Bug Bounty: {plataforma}")
        print(f"  Escopo: {', '.join(escopo[:3])}")

        for alvo in escopo[:5]:  # máximo 5 alvos por ciclo
            print(f"\n  → Testando: {alvo}")

            # Scan de rede
            vulns_rede = self._scan_rede(alvo)

            # Scan web se for domínio
            vulns_web = []
            if not alvo.replace(".", "").isnumeric():
                vulns_web = self._scan_web(alvo)

            todas_vulns = vulns_rede + vulns_web
            resultado["vulnerabilidades"].extend(todas_vulns)
            resultado["alvos_testados"] += 1

        # Gerar relatório
        if resultado["vulnerabilidades"]:
            resultado["relatorio"] = self._gerar_relatorio(
                resultado["vulnerabilidades"], plataforma
            )
            # Salvar no Supabase
            self._salvar_descoberta(
                {"host": ", ".join(escopo[:2]), "descricao": f"Programa {plataforma}"},
                resultado["vulnerabilidades"]
            )

        return resultado

    def _gerar_relatorio(self, vulns: list, plataforma: str) -> str:
        """Gera relatório no formato da plataforma."""
        if not self.groq:
            return ""

        vulns_txt = json.dumps(vulns[:10], ensure_ascii=False, indent=2)

        try:
            return self.groq.conversar(
                f"""Gere um relatório de bug bounty profissional para {plataforma}.

Vulnerabilidades encontradas:
{vulns_txt}

Formato: título, severidade (CVSS), descrição técnica, impacto, reprodução, remediação.
Em inglês. Objetivo: ser aceito pela plataforma e receber recompensa.""",
                ""
            )
        except Exception:
            return ""

    def _salvar_descoberta(self, alvo: dict, vulns: list):
        """Salva descobertas como memória de pentest."""
        if not self.sb or not vulns:
            return
        try:
            host = alvo.get("host", "?")
            vulns_txt = "\n".join(
                f"- [{v.get('severidade','?').upper()}] {v.get('tipo','?')}: {v.get('header', v.get('porta','?'))}"
                for v in vulns[:10]
            )
            self.sb.post("libertus_memoria", {
                "tipo": "scan_resultado",
                "titulo": f"[BugBounty] {host}: {len(vulns)} issues",
                "conteudo": f"Alvo: {host}\n\nProblemas encontrados:\n{vulns_txt}",
                "tags": ["bugbounty", "scan", host],
                "projeto": "SHIELD",
                "peso_vivo": 8.0,
                "decaimento_ativo": False
            })
        except Exception:
            pass
