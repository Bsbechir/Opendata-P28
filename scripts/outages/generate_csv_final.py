''' Ce script permet de regrouper les 2 sources de données d'indisponibilités de production nucléaire dans un seul CSV.
 On prend les données d'indisponibilité de production nucléaire de RTE via les fichiers xlsx et de l'API RTE (csv) via un script présent sur ce git (csv). 
 On les nettoie et on les fusionne dans un seul fichier CSV final.
 Le fichier final peut etre ensuite utilisé pour faire des analyses ou des visualisations sur les indisponibilités de production nucléaire en France.
 
 Attention : ce script suppose que les données d'indisponibilité de production nucléaire ont déjà été téléchargées en : 
 1: Exécutant le scripts download_rte_unavailability.py.Ce script télécharge les données d'indisponibilité de production nucléaire de RTE via leur API et les sauvegarde dans un fichier CSV. 
 2: En ayant les fichiers xlsx de RTE déjà présents dans le dossier spécifié "~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction" sur votre ordinateur. 
 
 Si ces données ne sont pas présentes, ce script ne pourra pas fonctionner correctement. Assurez-vous d'avoir exécuté les scripts de téléchargement et d'avoir les fichiers nécessaires avant de lancer ce script.

 Après avoir exécuté ce script, vous trouverez le fichier CSV final dans le dossier output du projet, avec le nom indisponibilites_nucleaire_final.csv.
 Ce fichier contiendra toutes les données d'indisponibilité de production nucléaire fusionnées et nettoyées, prêtes à être utilisées.'''

import pandas as pd
import os
import glob

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # On définit le chemin de base du projet.
OUTPUT_DIR = os.path.join(BASE_DIR, "output") # On définit le chemin du dossier de sortie où les données finales seront sauvegardées. Ce dossier doit exister pour que le script puisse enregistrer le fichier CSV final.

# Tout d'abord on charge les fichiers xlsx de RTE

print("Chargement RTE xlsx...")

rte_folder = os.path.expanduser(
    "~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/"
) 

xlsx_files = sorted(glob.glob(os.path.join(rte_folder, "*.xlsx"))) # On utilise glob pour trouver tous les fichiers xlsx dans le dossier spécifié. Cela nous permet de charger tous les fichiers d'indisponibilité de production nucléaire de RTE, même s'ils sont ajoutés ou mis à jour au fil du temps.
print(f"Fichiers trouvés : {len(xlsx_files)}")

dfs_rte = []
for f in xlsx_files:
    print(f"  {os.path.basename(f)}...")
    df_tmp = pd.read_excel(f) # On charge chaque fichier xlsx de RTE dans un DataFrame temporaire. Chaque fichier peut contenir des données d'indisponibilité de production nucléaire pour une période spécifique, et en les chargeant tous, nous pouvons ensuite les fusionner pour obtenir une vue complète des données de RTE.
    df_tmp["file_name"] = os.path.basename(f) # On ajoute une colonne "file_name" à chaque DataFrame temporaire pour garder une trace de l'origine des données.
    dfs_rte.append(df_tmp) # On ajoute chaque DataFrame temporaire à une liste.
df_rte = pd.concat(dfs_rte, ignore_index=True) # Après avoir chargé tous les fichiers xlsx de RTE, on les concatène en un seul DataFrame. Cela nous donne un DataFrame complet avec toutes les données d'indisponibilité de production nucléaire de RTE, ce qui facilitera le nettoyage et la fusion avec les autres sources de données.
print(f"RTE brut : {len(df_rte)} lignes")

# Les noms de colonnes RTE changent un peu selon les fichiers ainsi on utilise cette méthode suggérée par IA
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
        rename_map[col] = "outage_cause" # On crée ainsi un dictionnaire de renommage pour les colonnes du DataFrame de RTE.

df_rte = df_rte.rename(columns=rename_map) #On utilise le dictionnaire de renommage 
df_rte["creation_dt (UTC)"] = df_rte["publication_dt (UTC)"] # On crée lacolonne "creation_dt (UTC)" à partir de la colonne "publication_dt (UTC)". Cela nous permet de garder une trace de la date de création des données d'indisponibilité de production nucléaire, ce qui nous est utile pour l'analyse et le suivi des données au fil du temps
df_rte["source"] = "RTE" # Nos données viennent de RTE

