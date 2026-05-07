''' Ici nous avons un script pour visualiser les différents arrêts nucléaires par réacteur ou par site.
Il utilise le fichier CSV final généré par le processus de mise à jour des données d'indisponibilité de production nucléaire.
Executez le script update.py avant de lancer ce script pour vous assurer que les données sont à jour.
'''
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import os
import sys

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
CSV_PATH   = os.path.join(BASE_DIR, "output", "indisponibilites_nucleaire_final.csv")
PLOTS_DIR  = os.path.join(BASE_DIR, "output", "plots", "centrales") # Le dossier où les graphiques individuels par centrale seront sauvegardés. Chaque graphique portera le nom de la centrale correspondante (ex: GRAVELINES_1.png)


def load_data():
    if not os.path.exists(CSV_PATH):
        print(f"ERREUR : CSV non trouvé : {CSV_PATH}")
        print("Lancez d'abord : python3 scripts/outages/generate_csv_final.py")
        sys.exit(1) # On vérifie que le fichier CSV final existe avant de tenter de le charger
    df = pd.read_csv(CSV_PATH, sep=";", low_memory=False) # On charge le fichier CSV final dans un DataFrame pandas. Le séparateur est ';' et low_memory=False permet de charger les données plus rapidement en utilisant plus de mémoire.
    df["outage_begin_dt (UTC)"] = pd.to_datetime(df["outage_begin_dt (UTC)"], utc=True)
    df["outage_end_dt (UTC)"]   = pd.to_datetime(df["outage_end_dt (UTC)"], utc=True) # On convertit les colonnes de date de début et de fin des arrêts en format datetime avec timezone UTC. Cela nous permettra de faire des calculs de durée et de filtrer les données par date plus facilement.
    return df


def list_centrales(df):
    '''Affiche la liste de tous les réacteurs et sites disponibles dans les données d'indisponibilité de production nucléaire.''
    '''
    units = sorted(df["unit_name"].unique())

    sites = sorted(set(u.rsplit(" ", 1)[0] for u in units if " " in u)) # On extrait les sites à partir des noms des unités de production. On suppose que le nom de l'unité est composé du nom du site suivi d'un numéro (ex: "GRAVELINES 1"). En séparant par le dernier espace, on obtient le nom du site (ex: "GRAVELINES").

    print(f"\n>> {len(units)} réacteurs disponibles")
    for u in units:
        count = len(df[df["unit_name"] == u])
        print(f"  {u:<25} ({count} événements)")

    print(f"\n>> {len(sites)} sites disponibles")
    for s in sites:
        n = len([u for u in units if u.startswith(s)])
        print(f"  {s:<25} ({n} réacteurs)") # On affiche la liste de tous les réacteurs et sites disponibles dans les données d'indisponibilité de production nucléaire, ainsi que le nombre d'événements associés à chaque réacteur et le nombre de réacteurs associés à chaque site. Cela permet d'avoir une vue d'ensemble des données disponibles et de choisir les réacteurs ou sites à visualiser.


