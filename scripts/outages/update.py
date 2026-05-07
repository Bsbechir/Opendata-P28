"""
update.py
=========
Script d'orchestration : lance les 3 étapes dans l'ordre.
  1. Télécharger les données ENTSO-E
  2. Télécharger les données RTE API
  3. Fusionner tout et produire le CSV final

Usage : python3 scripts/outages/update.py

Prérequis : les 3 variables d'environnement doivent être définies
  - ENTSOE_API_KEY
  - RTE_CLIENT_ID
  - RTE_CLIENT_SECRET
"""

import subprocess
import sys
import os

# Trouver le dossier racine du projet et le dossier des scripts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE_DIR, "scripts", "outages")

# Les étapes à exécuter dans l'ordre
steps = [
    ("Téléchargement ENTSO-E...", "download_entsoe.py"),
    ("Téléchargement RTE API...", "download_rte_unavailability.py"),
    ("Génération du CSV final...", "generate_csv_final.py"),
]

for msg, script in steps:
    print(msg)
    result = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)], cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"Échec : {script}")
        sys.exit(1)

print("\nMise à jour terminée.")
