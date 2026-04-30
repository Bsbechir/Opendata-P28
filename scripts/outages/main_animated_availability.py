#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from pub_data_visualization import global_var, outages

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH_CLEAN_DATA = os.path.join(BASE_DIR, "output", "indisponibilites_nucleaire_rte_CLEAN.csv")
FOLDER_OUT      = os.path.join(BASE_DIR, "output", "plots")

if not os.path.exists(FOLDER_OUT):
    os.makedirs(FOLDER_OUT)

COL_ID       = 'publication_id'
COL_VER      = 'publication_version'
COL_PUB      = 'publication_dt (UTC)'
COL_CREATION = 'creation_dt (UTC)'
COL_BEG      = 'outage_begin_dt (UTC)'
COL_END      = 'outage_end_dt (UTC)'
COL_UNIT     = 'unit_name'
COL_STATUS   = 'outage_status'
COL_CAPA_NOM   = 'nominal capacity (MW)'
COL_CAPA_OUT   = 'outage_capacity_mw'
COL_CAPA_AVAIL = 'available capacity (MW)'

print(f"Chargement : {PATH_CLEAN_DATA}")
try:
    df = pd.read_csv(PATH_CLEAN_DATA, sep=";", encoding="utf-8")
except:
    df = pd.read_csv(PATH_CLEAN_DATA, sep=";", encoding="latin-1")

mapping = {
    'message_id':            COL_ID,
    'version':               COL_VER,
    'date_publication_utc':  COL_PUB,
    'nom_unite':             COL_UNIT,
    'statut':                COL_STATUS,
    'puissance_max_mw':      COL_CAPA_NOM,
    'puissance_indispo_max_mw': COL_CAPA_OUT,
    'puissance_dispo_min_mw':   COL_CAPA_AVAIL,
}
df = df.rename(columns=mapping)

df[COL_PUB] = pd.to_datetime(df[COL_PUB], utc=True)

# On limite à 15 jours pour éviter de saturer la RAM lors du calcul des programmes
dernier_message = df[COL_PUB].max()
df = df[df[COL_PUB] > (dernier_message - pd.Timedelta(days=15))]
print(f"Messages à traiter : {len(df)}")

df[COL_CREATION] = df[COL_PUB]
df[COL_BEG]      = df[COL_PUB]
df[COL_END]      = df[COL_PUB] + pd.Timedelta(days=7)
df[COL_VER]      = df[COL_VER].fillna(1).astype(int)
df['production_source'] = 'Nuclear'

for c in [COL_CAPA_NOM, COL_CAPA_OUT, COL_CAPA_AVAIL]:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

df = df.set_index([COL_ID, COL_VER, COL_PUB], drop=False)

print("Calcul des programmes...")
try:
    date_min = df[COL_PUB].min()
    date_max = df[COL_PUB].max() + pd.Timedelta(days=1)

    dikt_programs_raw, _ = outages.tools.compute_all_programs(df)

    # Resample à 1h pour réduire la taille en mémoire avant la consolidation
    dikt_programs = {}
    for unit, d_unit in dikt_programs_raw.items():
        if d_unit is not None and not d_unit.empty:
            dikt_programs[unit] = d_unit.resample('1h').first().ffill()

    if not dikt_programs:
        raise ValueError("Aucun programme calculé.")

    dh = outages.tools.sum_programs(
        dikt_programs,
        production_dt_min  = date_min,
        production_dt_max  = date_max,
        publication_dt_min = date_min,
        publication_dt_max = date_max,
    )

    print("Génération de l'animation...")
    outages.plot.animated_availability(
        dh,
        production_dt_min  = date_min,
        production_dt_max  = date_max,
        data_source        = global_var.data_source_outages_rte,
        map_code           = global_var.geography_map_code_france,
        production_source  = global_var.production_source_nuclear,
        folder_out         = FOLDER_OUT,
        close              = False,
    )

    print(f"Terminé. Fichier dans : {FOLDER_OUT}")

except Exception as e:
    print(f"Erreur : {e}")
    import traceback
    traceback.print_exc()
