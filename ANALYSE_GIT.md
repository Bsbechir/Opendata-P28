# Analyse critique du dépôt Git — Opendata-P28

## État actuel

| Métrique | Valeur |
|---|---|
| Branche de travail | `groupe-a-data` |
| Commits Groupe A | ~17 |
| Contributeurs | Bechir (majorité des commits), Valentin (3 commits) |
| Taille repo | 80 Mo (dont 31 Mo dans `.git/`) |
| Taille CSV trackés | 49 Mo (avant nettoyage salve 1) |

## Points positifs

- **Commits clairs** : les messages décrivent bien ce qui a été fait (`"CSV final nettoyé : 71726 lignes, types harmonisés, dates UTC"`)
- **Progression logique** : les commits suivent les phases du projet (installation → données → fusion → nettoyage)
- **Branche séparée** : le travail est isolé sur `groupe-a-data`, le `master` (code CRE) reste intact
- **3 sources fusionnées** : le CSV final est complet (RTE xlsx + RTE API + ENTSO-E)

## Problèmes identifiés et corrigés

| Problème | Gravité | Statut |
|---|---|---|
| Secrets API RTE en dur dans le code | Critique | Corrigé (salve 1) |
| CSV de 49 Mo trackés dans git | Moyen | Corrigé (salve 1) |
| Fichier pickle orphelin (`df.pckl`) | Moyen | Corrigé (salve 1) |
| Chemin Windows hardcodé | Moyen | Corrigé (salve 1) |
| `.gitignore` incomplet | Moyen | Corrigé (salve 1) |
| README = celui de la CRE | Moyen | Corrigé (salve 2) |
| Modules CRE inutilisés | Mineur | Corrigé (salve 2) |
| `requirements.txt` = dump 150 packages | Mineur | Corrigé (salve 2) |

## Problèmes restants

| Problème | Gravité | Action |
|---|---|---|
| Historique git contient encore les secrets | Critique | Révoquer les credentials RTE (action manuelle) |
| Historique git contient 93 Mo de CSV supprimés | Moyen | `git filter-branch` ou BFG si besoin de réduire la taille |
| Déséquilibre contributions (Bechir ~14 commits, Valentin ~3) | Info | Normal si répartition convenue |
| Pas de tags/releases | Mineur | Ajouter un tag `v1.0` au moment de la livraison |
| Pas de CI/CD | Mineur | Hors scope du projet |
| Pas de tests unitaires | Mineur | Hors scope du projet |

## Recommandations pour la soutenance

1. **Révoquer les anciens credentials RTE** — c'est la seule action urgente restante
2. **Ajouter un tag** `v1.0-livraison` sur le commit de livraison
3. **Mentionner dans la soutenance** : la migration des secrets, le nettoyage du repo, l'analyse croisée des sources
4. **Le `main_incremental_programs.py`** peut être livré au Groupe B séparément (via un PR ou un fichier zip)
