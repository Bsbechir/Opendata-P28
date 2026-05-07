"""
generate_csv_final.py
=====================
Script principal de fusion. Il prend 3 sources :
  1. Fichiers xlsx RTE (téléchargés manuellement depuis services-rte.com)
  2. CSV ENTSO-E (généré par download_entsoe.py)
  3. CSV RTE API (généré par download_rte_unavailability.py)

Il harmonise les noms de colonnes, fusionne tout dans un seul DataFrame,
déduplique, et exporte le CSV final.

Résultat : output/indisponibilites_nucleaire_final.csv
"""

import pandas as pd
import os
import glob

# --- Chemins ---
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ================================================================
# SOURCE 1 : Fichiers xlsx RTE (téléchargement manuel)
# ================================================================
print("Chargement RTE xlsx...")

# Ces fichiers doivent être placés manuellement dans ce dossier
rte_folder = os.path.expanduser(
    "~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/"
)

xlsx_files = sorted(glob.glob(os.path.join(rte_folder, "*.xlsx")))
print(f"Fichiers trouvés : {len(xlsx_files)}")

# Lire chaque fichier Excel et les empiler dans un seul DataFrame
dfs_rte = []
for f in xlsx_files:
    print(f"  {os.path.basename(f)}...")
    df_tmp = pd.read_excel(f)
    df_tmp["file_name"] = os.path.basename(f)  # garder la trace du fichier source
    dfs_rte.append(df_tmp)

df_rte = pd.concat(dfs_rte, ignore_index=True)
print(f"RTE brut : {len(df_rte)} lignes")

# --- Renommage des colonnes RTE ---
# Les colonnes des xlsx RTE ont des noms longs en français avec accents.
# On les renomme vers un format standard anglais.
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
    elif col.startswith("Type d") and "indisponibilit" in col:
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

# Filtrer : ne garder que le nucléaire
df_rte = df_rte[df_rte["production_source"] == "Nucléaire"].copy()
print(f"RTE nucléaire : {len(df_rte)} lignes")

# ================================================================
# SOURCE 2 : ENTSO-E (généré par download_entsoe.py)
# ================================================================
print("\nChargement ENTSO-E...")
entsoe_path = os.path.join(OUTPUT_DIR, "indisponibilites_entsoe.csv")
df_entsoe = pd.read_csv(entsoe_path, sep=";", low_memory=False)
print(f"ENTSO-E brut : {len(df_entsoe)} lignes")

# Filtrer nucléaire
df_entsoe = df_entsoe[df_entsoe["plant_type"] == "Nuclear"].copy()
print(f"ENTSO-E nucléaire : {len(df_entsoe)} lignes")

# Renommage vers le format standard
df_entsoe = df_entsoe.rename(columns={
    "created_doc_time":          "creation_dt (UTC)",
    "avail_qty":                 "available capacity (MW)",
    "nominal_power":             "nominal capacity (MW)",
    "production_resource_name":  "unit_name",
    "mrid":                      "publication_id",
    "revision":                  "version",
    "start":                     "outage_begin_dt (UTC)",
    "end":                       "outage_end_dt (UTC)",
    "biddingzone_domain":        "map_code",
})

df_entsoe["production_source"] = "nuclear"

# Traduction des types d'arrêt
df_entsoe["outage_type"] = df_entsoe["businesstype"].map({
    "Planned maintenance": "planned",
    "Unplanned outage":    "fortuitous",
}).fillna(df_entsoe["businesstype"])

# Conversion des dates en format datetime UTC
for col in ["creation_dt (UTC)", "outage_begin_dt (UTC)", "outage_end_dt (UTC)"]:
    if col in df_entsoe.columns:
        df_entsoe[col] = pd.to_datetime(df_entsoe[col], utc=True)

# Colonnes manquantes dans ENTSO-E (pas fournies par cette source)
df_entsoe["producer_name"]        = "EDF"
df_entsoe["outage_cause"]         = ""
df_entsoe["outage_status"]        = ""
df_entsoe["publication_dt (UTC)"] = df_entsoe["creation_dt (UTC)"]
df_entsoe["source"]               = "ENTSOE"

# ================================================================
# SOURCE 3 : API RTE (généré par download_rte_unavailability.py)
# ================================================================
print("\nChargement RTE API...")
rte_api_path = os.path.join(BASE_DIR, "scripts", "outages", "indisponibilites_nucleaires_rte.csv")
df_rte_api = pd.read_csv(rte_api_path, sep=",", low_memory=False)
print(f"RTE API brut : {len(df_rte_api)} lignes")

# Renommage vers le format standard
df_rte_api = df_rte_api.rename(columns={
    "identifier":                              "publication_id",
    "version":                                 "version",
    "publication_date":                        "publication_dt (UTC)",
    "start_date":                              "outage_begin_dt (UTC)",
    "end_date":                                "outage_end_dt (UTC)",
    "affected_asset_or_unit_name":             "unit_name",
    "available_capacity_mw":                   "available capacity (MW)",
    "installed_capacity_mw":                   "nominal capacity (MW)",
    "market_participant":                      "producer_name",
    "creation_date":                           "creation_dt (UTC)",
    "reason":                                  "outage_cause",
    "event_status":                            "outage_status",
})

df_rte_api["production_source"] = "nuclear"
df_rte_api["map_code"] = "FR"

# Traduction des types et statuts
df_rte_api["outage_type"] = df_rte_api["unavailability_type"].map({
    "PLANNED":   "planned",
    "UNPLANNED": "fortuitous",
}).fillna(df_rte_api["unavailability_type"])

