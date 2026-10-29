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

let exemplos = [];
let itensPasso = [];
let passoAtual = -1;

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
  itensPasso = [];
  passoAtual = -1;
  contagemEl.replaceChildren();
  coloridoEl.replaceChildren();
  corpoEl.replaceChildren();
  errosEl.replaceChildren();
  passoTextoEl.textContent = "";
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
    celula.colSpan = 4;
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

function renderizarLexico(codigo, dados) {
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
      !Array.isArray(dados.erros)
    ) {
      mostrarResultado(MENSAGEM_INESPERADO, "erro");
      return;
    }

    mostrarResultado(
      dados.mensagem,
      dados.sucesso ? "ok" : "erro",
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
    const resposta = await fetch("examples.json");
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
