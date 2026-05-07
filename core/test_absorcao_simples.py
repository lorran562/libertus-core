#!/usr/bin/env python3
"""
Teste simples de absorção - bypass do módulo complexo
"""
import sys
from pathlib import Path

print("🧪 TESTE SIMPLES DE ABSORÇÃO DOCLING\n")

# 1. Carrega Docling
print("1. Carregando Docling...")
from docling.document_converter import DocumentConverter
converter = DocumentConverter()
print("   ✅ Docling carregado!\n")

# 2. Lista PDFs disponíveis
print("2. PDFs na biblioteca:")
pdfs = [
    ("Pentest", "https://www.offensive-security.com/pwk-online/PWK-Example-Report-v1.pdf"),
]
for nome, url in pdfs:
    print(f"   - {nome}: {url}")
print()

# 3. Tenta baixar primeiro PDF
print("3. Testando download do primeiro PDF...")
import requests
try:
    response = requests.get(pdfs[0][1], timeout=30)
    if response.status_code == 200:
        print(f"   ✅ Download sucesso! Tamanho: {len(response.content)} bytes")
        
        # Salva temporariamente
        temp_pdf = Path("/tmp/test_pentest.pdf")
        temp_pdf.write_bytes(response.content)
        print(f"   💾 Salvo em: {temp_pdf}")
    else:
        print(f"   ❌ HTTP {response.status_code}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n✅ Teste concluído!")
