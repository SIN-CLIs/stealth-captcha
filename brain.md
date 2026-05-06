# brain.md — Architektur (stealth-captcha)

> **← [stealth-runner/brain.md](https://github.com/OpenSIN-AI/stealth-runner/blob/main/brain.md) für Gesamtarchitektur**

---

## Repo-Architektur

- **Layer**: 🔒 CAPTCHA
- **Beschreibung**: Captcha Solver — GeeTest, reCAPTCHA, Text-OCR
- **Technologie**: (Dokumentation folgt)

## Stealth Suite Integration

Dieses Repo ist Teil der Stealth Suite und MUSS:
1. CUA-ONLY Architektur respektieren
2. Pipeline (perceive→plan→guard→execute→critique) einhalten
3. BANNED Tools vermeiden

## Abhängigkeiten

- [stealth-runner](https://github.com/OpenSIN-AI/stealth-runner) — Orchestrator
- DOC-HEALTH: `python3 /Users/jeremy/dev/stealth-runner/scripts/check_doc_health.py --repo stealth-captcha`

**Letztes Update**: 2026-05-05
