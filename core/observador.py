"""
observador.py — Observador de Eventos do Libertus

Monitora o vault por mudanças e reage automaticamente.
Rodado como thread dentro do daemon ou standalone.

Eventos detectados:
- Novo arquivo .md criado pelo usuário → absorção automática
- Arquivo modificado → reavaliação de contexto
- Nova skill salva → validação automática
"""

import time, json, hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Callable


class Observador:
    """
    Watcher de arquivos que roda em background.
    Detecta mudanças e dispara callbacks correspondentes.
    """

    PASTAS_OBSERVADAS = ["memoria", "evolucao", "skills", "projetos", "erros"]

    def __init__(self, root: Path):
        self.root = root
        self.state_file = root / "memory" / "observer_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.estado: Dict[str, str] = self._carregar_estado()
        self.callbacks: Dict[str, Callable] = {}
        self.rodando = True

    def registrar_callback(self, evento: str, callback: Callable):
        """
        Registra callback para um tipo de evento.
        Eventos: novo_arquivo, arquivo_modificado, arquivo_removido
        """
        self.callbacks[evento] = callback

    def escanear_uma_vez(self) -> Dict:
        """
        Faz uma varredura e retorna mudanças detectadas.
        Não bloqueia — rápido o suficiente para rodar a cada 60s.
        """
        mudancas = {"novos": [], "modificados": [], "removidos": []}
        novo_estado = {}

        for pasta in self.PASTAS_OBSERVADAS:
            dir_pasta = self.root / pasta
            if not dir_pasta.exists():
                continue

            for arq in dir_pasta.glob("*.md"):
                chave = str(arq.relative_to(self.root))
                try:
                    hash_atual = self._hash_arquivo(arq)
                    novo_estado[chave] = hash_atual

                    if chave not in self.estado:
                        mudancas["novos"].append(chave)
                        self._disparar("novo_arquivo", chave, arq)
                    elif self.estado[chave] != hash_atual:
                        mudancas["modificados"].append(chave)
                        self._disparar("arquivo_modificado", chave, arq)
                except Exception:
                    continue

        # Detecta removidos
        for chave in self.estado:
            if chave not in novo_estado:
                mudancas["removidos"].append(chave)
                self._disparar("arquivo_removido", chave, None)

        # Salva novo estado
        self.estado = novo_estado
        self._salvar_estado()

        return mudancas

    def rodar_continuo(self, intervalo: int = 60):
        """
        Loop contínuo — checa arquivos a cada N segundos.
        Usado quando o observador roda como thread.
        """
        while self.rodando:
            try:
                self.escanear_uma_vez()
                time.sleep(intervalo)
            except Exception:
                time.sleep(intervalo)

    def parar(self):
        """Para o loop contínuo."""
        self.rodando = False

    # ── Internos ──────────────────────────────────────────────────────────

    def _hash_arquivo(self, arq: Path) -> str:
        """Hash MD5 do conteúdo do arquivo para detectar modificações."""
        try:
            return hashlib.md5(arq.read_bytes()).hexdigest()
        except Exception:
            return ""

    def _carregar_estado(self) -> Dict:
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _salvar_estado(self):
        try:
            self.state_file.write_text(
                json.dumps(self.estado, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    def _disparar(self, evento: str, chave: str, arq):
        """Dispara callback se registrado."""
        callback = self.callbacks.get(evento)
        if callback:
            try:
                callback(chave, arq)
            except Exception:
                pass
