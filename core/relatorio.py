"""Exportação dos resultados para Excel e Markdown."""
from __future__ import annotations

import io

import pandas as pd

COLUNAS = [
    "Livro", "Elegível", "Método", "Motivo", "Nº Capítulos",
    "Fichado?", "Fichamento correspondente", "Similaridade", "Formato", "Arquivo",
]


def para_dataframe(linhas: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(linhas)
    for c in COLUNAS:
        if c not in df.columns:
            df[c] = None
    return df[COLUNAS]


def exportar_excel(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pesquisa")
    return buffer.getvalue()


def exportar_markdown(df: pd.DataFrame, detalhes_capitulos: dict[str, list]) -> str:
    linhas = ["# Organização da pesquisa (projeto RAIP)\n"]
    elegiveis = df[df["Elegível"] == "Sim"]
    nao_fichados = elegiveis[elegiveis["Fichado?"] == "Não"]

    linhas.append(f"- Total de livros: **{len(df)}**")
    linhas.append(f"- Elegíveis: **{len(elegiveis)}**")
    linhas.append(f"- Elegíveis ainda **não fichados**: **{len(nao_fichados)}**\n")

    if len(nao_fichados):
        linhas.append("## ⚠️ Elegíveis ainda NÃO fichados\n")
        for _, r in nao_fichados.iterrows():
            linhas.append(f"- {r['Livro']} ({r['Nº Capítulos']} capítulos)")
        linhas.append("")

    linhas.append("## Todos os livros elegíveis e capítulos\n")
    for _, r in elegiveis.iterrows():
        marca = "✅" if r["Fichado?"] == "Sim" else "❌"
        linhas.append(f"### {marca} {r['Livro']}")
        linhas.append(f"*Fichado:* {r['Fichado?']} — *Motivo:* {r['Motivo']}")
        caps = detalhes_capitulos.get(r["Arquivo"], [])
        if caps:
            for c in caps:
                linhas.append(f"{'  ' * (c['nivel'] - 1)}- {c['titulo']}")
        else:
            linhas.append("- (sem capítulos detectados por estilos de título)")
        linhas.append("")
    return "\n".join(linhas)
