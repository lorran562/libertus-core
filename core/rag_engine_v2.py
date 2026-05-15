import chromadb
from pathlib import Path
from typing import List, Dict
import hashlib

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("⚠️ Docling não instalado - usando fallback simples")

class RAGEngineV2:
    """RAG com Docling (se disponível) ou fallback PyPDF2"""
    
    def __init__(self, persist_dir: str = "~/LIBERTUS/memoria/chroma_db"):
        self.persist_dir = Path(persist_dir).expanduser()
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name="libertus_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        
        if DOCLING_AVAILABLE:
            self.converter = DocumentConverter()
        else:
            self.converter = None
    
    async def ingest_pdf(self, pdf_path: str, metadata: Dict = None):
        """Ingere PDF - usa Docling se disponível"""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
        
        if DOCLING_AVAILABLE and self.converter:
            chunks = await self._ingest_with_docling(pdf_path)
        else:
            chunks = await self._ingest_fallback(pdf_path)
        
        file_hash = hashlib.md5(pdf_path.read_bytes()).hexdigest()[:12]
        
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk['content'])
            metadatas.append({
                'source': str(pdf_path.name),
                'section': chunk.get('section', 'Unknown'),
                'type': chunk.get('type', 'text'),
                'context': chunk.get('context', ''),
                'file_hash': file_hash,
                'chunk_id': i,
                **(metadata or {})
            })
            ids.append(f"{file_hash}_{i}")
        
        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"✅ PDF ingerido: {pdf_path.name} ({len(chunks)} chunks)")
    
    async def _ingest_with_docling(self, pdf_path: Path) -> List[Dict]:
        """Parse com Docling - estruturado"""
        result = self.converter.convert(str(pdf_path))
        doc = result.document
        
        elements = []
        current_section = "Introdução"
        
        for item in doc.items:
            element = {
                'type': getattr(item, 'type', 'paragraph'),
                'content': getattr(item, 'text', ''),
                'section': current_section,
            }
            
            if element['type'] in ['heading', 'title']:
                current_section = element['content']
                element['is_section_start'] = True
            elif element['type'] == 'code':
                element['content'] = f"[CODE]\n{element['content']}\n[/CODE]"
            elif element['type'] == 'table':
                element['content'] = f"[TABLE]\n{item.export_to_markdown()}\n[/TABLE]"
            
            elements.append(element)
        
        return self._create_semantic_chunks(elements)
    
    async def _ingest_fallback(self, pdf_path: Path) -> List[Dict]:
        """Fallback sem Docling"""
        import PyPDF2
        
        text = ""
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        chunks = []
        chunk_size = 800
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i+chunk_size]
            if len(chunk_text.strip()) > 50:
                chunks.append({
                    'content': chunk_text,
                    'section': 'Documento',
                    'type': 'text',
                    'context': ''
                })
        
        return chunks
    
    def _create_semantic_chunks(self, elements: List[Dict]) -> List[Dict]:
        """Chunking inteligente baseado em seções"""
        chunks = []
        current_chunk = {'content': '', 'section': '', 'type': 'text', 'context': ''}
        
        for elem in elements:
            if elem.get('is_section_start'):
                if current_chunk['content'].strip():
                    chunks.append(current_chunk.copy())
                current_chunk = {
                    'content': elem['content'],
                    'section': elem['content'],
                    'type': 'text',
                    'context': elem['content']
                }
                continue
            
            if elem['type'] == 'code':
                if current_chunk['content'].strip():
                    chunks.append(current_chunk.copy())
                chunks.append({
                    'content': elem['content'],
                    'section': current_chunk['section'],
                    'type': 'code',
                    'context': f"Seção: {current_chunk['section']}"
                })
                current_chunk = {
                    'content': '', 'section': current_chunk['section'],
                    'type': 'text', 'context': current_chunk['section']
                }
                continue
            
            current_chunk['content'] += f"\n{elem['content']}"
            
            if len(current_chunk['content']) > 1000:
                chunks.append(current_chunk.copy())
                current_chunk = {
                    'content': '', 'section': current_chunk['section'],
                    'type': 'text', 'context': current_chunk['section']
                }
        
        if current_chunk['content'].strip():
            chunks.append(current_chunk)
        
        return chunks
    
    async def retrieve(self, query: str, top_k: int = 3, prefer_code: bool = False) -> str:
        """Recupera conhecimento relevante"""
        results = self.collection.query(query_texts=[query], n_results=top_k * 2)
        
        if not results['documents'] or not results['documents'][0]:
            return "[CONTEXTO RELEVANTE]\nNenhum conhecimento encontrado.\n\n[INSTRUÇÃO]\nResponda com base no seu conhecimento geral."
        
        chunks = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            chunks.append({
                'content': doc,
                'type': meta['type'],
                'section': meta['section'],
                'source': meta['source'],
                'context': meta.get('context', '')
            })
        
        if prefer_code or any(kw in query.lower() for kw in ['código', 'script', 'função', 'como fazer']):
            chunks.sort(key=lambda x: 0 if x['type'] == 'code' else 1)
        
        chunks = chunks[:top_k]
        
        formatted = "[CONTEXTO RELEVANTE]\n\n"
        for chunk in chunks:
            formatted += f"Fonte: {chunk['source']}\nSeção: {chunk['section']}\nTipo: {chunk['type']}\n"
            if chunk['context']:
                formatted += f"Contexto: {chunk['context']}\n"
            formatted += f"\n{chunk['content']}\n\n---\n\n"
        
        formatted += "[INSTRUÇÃO]\nResponda com base APENAS no contexto acima.\n"
        
        return formatted
    
    async def ingest_directory(self, dir_path: str):
        """Ingere todos PDFs"""
        dir_path = Path(dir_path)
        for pdf_file in dir_path.glob("**/*.pdf"):
            try:
                await self.ingest_pdf(str(pdf_file))
            except Exception as e:
                print(f"❌ Erro: {pdf_file}: {e}")
