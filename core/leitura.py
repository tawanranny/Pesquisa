"""
Despachante de leitura: escolhe o leitor certo por extensão (.docx ou .pdf)
e lista os arquivos suportados em uma pasta.
"""
from __future__ import annotations

from pathlib import Path

from .leitura_docx import ler_docx
from .leitura_pdf import ler_pdf
from .modelos import LivroLido

EXTENSOES = (".docx", ".pdf")


def ler_livro(caminho: Path, completo: bool = False,
              max_completo: int = 200000,
              paginas_ocr_completo: int = 30) -> LivroLido:
    suf = caminho.suffix.lower()
    if suf == ".docx":
        return ler_docx(caminho, completo=completo, max_completo=max_completo)
    if suf == ".pdf":
        return ler_pdf(caminho, completo=completo, max_completo=max_completo,
                       paginas_ocr_completo=paginas_ocr_completo)
    livro = LivroLido(caminho=caminho, nome_arquivo=caminho.name,
                      titulo=caminho.stem)
    livro.erro = f"Formato não suportado: {suf}"
    return livro


def listar_livros(pasta: Path) -> list[Path]:
    """Lista .docx e .pdf de uma pasta (recursivo), ignorando temporários."""
    if not pasta.exists():
        return []
    arquivos = [
        p for p in pasta.rglob("*")
        if p.suffix.lower() in EXTENSOES and not p.name.startswith("~$")
    ]
    return sorted(arquivos)
