#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIBERTUS v8.0 — Entidade Autônoma e Autoevolutiva
Novidades: IntentClassifier + Avaliador + Loop cognitivo completo
"""

import os, sys, json, time, uuid, datetime, re
from pathlib import Path
from typing import Optional, Dict, List, Any

LIBERTUS_ROOT = Path(__file__).parent.parent.resolve()
os.environ.setdefault("LIBERTUS_OBSIDIAN", str(LIBERTUS_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MODO_AUTONOMO = "--sem-claude" in sys.argv
MODO_STATUS   = "--status"    in sys.argv
for _f in ["--sem-claude", "--ensinar", "--status"]:
    if _f in sys.argv: sys.argv.remove(_f)

try:
    import httpx
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    print("pip3 install httpx colorama --break-system-packages"); sys.exit(1)

try:
    import anthropic
    CLAUDE_OK = True
except ImportError:
    CLAUDE_OK = False

sys.path.insert(0, str(Path(__file__).parent))

def _imp(nome):
    try: return __import__(nome)
    except ImportError: return None

from supabase_client import Supabase
from memoria_local   import MemoriaLocal
from seguranca       import Seguranca
from absorvedor      import Absorvedor
from groq_client     import Groq
from ollama_client   import Ollama
from motor_decisao   import MotorDecisao
from sistema_objetivos import SistemaObjetivos, Prazo
from auto_evolucao   import AutoEvolucao
from executor        import Executor
from git_sync        import GitSync
from eng_reversa     import EngenheiriaReversa
from intent_classifier import IntentClassifier
from libertus_daemon import NucleoCognitivo
from avaliador       import Avaliador

_s = _imp("scanner");  _r = _imp("reconhecimento")
_m = _imp("metodologia"); _w = _imp("wordlist_engine")
Scanner        = getattr(_s,"Scanner",None)
Reconhecimento = getattr(_r,"Reconhecimento",None)
Metodologia    = getattr(_m,"Metodologia",None)
WordlistEngine = getattr(_w,"WordlistEngine",None)

ANT_KEY  = os.environ.get("ANTHROPIC_API_KEY","")
GROQ_KEY = os.environ.get("GROQ_API_KEY","")
OLL_URL  = os.environ.get("OLLAMA_URL","http://localhost:11434")

C=Fore.CYAN;G=Fore.GREEN;Y=Fore.YELLOW;R=Fore.RED
M=Fore.MAGENTA;W=Fore.WHITE;X=Style.RESET_ALL

def ts(): return datetime.datetime.now().strftime("%H:%M:%S")
def log(msg,k="info"):
    ic={"info":(C,"i"),"ok":(G,chr(10003)),"warn":(Y,"!"),"error":(R,"x"),
        "claude":(M,"C"),"exec":(C,"E"),"mem":(G,"M"),"skill":(M,"S"),
        "learn":(G,"L"),"sec":(R,"#"),"groq":(G,"G"),"intent":(Y,">"),"eval":(C,"*")}
    col,ico=ic.get(k,(W,"."))
    print(f"[{ts()}] {col}{ico} {msg}{X}")


class Claude:
    SYSTEM = """Você é o PROFESSOR do LIBERTUS — IA pessoal de Lorran de Ariquemes-RO.
