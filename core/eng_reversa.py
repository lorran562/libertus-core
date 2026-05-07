"""
eng_reversa.py — Módulo de Engenharia Reversa do Libertus
Skill acionável para analisar, entender e melhorar sistemas e código.

Lê de:      qualquer arquivo de código fornecido
Escreve em: /LIBERTUS/evolucao/, /LIBERTUS/skills/, /LIBERTUS/projetos/
"""

import ast, re, json, dis, inspect, tokenize, io
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict


class EngReversaError(Exception):
    pass


class EngenheiriaReversa:
    """
    Skill de engenharia reversa do Libertus.

    Como o Libertus usa esta skill:
    1. Recebe código ou sistema para analisar
    2. Detecta linguagem e estrutura automaticamente
    3. Aplica análise profunda (AST, padrões, dependências)
    4. Produz relatório estruturado com melhorias
    5. Salva conhecimento extraído no vault

    Acionamento:
        er = EngenheiriaReversa(root=LIBERTUS_ROOT)
        relatorio = er.analisar(codigo=texto, contexto="sistema X")
        er.salvar_no_vault(relatorio)
    """

    LINGUAGENS = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".gd": "gdscript", ".cs": "csharp", ".java": "java",
        ".cpp": "cpp", ".c": "c", ".go": "go", ".rs": "rust",
        ".rb": "ruby", ".php": "php", ".sh": "bash", ".sql": "sql",
    }

    def __init__(self, root: Path = None):
        self.root = root
        if root:
            (root / "evolucao").mkdir(parents=True, exist_ok=True)
            (root / "skills").mkdir(parents=True, exist_ok=True)

    # ══════════════════════════════════════════════════════════════════════
    # API PÚBLICA — SKILL PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════

    def analisar(self, codigo: str = None, caminho: str = None,
                 contexto: str = "") -> Dict:
        """
        Ponto de entrada principal da skill.
        Aceita código como string ou caminho de arquivo.

        Retorna dicionário completo com:
        - estrutura detectada
        - dependências mapeadas
        - padrões identificados
        - pontos de melhoria
        - lógica reconstruída
        - score de qualidade
        """
        # Carrega código
        if caminho and not codigo:
            codigo, linguagem = self._carregar_arquivo(caminho)
        elif codigo:
            linguagem = self._detectar_linguagem(codigo, caminho)
        else:
            raise EngReversaError("Forneça código ou caminho")

        # Análise completa
        relatorio = {
            "linguagem":     linguagem,
            "contexto":      contexto,
            "metricas":      self._calcular_metricas(codigo),
            "estrutura":     self._analisar_estrutura(codigo, linguagem),
            "dependencias":  self._mapear_dependencias(codigo, linguagem),
            "padroes":       self._identificar_padroes(codigo, linguagem),
            "logica":        self._reconstruir_logica(codigo, linguagem),
            "melhorias":     self._detectar_melhorias(codigo, linguagem),
            "score":         0,
            "resumo":        "",
        }

        relatorio["score"]  = self._calcular_score(relatorio)
        relatorio["resumo"] = self._gerar_resumo(relatorio)

        return relatorio

    def analisar_sistema(self, pasta: str) -> Dict:
        """
        Analisa um sistema completo (pasta com múltiplos arquivos).
        Mapeia dependências entre módulos e detecta arquitetura.
        """
        p = Path(pasta)
        if not p.exists():
            raise EngReversaError(f"Pasta não encontrada: {pasta}")

        arquivos = []
        for ext in self.LINGUAGENS:
            arquivos.extend(p.rglob(f"*{ext}"))

        analises  = {}
        grafo_dep = defaultdict(list)

        for arq in arquivos[:50]:  # max 50 arquivos
            try:
                codigo, lang = self._carregar_arquivo(str(arq))
                analise = self.analisar(codigo=codigo, caminho=str(arq))
                chave   = str(arq.relative_to(p))
                analises[chave] = analise
                # Constrói grafo de dependências
                for dep in analise["dependencias"].get("internas", []):
                    grafo_dep[chave].append(dep)
            except Exception as e:
                analises[str(arq)] = {"erro": str(e)}

        return {
            "pasta":         pasta,
            "total_arquivos": len(arquivos),
            "arquivos_analisados": len(analises),
            "arquitetura":   self._detectar_arquitetura(analises),
            "grafo_dependencias": dict(grafo_dep),
            "arquivo_central": self._encontrar_central(grafo_dep),
            "analises":      analises,
            "resumo_sistema": self._resumir_sistema(analises),
        }

    def reconstruir_logica(self, codigo: str, linguagem: str = "python") -> str:
        """
        Reconstrói a lógica de negócio em linguagem natural.
        Útil para entender código legado ou desconhecido.
        """
        logica = self._reconstruir_logica(codigo, linguagem)
        partes = []

        if logica.get("objetivo"):
            partes.append(f"OBJETIVO: {logica['objetivo']}")

        if logica.get("entradas"):
            partes.append(f"ENTRADAS: {', '.join(logica['entradas'])}")

        if logica.get("saidas"):
            partes.append(f"SAÍDAS: {', '.join(logica['saidas'])}")

        if logica.get("fluxo"):
            partes.append("FLUXO:")
            for i, passo in enumerate(logica["fluxo"], 1):
                partes.append(f"  {i}. {passo}")

        if logica.get("condicoes"):
            partes.append(f"CONDIÇÕES: {', '.join(logica['condicoes'])}")

        if logica.get("efeitos_colaterais"):
            partes.append(f"EFEITOS: {', '.join(logica['efeitos_colaterais'])}")

        return "\n".join(partes)

    def sugerir_melhorias(self, codigo: str, linguagem: str = "python") -> List[Dict]:
        """
        Detecta e prioriza melhorias específicas com código de exemplo.
        """
        return self._detectar_melhorias(codigo, linguagem)

    def salvar_no_vault(self, relatorio: Dict, nome: str = ""):
        """Salva análise no vault do Libertus."""
        if not self.root:
            return
        import datetime
        ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nome  = nome or f"eng_reversa_{ts}"
        arq   = self.root / "evolucao" / f"{nome}.md"
        conteudo = self._formatar_markdown(relatorio)
        arq.write_text(conteudo, encoding="utf-8")
        return str(arq)

    # ══════════════════════════════════════════════════════════════════════
    # ANÁLISE DE ESTRUTURA
    # ══════════════════════════════════════════════════════════════════════

    def _analisar_estrutura(self, codigo: str, linguagem: str) -> Dict:
        """Extrai estrutura: classes, funções, variáveis globais."""
        estrutura = {
            "classes":    [],
            "funcoes":    [],
            "variaveis":  [],
            "decoradores": [],
            "constantes": [],
        }

        if linguagem == "python":
            estrutura.update(self._estrutura_python(codigo))
        elif linguagem in ("javascript", "typescript"):
            estrutura.update(self._estrutura_js(codigo))
        elif linguagem == "gdscript":
            estrutura.update(self._estrutura_gdscript(codigo))
        else:
            estrutura.update(self._estrutura_generica(codigo))

        return estrutura

    def _estrutura_python(self, codigo: str) -> Dict:
        """Análise de estrutura Python via AST."""
        result = {"classes": [], "funcoes": [], "variaveis": [],
                  "decoradores": [], "constantes": []}
        try:
            tree = ast.parse(codigo)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    metodos = [n.name for n in ast.walk(node)
                               if isinstance(n, ast.FunctionDef)]
                    result["classes"].append({
                        "nome":     node.name,
                        "linha":    node.lineno,
                        "metodos":  metodos,
                        "heranca":  [b.id for b in node.bases
                                     if isinstance(b, ast.Name)],
                    })
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in node.args.args]
                    docstring = ast.get_docstring(node) or ""
                    result["funcoes"].append({
                        "nome":      node.name,
                        "linha":     node.lineno,
                        "args":      args,
                        "async":     isinstance(node, ast.AsyncFunctionDef),
                        "docstring": docstring[:100],
                        "retorna":   self._inferir_retorno(node),
                    })
                elif isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            nome = t.id
                            if nome.isupper():
                                result["constantes"].append(nome)
                            else:
                                result["variaveis"].append(nome)
        except SyntaxError as e:
            result["erro_sintaxe"] = str(e)
        return result

    def _estrutura_js(self, codigo: str) -> Dict:
        """Análise de estrutura JavaScript/TypeScript via regex."""
        return {
            "classes":  re.findall(r"class\s+(\w+)", codigo),
            "funcoes":  re.findall(r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()", codigo),
            "imports":  re.findall(r"import\s+.*?from\s+['\"](.+?)['\"]", codigo),
            "exports":  re.findall(r"export\s+(?:default\s+)?(?:class|function|const)\s+(\w+)", codigo),
        }

    def _estrutura_gdscript(self, codigo: str) -> Dict:
        """Análise de estrutura GDScript (Godot)."""
        return {
            "extends":   re.findall(r"extends\s+(\w+)", codigo),
            "classes":   re.findall(r"class\s+(\w+)", codigo),
            "funcoes":   re.findall(r"func\s+(\w+)\s*\(", codigo),
            "variaveis": re.findall(r"(?:var|const|@export)\s+(\w+)", codigo),
            "sinais":    re.findall(r"signal\s+(\w+)", codigo),
            "autoloads": re.findall(r"(?:GameManager|SurvivalSystem|Inventory|AudioManager)\.\w+", codigo),
        }

    def _estrutura_generica(self, codigo: str) -> Dict:
        """Análise genérica para linguagens não mapeadas."""
        return {
            "linhas":    codigo.count("\n") + 1,
            "funcoes":   re.findall(r"(?:def|func|function|void|int|str)\s+(\w+)\s*\(", codigo),
            "classes":   re.findall(r"(?:class|struct|interface)\s+(\w+)", codigo),
            "comentarios": len(re.findall(r"(?://|#|/\*).+", codigo)),
        }

    # ══════════════════════════════════════════════════════════════════════
    # DEPENDÊNCIAS
    # ══════════════════════════════════════════════════════════════════════

    def _mapear_dependencias(self, codigo: str, linguagem: str) -> Dict:
        """Mapeia imports, dependências externas e internas."""
        deps = {"externas": [], "internas": [], "stdlib": []}

        if linguagem == "python":
            try:
                tree = ast.parse(codigo)
                stdlib = self._get_stdlib()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            nome = alias.name.split(".")[0]
                            if nome in stdlib:
                                deps["stdlib"].append(nome)
                            else:
                                deps["externas"].append(nome)
                    elif isinstance(node, ast.ImportFrom):
                        mod = node.module or ""
                        if mod.startswith("."):
                            deps["internas"].append(mod)
                        elif mod.split(".")[0] in self._get_stdlib():
                            deps["stdlib"].append(mod)
                        else:
                            deps["externas"].append(mod)
            except Exception:
                pass

        elif linguagem in ("javascript", "typescript"):
            deps["externas"] = re.findall(
                r"(?:import|require)\s*\(?['\"](?!\.)(.*?)['\"]", codigo)
            deps["internas"] = re.findall(
                r"(?:import|require)\s*\(?['\"](\./.*?)['\"]", codigo)

        # Remove duplicatas
        for k in deps:
            deps[k] = list(set(deps[k]))

        return deps

    # ══════════════════════════════════════════════════════════════════════
    # PADRÕES DE DESIGN
    # ══════════════════════════════════════════════════════════════════════

    def _identificar_padroes(self, codigo: str, linguagem: str) -> List[Dict]:
        """Identifica padrões de design e anti-padrões."""
        padroes  = []
        codigo_l = codigo.lower()

        # Padrões positivos
        checks = [
            ("Singleton",     r"_instance\s*=\s*None|getInstance\(\)", "design_pattern"),
            ("Observer",      r"def\s+notify|emit_signal|\.connect\(", "design_pattern"),
            ("Factory",       r"def\s+create|def\s+make|Factory", "design_pattern"),
            ("Strategy",      r"def\s+execute.*self|strategy\s*=", "design_pattern"),
            ("Decorator",     r"@\w+\s*\ndef\s+\w+", "design_pattern"),
            ("MVC",           r"(?:model|view|controller|Model|View|Controller)", "arquitetura"),
            ("Repository",    r"(?:Repository|repo|DAO)\s*[:\(]", "arquitetura"),
            ("Async/Await",   r"async\s+def|await\s+", "concorrencia"),
            ("Context Manager", r"__enter__|__exit__|with\s+", "boas_praticas"),
            ("Type Hints",    r"def\s+\w+\s*\([^)]*:\s*\w+", "boas_praticas"),
        ]

        for nome, padrao, categoria in checks:
            if re.search(padrao, codigo):
                padroes.append({
                    "nome":      nome,
                    "categoria": categoria,
                    "tipo":      "positivo",
                })

        # Anti-padrões
        anti_checks = [
            ("God Class",      r"class\s+\w+.*?(?:def\s+\w+.*?){20,}", "anti_padrao"),
            ("Magic Numbers",  r"(?<!\w)(?:[2-9]\d{2,}|\d{4,})(?!\w)", "anti_padrao"),
            ("Variável genérica", r"\b(?:var\d|temp|tmp|data|obj|item)\b", "anti_padrao"),
            ("Print debug",    r"print\s*\(['\"]DEBUG|console\.log\(['\"]DEBUG", "anti_padrao"),
            ("Bare except",    r"except\s*:", "anti_padrao"),
            ("Hard-coded path", r"['\"](?:C:\\\\|/home/|/Users/)\w", "anti_padrao"),
        ]

        for nome, padrao, categoria in anti_checks:
            if re.search(padrao, codigo):
                padroes.append({
                    "nome":      nome,
                    "categoria": categoria,
                    "tipo":      "negativo",
                    "impacto":   "manutenibilidade",
                })

        return padroes

    # ══════════════════════════════════════════════════════════════════════
    # RECONSTRUÇÃO DE LÓGICA
    # ══════════════════════════════════════════════════════════════════════

    def _reconstruir_logica(self, codigo: str, linguagem: str) -> Dict:
        """
        Reconstrói lógica de negócio em linguagem natural.
        Analisa fluxo de controle, entradas, saídas e efeitos.
        """
        logica = {
            "objetivo":          self._inferir_objetivo(codigo),
            "entradas":          self._extrair_entradas(codigo, linguagem),
            "saidas":            self._extrair_saidas(codigo, linguagem),
            "fluxo":             self._extrair_fluxo(codigo, linguagem),
            "condicoes":         self._extrair_condicoes(codigo),
            "loops":             self._extrair_loops(codigo),
            "efeitos_colaterais": self._detectar_efeitos(codigo),
        }
        return logica

    def _inferir_objetivo(self, codigo: str) -> str:
        """Infere o objetivo principal do código."""
        # 1. Tenta docstring
        doc_match = re.search(r'"""(.*?)"""', codigo, re.DOTALL)
        if doc_match:
            return doc_match.group(1).strip()[:200]

        # 2. Nome das funções principais
        funcs = re.findall(r"def\s+(\w+)\s*\(", codigo)
        if funcs:
            nomes = [f.replace("_", " ") for f in funcs[:3]]
            return f"Realiza: {', '.join(nomes)}"

        # 3. Comentários
        comentarios = re.findall(r"#\s*(.+)", codigo)
        if comentarios:
            return comentarios[0][:200]

        return "Objetivo não detectado — sem docstring ou comentários descritivos"

    def _extrair_entradas(self, codigo: str, linguagem: str) -> List[str]:
        """Extrai parâmetros de entrada."""
        entradas = []
        if linguagem == "python":
            try:
                tree = ast.parse(codigo)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for arg in node.args.args:
                            if arg.arg != "self":
                                entradas.append(arg.arg)
            except Exception:
                pass
        else:
            # Regex genérico
            matches = re.findall(r"(?:def|func|function)\s+\w+\s*\(([^)]+)\)", codigo)
            for m in matches:
                params = [p.strip().split(":")[0].split("=")[0].strip()
                          for p in m.split(",") if p.strip()]
                entradas.extend([p for p in params if p and p != "self"])

        return list(set(entradas))[:10]

    def _extrair_saidas(self, codigo: str, linguagem: str) -> List[str]:
        """Extrai o que o código retorna ou produz."""
        saidas = []

        # Returns
        returns = re.findall(r"return\s+(.+?)(?:\n|$)", codigo)
        for r in returns[:5]:
            saidas.append(f"return: {r.strip()[:50]}")

        # Prints/outputs
        if re.search(r"print\s*\(|console\.log", codigo):
            saidas.append("saída de texto (print/console)")

        # Arquivos escritos
        if re.search(r"\.write\s*\(|open\s*\(.*['\"]w['\"]", codigo):
            saidas.append("escreve arquivo")

        # Requisições HTTP
        if re.search(r"requests\.|httpx\.|fetch\(|axios\.", codigo):
            saidas.append("requisição HTTP")

        # Banco de dados
        if re.search(r"\.post\(|\.insert\(|\.save\(|cursor\.execute", codigo):
            saidas.append("persiste no banco de dados")

        return saidas or ["sem saída explícita detectada"]

    def _extrair_fluxo(self, codigo: str, linguagem: str) -> List[str]:
        """Extrai fluxo de execução em linguagem natural."""
        fluxo = []

        if linguagem == "python":
            try:
                tree = ast.parse(codigo)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fluxo.append(f"Executa função '{node.name}'")
                    elif isinstance(node, ast.If):
                        fluxo.append("Verifica condição e bifurca execução")
                    elif isinstance(node, (ast.For, ast.While)):
                        fluxo.append("Itera sobre elementos")
                    elif isinstance(node, ast.Try):
                        fluxo.append("Tenta operação com tratamento de erro")
                    elif isinstance(node, ast.With):
                        fluxo.append("Gerencia contexto (with statement)")
            except Exception:
                pass

        return fluxo[:8] or ["fluxo não detectado automaticamente"]

    def _extrair_condicoes(self, codigo: str) -> List[str]:
        """Extrai condições lógicas principais."""
        condicoes = []
        ifs = re.findall(r"if\s+(.+?):", codigo)
        for c in ifs[:5]:
            condicoes.append(c.strip()[:80])
        return condicoes

    def _extrair_loops(self, codigo: str) -> List[str]:
        """Extrai loops e iterações."""
        loops = []
        fors   = re.findall(r"for\s+(.+?)\s+in\s+(.+?):", codigo)
        whiles = re.findall(r"while\s+(.+?):", codigo)
        for var, iteravel in fors[:3]:
            loops.append(f"for {var.strip()} in {iteravel.strip()}")
        for cond in whiles[:2]:
            loops.append(f"while {cond.strip()}")
        return loops

    def _detectar_efeitos(self, codigo: str) -> List[str]:
        """Detecta efeitos colaterais do código."""
        efeitos = []
        checks = [
            (r"os\.(remove|rename|makedirs|system)", "manipula sistema de arquivos"),
            (r"subprocess\.", "executa processo externo"),
            (r"requests\.|httpx\.|urllib", "faz requisição de rede"),
            (r"\.write\(|open\(.*['\"]w", "escreve em arquivo"),
            (r"\.delete\(|DROP|DELETE", "deleta dados"),
            (r"time\.sleep|asyncio\.sleep", "pausa execução"),
            (r"threading\.|multiprocessing\.", "usa paralelismo"),
            (r"import\s+os\b", "acessa sistema operacional"),
        ]
        for padrao, descricao in checks:
            if re.search(padrao, codigo):
                efeitos.append(descricao)
        return efeitos

    # ══════════════════════════════════════════════════════════════════════
    # MELHORIAS
    # ══════════════════════════════════════════════════════════════════════

    def _detectar_melhorias(self, codigo: str, linguagem: str) -> List[Dict]:
        """Detecta e prioriza melhorias com exemplos de código."""
        melhorias = []

        checks = [
            # (condição, título, descrição, exemplo, prioridade)
            (
                not re.search(r'""".*?"""', codigo, re.DOTALL) and
                re.search(r"def\s+\w+", codigo),
                "Adicionar docstrings",
                "Funções sem documentação dificultam manutenção",
                '"""Descreve o que a função faz, parâmetros e retorno."""',
                "alta"
            ),
            (
                re.search(r"except\s*:", codigo),
                "Especificar exceções no except",
                "Bare except captura até SystemExit e KeyboardInterrupt",
                "except (ValueError, TypeError) as e:\n    log(str(e), 'error')",
                "alta"
            ),
            (
                re.search(r"def\s+\w+\s*\([^)]*\)\s*:", codigo) and
                not re.search(r"def\s+\w+\s*\([^)]*:\s*\w+", codigo),
                "Adicionar type hints",
                "Type hints melhoram IDE support e detectam bugs precocemente",
                "def processar(dados: str, limite: int = 10) -> Dict:",
                "media"
            ),
            (
                re.search(r"print\s*\(", codigo) and
                not re.search(r"import logging|from.*log", codigo),
                "Substituir print por logging",
                "print não permite controle de nível, arquivo ou formatação",
                "import logging\nlogging.info('mensagem')",
                "media"
            ),
            (
                len(codigo.split("\n")) > 300 and
                re.search(r"def\s+\w+", codigo),
                "Refatorar — arquivo muito longo",
                f"Arquivo com {len(codigo.split(chr(10)))} linhas — dividir em módulos",
                "# Extrair classes/funções para módulos separados",
                "media"
            ),
            (
                re.search(r"time\.sleep\(\d+\)", codigo),
                "Substituir sleep fixo por retry com backoff",
                "sleep fixo é frágil — use exponential backoff",
                "for i in range(3):\n    try: ...\n    except: time.sleep(2**i)",
                "baixa"
            ),
            (
                re.search(r"httpx\.|requests\.", codigo) and
                not re.search(r"timeout\s*=", codigo),
                "Adicionar timeout nas requisições HTTP",
                "Requisições sem timeout travam indefinidamente",
                "httpx.get(url, timeout=30)",
                "alta"
            ),
            (
                re.search(r"['\"]SELECT|['\"]INSERT|['\"]UPDATE", codigo) and
                re.search(r"\+\s*\w+|\{.*\}", codigo),
                "Usar parâmetros em queries SQL",
                "Concatenação de SQL é vulnerável a SQL injection",
                "cursor.execute('SELECT * FROM t WHERE id = ?', (id,))",
                "critica"
            ),
        ]

        for condicao, titulo, descricao, exemplo, prioridade in checks:
            if condicao:
                melhorias.append({
                    "titulo":     titulo,
                    "descricao":  descricao,
                    "exemplo":    exemplo,
                    "prioridade": prioridade,
                })

        return sorted(melhorias,
                      key=lambda x: {"critica":4,"alta":3,"media":2,"baixa":1}
                      .get(x["prioridade"],0), reverse=True)

    # ══════════════════════════════════════════════════════════════════════
    # MÉTRICAS E SCORE
    # ══════════════════════════════════════════════════════════════════════

    def _calcular_metricas(self, codigo: str) -> Dict:
        linhas  = codigo.split("\n")
        return {
            "total_linhas":     len(linhas),
            "linhas_codigo":    sum(1 for l in linhas if l.strip() and not l.strip().startswith("#")),
            "linhas_comentario": sum(1 for l in linhas if l.strip().startswith("#")),
            "linhas_vazias":    sum(1 for l in linhas if not l.strip()),
            "total_chars":      len(codigo),
            "funcoes_count":    len(re.findall(r"def\s+\w+", codigo)),
            "classes_count":    len(re.findall(r"class\s+\w+", codigo)),
            "imports_count":    len(re.findall(r"^(?:import|from)\s+", codigo, re.MULTILINE)),
            "complexidade_est": len(re.findall(r"\b(?:if|elif|for|while|except|with)\b", codigo)),
            "taxa_comentario":  round(
                sum(1 for l in linhas if l.strip().startswith("#")) /
                max(len(linhas), 1) * 100, 1
            ),
        }

    def _calcular_score(self, relatorio: Dict) -> int:
        """Calcula score de qualidade 0-100."""
        score = 70  # base

        metricas = relatorio.get("metricas", {})
        padroes  = relatorio.get("padroes", [])
        melhorias = relatorio.get("melhorias", [])

        # Bônus por boas práticas
        positivos = [p for p in padroes if p.get("tipo") == "positivo"]
        score += min(len(positivos) * 3, 15)

        # Taxa de comentário
        if metricas.get("taxa_comentario", 0) > 15:
            score += 5

        # Penalidades
        negativos = [p for p in padroes if p.get("tipo") == "negativo"]
        score -= len(negativos) * 4

        criticas = [m for m in melhorias if m.get("prioridade") == "critica"]
        score -= len(criticas) * 10

        altas = [m for m in melhorias if m.get("prioridade") == "alta"]
        score -= len(altas) * 5

        return max(0, min(100, score))

    # ══════════════════════════════════════════════════════════════════════
    # ANÁLISE DE SISTEMA
    # ══════════════════════════════════════════════════════════════════════

    def _detectar_arquitetura(self, analises: Dict) -> str:
        """Detecta padrão arquitetural do sistema."""
        nomes = " ".join(analises.keys()).lower()
        if "controller" in nomes and "model" in nomes:
            return "MVC (Model-View-Controller)"
        if "router" in nomes or "route" in nomes:
            return "API REST com roteamento"
        if "autoload" in nomes or "gamemanager" in nomes:
            return "Game Architecture (Singleton + Autoloads)"
        if "service" in nomes and "repository" in nomes:
            return "Service-Repository Pattern"
        if "core" in nomes and "module" in nomes:
            return "Modular / Plugin Architecture"
        return "Arquitetura personalizada"

    def _encontrar_central(self, grafo: Dict) -> str:
        """Encontra o arquivo mais referenciado (ponto central)."""
        if not grafo:
            return "não detectado"
        contagem = defaultdict(int)
        for deps in grafo.values():
            for dep in deps:
                contagem[dep] += 1
        if contagem:
            return max(contagem, key=contagem.get)
        return "não detectado"

    def _resumir_sistema(self, analises: Dict) -> str:
        """Gera resumo do sistema completo."""
        total_funcoes  = sum(len(a.get("estrutura",{}).get("funcoes",[])) for a in analises.values() if isinstance(a, dict))
        total_classes  = sum(len(a.get("estrutura",{}).get("classes",[])) for a in analises.values() if isinstance(a, dict))
        total_linhas   = sum(a.get("metricas",{}).get("total_linhas",0) for a in analises.values() if isinstance(a, dict))
        scores         = [a.get("score",0) for a in analises.values() if isinstance(a, dict) and a.get("score")]
        score_medio    = round(sum(scores)/len(scores),1) if scores else 0

        return (f"Sistema com {len(analises)} arquivos | "
                f"{total_linhas} linhas | "
                f"{total_classes} classes | "
                f"{total_funcoes} funções | "
                f"Score médio: {score_medio}/100")

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _carregar_arquivo(self, caminho: str):
        p   = Path(caminho)
        ext = p.suffix.lower()
        lang = self.LINGUAGENS.get(ext, "generico")
        codigo = p.read_text(encoding="utf-8", errors="replace")
        return codigo, lang

    def _detectar_linguagem(self, codigo: str, caminho: str = None) -> str:
        if caminho:
            ext = Path(caminho).suffix.lower()
            if ext in self.LINGUAGENS:
                return self.LINGUAGENS[ext]
        # Heurísticas
        if "def " in codigo and "import " in codigo:
            return "python"
        if "func " in codigo and "extends " in codigo:
            return "gdscript"
        if "function " in codigo and "const " in codigo:
            return "javascript"
        if "public class " in codigo or "void " in codigo:
            return "java"
        return "generico"

    def _inferir_retorno(self, node) -> str:
        """Infere tipo de retorno de uma função Python via AST."""
        if node.returns:
            try:
                return ast.unparse(node.returns)
            except Exception:
                pass
        # Busca return statements
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value:
                try:
                    return type(ast.literal_eval(child.value)).__name__
                except Exception:
                    break
        return "Any"

    def _get_stdlib(self) -> set:
        """Retorna módulos da stdlib Python."""
        return {
            "os","sys","re","json","time","datetime","pathlib","typing",
            "collections","itertools","functools","io","abc","math","random",
            "hashlib","uuid","threading","multiprocessing","subprocess",
            "logging","unittest","contextlib","copy","enum","dataclasses",
            "socket","http","urllib","email","html","xml","csv","sqlite3",
            "asyncio","concurrent","inspect","traceback","warnings","string",
            "struct","binascii","base64","zlib","gzip","zipfile","tarfile",
            "shutil","tempfile","glob","fnmatch","stat","platform","signal",
        }

    def _gerar_resumo(self, relatorio: Dict) -> str:
        m   = relatorio.get("metricas", {})
        s   = relatorio.get("estrutura", {})
        mel = relatorio.get("melhorias", [])
        return (
            f"Código em {relatorio['linguagem']} | "
            f"{m.get('total_linhas',0)} linhas | "
            f"{len(s.get('funcoes',[]))} funções | "
            f"{len(s.get('classes',[]))} classes | "
            f"Score: {relatorio.get('score',0)}/100 | "
            f"{len(mel)} melhorias sugeridas"
        )

    def _formatar_markdown(self, relatorio: Dict) -> str:
        """Formata o relatório como markdown para o Obsidian."""
        import datetime
        m   = relatorio.get("metricas", {})
        mel = relatorio.get("melhorias", [])
        pad = relatorio.get("padroes", [])
        log = relatorio.get("logica", {})

        linhas = [
            f"---\ntitulo: Engenharia Reversa — {relatorio.get('contexto','análise')}\n"
            f"data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"linguagem: {relatorio.get('linguagem','?')}\n"
            f"score: {relatorio.get('score',0)}\n"
            f"tags: [\"eng_reversa\",\"{relatorio.get('linguagem','?')}\"]\n---\n",

            f"## Resumo\n{relatorio.get('resumo','')}\n",

            f"## Métricas\n"
            f"- Linhas: {m.get('total_linhas',0)}\n"
            f"- Funções: {m.get('funcoes_count',0)}\n"
            f"- Classes: {m.get('classes_count',0)}\n"
            f"- Complexidade estimada: {m.get('complexidade_est',0)}\n"
            f"- Taxa de comentário: {m.get('taxa_comentario',0)}%\n",

            f"## Lógica Reconstruída\n"
            f"**Objetivo:** {log.get('objetivo','?')}\n\n"
            f"**Entradas:** {', '.join(log.get('entradas',[]) or ['nenhuma'])}\n\n"
            f"**Saídas:** {', '.join(log.get('saidas',[]) or ['nenhuma'])}\n\n"
            f"**Efeitos colaterais:** {', '.join(log.get('efeitos_colaterais',[]) or ['nenhum'])}\n",

            f"## Padrões Identificados\n"
            + "\n".join(
                f"- {'✅' if p['tipo']=='positivo' else '⚠️'} **{p['nome']}** [{p['categoria']}]"
                for p in pad
            ) + "\n",

            f"## Melhorias Sugeridas\n"
            + "\n".join(
                f"### [{m['prioridade'].upper()}] {m['titulo']}\n"
                f"{m['descricao']}\n```\n{m['exemplo']}\n```"
                for m in mel
            ) + "\n",
        ]

        return "\n".join(linhas)
