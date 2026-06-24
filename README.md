# 📚 Organizador de Pesquisa — Projeto RAIP

**App web local** (interface HTML própria, servida por Flask) que lê seus
**livros** e **fichamentos** em `.docx` e **PDF** (com texto ou escaneado via
OCR), direto da pasta do **OneDrive sincronizada** no seu computador, e:

1. **Examina cada livro um a um** e cataloga **somente os adicionados a partir
   de uma data de corte** (padrão: 2.º semestre de 2025 — 01/07/2025);
2. **Classifica por grau de incorporação** (1.º/2.º/3.º/Irrelevante) e distribui
   nas **9 pastas temáticas** do RAIP;
3. **Organiza cada livro por capítulos** (sem gastar tokens);
4. **Mostra quais elegíveis ainda não foram fichados** (cruza com os fichamentos);
5. Mantém um **catálogo editável** (Seção 8) salvo em CSV.

> ⚠️ **Onde rodar:** este programa roda **na sua máquina**, onde o OneDrive está
> sincronizado — é ele que abre fisicamente a pasta e percorre os livros. A data
> de corte usa **criação OU modificação** do arquivo (no Windows, a data de
> criação é a de quando o arquivo passou a existir na pasta).

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

## 2. Definir a elegibilidade (RAIP)

Abra **`config/criterios_raip.yaml`**. Há dois modos:

**Modo A — Lista de eleitos (recomendado, mais preciso, ZERO token).**
O projeto RAIP já elege os livros da tese. Cole essa lista em `lista_livros_eleitos`
(ou aponte um `.txt` em `arquivo_livros_eleitos`). O app marca como elegível quem está
na lista (casamento aproximado por título/nome de arquivo) — funciona até para PDF escaneado,
pois compara pelo nome.

**Modo B — Palavras-chave (quando não há lista pronta).**
Deixe a lista vazia e preencha:
- `escopo_pesquisa`: descrição do projeto RAIP (para a IA decidir dúvidas);
- `palavras_chave_elegivel`: termos centrais (cada acerto soma ponto);
- `palavras_chave_excluir`: termos de livros que **não** entram.

> Tendo a lista de eleitos do RAIP, use o Modo A: é o mais fiel à sua curadoria.

## 2.1 PDFs escaneados (OCR)

PDFs **com texto** são lidos direto (capítulos vêm do sumário/marcadores do PDF).
PDFs **escaneados** (imagens) precisam de OCR local para ter o conteúdo lido:

1. `pip install pytesseract pdf2image` (já estão no requirements);
2. Instale os programas do sistema **Tesseract** (com português) e **Poppler**:
   - Windows: Tesseract — <https://github.com/UB-Mannheim/tesseract/wiki>; Poppler — `poppler-windows`.

Sem OCR, o PDF escaneado aparece como **`pdf-sem-texto`** — ainda é avaliado pelo
título (modo lista) e pelos marcadores, mas o conteúdo não é lido.

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
python servidor.py
```

Ele abre sozinho no navegador em **http://127.0.0.1:5000**. Na tela:

- Informe a **pasta de livros** e a **pasta de fichamentos** (caminhos do OneDrive
  sincronizado, ex.: `C:\Users\SeuNome\OneDrive\Pesquisa\livros`).
- Ajuste a **data de corte** (padrão 01/07/2025 — só cataloga o que foi adicionado
  a partir dela).
- Clique em **🔎 Analisar biblioteca**.

Você verá:
- métricas (total, elegíveis, fichados, falta fichar);
- distribuição por **grau de incorporação** e tabela filtrável (por grau e busca);
- o **catálogo editável (Seção 8)** — veja abaixo;
- botões para exportar **Excel** e **relatório Markdown**.

## 4.1 Catálogo editável (Seção 8)

Cada obra vira um registro com os campos do documento operacional: referência
(NBR 6023:2025), autor(es), ano, idioma, **pasta(s) temática(s)**, **grau de
incorporação**, **fichamento disponível?**, **capítulo(s) de incidência**,
pendência bibliográfica, localização física e observações.

- Os campos **automáticos** (referência inicial, grau, pastas, fichamento) já
  vêm preenchidos pela análise; os demais você edita direto na tabela.
- Clique em **💾 Salvar catálogo** para gravar em `catalogo_raip.csv`.
- Ao **reanalisar** a biblioteca, novos livros entram e **suas edições salvas
  são preservadas** (só os campos em branco recebem valores automáticos).
- Campos com múltiplos valores (pastas, capítulos) usam `;` como separador.

---

## 📁 Estrutura do projeto

```
servidor.py                 # app web local (Flask) — interface principal
web/
  templates/index.html      # interface HTML
  static/style.css          # estilo
  static/app.js             # lógica do front (chama o servidor)
config/criterios_raip.yaml  # critérios de classificação (você preenche)
core/
  modelos.py                # estruturas de dados compartilhadas
  leitura.py                # despachante: escolhe leitor por extensão
  leitura_docx.py           # lê .docx, capítulos por estilos de título
  leitura_pdf.py            # lê PDF (texto + OCR), capítulos pelos marcadores
  datas.py                  # data dos arquivos (filtro por data de adição)
  elegibilidade.py          # grau de incorporação + pastas + IA (casos em dúvida)
  fichamentos.py            # cruzamento livro ↔ fichamento (nome aproximado)
  catalogo.py               # catálogo editável (Seção 8): campos por registro
  importacao.py             # importa lista de títulos mapeados do RAIP
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
- **Tenho EPUB/MOBI também.** Hoje o app lê `.docx` e PDF. Suporte a EPUB/MOBI dá para adicionar; me avise.
- **Quero acessar o OneDrive sem sincronizar (via nuvem).** É possível usar a API Microsoft Graph
  (conta pessoal). Como exige registrar um app no Azure e autenticar, o caminho padrão aqui é a
  pasta sincronizada (mais simples). Me avise se preferir o acesso via nuvem.
