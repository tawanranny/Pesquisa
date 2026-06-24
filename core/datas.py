"""
Datas dos arquivos, para filtrar livros pela data em que foram adicionados.

OneDrive não expõe diretamente "data em que o arquivo foi adicionado à nuvem".
A melhor aproximação local é combinar data de CRIAÇÃO e de MODIFICAÇÃO:
incluímos o livro se QUALQUER uma das duas for igual/posterior ao corte
(equivale a comparar a mais recente das duas com o corte).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


def _criacao(st) -> float:
    """Data de criação. No Windows é st_ctime; em macOS, st_birthtime."""
    return getattr(st, "st_birthtime", None) or st.st_ctime


def data_referencia(caminho: Path) -> datetime:
    """A mais recente entre criação e modificação (critério 'criação OU mod.')."""
    st = Path(caminho).stat()
    return datetime.fromtimestamp(max(_criacao(st), st.st_mtime))


def inicio_segundo_semestre(ano: int) -> datetime:
    """1.º de julho do ano informado (início do 2.º semestre)."""
    return datetime(ano, 7, 1)


def apos_corte(caminho: Path, corte: datetime | None) -> bool:
    """True se o arquivo deve ser incluído (sem corte => sempre inclui)."""
    if corte is None:
        return True
    return data_referencia(caminho) >= corte
