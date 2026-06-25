"use strict";

let LINHAS = [];      // resultado da análise
let DETALHES = {};    // capítulos por arquivo
let CAT = null;       // {colunas, registros, opcoes, auto}

const $ = (id) => document.getElementById(id);

function badgeGrau(g) {
  const m = { "1": "b1", "2": "b2", "3": "b3" };
  let cls = "bduv";
  if (g.includes("Irrelev")) cls = "birr";
  else if (g.includes("Potenc") || g.includes("vida")) cls = "bduv";
  else if (g[0] in m) cls = m[g[0]];
  else if (g.includes("lista")) cls = "b1";
  return `<span class="badge ${cls}">${g || "—"}</span>`;
}

async function postJSON(url, dados) {
  const r = await fetch(url, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(j.erro || "Erro na requisição");
  return j;
}

// ---------------------------------------------------------------- Análise
let POLL = null;

async function analisar() {
  const status = $("status");
  $("btn-analisar").disabled = true;
  $("progresso-wrap").classList.remove("oculto");
  try {
    const chave = ($("chave_ia") && $("chave_ia").value) || "";
    const backend = document.querySelector('input[name="backend"]:checked').value;
    await postJSON("/analisar", {
      pasta_livros: $("pasta_livros").value,
      pasta_fichamentos: $("pasta_fichamentos").value,
      data_corte: $("data_corte").value,
      limiar_fichamento: $("limiar_fichamento").value,
      usar_ia: $("usar_ia").checked,
      usar_cache: $("usar_cache").checked,
      modo_ia_total: $("modo_ia_total").checked,
      backend: backend,
      chave_ia: chave,
      salvar_chave: $("salvar_chave") && $("salvar_chave").checked,
    });
    status.textContent = "Lendo a biblioteca livro a livro…";
    POLL = setInterval(checarProgresso, 1500);
  } catch (e) {
    status.textContent = "⚠️ " + e.message;
    $("btn-analisar").disabled = false;
    $("progresso-wrap").classList.add("oculto");
  }
}

async function checarProgresso() {
  let p;
  try { p = await (await fetch("/progresso")).json(); }
  catch (e) { return; }

  if (p.total) {
    const pct = Math.round((p.i / p.total) * 100);
    $("barra-fill").style.width = pct + "%";
    $("progresso-texto").textContent =
      `Lendo ${p.i} de ${p.total} (${pct}%) — ${p.atual}`;
  }

  if (!p.rodando) {
    clearInterval(POLL); POLL = null;
    $("btn-analisar").disabled = false;
    if (p.erro) {
      $("status").textContent = "⚠️ " + p.erro;
      $("progresso-wrap").classList.add("oculto");
      return;
    }
    if (p.pronto) {
      const j = p.resultado;
      LINHAS = j.linhas; DETALHES = j.detalhes;
      mostrarAvisos(j.avisos || []);
      mostrarResumo(j.resumo);
      montarFiltroGraus(j.resumo.graus);
      renderTabela();
      CAT = null;
      $("tabela-cat").querySelector("tbody").innerHTML = "";
      $("tabela-cat").querySelector("thead").innerHTML = "";
      ["resumo", "sec-resultado", "sec-catalogo"].forEach((s) => $(s).classList.remove("oculto"));
      $("barra-fill").style.width = "100%";
      $("status").textContent = `✓ ${j.resumo.total} livro(s) catalogado(s).`;
      $("progresso-wrap").classList.add("oculto");
    }
  }
}

function mostrarAvisos(avisos) {
  const box = $("avisos");
  if (!avisos.length) { box.classList.add("oculto"); box.innerHTML = ""; return; }
  box.innerHTML = avisos.map((a) => `<div class="aviso">⚠️ ${esc(a)}</div>`).join("");
  box.classList.remove("oculto");
}

function mostrarResumo(r) {
  $("m-total").textContent = r.total;
  $("m-eleg").textContent = r.elegiveis;
  $("m-fich").textContent = r.fichados;
  $("m-falta").textContent = r.falta_fichar;
  $("m-duvida").textContent = r.duvidas != null ? r.duvidas : 0;
  $("m-ia").textContent = r.ia_usada != null ? r.ia_usada : 0;
  const cores = { "1": "var(--g1)", "2": "var(--g2)", "3": "var(--g3)" };
  const barra = $("graus-barra"); barra.innerHTML = "";
  Object.entries(r.graus).sort().forEach(([g, n]) => {
    let cor = "#8d99ae";
    if (g.includes("Irrelev")) cor = "var(--girr)";
    else if (g[0] in cores) cor = cores[g[0]];
    const el = document.createElement("span");
    el.className = "gbloco"; el.style.background = cor;
    el.style.color = g[0] === "3" ? "#5b4a1a" : "#fff";
    el.textContent = `${g}: ${n}`;
    barra.appendChild(el);
  });
}

function montarFiltroGraus(graus) {
  const sel = $("f-grau");
  sel.innerHTML = '<option value="">Todos os graus</option>';
  Object.keys(graus).sort().forEach((g) => {
    if (!g || g === "-") return;
    const o = document.createElement("option"); o.value = g; o.textContent = g;
    sel.appendChild(o);
  });
}

function renderTabela() {
  const soEleg = $("f-eleg").checked, soFalta = $("f-falta").checked;
  const grau = $("f-grau").value, busca = $("f-busca").value.toLowerCase();
  const tb = $("tabela").querySelector("tbody");
  tb.innerHTML = "";
  LINHAS.filter((l) => {
    if (soEleg && l["Elegível"] !== "Sim") return false;
    if (soFalta && l["Fichado?"] !== "Não") return false;
    if (grau && l["Grau"] !== grau) return false;
    if (busca && !(l["Livro"] || "").toLowerCase().includes(busca)) return false;
    return true;
  }).forEach((l) => {
    const tr = document.createElement("tr");
    const fich = l["Fichado?"];
    const fichHTML = fich === "Sim" ? '<span class="sim">✓ Sim</span>'
      : fich === "Não" ? '<span class="nao">✗ Não</span>' : "—";
    tr.innerHTML = `
      <td><strong>${esc(l["Livro"])}</strong><br><small>${esc(l["Arquivo"])}</small></td>
      <td>${badgeGrau(l["Grau"] || "")}</td>
      <td>${esc(l["Pastas temáticas"] || "—")}</td>
      <td>${l["Nº Capítulos"]}</td>
      <td>${fichHTML}</td>
      <td>${esc(l["Adicionado em"] || "")}</td>
      <td><small>${esc(l["Motivo"] || "")}</small></td>`;
    tb.appendChild(tr);
  });
}

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// ---------------------------------------------------------------- Catálogo
async function carregarCatalogo() {
  $("cat-status").textContent = "Montando…";
  try {
    CAT = await postJSON("/catalogo/dados", { caminho: $("cat_caminho").value });
    renderCatalogo();
    $("cat-status").textContent = `${CAT.registros.length} registro(s).`;
  } catch (e) { $("cat-status").textContent = "⚠️ " + e.message; }
}

function renderCatalogo() {
  const thead = $("tabela-cat").querySelector("thead");
  const tbody = $("tabela-cat").querySelector("tbody");
  thead.innerHTML = "<tr>" + CAT.colunas.map((c) => `<th>${esc(c)}</th>`).join("") + "</tr>";
  tbody.innerHTML = "";
  CAT.registros.forEach((reg, i) => {
    const tr = document.createElement("tr");
    CAT.colunas.forEach((col) => {
      const td = document.createElement("td");
      const auto = CAT.auto.includes(col);
      if (auto) td.className = "auto";
      const val = reg[col] == null ? "" : reg[col];
      if (col === "Arquivo") {
        td.innerHTML = `<input data-i="${i}" data-c="${esc(col)}" value="${esc(val)}" readonly>`;
      } else if (CAT.opcoes[col]) {
        const ops = CAT.opcoes[col].map((o) =>
          `<option ${o === val ? "selected" : ""}>${esc(o)}</option>`).join("");
        td.innerHTML = `<select data-i="${i}" data-c="${esc(col)}">${ops}</select>`;
      } else {
        td.innerHTML = `<input data-i="${i}" data-c="${esc(col)}" value="${esc(val)}">`;
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

function coletarCatalogo() {
  $("tabela-cat").querySelectorAll("input,select").forEach((el) => {
    CAT.registros[el.dataset.i][el.dataset.c] = el.value;
  });
  return CAT.registros;
}

async function salvarCatalogo() {
  if (!CAT) { $("cat-status").textContent = "Monte o catálogo primeiro."; return; }
  try {
    const j = await postJSON("/catalogo/salvar", {
      caminho: $("cat_caminho").value, registros: coletarCatalogo(),
    });
    $("cat-status").textContent = `💾 Salvo: ${j.caminho} (${j.n} registros).`;
  } catch (e) { $("cat-status").textContent = "⚠️ " + e.message; }
}

// ---------------------------------------------------------------- Importar
async function importar() {
  try {
    const j = await postJSON("/importar", {
      texto: $("imp_texto").value, salvar_eleitos: $("imp_eleitos").checked,
    });
    $("imp-status").textContent =
      `${j.n} título(s) reconhecido(s)` + (j.salvo ? " — salvos como eleitos. Reanalise." : ".");
  } catch (e) { $("imp-status").textContent = "⚠️ " + e.message; }
}

// ---------------------------------------------------------------- Eventos
$("btn-analisar").addEventListener("click", analisar);
$("btn-carregar-cat").addEventListener("click", carregarCatalogo);
$("btn-salvar-cat").addEventListener("click", salvarCatalogo);
$("btn-importar").addEventListener("click", importar);
["f-eleg", "f-falta", "f-grau", "f-busca"].forEach((id) =>
  $(id).addEventListener("input", renderTabela));

// Mostra o campo da chave só quando o modo "API" estiver selecionado.
function alternarChave() {
  const backend = document.querySelector('input[name="backend"]:checked').value;
  $("bloco-chave").classList.toggle("oculto", backend !== "api");
}
document.querySelectorAll('input[name="backend"]').forEach((r) =>
  r.addEventListener("change", alternarChave));
alternarChave();
