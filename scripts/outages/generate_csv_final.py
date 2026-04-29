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
print("=== Chargement RTE ===")
rte_path = os.path.expanduser(
    "~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/IndisponibilitesProduction.csv"
)
df_rte = pd.read_csv(rte_path, sep=";", low_memory=False)
print(f"RTE brut : {len(df_rte)} lignes")

# Filtrer nucléaire
df_rte = df_rte[df_rte["Filière de production"] == "Nucléaire"].copy()
print(f"RTE nucléaire : {len(df_rte)} lignes")

# Renommer au format EDF (df.pckl)
df_rte = df_rte.rename(columns={
    "Date et heure de publication (UTC)": "publication_dt (UTC)",
    "Message ID": "publication_id",
    "Version": "version",
    "Statut": "outage_status",
    "Type d'indisponibilité": "outage_type",
    "Nom de l'acteur de marché": "producer_name",
    "Nom de l'ouvrage": "unit_name",
    "Filière de production": "production_source",
    "Code localisation": "map_code",
    "Capacité installée": "nominal capacity (MW)",
    "Capacité disponible minimale": "available capacity (MW)",
    "Date de début de l'événement (UTC)": "outage_begin_dt (UTC)",
    "Date de fin de l'événement (UTC)": "outage_end_dt (UTC)",
    "Cause de l'indisponibilité": "outage_cause",
    
})

# Convertir les dates
for col in ["publication_dt (UTC)", "outage_begin_dt (UTC)", "outage_end_dt (UTC)", "creation_dt (UTC)"]:
    if col in df_rte.columns:
        df_rte[col] = pd.to_datetime(df_rte[col], utc=True)

# Harmoniser les valeurs
df_rte["production_source"] = "nuclear"
df_rte["outage_type"] = df_rte["outage_type"].map({
    "Planifiée": "planned",
    "Fortuite": "fortuitous",
}).fillna(df_rte["outage_type"])
df_rte["map_code"] = "FR"
df_rte["source"] = "RTE"

# Nettoyer le nom du réacteur (enlever les guillemets)
df_rte["unit_name"] = df_rte["unit_name"].str.strip('"')
df_rte["producer_name"] = df_rte["producer_name"].str.strip('"')

# ============================================================
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
