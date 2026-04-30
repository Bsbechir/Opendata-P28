#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import matplotlib.pyplot as plt
from pub_data_visualization import outages

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH_CLEAN_DATA = os.path.join(BASE_DIR, "output", "indisponibilites_nucleaire_rte_CLEAN.csv")
FOLDER_OUT      = os.path.join(BASE_DIR, "output", "plots")

UNIT_TO_PLOT = 'BELLEVILLE 1'

df = pd.read_csv(PATH_CLEAN_DATA, sep=";", encoding="utf-8")
mapping = {
    'message_id':             'publication_id',
    'version':                'publication_version',
    'date_publication_utc':   'publication_dt (UTC)',
    'nom_unite':              'unit_name',
    'puissance_dispo_min_mw': 'available capacity (MW)',
}
df = df.rename(columns=mapping)
df['publication_dt (UTC)'] = pd.to_datetime(df['publication_dt (UTC)'], utc=True)

df_unit = df[df['unit_name'] == UNIT_TO_PLOT].copy()

if df_unit.empty:
    print(f"Unité {UNIT_TO_PLOT} introuvable.")
else:
    # Tri par version pour visualiser l'évolution chronologique des révisions
    df_unit = df_unit.sort_values('publication_version')

    plt.figure(figsize=(12, 6))

    for version in df_unit['publication_version'].unique():
        df_ver = df_unit[df_unit['publication_version'] == version]
        label  = f"v{version} ({df_ver['publication_dt (UTC)'].iloc[0].strftime('%d/%m %H:%M')})"

        # Escalier de 5 jours à partir de la date de publication pour simuler la disponibilité déclarée
        plt.step(
            [df_ver['publication_dt (UTC)'].iloc[0],
             df_ver['publication_dt (UTC)'].iloc[0] + pd.Timedelta(days=5)],
            [df_ver['available capacity (MW)'].iloc[0],
             df_ver['available capacity (MW)'].iloc[0]],
            where='post',
            label=label,
        )

    plt.title(f"Evolution de la disponibilité déclarée - {UNIT_TO_PLOT}")
    plt.xlabel("Date")
    plt.ylabel("Puissance disponible (MW)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    out_file = os.path.join(FOLDER_OUT, f"incremental_custom_{UNIT_TO_PLOT}.png")
    plt.savefig(out_file)
    print(f"Graphique sauvegardé : {out_file}")
    plt.show()