Para tarefas técnicas, responda com skill Python reutilizável no formato:
```skill
NOME: nome_snake_case
CATEGORIA: automacao|web|sistema|seguranca|dados
DESCRICAO: uma linha
PARAMETROS: {}
TAGS: []
CODIGO:
resultado = "saída"
```
Para conversas, responda naturalmente em português."""

    def __init__(self):
        if not CLAUDE_OK or not ANT_KEY:
            raise ImportError("sem API key")
        self.c = anthropic.Anthropic(api_key=ANT_KEY)
        self.model = "claude-sonnet-4-6"

    def pensar(self, prompt: str, max_tokens: int = 4096) -> str:
        try:
            r = self.c.messages.create(
                model=self.model, max_tokens=max_tokens,
                system=self.SYSTEM,
                messages=[{"role":"user","content":prompt}])
            return r.content[0].text
        except Exception as e:
            if "credit" in str(e).lower(): log("Claude sem credito","warn"); return ""
            raise


class Orquestrador:
    def __init__(self):
        log("Iniciando LIBERTUS v8.0...","info")
        log(f"Root: {LIBERTUS_ROOT}","info")
        self.sb  = Supabase()
        self.mem = MemoriaLocal(LIBERTUS_ROOT)
        self.clf = IntentClassifier()
        self.decisao  = MotorDecisao(LIBERTUS_ROOT)
        self.obj      = SistemaObjetivos(LIBERTUS_ROOT)
        self.evolucao = AutoEvolucao(LIBERTUS_ROOT)
        self.avaliador = Avaliador(LIBERTUS_ROOT)
        self.seg      = Seguranca()
        self.abs      = Absorvedor(LIBERTUS_ROOT)
        self.executor = Executor(LIBERTUS_ROOT, self.seg)
        self.git      = GitSync(LIBERTUS_ROOT)
        self.er       = EngenheiriaReversa(LIBERTUS_ROOT)
        self.scanner  = Scanner(LIBERTUS_ROOT)   if Scanner   else None
        self.recon    = Reconhecimento(LIBERTUS_ROOT) if Reconhecimento else None
        self.metodo   = Metodologia(LIBERTUS_ROOT)   if Metodologia   else None
        self.wordlist = WordlistEngine(LIBERTUS_ROOT) if WordlistEngine else None
        self.groq   = Groq(GROQ_KEY) if GROQ_KEY else None
        self.ollama = Ollama(OLL_URL)
        self.claude: Optional[Claude] = None
        if not MODO_AUTONOMO and CLAUDE_OK and ANT_KEY:
            try: self.claude = Claude(); log("Claude API OK","ok")
            except Exception as e: log(f"Claude offline: {e}","warn")
        if self.groq: log("Groq API disponivel (llama3-70b)","ok")
        self._stats = {"total":0,"skill":0,"groq":0,"ollama":0,"claude":0,"autonomo":0}

    def processar(self, entrada: str) -> str:
        self._stats["total"] += 1
        sid = str(uuid.uuid4())[:8]
        t0  = time.time()

        intent = self.clf.classificar(entrada)
        log(f"Intencao: {self.clf.resumo(intent)}","intent")
        ctx_local = self.mem.buscar_contexto(entrada)
        resultado = ""; executor_usado = "fallback"

        if intent.tipo == "pentest_completo" and intent.alvo:
            resultado = self._pentest(intent); executor_usado = "pentest"
            self._stats["autonomo"] += 1
        elif intent.tipo == "recon" and intent.alvo:
            resultado = self._recon(intent); executor_usado = "recon"
            self._stats["autonomo"] += 1
        elif intent.tipo == "scan" and intent.alvo:
            resultado = self._scan(intent); executor_usado = "scan"
            self._stats["autonomo"] += 1
        elif intent.tipo == "wordlist" and intent.alvo:
            resultado = self._wordlist(intent); executor_usado = "wordlist"
            self._stats["autonomo"] += 1
        elif intent.tipo == "analisar_codigo":
            resultado = self._eng_reversa(intent, entrada); executor_usado = "eng_reversa"
            self._stats["autonomo"] += 1
        elif intent.tipo == "evolucao":
            plano = self.evolucao.ciclo(self.sb, self.mem)
            resultado = self._fmt_evolucao(plano); executor_usado = "evolucao"
        elif intent.tipo == "absorver" and intent.alvo:
            resultado = self.abs.processar(intent.alvo); executor_usado = "absorvedor"
        else:
            skills = self.sb.buscar_skill_relevante(entrada)
            if skills and intent.tipo != "conversa":
                skill = skills[0]
                log(f"Skill: {skill.get('nome','?')}","skill")
                res = self.sb.executar_skill_code(skill, entrada)
                if res.get("status") == "done":
                    resultado = res["resultado"]; executor_usado = "skill"
                    self._stats["skill"] += 1
            if not resultado and self.groq:
                resultado = self.groq.conversar(entrada, ctx_local)
                executor_usado = "groq"; self._stats["groq"] += 1
            if not resultado and self.claude and not MODO_AUTONOMO:
                log("Chamando Claude...","claude")
                resposta = self.claude.pensar(self._ctx(entrada, ctx_local))
                if resposta:
                    resultado = resposta; executor_usado = "claude"; self._stats["claude"] += 1
                    sk = self._extrair_skill(resposta)
                    if sk: self.sb.salvar_skill_completa(**sk, origem="claude"); log(f"Skill: {sk['name']}","learn")
            if not resultado and self.ollama.model:
                resultado = self.ollama.gerar(entrada, ctx_local)
                executor_usado = "ollama"; self._stats["ollama"] += 1
            if not resultado:
                resultado = "Sem executor disponivel. Configure GROQ_API_KEY."

        duracao = int((time.time() - t0) * 1000)
        aval = self.avaliador.avaliar(entrada, resultado, executor_usado, duracao)
        score_val = aval.get('score', 0)
        diag_val  = aval.get('diagnostico', '')
        log(f"Score: {score_val}/10 | {diag_val}", "eval")

        if aval.get("score", 0) >= 7 and executor_usado not in ("groq","conversa"):
            self.mem.salvar_aprendizado(f"exec_{executor_usado}", f"Tarefa: {entrada[:80]}", skill=executor_usado)

        score_final = aval.get('score', 0)
        self.sb.salvar_execucao(sid, entrada,
            {"executor":executor_usado,"intent":intent.tipo},
            {"resultado":str(resultado)[:600],"score":score_final},
            executor_usado, duracao, "", f"v8|score:{score_final}")
        return resultado

    def _pentest(self, intent) -> str:
        alvo = intent.alvo; partes = []
        log(f"Pentest autonomo: {alvo}","exec")
        if self.recon:
            log("Fase 1/4: Reconhecimento...","exec")
            d = self.recon.analisar_dominio(alvo)
            partes.append("## RECONHECIMENTO\n" + self.recon.gerar_relatorio(d))
        if self.scanner:
            log("Fase 2/4: Scan web...","exec")
            d = self.scanner.scan_web(f"https://{alvo}")
            partes.append("## SCAN WEB\n" + self.scanner.interpretar(d))
            log("Fase 3/4: Scan portas...","exec")
            d = self.scanner.scan_rapido(alvo)
            partes.append("## PORTAS\n" + self.scanner.interpretar(d))
        if self.metodo:
            log("Fase 4/4: Findings...","exec")
            eng = self.metodo.iniciar_engajamento(alvo)
            for _ in range(4):
                eng = self.metodo.executar_fase(eng, recon=self.recon, scanner=self.scanner)
            partes.append("## RELATORIO\n" + self.metodo.resumo(eng))
        if not partes:
            return f"Modulos de seguranca nao disponiveis. pip3 install httpx"
        rel = f"# RELATORIO DE SEGURANCA — {alvo}\nData: {datetime.datetime.now():%Y-%m-%d %H:%M}\n\n"
        rel += "\n\n".join(partes)
        self.mem.salvar("projetos", f"pentest_{alvo}", rel, ["pentest", alvo])
        return rel

    def _recon(self, intent) -> str:
        if not self.recon: return "Modulo reconhecimento nao disponivel."
        d = self.recon.analisar_dominio(intent.alvo)
        return self.recon.gerar_relatorio(d)

    def _scan(self, intent) -> str:
        if not self.scanner: return "Modulo scanner nao disponivel."
        d = self.scanner.scan_rapido(intent.alvo)
        return self.scanner.interpretar(d)

    def _wordlist(self, intent) -> str:
        if not self.wordlist: return "Modulo wordlist nao disponivel."
        r = self.wordlist.gerar_para_alvo(intent.alvo)
        return (f"Wordlists para {intent.alvo}:\n"
                f"  Senhas: {r['total_senhas']}\n"
                f"  Diretorios: {len(r['diretorios'])}\n"
                f"  Subdominios: {len(r['subdominios'])}\n"
                f"Salvo em: {LIBERTUS_ROOT}/memory/feedback/")

    def _eng_reversa(self, intent, entrada) -> str:
        alvo = intent.alvo
        if alvo and Path(alvo).exists():
            r = self.er.analisar(caminho=alvo, contexto=entrada)
        else:
            codigo = re.search(r"```[\w]*\n(.*?)```", entrada, re.DOTALL)
            if codigo: r = self.er.analisar(codigo=codigo.group(1), contexto=entrada)
            else: return "Forneca caminho de arquivo ou codigo entre ``` para analisar."
        self.er.salvar_no_vault(r, alvo or "analise")
        return r["resumo"] + "\n\n" + "\n".join(
            f"[{m['prioridade'].upper()}] {m['titulo']}: {m['descricao']}"
            for m in r["melhorias"])

    def _fmt_evolucao(self, plano) -> str:
        ops = plano.get("oportunidades",[])
        linhas = [f"=== CICLO DE EVOLUCAO ===", f"Oportunidades: {len(ops)}"]
        for o in ops: linhas.append(f"  [{o['prioridade']}] {o['descricao']}")
        linhas.append(self.evolucao.historico(3))
        return "\n".join(linhas)

    def _ctx(self, tarefa, ctx_local) -> str:
        sks = self.sb.buscar_skill_relevante(tarefa)
        sk = "\n".join(f"- {s.get('nome','?')}: {s.get('descricao','')[:50]}" for s in sks[:3]) or "Nenhuma"
        return f"TAREFA: {tarefa}\n\nCONTEXTO:\n{ctx_local[:300] if ctx_local else 'Nenhum'}\n\nSKILLS:\n{sk}"

    def _extrair_skill(self, texto) -> Optional[Dict]:
        m = re.search(r"```skill\s*(.*?)```", texto, re.DOTALL)
        if not m: return None
        bloco = m.group(1).strip(); sk = {}
        for campo, chave in [("NOME","name"),("CATEGORIA","category"),("DESCRICAO","description"),("PARAMETROS","parameters"),("TAGS","tags")]:
            pm = re.search(rf"^{campo}:\s*(.+)$", bloco, re.MULTILINE)
            if pm:
                val = pm.group(1).strip()
                if chave in ("parameters","tags"):
                    try: sk[chave] = json.loads(val)
                    except: sk[chave] = {} if chave=="parameters" else []
                else: sk[chave] = val
        cm = re.search(r"CODIGO:\s*(.*?)(?=\Z)", bloco, re.DOTALL)
        if cm: sk["code"] = cm.group(1).strip()
        return sk if sk.get("name") and sk.get("code") else None

    def _score_autonomia(self) -> str:
        t = self._stats["total"]
        if not t: return "N/A"
        sem = sum(self._stats[k] for k in ["skill","groq","ollama","autonomo"])
        return f"{int(sem/t*100)}% autonomo | auto:{self._stats['autonomo']} skill:{self._stats['skill']} groq:{self._stats['groq']} claude:{self._stats['claude']}"


def main():
    orch = Orquestrador()
    if MODO_STATUS:
        skills = orch.sb.get_skills()
        aut = sum(1 for s in skills if s.get("executor")=="libertus")
        mems = orch.sb.get("libertus_memoria","select=id&limit=500")
        print(f"\n{C}=== LIBERTUS v8.0 STATUS ==={X}")
        print(f"Root:      {G}{LIBERTUS_ROOT}{X}")
        print(f"Skills:    {G}{len(skills)}{X} | {G}{aut}{X} autonomas")
        print(f"Memorias:  {G}{len(mems)}{X}")
        print(f"Claude:    {G+'OK'+X if orch.claude else R+'offline'+X}")
        print(f"Groq:      {G+'OK'+X if orch.groq else Y+'sem chave'+X}")
        print(f"Ollama:    {G+orch.ollama.model+X if orch.ollama.model else Y+'offline'+X}")
        print(f"Scanner:   {G+'OK'+X if orch.scanner else Y+'nao disponivel'+X}")
        print(f"Recon:     {G+'OK'+X if orch.recon else Y+'nao disponivel'+X}")
        print(f"Objetivos: {G}{len(orch.obj.listar())}{X} ativos")
        print(f"Obsidian:  {G}{LIBERTUS_ROOT}{X}\n")
        return

    # Verifica se daemon está rodando e mostra resumo
    try:
        nucleo = NucleoCognitivo.__new__(NucleoCognitivo)
        nucleo.root = LIBERTUS_ROOT
        resumo = nucleo.resumo_ao_acordar()
        print(f"\n{M}{'='*60}{X}")
        for linha in resumo.split("\n"):
            print(f"{M}  {linha}{X}")
        print(f"{M}{'='*60}{X}")
    except Exception:
        pass

    print(f"\n{C}{'='*60}{X}")
    print(f"{C}  LIBERTUS v8.0 — Fale naturalmente, eu executo{X}")
    print(f"{C}{'='*60}{X}")
    print(f"  Root: {LIBERTUS_ROOT}")
    print(f"  /status /skills /ensinar /absorver /evolucao /sair")
    print(f"{C}{'='*60}{X}\n")

    while True:
        try:
            entrada = input(f"{C}Voce > {X}").strip()
            if not entrada: continue
            if entrada == "/sair":
                print(f"\n{G}Encerrado. {orch._score_autonomia()}{X}"); break
            elif entrada == "/status":
                skills = orch.sb.get_skills()
                aut = sum(1 for s in skills if s.get("executor")=="libertus")
                print(f"\nSkills: {G}{len(skills)}{X} | {G}{aut}{X} autonomas | {G}{orch._score_autonomia()}{X}\n")
            elif entrada.startswith("/skills"):
                busca = entrada.replace("/skills","").strip()
                skills = orch.sb.get_skills()
                if busca: skills = [s for s in skills if busca.lower() in (s.get("name","")+s.get("description","")).lower()]
                for s in skills[:12]:
                    cor = G if s.get("executor")=="libertus" else Y
                    print(f"  {cor}*{X} {s.get('name','?')} [{s.get('category','?')}] *{s.get('score',0)} — {s.get('description','')[:55]}")
                print()
            elif entrada.startswith("/absorver"):
                cam = entrada.replace("/absorver","").strip()
                print(orch.abs.processar(cam) if cam else "Uso: /absorver <caminho>")
            elif entrada == "/evolucao":
                plano = orch.evolucao.ciclo(orch.sb, orch.mem)
                print(f"\n{orch._fmt_evolucao(plano)}\n")
            elif entrada == "/ensinar":
                nome = input("Nome: ").strip(); desc = input("Desc: ").strip()
                cat  = input("Cat: ").strip() or "auto"
                print("Codigo (linha vazia encerra):"); linhas = []
                while True:
                    l = input()
                    if not l: break
                    linhas.append(l)
                if nome and linhas:
                    ok = orch.sb.salvar_skill_completa(nome,desc,cat,"libertus","\n".join(linhas),{},[],  "manual")
                    if ok: log("Skill salva!", "ok")
            else:
                resultado = orch.processar(entrada)
                print(f"\n{G}{'─'*60}{X}")
                for linha in str(resultado)[:3000].split("\n"): print(f"  {linha}")
                print(f"{G}{'─'*60}{X}")
                print(f"  {Y}{orch._score_autonomia()}{X}\n")
        except KeyboardInterrupt:
            print(f"\n{Y}Ctrl+C — use /sair{X}")
        except Exception as e:
            log(f"Erro: {e}","error")

if __name__ == "__main__":
    main()
