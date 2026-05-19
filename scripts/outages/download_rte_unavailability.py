'''Ce fichier récupère les données d'indisponibilités depuis l'API RTE
Attention : Il faut mettre RTE_CLIENT_ID et RTE_CLIENT_SECRET dans l'environnement avant de lancer ce script (cf README.md)
Lancez :
   export RTE_CLIENT_ID='votre_id'
   export RTE_CLIENT_SECRET='votre_secret'
Le script rend un CSV avec les données d'indisponibilité de production nucléaire en France de 2015 à 2025, sauvegardé dans output/indisponibilites_nucleaires_rte.csv
'''
import requests
import base64
import json
import csv
import time
import os
import sys
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env") # On cherche un fichier .env à la racine du projet pour charger les variables d'environnement. 
# Si ce fichier existe, on lit chaque ligne et on ajoute les variables d'environnement définies dans ce fichier à l'environnement d'exécution du script. 
# Cela permet de stocker les identifiants de manière sécurisée et de ne pas les inclure directement dans le code source. Le format attendu du fichier .env est une ligne par variable, avec le format KEY=VALUE, et les lignes commençant par # sont considérées comme des commentaires.
if os.path.isfile(env_file):
    for line in open(env_file):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1) # On sépare la ligne en deux parties : la clé (k) et la valeur (v). Le paramètre 1 de split signifie que l'on ne fait qu'une seule séparation, ce qui permet de gérer les valeurs qui contiennent elles-mêmes des signes égal.
            os.environ.setdefault(k, v) # On ajoute la variable d'environnement à l'environnement d'exécution du script, mais seulement si elle n'est pas déjà définie (os.environ.setdefault).

client_id = os.environ.get("RTE_CLIENT_ID")
client_secret = os.environ.get("RTE_CLIENT_SECRET")
if not client_id or not client_secret:
    print("ERREUR : RTE_CLIENT_ID et RTE_CLIENT_SECRET non définis")
    print("Lancez :")
    print("  export RTE_CLIENT_ID='votre_id'")
    print("  export RTE_CLIENT_SECRET='votre_secret'")
    sys.exit(1)

url_base = "https://digital.iservices.rte-france.com"
url_api = f"{url_base}/open_api/unavailability_additional_information/v7/generation_unavailabilities"

annee_debut = 2015
annee_fin = 2026

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
fichier_csv = os.path.join(SCRIPT_DIR, "indisponibilites_nucleaires_rte.csv")


def get_token():
    """
    Récupère un jeton d'accès (access_token) auprès du serveur d'authentification.
    Utilise la méthode 'Basic Auth' pour envoyer les identifiants client.
    """
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode() # On concatène l'ID client et le code secret. Puis on encode cette chaîne en base64(format requis)
    r = requests.post(
        f"{url_base}/token/oauth/",
        headers={"Authorization": f"Basic {credentials}"}
    ) # On envoie une requête POST pour obtenir le token d'accès auprès du serveur d'authentification. L'URL et les paramètres sont spécifiques à l'API RTE.
    if r.status_code != 200:
        print(f"Erreur token: {r.status_code} {r.text}") #La requête n'est pas acceptée
        return None
    return r.json()["access_token"]


def download_month(token, year, month):
    """
    Prépare les paramètres de requête pour télécharger les données 
    d'un mois complet auprès d'une API (format UTC).
    """
    start = f"{year}-{month:02d}-01T00:00:00Z" # Génère la date de début : 1er jour du mois à 00:00:00 UTC,:02d permet d'avoir un formatage du moissur deux chiffres (ex: 2025-01 au lieu de 2025-1)
    if month == 12:
        end = f"{year+1}-01-01T00:00:00Z" # Si on est en décembre, la fin est le 1er janvier de l'année suivante
    else:
        end = f"{year}-{month+1:02d}-01T00:00:00Z" # Sinon, la fin est le 1er jour du mois suivant

    headers = {"Authorization": f"Bearer {token}"} # On prends le token récupéré précédemment.
    params = {
        "start_date": start,
        "end_date": end,
    }

    r = requests.get(url_api, headers=headers, params=params)

    if r.status_code in [200, 206]: # Dans le cas d'une authentification réussie
        data = r.json() # On récupère la liste des données d'indisponibilités. 
        unavails = data.get("generation_unavailabilities", [])
        return unavails
    elif r.status_code == 401:
        return "TOKEN_EXPIRED" # Le token a expiré, il faut le renouveler
    elif r.status_code == 404:
        return [] #404 signifie qu'il n'y a pas de données pour cette période, on retourne une liste vide
    else:
        print(f"  Erreur {r.status_code}: {r.text[:200]}")
        return []


def filter_nuclear(unavails):
    return [u for u in unavails if u.get("fuel_type") == "NUCLEAR"] #On garde uniquement les indisponibilités liées au nucléaire


