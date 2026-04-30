"""
Script de génération du CSV final des indisponibilités nucléaires.
Lit les données RTE (CSV brut) et ENTSO-E, les transforme au format
attendu par EDF (même colonnes que df.pckl), et exporte.
"""

import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ============================================================
# 1. CHARGER LES DONNÉES RTE
# ============================================================
# ============================================================
# 1. CHARGER LES DONNÉES RTE (tous les .xlsx)
# ============================================================
print("=== Chargement RTE ===")
import glob

rte_folder = os.path.expanduser(
    "~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/"
)

xlsx_files = sorted(glob.glob(os.path.join(rte_folder, "*.xlsx")))
print(f"Fichiers trouvés : {len(xlsx_files)}")

dfs_rte = []
for f in xlsx_files:
    print(f"  Lecture {os.path.basename(f)}...")
    df_tmp = pd.read_excel(f)
    df_tmp["file_name"] = os.path.basename(f)
    dfs_rte.append(df_tmp)

df_rte = pd.concat(dfs_rte, ignore_index=True)
print(f"RTE brut : {len(df_rte)} lignes")

# Renommer au format EDF — on matche par le début du nom pour éviter les problèmes d'apostrophes
rename_map = {}
for col in df_rte.columns:
    if col.startswith("Date et heure de publication"):
        rename_map[col] = "publication_dt (UTC)"
    elif col == "Message ID":
        rename_map[col] = "publication_id"
    elif col == "Version":
        rename_map[col] = "version"
    elif col == "Statut":
        rename_map[col] = "outage_status"
    elif col.startswith("Type d"):
        if "indisponibilit" in col:
            rename_map[col] = "outage_type"
    elif col.startswith("Nom de l") and "acteur" in col:
        rename_map[col] = "producer_name"
    elif col.startswith("Nom de l") and "ouvrage" in col:
        rename_map[col] = "unit_name"
    elif col.startswith("Fili"):
        rename_map[col] = "production_source"
    elif col == "Code localisation":
        rename_map[col] = "map_code"
    elif col.startswith("Capacit") and "install" in col:
        rename_map[col] = "nominal capacity (MW)"
    elif col.startswith("Capacit") and "disponible minimale" in col:
        rename_map[col] = "available capacity (MW)"
    elif col.startswith("Date de d"):
        rename_map[col] = "outage_begin_dt (UTC)"
    elif col.startswith("Date de fin"):
        rename_map[col] = "outage_end_dt (UTC)"
    elif col.startswith("Cause"):
        rename_map[col] = "outage_cause"

df_rte = df_rte.rename(columns=rename_map)
df_rte["creation_dt (UTC)"] = df_rte["publication_dt (UTC)"]
df_rte["source"] = "RTE"
print(f"Colonnes RTE renommées : {list(rename_map.values())}")

# 2. CHARGER LES DONNÉES ENTSO-E
# ============================================================
print("\n=== Chargement ENTSO-E ===")
entsoe_path = os.path.join(OUTPUT_DIR, "indisponibilites_entsoe.csv")
df_entsoe = pd.read_csv(entsoe_path, sep=";", low_memory=False)
print(f"ENTSO-E brut : {len(df_entsoe)} lignes")

# Filtrer nucléaire
df_entsoe = df_entsoe[df_entsoe["plant_type"] == "Nuclear"].copy()
print(f"ENTSO-E nucléaire : {len(df_entsoe)} lignes")

# Renommer au format EDF
df_entsoe = df_entsoe.rename(columns={
    "created_doc_time": "creation_dt (UTC)",
    "avail_qty": "available capacity (MW)",
    "nominal_power": "nominal capacity (MW)",
    "production_resource_name": "unit_name",
    "mrid": "publication_id",
    "revision": "version",
    "start": "outage_begin_dt (UTC)",
    "end": "outage_end_dt (UTC)",
    "biddingzone_domain": "map_code",
})

# Convertir les dates
for col in ["creation_dt (UTC)", "outage_begin_dt (UTC)", "outage_end_dt (UTC)"]:
    if col in df_entsoe.columns:
        df_entsoe[col] = pd.to_datetime(df_entsoe[col], utc=True)

# Harmoniser les valeurs
df_entsoe["production_source"] = "nuclear"
df_entsoe["outage_type"] = df_entsoe["businesstype"].map({
    "Planned maintenance": "planned",
    "Unplanned outage": "fortuitous",
}).fillna(df_entsoe["businesstype"])
df_entsoe["producer_name"] = "EDF"
df_entsoe["outage_cause"] = ""
df_entsoe["outage_status"] = ""
df_entsoe["publication_dt (UTC)"] = df_entsoe["creation_dt (UTC)"]
df_entsoe["source"] = "ENTSOE"

# ============================================================
# 3. COLONNES COMMUNES (format df.pckl)
# ============================================================
colonnes_finales = [
    "publication_id",
    "version",
    "publication_dt (UTC)",
    "outage_begin_dt (UTC)",
    "outage_end_dt (UTC)",
    "unit_name",
    "available capacity (MW)",
    "nominal capacity (MW)",
    "producer_name",
    "map_code",
    "production_source",
    "creation_dt (UTC)",
    "outage_type",
    "outage_cause",
    "outage_status",
    "source",  # colonne ajoutée pour savoir d'où vient la ligne
]

# Ne garder que les colonnes communes
for col in colonnes_finales:
    if col not in df_rte.columns:
        df_rte[col] = ""
    if col not in df_entsoe.columns:
        df_entsoe[col] = ""

df_rte = df_rte[colonnes_finales]
df_entsoe = df_entsoe[colonnes_finales]

# ============================================================
# 4. FUSIONNER
# ============================================================
print("\n=== Fusion ===")
df_final = pd.concat([df_rte, df_entsoe], ignore_index=True)
print(f"Total après fusion : {len(df_final)} lignes")
print(f"  - RTE : {len(df_rte)} lignes")
print(f"  - ENTSO-E : {len(df_entsoe)} lignes")

# ============================================================
# 5. STATS
# ============================================================
print("\n=== Résumé ===")
print(f"Réacteurs : {df_final['unit_name'].nunique()}")
print(f"Types d'arrêt : {df_final['outage_type'].unique().tolist()}")

# ============================================================
# 6. EXPORTER
# ============================================================
output_file = os.path.join(OUTPUT_DIR, "indisponibilites_nucleaire_final.csv")
df_final.to_csv(output_file, sep=";", index=False, encoding="utf-8")
print(f"\nCSV exporté : {output_file}")
print(f"Lignes : {len(df_final)}")
