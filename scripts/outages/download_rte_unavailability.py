import requests
import base64
import csv
import time
import os
import sys
from datetime import datetime

# identifiants pour l'API RTE
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
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    r = requests.post(
        f"{url_base}/token/oauth/",
        headers={"Authorization": f"Basic {credentials}"}
    )
    if r.status_code != 200:
        print(f"Erreur token: {r.status_code} {r.text}")
        return None
    return r.json()["access_token"]


def download_month(token, year, month):
    start = f"{year}-{month:02d}-01T00:00:00Z"
    if month == 12:
        end = f"{year+1}-01-01T00:00:00Z"
    else:
        end = f"{year}-{month+1:02d}-01T00:00:00Z"

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "start_date": start,
        "end_date": end,
    }

    r = requests.get(url_api, headers=headers, params=params)

    if r.status_code in [200, 206]:
        data = r.json()
        unavails = data.get("generation_unavailabilities", [])
        return unavails
    elif r.status_code == 401:
        return "TOKEN_EXPIRED"
    elif r.status_code == 404:
        return []
    else:
        print(f"  Erreur {r.status_code}: {r.text[:200]}")
        return []


def filter_nuclear(unavails):
    return [u for u in unavails if u.get("fuel_type") == "NUCLEAR"]


def extract_row(u):
    values = u.get("values", [{}])
    first_val = values[0] if values else {}

    return {
        "identifier": u.get("identifier", ""),
        "version": u.get("version", ""),
        "creation_date": u.get("creation_date", ""),
        "publication_date": u.get("publication_date", ""),
        "start_date": u.get("start_date", ""),
        "end_date": u.get("end_date", ""),
        "unavailability_type": u.get("unavailability_type", ""),
        "event_status": u.get("event_status", ""),
        "fuel_type": u.get("fuel_type", ""),
        "market_participant": u.get("market_participant", ""),
        "affected_asset_or_unit_eic_code": u.get("affected_asset_or_unit_eic_code", ""),
        "affected_asset_or_unit_name": u.get("affected_asset_or_unit_name", ""),
        "affected_asset_or_unit_type": u.get("affected_asset_or_unit_type", ""),
        "installed_capacity_mw": u.get("affected_asset_or_unit_installed_capacity", ""),
        "available_capacity_mw": first_val.get("available_capacity", ""),
        "unavailable_capacity_mw": first_val.get("unavailable_capacity", ""),
        "reason": u.get("reason", ""),
        "remarks": u.get("remarks", ""),
    }


def main():
    print(">> Telechargement des indisponibilites nucleaires RTE")
    print(f"Periode: {annee_debut} - {annee_fin}")

    token = get_token()
    if not token:
        print("Impossible d'obtenir le token. Verifie tes identifiants.")
        return

    print("Token OK\n")

    all_rows = []
    total_brut = 0
    total_nuclear = 0

    for year in range(annee_debut, annee_fin + 1):
        for month in range(1, 13):
            now = datetime.now()
            if year == now.year and month > now.month:
                break
            if year > now.year:
                break

            print(f"  {year}-{month:02d}...", end=" ", flush=True)

            result = download_month(token, year, month)

            if result == "TOKEN_EXPIRED":
                print("token expire, renouvellement...", end=" ", flush=True)
                token = get_token()
                if not token:
                    print("ERREUR: impossible de renouveler le token")
                    return
                result = download_month(token, year, month)
                if result == "TOKEN_EXPIRED":
                    print("ERREUR persistante")
                    continue

            nuclear = filter_nuclear(result)
            total_brut += len(result)
            total_nuclear += len(nuclear)

            for u in nuclear:
                all_rows.append(extract_row(u))

            print(f"{len(result)} brut -> {len(nuclear)} nucleaire")

            # l'API limite le nombre d'appels, donc on ralentit un peu
            time.sleep(3)

    print("\n---")
    print(f"Total brut: {total_brut}")
    print(f"Total nucleaire: {total_nuclear}")
    print("---")

    if all_rows:
        fieldnames = list(all_rows[0].keys())
        with open(fichier_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nCSV exporte: {fichier_csv}")
        print(f"Nombre de lignes: {len(all_rows)}")
    else:
        print("\nAucune donnee recuperee.")

if __name__ == "__main__":
    main()
