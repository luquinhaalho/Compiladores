const MENSAGEM_VAZIA = "Informe um código-fonte antes de solicitar a análise.";
const MENSAGEM_BRANCO =
  "Não há conteúdo útil para analisar. Informe um programa antes de continuar.";
const MENSAGEM_COMUNICACAO =
  "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.";
const MENSAGEM_INESPERADO =
  "Ocorreu um erro inesperado ao processar o código. Tente novamente.";
const MENSAGEM_INICIAL = "O resultado da solicitação aparece aqui.";

const ROTULOS = {
  PALAVRA_RESERVADA: "Palavra reservada",
  IDENTIFICADOR: "Identificador",
  LITERAL_INTEIRO: "Literal inteiro",
  LITERAL_REAL: "Literal real",
  OPERADOR: "Operador",
  DELIMITADOR: "Delimitador",
  ERRO_LEXICO: "Erro léxico",
};

const formEl = document.getElementById("form-analise");
const exemploEl = document.getElementById("exemplo");
const notaEl = document.getElementById("exemplo-nota");
const codigoEl = document.getElementById("codigo");
const botaoEl = document.getElementById("analisar");
const resultadoEl = document.getElementById("resultado");
const detalheEl = document.getElementById("resultado-detalhe");
const painelEl = document.getElementById("painel-lexico");
const contagemEl = document.getElementById("contagem");
const coloridoEl = document.getElementById("codigo-colorido");
const corpoEl = document.getElementById("tokens-corpo");
const errosEl = document.getElementById("erros-lexicos");
const passoTextoEl = document.getElementById("passo-texto");
const passoAnteriorEl = document.getElementById("passo-anterior");
const passoProximoEl = document.getElementById("passo-proximo");
const painelSintaticoEl = document.getElementById("painel-sintatico");
const statusSintaticoEl = document.getElementById("status-sintatico");
const arvoreEl = document.getElementById("arvore-ast");
const astTextualEl = document.getElementById("ast-textual");
const errosSintaticosEl = document.getElementById("erros-sintaticos");
const expandirAstEl = document.getElementById("expandir-ast");
const recolherAstEl = document.getElementById("recolher-ast");
const exportarAstEl = document.getElementById("exportar-ast");
const explicarNoEl = document.getElementById("explicar-no");
const explicarErroSintaticoEl = document.getElementById("explicar-erro-sintatico");
const explicarTokenEl = document.getElementById("explicar-token");
const perguntaIaEl = document.getElementById("pergunta-ia");
const perguntarIaEl = document.getElementById("perguntar-ia");
const statusIaEl = document.getElementById("status-ia");
const respostaIaEl = document.getElementById("resposta-ia");

let exemplos = [];
let itensPasso = [];
let passoAtual = -1;
let codigoAtual = "";
let astAtual = null;
let noSelecionado = null;
let ultimaAnalise = null;
let errosSintaticosAtuais = [];
let iaOcupada = false;

function mostrarResultado(texto, tipo, detalhe) {
  resultadoEl.textContent = texto;
  resultadoEl.classList.remove("is-ok", "is-error");
  if (tipo === "ok") {
    resultadoEl.classList.add("is-ok");
  } else if (tipo === "erro") {
    resultadoEl.classList.add("is-error");
  }
  detalheEl.textContent = detalhe || "";
}

function limparPainel() {
  painelEl.hidden = true;
  painelSintaticoEl.hidden = true;
  itensPasso = [];
  passoAtual = -1;
  codigoAtual = "";
  astAtual = null;
  noSelecionado = null;
  contagemEl.replaceChildren();
  coloridoEl.replaceChildren();
  corpoEl.replaceChildren();
  errosEl.replaceChildren();
  passoTextoEl.textContent = "";
  arvoreEl.replaceChildren();
  astTextualEl.textContent = "";
  errosSintaticosEl.replaceChildren();
  statusSintaticoEl.textContent = "";
  ultimaAnalise = null;
  errosSintaticosAtuais = [];
  statusIaEl.textContent = "";
  respostaIaEl.hidden = true;
  respostaIaEl.textContent = "";
}

