"""
Decisão de elegibilidade dos livros (projeto RAIP).

Esquema híbrido econômico:
  1) Regras/palavras-chave (custo zero de token).
  2) Só os casos "em dúvida" vão para a IA, recebendo APENAS título + sumário.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .leitura_docx import LivroLido


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


def avaliar(
    livro: LivroLido,
    config: dict,
    cliente_ia=None,
) -> ResultadoElegibilidade:
    """
    Decide a elegibilidade. Usa a IA somente na zona de dúvida e somente se
    um cliente de IA for fornecido (chave de API configurada).
    """
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
