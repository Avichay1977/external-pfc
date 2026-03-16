const http = require("http");
const fs = require("fs");
const path = require("path");
const dir = path.dirname(__filename);
const mime = { ".html": "text/html", ".js": "application/javascript", ".css": "text/css" };
http.createServer((req, res) => {
  const file = path.join(dir, req.url === "/" ? "pfc_ipad.html" : req.url);
  const ext = path.extname(file);
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); res.end("Not found"); return; }
    res.writeHead(200, { "Content-Type": mime[ext] || "text/plain" });
    res.end(data);
  });
}).listen(8080, () => console.log("Server on 8080"));
