"""
metodologia.py — Motor de Metodologia de Pentest
Encadeia fases automaticamente: Recon → Scan → Enum → Exploit → Post
Registra cada fase e decide próximos passos com base nos resultados.

Escreve em: /LIBERTUS/memory/decisions/, /LIBERTUS/memory/feedback/
"""

import json, datetime
from pathlib import Path
from typing import Dict, List, Optional


FASES = ["reconhecimento", "scan", "enumeracao", "exploracao", "pos_exploracao", "relatorio"]


class Metodologia:
    def __init__(self, root: Path = None):
        self.root = root
        self.dir_feedback  = (root / "memory" / "feedback")  if root else None
        self.dir_decisions = (root / "memory" / "decisions") if root else None
        for d in [self.dir_feedback, self.dir_decisions]:
            if d: d.mkdir(parents=True, exist_ok=True)

    # ── API pública ───────────────────────────────────────────────────────

    def iniciar_engajamento(self, alvo: str, escopo: str = "",
                            tipo: str = "black_box") -> Dict:
        """
        Inicia um engajamento de pentest estruturado.
        tipo: black_box | grey_box | white_box
        """
        eng = {
            "id":        datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
            "alvo":      alvo,
            "escopo":    escopo or alvo,
            "tipo":      tipo,
            "inicio":    datetime.datetime.now().isoformat(),
            "fase_atual": "reconhecimento",
            "fases":     {f: {"status": "pendente", "resultados": {}} for f in FASES},
            "findings":  [],
            "risk_score": 0,
        }
        self._salvar_engajamento(eng)
        return eng

    def executar_fase(self, eng: Dict, recon=None, scanner=None) -> Dict:
        """
        Executa a fase atual do engajamento e avança para a próxima.
        Usa módulos scanner e reconhecimento se disponíveis.
        """
        fase = eng["fase_atual"]
        alvo = eng["alvo"]

        if fase == "reconhecimento":
            resultado = self._fase_recon(alvo, recon)
        elif fase == "scan":
            resultado = self._fase_scan(alvo, scanner)
        elif fase == "enumeracao":
            resultado = self._fase_enum(alvo, eng)
        elif fase == "exploracao":
            resultado = self._fase_exploracao(eng)
        elif fase == "pos_exploracao":
            resultado = self._fase_pos_exploracao(eng)
        elif fase == "relatorio":
            resultado = self._gerar_relatorio(eng)
        else:
            resultado = {"status": "completo"}

        eng["fases"][fase]["status"]    = "concluido"
        eng["fases"][fase]["resultados"] = resultado
        eng["fases"][fase]["fim"]        = datetime.datetime.now().isoformat()

        # Extrai findings da fase
        findings = resultado.get("findings", [])
        eng["findings"].extend(findings)
        eng["risk_score"] = self._calcular_risk(eng["findings"])

        # Avança fase
        idx = FASES.index(fase)
        if idx + 1 < len(FASES):
            eng["fase_atual"] = FASES[idx + 1]

        self._salvar_engajamento(eng)
        return eng

    def executar_completo(self, alvo: str, escopo: str = "",
                          recon=None, scanner=None) -> Dict:
        """Executa todas as fases em sequência."""
        eng = self.iniciar_engajamento(alvo, escopo)
        for _ in FASES:
            eng = self.executar_fase(eng, recon=recon, scanner=scanner)
        return eng

    def resumo(self, eng: Dict) -> str:
        """Resumo executivo do engajamento."""
        findings = eng.get("findings", [])
        criticos = [f for f in findings if f.get("severity") == "CRITICO"]
        altos    = [f for f in findings if f.get("severity") == "ALTO"]
        medios   = [f for f in findings if f.get("severity") == "MEDIO"]

        linhas = [
            f"=== PENTEST REPORT — {eng['alvo']} ===",
            f"Tipo: {eng['tipo']} | Início: {eng['inicio'][:16]}",
            f"Risk Score: {eng['risk_score']}/100\n",
            f"FINDINGS ({len(findings)} total):",
            f"  CRÍTICO: {len(criticos)}",
            f"  ALTO:    {len(altos)}",
            f"  MÉDIO:   {len(medios)}\n",
        ]

        if criticos:
            linhas.append("CRÍTICOS — ação imediata necessária:")
            for f in criticos:
                linhas.append(f"  [{f['fase']}] {f['titulo']}")
                linhas.append(f"  → {f['recomendacao']}")

        if altos:
            linhas.append("\nALTOS — corrigir em 30 dias:")
            for f in altos:
                linhas.append(f"  [{f['fase']}] {f['titulo']}")

        linhas.append(f"\nPRÓXIMOS PASSOS:")
        for p in self._proximos_passos(eng)[:5]:
            linhas.append(f"  • {p}")

        return "\n".join(linhas)

    # ── Fases ─────────────────────────────────────────────────────────────

    def _fase_recon(self, alvo: str, recon) -> Dict:
        resultado = {
            "fase":    "reconhecimento",
            "alvo":    alvo,
            "findings": [],
        }
        if recon:
            try:
                dados = recon.analisar_dominio(alvo)
                resultado["dados"] = dados

                # Detecta findings
                if dados.get("ssl", {}).get("san"):
                    san = dados["ssl"]["san"]
                    if len(san) > 5:
                        resultado["findings"].append({
                            "titulo":        f"{len(san)} subdomínios via certificado SSL",
                            "severity":      "INFO",
                            "fase":          "reconhecimento",
                            "recomendacao":  "Mapear e verificar segurança de cada subdomínio",
                            "evidencia":     str(san[:5]),
                        })

                for exp in dados.get("exposicoes", []):
                    resultado["findings"].append({
                        "titulo":       exp,
                        "severity":     "MEDIO",
                        "fase":         "reconhecimento",
                        "recomendacao": "Revisar configuração e reduzir superfície de ataque",
                        "evidencia":    exp,
                    })
            except Exception as e:
                resultado["erro"] = str(e)
        else:
            resultado["nota"] = "Módulo recon não disponível — execute manualmente"
            resultado["checklist"] = [
                f"whois {alvo}",
                f"dig {alvo} ANY",
                f"curl https://crt.sh/?q=%.{alvo}&output=json | jq .[].name_value",
                f"theHarvester -d {alvo} -b all",
            ]
        return resultado

    def _fase_scan(self, alvo: str, scanner) -> Dict:
        resultado = {
            "fase":     "scan",
            "alvo":     alvo,
            "findings": [],
        }
        if scanner:
            try:
                dados = scanner.scan_rapido(alvo)
                resultado["dados"] = dados

                # Converte vetores em findings
                for v in dados.get("vetores", []):
                    sev = "ALTO" if v["prioridade"] == "ALTA" else "MEDIO"
                    resultado["findings"].append({
                        "titulo":       f"{v['servico']} ({v['porta']}) — {v['vetor']}",
                        "severity":     sev,
                        "fase":         "scan",
                        "porta":        v["porta"],
                        "recomendacao": f"Investigar {v['servico']} na porta {v['porta']}",
                        "evidencia":    f"Porta {v['porta']}/tcp aberta",
                    })

                for cve in dados.get("cves_detectados", []):
                    resultado["findings"].append({
                        "titulo":       f"CVE detectado: {cve['cve']}",
                        "severity":     "CRITICO",
                        "fase":         "scan",
                        "porta":        cve["porta"],
                        "recomendacao": "Aplicar patch imediatamente",
                        "evidencia":    f"{cve['servico']} {cve['versao']}",
                    })
            except Exception as e:
                resultado["erro"] = str(e)
        else:
            resultado["checklist"] = [
                f"nmap -sV -sC -O --open -T4 {alvo}",
                f"nmap -p- --open -T4 {alvo}",
                f"nmap --script=vuln {alvo}",
                f"nmap --script smb-vuln* -p 445 {alvo}",
            ]
        return resultado

    def _fase_enum(self, alvo: str, eng: Dict) -> Dict:
        """Enumeração baseada no que foi encontrado no scan."""
        resultado = {"fase": "enumeracao", "findings": [], "checklist": []}
        portas_abertas = set()

        for fase_dados in eng["fases"].values():
            for f in fase_dados.get("resultados", {}).get("findings", []):
                if f.get("porta"):
                    portas_abertas.add(f["porta"])

        if 80 in portas_abertas or 443 in portas_abertas:
            resultado["checklist"].extend([
                f"gobuster dir -u http://{alvo} -w /usr/share/wordlists/dirb/common.txt",
                f"nikto -h {alvo}",
                f"sqlmap -u http://{alvo} --forms --batch --crawl=3",
                f"curl -I http://{alvo} | grep -E 'Server|X-Powered'",
            ])

        if 445 in portas_abertas:
            resultado["checklist"].extend([
                f"smbmap -H {alvo}",
                f"smbclient -L //{alvo} -N",
                f"nmap --script smb-enum-shares,smb-enum-users -p 445 {alvo}",
                f"nmap --script smb-vuln-ms17-010 -p 445 {alvo}",
            ])
            resultado["findings"].append({
                "titulo":       "SMB exposto — verificar EternalBlue e compartilhamentos",
                "severity":     "ALTO",
                "fase":         "enumeracao",
                "recomendacao": "Verificar patch MS17-010 e restringir acesso SMB",
                "evidencia":    "Porta 445/tcp aberta",
            })

        if 21 in portas_abertas:
            resultado["checklist"].append(f"ftp {alvo} → tentar anonymous:anonymous")
            resultado["findings"].append({
                "titulo":       "FTP exposto — testar acesso anônimo",
                "severity":     "MEDIO",
                "fase":         "enumeracao",
                "recomendacao": "Desabilitar FTP anônimo, usar SFTP",
                "evidencia":    "Porta 21/tcp aberta",
            })

        if 22 in portas_abertas:
            resultado["checklist"].append(
                f"ssh {alvo} -o PreferredAuthentications=password → verificar se aceita senha"
            )

        if 3306 in portas_abertas:
            resultado["checklist"].extend([
                f"nmap --script mysql-empty-password -p 3306 {alvo}",
                f"nmap --script mysql-info -p 3306 {alvo}",
            ])
            resultado["findings"].append({
                "titulo":       "MySQL exposto externamente",
                "severity":     "ALTO",
                "fase":         "enumeracao",
                "recomendacao": "Restringir acesso MySQL a localhost apenas",
                "evidencia":    "Porta 3306/tcp aberta externamente",
            })

        if 6379 in portas_abertas or 27017 in portas_abertas:
            resultado["findings"].append({
                "titulo":       "Banco de dados NoSQL exposto — sem autenticação provável",
                "severity":     "CRITICO",
                "fase":         "enumeracao",
                "recomendacao": "Fechar porta externamente e habilitar autenticação",
                "evidencia":    "Redis/MongoDB exposto sem autenticação",
            })

        return resultado

    def _fase_exploracao(self, eng: Dict) -> Dict:
        """Gera plano de exploração baseado nos findings."""
        resultado = {"fase": "exploracao", "findings": [], "plano": []}
        criticos = [f for f in eng["findings"] if f.get("severity") == "CRITICO"]
        altos    = [f for f in eng["findings"] if f.get("severity") == "ALTO"]

        for f in criticos[:3]:
            resultado["plano"].append({
                "prioridade": 1,
                "finding":    f["titulo"],
                "tecnica":    self._tecnica_para_finding(f),
                "ferramenta": self._ferramenta_para_finding(f),
            })

        for f in altos[:3]:
            resultado["plano"].append({
                "prioridade": 2,
                "finding":    f["titulo"],
                "tecnica":    self._tecnica_para_finding(f),
                "ferramenta": self._ferramenta_para_finding(f),
            })

        resultado["nota"] = "Executar APENAS com autorização explícita por escrito"
        return resultado

    def _fase_pos_exploracao(self, eng: Dict) -> Dict:
        return {
            "fase":     "pos_exploracao",
            "findings": [],
            "checklist": [
                "id && whoami && hostname",
                "cat /etc/passwd | grep -v nologin",
                "sudo -l → verificar comandos sem senha",
                "find / -perm -4000 2>/dev/null → binários SUID",
                "cat /proc/version → versão do kernel",
                "linpeas.sh → enumeração automática",
                "Verificar credenciais em arquivos de config",
                "Verificar histórico de comandos: ~/.bash_history",
                "Pivotar para rede interna se disponível",
                "Documentar evidências antes de qualquer limpeza",
            ],
        }

    def _gerar_relatorio(self, eng: Dict) -> Dict:
        return {
            "fase":          "relatorio",
            "findings":      [],
            "resumo":        self.resumo(eng),
            "total_findings": len(eng["findings"]),
            "risk_score":    eng["risk_score"],
            "recomendacoes": self._recomendacoes_finais(eng),
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    def _calcular_risk(self, findings: List[Dict]) -> int:
        score = 0
        pesos = {"CRITICO": 25, "ALTO": 15, "MEDIO": 8, "BAIXO": 3, "INFO": 1}
        for f in findings:
            score += pesos.get(f.get("severity", "INFO"), 1)
        return min(100, score)

    def _proximos_passos(self, eng: Dict) -> List[str]:
        passos = []
        fase   = eng.get("fase_atual", "")
        if fase == "reconhecimento":
            passos.append("Executar scan de portas completo")
        elif fase == "scan":
            passos.append("Enumerar serviços descobertos")
        elif fase == "enumeracao":
            passos.append("Selecionar vetores e iniciar exploração")
        elif fase == "exploracao":
            passos.append("Documentar acesso obtido e escalar privilégio")
        elif fase == "pos_exploracao":
            passos.append("Compilar evidências e gerar relatório")

        criticos = [f for f in eng.get("findings",[]) if f.get("severity")=="CRITICO"]
        for f in criticos[:3]:
            passos.append(f"Explorar: {f['titulo']}")

        return passos

    def _tecnica_para_finding(self, f: Dict) -> str:
        titulo = f.get("titulo","").lower()
        if "eternalblue" in titulo or "ms17" in titulo:
            return "Buffer overflow via SMB — exploit público disponível"
        if "sql" in titulo:
            return "SQL injection — extração de dados via UNION/Blind"
        if "redis" in titulo or "mongodb" in titulo:
            return "Acesso direto sem autenticação"
        if "ftp" in titulo:
            return "Login anônimo ou brute force"
        if "cve" in titulo:
            return "Exploit público disponível no ExploitDB"
        return "Investigação manual necessária"

    def _ferramenta_para_finding(self, f: Dict) -> str:
        titulo = f.get("titulo","").lower()
        if "eternalblue" in titulo:
            return "metasploit: exploit/windows/smb/ms17_010_eternalblue"
        if "sql" in titulo:
            return "sqlmap"
        if "redis" in titulo:
            return "redis-cli"
        if "mongodb" in titulo:
            return "mongosh"
        if "ftp" in titulo:
            return "hydra ou ftp client"
        if "cve" in titulo:
            return "searchsploit + metasploit"
        return "nmap --script=vuln"

    def _recomendacoes_finais(self, eng: Dict) -> List[str]:
        recs = list({f["recomendacao"] for f in eng.get("findings",[])
                     if f.get("recomendacao")})
        recs.extend([
            "Implementar patch management contínuo",
            "Realizar pentest periódico (mínimo anual)",
            "Configurar SIEM para detecção de anomalias",
            "Treinar equipe em segurança ofensiva e defensiva",
        ])
        return recs[:10]

    def _salvar_engajamento(self, eng: Dict):
        if not self.dir_feedback:
            return
        arq = self.dir_feedback / f"engajamento_{eng['id']}.json"
        arq.write_text(json.dumps(eng, ensure_ascii=False, indent=2),
                       encoding="utf-8")
