import os
import pandas as pd

path = r"C:\Users\Valen\_energy_tmp_data\RTE\Centrales_production_reference"
os.makedirs(path, exist_ok=True)

# On crée un fichier vide ou minimal pour satisfaire la vérification du script
# Le script concatène des objets, donc on lui donne une structure compatible
df_ref = pd.DataFrame(columns=['production_site', 'production_unit', 'production_source', 'capacity_mw'])
df_ref.to_csv(os.path.join(path, "Centrales_production_reference_FR.csv"), sep=";", index=False)

print(f"Fichier de référence créé dans {path}")