from flask import Flask, render_template_string, request, redirect, url_for, send_file
from datetime import datetime
import csv
from models import db, OrdemProducao

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///production.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

META_PEÇAS_POR_HORA = 8
HORAS_TRABALHO = list(range(8, 18))
META_DIARIA = META_PEÇAS_POR_HORA * len(HORAS_TRABALHO)

HTML_TEMPLATE = '''
<!doctype html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <title>Controle de Produção</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: Arial; max-width: 900px; margin: 20px auto; }
    .ordem { border: 1px solid #ccc; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .finalizada { background-color: #d4edda; }
    button { padding: 10px 15px; margin: 5px; font-size: 16px; }
    .resumo { background-color: #f0f0f0; padding: 15px; border-radius: 5px; }
    .barra-progresso { width: 100%; background-color: #ddd; border-radius: 5px; overflow: hidden; height: 25px; margin-top: 10px; }
    .progresso { height: 100%; text-align: center; color: white; font-weight: bold; line-height: 25px; }
  </style>
</head>
<body>
  <h1>🏭 Controle de Produção</h1>

  <div class='resumo'>
    <strong>Resumo do Dia ({{ hoje }}):</strong><br>
    Ordens finalizadas: {{ ordens_finalizadas }}<br>
    Peças produzidas hoje: {{ pecas_produzidas }} / {{ meta_diaria }}
    <div class="barra-progresso">
      <div class="progresso" style="width: {{ progresso }}%; background-color: {{ cor_progresso }};">
        {{ progresso }}%
      </div>
    </div>
  </div>

  <h2>Nova Ordem</h2>
  <form method='post' action='/nova_ordem'>
    Quantidade de peças: <input type='number' name='total' min='1' required>
    <button type='submit'>Adicionar</button>
  </form>

  <h2>Ordens</h2>
  {% for ordem in ordens %}
    <div class='ordem {% if ordem.finalizada %}finalizada{% endif %}'>
      <strong>Ordem {{ ordem.id }}</strong><br>
      Peças: {{ ordem.produzidas }} / {{ ordem.total }}<br>
      {% if not ordem.finalizada %}
        <a href='/adicionar_peca/{{ ordem.id }}'><button>+1 Peça</button></a>
        <a href='/finalizar_ordem/{{ ordem.id }}'><button>Finalizar</button></a>
      {% else %}
        ✅ Finalizada
      {% endif %}
    </div>
  {% endfor %}

  <a href='/gerar_relatorio'><button>Gerar Relatório CSV</button></a>
</body>
</html>
'''

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/")
def index():
    hoje = datetime.today().strftime("%Y-%m-%d")
    ordens = OrdemProducao.query.all()
    ordens_finalizadas = OrdemProducao.query.filter_by(finalizada=True).count()
    pecas_produzidas = sum(o.produzidas for o in ordens)
    progresso = int((pecas_produzidas / META_DIARIA) * 100) if META_DIARIA > 0 else 0
    progresso = min(progresso, 100)
    cor_progresso = "green" if progresso >= 100 else "red"

    return render_template_string(
        HTML_TEMPLATE,
        ordens=ordens,
        hoje=hoje,
        ordens_finalizadas=ordens_finalizadas,
        pecas_produzidas=pecas_produzidas,
        meta_diaria=META_DIARIA,
        progresso=progresso,
        cor_progresso=cor_progresso
    )

@app.route("/nova_ordem", methods=["POST"])
def nova_ordem():
    total = int(request.form["total"])
    ordem = OrdemProducao(total=total)
    db.session.add(ordem)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/adicionar_peca/<int:ordem_id>")
def adicionar_peca(ordem_id):
    ordem = OrdemProducao.query.get(ordem_id)
    if ordem and not ordem.finalizada:
        ordem.produzidas += 1
        if ordem.produzidas >= ordem.total:
            ordem.finalizada = True
            ordem.data_finalizacao = datetime.today().strftime("%Y-%m-%d")
        db.session.commit()
    return redirect(url_for("index"))

@app.route("/finalizar_ordem/<int:ordem_id>")
def finalizar_ordem(ordem_id):
    ordem = OrdemProducao.query.get(ordem_id)
    if ordem:
        ordem.finalizada = True
        ordem.data_finalizacao = datetime.today().strftime("%Y-%m-%d")
        db.session.commit()
    return redirect(url_for("index"))

@app.route("/gerar_relatorio")
def gerar_relatorio():
    hoje = datetime.today().strftime("%Y-%m-%d")
    nome_arquivo = f"relatorio_{hoje}.csv"
    ordens = OrdemProducao.query.filter_by(data_finalizacao=hoje).all()

    with open(nome_arquivo, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "id_ordem", "total_pecas", "produzidas", "finalizada"])
        for o in ordens:
            writer.writerow([o.data_finalizacao, o.id, o.total, o.produzidas, o.finalizada])

    return send_file(nome_arquivo, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
