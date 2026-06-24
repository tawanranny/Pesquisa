"""
Orquestração da análise: lê livros, decide elegibilidade, cruza fichamentos
e monta as linhas do relatório. Respeita o cache para economizar tokens.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from .cache import Cache
from .elegibilidade import avaliar
from .fichamentos import carregar_fichamentos, encontrar_fichamento
from .leitura_docx import listar_docx, ler_livro


def analisar(
    pasta_livros: Path,
    pasta_fichamentos: Path,
    config: dict,
    cliente_ia=None,
    limiar_fichamento: int = 80,
    usar_cache: bool = True,
    progresso: Callable[[int, int, str], None] | None = None,
) -> tuple[list[dict], dict[str, list]]:
    """
    Retorna (linhas, detalhes_capitulos).
    `progresso(i, total, nome)` é chamado a cada livro (para barra de progresso).
    """
    cache = Cache()
    fichamentos = carregar_fichamentos(pasta_fichamentos)
    arquivos = listar_docx(pasta_livros)
    total = len(arquivos)

    linhas: list[dict] = []
    detalhes: dict[str, list] = {}

    for i, caminho in enumerate(arquivos, start=1):
        if progresso:
            progresso(i, total, caminho.name)

        livro = ler_livro(caminho)
        detalhes[caminho.name] = [
            {"titulo": c.titulo, "nivel": c.nivel} for c in livro.capitulos
        ]

        if livro.erro:
            linhas.append({
                "Livro": livro.titulo, "Elegível": "Erro", "Método": "-",
                "Motivo": livro.erro, "Nº Capítulos": 0, "Fichado?": "-",
                "Fichamento correspondente": "-", "Similaridade": 0,
                "Arquivo": caminho.name,
            })
            continue

        # --- Elegibilidade (com cache por hash) ---
        cacheado = cache.obter(livro.hash_arquivo) if usar_cache else None
        if cacheado:
            elegivel = cacheado["elegivel"]
            metodo = cacheado["metodo"]
            motivo = cacheado["motivo"]
        else:
            res = avaliar(livro, config, cliente_ia)
            elegivel, metodo, motivo = res.elegivel, res.metodo, res.motivo
            cache.salvar(livro.hash_arquivo, {
                "elegivel": elegivel, "metodo": metodo, "motivo": motivo,
                "titulo": livro.titulo,
            })

        # --- Cruzamento com fichamentos (sempre recalculado: é local/barato) ---
        if elegivel:
            status = encontrar_fichamento(
                livro.titulo, livro.nome_arquivo, fichamentos, limiar_fichamento
            )
            fichado = "Sim" if status.fichado else "Não"
            ficha = status.fichamento_correspondente or "—"
            sim = status.similaridade
        else:
            fichado, ficha, sim = "—", "—", 0

        linhas.append({
            "Livro": livro.titulo,
            "Elegível": "Sim" if elegivel else "Não",
            "Método": metodo,
            "Motivo": motivo,
            "Nº Capítulos": livro.num_capitulos,
            "Fichado?": fichado,
            "Fichamento correspondente": ficha,
            "Similaridade": sim,
            "Arquivo": caminho.name,
        })

    return linhas, detalhes
