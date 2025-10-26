from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class OrdemProducao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Integer, nullable=False)
    produzidas = db.Column(db.Integer, default=0)
    finalizada = db.Column(db.Boolean, default=False)
    data_finalizacao = db.Column(db.String(20), nullable=True)
