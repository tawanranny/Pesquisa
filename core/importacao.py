"""
Importação da lista de títulos já mapeados do RAIP (ex.: os 63 do corpus).

Tolerante a formatos: aceita uma TABELA markdown, colunas separadas por '|',
TAB ou ';', ou simplesmente um TÍTULO por linha. Reconhece colunas de
título/autor/ano/idioma/pasta/grau/fichamento/capítulo pelo cabeçalho.

Saídas:
  • registros no formato do catálogo (Seção 8);
  • lista de títulos para o modo "livros eleitos".
"""
from __future__ import annotations

import re
import unicodedata

from . import catalogo as cat


def _norm(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", txt or "")
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt.strip().lower()


# Sinônimos de cabeçalho -> coluna do catálogo.
_MAPA_CABECALHO = {
    "Referência bibliográfica completa": (
        "titulo", "título", "obra", "referencia", "referência", "livro", "title"),
    "Autor(es)": ("autor", "autores", "author"),
    "Ano de publicação": ("ano", "year"),
    "Idioma original": ("idioma", "lingua", "língua", "language"),
    "Pasta(s) temática(s)": ("pasta", "pastas", "tematica", "temática", "tema"),
    "Grau de incorporação": ("grau", "incorporacao", "incorporação", "relevancia",
                             "relevância"),
    "Fichamento disponível?": ("fichamento", "fichado", "ficha"),
    "Capítulo(s) de incidência": ("capitulo", "capítulo", "capitulos", "capítulos",
                                  "incidencia", "incidência"),
}


def _coluna_de(cabecalho: str) -> str | None:
    n = _norm(cabecalho)
    for coluna, termos in _MAPA_CABECALHO.items():
        if any(t in n for t in termos):
            return coluna
    return None


def _normalizar_grau(valor: str) -> str:
    n = _norm(valor)
    if not n:
        return ""
    if n.startswith("1") or "alta" in n or "primeiro" in n:
        return "1.º grau"
    if n.startswith("2") or "media" in n or "média" in n or "segundo" in n:
        return "2.º grau"
    if n.startswith("3") or "baixa" in n or "terceiro" in n or "defer" in n:
        return "3.º grau"
    if "irrelev" in n:
        return "Irrelevante"
    if "potenc" in n:
        return "Potencial"
    return valor.strip()


def _dividir(linha: str) -> list[str]:
    """Quebra uma linha em células, detectando o separador."""
    bruto = linha.strip().strip("|")
    for sep in ("|", "\t", ";"):
        if sep in bruto:
            return [c.strip() for c in bruto.split(sep)]
    return [bruto.strip()]


def _eh_separador_md(linha: str) -> bool:
    """Linha de separação de tabela markdown, ex.: |---|:--:|---|."""
    return bool(re.fullmatch(r"[\s|:\-]+", linha)) and "-" in linha


def importar_lista(texto: str) -> tuple[list[dict], list[str]]:
    """Retorna (registros_catalogo, titulos). Cada registro segue cat.COLUNAS."""
    linhas = [l for l in (texto or "").splitlines() if l.strip()]
    linhas = [l for l in linhas if not _eh_separador_md(l)]
    if not linhas:
        return [], []

    # Detecta cabeçalho: a 1.ª linha mapeia para >= 2 colunas conhecidas?
    primeira = _dividir(linhas[0])
    mapeadas = [(_coluna_de(c), i) for i, c in enumerate(primeira)]
    tem_cabecalho = sum(1 for c, _ in mapeadas if c) >= 2

    if tem_cabecalho:
        col_por_idx = {i: c for c, i in mapeadas if c}
        corpo = linhas[1:]
    else:
        # Sem cabeçalho: 1.ª célula = título; demais ignoradas.
        col_por_idx = {0: "Referência bibliográfica completa"}
        corpo = linhas

    registros, titulos = [], []
    for linha in corpo:
        celulas = _dividir(linha)
        reg = {col: "" for col in cat.COLUNAS}
        for idx, valor in enumerate(celulas):
            coluna = col_por_idx.get(idx)
            if not coluna or not valor:
                continue
            if coluna == "Grau de incorporação":
                valor = _normalizar_grau(valor)
            reg[coluna] = valor
        titulo = reg.get("Referência bibliográfica completa", "").strip()
        if not titulo:
            continue
        registros.append(reg)
        titulos.append(titulo)
    return registros, titulos
