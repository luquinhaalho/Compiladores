const MENSAGEM_VAZIA = "Informe um código-fonte antes de solicitar a análise.";
const MENSAGEM_BRANCO =
  "Não há conteúdo útil para analisar. Informe um programa antes de continuar.";
const MENSAGEM_COMUNICACAO =
  "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.";
const MENSAGEM_INESPERADO =
  "Ocorreu um erro inesperado ao processar o código. Tente novamente.";

const formEl = document.getElementById("form-analise");
const exemploEl = document.getElementById("exemplo");
const notaEl = document.getElementById("exemplo-nota");
const codigoEl = document.getElementById("codigo");
const botaoEl = document.getElementById("analisar");
const resultadoEl = document.getElementById("resultado");
const detalheEl = document.getElementById("resultado-detalhe");

let exemplos = [];

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
  if (!escolhido) {
    notaEl.textContent = "";
    return;
  }
  codigoEl.value = escolhido.codigo;
  notaEl.textContent = escolhido.demonstra;
  codigoEl.focus();
});

formEl.addEventListener("submit", (evento) => {
  evento.preventDefault();
  solicitarAnalise();
});

async function solicitarAnalise() {
  const codigo = codigoEl.value;
  if (codigo === "") {
    mostrarResultado(MENSAGEM_VAZIA, "erro");
    return;
  }
  if (codigo.trim() === "") {
    mostrarResultado(MENSAGEM_BRANCO, "erro");
    return;
  }

  botaoEl.disabled = true;
  botaoEl.textContent = "Analisando…";
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
      typeof dados.caracteres !== "number"
    ) {
      mostrarResultado(MENSAGEM_INESPERADO, "erro");
      return;
    }

    mostrarResultado(
      dados.mensagem,
      "ok",
      dados.caracteres + " caracteres recebidos."
    );
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
