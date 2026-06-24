"""
Leitura de PDFs: com texto (extração direta) e escaneados (OCR).

Estratégia (sem gastar tokens de IA):
  • Capítulos vêm dos MARCADORES/sumário embutido no PDF (outline), quando existem.
  • Texto: extraído direto do PDF; se vier vazio (PDF escaneado), tenta OCR local.

O OCR é OPCIONAL: requer os pacotes pytesseract + pdf2image e o programa
Tesseract instalado no sistema. Se não estiver disponível, o PDF escaneado é
marcado como "pdf-sem-texto" (capítulos e elegibilidade ficam para revisão).
"""
from __future__ import annotations

from pathlib import Path

from .modelos import Capitulo, LivroLido, hash_arquivo

# Limite de páginas para OCR (controla tempo). Suficiente p/ capa+sumário+início.
PAGINAS_OCR = 15
MIN_TEXTO_VALIDO = 200  # menos que isso no PDF inteiro => tratamos como escaneado


def _extrair_outline(reader) -> list[Capitulo]:
    """Lê os marcadores (bookmarks) do PDF como capítulos, com nível pela profundidade."""
    capitulos: list[Capitulo] = []

    def percorrer(itens, nivel=1):
        for item in itens:
            if isinstance(item, list):
                percorrer(item, nivel + 1)
            else:
                titulo = getattr(item, "title", None)
                if titulo:
                    capitulos.append(Capitulo(titulo=str(titulo).strip(), nivel=nivel))

    try:
        percorrer(reader.outline)
    except Exception:
        pass
    return capitulos


def _ocr_paginas(caminho: Path, max_paginas: int) -> str:
    """OCR das primeiras páginas. Retorna '' se as dependências não existirem."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except Exception:
        return ""  # dependências de OCR ausentes
    try:
        imagens = convert_from_path(str(caminho), first_page=1, last_page=max_paginas)
        partes = [pytesseract.image_to_string(img, lang="por") for img in imagens]
        return "\n".join(partes).strip()
    except Exception:
        return ""


def ler_pdf(caminho: Path, max_inicio_chars: int = 3000) -> LivroLido:
    livro = LivroLido(
        caminho=caminho, nome_arquivo=caminho.name,
        titulo=caminho.stem, formato="pdf-texto",
    )
    try:
        from pypdf import PdfReader
        livro.hash_arquivo = hash_arquivo(caminho)
        reader = PdfReader(str(caminho))
    except Exception as e:
        livro.erro = f"Falha ao abrir PDF: {e}"
        return livro

    # 1) Capítulos pelos marcadores embutidos.
    livro.capitulos = _extrair_outline(reader)

    # 2) Texto direto das primeiras páginas.
    partes: list[str] = []
    try:
        for pagina in reader.pages[:PAGINAS_OCR]:
            t = pagina.extract_text() or ""
            if t:
                partes.append(t)
            if len("".join(partes)) > max_inicio_chars * 2:
                break
    except Exception:
        pass
    texto = "\n".join(partes).strip()

    # 3) PDF escaneado? Pouco/nenhum texto -> tenta OCR.
    if len(texto) < MIN_TEXTO_VALIDO:
        ocr = _ocr_paginas(caminho, PAGINAS_OCR)
        if ocr:
            texto = ocr
            livro.formato = "pdf-ocr"
        else:
            # Sem texto e sem OCR: NÃO é erro fatal. Ainda dá para avaliar
            # elegibilidade pelo título (modo lista) e ler capítulos do outline.
            livro.formato = "pdf-sem-texto"

    # Metadados: título do PDF, se houver.
    try:
        if reader.metadata and reader.metadata.title:
            livro.titulo = str(reader.metadata.title).strip()
    except Exception:
        pass

    livro.inicio_texto = texto[:max_inicio_chars]
    if livro.capitulos:
        livro.sumario_texto = "\n".join(
            ("  " * (c.nivel - 1)) + c.titulo for c in livro.capitulos
        )
    else:
        # Sem marcadores: usa o início do texto como contexto para a IA.
        livro.sumario_texto = livro.inicio_texto
    return livro
