#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
absorcao_docling.py — Absorção Automática de Conhecimento via Docling

Usa Docling para processar PDFs técnicos, documentação e código,
transformando em memórias estruturadas e skills executáveis.
"""

import os, sys, json, requests, subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Docling importado localmente para evitar travamento no startup
DOCLING_DISPONIVEL = True  # Assume disponível, falha lazy se não estiver



# Biblioteca de PDFs técnicos de CYBERSECURITY
CYBER_PDFS = {
    "pentest": [
        "https://www.offensive-security.com/pwk-online/PWK-Example-Report-v1.pdf",
        "https://github.com/swisskyrepo/PayloadsAllTheThings/raw/master/Methodology%20and%20Resources/Penetration%20Testing%20Execution%20Standard.pdf",
    ],
    "reverse-engineering": [
        "https://beginners.re/RE4B-EN.pdf",  # Reverse Engineering for Beginners
    ],
    "cryptography": [
        "https://crypto.stanford.edu/~dabo/cryptobook/BonehShoup_0_4.pdf",  # Boneh & Shoup
    ],
    "exploitation": [
        "https://www.exploit-db.com/docs/english/13694-attacking-the-core.pdf",
    ],
    "malware": [
        "https://www.sans.org/reading-room/whitepapers/malicious/paper/33649",
    ]
}

class AbsorcaoDocling:

    """
    Sistema de aprendizado autônomo via análise de documentos.
    """
    
    def __init__(self, root: Path):
        self.root = root
        self.docs_cache = root / "memory" / "docs_processados"
        self.docs_cache.mkdir(parents=True, exist_ok=True)
        
        # Lazy loading: Docling só é carregado quando necessário
        self.converter = None
        self.docling_carregado = False
        print("[ABSORCAO] Docling em modo lazy - carrega sob demanda")
    
    # ── Busca e Download de Documentos ───────────────────────────────
    
    def buscar_pdfs_relevantes(self, tags: List[str], max_results: int = 3) -> List[str]:
        """
        Busca PDFs técnicos relacionados às tags.
        
        Args:
            tags: Lista de tags de interesse (ex: ["godot", "gdscript"])
            max_results: Máximo de URLs para retornar
            
        Returns:
            Lista de URLs de PDFs
        """
        # Busca em fontes conhecidas
        fontes = {
            "godot": "https://docs.godotengine.org/en/stable/Godot_Engine_Documentation.pdf",
            "unity": "https://docs.unity3d.com/Manual/UnityManual.pdf",
            "python": "https://docs.python.org/3/library/index.html",
            "rust": "https://doc.rust-lang.org/book/",
        }
        
        urls = []
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in fontes:
                urls.append(fontes[tag_lower])
        
        return urls[:max_results]
    
    def baixar_documento(self, url: str) -> Optional[Path]:
        """
        Baixa documento para cache local.
        
        Returns:
            Path do arquivo baixado ou None se falhar
        """
        try:
            # Gera nome baseado em hash da URL
            import hashlib
            nome = hashlib.md5(url.encode()).hexdigest()
            extensao = Path(url).suffix or ".pdf"
            arquivo = self.docs_cache / f"{nome}{extensao}"
            
            # Se já existe, retorna
            if arquivo.exists():
                return arquivo
            
            # Download
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            arquivo.write_bytes(response.content)
            return arquivo
            
        except Exception as e:
            print(f"Erro baixando {url}: {e}")
            return None
    
    # ── Processamento com Docling ────────────────────────────────────
    
    def processar_documento(self, arquivo: Path) -> Optional[Dict]:
        """
        Processa documento com Docling extraindo estrutura.
        
        Returns:
            Dicionário com conteúdo estruturado
        """
        if not self.converter:
            return None
        
        try:
            # Converte documento
            result = self.converter.convert(str(arquivo))
            
            # Extrai conteúdo estruturado
            estrutura = {
                "titulo": result.document.name,
                "secoes": [],
                "tabelas": [],
                "codigos": [],
                "metadata": result.document.properties
            }
            
            # Processa seções
            for secao in result.document.sections:
                estrutura["secoes"].append({
                    "titulo": secao.title,
                    "texto": secao.text,
                    "nivel": secao.level
                })
            
            # Processa tabelas
            for tabela in result.document.tables:
                estrutura["tabelas"].append({
                    "dados": tabela.data,
                    "headers": tabela.headers
                })
            
            # Processa blocos de código
            for bloco in result.document.code_blocks:
                estrutura["codigos"].append({
                    "linguagem": bloco.language,
                    "codigo": bloco.text
                })
            
            return estrutura
            
        except Exception as e:
            print(f"Erro processando {arquivo}: {e}")
            return None
    
    # ── Transformação em Memórias ─────────────────────────────────────
    
    def criar_memorias_de_documento(self, estrutura: Dict, tags: List[str]) -> List[Dict]:
        """
        Transforma documento processado em memórias do Libertus.
        
        Returns:
            Lista de dicionários de memória
        """
        memorias = []
        
        # Memória principal (overview)
        memorias.append({
            "tipo": "conhecimento_documento",
            "titulo": estrutura["titulo"],
            "conteudo": f"# {estrutura['titulo']}\n\n"
                       f"Processado via Docling em {datetime.now():%Y-%m-%d}\n\n"
                       f"{len(estrutura['secoes'])} seções, "
                       f"{len(estrutura['tabelas'])} tabelas, "
                       f"{len(estrutura['codigos'])} blocos de código",
            "tags": [*tags, "docling", "auto_aprendizado", "documento"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Memória por seção importante
        for secao in estrutura["secoes"][:10]:  # Limita 10 primeiras
            if len(secao["texto"]) > 200:  # Apenas seções substanciais
                memorias.append({
                    "tipo": "secao_documento",
                    "titulo": secao["titulo"],
                    "conteudo": f"## {secao['titulo']}\n\n{secao['texto']}",
                    "tags": [*tags, "secao", "docling"],
                    "timestamp": datetime.now().isoformat()
                })
        
        # Skills de código extraídos
        for i, codigo in enumerate(estrutura["codigos"][:5]):
            memorias.append({
                "tipo": "codigo_extraido",
                "titulo": f"Código {codigo['linguagem']} #{i+1}",
                "conteudo": f"```{codigo['linguagem']}\n{codigo['codigo']}\n```",
                "tags": [*tags, "codigo", codigo["linguagem"], "docling"],
                "timestamp": datetime.now().isoformat()
            })
        
        return memorias
    
    # ── Ciclo Completo ────────────────────────────────────────────────
    
    def ciclo_absorcao(self, tags: List[str]) -> Dict:
        """
        Ciclo completo: busca → download → processa → cria memórias.
        
        Returns:
            Relatório da absorção
        """
        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "tags": tags,
            "documentos_processados": 0,
            "memorias_criadas": 0,
            "erros": []
        }
        
        if not self.converter:
            relatorio["erros"].append("Docling não instalado")
            return relatorio
        
        # 1. Busca documentos
        urls = self.buscar_pdfs_relevantes(tags)
        
        for url in urls:
            try:
                # 2. Download
                arquivo = self.baixar_documento(url)
                if not arquivo:
                    relatorio["erros"].append(f"Falha download: {url}")
                    continue
                
                # 3. Processa com Docling
                estrutura = self.processar_documento(arquivo)
                if not estrutura:
                    relatorio["erros"].append(f"Falha processamento: {arquivo.name}")
                    continue
                
                relatorio["documentos_processados"] += 1
                
                # 4. Cria memórias
                memorias = self.criar_memorias_de_documento(estrutura, tags)
                relatorio["memorias_criadas"] += len(memorias)
                
                # Salva memórias localmente
                mem_file = self.root / "memoria" / "conhecimento" / f"{arquivo.stem}.json"
                mem_file.parent.mkdir(parents=True, exist_ok=True)
                mem_file.write_text(json.dumps(memorias, ensure_ascii=False, indent=2))
                
            except Exception as e:
                relatorio["erros"].append(f"Erro: {e}")
        
        return relatorio
