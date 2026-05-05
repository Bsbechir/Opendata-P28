import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE_DIR, "scripts", "outages")

steps = [
    ("Téléchargement ENTSO-E...", "download_entsoe.py"),
    ("Téléchargement RTE API...", "download_rte_unavailability.py"),
    ("Génération du CSV final...", "generate_csv_final.py"),
]

for msg, script in steps:
    print(msg)
    result = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)], cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"Echec : {script}")
        sys.exit(1)

print("\nMise à jour terminée.")