def plot_centrale(df, unit_name, year_min=None, year_max=None, save_path=None):
    '''Affiche un graphique des arrêts pour un réacteur donné, avec des couleurs différentes pour les arrêts planifiés et fortuits. On peut aussi filtrer les arrêts par année minimum et maximum'''
    
    df_unit = df[df["unit_name"] == unit_name].copy() # On filtre les données pour ne garder que les arrêts correspondant au réacteur spécifié par unit_name
    if len(df_unit) == 0:
        print(f"Aucune donnée pour '{unit_name}'")
        return # Si aucune donnée n'est trouvée pour le réacteur spécifié, on affiche un message et on quitte la fonction.

    if year_min:
        df_unit = df_unit[df_unit["outage_begin_dt (UTC)"].dt.year >= year_min]
    if year_max:
        df_unit = df_unit[df_unit["outage_begin_dt (UTC)"].dt.year <= year_max] 

    df_unit["duration"] = (
        df_unit["outage_end_dt (UTC)"] - df_unit["outage_begin_dt (UTC)"]
    ).dt.total_seconds() / 86400  # On calcule la durée de chaque arrêt en jours en soustrayant la date de début de la date de fin et en convertissant le résultat en secondes, puis en divisant par 86400 (le nombre de secondes dans une journée)

    colors = df_unit["outage_type"].map({ # On attribue une couleur à chaque type d'arrêt : bleu pour les arrêts planifiés, rouge pour les arrêts fortuits, et gris pour les types d'arrêt inconnus ou non spécifiés.
        "planned":    "#2196F3",   
        "fortuitous": "#F44336",   
    }).fillna("#9E9E9E")           

    fig, ax = plt.subplots(figsize=(16, 6))

    ax.barh(
        y=range(len(df_unit)),
        width=df_unit["duration"].values,
        left=mdates.date2num(df_unit["outage_begin_dt (UTC)"].values),
        height=0.6,
        color=colors.values,
        alpha=0.8,
        edgecolor="white",
        linewidth=0.3,
    ) #Commandes suggérés par IA pour faire un graphique en barres horizontales où chaque barre représente un arrêt nucléaire. La position verticale de chaque barre correspond à un arrêt différent, la largeur de la barre correspond à la durée de l'arrêt, et la couleur de la barre correspond au type d'arrêt (planifié ou fortuit).

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.YearLocator()) # On formate l'axe des x pour afficher les dates au format "année-mois" et on place une graduation tous les ans. Cela permet de visualiser clairement la répartition des arrêts dans le temps.
    plt.xticks(rotation=45, ha="right")

    ax.set_yticks([])

    pw = df_unit["nominal capacity (MW)"].median()

    ax.set_title(
        f"{unit_name}  —  {int(pw)} MW  —  {len(df_unit)} arrêts",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.set_xlabel("Date", fontsize=11)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2196F3", label="Arrêt planifié"),
        Patch(facecolor="#F44336", label="Arrêt fortuit"),
    ] # On crée une légende pour expliquer les couleurs utilisées dans le graphique
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    ax.grid(axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150) # Si un chemin de sauvegarde est spécifié lors de l'appel de la fonction, on enregistre le graphique dans ce chemin avec une résolution de 150 dpi. Sinon, on affiche le graphique à l'écran.
        plt.close(fig)
    else:
        plt.show()


