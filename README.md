# Etude des indisponibilités du parc nucléaire français

## Préambule 
Ce dépôt git est le résultat d'un projet effectué par des étudiants de CentraleSupélec dans le cadre de l'enseignement Pôle Projet de l'école et en partenariat avec l'entreprise EDF. Ce travail s'effectue au sein du pôle 17 " Nouveaux Concepts Énergétiques" et a pour but d'étudier la disponibilité du parc nucléaire français. Ce git constitue la première partie de ce travail.

Nous avons construit ce travail à partir d'un repo Git fourni par l'entreprise EDF:
[cre-dev/pub-data-visualization](https://github.com/cre-dev/pub-data-visualization)

## Objectif

Le but est premièrement de récuperer les données d'indisponibilités du parc nucleaire français en s'appuyant sur les publications de RTE. 
Ensuite, de nettoyer les données puis les fusionner afin de créer un CSV qui répertorie toutes les informations des deux sources.
Dans le cadre de notre projet, ce fichier CSV est publié sur l'Open-Data d'EDF. Il a pu également servir à alimenter un site que nos camarades construisent, qui propose une visualisation de ces données (le travail sur le site constitue la deuxième partie de notre projet).

> **Note sur l'architecture du projet** : Ce script agit comme un consommateur de flux. Nous ne développons pas une nouvelle API publique ; nous requêtons l'API existantes de RTE et lisons des fichiers locaux pour consolider l'ensemble des données dans un fichier plat unique.

## Sources utilisées

Note importante: Ce projet s'appuie sur le cadre réglementaire européen REMIT (Regulation on Wholesale Energy Market Integrity and Transparency), qui impose aux exploitants une transparence totale et immédiate sur les indisponibilités de production afin de garantir l'intégrité des marchés de l'énergie et d'éviter toute asymétrie d'information.

| Source | Méthode | Script | Obligation légale |
|---|---|---|---|
| RTE (fichiers xlsx) | Manuel (services-rte.com) | Lu par `generate_csv_final.py` | Code de l'Énergie : Publication historique des données de marché |
| RTE API | Automatique (API REST) | `download_rte_unavailability.py` | Règlement REMIT : Obligation de transparence immédiate sur les informations privilégiées |


### Pourquoi prendre RTE comme source ?

Obligation Miroir : En vertu du règlement REMIT, toute indisponibilité de production doit être publiée simultanément sur la plateforme nationale (RTE).


## Création du fichier CSV final

**Fichier** : `output/indisponibilites_nucleaire_final.csv`

**Ordre de grandeur** : environ 110 000 lignes avant les derniers nettoyages, 58 reacteurs, 3 sources au depart. Le nombre final peut changer si on relance les scripts avec de nouvelles données.

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

### Limites connues de nos sources

- La déduplication cross-source reste approximative : on compare surtout le réacteur, le jour de début et le type d'arrêt
- Période : janvier 2015 à aujourd'hui selon les fichiers disponibles
- Le statut `DISMISSED` (62 lignes RTE API) n'est pas traduit en français

## Prérequis techniques

Python : version 3.10 ou supérieure (développé et testé avec Python 3.12)

## Installation

```bash
git clone https://github.com/Bsbechir/Opendata-P28.git
cd Opendata-P28
git checkout groupe-a-data
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## Prérequis : Installation des fichiers sources 

### Prérequis : Téléchargement des fichiers historiques RTE (`.xlsx`)

Certaines données historiques ne sont pas disponibles via API et doivent être récupérées manuellement.

Les fichiers `.xlsx` contiennent l'historique des indisponibilités déclarées par les producteurs
Comme l'importation de l'ensemble des données depuis 2015 est trop lourde pour le site on s'y prend en 2 fois (La première fois on prend les données provenant du `2015-01-01` au `2019-12-31`, puis la deuxième fois on prend du `2020-01-01` à aujourd'hui). Voici les étapes détaillées de la procédure:

1. **Accéder au portail** : Allez sur le portail IIP de RTE : [https://iip.cloud-rte-france.com/production-unavailability](https://iip.cloud-rte-france.com/production-unavailability)
2. **Inscription / Connexion** : Si vous n'avez pas de compte, cliquez sur "S'inscrire" et créez-en un (*Note : la validation peut prendre quelques jours*).
3. **Navigation** : Une fois connecté, vous arrivez sur la page *Pourvoirie / Production unavailability*.
> **Attention**: A répeter 2 fois les étapes 4 à 7, on exporte 2 fichiers en tout.
4. **Filtrer les données** : Cliquez sur "More filters" puis sélectionnez :
   * **Fuel type** : `Nuclear`
   * **Period** : La première fois on prend du `2015-01-01` à `2019-12-31`, puis la deuxième fois on prend du `2020-01-01` à aujourd'hui.
5. **Exporter** : Cliquez sur **Search** puis sur **Export** (bouton en haut à droite du tableau).
6. **Télécharger** : Téléchargez le fichier `.xlsx` généré.
7. **Organiser les fichiers** : Placez le ou les fichiers téléchargés dans le dossier dédié. 

Vous pouvez créer le dossier et y déplacer vos fichiers à l'aide des commandes suivantes :

```bash
# Créer le dossier s'il n'existe pas
mkdir -p ~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/

# Déplacer le fichier XLSX spécifique (adaptez le nom si nécessaire)
mv ~/Downloads/nom_du_fichier_rte.xlsx ~/_energy_public_data/24_RTE/DonneesIndisponibilitesProduction/
```

Note : Le script generate_csv_final.py lit automatiquement tous les fichiers .xlsx présents dans ce dossier. Vous pouvez donc y stocker plusieurs fichiers couvrant des périodes différentes. Nous, nous avons pris une période spécifique mais vous pouvez bien entendu prendre n'importe quelle période.


### Prérequis : Configuration des clés API

Le projet nécessite des clés d'accès à l'API de **RTE**. Ces informations sensibles doivent être configurées via des variables d'environnement.

#### 1. Clés d'API requises
L'accès aux données de RTE est gratuit, mais nécessite la création d'une "Application" sur leur plateforme.

1. **Créer un compte** :
   * Rendez-vous sur le [Portail Data RTE](https://data.rte-france.com/).
   * Cliquez sur **Connexion / Inscription** en haut à droite.
   * Remplissez le formulaire (l'activation du compte par email est instantanée).

2. **Créer une Application** :
   * Une fois connecté, cliquez sur votre prénom en haut à droite, puis sur **Mon Espace**.
   * Dans l'onglet **Mes applications**, cliquez sur le bouton **Créer une application**.
   * Donnez-lui un nom (par exemple : `Analyse-Indisponibilites`) et une description rapide, puis validez.

3. **S'abonner à l'API** :
   * Allez dans le **Catalogue d'APIs** (accessible depuis le menu du haut).
   * Recherchez l'API **Unavailability Additional Information** (généralement dans la catégorie *Production* ou *Génération*). 
   * *Lien direct vers le catalogue : [API Unavailability v7.0](https://data.rte-france.com/catalog/-/api/generation/Unavailability-Additional-Information/v7.0).*
   * Cliquez sur le bouton **S'abonner** (ou *Subscribe*).
   * Dans la liste déroulante, sélectionnez l'application que vous venez de créer (`Analyse-Indisponibilites`) et validez. L'accès est validé immédiatement.

4. **Récupérer vos identifiants** :
   * Retournez dans **Mon Espace** > **Mes applications**.
   * Cliquez sur le nom de votre application.
   * Vous y trouverez deux clés indispensables :
     * **ID Client** (qui correspondra à `RTE_CLIENT_ID`)
     * **Secret Client** (qui correspondra à `RTE_CLIENT_SECRET`)

#### 2. Mise en place des variables
Un fichier `.env.example` est fourni à la racine du projet pour servir de modèle. 
Pour des raisons de **sécurité** et de **collaboration**, les identifiants ne doivent jamais être écrits directement dans le code ou dans le fichier exemple (qui est partagé sur Git). Vous devez créer votre propre fichier local `.env` pour stocker vos identifiants en toute sécurité.

**Étape 1 :** Dupliquez le modèle vierge pour créer votre fichier de configuration personnel :
```bash
cp .env.example .env
```

**Étape 2 :** Ouvrez le fichier `.env` avec l'éditeur de votre choix pour le modifier :

```bash
# Option A : Directement dans le terminal (Recommandé / Universel)
nano .env   # (Faites Ctrl+O puis Entrée pour sauvegarder, Ctrl+X pour quitter)

# Option B : Si vous utilisez Visual Studio Code
code .env

# Option C : Sur Mac (avec l'application TextEdit par défaut)
open .env

# Option D : Sur Windows / Git Bash (avec le Bloc-notes)
notepad .env
```

**Étape 3 :** Dans l'éditeur, remplacez les valeurs fictives par vos vraies clés RTE :
```env
RTE_CLIENT_ID=votre_client_id_ici
RTE_CLIENT_SECRET=votre_client_secret_ici
```

> **Attention aux fichiers cachés** : Le fichier s'appelant `.env`, il est considéré comme un fichier caché par votre système d'exploitation. Il n'apparaîtra probablement pas dans votre explorateur de fichiers graphique (Finder, Explorateur Windows). Privilégiez les commandes du terminal ci-dessus pour le manipuler.
>
> **Information** : Le fichier `.env` est lu automatiquement par les scripts Python dès leur lancement.
 


## Utilisation

*Note importante*: Selon la configuration de votre système et si vous n'utilisez pas d'environnement virtuel, il se peut que vous deviez remplacer la commande python3 par python (notamment sous Windows).

```bash
# Pour obtenir le fichier CSV vous pouvez lancer:
python3 scripts/outages/update.py

# Sinon on peut toujours relancer les étapes une par une:
python3 scripts/outages/download_rte_unavailability.py
python3 scripts/outages/generate_csv_final.py

# Nous avons de plus gardé et reconfiguré une visualisation présente sur le Git de La CRE vous devez exécuter ces fichiers après avoir obtenu le CSV.

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
│   ├── download_rte_unavailability.py      # Récupère les données via l'API RTE
│   ├── generate_csv_final.py               # Fusionne les 2 sources et génère le CSV 
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
| Equipe en charge de la récupération des données d'indisponibilités| Bechir Bechir, Valentin Lavigne |
| Equipe en charge du site Internet contenant les visualisations | Oumar El_Hadj Amadou, Corentin Prizzon|
| Encadrement du projet | EDF, CentraleSupelec |
| Repo d'origine | [cre-dev/pub-data-visualization](https://github.com/cre-dev/pub-data-visualization) |

