"""
Script d'extraction des indisponibilités nucléaires depuis les données RTE.
Lit le fichier IndisponibilitesProduction.csv téléchargé depuis services-rte.com
et produit un CSV propre.

Usage:
    python extract_indisponibilites_rte.py
"""

import pandas as pd
import os
import sys

# === CHEMINS ===
INPUT_FILE = os.path.expanduser(
    "~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/IndisponibilitesProduction.csv"
)
OUTPUT_DIR = os.path.expanduser("~/Opendata-P28/output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "indisponibilites_nucleaire_rte.csv")


def load_rte_data(filepath):
    """Charge le CSV RTE."""
    print(f"Lecture de {filepath}...")
    df = pd.read_csv(
        filepath,
        sep=";",
        encoding="utf-8",
        low_memory=False,
    )
    print(f"  {len(df)} lignes chargées")
    print(f"  Colonnes : {list(df.columns)}")
    return df


def clean_rte_data(df):
    """Nettoie et transforme les données RTE en CSV propre."""

    # Données déjà filtrées sur le nucléaire depuis services-rte.com

    # --- Garder seulement la dernière version de chaque indisponibilité ---
    if "Message ID" in df.columns and "Version" in df.columns:
        df["Version"] = pd.to_numeric(df["Version"], errors="coerce")
        df = df.sort_values("Version", ascending=False)
        df = df.drop_duplicates(subset=["Message ID"], keep="first")
        print(f"  {len(df)} lignes après dédoublonnage (dernière version)")

    # --- Convertir les dates ---
    date_cols = [
        "Date et heure de publication (UTC)",
        "Date de début de l'événement (UTC)",
        "Date de fin de l'événement (UTC)",
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    # --- Convertir les puissances en numérique ---
    num_cols = [
        "Capacité installée",
        "Capacité disponible minimale",
        "Capacité indisponible maximale",
        "Capacité disponible",
        "Capacité indisponible",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- Extraire le nom du site depuis le nom de l'ouvrage ---
    if "Nom de l'ouvrage" in df.columns:
        df["site"] = (
            df["Nom de l'ouvrage"]
            .str.replace(r"\s*\d+$", "", regex=True)
            .str.strip()
        )

    # --- Renommer les colonnes pour le CSV final ---
    rename_map = {
        "Date et heure de publication (UTC)": "date_publication_utc",
        "Message ID": "message_id",
        "Version": "version",
        "Statut": "statut",
        "Type d'indisponibilité": "type_indisponibilite",
        "Nom de l'acteur de marché": "producteur",
        "Nom de l'ouvrage": "nom_unite",
        "Code EIC de l'ouvrage": "code_eic",
        "Filière de production": "filiere",
        "Capacité installée": "puissance_max_mw",
        "Capacité disponible minimale": "puissance_dispo_min_mw",
        "Capacité indisponible maximale": "puissance_indispo_max_mw",
        "Date de début de l'événement (UTC)": "debut_indispo_utc",
        "Date de fin de l'événement (UTC)": "fin_indispo_utc",
        "Cause de l'indisponibilité": "cause",
        "Remarques": "remarques",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # --- Sélectionner les colonnes finales ---
    final_cols = [
        "date_publication_utc",
        "message_id",
        "version",
        "statut",
        "type_indisponibilite",
        "producteur",
        "nom_unite",
        "site",
        "code_eic",
        "filiere",
        "puissance_max_mw",
        "puissance_dispo_min_mw",
        "puissance_indispo_max_mw",
        "debut_indispo_utc",
        "fin_indispo_utc",
        "cause",
    ]
    final_cols = [c for c in final_cols if c in df.columns]
    df = df[final_cols]

    # --- Trier par date ---
    if "debut_indispo_utc" in df.columns:
        df = df.sort_values("debut_indispo_utc", ascending=True)

    df = df.reset_index(drop=True)
    return df


def print_summary(df):
    """Affiche un résumé des données."""
    print("\n=== RÉSUMÉ ===")
    print(f"Nombre de lignes : {len(df)}")
    if "debut_indispo_utc" in df.columns:
        print(f"Période : {df['debut_indispo_utc'].min()} → {df['debut_indispo_utc'].max()}")
    if "nom_unite" in df.columns:
        print(f"Unités : {df['nom_unite'].nunique()} unités distinctes")
        print(f"  {sorted(df['nom_unite'].unique())}")
    if "site" in df.columns:
        print(f"Sites : {df['site'].nunique()} sites distincts")
    if "type_indisponibilite" in df.columns:
        print(f"Types : {df['type_indisponibilite'].value_counts().to_dict()}")
    if "statut" in df.columns:
        print(f"Statuts : {df['statut'].value_counts().to_dict()}")


def main():
    # Vérifier que le fichier existe
    if not os.path.exists(INPUT_FILE):
        print(f"ERREUR : fichier introuvable : {INPUT_FILE}")
        print("As-tu copié le fichier avec :")
        print(f"  cp ~/Downloads/IndisponibilitesProduction.csv {os.path.dirname(INPUT_FILE)}/")
        sys.exit(1)

    # Charger
    df = load_rte_data(INPUT_FILE)

    # Nettoyer
    df = clean_rte_data(df)

    # Résumé
    print_summary(df)

    # Sauvegarder
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, sep=";")
    print(f"\nCSV sauvegardé : {OUTPUT_FILE}")
    print(f"  {len(df)} lignes × {len(df.columns)} colonnes")

    # Générer le fichier de référence des centrales
    ref_file = os.path.join(OUTPUT_DIR, "reference_centrales_nucleaires.csv")
    ref = df[["nom_unite", "site", "code_eic", "puissance_max_mw"]].drop_duplicates("nom_unite")
    ref = ref.sort_values("site").reset_index(drop=True)
    ref.to_csv(ref_file, index=False, sep=";")
    print(f"\nRéférence centrales sauvegardée : {ref_file}")
    print(f"  {len(ref)} tranches sur {ref['site'].nunique()} sites")


if __name__ == "__main__":
    main()
