# Etude des indisponibilités du parc nucléaire français

## Préambule 
Ce git est le fruit d'un projet effectué par des étudiants de CentraleSupélec dans le cadre de l'enseignement Pôle Projet de l'école en partenariat avec l'entreprise EDF. Ce travail s'effectue au sein du pôle 17 " Nouveaux Concepts Énergétiques" et a pour but d'étudier la disponibilité du parc nucléaire français. Ce git constitue la première partie de ce travail.

Nous avons construit notre travail à partir d'un repo Git fourni par l'entreprise EDF:
[cre-dev/pub-data-visualization](https://github.com/cre-dev/pub-data-visualization)

## Objectif

Le but est premièrement de récuperer les données d'indisponibilites du parc nucleaire francais en s'appuyant sur les publications des API d'ENTSOE et RTE. 
Ensuite de nettoyer les données, les fusionner afin de créer un CSV qui répertorie toutes les informations.
Dans le cadre de notre projet ce fichier CSV doit ensuite pouvoir être éventuellement utilisé pour être publié sur l'Open-Data d'EDF. Il doit pouvoir également servir à alimenter un site que nos camarades construisent, qui propose une visualisation de ces données.

# Note importante: On ne réalise pas d'API ici. On utilise celles de ENTSOE et RTE pour construire un fichier.


## Sources utilisées

# Note importante: Ce projet s'appuie sur le cadre réglementaire européen REMIT (Regulation on Wholesale Energy Market Integrity and Transparency), qui impose aux exploitants une transparence totale et immédiate sur les indisponibilités de production afin de garantir l'intégrité des marchés de l'énergie et d'éviter toute asymétrie d'information. »

| Source | Méthode | Script | Obligation légale |
|---|---|---|---|
| RTE (fichiers xlsx) | Manuel (services-rte.com) | Lu par `generate_csv_final.py` | Code de l'Énergie : Publication historique des données de marché |
| RTE API | Automatique (API REST) | `download_rte_unavailability.py` | Règlement REMIT : Obligation de transparence immédiate sur les informations privilégiées |
| ENTSO-E | Automatique (entsoe-py) | `download_entsoe.py` | Règlement Transparence (UE 543/2013) : Centralisation européenne des données de production |

# Pourquoi croiser ces sources ?
Bien que RTE soit l'acteur central pour le parc français, ce projet utilise une approche multi-sources pour plusieurs raisons :

Complétude des données : RTE est la source la plus riche sur les causes d'arrêts en français, tandis qu'ENTSO-E fournit une vision standardisée au niveau européen.

Obligation Miroir : En vertu du règlement REMIT, toute indisponibilité de production doit être publiée simultanément sur la plateforme nationale (RTE) et sur la plateforme européenne (ENTSO-E Transparency Platform). Ce script vérifie la cohérence de ce "miroir".

Résilience : L'utilisation des deux plateformes permet de pallier d'éventuels retards de mise à jour ou des indisponibilités temporaires d'une des deux API.

## Création du fichier CSV final

**Fichier** : `output/indisponibilites_nucleaire_final.csv`

**Ordre de grandeur** : environ 110 000 lignes avant les derniers nettoyages, 58 reacteurs, 3 sources au depart. Le nombre final peut changer si on relance les scripts avec de nouvelles donnees.

Voici la description des colonnes présentes sur le CSV :

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

### Limites connues de nos sources

- Les données ENTSO-E n'ont pas de `outage_cause` ni `outage_status` (ces champs sont vides)
- La déduplication cross-source reste approximative : on compare surtout le réacteur, le jour de début et le type d'arrêt
- Période : juillet 2014 à aujourd'hui selon les fichiers disponibles
- Le statut `DISMISSED` (62 lignes RTE API) n'est pas traduit en français

### Prérequis : Installation des fichiers sources 

Certaines données historiques ne sont pas disponibles via API et doivent être récupérées manuellement.

Données RTE (Excel) : Vous devez télécharger les fichiers .xlsx directement depuis le site services-rte.com.

Chemin local : Ces fichiers doivent impérativement être placés dans le répertoire suivant pour être détectés par le script de fusion :
~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/

Note : Le script generate_csv_final.py utilise ce chemin spécifique pour intégrer l'historique aux données récupérées automatiquement par API.


## Configuration

Le projet nécessite des clés d'accès aux API de **RTE** et d'**ENTSO-E**. Ces informations sensibles doivent être configurées via des variables d'environnement.

### 1. Clés d'API requises
Vous pouvez obtenir vos accès gratuitement sur les portails développeurs respectifs :
*   **RTE** : [Portail Data de RTE](https://www.services-rte.com/) (créez une application pour obtenir l'ID et le Secret).
*   **ENTSO-E** : [Transparency Platform](https://transparency.entsoe.eu/) (la clé s'obtient dans les paramètres de votre compte).

### 2. Mise en place des variables
Un fichier `.env.example` est fourni à la racine du projet pour servir de modèle. 

**Option A : Via un fichier `.env` (Recommandé)**  
Copiez le fichier d'exemple et remplissez-le avec vos accès :
```bash
cp .env.example .env
```
Editez ensuite le fichier .env avec vos clés


**Option B : Export direct dans le terminal (Session temporaire)

Si vous ne souhaitez pas créer de fichier `.env`, vous devez exporter les variables manuellement dans votre terminal avant d'exécuter les scripts. Attention, ces variables disparaîtront à la fermeture du terminal.

```bash
# Configuration pour RTE
export RTE_CLIENT_ID='votre_id_client_ici'
export RTE_CLIENT_SECRET='votre_secret_client_ici'

#Configuration pour ENTSO-E
export ENTSOE_API_KEY='votre_cle_api_ici'
#Vérification (optionnel)
echo $RTE_CLIENT_ID 
```
## Installation

```bash
git clone https://github.com/Bsbechir/Opendata-P28.git
cd Opendata-P28
git checkout groupe-a-data
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
# Pour obtenir le fichier CSV vous pouvez lancez
python3 scripts/outages/update.py

# Sinon on peut toujours relancer les étapes une par une
python3 scripts/outages/download_entsoe.py
python3 scripts/outages/download_rte_unavailability.py
python3 scripts/outages/generate_csv_final.py

# Nous avons de plus garder et reconfigurer une visualisation présente sur le Git de La CRE vous devez exécuter ces fichiers après avoir obtenu le CSV

python3 scripts/outages/main_incremental_programs.py --list
python3 scripts/outages/main_incremental_programs.py --centrale "GRAVELINES 1"
python3 scripts/outages/main_incremental_programs.py --site GRAVELINES --annee-min 2020
python3 scripts/outages/main_incremental_programs.py --all
```

## Structure du repo git 
Vous trouverez en haut de chaque script une description précise de ce qu'il fait. 
```
Opendata-P28/
├── scripts/outages/
│   ├── download_entsoe.py                  # Récupère les données via l'API d'ENTSO-E
│   ├── download_rte_unavailability.py      # Récupère les données via l'API RTE
│   ├── generate_csv_final.py               # Fusionne les 3 sources et génère le CSV 
│   ├── update.py                           # Lance les scripts dans l'ordre avec les dernières modifications
│   └── main_incremental_programs.py        # Quelques simulations et graphiques sur des données specifiques à un réacteur ou un site de production
├── output/
│   └── (CSV génerés par les script)
├── .env.example
├── requirements.txt
└── README.md
```


## Équipe ayant travaillé sur ce projet

| Rôle | Nom |
|---|---|
| Equipe en charge de la récupération des données d'indisponibilités| Bechir Sidi Aly, Valentin Lavigne |
| Equipe en charge du site Internet contenant les visualisations | Oumar El_Hadj Amadou, Corentin Prizzon|
| Encadrement du projet | EDF, CentraleSupelec |
| Repo d'origine | [cre-dev/pub-data-visualization](https://github.com/cre-dev/pub-data-visualization) |