function rotulo(tipo) {
  return ROTULOS[tipo] || tipo;
}

function indiceDaPosicao(codigo, linha, coluna) {
  let indice = 0;
  let linhaAtual = 1;
  let colunaAtual = 1;
  while (indice < codigo.length) {
    if (linhaAtual === linha && colunaAtual === coluna) {
      return indice;
    }
    const caractere = codigo[indice];
    if (caractere === "\r") {
      indice += codigo[indice + 1] === "\n" ? 2 : 1;
      linhaAtual += 1;
      colunaAtual = 1;
      continue;
    }
    if (caractere === "\n") {
      indice += 1;
      linhaAtual += 1;
      colunaAtual = 1;
      continue;
    }
    indice += 1;
    colunaAtual += 1;
  }
  if (linhaAtual === linha && colunaAtual === coluna) {
    return codigo.length;
  }
  return -1;
}

function acrescentarTexto(texto) {
  if (!texto) {
    return;
  }
  coloridoEl.append(document.createTextNode(texto));
}

function destacar(codigo) {
  coloridoEl.replaceChildren();
  const marcas = itensPasso
    .map((item, indice) => ({
      item,
      indice,
      inicio: indiceDaPosicao(codigo, item.linha, item.coluna),
    }))
    .filter((marca) => marca.inicio >= 0)
    .sort((a, b) => a.inicio - b.inicio);

  let cursor = 0;
  for (const marca of marcas) {
    if (marca.inicio < cursor) {
      continue;
    }
    acrescentarTexto(codigo.slice(cursor, marca.inicio));
    const fim = marca.inicio + marca.item.lexema.length;
    const trecho = document.createElement("span");
    trecho.className =
      marca.item.tipo === "ERRO_LEXICO" ? "tok-erro" : "tok-" + marca.item.tipo;
    trecho.dataset.passo = String(marca.indice);
    trecho.textContent = codigo.slice(marca.inicio, Math.min(fim, codigo.length));
    coloridoEl.append(trecho);
    cursor = Math.min(fim, codigo.length);
  }
  acrescentarTexto(codigo.slice(cursor));
}

function preencherContagem(tokens) {
  contagemEl.replaceChildren();
  const totais = new Map();
  for (const token of tokens) {
    totais.set(token.tipo, (totais.get(token.tipo) || 0) + 1);
  }
  const total = document.createElement("li");
  total.textContent = tokens.length + (tokens.length === 1 ? " token" : " tokens");
  contagemEl.append(total);
  for (const [tipo, quantidade] of totais) {
    const item = document.createElement("li");
    item.textContent = quantidade + " " + rotulo(tipo).toLowerCase();
    contagemEl.append(item);
  }
}

function preencherTabela(tokens) {
  corpoEl.replaceChildren();
  if (tokens.length === 0) {
    const linha = document.createElement("tr");
    const celula = document.createElement("td");
    celula.colSpan = 5;
    celula.textContent = "Nenhum token reconhecido.";
    linha.append(celula);
    corpoEl.append(linha);
    return;
  }
  for (const token of tokens) {
    const linha = document.createElement("tr");
    linha.dataset.passo = String(itensPasso.indexOf(token));
    for (const valor of [rotulo(token.tipo), token.lexema, token.linha, token.coluna]) {
      const celula = document.createElement("td");
      celula.textContent = String(valor);
      linha.append(celula);
    }
    const acao = document.createElement("td");
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "btn-ia";
    botao.textContent = "Explicar";
    botao.addEventListener("click", () => explicarToken(token));
    acao.append(botao);
    linha.append(acao);
    corpoEl.append(linha);
  }
}

function preencherErros(erros) {
  errosEl.replaceChildren();
  if (erros.length === 0) {
    const item = document.createElement("li");
    item.textContent = "Nenhum erro léxico nesta análise.";
    errosEl.append(item);
    return;
  }
  for (const erro of erros) {
    const item = document.createElement("li");
    item.dataset.passo = String(itensPasso.indexOf(erro));
    item.textContent = erro.mensagem;
    errosEl.append(item);
  }
}

