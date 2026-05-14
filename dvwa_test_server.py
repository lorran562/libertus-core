#!/usr/bin/env python3
"""
DVWA SIMPLIFICADO - Servidor vulnerável para testes do LIBERTUS
NÃO USE EM PRODUÇÃO - APENAS PARA TESTES
"""

from flask import Flask, request, render_template_string
import sqlite3
import time

app = Flask(__name__)

# Criar banco de dados vulnerável
def init_db():
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT
        )
    ''')
    cursor.execute("DELETE FROM users")
    cursor.execute("INSERT INTO users VALUES (1, 'admin', 'password123', 'admin@test.com')")
    cursor.execute("INSERT INTO users VALUES (2, 'user', 'user123', 'user@test.com')")
    conn.commit()
    conn.close()

init_db()

# VULNERABILIDADE 1: SQL Injection
@app.route('/sqli')
def sqli():
    user_id = request.args.get('id', '1')
    
    # VULNERÁVEL: Sem sanitização
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()
    
    try:
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        
        if result:
            return f"User found: {result}"
        else:
            return "User not found"
    except Exception as e:
        return f"SQL Error: {str(e)}"

# VULNERABILIDADE 2: XSS Reflected
@app.route('/xss')
def xss():
    search = request.args.get('search', '')
    
    # VULNERÁVEL: Sem sanitização
    html = f'''
    <html>
    <body>
        <h1>Search Results</h1>
        <p>You searched for: {search}</p>
        <form>
            <input name="search" value="{search}">
            <button>Search</button>
        </form>
    </body>
    </html>
    '''
    
    return html

# VULNERABILIDADE 3: Time-based SQLi
@app.route('/sqli_time')
def sqli_time():
    user_id = request.args.get('id', '1')
    
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()
    
    try:
        # Simular SLEEP() do MySQL
        if 'SLEEP' in user_id.upper():
            time.sleep(5)
        
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

# Página inicial
@app.route('/')
def index():
    return '''
    <html>
    <body>
        <h1>DVWA Simplificado - Teste do LIBERTUS</h1>
        <ul>
            <li><a href="/sqli?id=1">SQL Injection Test</a></li>
            <li><a href="/xss?search=test">XSS Test</a></li>
            <li><a href="/sqli_time?id=1">Time-based SQLi Test</a></li>
        </ul>
        <p><b>ATENÇÃO:</b> Site vulnerável APENAS para testes!</p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🔬 DVWA Simplificado iniciando...")
    print("URL: http://localhost:8080")
    print("")
    print("Endpoints vulneráveis:")
    print("- /sqli?id=1 (SQL Injection)")
    print("- /xss?search=test (XSS Reflected)")
    print("- /sqli_time?id=1 (Time-based SQLi)")
    print("")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
