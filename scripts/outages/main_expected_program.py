#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import matplotlib.pyplot as plt
from pub_data_visualization import global_var, outages

# === CONFIGURATION DES CHEMINS ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH_CLEAN_DATA = os.path.join(BASE_DIR, "output", "indisponibilites_nucleaire_rte_CLEAN.csv")
FOLDER_OUT = os.path.join(BASE_DIR, "output", "plots")

# Choix de l'unité à afficher (vérifie le nom exact dans ton CSV)
UNIT_TO_PLOT = 'BELLEVILLE 1' 

# === NOMS DE COLONNES ===
COL_ID, COL_VER, COL_PUB = 'publication_id', 'publication_version', 'publication_dt (UTC)'
COL_UNIT, COL_STATUS = 'unit_name', 'outage_status'
COL_CAPA_NOM, COL_CAPA_OUT, COL_CAPA_AVAIL = 'nominal capacity (MW)', 'outage_capacity_mw', 'available capacity (MW)'

print(f"--- Chargement : {PATH_CLEAN_DATA} ---")
df = pd.read_csv(PATH_CLEAN_DATA, sep=";", encoding="utf-8")

# --- MAPPING & PRÉPARATION ---
mapping = {
    'message_id': COL_ID, 'version': COL_VER, 'date_publication_utc': COL_PUB,
    'nom_unite': COL_UNIT, 'statut': COL_STATUS,
    'puissance_max_mw': COL_CAPA_NOM, 'puissance_indispo_max_mw': COL_CAPA_OUT,
    'puissance_dispo_min_mw': COL_CAPA_AVAIL
}
df = df.rename(columns=mapping)
df[COL_PUB] = pd.to_datetime(df[COL_PUB], utc=True)

# Filtre sur l'unité choisie
df_unit = df[df[COL_UNIT] == UNIT_TO_PLOT].copy()

if df_unit.empty:
    print(f"⚠️ L'unité {UNIT_TO_PLOT} n'a pas été trouvée. Unités dispo : {df[COL_UNIT].unique()[:5]}...")
else:
    # Paramètres requis par la lib
    df_unit['creation_dt (UTC)'] = df_unit[COL_PUB]
    df_unit['outage_begin_dt (UTC)'] = df_unit[COL_PUB]
    df_unit['outage_end_dt (UTC)'] = df_unit[COL_PUB] + pd.Timedelta(days=7)
    df_unit[COL_VER] = df_unit[COL_VER].fillna(1).astype(int)
    
    for c in [COL_CAPA_NOM, COL_CAPA_OUT, COL_CAPA_AVAIL]:
        df_unit[c] = pd.to_numeric(df_unit[c], errors='coerce').fillna(0)

    # Indexation multi-niveau
    df_unit = df_unit.set_index([COL_ID, COL_VER, COL_PUB], drop=False)

    print(f"--- Calcul du programme pour {UNIT_TO_PLOT} ---")
    try:
        # Calcul du programme attendu
        program, _ = outages.tools.compute_program(df_unit)
        
        # Plot
        print("--- Génération du graphique ---")
        outages.plot.expected_program(
            program,
            unit_name=UNIT_TO_PLOT,
            folder_out=FOLDER_OUT,
            close=False
        )
        print(f"\n✅ Terminé ! Cherche le fichier 'expected_program_{UNIT_TO_PLOT}.png' dans {FOLDER_OUT}")

    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
