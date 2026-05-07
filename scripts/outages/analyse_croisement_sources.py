# compare les donnees RTE et ENTSO-E
# RTE est la reference (obligation legale de tout publier)

import pandas as pd
import os

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# --- Chargement du CSV final ---
print("=" * 70)
print("ANALYSE CROISÉE DES SOURCES RTE vs ENTSO-E")
print("=" * 70)

df = pd.read_csv(
    os.path.join(OUTPUT_DIR, "indisponibilites_nucleaire_final.csv"),
    sep=";", low_memory=False
)

# Convertir les dates
for col in ["outage_begin_dt (UTC)", "outage_end_dt (UTC)"]:
    df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

# Séparer les sources
df_rte    = df[df["source"].isin(["RTE", "RTE_API"])].copy()
df_entsoe = df[df["source"] == "ENTSOE"].copy()

print(f"\nLignes RTE (xlsx + API) : {len(df_rte)}")
print(f"Lignes ENTSO-E          : {len(df_entsoe)}")

# 1. reacteurs par source
print("\n" + "=" * 70)
print("1. RÉACTEURS PAR SOURCE")
print("=" * 70)

reacteurs_rte    = set(df_rte["unit_name"].unique())
reacteurs_entsoe = set(df_entsoe["unit_name"].unique())

only_rte    = reacteurs_rte - reacteurs_entsoe
only_entsoe = reacteurs_entsoe - reacteurs_rte
communs     = reacteurs_rte & reacteurs_entsoe

print(f"Réacteurs RTE          : {len(reacteurs_rte)}")
print(f"Réacteurs ENTSO-E      : {len(reacteurs_entsoe)}")
print(f"Réacteurs en commun    : {len(communs)}")
print(f"Uniquement dans RTE    : {len(only_rte)}")
if only_rte:
    for r in sorted(only_rte):
        print(f"  - {r}")
print(f"Uniquement dans ENTSO-E: {len(only_entsoe)}")
if only_entsoe:
    for r in sorted(only_entsoe):
        print(f"  - {r}")

# 2. couverture temporelle
print("\n" + "=" * 70)
print("2. COUVERTURE TEMPORELLE")
print("=" * 70)

print(f"RTE     : {df_rte['outage_begin_dt (UTC)'].min()} → {df_rte['outage_begin_dt (UTC)'].max()}")
print(f"ENTSO-E : {df_entsoe['outage_begin_dt (UTC)'].min()} → {df_entsoe['outage_begin_dt (UTC)'].max()}")

print("\nNombre d'événements par année et par source :")
df["year"] = df["outage_begin_dt (UTC)"].dt.year
pivot = df.groupby(["year", "source"]).size().unstack(fill_value=0)
print(pivot.to_string())

# 3. intersection des evenements
print("\n" + "=" * 70)
print("3. INTERSECTION DES ÉVÉNEMENTS")
print("=" * 70)

# cle = reacteur + jour de debut
df_rte["match_key"] = (
    df_rte["unit_name"].str.upper().str.strip() + "|" +
    df_rte["outage_begin_dt (UTC)"].dt.strftime("%Y-%m-%d")
)
df_entsoe["match_key"] = (
    df_entsoe["unit_name"].str.upper().str.strip() + "|" +
    df_entsoe["outage_begin_dt (UTC)"].dt.strftime("%Y-%m-%d")
)

keys_rte    = set(df_rte["match_key"].dropna().unique())
keys_entsoe = set(df_entsoe["match_key"].dropna().unique())

intersection   = keys_rte & keys_entsoe
only_in_rte    = keys_rte - keys_entsoe
only_in_entsoe = keys_entsoe - keys_rte

print(f"Événements matchés (même réacteur + même jour) : {len(intersection)}")
print(f"Uniquement dans RTE     : {len(only_in_rte)}")
print(f"Uniquement dans ENTSO-E : {len(only_in_entsoe)}")

taux_couverture = 0.0
if len(keys_rte) > 0:
    taux_couverture = len(intersection) / len(keys_rte) * 100
    print(f"\nTaux de couverture ENTSO-E par rapport à RTE : {taux_couverture:.1f}%")
    print("(= % des événements RTE qui ont un équivalent dans ENTSO-E)")

# 4. puissances
print("\n" + "=" * 70)
print("4. COHÉRENCE DES PUISSANCES NOMINALES")
print("=" * 70)

pw_rte    = df_rte.groupby("unit_name")["nominal capacity (MW)"].median().rename("MW_RTE")
pw_entsoe = df_entsoe.groupby("unit_name")["nominal capacity (MW)"].median().rename("MW_ENTSOE")

pw_compare = pd.concat([pw_rte, pw_entsoe], axis=1).dropna()
pw_compare["ecart_MW"] = (pw_compare["MW_RTE"] - pw_compare["MW_ENTSOE"]).abs()
pw_compare["ecart_%"]  = (pw_compare["ecart_MW"] / pw_compare["MW_RTE"] * 100).round(1)

ecarts = pw_compare[pw_compare["ecart_%"] > 5]
if len(ecarts) > 0:
    print(f"{len(ecarts)} réacteurs avec écart de puissance > 5% :")
    print(ecarts.to_string())
else:
    print("Toutes les puissances nominales sont cohérentes (écart < 5%)")

# 5. export
rapport_path = os.path.join(OUTPUT_DIR, "rapport_croisement_sources.csv")
df_rapport = pd.DataFrame({
    "métrique": [
        "Lignes RTE (xlsx+API)",
        "Lignes ENTSO-E",
        "Réacteurs RTE",
        "Réacteurs ENTSO-E",
        "Réacteurs communs",
        "Événements matchés",
        "Uniquement RTE",
        "Uniquement ENTSO-E",
        "Taux couverture ENTSO-E (%)",
    ],
    "valeur": [
        len(df_rte),
        len(df_entsoe),
        len(reacteurs_rte),
        len(reacteurs_entsoe),
        len(communs),
        len(intersection),
        len(only_in_rte),
        len(only_in_entsoe),
        f"{taux_couverture:.1f}" if len(keys_rte) > 0 else "N/A",
    ]
})
df_rapport.to_csv(rapport_path, sep=";", index=False)
print(f"\nRapport exporté : {rapport_path}")

print("\n" + "=" * 70)
print("ANALYSE TERMINÉE")
print("=" * 70)
