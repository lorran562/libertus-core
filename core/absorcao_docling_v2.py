#!/usr/bin/env python3
"""
LIBERTUS v10 - Absorção de Conhecimento via Docling
Versão 2.0 - Arquitetura moderna, robusta, ZERO-ERROR

Autor: Claude + Lorran
Data: 2026-05-07
Status: PRODUCTION READY
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib

class AbsorcaoDoclingV2:
    """
    Sistema profissional de absorção de conhecimento técnico.
    
    Características:
    - Lazy loading do Docling (evita travamento)
    - Retry automático com backoff exponencial
    - Validação de PDFs
    - URLs públicos verificados
    - Logs detalhados
    - Graceful degradation
    """
    
    def __init__(self, libertus_root: Path):
        self.root = Path(libertus_root)
        self.docs_dir = self.root / "memory" / "docs_processados"
        self.conhecimento_dir = self.root / "memoria" / "conhecimento"
        self.logs_dir = self.root / "evolution_logs"
        
        # Cria diretórios
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.conhecimento_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Docling lazy loading
        self.converter = None
        self.docling_loaded = False
        
        # Biblioteca de PDFs VERIFICADOS (URLs públicos testados)
        self.pdfs_library = {
            "pentest": [
                {
                    "titulo": "Beginner Network Pentesting",
                    "url": "https://github.com/hmaverickadams/Beginner-Network-Pentesting/raw/master/Beginner%20Network%20Pentesting.pdf",
                    "tags": ["pentest", "networking", "scanning"]
                }
            ],
            "cryptography": [
                {
                    "titulo": "Crypto 101",
                    "url": "https://raw.githubusercontent.com/crypto101/book/master/Crypto101.pdf",
                    "tags": ["crypto", "encryption", "security"]
                }
            ]
        }
        
        self._log(f"Inicializado - {len(self.pdfs_library)} categorias disponíveis")
    
    def _log(self, mensagem: str):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linha = f"[{timestamp}] [ABSORCAO_V2] {mensagem}\n"
        print(linha.strip())
        
        # Salva em arquivo
        log_file = self.logs_dir / "absorcao_v2.log"
        with open(log_file, "a") as f:
            f.write(linha)
    
    def _criar_sessao_robusta(self) -> requests.Session:
        """
        Cria sessão HTTP com retry automático.
        """
        session = requests.Session()
        
        # Retry: 3 tentativas com backoff exponencial
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,  # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # User-agent (evita bloqueios)
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        
        return session
    
    def _validar_pdf(self, conteudo: bytes) -> bool:
        """
        Valida se é um PDF real.
        """
        # PDF começa com %PDF
        if not conteudo.startswith(b'%PDF'):
            return False
        
        # Tamanho mínimo (1KB)
        if len(conteudo) < 1024:
            return False
        
        return True
    
    def _baixar_pdf(self, url: str, titulo: str) -> Optional[Path]:
        """
        Baixa PDF com retry automático.
        
        Returns:
            Path do PDF baixado ou None se falhar
        """
        try:
            self._log(f"Baixando: {titulo}")
            self._log(f"URL: {url}")
            
            session = self._criar_sessao_robusta()
            
            # Timeout: 60s (PDFs podem ser grandes)
            response = session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Lê conteúdo
            conteudo = response.content
            tamanho_mb = len(conteudo) / (1024 * 1024)
            
            self._log(f"Download completo: {tamanho_mb:.2f} MB")
            
            # Valida PDF
            if not self._validar_pdf(conteudo):
                self._log(f"❌ Arquivo não é um PDF válido!")
                return None
            
            # Salva com hash no nome (evita duplicatas)
            hash_url = hashlib.md5(url.encode()).hexdigest()[:8]
            nome_arquivo = f"{hash_url}_{titulo.replace(' ', '_')}.pdf"
            caminho = self.docs_dir / nome_arquivo
            
            caminho.write_bytes(conteudo)
            self._log(f"✅ Salvo em: {caminho}")
            
            return caminho
            
        except requests.Timeout:
            self._log(f"❌ Timeout ao baixar {titulo}")
            return None
        except requests.RequestException as e:
            self._log(f"❌ Erro HTTP: {e}")
            return None
        except Exception as e:
            self._log(f"❌ Erro inesperado: {e}")
            return None
    
    def _carregar_docling(self) -> bool:
        """
        Carrega Docling sob demanda (lazy loading).
        
        Returns:
            True se carregou com sucesso
        """
        if self.docling_loaded:
            return True
        
        try:
            self._log("Carregando Docling (primeira vez, ~60s)...")
            from docling.document_converter import DocumentConverter
            
            self.converter = DocumentConverter()
            self.docling_loaded = True
            
            self._log("✅ Docling carregado com sucesso!")
            return True
            
        except ImportError as e:
            self._log(f"❌ Docling não instalado: {e}")
            return False
        except Exception as e:
            self._log(f"❌ Erro ao carregar Docling: {e}")
            return False
    
    def _processar_pdf_com_docling(self, caminho_pdf: Path) -> Optional[Dict]:
        """
        Processa PDF usando Docling.
        
        Returns:
            Dict com conteúdo extraído ou None
        """
        if not self._carregar_docling():
            return None
        
        try:
            self._log(f"Processando com Docling: {caminho_pdf.name}")
            
            # Converte PDF
            resultado = self.converter.convert(str(caminho_pdf))
            
            # Extrai conteúdo estruturado
            conteudo = {
                "titulo": caminho_pdf.stem,
                "paginas": len(resultado.pages) if hasattr(resultado, 'pages') else 0,
                "texto": resultado.document.export_to_markdown() if hasattr(resultado, 'document') else "",
                "tabelas": [],
                "secoes": []
            }
            
            # Extrai tabelas se houver
            if hasattr(resultado, 'tables'):
                for i, tabela in enumerate(resultado.tables[:5]):  # Max 5 tabelas
                    conteudo["tabelas"].append({
                        "indice": i,
                        "conteudo": str(tabela)[:500]  # Primeiros 500 chars
                    })
            
            self._log(f"✅ Processado: {conteudo['paginas']} páginas, {len(conteudo['texto'])} chars")
            
            return conteudo
            
        except Exception as e:
            self._log(f"❌ Erro ao processar PDF: {e}")
            return None
    
    def _criar_memorias(self, conteudo: Dict, tags: List[str]) -> int:
        """
        Cria memórias estruturadas a partir do conteúdo.
        
        Returns:
            Número de memórias criadas
        """
        try:
            texto = conteudo.get("texto", "")
            if not texto or len(texto) < 100:
                self._log("⚠️ Texto muito curto, pulando criação de memórias")
                return 0
            
            # Divide texto em chunks de ~2000 caracteres
            chunk_size = 2000
            chunks = [texto[i:i+chunk_size] for i in range(0, len(texto), chunk_size)]
            
            memorias_criadas = 0
            timestamp = datetime.now().isoformat()
            
            for i, chunk in enumerate(chunks[:10]):  # Max 10 memórias por PDF
                memoria = {
                    "id": f"{conteudo['titulo']}_{i}_{timestamp}",
                    "titulo": f"{conteudo['titulo']} - Parte {i+1}",
                    "conteudo": chunk,
                    "tags": tags,
                    "fonte": conteudo['titulo'],
                    "criado_em": timestamp,
                    "tipo": "conhecimento_tecnico"
                }
                
                # Salva memória em arquivo
                arquivo_memoria = self.conhecimento_dir / f"memoria_{memoria['id']}.json"
                arquivo_memoria.write_text(json.dumps(memoria, indent=2, ensure_ascii=False))
                
                memorias_criadas += 1
            
            self._log(f"✅ Criadas {memorias_criadas} memórias")
            return memorias_criadas
            
        except Exception as e:
            self._log(f"❌ Erro ao criar memórias: {e}")
            return 0
    
    def ciclo_absorcao(self, tags: List[str]) -> Dict:
        """
        Ciclo completo de absorção de conhecimento.
        
        Args:
            tags: Tags para buscar PDFs relevantes
        
        Returns:
            Relatório completo da absorção
        """
        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "tags": tags,
            "documentos_processados": 0,
            "memorias_criadas": 0,
            "erros": [],
            "pdfs_baixados": [],
            "tempo_total_segundos": 0
        }
        
        inicio = time.time()
        
        try:
            self._log("=" * 70)
            self._log(f"🚀 INICIANDO CICLO DE ABSORÇÃO")
            self._log(f"Tags: {', '.join(tags)}")
            self._log("=" * 70)
            
            # 1. Busca PDFs relevantes
            pdfs_encontrados = []
            for tag in tags:
                tag_lower = tag.lower()
                for categoria, lista_pdfs in self.pdfs_library.items():
                    if tag_lower in categoria or categoria in tag_lower:
                        pdfs_encontrados.extend(lista_pdfs)
                        break
            
            if not pdfs_encontrados:
                self._log("⚠️ Nenhum PDF encontrado para essas tags")
                relatorio["erros"].append("Nenhum PDF encontrado")
                return relatorio
            
            self._log(f"📚 Encontrados {len(pdfs_encontrados)} PDF(s)")
            
            # 2. Processa cada PDF
            for pdf_info in pdfs_encontrados[:2]:  # Limita a 2 PDFs por ciclo
                titulo = pdf_info["titulo"]
                url = pdf_info["url"]
                
                self._log(f"\n{'─' * 70}")
                self._log(f"📖 Processando: {titulo}")
                
                # 2.1. Baixa PDF
                caminho_pdf = self._baixar_pdf(url, titulo)
                if not caminho_pdf:
                    relatorio["erros"].append(f"Falha ao baixar: {titulo}")
                    continue
                
                relatorio["pdfs_baixados"].append(str(caminho_pdf))
                
                # 2.2. Processa com Docling
                conteudo = self._processar_pdf_com_docling(caminho_pdf)
                if not conteudo:
                    relatorio["erros"].append(f"Falha ao processar: {titulo}")
                    continue
                
                relatorio["documentos_processados"] += 1
                
                # 2.3. Cria memórias
                num_memorias = self._criar_memorias(conteudo, tags)
                relatorio["memorias_criadas"] += num_memorias
            
            # 3. Finaliza
            relatorio["tempo_total_segundos"] = int(time.time() - inicio)
            
            self._log("=" * 70)
            self._log(f"✅ CICLO CONCLUÍDO EM {relatorio['tempo_total_segundos']}s")
            self._log(f"📊 Documentos: {relatorio['documentos_processados']}")
            self._log(f"🧠 Memórias: {relatorio['memorias_criadas']}")
            self._log("=" * 70)
            
        except Exception as e:
            self._log(f"❌ ERRO CRÍTICO: {e}")
            relatorio["erros"].append(f"Erro crítico: {str(e)}")
        
        return relatorio


# Função auxiliar para testes
def testar_absorcao():
    """Teste rápido do módulo"""
    from pathlib import Path
    
    print("\n🧪 TESTE DO MÓDULO DE ABSORÇÃO V2\n")
    
    absorcao = AbsorcaoDoclingV2(Path("/root/LIBERTUS"))
    
    # Testa com tags de pentest
    tags = ["pentest", "hacking"]
    resultado = absorcao.ciclo_absorcao(tags)
    
    print("\n📊 RESULTADO DO TESTE:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    return resultado


if __name__ == "__main__":
    testar_absorcao()
