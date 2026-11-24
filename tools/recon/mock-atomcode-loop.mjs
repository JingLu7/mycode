#!/usr/bin/env node
// mock-atomcode-loop.mjs — 驱动多轮 loop：第一次返回 tool_use，第二次返回最终文本
import http from 'node:http';
import fs from 'node:fs';

const PORT = 3457;
const OUTPUT_DIR = '/data/taoming/project/mycode/artifacts/recon/atomcode';
let reqCount = 0;

const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    reqCount++;
    const entry = { seq: reqCount, method: req.method, url: req.url, headers: req.headers, body };
    fs.writeFileSync(`${OUTPUT_DIR}/loop-req-${String(reqCount).padStart(2,'0')}.json`, JSON.stringify(entry, null, 2));
    console.error(`[mock] #${reqCount} ${req.method} ${req.url}`);

    if (req.url.includes('/chat/completions')) {
      res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive' });

      if (reqCount === 1) {
        // 第一次：返回 tool_use（让 atomcode 执行 read_file）
        const toolCall = {
          id: 'call_recon_01',
          function: { name: 'read_file', arguments: JSON.stringify({ file_path: '/etc/hostname' }) },
        };
        // SSE: tool_calls
        res.write(`data: ${JSON.stringify({ id:'x', object:'chat.completion.chunk', created:Date.now(), model:'qwen3.8-27b', choices:[{ index:0, delta:{ role:'assistant', content:null, tool_calls:[{ index:0, id:toolCall.id, type:'function', function:toolCall.function }] }, finish_reason:null }] })}\n\n`);
        res.write(`data: ${JSON.stringify({ id:'x', object:'chat.completion.chunk', created:Date.now(), model:'qwen3.8-27b', choices:[{ index:0, delta:{}, finish_reason:'tool_calls' }] })}\n\n`);
        res.write('data: [DONE]\n\n');
        res.end();
      } else {
        // 第二次及以后：返回最终文本
        res.write(`data: ${JSON.stringify({ id:'x', object:'chat.completion.chunk', created:Date.now(), model:'qwen3.8-27b', choices:[{ index:0, delta:{ role:'assistant', content:'Done. I read the file.' }, finish_reason:null }] })}\n\n`);
        res.write(`data: ${JSON.stringify({ id:'x', object:'chat.completion.chunk', created:Date.now(), model:'qwen3.8-27b', choices:[{ index:0, delta:{}, finish_reason:'stop' }] })}\n\n`);
        res.write('data: [DONE]\n\n');
        res.end();
      }
    } else {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end('{}');
    }
  });
});

server.listen(PORT, '127.0.0.1', () => console.error(`[mock-loop] listening on ${PORT}`));
process.on('SIGTERM', () => { server.close(); process.exit(0); });
process.on('SIGINT', () => { server.close(); process.exit(0); });