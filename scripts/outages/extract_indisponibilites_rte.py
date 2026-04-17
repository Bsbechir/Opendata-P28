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

# === CONFIGURATION DES CHEMINS ===

# On récupère la racine de ton projet Git (pub-data-visualization)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Chemin exact d'après ton screenshot :
# On remonte d'un niveau pour sortir de 'pub-data-visualization' et entrer dans 'Opendata-P28'
PARENT_DIR = os.path.dirname(BASE_DIR)

INPUT_FILE = os.path.join(
    PARENT_DIR, 
    "_energy_public_data", 
    "24_RTE", 
    "DonneesIndisponibilitesProduction", 
    "indisponibilites_nucleaire_rte.csv"
)

# Dossier de sortie dans ton projet Git
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "indisponibilites_nucleaire_rte_CLEAN.csv")

def load_rte_data(filepath):
    """Charge le CSV avec gestion des erreurs d'encodage."""
    print(f"--- Lecture du fichier source : {filepath}")
    if not os.path.exists(filepath):
        return None
        
    try:
        # Test avec point-virgule (standard RTE)
        df = pd.read_csv(filepath, sep=";", encoding="utf-8", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, sep=";", encoding="latin-1", low_memory=False)
    return df

def clean_rte_data(df):
    """Nettoyage des colonnes et formats."""
    print(f"--- Nettoyage de {len(df)} lignes...")
    
    # Garder la version la plus récente
    if "Version" in df.columns and "Message ID" in df.columns:
        df["Version"] = pd.to_numeric(df["Version"], errors="coerce")
        df = df.sort_values("Version", ascending=False).drop_duplicates(subset=["Message ID"])

    # Conversion des dates
    for col in ["Date de début de l'événement (UTC)", "Date de fin de l'événement (UTC)"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    # Création du nom de site simplifié
    if "Nom de l'ouvrage" in df.columns:
        df["site"] = df["Nom de l'ouvrage"].str.replace(r"\s*\d+$", "", regex=True).str.strip()

    # Mapping pour l'animation
    rename_map = {
        "Date de début de l'événement (UTC)": "debut_indispo_utc",
        "Date de fin de l'événement (UTC)": "fin_indispo_utc",
        "Nom de l'ouvrage": "nom_unite",
        "Capacité installée": "puissance_max_mw",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    return df

def main():
    df = load_rte_data(INPUT_FILE)
    
    if df is None:
        print(f"\nERREUR : Le fichier est introuvable au chemin :\n{INPUT_FILE}")
        sys.exit(1)

    df_clean = clean_rte_data(df)

    # Sauvegarde
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_clean.to_csv(OUTPUT_FILE, index=False, sep=";")
    
    print(f"\nSUCCÈS !")
    print(f"Fichier source : {INPUT_FILE}")
    print(f"Fichier propre créé : {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
