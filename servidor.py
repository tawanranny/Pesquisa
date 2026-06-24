"""
Organizador de Pesquisa — Projeto RAIP (interface web local, Flask).

Interface gráfica própria (HTML/CSS), rodando no seu computador. Lê a pasta do
OneDrive sincronizada, examina cada livro um a um, cataloga somente os
adicionados a partir da data de corte (padrão: 2.º semestre de 2025) e
classifica por grau de incorporação e pastas temáticas (projeto RAIP).

Como rodar:
    pip install -r requirements.txt
    python servidor.py
    # abre automaticamente em http://127.0.0.1:5000
"""
from __future__ import annotations

import os
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file

from core import catalogo as cat
from core.analise import analisar
from core.importacao import importar_lista
from core.relatorio import exportar_excel, exportar_markdown, para_dataframe

load_dotenv()

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")

CAMINHO_CONFIG = Path("config/criterios_raip.yaml")
CAMINHO_ELEITOS = Path("config/livros_eleitos.txt")

# Estado da última análise (para exportações e catálogo).
ESTADO: dict = {"linhas": [], "detalhes": {}}


def carregar_config() -> dict:
    cfg = {}
    if CAMINHO_CONFIG.exists():
        cfg = yaml.safe_load(CAMINHO_CONFIG.read_text(encoding="utf-8")) or {}
    if not cfg.get("arquivo_livros_eleitos") and CAMINHO_ELEITOS.exists():
        cfg["arquivo_livros_eleitos"] = str(CAMINHO_ELEITOS)
    return cfg


def criar_cliente_ia(usar_ia: bool):
    if not usar_ia:
        return None
    chave = os.getenv("ANTHROPIC_API_KEY")
    if not chave:
        return None
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=chave)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    cfg = carregar_config()
    modo_eleitos = bool(cfg.get("lista_livros_eleitos") or
                        cfg.get("arquivo_livros_eleitos"))
    return render_template(
        "index.html",
        tem_ia=bool(os.getenv("ANTHROPIC_API_KEY")),
        modo_eleitos=modo_eleitos,
        corte_padrao="2025-07-01",
        escopo=(cfg.get("escopo_pesquisa") or "").strip()[:600],
    )


@app.route("/analisar", methods=["POST"])
def rota_analisar():
    d = request.get_json(force=True)
    pasta_livros = Path(d.get("pasta_livros", "").strip())
    pasta_fichamentos = Path(d.get("pasta_fichamentos", "").strip())
    if not pasta_livros.exists():
        return jsonify({"erro": f"Pasta de livros não encontrada: {pasta_livros}"}), 400

    corte = None
    if d.get("data_corte"):
        try:
            corte = datetime.strptime(d["data_corte"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"erro": "Data de corte inválida (use AAAA-MM-DD)."}), 400

    cfg = carregar_config()
    cliente_ia = criar_cliente_ia(bool(d.get("usar_ia")))
    try:
        linhas, detalhes = analisar(
            pasta_livros, pasta_fichamentos, cfg,
            cliente_ia=cliente_ia,
            limiar_fichamento=int(d.get("limiar_fichamento", 80)),
            usar_cache=bool(d.get("usar_cache", True)),
            data_corte=corte,
        )
    except Exception as e:
        return jsonify({"erro": f"Falha na análise: {e}"}), 500

    ESTADO["linhas"] = linhas
    ESTADO["detalhes"] = detalhes

    elegiveis = [l for l in linhas if l.get("Elegível") == "Sim"]
    falta = [l for l in elegiveis if l.get("Fichado?") == "Não"]
    graus: dict[str, int] = {}
    for l in linhas:
        graus[l.get("Grau", "")] = graus.get(l.get("Grau", ""), 0) + 1

    return jsonify({
        "linhas": linhas,
        "detalhes": detalhes,
        "resumo": {
            "total": len(linhas),
            "elegiveis": len(elegiveis),
            "fichados": sum(1 for l in elegiveis if l.get("Fichado?") == "Sim"),
            "falta_fichar": len(falta),
            "graus": graus,
        },
    })


@app.route("/catalogo/dados", methods=["POST"])
def rota_catalogo_dados():
    d = request.get_json(force=True)
    caminho = Path(d.get("caminho", "catalogo_raip.csv"))
    auto = cat.construir_catalogo(ESTADO["linhas"])
    df = cat.mesclar(auto, cat.carregar(caminho))
    return jsonify({
        "colunas": cat.COLUNAS,
        "registros": df.to_dict(orient="records"),
        "opcoes": {
            "Idioma original": cat.IDIOMAS,
            "Grau de incorporação": cat.GRAUS,
            "Fichamento disponível?": cat.FICHAMENTO,
        },
        "auto": sorted(cat.CAMPOS_AUTO),
    })


@app.route("/catalogo/salvar", methods=["POST"])
def rota_catalogo_salvar():
    d = request.get_json(force=True)
    caminho = Path(d.get("caminho", "catalogo_raip.csv"))
    registros = d.get("registros", [])
    df = pd.DataFrame(registros, columns=cat.COLUNAS)
    try:
        cat.salvar(df, caminho)
    except Exception as e:
        return jsonify({"erro": f"Não foi possível salvar: {e}"}), 500
    return jsonify({"ok": True, "caminho": str(caminho), "n": len(df)})


@app.route("/importar", methods=["POST"])
def rota_importar():
    d = request.get_json(force=True)
    registros, titulos = importar_lista(d.get("texto", ""))
    if d.get("salvar_eleitos"):
        CAMINHO_ELEITOS.parent.mkdir(parents=True, exist_ok=True)
        CAMINHO_ELEITOS.write_text("\n".join(titulos), encoding="utf-8")
    return jsonify({"n": len(titulos), "titulos": titulos[:50],
                    "salvo": bool(d.get("salvar_eleitos"))})


@app.route("/exportar/<fmt>")
def rota_exportar(fmt: str):
    if not ESTADO["linhas"]:
        return "Nenhuma análise ainda.", 400
    df = para_dataframe(ESTADO["linhas"])
    if fmt == "excel":
        dados = exportar_excel(df)
        return send_file(
            _buffer(dados), as_attachment=True, download_name="pesquisa_raip.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if fmt == "md":
        dados = exportar_markdown(df, ESTADO["detalhes"]).encode("utf-8")
        return send_file(_buffer(dados), as_attachment=True,
                         download_name="pesquisa_raip.md", mimetype="text/markdown")
    return "Formato desconhecido.", 404


def _buffer(dados: bytes):
    import io
    return io.BytesIO(dados)


def _abrir_navegador():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    if os.getenv("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.2, _abrir_navegador).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
