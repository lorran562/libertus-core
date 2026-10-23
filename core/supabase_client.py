import time
from functools import wraps

def retry_on_error(max_retries=3, delay=2):
    """Retry decorator para operações Supabase"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"[RETRY] {func.__name__} falhou (tentativa {attempt+1}/{max_retries}): {e}")
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator

"""
supabase_client.py — Memória Executável do Libertus
Gerencia skills, memórias, sessões e padrões no Supabase.
"""

import httpx, json, datetime, time
from typing import List, Dict, Any, Optional


SB_URL = "https://jkgrmlfqgprcwfooovkx.supabase.co"
SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImprZ3JtbGZxZ3ByY3dmb29vdmt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMyNTY4NTIsImV4cCI6MjA4ODgzMjg1Mn0.f0N9ase2ZoYKq4JL7zVT9rzrjjsslYMPLcwd-k5Z8DA"
SKILL_THRESHOLD = 3


class Supabase:
    def __init__(self):
        self.h = {
            "apikey": SB_KEY,
            "Authorization": f"Bearer {SB_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self.b = SB_URL + "/rest/v1"
        try:
            # Retry com backoff: um blip de TLS/DNS no boot matava o daemon
            # inteiro (ConnectionError -> watchdog restart a cada 60s).
            # Visto em 18/10: "certificate is not yet valid" transitório.
            ultimo_erro = None
            for tentativa in range(3):
                try:
                    r = httpx.get(f"{self.b}/libertus_skills?limit=1",
                                  headers=self.h, timeout=8)
                    if r.status_code < 500:
                        ultimo_erro = None
                        break
                except Exception as e:
                    ultimo_erro = e
                    time.sleep(2 * (tentativa + 1))
            if ultimo_erro is not None:
                raise ConnectionError(f"Supabase falhou: {ultimo_erro}")
        except ConnectionError:
            raise
        except Exception as e:
            raise ConnectionError(f"Supabase falhou: {e}")

    # ── CRUD básico ───────────────────────────────────────────────────────

    def get(self, t: str, q: str = "") -> List[Dict]:
        try:
            r = httpx.get(f"{self.b}/{t}?{q}", headers=self.h, timeout=15)
            return r.json() if r.status_code == 200 else []
        except:
            return []

    def post(self, t: str, d: Dict) -> Dict:
        try:
            r = httpx.post(f"{self.b}/{t}", headers=self.h,
                           json=d, timeout=15)
            data = r.json() if r.text else {}
            return data[0] if isinstance(data, list) and data else data
        except:
            return {}

    def patch(self, t: str, f: str, d: Dict):
        try:
            httpx.patch(f"{self.b}/{t}?{f}", headers=self.h,
                        json=d, timeout=15)
        except:
            pass

    def upsert(self, t: str, d: Dict, conflict: str = "name") -> bool:
        try:
            h = {**self.h,
                 "Prefer": "resolution=merge-duplicates,return=representation"}
            r = httpx.post(f"{self.b}/{t}", headers=h, json=d, timeout=15)
            return r.status_code in (200, 201)
        except:
            return False

    def rpc(self, fn: str, params: Dict) -> Any:
        try:
            r = httpx.post(f"{SB_URL}/rest/v1/rpc/{fn}",
                           headers=self.h, json=params, timeout=15)
            return r.json() if r.status_code == 200 else None
        except:
            return None

    # ── SKILL ENGINE ──────────────────────────────────────────────────────

    def buscar_skill_relevante(self, tarefa: str,
                               limite: int = 5) -> List[Dict]:
        palavras = [w for w in tarefa.lower().split() if len(w) > 3][:4]
        results, seen = [], set()

        for p in palavras:
            rows = self.rpc("buscar_skill_relevante",
                            {"p_query": p, "p_limit": 3})
            if isinstance(rows, list):
                for row in rows:
                    nome = row.get("nome", "")
                    if nome and nome not in seen:
                        seen.add(nome); results.append(row)

        if not results:
            kw = palavras[0] if palavras else tarefa[:10]
            for tabela, campos in [
                ("libertus_skills",
                 "name,description,category,code,parametros,score"),
                ("agent_skills",
                 "name,description,category,code,inputs,usage_count"),
            ]:
                rows = self.get(
                    tabela,
                    f"select={campos}&ativo=eq.true"
                    f"&description=ilike.*{kw}*&order=score.desc&limit=3"
                )
                for row in rows:
                    nome = row.get("name", "")
                    if nome and nome not in seen:
                        seen.add(nome)
                        results.append({
                            "nome":      nome,
                            "descricao": row.get("description", ""),
                            "categoria": row.get("category", ""),
                            "codigo":    row.get("code", ""),
                            "parametros":row.get("parametros",
                                                  row.get("inputs", {})),
                            "score":     float(row.get("score",
                                               row.get("usage_count", 0))),
                            "sistema":   tabela.split("_")[0],
                        })

        results.sort(key=lambda x: float(x.get("score", 0) or 0),
                     reverse=True)
        return results[:limite]

    def executar_skill_code(self, skill: Dict, tarefa: str,
                            params: Dict = None) -> Dict:
        """Executa skill com análise de segurança prévia."""
        from seguranca import Seguranca
        sec = Seguranca()

        codigo = skill.get("codigo", skill.get("code", ""))
        if not codigo:
            return {"status": "skip", "resultado": "Sem código", "usou_skill": False}

        ok_seg, alertas = sec.analisar(codigo)

        t0 = time.time()
        try:
            import subprocess as _sp, re as _re
            from pathlib import Path as _Path
            ctx = {
                "tarefa": tarefa, "params": params or {},
                "resultado": None, "Path": _Path,
                "json": json, "subprocess": _sp,
                "datetime": datetime, "time": time, "re": _re,
            }
            exec(compile(codigo, f"skill_{skill.get('nome','?')}", "exec"), ctx)
            duracao = int((time.time() - t0) * 1000)
            resultado = ctx.get("resultado", "Executado")
            self.rpc("registrar_uso_skill", {
                "p_name": skill.get("nome", ""),
                "p_sucesso": True, "p_duracao_ms": duracao
            })
            return {
                "status": "done",
                "resultado": str(resultado)[:1500],
                "skill_usada": skill.get("nome", ""),
                "duracao_ms": duracao,
                "usou_skill": True,
                "alertas_seg": alertas,
            }
        except Exception as e:
            self.rpc("registrar_uso_skill", {
                "p_name": skill.get("nome", ""),
                "p_sucesso": False, "p_duracao_ms": 0
            })
            return {"status": "failed", "resultado": f"Erro: {e}",
                    "usou_skill": False}

    def salvar_skill_completa(self, name: str, description: str,
                              category: str, executor: str,
                              code: str, parameters: Dict = None,
                              tags: List = None, origem: str = "claude") -> bool:
        existente = self.get("libertus_skills",
                             f"name=eq.{name}&select=id,version,uso_count")
        if existente:
            v = existente[0].get("version", 1)
            self.patch("libertus_skills", f"name=eq.{name}", {
                "description": description, "code": code,
                "parametros": parameters or {}, "tags": tags or [],
                "version": v + 1,
                "updated_at": datetime.datetime.now().isoformat(),
            })
            return True

        return self.upsert("libertus_skills", {
            "name": name, "description": description,
            "category": category, "executor": executor,
            "code": code, "parametros": parameters or {},
            "tags": tags or [], "origem": origem,
            "version": 1, "score": 5.0, "uso_count": 0, "ativo": True,
        })

    # ── MEMÓRIA ───────────────────────────────────────────────────────────

    def salvar_execucao(self, sid, inp, plano, resultado,
                        executor, ms, obs="", apr=""):
        return self.post("libertus_sessoes", {
            "session_id": sid, "input": inp, "plano": plano,
            "resultado": resultado, "executor": executor,
            "duracao_ms": ms, "obsidian_path": obs,
            "aprendizado": apr, "status": "done",
        })

    def salvar_memoria(self, titulo, conteudo, tipo="execucao",
                       tags=None, relevancia=5):
        return self.post("libertus_memoria", {
            "titulo": titulo, "conteudo": conteudo,
            "tipo": tipo, "tags": tags or [], "relevancia": relevancia,
        })

    def get_skills(self) -> List[Dict]:
        return self.get("libertus_skills",
                        "order=score.desc,uso_count.desc&limit=50&ativo=eq.true")

    def get_memorias(self, limit: int = 10) -> List[Dict]:
        return self.get("libertus_memoria",
                        f"order=relevancia.desc&limit={limit}")

    def get_sessoes(self, limit: int = 5) -> List[Dict]:
        return self.get("libertus_sessoes",
                        f"order=created_at.desc&limit={limit}"
                        f"&select=input,executor,status,duracao_ms")
