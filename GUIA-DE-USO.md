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

## Parte 8 — Ligar a IA para decidir os casos "em dúvida"

Quando as regras automáticas **não conseguem** decidir o grau de um livro
(o título não tem palavras-chave, ou é um PDF escaneado), o programa pede ajuda
à inteligência artificial. Há **dois caminhos** — escolha **um**.

### ⭐ Caminho A (recomendado p/ você): usar o seu plano Max — sem custo extra

Você já paga o **plano Max**, e ele inclui o **Claude Code**. O programa pode
usar o Claude Code para decidir as dúvidas, **sem chave de API e sem custo
adicional**. Só precisa instalar o Claude Code no seu PC, uma vez.

1. **Instalar o Node.js** (necessário para instalar o Claude Code):
   - Acesse **https://nodejs.org** e baixe a versão **LTS**.
   - Instale (pode avançar com as opções padrão).
2. **Instalar o Claude Code**:
   - Abra o **PowerShell** (aperte a tecla Windows, digite `PowerShell`, Enter).
   - Cole este comando e aperte Enter:
     ```
     npm install -g @anthropic-ai/claude-code
     ```
   - Espere terminar. (Há também um instalador alternativo na documentação
     oficial: https://docs.claude.com/claude-code .)
3. **Fazer login com sua conta Max**:
   - Ainda no PowerShell, digite `claude` e aperte Enter.
   - Vai abrir o navegador para você **entrar com a mesma conta do seu Max**.
   - Depois de logar, pode fechar (digite `/exit` e Enter, ou feche a janela).
4. **No programa**: deixe marcado **"Usar meu plano Max"** e clique em
   **🔎 Analisar biblioteca**. Pronto — as dúvidas serão decididas usando o Max.

> ⏳ Com muitas dúvidas, essa etapa pode levar **alguns minutos** (cada livro é
> uma consulta). Os resultados ficam em cache: da segunda vez é instantâneo.
> Se aparecer o aviso *"Claude Code não encontrado"*, refaça os passos 2 e 3.

### Caminho B (alternativa): usar uma chave de API (cobrança por uso)

Se preferir não instalar o Claude Code, dá para usar uma **chave de API**. Tem
um **custo baixo** (alguns centavos para a biblioteca toda; mínimo de crédito de
~US$ 5 ao criar a conta).

1. Acesse **https://console.anthropic.com**, crie a conta e, em **"Billing"**,
   adicione um crédito.
2. Em **"API Keys"** → **"Create Key"**, **copie** a chave (`sk-ant-...`).
   ⚠️ Ela só aparece uma vez.
3. No programa, escolha **"Usar chave de API"**, **cole** a chave no campo e
   deixe **"Guardar para as próximas vezes"** marcado. Analise de novo.

> 🔒 Em ambos os casos, nada disso sai do seu computador. A chave (caminho B)
> fica num arquivo `.env` local e nunca vai para o GitHub nem para mim.

---

## ❗ Se algo der errado

| Problema | O que fazer |
|---|---|
| "Python não encontrado" na janela preta | Refaça a Parte 1 e **marque "Add Python to PATH"**. |
| **`claude` "não é reconhecido"** no PowerShell | **Feche e reabra o PowerShell** (o atalho só vale em janelas novas). Se persistir: confira `npm --version`; reinstale o Node (LTS) e reinicie; ou use o instalador nativo `irm https://claude.ai/install.ps1 \| iex`. |
| **npm:** *"execução de scripts foi desabilitada"* / `UnauthorizedAccess` | O Windows bloqueia scripts. Rode `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (confirme com **S**) e instale de novo. Alternativa: use `npm.cmd install -g @anthropic-ai/claude-code`. |
| Ao rodar `claude`, ele pede uma **API key** | Você escolheu a opção errada de login. Rode `claude` de novo e selecione a opção da **conta/assinatura (Pro/Max)**, não a de API. |
| O **app** pede chave mesmo no modo Max | No modo **"Usar meu plano Max"** não é preciso chave. Se o app insiste, o `claude` ainda não está instalado/logado — finalize a Parte 8. Se você nem vê a opção "Usar meu plano Max", **rebaixe o programa** (Parte 2). |
| O navegador não abriu sozinho | Digite **http://127.0.0.1:5000** na barra do navegador. |
| "Pasta de livros não encontrada" | Confira se colou o caminho certo (Parte 3). |
| Um livro fichado aparece como "Não" | Ajuste o **"Rigor do casamento"** ou renomeie o fichamento. |
| Aviso azul do Windows ao abrir o .bat | "Mais informações" → "Executar assim mesmo". |

Qualquer dúvida, me chame que eu te oriento. 🙂