df_rte_api["outage_status"] = df_rte_api["outage_status"].map({
    "ACTIVE":    "Actif",
    "INACTIVE":  "Inactif",
    "CANCELLED": "Annulé",
}).fillna(df_rte_api["outage_status"])

df_rte_api["outage_cause"] = df_rte_api["outage_cause"].map({
    "COMPLEMENTARY_INFORMATION": "Information Complémentaire",
    "FORESEEN_MAINTENANCE":      "Maintenance prévue",
    "UNPLANNED_MAINTENANCE":     "Maintenance non prévue",
    "UNPLANNED_OUTAGE":          "Arrêt non prévu",
    "PLANNED_MAINTENANCE":       "Maintenance prévue",
}).fillna(df_rte_api["outage_cause"])

for col in ["publication_dt (UTC)", "outage_begin_dt (UTC)", "outage_end_dt (UTC)", "creation_dt (UTC)"]:
    if col in df_rte_api.columns:
        df_rte_api[col] = pd.to_datetime(df_rte_api[col], utc=True)

df_rte_api["source"] = "RTE_API"
print(f"RTE API nucléaire : {len(df_rte_api)} lignes")

# ================================================================
# FUSION des 3 sources
# ================================================================

# Liste des colonnes qu'on garde dans le CSV final
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
    "source",
]

# S'assurer que toutes les colonnes existent dans chaque source
for col in colonnes_finales:
    if col not in df_rte.columns:
        df_rte[col] = ""
    if col not in df_entsoe.columns:
        df_entsoe[col] = ""
    if col not in df_rte_api.columns:
        df_rte_api[col] = ""

# Ne garder que les colonnes finales
df_rte     = df_rte[colonnes_finales]
df_entsoe  = df_entsoe[colonnes_finales]
df_rte_api = df_rte_api[colonnes_finales]

# Empiler les 3 DataFrames
print("\nFusion...")
df_final = pd.concat([df_rte, df_entsoe, df_rte_api], ignore_index=True)
print(f"Total : {len(df_final)} lignes  (RTE xlsx: {len(df_rte)}, ENTSO-E: {len(df_entsoe)}, RTE API: {len(df_rte_api)})")

# ================================================================
# NETTOYAGE final
# ================================================================
print("\nNettoyage...")

# Harmoniser les types d'arrêt (les xlsx RTE utilisent le français)
df_final["outage_type"] = df_final["outage_type"].replace({
    "Planifiée": "planned",
    "Fortuite":  "fortuitous",
})
print(f"Types d'arrêt : {df_final['outage_type'].unique().tolist()}")

# Uniformiser ces colonnes
df_final["production_source"] = "nuclear"
df_final["map_code"]          = "FR"

# Nettoyer les espaces et guillemets parasites dans les noms
df_final["unit_name"]     = df_final["unit_name"].str.strip().str.strip('"')
df_final["producer_name"] = df_final["producer_name"].str.strip().str.strip('"')

# Convertir toutes les dates en datetime UTC
for col in ["publication_dt (UTC)", "outage_begin_dt (UTC)", "outage_end_dt (UTC)", "creation_dt (UTC)"]:
    df_final[col] = pd.to_datetime(df_final[col], utc=True, errors="coerce")

# --- Déduplication intra-source ---
# Même publication_id + même version = doublon exact → on garde 1 seul
df_final = df_final.sort_values(["publication_id", "version"], ascending=[True, False])
df_final = df_final.drop_duplicates(subset=["publication_id", "version"], keep="first")
print(f"Après dédup intra-source : {len(df_final)} lignes")

# --- Déduplication cross-source ---
# Un même arrêt peut exister dans RTE xlsx ET RTE API avec des IDs différents.
# On les détecte par : même réacteur + même jour de début + même type d'arrêt.
# Priorité : RTE (xlsx officiel) > RTE_API > ENTSOE
df_final["_dedup_key"] = (
    df_final["unit_name"].str.upper().str.strip() + "|" +
    pd.to_datetime(df_final["outage_begin_dt (UTC)"], utc=True).dt.strftime("%Y-%m-%d") + "|" +
    df_final["outage_type"].str.lower().str.strip()
)
source_priority = {"RTE": 0, "RTE_API": 1, "ENTSOE": 2}
df_final["_source_rank"] = df_final["source"].map(source_priority).fillna(3)
df_final = df_final.sort_values(["_dedup_key", "_source_rank", "version"], ascending=[True, True, False])
before_cross = len(df_final)
df_final = df_final.drop_duplicates(subset=["_dedup_key"], keep="first")
print(f"Dédup cross-source : {before_cross} → {len(df_final)} ({before_cross - len(df_final)} doublons retirés)")
df_final = df_final.drop(columns=["_dedup_key", "_source_rank"])

# Trier par date de début
df_final = df_final.sort_values("outage_begin_dt (UTC)").reset_index(drop=True)
print(f"Après déduplication : {len(df_final)} lignes")
print(f"Réacteurs distincts : {df_final['unit_name'].nunique()}")

# ================================================================
# EXPORT
# ================================================================
output_file = os.path.join(OUTPUT_DIR, "indisponibilites_nucleaire_final.csv")
df_final.to_csv(output_file, sep=";", index=False, encoding="utf-8")
print(f"\nCSV exporté : {output_file}")
print(f"Lignes : {len(df_final)}")
print(f"Sources : {df_final['source'].value_counts().to_dict()}")
