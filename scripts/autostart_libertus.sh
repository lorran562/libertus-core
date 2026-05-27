#!/bin/bash
# LIBERTUS Autostart — abre terminal com briefing matinal

sleep 3  # aguarda desktop carregar

gnome-terminal \
  --title="LIBERTUS" \
  --geometry=100x30+100+100 \
  -- bash -c "
    echo ''
    echo '╔══════════════════════════════════════════╗'
    echo '║           L I B E R T U S               ║'
    echo '║        Seu escudo digital — SHIELD       ║'
    echo '╚══════════════════════════════════════════╝'
    echo ''
    python3 ~/LIBERTUS/scripts/morning_brief.py
    echo ''
    echo '----------------------------------------'
    echo 'Para conversar: hermes chat'
    echo '----------------------------------------'
    exec bash
  "
