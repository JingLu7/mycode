#!/usr/bin/env node
// mock-atomcode.mjs — 记录型 mock 端点，捕获 atomcode 的真实 API 请求
// atomcode 用 OpenAI 兼容接口（/v1/chat/completions），不是 Anthropic 格式
import http from 'node:http';
import fs from 'node:fs';

const PORT = parseInt(process.env.MOCK_PORT || '3456', 10);
const OUTPUT_DIR = process.env.MOCK_OUTPUT_DIR || '/data/taoming/project/mycode/artifacts/recon/atomcode';
let reqCount = 0;

const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    reqCount++;
    const entry = {
      seq: reqCount,
      method: req.method,
      url: req.url,
      headers: req.headers,
      body: body,
    };
    // 落盘每个请求
    const outFile = `${OUTPUT_DIR}/req-${String(reqCount).padStart(2, '0')}.json`;
    fs.writeFileSync(outFile, JSON.stringify(entry, null, 2));
    // 也写一个 latest
    fs.writeFileSync(`${OUTPUT_DIR}/capture-latest.json`, JSON.stringify(entry, null, 2));
    console.error(`[mock] #${reqCount} ${req.method} ${req.url} → ${outFile}`);

    // 返回 OpenAI 格式响应
    if (req.url.includes('/chat/completions')) {
      // 检查是否要求流式
      let isStream = false;
      try { isStream = JSON.parse(body).stream === true; } catch {}

      if (isStream) {
        // SSE 流式响应
        res.writeHead(200, {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        });
        const chunk = {
          id: 'chatcmpl-mock',
          object: 'chat.completion.chunk',
          created: Math.floor(Date.now() / 1000),
          model: 'qwen3.8-27b',
          choices: [{ index: 0, delta: { role: 'assistant', content: 'ok' }, finish_reason: null }],
        };
        res.write(`data: ${JSON.stringify(chunk)}\n\n`);
        const done = {
          id: 'chatcmpl-mock',
          object: 'chat.completion.chunk',
          created: Math.floor(Date.now() / 1000),
          model: 'qwen3.8-27b',
          choices: [{ index: 0, delta: {}, finish_reason: 'stop' }],
        };
        res.write(`data: ${JSON.stringify(done)}\n\n`);
        res.write('data: [DONE]\n\n');
        res.end();
      } else {
        // 非流式响应
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          id: 'chatcmpl-mock',
          object: 'chat.completion',
          created: Math.floor(Date.now() / 1000),
          model: 'qwen3.8-27b',
          choices: [{
            index: 0,
            message: { role: 'assistant', content: 'ok' },
            finish_reason: 'stop',
          }],
          usage: { prompt_tokens: 10, completion_tokens: 1, total_tokens: 11 },
        }));
      }
    } else if (req.url.includes('/models')) {
      // /v1/models 端点
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        object: 'list',
        data: [{ id: 'qwen3.8-27b', object: 'model', created: 0, owned_by: 'mock' }],
      }));
    } else {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end('{}');
    }
  });
});

server.listen(PORT, '127.0.0.1', () => {
  console.error(`[mock] listening on http://127.0.0.1:${PORT}`);
});

// 优雅退出
process.on('SIGTERM', () => { server.close(); process.exit(0); });
process.on('SIGINT', () => { server.close(); process.exit(0); });