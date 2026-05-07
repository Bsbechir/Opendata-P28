# Projet P17 — Données de disponibilité nucléaire (Groupe A)

## Objectif

Récupérer les données d'indisponibilité du parc nucléaire français depuis des sources publiques, les nettoyer et les fusionner en un seul fichier CSV livrable à EDF et au Groupe B.

**Ce qu'on ne fait PAS** : pas d'API, pas de connexion aux serveurs EDF, pas de publication sur l'OpenData (c'est EDF qui s'en charge avec notre CSV).

---

## Sources de données

| Source | Méthode | Script | Obligation légale |
|---|---|---|---|
| RTE (fichiers xlsx) | Manuel (services-rte.com) | Lu par `generate_csv_final.py` | RTE doit tout publier |
| RTE API | Automatique (API REST) | `download_rte_unavailability.py` | Mêmes données |
| ENTSO-E | Automatique (entsoe-py) | `download_entsoe.py` | Miroir européen |

> **Note** : RTE a l'obligation légale de publier toutes les indisponibilités. Les données RTE sont donc la **référence**. ENTSO-E est un miroir qui reçoit les données de RTE.

---

## CSV final

**Fichier** : `output/indisponibilites_nucleaire_final.csv`
**Taille** : ~110 000 lignes, 58 réacteurs, 3 sources fusionnées

| Colonne | Description | Exemple |
|---|---|---|
| `publication_id` | Identifiant unique de l'événement | `-EDF-05470-...` |
| `version` | Numéro de version | `2` |
| `publication_dt (UTC)` | Date de publication | `2024-01-15 08:30:00+00:00` |
| `outage_begin_dt (UTC)` | Début de l'arrêt | `2024-02-01 00:00:00+00:00` |
| `outage_end_dt (UTC)` | Fin prévue | `2024-05-15 00:00:00+00:00` |
| `unit_name` | Réacteur | `GRAVELINES 1` |
| `available capacity (MW)` | Puissance dispo pendant l'arrêt | `0.0` |
| `nominal capacity (MW)` | Puissance nominale installée | `910.0` |
| `producer_name` | Producteur | `EDF` |
| `map_code` | Zone géographique | `FR` |
| `production_source` | Filière | `nuclear` |
| `creation_dt (UTC)` | Date de création du document | `2024-01-10 ...` |
| `outage_type` | Type d'arrêt | `planned` ou `fortuitous` |
| `outage_cause` | Cause (si dispo) | `Maintenance prévue` |
| `outage_status` | Statut | `Actif`, `Inactif`, `Annulé` |
| `source` | Provenance | `RTE`, `RTE_API`, `ENTSOE` |

### Limites connues

- Les données ENTSO-E n'ont pas de `outage_cause` ni `outage_status` (ces champs sont vides)
- Pas de déduplication cross-source : un même événement peut apparaître dans RTE xlsx ET RTE API avec des `publication_id` différents
- Période : juillet 2014 → aujourd'hui
- Le statut `DISMISSED` (62 lignes RTE API) n'est pas traduit en français

---

## Installation

```bash
git clone https://github.com/Bsbechir/Opendata-P28.git
cd Opendata-P28
git checkout groupe-a-data
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Créer les variables d'environnement (voir `.env.example`) :

```bash
export RTE_CLIENT_ID='votre_id'
export RTE_CLIENT_SECRET='votre_secret'
export ENTSOE_API_KEY='votre_cle'
```

## Utilisation

```bash
# Mise à jour complète (téléchargement + fusion)
python3 scripts/outages/update.py

# Ou étape par étape :
python3 scripts/outages/download_entsoe.py
python3 scripts/outages/download_rte_unavailability.py
python3 scripts/outages/generate_csv_final.py

# Analyse croisée RTE vs ENTSO-E
python3 scripts/outages/analyse_croisement_sources.py

# Visualisation par réacteur
python3 scripts/outages/main_incremental_programs.py --list
python3 scripts/outages/main_incremental_programs.py --centrale "GRAVELINES 1"
python3 scripts/outages/main_incremental_programs.py --site GRAVELINES --annee-min 2020
```

### Données manuelles

Les fichiers xlsx RTE doivent être dans :
```
~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/
```

---

## Structure du repo

```
Opendata-P28/
├── scripts/outages/
│   ├── download_entsoe.py                  # Télécharge ENTSO-E
│   ├── download_rte_unavailability.py      # Télécharge API RTE
│   ├── generate_csv_final.py               # Fusionne les 3 sources → CSV
│   ├── update.py                           # Lance tout dans l'ordre
│   ├── analyse_croisement_sources.py       # Compare RTE vs ENTSO-E
│   └── main_incremental_programs.py        # Visualisation Gantt par centrale
├── output/
│   └── (CSV générés, non trackés par git)
├── .env.example                            # Template des clés API
├── requirements.txt                        # Dépendances Python
└── README.md                               # Ce fichier
```

---

## Équipe

| Rôle | Nom |
|---|---|
| Groupe A | Bechir Sidi Aly, Valentin Lavigne |
| Groupe B | Oumar, Corentin |
| Encadrement | EDF |
| Repo d'origine | [cre-dev/pub-data-visualization](https://github.com/cre-dev/pub-data-visualization) |
