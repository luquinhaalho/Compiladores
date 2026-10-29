const { test, expect } = require("@playwright/test");
const exemplos = require("../public/examples.json");

const MENSAGEM_VAZIA = "Informe um código-fonte antes de solicitar a análise.";
const MENSAGEM_BRANCO =
  "Não há conteúdo útil para analisar. Informe um programa antes de continuar.";
const MENSAGEM_COMUNICACAO =
  "Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.";
const MENSAGEM_INESPERADO =
  "Ocorreu um erro inesperado ao processar o código. Tente novamente.";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#exemplo option")).toHaveCount(exemplos.length + 1);
});

test("mostra a identificação, o editor, os exemplos e o resultado", async ({ page }) => {
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Árvores de sintaxe abstrata"
  );
  await expect(page.getByText("Java", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Código-fonte")).toBeVisible();
  await expect(page.getByRole("button", { name: "Analisar" })).toBeEnabled();
  await expect(page.getByRole("region", { name: "Resultado" })).toBeVisible();

  const seletor = page.getByLabel("Exemplo de programa");
  for (const exemplo of exemplos) {
    await expect(seletor.locator(`option[value="${exemplo.id}"]`)).toHaveText(
      exemplo.titulo
    );
  }
});

test("cada exemplo substitui o código anterior e pode ser editado", async ({ page }) => {
  const editor = page.getByLabel("Código-fonte");
  const seletor = page.getByLabel("Exemplo de programa");

  for (const exemplo of exemplos) {
    await seletor.selectOption(exemplo.id);
    await expect(editor).toHaveValue(exemplo.codigo);
    await expect(page.locator("#exemplo-nota")).toHaveText(exemplo.demonstra);
  }

  await seletor.selectOption(exemplos[0].id);
  await editor.fill(exemplos[0].codigo + "\nint extra = 1;\n");
  await expect(editor).toHaveValue(exemplos[0].codigo + "\nint extra = 1;\n");

  await seletor.selectOption(exemplos[1].id);
  await expect(editor).toHaveValue(exemplos[1].codigo);
});

test("envia o código editado e preserva o texto no editor", async ({ page }) => {
  const editor = page.getByLabel("Código-fonte");
  const codigo = 'int nome = 1 + 2; // "ação" <>&';
  await editor.fill(codigo);
  await page.getByRole("button", { name: "Analisar" }).click();

  await expect(page.getByRole("status")).toContainText("Análise léxica concluída");
  await expect(page.locator("#resultado-detalhe")).toHaveText(
    codigo.length + " caracteres recebidos."
  );
  await expect(page.getByRole("table")).toContainText("nome");
  await expect(page.locator("#erros-lexicos")).toContainText("Nenhum erro léxico");
  await expect(editor).toHaveValue(codigo);
  await expect(page.getByRole("button", { name: "Analisar" })).toBeEnabled();
});

test("recusa entrada vazia e entrada só com espaços", async ({ page }) => {
  const editor = page.getByLabel("Código-fonte");
  await page.getByRole("button", { name: "Analisar" }).click();
  await expect(page.getByRole("status")).toHaveText(MENSAGEM_VAZIA);
  await expect(editor).toHaveValue("");

  await editor.fill(" \n\t ");
  await page.getByRole("button", { name: "Analisar" }).click();
  await expect(page.getByRole("status")).toHaveText(MENSAGEM_BRANCO);
  await expect(editor).toHaveValue(" \n\t ");
});

test("explica quando o servidor não responde", async ({ page }) => {
  await page.route("**/api/analisar", (route) => route.abort());
  await page.getByLabel("Código-fonte").fill("int numero = 10;\n");
  await page.getByRole("button", { name: "Analisar" }).click();

  await expect(page.getByRole("status")).toHaveText(MENSAGEM_COMUNICACAO);
  await expect(page.getByRole("button", { name: "Analisar" })).toBeEnabled();
  await expect(page.getByLabel("Código-fonte")).toHaveValue("int numero = 10;\n");
});

test("mostra os tokens e avança o passo a passo", async ({ page }) => {
  await page.getByLabel("Código-fonte").fill("int numero = 10;\n");
  await page.getByRole("button", { name: "Analisar" }).click();

  await expect(page.locator("#explicacao-lexica")).toContainText("lexema");
  await expect(page.getByRole("table")).toContainText("Palavra reservada");
  await expect(page.getByRole("table")).toContainText("numero");
  await expect(page.locator("#passo-texto")).toContainText("int");
  await expect(page.locator("#passo-texto")).toContainText("palavra reservada");

  await page.getByRole("button", { name: "Próximo passo" }).click();
  await expect(page.locator("#passo-texto")).toContainText("numero");
  await expect(page.locator("#passo-texto")).toContainText("identificador");
});

test("mostra o erro léxico sem apagar os tokens válidos", async ({ page }) => {
  await page.getByLabel("Código-fonte").fill("int a = 1 @ 2;\n");
  await page.getByRole("button", { name: "Analisar" }).click();

  await expect(page.getByRole("status")).toContainText("1 erro léxico");
  await expect(page.locator("#erros-lexicos")).toContainText("não reconhecido");
  await expect(page.locator("#erros-lexicos")).toContainText("@");
  await expect(page.getByRole("table")).toContainText("int");
  await expect(page.getByRole("button", { name: "Analisar" })).toBeEnabled();
});

test("mostra uma mensagem genérica quando o servidor falha", async ({ page }) => {
  await page.route("**/api/analisar", (route) =>
    route.fulfill({
      status: 500,
      contentType: "text/plain",
      body: "Traceback (most recent call last): segredo interno",
    })
  );
  await page.getByLabel("Código-fonte").fill("int numero = 10;\n");
  await page.getByRole("button", { name: "Analisar" }).click();

  await expect(page.getByRole("status")).toHaveText(MENSAGEM_INESPERADO);
  await expect(page.getByRole("status")).not.toContainText("Traceback");
  await expect(page.getByRole("status")).not.toContainText("segredo");
});
