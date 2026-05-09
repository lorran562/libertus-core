#!/usr/bin/env python3
"""
LIBERTUS REVERSE ENGINEERING MODULE
Engenharia reversa de JS, binários, APIs

CAPACIDADES:
- JS deobfuscation (eval, packed, minified)
- API endpoint extraction
- Hardcoded secrets detection
- Binary string analysis
- Protocol reverse engineering
- Source map recovery
"""

import re
import base64
import json
from typing import List, Dict, Optional
import subprocess

class LibertusReverse:
    """Engenharia reversa e análise de código"""
    
    def __init__(self):
        self.secrets_patterns = self._load_secret_patterns()
        self.api_patterns = self._load_api_patterns()
    
    def _load_secret_patterns(self) -> Dict[str, str]:
        """Padrões para detectar secrets hardcoded"""
        return {
            'aws_key': r'AKIA[0-9A-Z]{16}',
            'aws_secret': r'aws_secret_access_key\s*=\s*["\']([^"\']+)["\']',
            'google_api': r'AIza[0-9A-Za-z\\-_]{35}',
            'github_token': r'gh[pousr]_[0-9a-zA-Z]{36}',
            'slack_token': r'xox[baprs]-[0-9]{10,12}-[0-9]{10,12}-[0-9a-zA-Z]{24,32}',
            'stripe_key': r'sk_live_[0-9a-zA-Z]{24,}',
            'jwt': r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*',
            'private_key': r'-----BEGIN [A-Z ]+ PRIVATE KEY-----',
            'password': r'password\s*[=:]\s*["\']([^"\']+)["\']',
            'api_key': r'api[_-]?key\s*[=:]\s*["\']([^"\']+)["\']',
            'secret': r'secret\s*[=:]\s*["\']([^"\']+)["\']',
            'token': r'token\s*[=:]\s*["\']([^"\']+)["\']',
        }
    
    def _load_api_patterns(self) -> List[str]:
        """Padrões para detectar endpoints de API"""
        return [
            r'/api/v\d+/[a-z_/]+',
            r'/api/[a-z_/]+',
            r'https?://[a-zA-Z0-9.-]+/api/[^\s"\']+',
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']',
            r'\.ajax\({[^}]*url:\s*["\']([^"\']+)["\']',
        ]
    
    def deobfuscate_js(self, js_code: str) -> Dict:
        """Desobfusca JavaScript"""
        results = {
            'original_size': len(js_code),
            'deobfuscated': None,
            'secrets_found': [],
            'apis_found': [],
            'techniques_used': []
        }
        
        # 1. Detecta tipo de ofuscação
        if 'eval(function(p,a,c,k,e,d)' in js_code:
            results['techniques_used'].append('packer')
            deobfuscated = self._unpack_packer(js_code)
            if deobfuscated:
                js_code = deobfuscated
                results['deobfuscated'] = deobfuscated
        
        # 2. Base64 decode
        if re.search(r'atob\(["\']([A-Za-z0-9+/=]+)["\']\)', js_code):
            results['techniques_used'].append('base64')
            js_code = self._decode_base64_strings(js_code)
        
        # 3. String concatenation
        if re.search(r'["\'][^"\']*["\']\s*\+\s*["\']', js_code):
            results['techniques_used'].append('string_concat')
            js_code = self._merge_string_concat(js_code)
        
        # 4. Hex encoding
        if r'\x' in js_code:
            results['techniques_used'].append('hex_encoding')
            js_code = self._decode_hex_strings(js_code)
        
        # 5. Procura secrets
        results['secrets_found'] = self.find_secrets(js_code)
        
        # 6. Procura APIs
        results['apis_found'] = self.find_api_endpoints(js_code)
        
        results['final_code'] = js_code
        results['final_size'] = len(js_code)
        
        return results
    
    def _unpack_packer(self, packed_code: str) -> Optional[str]:
        """Descompacta código packed com Dean Edwards Packer"""
        try:
            # Extrai a função eval
            match = re.search(r"eval\(function\(p,a,c,k,e,d\){(.+?)}\((.+?)\)\)", 
                            packed_code, re.DOTALL)
            if not match:
                return None
            
            # Executa em Node.js para desempacotar
            # (Em produção, usar biblioteca JS em Python ou sandbox)
            # Por enquanto, retorna indicação
            return f"// PACKED CODE DETECTED\n{packed_code[:500]}..."
        
        except Exception as e:
            return None
    
    def _decode_base64_strings(self, code: str) -> str:
        """Decodifica strings base64"""
        def replace_b64(match):
            try:
                decoded = base64.b64decode(match.group(1)).decode('utf-8')
                return f'"{decoded}"'
            except:
                return match.group(0)
        
        return re.sub(r'atob\(["\']([A-Za-z0-9+/=]+)["\']\)', replace_b64, code)
    
    def _merge_string_concat(self, code: str) -> str:
        """Junta concatenações de strings"""
        # Simplificado - em produção, usar AST parser
        pattern = r'["\']([^"\']*)["\'] *\+ *["\']([^"\']*)["\']'
        
        def merge(match):
            return f'"{match.group(1)}{match.group(2)}"'
        
        # Aplica múltiplas vezes até não ter mais mudanças
        prev = ""
        while prev != code:
            prev = code
            code = re.sub(pattern, merge, code)
        
        return code
    
    def _decode_hex_strings(self, code: str) -> str:
        """Decodifica strings hex (\\x41\\x42)"""
        def decode_hex(match):
            hex_str = match.group(0)
            try:
                # Remove \x e converte
                cleaned = hex_str.replace('\\x', '')
                decoded = bytes.fromhex(cleaned).decode('utf-8')
                return f'"{decoded}"'
            except:
                return hex_str
        
        return re.sub(r'((?:\\x[0-9a-fA-F]{2})+)', decode_hex, code)
    
    def find_secrets(self, code: str) -> List[Dict]:
        """Encontra secrets hardcoded"""
        secrets = []
        
        for secret_type, pattern in self.secrets_patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                secret_value = match.group(0)
                if match.groups():
                    secret_value = match.group(1)
                
                secrets.append({
                    'type': secret_type,
                    'value': secret_value,
                    'severity': 'CRITICAL',
                    'position': match.start()
                })
        
        return secrets
    
    def find_api_endpoints(self, code: str) -> List[str]:
        """Encontra endpoints de API no código"""
        endpoints = set()
        
        for pattern in self.api_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                if match.groups():
                    endpoint = match.group(1) if len(match.groups()) >= 1 else match.group(0)
                else:
                    endpoint = match.group(0)
                endpoints.add(endpoint)
        
        return list(endpoints)
    
    def analyze_binary(self, binary_path: str) -> Dict:
        """Analisa binário em busca de secrets"""
        results = {
            'strings_found': [],
            'secrets_found': [],
            'interesting_imports': [],
            'urls_found': []
        }
        
        try:
            # Extrai strings do binário
            output = subprocess.run(
                ['strings', binary_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            strings = output.stdout.split('\n')
            
            # Filtra strings interessantes (>5 chars)
            interesting = [s for s in strings if len(s) > 5]
            results['strings_found'] = interesting[:100]  # Top 100
            
            # Procura secrets nas strings
            full_text = '\n'.join(strings)
            results['secrets_found'] = self.find_secrets(full_text)
            
            # Procura URLs
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, full_text)
            results['urls_found'] = list(set(urls))
            
            # Procura imports suspeitos (se for ELF/PE)
            suspicious_imports = [
                'system', 'exec', 'shell', 'cmd',
                'socket', 'connect', 'send', 'recv',
                'CreateProcess', 'ShellExecute'
            ]
            
            for imp in suspicious_imports:
                if imp in full_text:
                    results['interesting_imports'].append(imp)
        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def extract_sourcemap(self, js_url: str) -> Optional[Dict]:
        """Tenta recuperar source map"""
        # Verifica se há comentário //# sourceMappingURL=
        # Baixa e parseia source map
        # Retorna código original
        pass  # Implementar
    
    def analyze_webpack_bundle(self, bundle_code: str) -> Dict:
        """Analisa bundle webpack para extrair módulos"""
        results = {
            'modules_found': 0,
            'entry_points': [],
            'dependencies': []
        }
        
        # Detecta padrão webpack
        webpack_pattern = r'webpackJsonp\(\[(.*?)\],'
        if re.search(webpack_pattern, bundle_code):
            results['is_webpack'] = True
            # Extrair módulos
            # Em produção: parser completo
        
        return results


# Exemplo
if __name__ == "__main__":
    rev = LibertusReverse()
    
    # Test JS deobfuscation
    obfuscated = '''
    var _0x1234 = ["password", "admin123", "https://api.example.com/users"];
    eval(atob("Y29uc29sZS5sb2coImhhY2tlZCIp"));
    '''
    
    result = rev.deobfuscate_js(obfuscated)
    print("Secrets found:", result['secrets_found'])
    print("APIs found:", result['apis_found'])
