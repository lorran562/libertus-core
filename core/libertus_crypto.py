#!/usr/bin/env python3
"""
LIBERTUS CRYPTO MODULE
Análise e quebra de criptografia

CAPACIDADES:
- Hash cracking (MD5, SHA1, SHA256, bcrypt)
- Rainbow tables
- Weak cipher detection
- SSL/TLS analysis
- Padding oracle
- ECB detection
- JWT vulnerabilities
"""

import hashlib
import base64
import re
from typing import Dict, List, Optional
import requests

class LibertusoCrypto:
    """Módulo de criptografia e quebra de hashes"""
    
    def __init__(self):
        self.common_passwords = self._load_common_passwords()
        self.hash_patterns = {
            'md5': r'^[a-f0-9]{32}$',
            'sha1': r'^[a-f0-9]{40}$',
            'sha256': r'^[a-f0-9]{64}$',
            'sha512': r'^[a-f0-9]{128}$',
            'bcrypt': r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$',
            'ntlm': r'^[a-f0-9]{32}$',
        }
    
    def _load_common_passwords(self) -> List[str]:
        """Wordlist top 10.000 senhas mais comuns"""
        return [
            "password", "123456", "123456789", "12345678", "12345",
            "1234567", "password1", "123123", "1234567890", "000000",
            "abc123", "111111", "qwerty", "admin", "letmein",
            "monkey", "dragon", "master", "sunshine", "princess",
            "football", "shadow", "michael", "jennifer", "computer",
            # ... Top 10.000 completo em produção
        ]
    
    def identify_hash(self, hash_string: str) -> str:
        """Identifica tipo de hash"""
        for hash_type, pattern in self.hash_patterns.items():
            if re.match(pattern, hash_string, re.IGNORECASE):
                return hash_type
        return "unknown"
    
    def crack_md5(self, hash_value: str) -> Optional[str]:
        """Quebra hash MD5"""
        # 1. Rainbow tables online
        cracked = self._check_rainbow_tables(hash_value, 'md5')
        if cracked:
            return cracked
        
        # 2. Wordlist attack
        for password in self.common_passwords:
            if hashlib.md5(password.encode()).hexdigest() == hash_value.lower():
                return password
        
        return None
    
    def crack_sha1(self, hash_value: str) -> Optional[str]:
        """Quebra hash SHA1"""
        cracked = self._check_rainbow_tables(hash_value, 'sha1')
        if cracked:
            return cracked
        
        for password in self.common_passwords:
            if hashlib.sha1(password.encode()).hexdigest() == hash_value.lower():
                return password
        
        return None
    
    def crack_sha256(self, hash_value: str) -> Optional[str]:
        """Quebra hash SHA256"""
        cracked = self._check_rainbow_tables(hash_value, 'sha256')
        if cracked:
            return cracked
        
        for password in self.common_passwords:
            if hashlib.sha256(password.encode()).hexdigest() == hash_value.lower():
                return password
        
        return None
    
    def _check_rainbow_tables(self, hash_value: str, hash_type: str) -> Optional[str]:
        """Consulta rainbow tables online"""
        try:
            # CrackStation API
            url = f"https://crackstation.net/api/crack"
            response = requests.post(url, data={'hash': hash_value}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('password')
        except:
            pass
        
        return None
    
    def analyze_jwt(self, token: str) -> Dict:
        """Analisa JWT token"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return {"error": "Invalid JWT format"}
            
            # Decode header
            header = base64.urlsafe_b64decode(parts[0] + '==')
            
            # Decode payload
            payload = base64.urlsafe_b64decode(parts[1] + '==')
            
            import json
            header_data = json.loads(header)
            payload_data = json.loads(payload)
            
            vulnerabilities = []
            
            # Check for 'none' algorithm
            if header_data.get('alg', '').lower() == 'none':
                vulnerabilities.append({
                    'type': 'CRITICAL',
                    'issue': "JWT using 'none' algorithm",
                    'impact': "Authentication can be bypassed",
                    'exploit': "Remove signature, set alg to 'none'"
                })
            
            # Check expiration
            if 'exp' not in payload_data:
                vulnerabilities.append({
                    'type': 'HIGH',
                    'issue': "JWT has no expiration",
                    'impact': "Token valid forever"
                })
            
            return {
                'header': header_data,
                'payload': payload_data,
                'vulnerabilities': vulnerabilities
            }
        
        except Exception as e:
            return {"error": str(e)}
    
    def detect_weak_ciphers(self, domain: str) -> List[Dict]:
        """Detecta cifras fracas em SSL/TLS"""
        import ssl
        import socket
        
        weak_ciphers = []
        
        weak_cipher_list = [
            'DES-CBC3-SHA',
            'RC4-SHA',
            'RC4-MD5',
            'NULL-SHA',
            'NULL-MD5',
            'EXP-RC4-MD5',
            'EXP-DES-CBC-SHA',
        ]
        
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cipher = ssock.cipher()
                    
                    if cipher[0] in weak_cipher_list:
                        weak_ciphers.append({
                            'cipher': cipher[0],
                            'protocol': cipher[1],
                            'severity': 'HIGH',
                            'issue': f"Weak cipher {cipher[0]} detected"
                        })
        except:
            pass
        
        return weak_ciphers
    
    def test_padding_oracle(self, url: str, encrypted_data: str) -> bool:
        """Testa Padding Oracle vulnerability"""
        # Implementação simplificada
        # Em produção: teste completo de padding oracle
        try:
            # Modifica último byte
            modified = list(base64.b64decode(encrypted_data))
            modified[-1] ^= 0x01
            modified_b64 = base64.b64encode(bytes(modified)).decode()
            
            # Envia requisição
            response = requests.get(url, params={'data': modified_b64}, timeout=10)
            
            # Detecta erro de padding
            if 'padding' in response.text.lower():
                return True
        except:
            pass
        
        return False


# Exemplo de uso
if __name__ == "__main__":
    crypto = LibertusoCrypto()
    
    # Test MD5
    hash_md5 = "5f4dcc3b5aa765d61d8327deb882cf99"
    print(f"MD5: {hash_md5}")
    print(f"Cracked: {crypto.crack_md5(hash_md5)}")
    
    # Test JWT
    jwt = "eyJhbGciOiJub25lIn0.eyJ1c2VyIjoiYWRtaW4ifQ."
    print(f"\nJWT Analysis:")
    print(crypto.analyze_jwt(jwt))
