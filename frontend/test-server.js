const http = require("http");
const fs = require("fs");
const path = require("path");

const port = Number(process.env.PORT || 4173);
const backend = process.env.BACKEND_URL || "http://127.0.0.1:5001";
const root = path.join(__dirname, "public");
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://127.0.0.1:" + port);
  if (url.pathname.startsWith("/api/")) {
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    try {
      const upstream = await fetch(backend + url.pathname + url.search, {
        method: req.method,
        headers: {
          "content-type": req.headers["content-type"] || "application/json",
        },
        body: req.method === "GET" || req.method === "HEAD" ? undefined : Buffer.concat(chunks),
      });
      const payload = Buffer.from(await upstream.arrayBuffer());
      res.writeHead(upstream.status, {
        "content-type": upstream.headers.get("content-type") || "application/json",
      });
      res.end(payload);
    } catch (_error) {
      res.writeHead(502, { "content-type": "text/plain; charset=utf-8" });
      res.end("bad gateway");
    }
    return;
  }

  const relative = decodeURIComponent(url.pathname === "/" ? "index.html" : url.pathname.slice(1));
  const file = path.join(root, relative);
  if (!file.startsWith(root)) {
    res.writeHead(403);
    res.end();
    return;
  }
  fs.readFile(file, (error, data) => {
    if (error) {
      res.writeHead(404);
      res.end("not found");
      return;
    }
    res.writeHead(200, {
      "content-type": types[path.extname(file)] || "application/octet-stream",
    });
    res.end(data);
  });
});

server.listen(port, "127.0.0.1", () => {
  console.log("test server on " + port);
});
