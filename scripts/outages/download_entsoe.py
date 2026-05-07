# recupere les indispos ENTSO-E pour la France
# il faut mettre ENTSOE_API_KEY dans l'environnement avant

import os
import sys
from entsoe import EntsoePandasClient
import pandas as pd

api_key = os.environ.get("ENTSOE_API_KEY")
if not api_key:
    print("ERREUR : variable ENTSOE_API_KEY non définie")
    print("Lancez : export ENTSOE_API_KEY='votre_clé'")
    sys.exit(1)


client = EntsoePandasClient(api_key=api_key)

# periode assez large pour couvrir tout le projet
start = pd.Timestamp('20150101', tz='Europe/Paris')
end   = pd.Timestamp('20260101', tz='Europe/Paris')

print("Téléchargement des indisponibilités FR...")
df = client.query_unavailability_of_generation_units('FR', start=start, end=end)
print(f"{len(df)} lignes téléchargées")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
output_path = os.path.join(BASE_DIR, "output", "indisponibilites_entsoe.csv")
df.to_csv(output_path, sep=';')
print(f"Sauvegardé dans {output_path}")
