# studer-next3-ha

Réponds toujours en français.

## Contrôle de sécurité avant déploiement (Sanitize)

Avant tout déploiement (publication d'une version : tag, release GitHub, HACS) et avant toute fusion dans `main` :

1. Lance `uv run --directory "$HOME/Developer/Sanitize platforms" sanitize check studer-next3-ha`.
2. Montre-moi le verdict tel quel.
3. S'il est rouge (⛔ : failles P0 ou P1 ouvertes), ne déploie pas et ne fusionne pas : explique ce qui bloque et demande-moi comment procéder. Les corrections attendues : `uv run --directory "$HOME/Developer/Sanitize platforms" sanitize prompt studer-next3-ha`.
4. Si la commande échoue ou que Sanitize est introuvable, dis-le-moi : ne passe jamais outre de toi-même (pas de `SANITIZE_SKIP=1` sans mon accord explicite).
