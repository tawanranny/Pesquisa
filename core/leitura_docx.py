"""
Leitura de arquivos .docx: extrai título, capítulos e texto.

Tudo aqui é feito localmente, SEM gastar tokens de IA. Os capítulos são
detectados pelos estilos de título do Word (Título 1/2, Heading 1/2).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document


@dataclass
class Capitulo:
    titulo: str
    nivel: int  # 1 = Título 1 (capítulo), 2 = Título 2 (seção), etc.


@dataclass
class LivroLido:
    caminho: Path
    nome_arquivo: str
    titulo: str                       # melhor palpite do título da obra
    capitulos: list[Capitulo] = field(default_factory=list)
    sumario_texto: str = ""           # capítulos concatenados (contexto p/ IA)
    inicio_texto: str = ""            # primeiros parágrafos do corpo
    hash_arquivo: str = ""
    erro: str = ""

    @property
    def num_capitulos(self) -> int:
        return sum(1 for c in self.capitulos if c.nivel == 1)


def hash_arquivo(caminho: Path) -> str:
    """MD5 do conteúdo + tamanho. Base do cache: muda só se o arquivo mudar."""
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def _nivel_titulo(nome_estilo: str | None, style_id: str | None) -> int:
    """
    Retorna o nível do título (1, 2, 3...) ou 0 se o parágrafo não é título.
    Funciona com Word em português ("Título 1") e inglês ("Heading 1"),
    e também pelo style_id interno ("Heading1").
    """
    candidatos = [nome_estilo or "", style_id or ""]
    for txt in candidatos:
        m = re.search(r"(?:heading|t[íi]tulo)\s*([1-9])", txt, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0


def ler_livro(caminho: Path, max_inicio_chars: int = 3000) -> LivroLido:
    """Lê um .docx e devolve título, capítulos e trechos de contexto."""
    livro = LivroLido(
        caminho=caminho,
        nome_arquivo=caminho.name,
        titulo=caminho.stem,  # fallback: nome do arquivo sem extensão
    )
    try:
        livro.hash_arquivo = hash_arquivo(caminho)
        doc = Document(str(caminho))
    except Exception as e:  # arquivo corrompido, protegido, etc.
        livro.erro = f"Falha ao abrir: {e}"
        return livro

    inicio_partes: list[str] = []
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
        else:
            if len("".join(inicio_partes)) < max_inicio_chars:
                inicio_partes.append(texto)

    # Título da obra: 1º Título 1, senão "Title", senão nome do arquivo.
    if primeiro_titulo1:
        livro.titulo = primeiro_titulo1
    else:
        for p in doc.paragraphs[:5]:
            try:
                if p.style and "title" in (p.style.name or "").lower():
                    if p.text.strip():
                        livro.titulo = p.text.strip()
                        break
            except Exception:
                pass

    livro.sumario_texto = "\n".join(
        ("  " * (c.nivel - 1)) + c.titulo for c in livro.capitulos
    )
    livro.inicio_texto = " ".join(inicio_partes)[:max_inicio_chars]
    return livro


def listar_docx(pasta: Path) -> list[Path]:
    """Lista todos os .docx de uma pasta (recursivo), ignorando temporários."""
    if not pasta.exists():
        return []
    return sorted(
        p for p in pasta.rglob("*.docx")
        if not p.name.startswith("~$")  # arquivos temporários do Word
    )
