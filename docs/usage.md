# Usage — Quick Guide

Prerequisites
- Python 3.10+
- Env vars: `JIRA_TOKEN` (obligatoire), `JIRA_SERVER` (optionnel, défaut: https://jira.ovhcloud.tools)
- Dépendance optionnelle: `graphviz` (uniquement si vous rendez un graphe image)

Installation
- Créez un venv puis installez:
  - pip install -r requirements.txt
  - pip install graphviz  # seulement si vous utilisez le rendu graphique

Commandes courantes
- Afficher l’arbre LSD pour FY26 Q1 (squad Network):
  - python jira-for-pci.py 26 1 Network
- Afficher en ignorant les issues PCI fermées:
  - python jira-for-pci.py 26 1 Network --skip-closed
- Propager le label de quarter (FY26Q1) sur les issues PCI non fermées:
  - python jira-for-pci.py 26 1 Network --action set-quarter
- Propager la priorité des Epics vers leurs Stories/Tasks:
  - python jira-for-pci.py 26 1 Network --action set-prio
- Lister les orphelins (labellisés FY26Q1 mais non présents dans l’arbre):
  - python jira-for-pci.py 26 1 Network --action find-orphans
- Agréger les story points des enfants d’un Epic PCI et l’écrire sur l’Epic:
  - python jira-for-pci.py 26 1 Network --action aggregate-points --pci-epic PCI-12345

Notes
- `--skip-closed` désactive les actions d’écriture; utile pour l’inspection.
- Le rendu image du graphe est disponible via `lsd.presenter.render_graph` si `graphviz` est installé.

Troubleshooting
- 401 / 403: vérifier `JIRA_TOKEN` et les permissions du compte.
- 429: gérer le rate limit (relancer plus tard, backoff côté appelant si nécessaire).
