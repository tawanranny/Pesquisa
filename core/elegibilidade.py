"""
Decisão de elegibilidade dos livros (projeto RAIP).

Esquema híbrido econômico:
  1) Regras/palavras-chave (custo zero de token).
  2) Só os casos "em dúvida" vão para a IA, recebendo APENAS título + sumário.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz, process

from .modelos import LivroLido


@dataclass
class ResultadoElegibilidade:
    elegivel: bool
    metodo: str          # "regras" ou "ia"
    pontuacao: int
    motivo: str


def _normalizar(txt: str) -> str:
    """minúsculas + sem acentos, para casar palavras-chave de forma robusta."""
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt.lower()


def _pontuar(livro: LivroLido, config: dict) -> tuple[int, list[str]]:
    """Conta palavras-chave positivas/negativas no título + sumário + início."""
    base = _normalizar(
        f"{livro.titulo}\n{livro.sumario_texto}\n{livro.inicio_texto}"
    )
    pontos = 0
    achados: list[str] = []

    for termo in (config.get("palavras_chave_elegivel") or []):
        if termo and _normalizar(str(termo)) in base:
            pontos += 1
            achados.append(f"+{termo}")
    for termo in (config.get("palavras_chave_excluir") or []):
        if termo and _normalizar(str(termo)) in base:
            pontos -= 1
            achados.append(f"-{termo}")
    return pontos, achados


def carregar_eleitos(config: dict) -> list[str]:
    """Lista de livros eleitos pelo RAIP. Pode vir embutida no YAML
    (lista_livros_eleitos) ou de um arquivo .txt (um título por linha)
    apontado por arquivo_livros_eleitos."""
    eleitos = list(config.get("lista_livros_eleitos") or [])
    caminho = config.get("arquivo_livros_eleitos")
    if caminho:
        p = Path(caminho)
        if p.exists():
            eleitos += [
                ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]
    return [str(e) for e in eleitos if str(e).strip()]


def _avaliar_por_lista(livro, eleitos, limiar=82):
    """Elegível se o título/arquivo casar com algum livro da lista de eleitos."""
    alvos = {_normalizar(livro.titulo), _normalizar(Path(livro.nome_arquivo).stem)}
    chaves = [_normalizar(e) for e in eleitos]
    melhor = 0
    melhor_nome = ""
    for alvo in alvos:
        if not alvo:
            continue
        achado = process.extractOne(alvo, chaves, scorer=fuzz.token_sort_ratio)
        if achado and achado[1] > melhor:
            melhor = int(achado[1])
            melhor_nome = eleitos[chaves.index(achado[0])]
    if melhor >= limiar:
        return ResultadoElegibilidade(
            True, "lista", melhor, f"Na lista RAIP: ~{melhor_nome} ({melhor}%)")
    return ResultadoElegibilidade(
        False, "lista", melhor, f"Fora da lista RAIP (melhor: {melhor}%)")


def avaliar(
    livro: LivroLido,
    config: dict,
    cliente_ia=None,
    eleitos: list[str] | None = None,
) -> ResultadoElegibilidade:
    """
    Decide a elegibilidade.
      1) Se há LISTA DE ELEITOS (RAIP), ela manda: elegível = está na lista.
      2) Senão, usa regras/palavras-chave.
      3) Só na zona de dúvida (e se houver cliente de IA) consulta a IA.
    """
    if eleitos:
        return _avaliar_por_lista(livro, eleitos)

    limiar_ok = int(config.get("limiar_elegivel", 2))
    limiar_nao = int(config.get("limiar_nao_elegivel", 0))

    pontos, achados = _pontuar(livro, config)
    detalhe = ", ".join(achados) if achados else "nenhuma palavra-chave"

    if pontos >= limiar_ok:
        return ResultadoElegibilidade(True, "regras", pontos,
                                      f"Palavras-chave: {detalhe}")
    if pontos <= limiar_nao:
        return ResultadoElegibilidade(False, "regras", pontos,
                                      f"Palavras-chave: {detalhe}")

    # Zona de dúvida.
    if cliente_ia is None:
        # Sem IA disponível: decisão conservadora -> marca como elegível
        # para revisão manual, sinalizando que precisa de checagem.
        return ResultadoElegibilidade(
            True, "regras", pontos,
            f"DÚVIDA (revisar manualmente) — {detalhe}",
        )

    return _avaliar_com_ia(livro, config, cliente_ia, pontos, detalhe)


def _avaliar_com_ia(livro, config, cliente_ia, pontos, detalhe):
    """Pergunta à IA usando apenas título + sumário (token mínimo)."""
    ia_cfg = config.get("ia", {}) or {}
    modelo = ia_cfg.get("modelo", "claude-haiku-4-5-20251001")
    max_ctx = int(ia_cfg.get("max_caracteres_contexto", 4000))
    escopo = config.get("escopo_pesquisa", "").strip()

    contexto = (livro.sumario_texto or livro.inicio_texto)[:max_ctx]
    prompt = (
        f"Escopo da pesquisa (projeto RAIP):\n{escopo}\n\n"
        f"Título do livro: {livro.titulo}\n"
        f"Sumário/estrutura:\n{contexto}\n\n"
        "Este livro é ELEGÍVEL para essa pesquisa? "
        "Responda na primeira linha apenas SIM ou NAO, "
        "e na segunda linha uma justificativa curta."
    )
    try:
        resp = cliente_ia.messages.create(
            model=modelo,
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = resp.content[0].text.strip()
        primeira = texto.splitlines()[0].strip().upper()
        elegivel = primeira.startswith("SIM")
        motivo = texto.replace("\n", " ").strip()
        return ResultadoElegibilidade(elegivel, "ia", pontos, f"IA: {motivo}")
    except Exception as e:
        # Falha na IA: cai na decisão conservadora por regras.
        return ResultadoElegibilidade(
            True, "regras", pontos,
            f"DÚVIDA (IA indisponível: {e}) — {detalhe}",
        )
