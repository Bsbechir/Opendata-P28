# petit script pour regarder les arrets par reacteur ou par site
# normalement c'est surtout utile au groupe B

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import os
import sys

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH   = os.path.join(BASE_DIR, "output", "indisponibilites_nucleaire_final.csv")
PLOTS_DIR  = os.path.join(BASE_DIR, "output", "plots", "centrales")


def load_data():
    if not os.path.exists(CSV_PATH):
        print(f"ERREUR : CSV non trouvé : {CSV_PATH}")
        print("Lancez d'abord : python3 scripts/outages/generate_csv_final.py")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH, sep=";", low_memory=False)
    df["outage_begin_dt (UTC)"] = pd.to_datetime(df["outage_begin_dt (UTC)"], utc=True)
    df["outage_end_dt (UTC)"]   = pd.to_datetime(df["outage_end_dt (UTC)"], utc=True)
    return df


def list_centrales(df):
    units = sorted(df["unit_name"].unique())

    sites = sorted(set(u.rsplit(" ", 1)[0] for u in units if " " in u))

    print(f"\n>> {len(units)} réacteurs disponibles")
    for u in units:
        count = len(df[df["unit_name"] == u])
        print(f"  {u:<25} ({count} événements)")

    print(f"\n>> {len(sites)} sites disponibles")
    for s in sites:
        n = len([u for u in units if u.startswith(s)])
        print(f"  {s:<25} ({n} réacteurs)")


def plot_centrale(df, unit_name, year_min=None, year_max=None, save_path=None):
    df_unit = df[df["unit_name"] == unit_name].copy()

    if len(df_unit) == 0:
        print(f"Aucune donnée pour '{unit_name}'")
        return

    if year_min:
        df_unit = df_unit[df_unit["outage_begin_dt (UTC)"].dt.year >= year_min]
    if year_max:
        df_unit = df_unit[df_unit["outage_begin_dt (UTC)"].dt.year <= year_max]

    df_unit["duration"] = (
        df_unit["outage_end_dt (UTC)"] - df_unit["outage_begin_dt (UTC)"]
    ).dt.total_seconds() / 86400  # en jours

    colors = df_unit["outage_type"].map({
        "planned":    "#2196F3",   # bleu
        "fortuitous": "#F44336",   # rouge
    }).fillna("#9E9E9E")           # gris si inconnu

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
    )

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
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
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    ax.grid(axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_site(df, site_name, year_min=None, year_max=None):
    units = sorted([u for u in df["unit_name"].unique() if u.startswith(site_name)])

    if not units:
        print(f"Aucun réacteur trouvé pour le site '{site_name}'")
        return

    df_site = df[df["unit_name"].isin(units)].copy()

    if year_min:
        df_site = df_site[df_site["outage_begin_dt (UTC)"].dt.year >= year_min]
    if year_max:
        df_site = df_site[df_site["outage_begin_dt (UTC)"].dt.year <= year_max]

    df_site["duration"] = (
        df_site["outage_end_dt (UTC)"] - df_site["outage_begin_dt (UTC)"]
    ).dt.total_seconds() / 86400

    colors = df_site["outage_type"].map({
        "planned":    "#2196F3",
        "fortuitous": "#F44336",
    }).fillna("#9E9E9E")

    unit_to_y = {u: i for i, u in enumerate(units)}
    df_site["y"] = df_site["unit_name"].map(unit_to_y)

    _, ax = plt.subplots(figsize=(18, max(4, len(units) * 1.2)))

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
    plt.xticks(rotation=45, ha="right")

    ax.set_title(
        f"Site {site_name}  —  {len(units)} réacteurs  —  {len(df_site)} arrêts",
        fontsize=14, fontweight="bold", pad=15
    )

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2196F3", label="Arrêt planifié"),
        Patch(facecolor="#F44336", label="Arrêt fortuit"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    ax.grid(axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.show()


def plot_all_centrales(df, year_min=None, year_max=None):
    units = sorted(df["unit_name"].dropna().unique())
    os.makedirs(PLOTS_DIR, exist_ok=True)

    print(f"\n>> Generation de {len(units)} graphes")
    for i, unit_name in enumerate(units, start=1):
        file_name = unit_name.replace("/", "-").replace(" ", "_") + ".png"
        save_path = os.path.join(PLOTS_DIR, file_name)
        print(f"  {i}/{len(units)} {unit_name}")
        plot_centrale(df, unit_name, year_min, year_max, save_path=save_path)

    print(f"\nGraphes sauvegardes dans : {PLOTS_DIR}")


def main():
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
        plot_all_centrales(df, args.annee_min, args.annee_max)
    elif args.centrale:
        plot_centrale(df, args.centrale, args.annee_min, args.annee_max)
    elif args.site:
        plot_site(df, args.site, args.annee_min, args.annee_max)
    else:
        # si rien n'est donne, on affiche juste les options
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
