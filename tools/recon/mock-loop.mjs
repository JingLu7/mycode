// R3: 可编程 SSE mock — 驱动 claude agent loop，抓取逐轮请求
// 用法: MOCK_SCENARIO=<parallel|error|multi|thinking> MOCK_OUT=<dir> node mock-loop.mjs
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'

const OUT = process.env.MOCK_OUT || '/tmp/r3-capture'
const SCENARIO = process.env.MOCK_SCENARIO || 'parallel'
fs.mkdirSync(OUT, { recursive: true })

let turn = 0

function sse(res, events) {
  res.writeHead(200, {
    'content-type': 'text/event-stream',
    'cache-control': 'no-cache',
    'connection': 'keep-alive',
  })
  for (const [event, data] of events) {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
  }
  res.end()
}

const MSG_START = () => ['message_start', {
  type: 'message_start',
  message: { id: 'msg_' + Date.now(), type: 'message', role: 'assistant', model: 'claude-opus-5-5', content: [], stop_reason: null, usage: { input_tokens: 10, output_tokens: 1 } },
}]

function toolUseEvents(toolUses, prefix = null) {
  const ev = []
  let idx = 0
  if (prefix) {
    ev.push(MSG_START())
    ev.push(['content_block_start', { type: 'content_block_start', index: idx, content_block: { type: 'thinking', thinking: '' } }])
    ev.push(['content_block_delta', { type: 'content_block_delta', index: idx, delta: { type: 'thinking_delta', thinking: prefix } }])
    ev.push(['content_block_stop', { type: 'content_block_stop', index: idx }])
    idx++
  } else {
    ev.push(MSG_START())
  }
  toolUses.forEach((tu) => {
    ev.push(['content_block_start', { type: 'content_block_start', index: idx, content_block: { type: 'tool_use', id: tu.id, name: tu.name, input: {} } }])
    ev.push(['content_block_delta', { type: 'content_block_delta', index: idx, delta: { type: 'input_json_delta', partial_json: JSON.stringify(tu.input) } }])
    ev.push(['content_block_stop', { type: 'content_block_stop', index: idx }])
    idx++
  })
  ev.push(['message_delta', { type: 'message_delta', delta: { stop_reason: 'tool_use' }, usage: { output_tokens: 10 } }])
  ev.push(['message_stop', { type: 'message_stop' }])
  return ev
}

function endTurnEvents(text) {
  return [
    MSG_START(),
    ['content_block_start', { type: 'content_block_start', index: 0, content_block: { type: 'text', text: '' } }],
    ['content_block_delta', { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text } }],
    ['content_block_stop', { type: 'content_block_stop', index: 0 }],
    ['message_delta', { type: 'message_delta', delta: { stop_reason: 'end_turn' }, usage: { output_tokens: 5 } }],
    ['message_stop', { type: 'message_stop' }],
  ]
}

function scenarioEvents(t) {
  if (SCENARIO === 'parallel') {
    if (t === 1) return toolUseEvents([
      { id: 'toolu_p1', name: 'Bash', input: { command: 'echo first', description: 'first' } },
      { id: 'toolu_p2', name: 'Bash', input: { command: 'echo second', description: 'second' } },
    ])
    return endTurnEvents('done-parallel')
  }
  if (SCENARIO === 'error') {
    if (t === 1) return toolUseEvents([
      { id: 'toolu_e1', name: 'Read', input: { file_path: '/nonexistent/xyz.txt' } },
    ])
    return endTurnEvents('done-error')
  }
  if (SCENARIO === 'multi') {
    if (t <= 3) return toolUseEvents([
      { id: 'toolu_m' + t, name: 'Bash', input: { command: `echo turn${t}`, description: `t${t}` } },
    ])
    return endTurnEvents('done-multi')
  }
  if (SCENARIO === 'thinking') {
    if (t === 1) return toolUseEvents([
      { id: 'toolu_t1', name: 'Bash', input: { command: 'echo think', description: 'think' } },
    ], 'Let me think about this carefully. I will run echo.')
    return endTurnEvents('done-thinking')
  }
  return endTurnEvents('default')
}

const server = http.createServer((req, res) => {
  let body = ''
  req.on('data', (c) => (body += c))
  req.on('end', () => {
    if (req.url.includes('/v1/messages')) {
      turn++
      fs.writeFileSync(path.join(OUT, `req-${String(turn).padStart(2, '0')}.json`), body)
      console.log(`[REQ ${turn}] ${req.method} ${req.url} len=${body.length}`)
      sse(res, scenarioEvents(turn))
    } else {
      console.log(`[other] ${req.method} ${req.url}`)
      res.writeHead(200, { 'content-type': 'application/json' })
      res.end('{}')
    }
  })
})

const PORT = Number(process.env.MOCK_PORT) || 8731

server.listen(PORT, '127.0.0.1', () => console.log(`R3 mock scenario=${SCENARIO} out=${OUT} on 127.0.0.1:${PORT}`))