function atualizarPasso() {
  coloridoEl.querySelectorAll(".is-current").forEach((elemento) => {
    elemento.classList.remove("is-current");
  });
  corpoEl.querySelectorAll(".is-current").forEach((elemento) => {
    elemento.classList.remove("is-current");
  });
  errosEl.querySelectorAll(".is-current").forEach((elemento) => {
    elemento.classList.remove("is-current");
  });

  if (passoAtual < 0 || itensPasso.length === 0) {
    passoTextoEl.textContent = "Não há tokens para percorrer.";
    passoAnteriorEl.disabled = true;
    passoProximoEl.disabled = true;
    return;
  }

  const item = itensPasso[passoAtual];
  passoTextoEl.textContent =
    "Passo " +
    (passoAtual + 1) +
    " de " +
    itensPasso.length +
    ": o scanner encontrou o lexema " +
    item.lexema +
    " e classificou como " +
    rotulo(item.tipo).toLowerCase() +
    ", na linha " +
    item.linha +
    ", coluna " +
    item.coluna +
    ".";
  passoAnteriorEl.disabled = passoAtual === 0;
  passoProximoEl.disabled = passoAtual === itensPasso.length - 1;

  const seletor = '[data-passo="' + passoAtual + '"]';
  coloridoEl.querySelectorAll(seletor).forEach((elemento) => {
    elemento.classList.add("is-current");
  });
  corpoEl.querySelectorAll(seletor).forEach((elemento) => {
    elemento.classList.add("is-current");
  });
  errosEl.querySelectorAll(seletor).forEach((elemento) => {
    elemento.classList.add("is-current");
  });
}

function rotuloNo(no) {
  const atr = no.atributos || {};
  if (atr.nome) {
    return atr.nome;
  }
  if (atr.valor !== undefined) {
    return String(atr.valor);
  }
  if (atr.operador) {
    return atr.operador;
  }
  if (atr.tipoDado) {
    return atr.tipoDado + " " + (atr.nome || "");
  }
  return "";
}

function textoAst(no, nivel) {
  const indent = "  ".repeat(nivel);
  const extra = rotuloNo(no);
  let linha = indent + no.tipo;
  if (extra) {
    linha += ": " + extra;
  }
  linha += "\n";
  for (const filho of no.filhos || []) {
    linha += textoAst(filho, nivel + 1);
  }
  return linha;
}

function destacarTrechoNo(no) {
  coloridoEl.querySelectorAll(".is-ast-selected").forEach((el) => {
    el.classList.remove("is-ast-selected");
  });
  if (!no || !codigoAtual) {
    return;
  }
  const inicio = indiceDaPosicao(codigoAtual, no.linha, no.coluna);
  if (inicio < 0) {
    return;
  }
  const fimLinha = no.linhaFim || no.linha;
  const fimColuna = no.colunaFim || no.coluna;
  let fim = indiceDaPosicao(codigoAtual, fimLinha, fimColuna);
  if (fim < 0) {
    fim = inicio;
  } else {
    fim += 1;
  }
  const spans = coloridoEl.querySelectorAll("span");
  let cursor = 0;
  for (const noTexto of coloridoEl.childNodes) {
    if (noTexto.nodeType === Node.TEXT_NODE) {
      cursor += noTexto.textContent.length;
      continue;
    }
    if (noTexto.nodeType === Node.ELEMENT_NODE) {
      const tamanho = noTexto.textContent.length;
      const spanInicio = cursor;
      const spanFim = cursor + tamanho;
      if (spanFim > inicio && spanInicio < fim) {
        noTexto.classList.add("is-ast-selected");
      }
      cursor = spanFim;
    }
  }
  spans.length;
}

function selecionarNo(no, botao) {
  noSelecionado = no;
  arvoreEl.querySelectorAll(".no-ast").forEach((el) => {
    el.classList.remove("is-selected");
  });
  if (botao) {
    botao.classList.add("is-selected");
  }
  destacarTrechoNo(no);
  if (no && no.regra) {
    statusSintaticoEl.textContent =
      "Nó " +
      no.tipo +
      " (linha " +
      no.linha +
      ", coluna " +
      no.coluna +
      "). Regra: " +
      no.regra;
  }
}