df_rte = df_rte[df_rte["production_source"] == "Nucléaire"].copy() # On filtre les données pour ne garder que celles qui concernent le nucléaire.
print(f"RTE nucléaire : {len(df_rte)} lignes")

# Enfin on recupere le csv obtenu avec l'API RTE
print("\nChargement RTE API...")
rte_api_path = os.path.join(BASE_DIR, "scripts", "outages", "indisponibilites_nucleaires_rte.csv")
df_rte_api = pd.read_csv(rte_api_path, sep=",", low_memory=False)
print(f"RTE API brut : {len(df_rte_api)} lignes")

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
# On renomme les colonnes du DataFrame de l'API RTE pour les faire correspondre au format que nous utilisons dans le fichier final. Cela facilite la fusion des données de l'API RTE avec celles de RTE et d'ENTSO-E.

df_rte_api["production_source"] = "nuclear"
df_rte_api["map_code"] = "FR"

df_rte_api["outage_type"] = df_rte_api["unavailability_type"].map({
    "PLANNED":   "planned",
    "UNPLANNED": "fortuitous",
}).fillna(df_rte_api["unavailability_type"]) # On crée une nouvelle colonne "outage_type" à partir de la colonne "unavailability_type" de l'API RTE. On mappe les types d'arrêt prévus et non prévus aux valeurs "planned" et "fortuitous" que nous utilisons dans le fichier final. Si un type d'arrêt ne correspond pas à ces catégories, on garde la valeur originale de "unavailability_type".

df_rte_api["outage_status"] = df_rte_api["outage_status"].map({
    "ACTIVE":    "Actif",
    "INACTIVE":  "Inactif",
    "CANCELLED": "Annulé",
}).fillna(df_rte_api["outage_status"]) # On mappe les statuts d'arrêt de l'API RTE aux valeurs "Actif", "Inactif" et "Annulé" que nous utilisons dans le fichier final. Si un statut ne correspond pas à ces catégories, on garde la valeur originale de "outage_status".

df_rte_api["outage_cause"] = df_rte_api["outage_cause"].map({
    "COMPLEMENTARY_INFORMATION": "Information Complémentaire",
    "FORESEEN_MAINTENANCE":      "Maintenance prévue",
    "UNPLANNED_MAINTENANCE":     "Maintenance non prévue",
    "UNPLANNED_OUTAGE":          "Arrêt non prévu",
    "PLANNED_MAINTENANCE":       "Maintenance prévue",
}).fillna(df_rte_api["outage_cause"]) # On mappe les causes d'arrêt de l'API RTE aux valeurs "Information Complémentaire", "Maintenance prévue", "Maintenance non prévue" et "Arrêt non prévu" que nous utilisons dans le fichier final. Si une cause ne correspond pas à ces catégories, on garde la valeur originale de "outage_cause".

for col in ["publication_dt (UTC)", "outage_begin_dt (UTC)", "outage_end_dt (UTC)", "creation_dt (UTC)"]:
    if col in df_rte_api.columns:
        df_rte_api[col] = pd.to_datetime(df_rte_api[col], utc=True) # On convertit les colonnes de dates de l'API RTE en format datetime avec timezone UTC.

df_rte_api["source"] = "RTE_API"
print(f"RTE API nucléaire : {len(df_rte_api)} lignes")

#On remet tout les colonnes dans le même ordre avant de concatener

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

for col in colonnes_finales: # Commandes suggérées par l'IA pour s'assurer que toutes les colonnes nécessaires sont présentes dans chaque DataFrame avant de les concaténer. Si une colonne est manquante dans un DataFrame, elle est créée avec des valeurs vides. Cela garantit que la fusion des données se fait correctement sans erreurs dues à des colonnes manquantes.
    if col not in df_rte.columns:
        df_rte[col] = ""
    if col not in df_rte_api.columns:
        df_rte_api[col] = ""

df_rte     = df_rte[colonnes_finales]
df_rte_api = df_rte_api[colonnes_finales]

