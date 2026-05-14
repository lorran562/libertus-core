# ⚡ LIBERTUS - COMANDOS RÁPIDOS

**Use este arquivo como referência rápida!**

---

## 🎯 ADICIONAR UM SITE PARA ESCANEAR

```bash
cd ~/LIBERTUS/core
python3 -c "
from target_manager import TargetManager, Priority
manager = TargetManager()
manager.add_target('SEU-SITE.com.br', Priority.CRITICAL.value, 'Descrição')
"
```

**Prioridades:**
- `Priority.CRITICAL.value` = 1 (escaneia PRIMEIRO)
- `Priority.HIGH.value` = 2
- `Priority.MEDIUM.value` = 3  
- `Priority.LOW.value` = 4 (escaneia POR ÚLTIMO)

---

## 📊 VER STATUS DO SISTEMA

```bash
# Ver se daemon está rodando
ps aux | grep production_daemon | grep -v grep

# Ver logs em tempo real
tail -f ~/LIBERTUS/logs/production_daemon.log

# Ver estatísticas
cd ~/LIBERTUS/core && python3 -c "from target_manager import TargetManager; import json; print(json.dumps(TargetManager().get_stats(), indent=2))"
```

---

## 🔄 CONTROLAR O DAEMON

```bash
# Parar
pkill -f production_daemon.py

# Iniciar
cd ~/LIBERTUS/core && nohup python3 production_daemon.py > /dev/null 2>&1 &

# Reiniciar
pkill -f production_daemon.py && cd ~/LIBERTUS/core && nohup python3 production_daemon.py > /dev/null 2>&1 &
```

---

## 📄 VER RELATÓRIOS

```bash
# Listar relatórios
ls -lht ~/LIBERTUS/relatorios/ | head -10

# Ver último relatório
cat $(ls -t ~/LIBERTUS/relatorios/*.md | head -1)

# Ver relatório específico (Laboratório São José)
cat ~/LIBERTUS/relatorios/RELATORIO_PROFISSIONAL_Laboratorio_Sao_Jose_*.md
```

---

## 🎯 TARGETS

```bash
# Listar todos
cd ~/LIBERTUS/core && python3 -c "from target_manager import TargetManager; [print(f'{t.url}: scans={t.scan_count}, vulns={t.vulnerabilities_found}') for t in TargetManager().get_all_targets()]"

# Ver próximo target
cd ~/LIBERTUS/core && python3 -c "from target_manager import TargetManager; t = TargetManager().get_next_target(); print(f'{t.url} (priority={t.priority})' if t else 'Nenhum')"
```

---

## 🔍 ESCANEAR UM SITE AGORA (MANUAL)

```bash
cd ~/LIBERTUS/core
python3 libertus_scanner_final.py SEU-SITE.com.br
```

---

## 📞 DADOS DE CONTATO (SHIELD)

WhatsApp: **(69) 99290-5682**  
Email: **josefernandes6340@gmail.com**  
Instagram: **@shieldweb**

---

## ⚠️ EMERGÊNCIA

```bash
# Se algo der errado, reiniciar TUDO:
cd ~/LIBERTUS
git pull origin main
pkill -f production_daemon.py
cd core && nohup python3 production_daemon.py > /dev/null 2>&1 &
tail -f logs/production_daemon.log
```

---

**ATALHO:** Salve este arquivo e sempre consulte quando precisar! 📌