function criarItemArvore(no) {
  const item = document.createElement("li");
  item.setAttribute("role", "treeitem");
  const botao = document.createElement("button");
  botao.type = "button";
  botao.className = "no-ast no-" + no.tipo;
  const badge = document.createElement("span");
  badge.className = "badge";
  badge.textContent = no.tipo;
  botao.append(badge);
  const extra = rotuloNo(no);
  if (extra) {
    botao.append(document.createTextNode(" " + extra));
  }
  botao.append(
    document.createTextNode("  L" + no.linha + ":C" + no.coluna)
  );
  botao.addEventListener("click", () => selecionarNo(no, botao));
  item.append(botao);

  if (no.filhos && no.filhos.length) {
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "passo";
    toggle.style.margin = "0 0 0 0.25rem";
    toggle.style.padding = "0.15rem 0.45rem";
    toggle.textContent = "−";
    const filhos = document.createElement("ul");
    filhos.setAttribute("role", "group");
    for (const filho of no.filhos) {
      filhos.append(criarItemArvore(filho));
    }
    toggle.addEventListener("click", () => {
      const oculto = filhos.hidden;
      filhos.hidden = !oculto;
      toggle.textContent = oculto ? "−" : "+";
    });
    item.insertBefore(toggle, botao);
    item.append(filhos);
  }
  return item;
}

function renderizarAst(ast) {
  arvoreEl.replaceChildren();
  astTextualEl.textContent = "";
  if (!ast) {
    return;
  }
  arvoreEl.append(criarItemArvore(ast));
  astTextualEl.textContent = textoAst(ast, 0).trimEnd();
}

function preencherErrosSintaticos(erros) {
  errosSintaticosAtuais = erros || [];
  errosSintaticosEl.replaceChildren();
  if (!erros || erros.length === 0) {
    const item = document.createElement("li");
    item.textContent = "Nenhum erro sintático nesta análise.";
    errosSintaticosEl.append(item);
    return;
  }
  for (const erro of erros) {
    const item = document.createElement("li");
    item.textContent = erro.mensagem;
    errosSintaticosEl.append(item);
  }
}

async function solicitarExplicacao(tipo, pergunta, contexto) {
  if (iaOcupada) {
    return;
  }
  iaOcupada = true;
  statusIaEl.textContent = "Consultando o Ollama (Llama 3.2)…";
  respostaIaEl.hidden = true;
  respostaIaEl.textContent = "";
  perguntarIaEl.disabled = true;
  explicarNoEl.disabled = true;
  explicarTokenEl.disabled = true;
  explicarErroSintaticoEl.disabled = true;
  try {
    const resposta = await fetch("/api/ia/explicar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tipo,
        pergunta,
        codigo: codigoAtual,
        contexto: contexto || null,
      }),
    });
    let dados = null;
    try {
      dados = await resposta.json();
    } catch (_erro) {
      dados = null;
    }
    if (!dados || typeof dados.mensagem !== "string") {
      statusIaEl.textContent = MENSAGEM_COMUNICACAO;
      return;
    }
    statusIaEl.textContent = dados.mensagem;
    if (dados.sucesso && dados.explicacao) {
      respostaIaEl.hidden = false;
      respostaIaEl.textContent = dados.explicacao;
    }
  } catch (_erro) {
    statusIaEl.textContent = MENSAGEM_COMUNICACAO;
  } finally {
    iaOcupada = false;
    perguntarIaEl.disabled = false;
    explicarNoEl.disabled = false;
    explicarTokenEl.disabled = false;
    explicarErroSintaticoEl.disabled = false;
  }
}

function explicarToken(token) {
  const pergunta =
    "Explique o que é um " +
    rotulo(token.tipo).toLowerCase() +
    " na linguagem analisada e a função do lexema '" +
    token.lexema +
    "' no código apresentado.";
  solicitarExplicacao("TOKEN", pergunta, {
    token,
    tokens: ultimaAnalise ? ultimaAnalise.tokens : [],
  });
}