#Debut de la fusion
print("\nFusion...")
df_final = pd.concat([df_rte, df_rte_api], ignore_index=True) #Concaténation des Dataframes en un seul final
print(f"Total : {len(df_final)} lignes  (RTE xlsx: {len(df_rte)}, RTE API: {len(df_rte_api)})")

#Ensuite on commence le nettoyage 
print("\nNettoyage...")

df_final["outage_type"] = df_final["outage_type"].replace({
    "Planifiée": "planned",
    "Fortuite":  "fortuitous",
})
print(f"Types d'arrêt : {df_final['outage_type'].unique().tolist()}")

df_final["production_source"] = "nuclear"
df_final["map_code"]          = "FR"

df_final["unit_name"]     = df_final["unit_name"].str.strip().str.strip('"') # On nettoie les noms des unités de production en supprimant les espaces superflus et les guillemets
df_final["producer_name"] = df_final["producer_name"].str.strip().str.strip('"')# On nettoie les noms des producteurs(ici il y a que EDF) de la même manière que pour les unités de production.

for col in ["publication_dt (UTC)", "outage_begin_dt (UTC)", "outage_end_dt (UTC)", "creation_dt (UTC)"]:
    df_final[col] = pd.to_datetime(df_final[col], utc=True, errors="coerce")

#On trie les données déjà vues : même publication et même version
df_final = df_final.sort_values(["publication_id", "version"], ascending=[True, False])
df_final = df_final.drop_duplicates(subset=["publication_id", "version"], keep="first") #On garde la ligne avec la version la plus récente

# Parfois le même arret est present dans plusieurs sources
# On choisit de garder RTE xlsx en premier car c'est la source la plus lisible ici

#Les commandes suivantes ont été suggérées par l'IA pour créer des clés de déduplication basées sur le nom de l'unité de production, la date de début de l'arrêt et le type d'arrêt. En attribuant une priorité (RTE xlsx > RTE API ) et en triant les données en conséquence, on peut ensuite supprimer les doublons en ne gardant que la ligne la plus prioritaire pour chaque arrêt.
df_final["_dedup_key"] = (
    df_final["unit_name"].str.upper().str.strip() + "|" +
    pd.to_datetime(df_final["outage_begin_dt (UTC)"], utc=True).dt.strftime("%Y-%m-%d") + "|" +
    df_final["outage_type"].str.lower().str.strip()
) # On crée une clé de déduplication en combinant le nom de l'unité de production, la date de début de l'arrêt et le type d'arrêt. Cela nous permet d'identifier les lignes qui correspondent au même arrêt, même si elles proviennent de sources différentes ou ont des formats légèrement différents (arrêts prévus ou imprévus).

source_priority = {"RTE": 0, "RTE_API": 1}
df_final["_source_rank"] = df_final["source"].map(source_priority).fillna(3) 
# On attribue une priorité à chaque source de données en créant une nouvelle colonne "_source_rank". Si une source n'est pas reconnue, elle reçoit une priorité de 3
before_cross = len(df_final)
df_final = df_final.drop_duplicates(subset=["_dedup_key"], keep="first")# On supprime les doublons en ne gardant que la ligne avec la source la plus prioritaire pour chaque clé de déduplication
print(f"Dédup cross-source : {before_cross} → {len(df_final)} ({before_cross - len(df_final)} doublons retirés)")

df_final = df_final.drop(columns=["_dedup_key", "_source_rank"]) # On supprime les colonnes temporaires utilisées pour la déduplication
df_final = df_final.sort_values("outage_begin_dt (UTC)").reset_index(drop=True)
print(f"Après déduplication : {len(df_final)} lignes")
print(f"Réacteurs distincts : {df_final['unit_name'].nunique()}")

output_file = os.path.join(OUTPUT_DIR, "indisponibilites_nucleaire_final.csv") # Le chemin complet du fichier CSV final avec son nom "indisponibilites_nucleaire_final.csv"
df_final.to_csv(output_file, sep=";", index=False, encoding="utf-8")
print(f"\nCSV exporté : {output_file}")
print(f"Lignes : {len(df_final)}")
print(f"Sources : {df_final['source'].value_counts().to_dict()}")
