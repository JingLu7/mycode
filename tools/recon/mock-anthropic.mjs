import http from 'node:http'
import fs from 'node:fs'

const LOG = '/tmp/captured-requests'
fs.mkdirSync(LOG, { recursive: true })
let n = 0

const server = http.createServer((req, res) => {
  let body = ''
  req.on('data', c => (body += c))
  req.on('end', () => {
    n++
    const rec = {
      n,
      ts: new Date().toISOString(),
      method: req.method,
      url: req.url,
      headers: req.headers,
      bodyLen: body.length,
      body: body.slice(0, 500000),
    }
    fs.writeFileSync(`${LOG}/${String(n).padStart(3, '0')}-${Date.now()}.json`, JSON.stringify(rec, null, 2))
    console.log(`[CAPTURE ${n}] ${req.method} ${req.url} len=${body.length}`)

    if (req.url.includes('/v1/messages')) {
      const payload = {
        id: 'msg_mock',
        type: 'message',
        role: 'assistant',
        model: 'claude-sonnet-4-5',
        content: [{ type: 'text', text: 'ok' }],
        stop_reason: 'end_turn',
        stop_sequence: null,
        usage: { input_tokens: 1, output_tokens: 1, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 },
      }
      res.writeHead(200, { 'content-type': 'application/json' })
      res.end(JSON.stringify(payload))
    } else {
      res.writeHead(200, { 'content-type': 'application/json' })
      res.end('{}')
    }
  })
})

server.listen(8731, '127.0.0.1', () => console.log('mock anthropic listening on 127.0.0.1:8731'))