function explicarNoSelecionado() {
  if (!noSelecionado) {
    statusIaEl.textContent =
      "Selecione um nó da AST antes de pedir a explicação à IA.";
    return;
  }
  const pergunta =
    "Explique o nó " +
    noSelecionado.tipo +
    " da AST e como ele se relaciona com os filhos e com o código-fonte.";
  solicitarExplicacao("AST", pergunta, {
    no: noSelecionado,
    ast: astAtual,
    tokens: ultimaAnalise ? ultimaAnalise.tokens : [],
  });
}

function explicarErroSintatico() {
  if (!errosSintaticosAtuais.length) {
    statusIaEl.textContent = "Não há erro sintático nesta análise para explicar.";
    return;
  }
  const erro = errosSintaticosAtuais[0];
  const pergunta =
    "Explique este erro sintático do parser, a regra gramatical envolvida e como corrigir o código.";
  solicitarExplicacao("ERRO_SINTATICO", pergunta, {
    erro,
    tokens: ultimaAnalise ? ultimaAnalise.tokens : [],
  });
}

function renderizarSintatico(sintatico) {
  painelSintaticoEl.hidden = false;
  if (!sintatico || sintatico.executado === false) {
    statusSintaticoEl.textContent =
      "Parser não executado: corrija os erros léxicos primeiro.";
    arvoreEl.replaceChildren();
    astTextualEl.textContent = "";
    preencherErrosSintaticos([]);
    return;
  }
  if (sintatico.sucesso) {
    statusSintaticoEl.textContent =
      "AST construída com sucesso. Clique em um nó para destacar o trecho no código.";
    astAtual = sintatico.ast;
    renderizarAst(sintatico.ast);
    preencherErrosSintaticos([]);
  } else {
    statusSintaticoEl.textContent = "A AST não foi produzida por causa de erro sintático.";
    astAtual = null;
    arvoreEl.replaceChildren();
    astTextualEl.textContent = "";
    preencherErrosSintaticos(sintatico.erros || []);
  }
}

function renderizarLexico(codigo, dados) {
  codigoAtual = codigo;
  ultimaAnalise = dados;
  itensPasso = dados.tokens.concat(dados.erros).sort((a, b) => {
    return a.linha - b.linha || a.coluna - b.coluna;
  });
  painelEl.hidden = false;
  preencherContagem(dados.tokens);
  destacar(codigo);
  preencherTabela(dados.tokens);
  preencherErros(dados.erros);
  passoAtual = itensPasso.length ? 0 : -1;
  atualizarPasso();
  renderizarSintatico(dados.sintatico);
}

function preencherExemplos(lista) {
  exemplos = lista;
  for (const exemplo of lista) {
    const opcao = document.createElement("option");
    opcao.value = exemplo.id;
    opcao.textContent = exemplo.titulo;
    exemploEl.appendChild(opcao);
  }
}

exemploEl.addEventListener("change", () => {
  const escolhido = exemplos.find((item) => item.id === exemploEl.value);
  limparPainel();
  mostrarResultado(MENSAGEM_INICIAL, "neutro");
  if (!escolhido) {
    notaEl.textContent = "";
    return;
  }
  codigoEl.value = escolhido.codigo;
  notaEl.textContent = escolhido.demonstra;
  codigoEl.focus();
});

passoAnteriorEl.addEventListener("click", () => {
  if (passoAtual > 0) {
    passoAtual -= 1;
    atualizarPasso();
  }
});

passoProximoEl.addEventListener("click", () => {
  if (passoAtual >= 0 && passoAtual < itensPasso.length - 1) {
    passoAtual += 1;
    atualizarPasso();
  }
});

expandirAstEl.addEventListener("click", () => {
  arvoreEl.querySelectorAll("ul").forEach((lista) => {
    lista.hidden = false;
  });
  arvoreEl.querySelectorAll("li > button.passo").forEach((botao) => {
    botao.textContent = "−";
  });
});

recolherAstEl.addEventListener("click", () => {
  arvoreEl.querySelectorAll(":scope > li ul").forEach((lista) => {
    lista.hidden = true;
  });
  arvoreEl.querySelectorAll("li > button.passo").forEach((botao) => {
    botao.textContent = "+";
  });
});

