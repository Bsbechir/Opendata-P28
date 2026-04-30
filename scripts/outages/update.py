import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Étape 1 : mise à jour du CSV ENTSO-E (appel réseau, nécessite ENTSOE_API_KEY)
print("Téléchargement ENTSO-E...")
download_script = os.path.join(BASE_DIR, "scripts", "outages", "download_entsoe.py")
result = subprocess.run([sys.executable, download_script], cwd=BASE_DIR)
if result.returncode != 0:
    print("Echec du téléchargement ENTSO-E.")
    print("Vérifiez : export ENTSOE_API_KEY='votre_clé'")
    sys.exit(1)

# Étape 2 : reconstruction du CSV final à partir des xlsx RTE + ENTSO-E
print("Génération du CSV final...")
generate_script = os.path.join(BASE_DIR, "scripts", "outages", "generate_csv_final.py")
result = subprocess.run([sys.executable, generate_script], cwd=BASE_DIR)
if result.returncode != 0:
    print("Echec de la génération du CSV.")
    sys.exit(1)

print("Mise à jour terminée.")
print("Pour intégrer de nouvelles données RTE :")
print("  1. Téléchargez les .xlsx depuis services-rte.com")
print("  2. Placez-les dans ~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/")
print("  3. Relancez ce script")
