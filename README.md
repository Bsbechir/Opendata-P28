# Projet P17 - indisponibilites nucleaires

## Objectif

Dans cette partie du projet, on s'occupe surtout de la donnee.

Le but est de recuperer les indisponibilites du parc nucleaire francais, puis de les nettoyer pour sortir un CSV commun. Ce fichier doit ensuite pouvoir etre utilise par EDF et par le groupe B pour la partie visualisation.

On ne fait pas d'API ici. On prepare les fichiers.


## Sources utilisees

| Source | Méthode | Script | Obligation légale |
|---|---|---|---|
| RTE (fichiers xlsx) | Manuel (services-rte.com) | Lu par `generate_csv_final.py` | RTE doit tout publier |
| RTE API | Automatique (API REST) | `download_rte_unavailability.py` | Mêmes données |
| ENTSO-E | Automatique (entsoe-py) | `download_entsoe.py` | Miroir européen |

En pratique, RTE est notre source principale. Les donnees ENTSO-E sont utiles pour comparer, mais elles sont moins completes sur certains champs.

## CSV final

**Fichier** : `output/indisponibilites_nucleaire_final.csv`

**Ordre de grandeur** : environ 110 000 lignes avant les derniers nettoyages, 58 reacteurs, 3 sources au depart. Le nombre final peut changer si on relance les scripts avec de nouvelles donnees.

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
- La deduplication cross-source reste approximative : on compare surtout le reacteur, le jour de debut et le type d'arret
- Période : juillet 2014 a aujourd'hui selon les fichiers disponibles
- Le statut `DISMISSED` (62 lignes RTE API) n'est pas traduit en français
- Les fichiers RTE xlsx sont encore recuperes a la main, donc il faut les mettre au bon endroit avant de lancer la fusion


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

Il faut mettre les cles API dans l'environnement. Le fichier `.env.example` donne le format attendu.

```bash
export RTE_CLIENT_ID='votre_id'
export RTE_CLIENT_SECRET='votre_secret'
export ENTSOE_API_KEY='votre_cle'
```

## Utilisation

```bash
# normalement on lance ca
python3 scripts/outages/update.py

# sinon on peut relancer les etapes une par une
python3 scripts/outages/download_entsoe.py
python3 scripts/outages/download_rte_unavailability.py
python3 scripts/outages/generate_csv_final.py

# visualisation rapide
python3 scripts/outages/main_incremental_programs.py --list
python3 scripts/outages/main_incremental_programs.py --centrale "GRAVELINES 1"
python3 scripts/outages/main_incremental_programs.py --site GRAVELINES --annee-min 2020
python3 scripts/outages/main_incremental_programs.py --all
```

### Données manuelles

Les fichiers xlsx RTE ne sont pas telecharges automatiquement par nos scripts. Il faut les mettre ici :
```
~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/
```


## Structure du repo

```
Opendata-P28/
├── scripts/outages/
│   ├── download_entsoe.py                  # recupere ENTSO-E
│   ├── download_rte_unavailability.py      # recupere l'API RTE
│   ├── generate_csv_final.py               # fusionne les sources
│   ├── update.py                           # lance les scripts dans l'ordre
│   └── main_incremental_programs.py        # quelques graphes par reacteur/site
├── output/
│   └── (CSV generes, non suivis par git)
├── .env.example
├── requirements.txt
└── README.md
```


## Équipe

| Rôle | Nom |
|---|---|
| Groupe A | Bechir Sidi Aly, Valentin Lavigne |
| Groupe B | Oumar, Corentin |
| Encadrement | EDF |
| Repo d'origine | [cre-dev/pub-data-visualization](https://github.com/cre-dev/pub-data-visualization) |

## Notes

Le script principal pour produire le CSV final est `scripts/outages/generate_csv_final.py`.

`update.py` sert juste a lancer les telechargements puis la fusion dans le bon ordre. Si une cle API manque ou si les xlsx RTE ne sont pas presents, il s'arrete avant de lancer les scripts.

Pour les graphes, `--centrale` affiche un seul reacteur, `--site` affiche tous les reacteurs d'un site, et `--all` sauvegarde un PNG par reacteur dans `output/plots/centrales/`.
