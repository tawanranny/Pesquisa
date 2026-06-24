"""Modelos de dados e utilitários compartilhados pelos leitores."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Capitulo:
    titulo: str
    nivel: int  # 1 = capítulo, 2 = seção, etc.


@dataclass
class LivroLido:
    caminho: Path
    nome_arquivo: str
    titulo: str
    formato: str = ""                 # "docx", "pdf-texto", "pdf-ocr", "pdf-sem-texto"
    capitulos: list[Capitulo] = field(default_factory=list)
    sumario_texto: str = ""           # capítulos concatenados (contexto p/ IA)
    inicio_texto: str = ""            # primeiros parágrafos do corpo
    hash_arquivo: str = ""
    erro: str = ""

    @property
    def num_capitulos(self) -> int:
        return sum(1 for c in self.capitulos if c.nivel == 1)


def hash_arquivo(caminho: Path) -> str:
    """MD5 do conteúdo. Base do cache: muda só se o arquivo mudar."""
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()
