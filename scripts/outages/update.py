"""
Script d'automatisation : re-télécharge les données ENTSO-E
et relance la génération du CSV final.
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# 1. RE-TÉLÉCHARGER LES DONNÉES ENTSO-E
# ============================================================
print("=== Téléchargement ENTSO-E ===")
download_script = os.path.join(BASE_DIR, "scripts", "outages", "download_entsoe.py")
result = subprocess.run([sys.executable, download_script], cwd=BASE_DIR)
if result.returncode != 0:
    print("ERREUR : le téléchargement ENTSO-E a échoué")
    print("Vérifiez votre clé API : export ENTSOE_API_KEY='votre_clé'")
    sys.exit(1)
print("Téléchargement ENTSO-E terminé\n")

# ============================================================
# 2. RE-GÉNÉRER LE CSV FINAL
# ============================================================
print("=== Génération du CSV final ===")
generate_script = os.path.join(BASE_DIR, "scripts", "outages", "generate_csv_final.py")
result = subprocess.run([sys.executable, generate_script], cwd=BASE_DIR)
if result.returncode != 0:
    print("ERREUR : la génération du CSV a échoué")
    sys.exit(1)

print("\n=== Mise à jour terminée ===")
print("Pour mettre à jour les données RTE :")
print("  1. Téléchargez les .xlsx depuis services-rte.com")
print("  2. Placez-les dans ~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/")
print("  3. Relancez ce script")