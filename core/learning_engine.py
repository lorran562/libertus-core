#!/usr/bin/env python3
"""
LIBERTUS LEARNING ENGINE
Aprendizado autônomo via PDFs (Docling) + Papers (ArXiv)
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

try:
    from docling.document_converter import DocumentConverter
    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class LearningEngine:
    """
    Engine de aprendizado autônomo
    - PDFs via Docling
    - Papers via ArXiv API
    - Integração com Groq LLM
    """
    
    def __init__(self, groq_client=None):
        self.groq_client = groq_client
        self.knowledge_dir = os.path.expanduser("~/LIBERTUS/knowledge_base")
        os.makedirs(self.knowledge_dir, exist_ok=True)
    
    async def learn_from_arxiv(self, topic: str, max_papers: int = 3) -> Dict:
        """Busca papers no ArXiv e aprende"""
        
        if not HAS_AIOHTTP:
            return {"error": "aiohttp não instalado"}
        
        print(f"📚 Buscando papers sobre: {topic}")
        
        # Buscar no ArXiv
        search_query = topic.replace(" ", "+")
        url = f"http://export.arxiv.org/api/query?search_query=all:{search_query}&start=0&max_results={max_papers}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    xml_data = await resp.text()
                    
                    # Parse simples (sem XML parser)
                    papers = []
                    entries = xml_data.split("<entry>")[1:]
                    
                    for entry in entries[:max_papers]:
                        title_start = entry.find("<title>") + 7
                        title_end = entry.find("</title>")
                        title = entry[title_start:title_end].strip()
                        
                        summary_start = entry.find("<summary>") + 9
                        summary_end = entry.find("</summary>")
                        summary = entry[summary_start:summary_end].strip()
                        
                        link_start = entry.find('href="') + 6
                        link_end = entry.find('"', link_start)
                        link = entry[link_start:link_end]
                        
                        papers.append({
                            "title": title,
                            "summary": summary[:500],
                            "link": link
                        })
                    
                    print(f"   ✅ {len(papers)} papers encontrados")
                    
                    # Processar com LLM
                    if self.groq_client and papers:
                        knowledge = await self._summarize_with_llm(topic, papers)
                        
                        # Salvar
                        filename = topic.replace(" ", "_").lower()[:50] + "_arxiv.json"
                        filepath = os.path.join(self.knowledge_dir, filename)
                        
                        with open(filepath, "w") as f:
                            json.dump({
                                "topic": topic,
                                "source": "arxiv",
                                "papers": papers,
                                "summary": knowledge,
                                "timestamp": datetime.now().isoformat()
                            }, f, indent=2)
                        
                        return {
                            "success": True,
                            "papers_count": len(papers),
                            "summary": knowledge,
                            "filepath": filepath
                        }
                    
                    return {"success": True, "papers": papers}
            
            except Exception as e:
                return {"error": str(e)}
    
    def learn_from_pdf(self, pdf_path: str) -> Dict:
        """Aprende com PDF via Docling"""
        
        if not HAS_DOCLING:
            return {"error": "Docling não instalado"}
        
        try:
            print(f"📄 Processando PDF: {pdf_path}")
            
            converter = DocumentConverter()
            result = converter.convert(pdf_path)
            
            text = result.document.export_to_markdown()
            
            print(f"   ✅ {len(text)} caracteres extraídos")
            
            return {
                "success": True,
                "text": text,
                "length": len(text)
            }
        
        except Exception as e:
            return {"error": str(e)}
    
    async def _summarize_with_llm(self, topic: str, papers: List[Dict]) -> str:
        """Resume papers com LLM"""
        
        papers_text = "\n\n".join([
            f"Paper: {p['title']}\nSummary: {p['summary']}"
            for p in papers
        ])
        
        prompt = f"""Analise estes papers sobre {topic} e extraia:

1. Principais vulnerabilidades descobertas
2. Técnicas de exploração
3. Payloads específicos mencionados
4. Contramedidas recomendadas

Papers:
{papers_text}

Resuma em formato técnico para uso em scanner de segurança."""
        
        try:
            response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Erro ao resumir: {str(e)}"


# Teste
if __name__ == "__main__":
    async def test():
        engine = LearningEngine()
        result = await engine.learn_from_arxiv("SQL Injection", max_papers=2)
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
