# LINK SYSTEM

Perfil público único para reunir vários sites em uma página, com painel administrativo privado.

## Recursos
- Perfil público sem senha.
- Login administrativo com usuário padrão `sixseven`.
- Gerenciamento global do título, descrição e links.
- Interface responsiva em roxo e azul.
- Flask + SQLAlchemy; PostgreSQL via `DATABASE_URL` ou SQLite local.

## Configuração local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="uma-chave-longa-e-aleatoria"
export ADMIN_USERNAME="sixseven"
export ADMIN_PASSWORD="defina-uma-senha-forte"
python main.py
```
Acesse `http://127.0.0.1:5000`. Perfil público: `/`; login do dono: `/admin`.

## Render
Configure no Web Service:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn main:app --bind 0.0.0.0:$PORT`
- Variáveis: `SECRET_KEY` (segredo longo aleatório), `ADMIN_USERNAME=sixseven`, `ADMIN_PASSWORD` (defina como segredo no painel Render), `DATABASE_URL` (PostgreSQL recomendado para persistência).

**Importante:** não coloque a senha no GitHub nem a envie no chat. O serviço precisa de PostgreSQL persistente para manter os links após reinicializações e novos deploys. SQLite é fallback apenas para desenvolvimento local.
