"""
update.py

Script d'orchestration robuste.

Avant de lancer les scripts, il vérifie que :
  - Les variables d'environnement sont définies
  - Le dossier des xlsx RTE existe

Après exécution, il affiche un résumé avec la taille du CSV final.

Usage : python3 scripts/outages/update.py
"""

import subprocess
import sys
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS  = os.path.join(BASE_DIR, "scripts", "outages")
OUTPUT   = os.path.join(BASE_DIR, "output")

# on verifie avant de lancer les 3 scripts
print(">> Mise a jour des donnees nucleaires")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")

errors = []

for var in ["ENTSOE_API_KEY", "RTE_CLIENT_ID", "RTE_CLIENT_SECRET"]:
    if not os.environ.get(var):
        errors.append(f"Variable manquante : {var}")

# les xlsx RTE ne sont pas telecharges par ce script
rte_folder = os.path.expanduser(
    "~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/"
)
if not os.path.isdir(rte_folder):
    errors.append(f"Dossier RTE xlsx introuvable : {rte_folder}")
else:
    xlsx_count = len([f for f in os.listdir(rte_folder) if f.endswith(".xlsx")])
    if xlsx_count == 0:
        errors.append(f"Aucun fichier .xlsx dans {rte_folder}")
    else:
        print(f"OK  {xlsx_count} fichiers xlsx RTE trouvés")

if errors:
    print("\nPROBLEMES DETECTES :")
    for e in errors:
        print(f"  {e}")
    print("\nCorrigez ces problèmes avant de relancer.")
    print("Voir .env.example pour les variables d'environnement.")
    sys.exit(1)

print("OK  Variables d'environnement OK")
print()

# ordre important : les telechargements avant la fusion
steps = [
    ("1/3 Téléchargement ENTSO-E",  "download_entsoe.py"),
    ("2/3 Téléchargement RTE API",  "download_rte_unavailability.py"),
    ("3/3 Fusion → CSV final",      "generate_csv_final.py"),
]

for msg, script in steps:
    print(f"\n>> {msg}")
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script)],
        cwd=BASE_DIR
    )
    if result.returncode != 0:
        print(f"\nEchec : {script}")
        sys.exit(1)

print("\n>> Resume")

csv_path = os.path.join(OUTPUT, "indisponibilites_nucleaire_final.csv")
if os.path.exists(csv_path):
    size_mb = os.path.getsize(csv_path) / (1024 * 1024)
    with open(csv_path, "r") as f:
        line_count = sum(1 for _ in f) - 1  # -1 pour le header
    print(f"  CSV final : {csv_path}")
    print(f"  {line_count:,} lignes")
    print(f"  {size_mb:.1f} Mo")
    print(f"  Mis a jour : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
else:
    print("  CSV final non trouvé")

print("\n>> Mise a jour terminee")
