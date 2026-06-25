"""
Classificação bibliográfica do projeto RAIP.

Em vez de só "elegível/não", produz o GRAU DE INCORPORAÇÃO (1.º / 2.º / 3.º /
Irrelevante) e as PASTAS TEMÁTICAS (1 a 9), conforme as Seções 5 a 7 do
documento operacional. Esquema híbrido econômico:
  1) Regras: autores centrais + palavras-chave por grau + pastas (zero token).
  2) IA: só quando as regras não acham nenhum sinal (dúvida); recebe só
     título + sumário. O resultado fica em cache.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from rapidfuzz import fuzz, process

from .modelos import LivroLido

GRAU_1 = "1.º grau"
GRAU_2 = "2.º grau"
GRAU_3 = "3.º grau / Deferred"
GRAU_DUVIDA = "Dúvida (revisar)"
IRRELEVANTE = "Irrelevante"


@dataclass
class ResultadoElegibilidade:
    elegivel: bool
    metodo: str                       # "lista" | "regras" | "ia"
    pontuacao: int
    motivo: str
    grau: str = ""
    pastas: list[str] = field(default_factory=list)


def _normalizar(txt: str) -> str:
    """minúsculas + sem acentos, para casar termos de forma robusta."""
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt.lower()


def _texto_base(livro: LivroLido) -> str:
    return _normalizar(
        f" {livro.titulo} {Path(livro.nome_arquivo).stem} "
        f"{livro.sumario_texto} {livro.inicio_texto} "
    )


def _achar_termos(base: str, termos) -> list[str]:
    """Termos da lista presentes no texto (substring normalizada)."""
    achados = []
    for t in (termos or []):
        if t and _normalizar(str(t)) in base:
            achados.append(str(t))
    return achados


def _achar_autores(base: str, autores) -> list[str]:
    """Autores presentes. Sobrenome único casa por palavra inteira; nomes
    compostos casam por substring."""
    achados = []
    for autor in (autores or []):
        chave = _normalizar(str(autor)).strip()
        if not chave:
            continue
        if " " in chave or "-" in chave:
            ok = chave in base
        else:
            ok = f" {chave} " in base  # fronteira de palavra
        if ok:
            achados.append(str(autor))
    return achados


def _pastas_tematicas(base: str, config: dict) -> list[str]:
    pastas = []
    for nome, termos in (config.get("pastas_tematicas") or {}).items():
        if _achar_termos(base, termos):
            pastas.append(nome)
    return pastas


# ---------------------------------------------------------------------------
# Modo lista de eleitos
# ---------------------------------------------------------------------------
def carregar_eleitos(config: dict) -> list[str]:
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


def _avaliar_por_lista(livro, config, eleitos, limiar=82):
    alvos = {_normalizar(livro.titulo), _normalizar(Path(livro.nome_arquivo).stem)}
    chaves = [_normalizar(e) for e in eleitos]
    melhor, melhor_nome = 0, ""
    for alvo in alvos:
        if not alvo:
            continue
        achado = process.extractOne(alvo, chaves, scorer=fuzz.token_sort_ratio)
        if achado and achado[1] > melhor:
            melhor = int(achado[1])
            melhor_nome = eleitos[chaves.index(achado[0])]
    pastas = _pastas_tematicas(_texto_base(livro), config)
    if melhor >= limiar:
        return ResultadoElegibilidade(
            True, "lista", melhor, f"Na lista RAIP: ~{melhor_nome} ({melhor}%)",
            grau="(lista RAIP)", pastas=pastas)
    return ResultadoElegibilidade(
        False, "lista", melhor, f"Fora da lista RAIP (melhor: {melhor}%)",
        grau=IRRELEVANTE, pastas=pastas)


# ---------------------------------------------------------------------------
# Classificação por regras (graus)
# ---------------------------------------------------------------------------
def _classificar_por_regras(livro, config):
    base = _texto_base(livro)

    aut_p = _achar_autores(base, config.get("autores_principais"))
    aut_c = _achar_autores(base, config.get("autores_complementares"))
    nucleo = _achar_termos(base, config.get("nucleo_primeiro_grau"))
    segundo = _achar_termos(base, config.get("sinais_segundo_grau"))
    excluir = _achar_termos(base, config.get("palavras_chave_excluir"))
    pastas = _pastas_tematicas(base, config)

    sinais_pos = len(aut_p) + len(aut_c) + len(nucleo) + len(segundo) + len(pastas)
    partes = []
    if aut_p:
        partes.append("autor principal: " + ", ".join(aut_p))
    if aut_c:
        partes.append("autor de apoio: " + ", ".join(aut_c))
    if nucleo:
        partes.append("núcleo: " + ", ".join(nucleo[:6]))
    if segundo:
        partes.append("apoio: " + ", ".join(segundo[:6]))
    if excluir:
        partes.append("exclusão: " + ", ".join(excluir))

    # Irrelevante só quando há sinal de exclusão e NENHUM sinal positivo.
    if excluir and sinais_pos == 0:
        return ResultadoElegibilidade(
            False, "regras", -len(excluir),
            "; ".join(partes) or "sinais de exclusão", grau=IRRELEVANTE,
            pastas=pastas)

    if aut_p or nucleo:
        grau = GRAU_1
    elif aut_c or segundo:
        grau = GRAU_2
    elif pastas:
        grau = GRAU_3
    else:
        grau = GRAU_DUVIDA  # nenhum sinal -> vai para IA, se houver

    motivo = "; ".join(partes) or "sem sinais nas regras"
    elegivel = grau != IRRELEVANTE
    return ResultadoElegibilidade(
        elegivel, "regras", sinais_pos, motivo, grau=grau, pastas=pastas)


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------
def avaliar(livro, config, cliente_ia=None, eleitos=None):
    if eleitos:
        return _avaliar_por_lista(livro, config, eleitos)

    res = _classificar_por_regras(livro, config)
    if res.grau != GRAU_DUVIDA:
        return res

    # Zona de dúvida: sem nenhum sinal de regra.
    if cliente_ia is None:
        sem_texto = (livro.formato == "pdf-sem-texto"
                     or len((livro.inicio_texto or "").strip()) < 40)
        if sem_texto:
            res.motivo = ("Sem texto legível (PDF escaneado sem OCR): só o título "
                          "foi analisado. Instale o OCR ou ligue a IA para decidir.")
        else:
            res.motivo = ("Nenhuma palavra-chave/autor reconhecido no título e no "
                          "início do texto. Ligue a IA para decidir automaticamente.")
        res.elegivel = True  # conservador: deixa para revisão
        return res
    return _avaliar_com_ia(livro, config, cliente_ia, res.pastas)


def _mapa_pastas(config) -> dict[str, str]:
    """Número da pasta -> nome completo (ex.: '7' -> '7 - Direito do Mar')."""
    mapa = {}
    for nome in (config.get("pastas_tematicas") or {}):
        num = str(nome).strip().split(" ", 1)[0].strip(" -.")
        if num:
            mapa[num] = nome
    return mapa


def _grau_de_rotulo(rotulo: str):
    r = (rotulo or "").strip().upper()
    if "IRREL" in r:
        return IRRELEVANTE, False
    if r.startswith("1"):
        return GRAU_1, True
    if r.startswith("2"):
        return GRAU_2, True
    if r.startswith("3"):
        return GRAU_3, True
    return GRAU_DUVIDA, True


def classificar_ia_completo(livro, config, cliente_ia):
    """Manda a IA LER o livro inteiro e julgá-lo frente ao escopo do projeto.
    Decide grau de incorporação, pastas temáticas e justificativa."""
    ia_cfg = config.get("ia", {}) or {}
    max_chars = int(ia_cfg.get("max_caracteres_livro", 200000))
    escopo = (config.get("escopo_pesquisa") or "").strip()
    mapa = _mapa_pastas(config)
    pastas_lista = "\n".join(f"  {n}: {nome.split(' - ', 1)[-1]}"
                             for n, nome in mapa.items())

    texto = (livro.texto_completo or livro.inicio_texto or "").strip()[:max_chars]
    if not texto:
        texto = "(sem texto legível — avalie apenas pelo título)"

    prompt = (
        "Você é um assistente de pesquisa acadêmica em Direito Ambiental "
        "Internacional. Leia o CONTEÚDO DO LIVRO abaixo e avalie, com critério, "
        "se e quanto ele serve à pesquisa, segundo o ESCOPO E CRITÉRIOS.\n\n"
        f"=== ESCOPO E CRITÉRIOS DO PROJETO ===\n{escopo}\n\n"
        f"=== PASTAS TEMÁTICAS (número: tema) ===\n{pastas_lista}\n\n"
        f"=== TÍTULO: {livro.titulo} ===\n"
        f"=== CONTEÚDO DO LIVRO (pode estar parcial) ===\n{texto}\n\n"
        "Responda EXATAMENTE neste formato, em português:\n"
        "GRAU: <1, 2, 3 ou IRRELEVANTE>\n"
        "PASTAS: <números das pastas aplicáveis separados por vírgula, ou '-'>\n"
        "JUSTIFICATIVA: <2 a 4 frases, citando elementos do escopo>"
    )
    try:
        resp = (cliente_ia(prompt) or "").strip()
    except Exception as e:
        return ResultadoElegibilidade(
            True, "regras", 0, f"DÚVIDA (IA indisponível: {e})",
            grau=GRAU_DUVIDA, pastas=[])

    grau, elegivel, pastas, justif = GRAU_DUVIDA, True, [], resp
    for linha in resp.splitlines():
        baixo = linha.strip()
        up = baixo.upper()
        if up.startswith("GRAU"):
            grau, elegivel = _grau_de_rotulo(baixo.split(":", 1)[-1])
        elif up.startswith("PASTAS"):
            nums = re.findall(r"\d+", baixo.split(":", 1)[-1])
            pastas = [mapa[n] for n in nums if n in mapa]
        elif up.startswith("JUSTIF"):
            justif = baixo.split(":", 1)[-1].strip()

    return ResultadoElegibilidade(
        elegivel, "ia", 0, "IA: " + justif.replace("\n", " ").strip()[:400],
        grau=grau, pastas=pastas)


def _avaliar_com_ia(livro, config, cliente_ia, pastas):
    """Classifica via IA usando apenas título + sumário (token mínimo).
    `cliente_ia` é uma função: perguntar(prompt) -> str (backend Max ou API)."""
    ia_cfg = config.get("ia", {}) or {}
    max_ctx = int(ia_cfg.get("max_caracteres_contexto", 4000))
    escopo = (config.get("escopo_pesquisa") or "").strip()

    contexto = (livro.sumario_texto or livro.inicio_texto)[:max_ctx]
    prompt = (
        f"Escopo da pesquisa (projeto RAIP):\n{escopo}\n\n"
        f"Título do livro: {livro.titulo}\n"
        f"Sumário/estrutura:\n{contexto}\n\n"
        "Classifique o GRAU DE INCORPORAÇÃO desta obra na pesquisa. "
        "Responda na 1.ª linha APENAS um destes rótulos: "
        "'1' (relevância alta/núcleo), '2' (relevância média/apoio), "
        "'3' (relevância baixa/correlata) ou 'IRRELEVANTE'. "
        "Na 2.ª linha, uma justificativa curta."
    )
    try:
        texto = (cliente_ia(prompt) or "").strip()
        rotulo = texto.splitlines()[0].strip().upper() if texto else ""
        if rotulo.startswith("IRREL"):
            grau, elegivel = IRRELEVANTE, False
        elif rotulo.startswith("1"):
            grau, elegivel = GRAU_1, True
        elif rotulo.startswith("2"):
            grau, elegivel = GRAU_2, True
        else:
            grau, elegivel = GRAU_3, True
        motivo = "IA: " + texto.replace("\n", " ").strip()
        return ResultadoElegibilidade(elegivel, "ia", 0, motivo,
                                      grau=grau, pastas=pastas)
    except Exception as e:
        return ResultadoElegibilidade(
            True, "regras", 0, f"DÚVIDA (IA indisponível: {e})",
            grau=GRAU_DUVIDA, pastas=pastas)
