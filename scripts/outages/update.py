'''Script de mise à jour des données d'indisponibilité de production nucléaire.

Avant de lancer les scripts, il faut s'assurer que (CF README.md) :
  - Les clés d'API ont été définies (RTE_CLIENT_ID, RTE_CLIENT_SECRET). Sinon, referez vous à download_rte_unavailability.py ou .env.example.
  - Le dossier des xlsx RTE existe et contient des fichiers.

Après exécution, le programme affiche un résumé avec la taille du CSV final. 
Le CSV final est mis à jour dans output/indisponibilites_nucleaire_final.csv
'''

import subprocess
import sys
import os
from datetime import datetime

env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")# On cherche un fichier .env à la racine du projet pour charger les variables d'environnement. 
#Si ce fichier existe, on lit chaque ligne et on ajoute les variables d'environnement définies dans ce fichier à l'environnement d'exécution du script.
# Cela permet de stocker les identifiants de manière sécurisée et de ne pas les inclure directement dans le code source.
if os.path.isfile(env_file):
    for line in open(env_file):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1) # On sépare la ligne en deux parties : la clé (k) et la valeur (v). Le paramètre 1 de split signifie que l'on ne fait qu'une seule séparation, ce qui permet de gérer les valeurs qui contiennent elles-mêmes des signes égal.
            os.environ.setdefault(k, v) # On ajoute la variable d'environnement à l'environnement d'exécution du script, mais seulement si elle n'est pas déjà définie (os.environ.setdefault).

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # On définit le chemin de base du projet.
SCRIPTS  = os.path.join(BASE_DIR, "scripts", "outages") # On définit le chemin du dossier contenant les scripts d'indisponibilité de production nucléaire.
OUTPUT   = os.path.join(BASE_DIR, "output") # On définit le chemin du dossier de sortie où les données finales seront sauvegardées


print(">> Mise a jour des donnees nucleaires")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}") # Affiche la date et l'heure de lancement de la mise à jour des données d'indisponibilité de production nucléaire. Cela permet de savoir quand les données ont été mises à jour pour la dernière fois.

errors = []

for var in ["RTE_CLIENT_ID", "RTE_CLIENT_SECRET"]:
    if not os.environ.get(var):
        errors.append(f"Variable manquante : {var}") #On vérifie que les variables d'environnement nécessaires pour accéder aux données d'indisponibilité de production nucléaire sont définies.

rte_folder = os.path.expanduser(
    "~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/"
)
if not os.path.isdir(rte_folder):
    errors.append(f"Dossier RTE xlsx introuvable : {rte_folder}")
else:
    xlsx_count = len([f for f in os.listdir(rte_folder) if f.endswith(".xlsx")])
    if xlsx_count == 0:
        errors.append(f"Aucun fichier .xlsx dans {rte_folder}") # On vérifie que le dossier des xlsx de RTE existe et contient des fichiers. Si ce n'est pas le cas, la mise à jour ne pourra pas se faire correctement
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

steps = [
    ("1/2 Téléchargement RTE API",  "download_rte_unavailability.py"),
    ("2/2 Fusion → CSV final",      "generate_csv_final.py"),
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
    # On exécute chaque script dans l'ordre défini précédemment à l'aide de subprocess.run. Si un script échoue (code de retour différent de 0), le processus s'arrête et un message d'erreur est affiché.

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
    # Affiche un résumé de la mise à jour des données d'indisponibilité de production nucléaire, y compris le nombre de lignes et la taille du fichier CSV final. Cela permet de vérifier que les données ont été mises à jour correctement et d'avoir une idée de la quantité de données disponibles.
else:
    print("  CSV final non trouvé")

print("\n>> Mise a jour terminee")
