# models.py
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    uri = os.getenv("DATABASE_URL")
    if not uri:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        instance_dir = os.path.join(base_dir, "instance")
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, "app.db")
        uri = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = app.config.get("SECRET_KEY", "tajny_klic_pro_session")

    db.init_app(app)
    with app.app_context():
        db.create_all()

class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class LikertAnswer(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    category        = db.Column(db.String(80), nullable=False)
    statement_index = db.Column(db.Integer, nullable=False)
    score           = db.Column(db.Integer, nullable=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

class DuelAnswer(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    option_a  = db.Column(db.String(80), nullable=False)
    option_b  = db.Column(db.String(80), nullable=False)
    chosen    = db.Column(db.String(80), nullable=False)
    created_at= db.Column(db.DateTime, default=datetime.utcnow)

class ResultProfile(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    rank      = db.Column(db.Integer, nullable=False)
    category  = db.Column(db.String(80), nullable=False)
    score     = db.Column(db.Float, nullable=True)  # kombinace (duely + likert)
    created_at= db.Column(db.DateTime, default=datetime.utcnow)
