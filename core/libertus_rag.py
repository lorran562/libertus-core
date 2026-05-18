#!/usr/bin/env python3
"""
LIBERTUS RAG - Sistema de Conhecimento
Absorve PDFs, indexa vetorialmente, responde perguntas
"""

import os
import chromadb
from pathlib import Path
from typing import List, Dict, Any
import hashlib

class LibertusRAG:
    """Sistema RAG para absorção e consulta de conhecimento"""
    
    def __init__(self, persist_dir: str = "/root/LIBERTUS/memoria/chroma"):
        """
        Inicializa sistema RAG
        
        Args:
            persist_dir: Diretório para persistir banco vetorial
        """
        self.persist_dir = persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        # Cliente ChromaDB
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Collection principal
        self.collection = self.client.get_or_create_collection(
            name="libertus_knowledge",
            metadata={"description": "Conhecimento absorvido de PDFs"}
        )
        
        print(f"✅ RAG inicializado: {self.collection.count()} documentos")
    
    def absorver_texto(self, texto: str, metadata: Dict[str, Any]) -> str:
        """
        Absorve texto no banco vetorial
        
        Args:
            texto: Texto a ser indexado
            metadata: Metadados (arquivo, página, etc)
            
        Returns:
            ID do documento indexado
        """
        # Gerar ID único
        doc_id = hashlib.md5(texto.encode()).hexdigest()
        
        # Indexar
        self.collection.add(
            documents=[texto],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def absorver_pdf_simples(self, pdf_path: str) -> List[str]:
        """
        Absorve PDF usando extração simples (PyPDF2)
        Docling será integrado depois para PDFs complexos
        
        Args:
            pdf_path: Caminho do PDF
            
        Returns:
            Lista de IDs dos documentos indexados
        """
        try:
            import PyPDF2
            
            doc_ids = []
            
            with open(pdf_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                
                for i, page in enumerate(pdf.pages):
                    texto = page.extract_text()
                    
                    if texto.strip():
                        metadata = {
                            "source": os.path.basename(pdf_path),
                            "page": i + 1,
                            "type": "pdf"
                        }
                        
                        doc_id = self.absorver_texto(texto, metadata)
                        doc_ids.append(doc_id)
            
            print(f"✅ PDF absorvido: {len(doc_ids)} páginas de {os.path.basename(pdf_path)}")
            return doc_ids
            
        except Exception as e:
            print(f"❌ Erro ao absorver PDF: {e}")
            return []
    
    def buscar_conhecimento(self, pergunta: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Busca conhecimento relevante
        
        Args:
            pergunta: Pergunta do usuário
            n_results: Número de resultados
            
        Returns:
            Lista de documentos relevantes com metadados
        """
        try:
            results = self.collection.query(
                query_texts=[pergunta],
                n_results=min(n_results, self.collection.count())
            )
            
            # Formatar resultados
            documentos = []
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    documentos.append({
                        'texto': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distancia': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return documentos
            
        except Exception as e:
            print(f"❌ Erro ao buscar: {e}")
            return []
    
    def listar_fontes(self) -> List[str]:
        """Lista todas as fontes de conhecimento absorvidas"""
        try:
            # Pegar todos os metadados
            all_data = self.collection.get()
            
            if not all_data['metadatas']:
                return []
            
            # Extrair fontes únicas
            fontes = set()
            for meta in all_data['metadatas']:
                if 'source' in meta:
                    fontes.add(meta['source'])
            
            return sorted(list(fontes))
            
        except Exception as e:
            print(f"❌ Erro ao listar fontes: {e}")
            return []
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema"""
        return {
            'total_documentos': self.collection.count(),
            'fontes': self.listar_fontes(),
            'persist_dir': self.persist_dir
        }


# Teste rápido
if __name__ == "__main__":
    rag = LibertusRAG()
    
    # Teste com texto simples
    rag.absorver_texto(
        "SQL Injection é uma vulnerabilidade onde atacante injeta código SQL malicioso",
        {"source": "teste.txt", "type": "text"}
    )
    
    # Buscar
    resultados = rag.buscar_conhecimento("como funciona SQL injection")
    print(f"\n📊 Resultados: {len(resultados)}")
    for r in resultados:
        print(f"  - {r['texto'][:100]}...")
    
    print(f"\n📈 Stats: {rag.stats()}")