exportarAstEl.addEventListener("click", () => {
  if (!astAtual) {
    statusSintaticoEl.textContent = "Não há AST para exportar nesta análise.";
    return;
  }
  const blob = new Blob([JSON.stringify(astAtual, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ast.json";
  link.click();
  URL.revokeObjectURL(url);
});

explicarNoEl.addEventListener("click", explicarNoSelecionado);
explicarErroSintaticoEl.addEventListener("click", explicarErroSintatico);
explicarTokenEl.addEventListener("click", () => {
  if (passoAtual < 0 || !itensPasso.length) {
    statusIaEl.textContent =
      "Analise um programa e selecione um passo/token antes de pedir a explicação.";
    return;
  }
  const item = itensPasso[passoAtual];
  if (item.tipo === "ERRO_LEXICO") {
    statusIaEl.textContent =
      "O passo atual é um erro léxico. Use um token válido da tabela.";
    return;
  }
  explicarToken(item);
});
perguntarIaEl.addEventListener("click", () => {
  const pergunta = perguntaIaEl.value.trim();
  if (!pergunta) {
    statusIaEl.textContent = "Digite uma pergunta para o assistente de IA.";
    return;
  }
  solicitarExplicacao("GERAL", pergunta, {
    tokens: ultimaAnalise ? ultimaAnalise.tokens : [],
    ast: astAtual,
    errosSintaticos: errosSintaticosAtuais,
  });
});

formEl.addEventListener("submit", (evento) => {
  evento.preventDefault();
  solicitarAnalise();
});

async function solicitarAnalise() {
  const codigo = codigoEl.value;
  if (codigo === "") {
    limparPainel();
    mostrarResultado(MENSAGEM_VAZIA, "erro");
    return;
  }
  if (codigo.trim() === "") {
    limparPainel();
    mostrarResultado(MENSAGEM_BRANCO, "erro");
    return;
  }

  botaoEl.disabled = true;
  botaoEl.textContent = "Analisando…";
  limparPainel();
  mostrarResultado("Enviando o código ao servidor…", "neutro");

  try {
    const resposta = await fetch("/api/analisar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codigo }),
    });

    let dados = null;
    try {
      dados = await resposta.json();
    } catch (_erro) {
      dados = null;
    }

    if (!resposta.ok) {
      if (resposta.status >= 500) {
        mostrarResultado(MENSAGEM_INESPERADO, "erro");
        return;
      }
      const mensagem =
        dados && typeof dados.mensagem === "string"
          ? dados.mensagem
          : MENSAGEM_INESPERADO;
      mostrarResultado(mensagem, "erro");
      return;
    }

    if (
      !dados ||
      dados.recebido !== true ||
      typeof dados.mensagem !== "string" ||
      typeof dados.caracteres !== "number" ||
      typeof dados.sucesso !== "boolean" ||
      !Array.isArray(dados.tokens) ||
      !Array.isArray(dados.erros) ||
      !dados.sintatico
    ) {
      mostrarResultado(MENSAGEM_INESPERADO, "erro");
      return;
    }

    const okGeral =
      dados.sucesso &&
      dados.sintatico.executado !== false &&
      dados.sintatico.sucesso === true;
    mostrarResultado(
      dados.mensagem,
      okGeral ? "ok" : "erro",
      dados.caracteres + " caracteres recebidos."
    );
    renderizarLexico(codigo, dados);
  } catch (_erro) {
    mostrarResultado(MENSAGEM_COMUNICACAO, "erro");
  } finally {
    botaoEl.disabled = false;
    botaoEl.textContent = "Analisar";
  }
}

async function carregarExemplos() {
  try {
    const resposta = await fetch("examples.json", { cache: "no-store" });
    if (!resposta.ok) {
      throw new Error("HTTP " + resposta.status);
    }
    const lista = await resposta.json();
    if (!Array.isArray(lista) || lista.length === 0) {
      throw new Error("lista vazia");
    }
    preencherExemplos(lista);
  } catch (_erro) {
    notaEl.textContent =
      "Não foi possível carregar os exemplos. Você ainda pode digitar um programa.";
  }
}

carregarExemplos();
