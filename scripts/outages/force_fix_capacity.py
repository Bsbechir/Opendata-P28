import os
import pandas as pd

path_dir = r"C:\Users\Valen\_energy_tmp_data\RTE\Centrales_production_reference"
os.makedirs(path_dir, exist_ok=True)

# Définition des colonnes
columns = [
    'capacity_mw', 
    'capacity_start_date (UTC)', 
    'capacity_end_date (UTC)', 
    'creation_dt (UTC)', 
    'publication_dt (UTC)',
    'production_source', 
    'production_unit', 
    'production_site'
]

# On crée une ligne avec des valeurs qui forcent Pandas à voir du numérique et du temps
data = {
    'capacity_mw': [0.0],
    'capacity_start_date (UTC)': ["2000-01-01 00:00:00"],
    'capacity_end_date (UTC)': ["2050-01-01 00:00:00"],
    'creation_dt (UTC)': ["2000-01-01 00:00:00"],
    'publication_dt (UTC)': ["2000-01-01 00:00:00"],
    'production_source': ["Nuclear"],
    'production_unit': ["DummyUnit"],
    'production_site': ["DummySite"]
}

df_fix = pd.DataFrame(data, columns=columns)

# SAUVEGARDE
file_path = os.path.join(path_dir, "Centrales_production_reference_FR.csv")
# On n'utilise pas de guillemets autour des dates pour éviter le type 'string' forcé
df_fix.to_csv(file_path, sep=";", index=False, quoting=0) 

print(f"✅ Référentiel forcé créé dans : {file_path}")

# VERIFICATION IMMEDIATE
test_df = pd.read_csv(file_path, sep=";")
print("Types détectés par Pandas pour vérification :")
print(test_df.dtypes)