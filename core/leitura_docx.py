"""
Leitura de arquivos .docx: título, capítulos (estilos de título) e texto.
Tudo local, SEM gastar tokens de IA.
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document

from .modelos import Capitulo, LivroLido, hash_arquivo


def _nivel_titulo(nome_estilo: str | None, style_id: str | None) -> int:
    """Nível do título (1, 2, 3...) ou 0 se não for título.
    Funciona em PT ("Título 1"), EN ("Heading 1") e pelo style_id ("Heading1")."""
    for txt in (nome_estilo or "", style_id or ""):
        m = re.search(r"(?:heading|t[íi]tulo)\s*([1-9])", txt, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0


def ler_docx(caminho: Path, max_inicio_chars: int = 3000,
             completo: bool = False, max_completo: int = 200000) -> LivroLido:
    livro = LivroLido(
        caminho=caminho, nome_arquivo=caminho.name,
        titulo=caminho.stem, formato="docx",
    )
    try:
        livro.hash_arquivo = hash_arquivo(caminho)
        doc = Document(str(caminho))
    except Exception as e:
        livro.erro = f"Falha ao abrir .docx: {e}"
        return livro

    inicio_partes: list[str] = []
    corpo_partes: list[str] = []   # texto integral (quando completo=True)
    primeiro_titulo1: str | None = None

    for p in doc.paragraphs:
        texto = (p.text or "").strip()
        if not texto:
            continue
        try:
            nome_estilo = p.style.name if p.style else None
            style_id = p.style.style_id if p.style else None
        except Exception:
            nome_estilo, style_id = None, None

        nivel = _nivel_titulo(nome_estilo, style_id)
        if nivel:
            livro.capitulos.append(Capitulo(titulo=texto, nivel=nivel))
            if nivel == 1 and primeiro_titulo1 is None:
                primeiro_titulo1 = texto
        elif len("".join(inicio_partes)) < max_inicio_chars:
            inicio_partes.append(texto)

        if completo and len("".join(corpo_partes)) < max_completo:
            corpo_partes.append(texto)

    if primeiro_titulo1:
        livro.titulo = primeiro_titulo1

    livro.sumario_texto = "\n".join(
        ("  " * (c.nivel - 1)) + c.titulo for c in livro.capitulos
    )
    livro.inicio_texto = " ".join(inicio_partes)[:max_inicio_chars]
    if completo:
        livro.texto_completo = "\n".join(corpo_partes)[:max_completo]
    return livro
