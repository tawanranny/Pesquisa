"""
Organizador de Pesquisa — Projeto RAIP
=======================================
App com interface (Streamlit) para:
  • detectar quais livros são ELEGÍVEIS à pesquisa (critérios do RAIP);
  • organizar cada livro por CAPÍTULOS (estilos de título do Word);
  • verificar quais elegíveis ainda NÃO foram FICHADOS.

Como rodar:
    pip install -r requirements.txt
    streamlit run app.py
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
import yaml
from dotenv import load_dotenv

from core.analise import analisar
from core.cache import Cache
from core.relatorio import exportar_excel, exportar_markdown, para_dataframe

load_dotenv()

st.set_page_config(page_title="Pesquisa RAIP", page_icon="📚", layout="wide")
st.title("📚 Organizador de Pesquisa — Projeto RAIP")
st.caption(
    "Detecta livros elegíveis, organiza por capítulos e mostra o que ainda "
    "falta fichar. Lê .docx e PDF (com texto ou escaneado via OCR) "
    "da pasta do OneDrive sincronizada."
)

CAMINHO_CONFIG = Path("config/criterios_raip.yaml")


def carregar_config() -> dict:
    if CAMINHO_CONFIG.exists():
        return yaml.safe_load(CAMINHO_CONFIG.read_text(encoding="utf-8")) or {}
    return {}


def criar_cliente_ia(usar_ia: bool):
    """Cria o cliente da Anthropic se houver chave; senão retorna None."""
    if not usar_ia:
        return None
    chave = os.getenv("ANTHROPIC_API_KEY")
    if not chave:
        st.sidebar.warning(
            "IA ligada, mas ANTHROPIC_API_KEY não encontrada. "
            "Casos em dúvida serão marcados para revisão manual."
        )
        return None
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=chave)
    except Exception as e:
        st.sidebar.error(f"Não foi possível iniciar a IA: {e}")
        return None


# --------------------------- Barra lateral -------------------------------
st.sidebar.header("⚙️ Configuração")

pasta_livros = st.sidebar.text_input(
    "Pasta de livros (OneDrive sincronizado)",
    value=st.session_state.get("pasta_livros", ""),
    placeholder=r"Ex.: C:\Users\Tawan\OneDrive\Pesquisa\livros",
)
pasta_fichamentos = st.sidebar.text_input(
    "Pasta de fichamentos (OneDrive sincronizado)",
    value=st.session_state.get("pasta_fichamentos", ""),
    placeholder=r"Ex.: C:\Users\Tawan\OneDrive\Pesquisa\fichamentos",
)

usar_ia = st.sidebar.checkbox(
    "Usar IA nos casos em dúvida", value=bool(os.getenv("ANTHROPIC_API_KEY"))
)
limiar_fichamento = st.sidebar.slider(
    "Rigor do casamento livro↔fichamento", 50, 100, 80,
    help="Quanto maior, mais parecidos os nomes precisam ser para contar como fichado.",
)
usar_cache = st.sidebar.checkbox(
    "Usar cache (economiza tokens)", value=True,
    help="Cada livro é analisado uma vez; se o arquivo não mudar, não reprocessa.",
)
if st.sidebar.button("🗑️ Limpar cache"):
    Cache().limpar()
    st.sidebar.success("Cache limpo.")

with st.sidebar.expander("📋 Critérios RAIP (resumo)"):
    cfg_preview = carregar_config()
    eleitos_prev = cfg_preview.get("lista_livros_eleitos") or []
    arq_eleitos = cfg_preview.get("arquivo_livros_eleitos") or ""
    if eleitos_prev or arq_eleitos:
        st.success(f"Modo LISTA DE ELEITOS ativo "
                   f"({len(eleitos_prev)} título(s){' + arquivo' if arq_eleitos else ''}).")
        st.caption("Elegível = está na lista do RAIP.")
    else:
        st.info("Modo PALAVRAS-CHAVE (sem lista de eleitos).")
        escopo = (cfg_preview.get("escopo_pesquisa") or "").strip()
        st.write("**Escopo:**", escopo[:300] or "_(não preenchido)_")
        st.write("**Palavras-chave elegível:**",
                 cfg_preview.get("palavras_chave_elegivel") or "_(vazio)_")
        st.write("**Palavras-chave excluir:**",
                 cfg_preview.get("palavras_chave_excluir") or "_(vazio)_")
    st.caption("Edite em config/criterios_raip.yaml")


# ------------------------------ Execução ---------------------------------
def validar_pastas() -> bool:
    ok = True
    if not pasta_livros or not Path(pasta_livros).exists():
        st.error("Pasta de livros inválida ou não informada.")
        ok = False
    if not pasta_fichamentos or not Path(pasta_fichamentos).exists():
        st.error("Pasta de fichamentos inválida ou não informada.")
        ok = False
    return ok


if st.button("🔎 Analisar biblioteca", type="primary"):
    if validar_pastas():
        st.session_state["pasta_livros"] = pasta_livros
        st.session_state["pasta_fichamentos"] = pasta_fichamentos
        config = carregar_config()
        cliente_ia = criar_cliente_ia(usar_ia)

        barra = st.progress(0.0, text="Iniciando...")

        def progresso(i, total, nome):
            barra.progress(i / max(total, 1), text=f"({i}/{total}) {nome}")

        with st.spinner("Lendo livros e cruzando fichamentos..."):
            linhas, detalhes = analisar(
                Path(pasta_livros), Path(pasta_fichamentos), config,
                cliente_ia=cliente_ia, limiar_fichamento=limiar_fichamento,
                usar_cache=usar_cache, progresso=progresso,
            )
        barra.empty()
        st.session_state["linhas"] = linhas
        st.session_state["detalhes"] = detalhes


# ------------------------------ Resultados -------------------------------
if "linhas" in st.session_state:
    linhas = st.session_state["linhas"]
    detalhes = st.session_state["detalhes"]
    df = para_dataframe(linhas)

    elegiveis = df[df["Elegível"] == "Sim"]
    nao_fichados = elegiveis[elegiveis["Fichado?"] == "Não"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Livros", len(df))
    c2.metric("Elegíveis", len(elegiveis))
    c3.metric("Já fichados", int((elegiveis["Fichado?"] == "Sim").sum()))
    c4.metric("Falta fichar", len(nao_fichados))

    st.subheader("Resultado")
    f1, f2 = st.columns(2)
    so_elegiveis = f1.checkbox("Só elegíveis", value=True)
    so_nao_fichados = f2.checkbox("Só não fichados", value=False)

    visao = df.copy()
    if so_elegiveis:
        visao = visao[visao["Elegível"] == "Sim"]
    if so_nao_fichados:
        visao = visao[visao["Fichado?"] == "Não"]

    st.dataframe(visao, use_container_width=True, hide_index=True)

    st.subheader("📖 Capítulos por livro")
    for _, r in visao.iterrows():
        caps = detalhes.get(r["Arquivo"], [])
        marca = "✅" if r["Fichado?"] == "Sim" else ("❌" if r["Fichado?"] == "Não" else "•")
        with st.expander(f"{marca} {r['Livro']} — {r['Nº Capítulos']} capítulo(s)"):
            if caps:
                for c in caps:
                    st.write(f"{'　' * (c['nivel'] - 1)}• {c['titulo']}")
            else:
                st.caption("Nenhum capítulo detectado pelos estilos de título do Word.")

    st.subheader("⬇️ Exportar")
    e1, e2 = st.columns(2)
    e1.download_button(
        "Baixar Excel (.xlsx)", data=exportar_excel(df),
        file_name="pesquisa_raip.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    e2.download_button(
        "Baixar relatório (.md)",
        data=exportar_markdown(df, detalhes).encode("utf-8"),
        file_name="pesquisa_raip.md", mime="text/markdown",
    )
else:
    st.info("Configure as pastas na barra lateral e clique em **Analisar biblioteca**.")
