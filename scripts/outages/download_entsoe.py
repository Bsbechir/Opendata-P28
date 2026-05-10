'''Ce fichier récupère les données d'indisponibilités depuis la source ENTSOE
Attention : Il faut mettre la clé API ENTSOE dans une variable d'environnement ENTSOE_API_KEY avant de lancer ce script (cf README.md)
Lancez : export ENTSOE_API_KEY='votre_clé'  
'''

import os
import sys
from entsoe import EntsoePandasClient
import pandas as pd

api_key = os.environ.get("ENTSOE_API_KEY")
if not api_key:
    print("ERREUR : variable ENTSOE_API_KEY non définie")
    print("Lancez : export ENTSOE_API_KEY='votre_clé'")
    sys.exit(1)#La clé d'API est nécessaire pour accéder aux données d'ENTSOE. Si elle n'est pas définie, le script se termine

client = EntsoePandasClient(api_key=api_key) # On crée un client pour interagir avec l'API d'ENTSOE en utilisant la clé d'API fournie. Ce client nous permettra de faire des requêtes pour récupérer les données d'indisponibilité de production nucléaire.

# On prend une période assez large pour récupérer les données d'indisponibilité de production nucléaire : de 2015 à 2025.
start = pd.Timestamp('20150101', tz='Europe/Paris')
end   = pd.Timestamp('20260101', tz='Europe/Paris')

print("Téléchargement des indisponibilités en cours...")
df = client.query_unavailability_of_generation_units('FR', start=start, end=end) # On utilise le client pour faire une requête à l'API d'ENTSOE afin de récupérer les données d'indisponibilités.On récupère tout les types de centrales de production.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # On définit le chemin de base pour sauvegarder les données.
output_path = os.path.join(BASE_DIR, "output", "indisponibilites_entsoe.csv") # On définit le chemin complet du fichier CSV où les données seront sauvegardées
df.to_csv(output_path, sep=';')
print(f"Sauvegardé dans {output_path}")
