import pandas as pd
import os

# Dossier cible
path = r'C:\Users\Valen\Downloads\pub-data-visualization\data\production_capacity\unit\rte\tmp'
os.makedirs(path, exist_ok=True)

# Création d'un référentiel minimal pour le nucléaire français
data = {
    'unit_name': ['BELLEVILLE 1', 'CHOOZ 1', 'CIVAUX 1', 'GRAVELINES 1', 'PALUEL 1'],
    'capacity_end_date (local)': ['2050-01-01 00:00:00+01:00'] * 5,
    'capacity_end_date (UTC)': ['2050-01-01 00:00:00'] * 5,
    'production_source': ['Nuclear'] * 5,
    'capacity_mw': [1300, 1500, 1500, 900, 1300]
}

df = pd.DataFrame(data)
df.to_csv(os.path.join(path, 'FR.csv'), sep=';', index=False)
print("Fichier de référence FR.csv créé avec succès !")