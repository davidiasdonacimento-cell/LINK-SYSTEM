import os
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-before-deploy")
db_url = os.environ.get("DATABASE_URL", "sqlite:///link_system.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.String(300), nullable=False)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    icon = db.Column(db.String(40), nullable=False, default="link")
    position = db.Column(db.Integer, nullable=False, default=0)

def setting(key, default):
    item = Setting.query.filter_by(key=key).first()
    return item.value if item else default

def owner_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("owner"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def valid_url(value):
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

@app.get("/")
def index():
    links = Link.query.order_by(Link.position, Link.id).all()
    return render_template("index.html", links=links,
        profile_title=setting("profile_title", "LINK SYSTEM"),
        profile_description=setting("profile_description", "Todos os meus sites em um só lugar"))

@app.route("/admin", methods=["GET", "POST"])
def login():
    if session.get("owner"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = os.environ.get("ADMIN_USERNAME", "sixseven")
        password = os.environ.get("ADMIN_PASSWORD", "")
        if password and request.form.get("username", "").strip() == username and check_password_hash(generate_password_hash(password), request.form.get("password", "")):
            session.clear()
            session["owner"] = True
            return redirect(url_for("dashboard"))
        flash("Login inválido ou senha administrativa ainda não configurada.", "error")
    return render_template("login.html", owner_name=os.environ.get("ADMIN_USERNAME", "sixseven"))

@app.get("/admin/painel")
@owner_required
def dashboard():
    return render_template("dashboard.html", links=Link.query.order_by(Link.position, Link.id).all(),
        profile_title=setting("profile_title", "LINK SYSTEM"),
        profile_description=setting("profile_description", "Todos os meus sites em um só lugar"))

@app.post("/admin/perfil")
@owner_required
def save_profile():
    for key, field, default in [
        ("profile_title", "profile_title", "LINK SYSTEM"),
        ("profile_description", "profile_description", "Todos os meus sites em um só lugar")
    ]:
        value = request.form.get(field, default).strip()[:300]
        item = Setting.query.filter_by(key=key).first()
        if item:
            item.value = value
        else:
            db.session.add(Setting(key=key, value=value))
    db.session.commit()
    flash("Perfil atualizado globalmente.", "success")
    return redirect(url_for("dashboard"))

@app.post("/admin/links/adicionar")
@owner_required
def add_link():
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()
    icon = request.form.get("icon", "link").strip()[:40]
    if not title or len(title) > 100 or not valid_url(url):
        flash("Informe um nome e uma URL válida começando com https:// ou http://.", "error")
    else:
        db.session.add(Link(title=title, url=url, icon=icon, position=(db.session.query(db.func.max(Link.position)).scalar() or 0) + 1))
        db.session.commit()
        flash("Link adicionado.", "success")
    return redirect(url_for("dashboard"))

@app.post("/admin/links/<int:link_id>/editar")
@owner_required
def edit_link(link_id):
    item = db.get_or_404(Link, link_id)
    title, url = request.form.get("title", "").strip(), request.form.get("url", "").strip()
    if title and len(title) <= 100 and valid_url(url):
        item.title, item.url = title, url
        item.icon = request.form.get("icon", "link").strip()[:40]
        db.session.commit()
        flash("Link atualizado.", "success")
    else:
        flash("Nome ou URL inválida.", "error")
    return redirect(url_for("dashboard"))

@app.post("/admin/links/<int:link_id>/excluir")
@owner_required
def delete_link(link_id):
    db.session.delete(db.get_or_404(Link, link_id))
    db.session.commit()
    flash("Link removido.", "success")
    return redirect(url_for("dashboard"))

@app.post("/admin/sair")
@owner_required
def logout():
    session.clear()
    return redirect(url_for("index"))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
