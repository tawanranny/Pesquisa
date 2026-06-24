"""
Cruzamento entre livros e fichamentos.

Descobre, para cada livro elegível, se já existe um fichamento correspondente,
usando correspondência aproximada de nomes/títulos (tolerante a variações).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz, process

from .leitura import listar_livros

# Termos comuns em nomes de fichamento que atrapalham o casamento.
_RUIDO = [
    "fichamento", "ficha", "resumo", "resenha", "notas", "anotacoes",
    "anotações", "leitura", "estudo",
]


def _normalizar(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    txt = txt.lower()
    for r in _RUIDO:
        txt = txt.replace(r, " ")
    txt = re.sub(r"[^a-z0-9]+", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


@dataclass
class Fichamento:
    caminho: Path
    nome_arquivo: str
    chave: str  # nome normalizado para casamento


def carregar_fichamentos(pasta: Path) -> list[Fichamento]:
    fichas: list[Fichamento] = []
    for caminho in listar_livros(pasta):
        fichas.append(
            Fichamento(
                caminho=caminho,
                nome_arquivo=caminho.name,
                chave=_normalizar(caminho.stem),
            )
        )
    return fichas


@dataclass
class StatusFichamento:
    fichado: bool
    fichamento_correspondente: str | None
    similaridade: int  # 0-100


def encontrar_fichamento(
    titulo_livro: str,
    nome_arquivo_livro: str,
    fichamentos: list[Fichamento],
    limiar: int = 80,
) -> StatusFichamento:
    """Procura o melhor fichamento para um livro. Compara por título e por
    nome de arquivo, ficando com a maior similaridade."""
    if not fichamentos:
        return StatusFichamento(False, None, 0)

    chaves = {f.chave: f for f in fichamentos}
    melhor_sim = 0
    melhor_ficha: Fichamento | None = None

    for alvo in {_normalizar(titulo_livro), _normalizar(Path(nome_arquivo_livro).stem)}:
        if not alvo:
            continue
        achado = process.extractOne(
            alvo, list(chaves.keys()), scorer=fuzz.token_sort_ratio
        )
        if achado and achado[1] > melhor_sim:
            melhor_sim = int(achado[1])
            melhor_ficha = chaves[achado[0]]

    if melhor_ficha and melhor_sim >= limiar:
        return StatusFichamento(True, melhor_ficha.nome_arquivo, melhor_sim)
    return StatusFichamento(False, None, melhor_sim)
