"""
Catálogo editável do RAIP (Seção 8 do documento operacional).

Cada obra vira um registro com os campos sugeridos. Os campos AUTOMÁTICOS
(grau, pastas, fichamento, título/arquivo) vêm da análise; os demais são
preenchidos por você. As edições são salvas em um arquivo e PRESERVADAS quando
você reanalisa a biblioteca (só completa os campos ainda em branco).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# Vocabulários (Seção 8) -----------------------------------------------------
IDIOMAS = ["", "Português", "Inglês", "Francês", "Alemão", "Espanhol", "Outro"]
GRAUS = ["", "1.º grau", "2.º grau", "3.º grau", "Potencial", "Irrelevante"]
FICHAMENTO = ["", "Sim", "Não", "Em elaboração"]
CAPITULOS = ["Introdução", "Cap. 1", "Cap. 2", "Cap. 3", "Cap. 4", "Cap. 5"]

# Chave de ligação registro <-> arquivo analisado.
CHAVE = "Arquivo"

COLUNAS = [
    CHAVE,
    "Referência bibliográfica completa",
    "Autor(es)",
    "Ano de publicação",
    "Idioma original",
    "Pasta(s) temática(s)",
    "Grau de incorporação",
    "Fichamento disponível?",
    "Capítulo(s) de incidência",
    "Pendência bibliográfica",
    "Localização física",
    "Observações",
]

# Campos preenchidos automaticamente pela análise (os demais são manuais).
CAMPOS_AUTO = {
    "Referência bibliográfica completa",
    "Pasta(s) temática(s)",
    "Grau de incorporação",
    "Fichamento disponível?",
}


def _mapear_grau(grau_interno: str) -> str:
    """Converte o grau interno do motor para o vocabulário da Seção 8."""
    g = (grau_interno or "").lower()
    if g.startswith("1"):
        return "1.º grau"
    if g.startswith("2"):
        return "2.º grau"
    if g.startswith("3"):
        return "3.º grau"
    if "irrelev" in g:
        return "Irrelevante"
    if "duvida" in g or "dúvida" in g:
        return "Potencial"
    return ""  # "(lista RAIP)" e demais ficam em branco para você decidir


def construir_catalogo(linhas: list[dict]) -> pd.DataFrame:
    """Monta o catálogo com os campos automáticos já preenchidos."""
    registros = []
    for r in linhas:
        fich = r.get("Fichado?", "")
        registros.append({
            CHAVE: r.get("Arquivo", ""),
            "Referência bibliográfica completa": r.get("Livro", ""),
            "Autor(es)": "",
            "Ano de publicação": "",
            "Idioma original": "",
            "Pasta(s) temática(s)":
                "" if r.get("Pastas temáticas") in (None, "—") else r.get("Pastas temáticas", ""),
            "Grau de incorporação": _mapear_grau(r.get("Grau", "")),
            "Fichamento disponível?": fich if fich in ("Sim", "Não") else "",
            "Capítulo(s) de incidência": "",
            "Pendência bibliográfica": "",
            "Localização física": "",
            "Observações": "",
        })
    df = pd.DataFrame(registros, columns=COLUNAS)
    return df


def mesclar(auto: pd.DataFrame, salvo: pd.DataFrame | None) -> pd.DataFrame:
    """Sobrepõe os valores salvos (suas edições) por cima do catálogo automático.
    Qualquer campo preenchido no arquivo salvo prevalece; campos em branco
    recebem o valor automático. Assim suas edições nunca são perdidas."""
    if salvo is None or salvo.empty:
        return auto
    salvo = salvo.set_index(CHAVE)
    resultado = auto.copy()
    for i, linha in resultado.iterrows():
        chave = linha[CHAVE]
        if chave in salvo.index:
            for col in COLUNAS:
                if col == CHAVE or col not in salvo.columns:
                    continue
                val = salvo.at[chave, col]
                if pd.notna(val) and str(val).strip():
                    resultado.at[i, col] = val
    return resultado


def carregar(caminho: Path) -> pd.DataFrame | None:
    if not caminho.exists():
        return None
    try:
        df = pd.read_csv(caminho, dtype=str).fillna("")
        for col in COLUNAS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUNAS]
    except Exception:
        return None


def salvar(df: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8")


def para_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
