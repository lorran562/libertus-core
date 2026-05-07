"""
wordlist_engine.py — Motor de Wordlists Contextuais
Gera wordlists inteligentes baseadas no alvo, não genéricas.
Contexto = mais chances de sucesso.

Escreve em: /LIBERTUS/memory/feedback/
"""

import re, hashlib, itertools, datetime
from pathlib import Path
from typing import List, Dict, Optional


class WordlistEngine:
    def __init__(self, root: Path = None):
        self.root = root
        self.dir_output = (root / "memory" / "feedback") if root else None
        if self.dir_output:
            self.dir_output.mkdir(parents=True, exist_ok=True)

    # ── API pública ───────────────────────────────────────────────────────

    def gerar_para_alvo(self, dominio: str, empresa: str = "",
                        emails: List[str] = None,
                        tecnologias: List[str] = None) -> Dict:
        """
        Gera wordlist contextual completa para o alvo.
        Combina: nome da empresa, domínio, padrões comuns, anos, variações.
        """
        palavras = set()

        # Extrai tokens do domínio
        tokens = self._tokenizar_dominio(dominio)
        if empresa:
            tokens.extend(self._tokenizar_nome(empresa))

        # Extrai usuários dos emails
        usuarios = []
        for email in (emails or []):
            local = email.split("@")[0]
            usuarios.append(local)
            tokens.extend(self._tokenizar_nome(local))

        # Gera variações para senhas
        palavras.update(self._variações_senha(tokens))

        # Gera usernames
        usernames = self._gerar_usernames(usuarios or tokens[:3])

        # Diretórios para web
        diretorios = self._diretorios_contextuais(dominio, tecnologias or [])

        # Subdomínios prováveis
        subdominios = self._subdominios_provaveis(dominio, tokens)

        resultado = {
            "alvo":          dominio,
            "timestamp":     datetime.datetime.now().isoformat(),
            "senhas":        sorted(palavras)[:500],
            "usernames":     usernames[:100],
            "diretorios":    diretorios[:300],
            "subdominios":   subdominios[:100],
            "total_senhas":  len(palavras),
        }

        self._salvar_wordlists(resultado, dominio)
        return resultado

    def gerar_senhas(self, palavras_base: List[str],
                     nivel: str = "medio") -> List[str]:
        """
        Gera variações de senha para uma lista de palavras base.
        nivel: basico | medio | avancado
        """
        senhas = set()
        for palavra in palavras_base[:10]:
            senhas.update(self._variações_senha([palavra]))
            if nivel in ("medio", "avancado"):
                senhas.update(self._combinacoes_duplas([palavra]))
            if nivel == "avancado":
                senhas.update(self._mascaras_avancadas(palavra))
        return sorted(senhas)[:1000]

    def gerar_usernames(self, nome_completo: str) -> List[str]:
        """Gera variações de username para um nome completo."""
        partes = nome_completo.lower().split()
        if not partes:
            return []
        return self._gerar_usernames(partes)

    def wordlist_diretorios(self, tecnologias: List[str],
                            custom: List[str] = None) -> List[str]:
        """Wordlist de diretórios baseada nas tecnologias detectadas."""
        return self._diretorios_contextuais("", tecnologias, custom or [])

    def salvar_arquivo(self, palavras: List[str],
                       nome: str = "wordlist.txt") -> str:
        """Salva wordlist em arquivo."""
        destino = (self.root / "memory" / "feedback" / nome) if self.root \
                  else Path(nome)
        destino.write_text("\n".join(palavras), encoding="utf-8")
        return str(destino)

    # ── Geradores ─────────────────────────────────────────────────────────

    def _tokenizar_dominio(self, dominio: str) -> List[str]:
        """Extrai tokens relevantes do domínio."""
        # Remove TLD e www
        base = re.sub(r"\.(com|net|org|io|br|co|gov|edu).*$", "", dominio)
        base = re.sub(r"^www\.", "", base)
        # Divide por separadores
        tokens = re.split(r"[.\-_]", base)
        return [t.lower() for t in tokens if len(t) > 2]

    def _tokenizar_nome(self, nome: str) -> List[str]:
        """Extrai tokens de um nome ou texto."""
        tokens = re.split(r"[\s.\-_@]", nome.lower())
        return [t for t in tokens if len(t) > 2]

    def _variações_senha(self, tokens: List[str]) -> List[str]:
        """Gera variações realistas de senha."""
        senhas = set()
        anos   = ["2023", "2024", "2025", "!", "@", "#", "123", "1234"]
        leet   = {"a":"@", "e":"3", "i":"1", "o":"0", "s":"$"}

        for token in tokens[:8]:
            t   = token.lower()
            tC  = t.capitalize()
            tU  = t.upper()

            # Básicas
            senhas.update([t, tC, tU])

            # Com números
            for ano in anos:
                senhas.update([
                    f"{tC}{ano}", f"{t}{ano}", f"{ano}{tC}",
                    f"{tC}{ano}!", f"{tC}@{ano}",
                ])

            # Com símbolos
            for sym in ["!", "@", "#", ".", "_"]:
                senhas.update([f"{tC}{sym}", f"{tC}{sym}123",
                               f"{t}{sym}", f"{sym}{tC}"])

            # Leet speak
            t_leet = t
            for char, sub in leet.items():
                t_leet = t_leet.replace(char, sub)
            if t_leet != t:
                senhas.add(t_leet)
                senhas.add(t_leet.capitalize())

        # Senhas comuns absolutas
        senhas.update([
            "123456", "password", "admin", "admin123", "root",
            "toor", "pass", "test", "guest", "letmein",
            "qwerty", "abc123", "Password1", "Welcome1",
        ])

        return [s for s in senhas if 4 <= len(s) <= 30]

    def _combinacoes_duplas(self, tokens: List[str]) -> List[str]:
        """Combina dois tokens para senhas compostas."""
        senhas = set()
        for a, b in itertools.combinations(tokens[:5], 2):
            senhas.update([
                f"{a}{b}", f"{a.capitalize()}{b}",
                f"{a}{b.capitalize()}", f"{a}_{b}",
                f"{a.capitalize()}{b.capitalize()}",
                f"{a}{b}123", f"{a.capitalize()}{b}!",
            ])
        return list(senhas)

    def _mascaras_avancadas(self, token: str) -> List[str]:
        """Variações avançadas com padrões de mascara."""
        senhas = set()
        t = token.capitalize()
        # Padrões comuns corporativos
        for mes in ["01","02","03","04","05","06","07","08","09","10","11","12"]:
            for ano in ["23","24","25"]:
                senhas.update([
                    f"{t}{mes}{ano}", f"{t}@{mes}{ano}",
                    f"{t}{mes}/20{ano}",
                ])
        return list(senhas)

    def _gerar_usernames(self, tokens: List[str]) -> List[str]:
        """Gera variações de username."""
        users = set()
        if not tokens:
            return []

        if len(tokens) >= 2:
            a, b = tokens[0], tokens[1]
            users.update([
                f"{a}.{b}", f"{a}_{b}", f"{a}{b}",
                f"{a[0]}{b}", f"{a}.{b[0]}", f"{a[0]}.{b}",
                f"{b}.{a}", f"{b}{a[0]}", f"{a[0:2]}{b}",
                a, b,
            ])

        # Adiciona token único se só um
        for t in tokens[:3]:
            users.update([t, f"{t}1", f"{t}01", f"admin", f"root",
                          f"administrator", f"user", f"guest", f"test"])

        return sorted(users)

    def _diretorios_contextuais(self, dominio: str,
                                tecnologias: List[str],
                                custom: List[str] = None) -> List[str]:
        """Gera wordlist de diretórios baseada no contexto."""
        dirs = set(custom or [])

        # Base universal
        dirs.update([
            "admin", "administrator", "login", "logout", "dashboard",
            "api", "api/v1", "api/v2", "swagger", "swagger-ui",
            "docs", "documentation", "backup", "backups", "db",
            "config", "configuration", ".env", ".git", ".git/config",
            "uploads", "files", "images", "assets", "static",
            "wp-admin", "wp-login.php", "wp-content", "wordpress",
            "phpmyadmin", "pma", "mysql", "phpinfo.php",
            "console", "shell", "cmd", "terminal",
            "test", "testing", "dev", "development", "staging",
            "old", "backup.zip", "backup.tar.gz", "www.zip",
            "robots.txt", "sitemap.xml", ".htaccess",
            "server-status", "server-info",
            "actuator", "actuator/env", "actuator/health",  # Spring Boot
            "graphql", "graphiql", "__graphql",
            "metrics", "health", "status", "ping",
            "private", "secret", "hidden", "internal",
        ])

        # Por tecnologia
        tech_dirs = {
            "wordpress": ["wp-admin", "wp-includes", "wp-content/uploads",
                         "wp-config.php", "xmlrpc.php"],
            "php":       ["phpinfo.php", "info.php", "test.php",
                         "shell.php", "admin.php"],
            "java":      ["WEB-INF", "META-INF", "actuator",
                         "struts", "faces"],
            "python":    ["admin/", "django-admin", "flask-debug"],
            "nginx":     ["nginx.conf", "vhost.conf"],
            "apache":    [".htaccess", ".htpasswd", "server-status"],
            "laravel":   ["storage", "telescope", "horizon", "_ignition"],
            "rails":     ["rails/info", "admin", "sidekiq"],
            "node":      ["node_modules", ".npmrc", "package.json"],
        }

        for tech in tecnologias:
            for t, extra_dirs in tech_dirs.items():
                if t in tech.lower():
                    dirs.update(extra_dirs)

        return sorted(dirs)

    def _subdominios_provaveis(self, dominio: str,
                                tokens: List[str]) -> List[str]:
        """Gera lista de subdomínios prováveis."""
        base = [
            "www", "mail", "webmail", "email", "smtp", "pop", "imap",
            "ftp", "sftp", "ssh", "vpn", "remote",
            "admin", "administrator", "panel", "cp", "cpanel", "whm",
            "dev", "development", "staging", "test", "testing", "qa",
            "api", "api2", "api-v2", "rest", "graphql",
            "static", "assets", "cdn", "media", "img", "images",
            "blog", "shop", "store", "app",
            "internal", "intranet", "private",
            "ns1", "ns2", "dns", "mx", "mail2",
            "backup", "old", "legacy",
            "monitor", "status", "metrics", "grafana", "kibana",
            "gitlab", "git", "ci", "jenkins", "travis",
            "jira", "confluence", "wiki",
        ]

        # Adiciona tokens do alvo
        for token in tokens[:5]:
            base.extend([token, f"{token}-api", f"{token}-admin",
                         f"api-{token}", f"dev-{token}"])

        return [f"{sub}.{dominio}" for sub in base]

    def _salvar_wordlists(self, resultado: Dict, dominio: str):
        if not self.dir_output:
            return
        # Salva senhas
        arq = self.dir_output / f"wordlist_senhas_{dominio}.txt"
        arq.write_text("\n".join(resultado["senhas"]), encoding="utf-8")
        # Salva diretórios
        arq2 = self.dir_output / f"wordlist_dirs_{dominio}.txt"
        arq2.write_text("\n".join(resultado["diretorios"]), encoding="utf-8")
        # Salva subdomínios
        arq3 = self.dir_output / f"wordlist_subs_{dominio}.txt"
        arq3.write_text("\n".join(resultado["subdominios"]), encoding="utf-8")
