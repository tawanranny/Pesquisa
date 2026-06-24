# 📚 Organizador de Pesquisa — Projeto RAIP

App com interface (Streamlit) que lê seus **livros** e **fichamentos** em `.docx`
(direto da pasta do **OneDrive sincronizada** no seu computador) e:

1. **Detecta os livros elegíveis** à pesquisa, segundo os critérios do projeto RAIP;
2. **Organiza cada livro por capítulos** (lidos pelos estilos de título do Word — sem gastar tokens);
3. **Mostra quais elegíveis ainda não foram fichados** (cruzando com a pasta de fichamentos).

## 🧠 Como ele economiza tokens

- **Capítulos e leitura**: extraídos localmente com `python-docx` — **custo zero**.
- **Elegibilidade híbrida**: primeiro por **palavras-chave** (custo zero). Só os casos
  *em dúvida* vão para a IA, e mesmo assim enviando **apenas título + sumário**, nunca o livro inteiro.
- **Cache por arquivo**: cada livro é analisado **uma única vez**. Se o arquivo não mudou,
  o resultado vem do cache e nenhum token é gasto de novo.

---

## 1. Instalação (uma vez)

Requer **Python 3.10+**. No terminal, dentro desta pasta:

```bash
pip install -r requirements.txt
```

## 2. Preencher os critérios do RAIP

Abra **`config/criterios_raip.yaml`** e preencha:

- `escopo_pesquisa`: cole a descrição do seu projeto RAIP (copie do claude.ai e cole aqui).
- `palavras_chave_elegivel`: termos centrais da pesquisa (cada acerto soma ponto).
- `palavras_chave_excluir`: termos de livros que **não** entram (ficção, etc.).

> Esse arquivo é o "cérebro" da elegibilidade — quanto mais completo, melhor o resultado
> e menos casos precisam ir para a IA.

## 3. (Opcional) Ligar a IA — chave da Anthropic

A IA só é usada nos casos *em dúvida*. Para habilitar:

1. Acesse **https://console.anthropic.com/** e crie uma conta.
2. Vá em **Settings → API Keys → Create Key** e copie a chave (começa com `sk-ant-...`).
3. Adicione créditos em **Billing** (a classificação usa o modelo barato `claude-haiku`,
   o custo é de centavos por centenas de livros).
4. Copie o arquivo `.env.example` para `.env` e cole a chave em `ANTHROPIC_API_KEY`.

Sem chave, o app funciona normalmente: os casos em dúvida ficam marcados como
**"revisar manualmente"**.

## 4. Rodar o app

```bash
streamlit run app.py
```

Abre no navegador. Na barra lateral:

- Informe a **pasta de livros** e a **pasta de fichamentos** (os caminhos do OneDrive
  sincronizado, ex.: `C:\Users\SeuNome\OneDrive\Pesquisa\livros`).
- Clique em **🔎 Analisar biblioteca**.

Você verá:
- métricas (total, elegíveis, fichados, falta fichar);
- tabela filtrável;
- capítulos de cada livro;
- botões para exportar **Excel** e **relatório Markdown**.

---

## 📁 Estrutura do projeto

```
app.py                      # interface Streamlit
config/criterios_raip.yaml  # critérios de elegibilidade (você preenche)
core/
  leitura_docx.py           # lê .docx, capítulos por estilos de título
  elegibilidade.py          # regras + camada de IA (casos em dúvida)
  fichamentos.py            # cruzamento livro ↔ fichamento (nome aproximado)
  cache.py                  # cache por hash (economiza tokens)
  analise.py                # orquestra tudo
  relatorio.py              # exporta Excel / Markdown
requirements.txt
.env.example                # modelo para a chave da API
```

## ❓ Dúvidas comuns

- **Onde fica a pasta do OneDrive?** No Windows costuma ser `C:\Users\<seu usuário>\OneDrive\...`.
  Garanta que os arquivos estão **disponíveis offline** (ícone de "círculo verde", não "nuvem").
- **Meus capítulos não aparecem.** O app detecta capítulos pelos **estilos de título** do Word
  (Título 1, Título 2...). Se o documento usa texto em negrito "na mão" em vez de estilos,
  os capítulos não são detectados — aplicar os estilos resolve.
- **Os livros não são .docx (são PDF/EPUB).** Dá para adicionar suporte; me avise.
