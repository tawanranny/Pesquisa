# 📖 Guia de uso — do zero, passo a passo

Este guia assume que você **nunca usou** programação, terminal ou GitHub.
Siga na ordem. Você faz isto **uma vez**; depois, abrir o programa é só um
clique duplo.

> 💻 Este guia é para **Windows** (que é o seu caso). O programa roda **no seu
> computador**, porque é lá que está a pasta do OneDrive com os livros.

---

## Parte 1 — Instalar o Python (uma vez só)

O "Python" é o motor que faz o programa funcionar.

1. Abra o site: **https://www.python.org/downloads/**
2. Clique no botão amarelo **"Download Python 3.x"**.
3. Abra o arquivo que baixou (fica em "Downloads", nome tipo `python-3.x.x.exe`).
4. ⚠️ **MUITO IMPORTANTE:** na primeira tela, **marque a caixinha embaixo**
   que diz **"Add Python to PATH"** (ou "Adicionar Python ao PATH").
   Sem isso, não funciona.
5. Clique em **"Install Now"** e espere terminar. Pode clicar em "Close" no fim.

✅ Pronto. Você não precisa abrir o Python — ele só precisa estar instalado.

---

## Parte 2 — Baixar o programa (uma vez só)

1. Abra este endereço no navegador (é o seu repositório, na versão do app):
   **https://github.com/tawanranny/pesquisa/tree/claude/peaceful-shannon-i074v6**
2. Clique no botão verde **"Code"** (fica à direita, acima da lista de arquivos).
3. No menu que abrir, clique em **"Download ZIP"**.
4. Vá em "Downloads", clique com o **botão direito** no arquivo `.zip` baixado e
   escolha **"Extrair tudo..."** → **"Extrair"**.
5. Vai aparecer uma pasta com os arquivos do programa (com `Iniciar-RAIP.bat`,
   `servidor.py`, etc.). **Mova essa pasta para um lugar fácil**, por exemplo a
   sua Área de Trabalho. Pode renomeá-la para `Pesquisa-RAIP`.

> 💡 Dica: deixe essa pasta sempre no mesmo lugar. É dela que você vai abrir o
> programa de agora em diante.

---

## Parte 3 — Organizar suas pastas no OneDrive (uma vez só)

O programa precisa de **duas pastas** no seu OneDrive:

1. Uma pasta só com os **livros** (arquivos `.pdf` ou `.docx`).
2. Uma pasta só com os **fichamentos** (também `.pdf` ou `.docx`).

Se já estão assim, ótimo. Se estão tudo junto, separe em duas pastas.

### Como descobrir o "caminho" de uma pasta (você vai precisar colar isso)

1. Abra o **Explorador de Arquivos** e navegue até a pasta dos livros.
2. Clique uma vez na **barra de endereço** lá em cima (a faixa que mostra o
   caminho da pasta). Ela vai ficar selecionada/azul.
3. Aperte **Ctrl + C** para copiar.
4. Guarde — você vai colar isso no programa. Faça o mesmo para a pasta de
   fichamentos.

> O caminho se parece com:
> `C:\Users\Tawan\OneDrive\Pesquisa\livros`

---

## Parte 4 — Abrir o programa (toda vez que for usar)

1. Entre na pasta do programa (ex.: `Pesquisa-RAIP` na Área de Trabalho).
2. Dê **dois cliques** no arquivo **`Iniciar-RAIP.bat`**.
   - Vai abrir uma **janela preta** com textos. É normal! Não feche.
   - Na primeira vez, ela demora alguns minutos (está instalando as peças).
   - Se aparecer um aviso do Windows ("Windows protegeu o computador"),
     clique em **"Mais informações"** → **"Executar assim mesmo"**.
