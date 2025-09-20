# Setup & Configuration

Environment variables
- JIRA_SERVER=https://jira.example.com  (optionnel; défaut: https://jira.ovhcloud.tools)
- JIRA_TOKEN=xxxxxxxx                   (obligatoire)

Example `.env`
```
JIRA_SERVER=https://...
JIRA_TOKEN=...
```
Astuce: utilisez `python-dotenv` en local si vous souhaitez charger automatiquement `.env`.

Install
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Optionnel pour rendu graphique
pip install graphviz
```

Run
```
python jira-for-pci.py 26 1 Network --action set-quarter
```

Security
- Ne pas committer de secrets.
- Utiliser des tokens à privilèges minimaux.

Troubleshooting
- Logs: l’application écrit `./out/logs.txt` (niveau DEBUG) et la console (INFO).
- Auth: vérifier `JIRA_TOKEN`. 401/403 indique souvent un token invalide ou des droits insuffisants.
