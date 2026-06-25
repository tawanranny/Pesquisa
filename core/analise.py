"""
Orquestração da análise: lê livros, decide elegibilidade, cruza fichamentos
e monta as linhas do relatório. Respeita o cache para economizar tokens.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from .cache import Cache
from .datas import apos_corte, data_referencia
from .elegibilidade import avaliar, carregar_eleitos
from .elegibilidade import classificar_ia_completo
from .fichamentos import carregar_fichamentos, encontrar_fichamento
from .leitura import listar_livros, ler_livro


def analisar(
    pasta_livros: Path,
    pasta_fichamentos: Path,
    config: dict,
    cliente_ia=None,
    limiar_fichamento: int = 80,
    usar_cache: bool = True,
    data_corte: datetime | None = None,
    modo_ia_total: bool = False,
    progresso: Callable[[int, int, str], None] | None = None,
) -> tuple[list[dict], dict[str, list]]:
    """
    Retorna (linhas, detalhes_capitulos).
    `data_corte`: se informado, só cataloga livros cuja data (criação OU
    modificação) seja igual/posterior ao corte.
    `modo_ia_total`: se True (e houver IA), a IA LÊ o livro inteiro e decide o
    grau frente ao escopo — em vez do juízo por palavras-chave.
    `progresso(i, total, nome)` é chamado a cada livro (para barra de progresso).
    """
    cache = Cache()
    fichamentos = carregar_fichamentos(pasta_fichamentos)
    eleitos = carregar_eleitos(config)
    ia_cfg = config.get("ia", {}) or {}
    # IA-total só faz sentido com IA disponível e sem a lista de eleitos no comando.
    ia_total = modo_ia_total and cliente_ia is not None and not eleitos
    max_completo = int(ia_cfg.get("max_caracteres_livro", 200000))
    paginas_ocr = int(ia_cfg.get("paginas_ocr_completo", 30))
    # Aplica o corte de data já na listagem (varre um a um e descarta antigos).
    todos = listar_livros(pasta_livros)
    arquivos = [c for c in todos if apos_corte(c, data_corte)]
    total = len(arquivos)

    linhas: list[dict] = []
    detalhes: dict[str, list] = {}

    for i, caminho in enumerate(arquivos, start=1):
        if progresso:
            progresso(i, total, caminho.name)

        data_add = data_referencia(caminho).strftime("%Y-%m-%d")
        livro = ler_livro(caminho, completo=ia_total,
                          max_completo=max_completo, paginas_ocr_completo=paginas_ocr)
        detalhes[caminho.name] = [
            {"titulo": c.titulo, "nivel": c.nivel} for c in livro.capitulos
        ]

        if livro.erro:
            linhas.append({
                "Livro": livro.titulo, "Grau": "-", "Elegível": "Erro",
                "Pastas temáticas": "-", "Método": "-",
                "Motivo": livro.erro, "Nº Capítulos": 0, "Fichado?": "-",
                "Fichamento correspondente": "-", "Similaridade": 0,
                "Formato": livro.formato or "-", "Adicionado em": data_add,
                "Arquivo": caminho.name,
            })
            continue

        # --- Elegibilidade ---
        # No modo IA-total, a IA lê o livro inteiro (passo caro): vale cachear.
        # Com lista de eleitos ou só regras o custo é zero -> recalcula sempre.
        usar_cache_aqui = usar_cache and eleitos == []
        cacheado = cache.obter(livro.hash_arquivo) if usar_cache_aqui else None
        if cacheado:
            elegivel = cacheado["elegivel"]
            metodo = cacheado["metodo"]
            motivo = cacheado["motivo"]
            grau = cacheado.get("grau", "")
            pastas = cacheado.get("pastas", [])
        else:
            if ia_total:
                res = classificar_ia_completo(livro, config, cliente_ia)
            else:
                res = avaliar(livro, config, cliente_ia, eleitos=eleitos)
            elegivel, metodo, motivo = res.elegivel, res.metodo, res.motivo
            grau, pastas = res.grau, res.pastas
            # Guarda no cache quando a IA decidiu (o passo demorado).
            if usar_cache_aqui and metodo == "ia":
                cache.salvar(livro.hash_arquivo, {
                    "elegivel": elegivel, "metodo": metodo, "motivo": motivo,
                    "grau": grau, "pastas": pastas, "titulo": livro.titulo,
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
            "Grau": grau,
            "Elegível": "Sim" if elegivel else "Não",
            "Pastas temáticas": "; ".join(pastas) if pastas else "—",
            "Método": metodo,
            "Motivo": motivo,
            "Nº Capítulos": livro.num_capitulos,
            "Fichado?": fichado,
            "Fichamento correspondente": ficha,
            "Similaridade": sim,
            "Formato": livro.formato,
            "Adicionado em": data_add,
            "Arquivo": caminho.name,
        })

    return linhas, detalhes
