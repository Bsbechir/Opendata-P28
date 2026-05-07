"""
download_entsoe.py
==================
Ce script télécharge les données d'indisponibilité des centrales françaises
depuis la plateforme européenne ENTSO-E (transparency.entsoe.eu).

Il utilise la bibliothèque entsoe-py qui se connecte à l'API ENTSO-E.
La clé API doit être définie dans la variable d'environnement ENTSOE_API_KEY.

Résultat : un fichier CSV dans output/indisponibilites_entsoe.csv
"""

import os
import sys
from entsoe import EntsoePandasClient
import pandas as pd

# --- Récupération de la clé API depuis les variables d'environnement ---
# On ne met JAMAIS la clé en dur dans le code (sécurité)
api_key = os.environ.get("ENTSOE_API_KEY")
if not api_key:
    print("ERREUR : variable ENTSOE_API_KEY non définie")
    print("Lancez : export ENTSOE_API_KEY='votre_clé'")
    sys.exit(1)

# --- Connexion au client ENTSO-E ---
client = EntsoePandasClient(api_key=api_key)

# --- Définition de la période de téléchargement ---
# On prend large : de 2015 à 2026 pour couvrir tout l'historique disponible
start = pd.Timestamp('20150101', tz='Europe/Paris')
end   = pd.Timestamp('20260101', tz='Europe/Paris')

# --- Téléchargement ---
# 'FR' = France. La fonction renvoie un DataFrame pandas avec toutes les
# indisponibilités de toutes les centrales françaises (pas que nucléaire)
print("Téléchargement des indisponibilités FR...")
df = client.query_unavailability_of_generation_units('FR', start=start, end=end)
print(f"{len(df)} lignes téléchargées")

# --- Sauvegarde ---
# On remonte de 2 niveaux (scripts/outages/ → racine) pour trouver output/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
output_path = os.path.join(BASE_DIR, "output", "indisponibilites_entsoe.csv")
df.to_csv(output_path, sep=';')
print(f"Sauvegardé dans {output_path}")