def plot_site(df, site_name, year_min=None, year_max=None):
    '''Affiche un graphique des arrêts pour un site'''
    units = sorted([u for u in df["unit_name"].unique() if u.startswith(site_name)]) # On récupère la liste des unités de production (réacteurs) qui appartiennent au site spécifié en filtrant les noms des unités qui commencent par le nom du site. Par exemple, si le site est "GRAVELINES", on récupère tous les réacteurs dont le nom commence par "GRAVELINES" (ex: "GRAVELINES 1", "GRAVELINES 2", etc
    if not units:
        print(f"Aucun réacteur trouvé pour le site '{site_name}'")
        return # Si aucun réacteur n'est trouvé pour le site spécifié, on affiche un message et on quitte la fonction.

    df_site = df[df["unit_name"].isin(units)].copy() # On filtre les données pour ne garder que les arrêts correspondant aux réacteurs du site spécifié
    if year_min:
        df_site = df_site[df_site["outage_begin_dt (UTC)"].dt.year >= year_min]
    if year_max:
        df_site = df_site[df_site["outage_begin_dt (UTC)"].dt.year <= year_max]

    df_site["duration"] = (
        df_site["outage_end_dt (UTC)"] - df_site["outage_begin_dt (UTC)"]
    ).dt.total_seconds() / 86400 #Même chose que dans l'autre fonction

    colors = df_site["outage_type"].map({
        "planned":    "#2196F3",
        "fortuitous": "#F44336",
    }).fillna("#9E9E9E") # Même chose que dans l'autre fonction

    unit_to_y = {u: i for i, u in enumerate(units)}
    df_site["y"] = df_site["unit_name"].map(unit_to_y)

    _, ax = plt.subplots(figsize=(18, max(4, len(units) * 1.2))) # Commandes suggérés par IA pour un meilleur tracé

    ax.barh(
        y=df_site["y"].values,
        width=df_site["duration"].values,
        left=mdates.date2num(df_site["outage_begin_dt (UTC)"].values),
        height=0.7,
        color=colors.values,
        alpha=0.8,
        edgecolor="white",
        linewidth=0.3,
    )

    ax.set_yticks(range(len(units)))
    ax.set_yticklabels(units, fontsize=10)
    ax.invert_yaxis()

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45, ha="right") # Même chose que dans l'autre fonction

    ax.set_title(
        f"Site {site_name}  —  {len(units)} réacteurs  —  {len(df_site)} arrêts",
        fontsize=14, fontweight="bold", pad=15
    ) 

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2196F3", label="Arrêt planifié"),
        Patch(facecolor="#F44336", label="Arrêt fortuit"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10) # Même chose que dans l'autre fonction


    ax.grid(axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.show()


def plot_all_centrales(df, year_min=None, year_max=None):
    '''Affiche un graphique pour chaque centrale'''
    units = sorted(df["unit_name"].dropna().unique()) # On récupère la liste de tous les réacteurs disponibles dans les données, en supprimant les valeurs manquantes (NaN) et en triant les noms par ordre alphabétique. Cette liste nous servira à générer un graphique pour chaque réacteur.
    os.makedirs(PLOTS_DIR, exist_ok=True)

    print(f"\n>> Generation de {len(units)} graphes")
    for i, unit_name in enumerate(units, start=1):
        file_name = unit_name.replace("/", "-").replace(" ", "_") + ".png"
        save_path = os.path.join(PLOTS_DIR, file_name)
        print(f"  {i}/{len(units)} {unit_name}")
        plot_centrale(df, unit_name, year_min, year_max, save_path=save_path) # On génère un graphique pour chaque réacteur en appelant la fonction plot_centrale avec le nom du réacteur et les années minimum et maximum si elles sont spécifiées. Chaque graphique est sauvegardé dans le dossier PLOTS_DIR avec un nom de fichier basé sur le nom du réacteur (ex: "GRAVELINES_1.png"). On affiche également une progression dans la console pour suivre l'avancement de la génération des graphiques.

    print(f"\nGraphes sauvegardes dans : {PLOTS_DIR}")


def main():
    '''Point d'entrée du script. Il parse les arguments de la ligne de commande pour déterminer quel graphique afficher (par réacteur, par site, ou tous les réacteurs), puis charge les données et appelle la fonction de tracé appropriée en fonction des arguments fournis. Si aucun argument n'est fourni, il affiche les options disponibles et un exemple d'utilisation.'''
    parser = argparse.ArgumentParser(
        description="Visualisation des arrêts nucléaires par réacteur ou par site"
    )
    parser.add_argument("--centrale", type=str, help="Nom du réacteur (ex: 'GRAVELINES 1')")
    parser.add_argument("--site", type=str, help="Nom du site (ex: 'GRAVELINES')")
    parser.add_argument("--all", action="store_true", help="Faire un graphe pour chaque réacteur")
    parser.add_argument("--list", action="store_true", help="Lister tous les réacteurs et sites")
    parser.add_argument("--annee-min", type=int, help="Année minimum (ex: 2020)")
    parser.add_argument("--annee-max", type=int, help="Année maximum (ex: 2025)")

    args = parser.parse_args() 

    print("Chargement des données...")
    df = load_data()

    if args.list:
        list_centrales(df)
        return

    if args.all:
        plot_all_centrales(df, args.annee_min, args.annee_max) # Si l'argument --all est fourni, on génère un graphique pour chaque réacteur en appelant la fonction plot_all_centrales avec les années minimum et maximum si elles sont spécifiées. Chaque graphique est sauvegardé dans le dossier PLOTS_DIR.
    elif args.centrale:
        plot_centrale(df, args.centrale, args.annee_min, args.annee_max) # Si l'argument --centrale est fourni avec le nom d'un réacteur, on génère un graphique pour ce réacteur en appelant la fonction plot_centrale avec le nom du réacteur et les années minimum et maximum si elles sont spécifiées. Le graphique est affiché à l'écran.
    elif args.site:
        plot_site(df, args.site, args.annee_min, args.annee_max) # Si l'argument --site est fourni avec le nom d'un site, on génère un graphique pour ce site en appelant la fonction plot_site avec le nom du site et les années minimum et maximum si elles sont spécifiées. Le graphique est affiché à l'écran.
    else:
        # Si rien n'est donné, on affiche juste les options
        print("\nOptions :")
        print("  --list                    Voir tous les réacteurs")
        print("  --all                     Sauvegarder un graphe par réacteur")
        print('  --centrale "GRAVELINES 1" Voir un réacteur')
        print("  --site GRAVELINES         Voir tout un site")
        print("  --annee-min 2020          Filtrer depuis 2020")
        print()
        print("Exemple :")
        print('  python3 scripts/outages/main_incremental_programs.py --site GRAVELINES --annee-min 2020')


if __name__ == "__main__":
    main()
