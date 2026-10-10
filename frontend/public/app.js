const messageEl = document.getElementById("message");
const detailEl = document.getElementById("detail");

async function loadHello() {
  try {
    const response = await fetch("/api/hello");
    if (!response.ok) {
      throw new Error("HTTP " + response.status);
    }
    const data = await response.json();
    if (!data || typeof data.message !== "string") {
      throw new Error("resposta sem mensagem");
    }
    messageEl.textContent = data.message;
    messageEl.classList.remove("is-error");
    detailEl.textContent =
      "O frontend encaminhou o pedido ao contêiner do backend e recebeu a resposta.";
  } catch (error) {
    messageEl.textContent = "Falha ao contatar o backend.";
    messageEl.classList.add("is-error");
    detailEl.textContent = error instanceof Error ? error.message : "erro desconhecido";
  }
}

loadHello();
