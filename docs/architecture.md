# Architecture — jira-automation

Overview
- CLI orchestrator: `jira-for-pci.py` parse les arguments, initialise le client Jira, construit l’arbre LSD et déclenche les actions.
- Domain layer: `lsd.models` (dataclasses) représente les issues LVL2/PCI et la logique utilitaire (ex: fermé ou non).
- Mapping: `lsd.mappers` convertit un `jira.Issue` en modèles de domaine sans appels réseau.
- Tree building: `lsd.tree_builder` construit une arborescence `nutree.Tree` LVL2 → PCI Epic → Tasks/Stories.
- Services (use-cases): `lsd.services` implémente les actions (propagation de labels/priorité, orphelins, agrégation de points).
- Adapters: `adapter.jira_repo.JiraRepository` implémente `adapter.ports.Repository` pour isoler les requêtes JQL et mutations.
- Presentation: `lsd.presenter` fournit l’affichage ASCII et un rendu graphique optionnel (Graphviz).
- Utilities: `lsd.logging_utils` (logging), `lsd.labels` (format des labels), `lsd.status` (statuts fermés + helper JQL).

Data Flow
1. CLI reçoit l’entrée (année, trimestre, squad, action).
2. Construction de l’arbre: requêtes JQL via `JiraRepository`, mapping vers domain, assemblage via `tree_builder`.
3. Affichage ASCII (par défaut) et/ou rendu graphique optionnel.
4. Exécution d’une action via `lsd.services` (écritures Jira uniquement via l’adapter).

Design Choices
- Séparation nette domaine/adapters: logique testable sans réseau, appels Jira centralisés.
- Idempotence côté adapter pour les mutations (ex: `add_label`).
- Centralisation des constantes/formatage (statuts fermés, labels sprint).

Extensibility
- Ajouter un nouveau filtre de squad en étendant les requêtes dans `adapter/jira_repo.py`.
- Ajouter une action en l’implémentant dans `lsd.services` (en s’appuyant sur `Repository`).

Security
- Ne jamais journaliser de secrets.
- Utiliser un token à privilège minimal.
