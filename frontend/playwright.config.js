const fs = require("fs");
const path = require("path");
const { defineConfig } = require("@playwright/test");

const chromeInstalado =
  process.platform === "win32" &&
  fs.existsSync("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe");

const python =
  process.env.PYTHON ||
  path.join(__dirname, "..", "backend", ".venv", "Scripts", "python.exe");

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 20000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:4173",
    // No Windows com Chrome instalado, os testes usam esse navegador.
    // Sem ele, o Playwright usa o Chromium baixado por `npx playwright install chromium`.
    ...(chromeInstalado ? { channel: "chrome" } : {}),
  },
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 5001`,
      cwd: path.join(__dirname, "..", "backend"),
      url: "http://127.0.0.1:5001/api/health",
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: "node test-server.js",
      url: "http://127.0.0.1:4173",
      env: {
        PORT: "4173",
        BACKEND_URL: "http://127.0.0.1:5001",
      },
      reuseExistingServer: false,
      timeout: 20000,
    },
  ],
});
