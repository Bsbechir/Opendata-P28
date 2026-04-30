#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import numpy as np
from pub_data_visualization import global_var, outages

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH_CLEAN_DATA = os.path.join(BASE_DIR, "output", "indisponibilites_nucleaire_rte_CLEAN.csv")
FOLDER_OUT      = os.path.join(BASE_DIR, "output", "plots")

if not os.path.exists(FOLDER_OUT):
    os.makedirs(FOLDER_OUT)

COL_ID, COL_VER, COL_PUB     = 'publication_id', 'publication_version', 'publication_dt (UTC)'
COL_UNIT, COL_STATUS          = 'unit_name', 'outage_status'
COL_CAPA_NOM, COL_CAPA_OUT, COL_CAPA_AVAIL = 'nominal capacity (MW)', 'outage_capacity_mw', 'available capacity (MW)'

print(f"Chargement : {PATH_CLEAN_DATA}")
df = pd.read_csv(PATH_CLEAN_DATA, sep=";", encoding="utf-8")

mapping = {
    'message_id': COL_ID, 'version': COL_VER, 'date_publication_utc': COL_PUB,
    'nom_unite': COL_UNIT, 'statut': COL_STATUS,
    'puissance_max_mw': COL_CAPA_NOM, 'puissance_indispo_max_mw': COL_CAPA_OUT,
    'puissance_dispo_min_mw': COL_CAPA_AVAIL,
}
df = df.rename(columns=mapping)
df[COL_PUB] = pd.to_datetime(df[COL_PUB], utc=True)

# Fenêtre glissante de 7 jours pour contenir la consommation mémoire de compute_all_programs
dernier = df[COL_PUB].max()
df = df[df[COL_PUB] > (dernier - pd.Timedelta(days=7))]
print(f"Messages après filtre : {len(df)}")

df['creation_dt (UTC)']      = df[COL_PUB]
df['outage_begin_dt (UTC)']  = df[COL_PUB]
df['outage_end_dt (UTC)']    = df[COL_PUB] + pd.Timedelta(days=2)
df[COL_VER]                  = df[COL_VER].fillna(1).astype(int)
df['production_source']      = 'Nuclear'

for c in [COL_CAPA_NOM, COL_CAPA_OUT, COL_CAPA_AVAIL]:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

df = df.set_index([COL_ID, COL_VER, COL_PUB], drop=False)

print("Calcul...")
try:
    dikt_programs_raw, _ = outages.tools.compute_all_programs(df)

    # Resample + dropna avant la fusion pour réduire l'empreinte mémoire
    dikt_programs = {}
    for u, d in dikt_programs_raw.items():
        if d is not None and not d.empty:
            dikt_programs[u] = d.resample('1h').first().ffill().dropna()

    dh = outages.tools.sum_programs(
        dikt_programs,
        production_dt_min  = df[COL_PUB].min(),
        production_dt_max  = df[COL_PUB].max() + pd.Timedelta(days=1),
        publication_dt_min = df[COL_PUB].min(),
        publication_dt_max = df[COL_PUB].max(),
    )

    print("Génération du graphique...")
    outages.plot.evolution_mean_availability(
        dh,
        folder_out = FOLDER_OUT,
        close      = False,
    )
    print(f"Graphique généré dans : {FOLDER_OUT}")

except Exception as e:
    print(f"Erreur : {e}")