def extract_row(u):
    """
    Transforme un objet d'indisponibilité brut en un dictionnaire plat (une ligne).
    'u' est un dictionnaire représentant une seule déclaration d'indisponibilité.
    """
    values = u.get("values", [{}])
    first_val = values[0] if values else {}#'values' est une liste de dictionnaires contenant les capacités disponibles et indisponibles. On prend le premier élément de cette liste pour extraire les informations de capacité. Si 'values' est vide, on utilise un dictionnaire vide pour éviter les erreurs d'accès.

    return {
        "identifier": u.get("identifier", ""),
        "version": u.get("version", ""),# Identifiants uniques de l'événement et de sa version
        "creation_date": u.get("creation_date", ""),
        "publication_date": u.get("publication_date", ""),# Dates de création et de publication de l'événement
        "start_date": u.get("start_date", ""),
        "end_date": u.get("end_date", ""),# Dates de début et de fin de l'indisponibilité
        "unavailability_type": u.get("unavailability_type", ""),# Type d'indisponibilité (ex: OUTAGE, DERATING, etc.)
        "event_status": u.get("event_status", ""),# Type d'indisponibilité et statut de l'événement (ex: PLANNED, UNPLANNED, etc.)
        "fuel_type": u.get("fuel_type", ""),# Type de combustible (ex: NUCLEAR)
        "market_participant": u.get("market_participant", ""), # Nom de l'acteur du marché responsable de l'unité de production concernée
        "affected_asset_or_unit_eic_code": u.get("affected_asset_or_unit_eic_code", ""),
        "affected_asset_or_unit_name": u.get("affected_asset_or_unit_name", ""),
        "affected_asset_or_unit_type": u.get("affected_asset_or_unit_type", ""),# Code EIC, nom et type de l'unité de production concernée
        "installed_capacity_mw": u.get("affected_asset_or_unit_installed_capacity", ""),
        "available_capacity_mw": first_val.get("available_capacity", ""),
        "unavailable_capacity_mw": first_val.get("unavailable_capacity", ""),# Capacités installée, disponible et indisponible en MW (extraites du premier élément de la liste 'values')
        "reason": u.get("reason", ""),
        "remarks": u.get("remarks", ""),# Raison et remarques associées à l'indisponibilité
    }


def main():
    '''Point d'entrée du script. Il gère le processus de téléchargement des données d'indisponibilité nucléaire depuis l'API de RTE, en traitant les données mois par mois, en filtrant pour ne garder que les arrêts nucléaires, et en extrayant les informations pertinentes pour les sauvegarder dans un fichier CSV. Le script gère également le renouvellement du token d'accès si celui-ci expire pendant le processus de téléchargement.'''
    print(">> Telechargement des indisponibilites nucleaires RTE")
    print(f"Periode: {annee_debut} - {annee_fin}")

    token = get_token()
    if not token: #Pas d'autorisation pour obtenir le token, on ne peut pas continuer
        print("Impossible d'obtenir le token. Veuillez vérifiez vos identifiants.")
        return

    print("Token OK\n")

    all_rows = [] # Liste pour stocker toutes les lignes extraites des données d'indisponibilité nucléaire
    total_brut = 0
    total_nuclear = 0

    for year in range(annee_debut, annee_fin + 1):
        for month in range(1, 13):
            print(f"  {year}-{month:02d}...", end=" ", flush=True)

            result = download_month(token, year, month)# On télécharge les données d'indisponibilité pour le mois en cours.

            if result == "TOKEN_EXPIRED":
                print("token expire, renouvellement...", end=" ", flush=True)
                token = get_token()# Si le token a expiré, on tente de le renouveler une fois.
                if not token:
                    print("ERREUR: impossible de renouveler le token")
                    return
                result = download_month(token, year, month)
                if result == "TOKEN_EXPIRED":
                    print("ERREUR persistante")
                    continue # Si le token continue à être refusé même après renouvellement, on passe au mois suivant sans traiter les données de ce mois.

            nuclear = filter_nuclear(result)
            total_brut += len(result)
            total_nuclear += len(nuclear)

            for u in nuclear:
                all_rows.append(extract_row(u)) # On transforme chaque objet d'indisponibilité nucléaire en une ligne plate (dictionnaire) et on l'ajoute à la liste all_rows.

            print(f"{len(result)} brut -> {len(nuclear)} nucleaire")

            # Un temps d'arrêt pour ne pas surcharger l'API avec trop de requêtes à la suite.
            time.sleep(3)

    print("\n---")
    print(f"Total brut: {total_brut}")
    print(f"Total nucleaire: {total_nuclear}")
    print("---")

    if all_rows: # Si on a récupéré des données, on les écrit dans un fichier CSV. Le nom du fichier est défini par la variable OUTPUT_CSV.
        fieldnames = list(all_rows[0].keys())
        with open(fichier_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)# On écrit les données dans le fichier CSV : d'abord l'en-tête avec les noms de colonnes, puis les lignes de données extraites.
        print(f"\nCSV exporte: {fichier_csv}")
        print(f"Nombre de lignes: {len(all_rows)}")
    else:
        print("\nAucune donnée n'a été récupérée.")

if __name__ == "__main__":
    main()
