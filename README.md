# SmartSplit

SmartSplit ist ein modular aufgebauter MVP einer Splitwise-Alternative auf Basis von Streamlit, SQLite und scikit-learn. Die App unterstuetzt Registrierung, Login, Gruppenverwaltung, Ausgaben, Zahlungsabgleich, Verzugszinsen und eine einfache ML-Schaetzung zur Rueckzahlungsdauer.

## Projektstruktur

```text
smartsplit/
├── app.py
├── Main.py
├── requirements.txt
├── README.md
├── database/
│   ├── __init__.py
│   ├── db.py
│   ├── init_db.py
│   └── models.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── expense_service.py
│   ├── group_service.py
│   ├── interest_service.py
│   ├── ml_service.py
│   └── payment_service.py
├── ui/
│   ├── __init__.py
│   ├── auth_pages.py
│   ├── dashboard.py
│   ├── expenses.py
│   ├── groups.py
│   ├── ml_analysis.py
│   └── payments.py
└── utils/
    ├── __init__.py
    ├── helpers.py
    └── seed_data.py
```

## Features

- Registrierung und Login mit gehashten Passwoertern
- Gruppen erstellen und Mitglieder per E-Mail hinzufuegen
- Ausgaben in Gruppen erfassen und gleichmaessig aufteilen
- Offene Forderungen, Verbindlichkeiten und Transaktionsvorschlaege berechnen
- Zahlungen verbuchen und Verlauf anzeigen
- Verzugszinsen ab dem 15. Tag mit 0,5 % pro Woche
- ML-Schaetzung der Rueckzahlungsdauer auf Basis historischer Zahlungen
- Seed-Daten fuer eine direkte Demo

## Demo-Zugaenge

Nach dem ersten Start werden Seed-Daten erzeugt:

- `alice@smartsplit.local` / `Password123!`
- `bob@smartsplit.local` / `Password123!`
- `carla@smartsplit.local` / `Password123!`

## Installation

1. Virtuelle Umgebung erstellen:

```powershell
python -m venv .venv
```

2. Virtuelle Umgebung aktivieren:

```powershell
.venv\Scripts\Activate.ps1
```

3. Abhaengigkeiten installieren:

```powershell
pip install -r requirements.txt
```

## Start

```powershell
streamlit run app.py
```

## Hinweise zur Architektur

- `database/` kapselt Schema, Verbindungsaufbau und Initialisierung.
- `services/` enthaelt die Geschaeftslogik fuer Auth, Gruppen, Ausgaben, Zahlungen, Zinsen und ML.
- `ui/` rendert die einzelnen Streamlit-Seiten.
- `utils/seed_data.py` stellt eine direkt demonstrierbare Beispielumgebung bereit.

## Datenbank

Die SQLite-Datenbank wird beim ersten Start automatisch unter `database/smartsplit.db` angelegt. Seed-Daten werden nur einmal erstellt.