3. Em poucos segundos, o seu **navegador abre sozinho** com o programa.
   (Se não abrir, digite no navegador: **http://127.0.0.1:5000**)

> ⛔ **Para fechar o programa quando terminar:** feche a **janela preta**.

---

## Parte 5 — Usar o programa

Na tela do navegador:

1. No campo **"Pasta de livros"**, cole (Ctrl + V) o caminho que você copiou.
2. No campo **"Pasta de fichamentos"**, cole o caminho da outra pasta.
3. Confira a **"data de corte"**. Já vem **01/07/2025** (2.º semestre de 2025):
   o programa só cataloga livros **adicionados a partir dessa data**. Pode mudar
   se quiser.
4. Clique em **"🔎 Analisar biblioteca"** e aguarde.
   - Ele vai abrir **cada livro, um por um**, ler os capítulos e classificar.
   - PDFs escaneados podem demorar mais (veja a Parte 7).
5. Aparecem:
   - **Resumo**: total, elegíveis, já fichados, falta fichar;
   - **Tabela**: cada livro com **grau**, **pastas temáticas**, **capítulos** e
     se está **fichado**;
   - **Catálogo (Seção 8)**: a planilha editável (veja a Parte 6);
   - botões para **baixar Excel** e **relatório**.

---

## Parte 6 — Comparação com os fichamentos e o catálogo

### Ele compara com a pasta de fichamentos? **Sim.**

Para cada livro elegível, o programa procura na **pasta de fichamentos** um
arquivo de nome parecido. Se encontra, marca **Fichado? = Sim** e mostra qual
fichamento casou e o **% de semelhança**. Se não encontra, marca **Não**
(é o que você ainda precisa fichar).

> 💡 Para o casamento funcionar bem, **nomeie o fichamento parecido com o livro**.
> Ex.: livro `Direito do Mar - Tanaka.pdf` → fichamento
> `Fichamento Direito do Mar - Tanaka.docx`. Palavras como "fichamento",
> "resumo" e acentos são ignoradas automaticamente. Se algum livro fichado
> aparecer como "Não", aumente ou diminua o **"Rigor do casamento"** na tela.

### O catálogo (Seção 8)

- Os campos **automáticos** (referência, grau, pastas, fichado) já vêm
  preenchidos — aparecem em **cinza**.
- Você edita o resto direto na tabela: autor, ano, idioma, **capítulo(s) de
  incidência**, pendências, etc.
- Clique em **"💾 Salvar catálogo"**. Ele grava um arquivo `catalogo_raip.csv`.
- Quando você **reanalisar** depois, os livros novos entram e **suas edições
  continuam lá** (só os campos em branco recebem valores automáticos).

---

## Parte 7 — (Opcional) Ler PDFs escaneados (OCR)

Se alguns livros forem **escaneados** (imagem, sem texto selecionável), o
programa precisa de dois acessórios para "enxergar" o texto. **Só faça isto se
tiver PDFs escaneados.**

1. **Tesseract** (com português): baixe em
   https://github.com/UB-Mannheim/tesseract/wiki — na instalação, marque o
   idioma **Portuguese**.
2. **Poppler**: baixe o "poppler-windows" (Release) em
   https://github.com/oschwartz10612/poppler-windows/releases — extraia e
   anote a pasta.

Sem isso, PDFs escaneados aparecem como **"pdf-sem-texto"**: ainda são
classificados pelo **título**, mas o conteúdo não é lido. (Se ficar complicado,
me avise que eu simplifico esse passo.)

---

## ❗ Se algo der errado

| Problema | O que fazer |
|---|---|
| "Python não encontrado" na janela preta | Refaça a Parte 1 e **marque "Add Python to PATH"**. |
| O navegador não abriu sozinho | Digite **http://127.0.0.1:5000** na barra do navegador. |
| "Pasta de livros não encontrada" | Confira se colou o caminho certo (Parte 3). |
| Um livro fichado aparece como "Não" | Ajuste o **"Rigor do casamento"** ou renomeie o fichamento. |
| Aviso azul do Windows ao abrir o .bat | "Mais informações" → "Executar assim mesmo". |

Qualquer dúvida, me chame que eu te oriento. 🙂
