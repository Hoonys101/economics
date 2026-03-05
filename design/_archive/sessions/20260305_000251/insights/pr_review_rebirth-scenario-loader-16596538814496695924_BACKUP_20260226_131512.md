🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached 30 context files using Smart Context Injector.
🚀 [GeminiWorker] Running task with manual: git-review.md
❌ Error: Error executing gemini subprocess: Gemini CLI Error (Code 1):
Loaded cached credentials.
Hook registry initialized with 0 hook entries
Error when talking to Gemini API Full report available at: C:\Users\GRAMPR~1\AppData\Local\Temp\gemini-client-error-Turn.run-sendMessageStream-2026-02-26T04-07-52-970Z.json GaxiosError: [{
  "error": {
    "code": 499,
    "message": "The operation was cancelled.",
    "errors": [
      {
        "message": "The operation was cancelled.",
        "domain": "global",
        "reason": "backendError"
      }
    ],
    "status": "CANCELLED"
  }
}
]
    at Gaxios._request (C:\Users\Gram Pro\AppData\Roaming\npm\node_modules\@google\gemini-cli\node_modules\gaxios\build\src\gaxios.js:142:23)
    at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
    at async OAuth2Client.requestAsync (C:\Users\Gram Pro\AppData\Roaming\npm\node_modules\@google\gemini-cli\node_modules\google-auth-library\build\src\auth\oauth2client.js:429:18)
    at async CodeAssistServer.requestStreamingPost (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/code_assist/server.js:171:21)
    at async CodeAssistServer.generateContentStream (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/code_assist/server.js:29:27)
    at async file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/loggingContentGenerator.js:138:26
    at async retryWithBackoff (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/utils/retry.js:109:28)
    at async GeminiChat.makeApiCallAndProcessStream (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/geminiChat.js:431:32)
    at async GeminiChat.streamWithRetries (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/geminiChat.js:263:40)
    at async Turn.run (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/turn.js:66:30) {
  config: {
    url: 'https://cloudcode-pa.googleapis.com/v1internal:streamGenerateContent?alt=sse',
    method: 'POST',
    params: { alt: 'sse' },
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'GeminiCLI/0.28.2/gemini-3-pro-preview (win32; x64) google-api-nodejs-client/9.15.1',
      Authorization: '<<REDACTED> - See `errorRedactor` option in `gaxios` for configuration>.',
      'x-goog-api-client': 'gl-node/22.17.0'
    },
    responseType: 'stream',
    body: '<<REDACTED> - See `errorRedactor` option in `gaxios` for configuration>.',
    signal: AbortSignal { aborted: false },
    paramsSerializer: [Function: paramsSerializer],
    validateStatus: [Function: validateStatus],
    errorRedactor: [Function: defaultErrorRedactor]
  },
  response: {
    config: {
      url: 'https://cloudcode-pa.googleapis.com/v1internal:streamGenerateContent?alt=sse',
      method: 'POST',
      params: [Object],
      headers: [Object],
      responseType: 'stream',
      body: '<<REDACTED> - See `errorRedactor` option in `gaxios` for configuration>.',
      signal: [AbortSignal],
      paramsSerializer: [Function: paramsSerializer],
      validateStatus: [Function: validateStatus],
      errorRedactor: [Function: defaultErrorRedactor]
    },
    data: '[{\n' +
      '  "error": {\n' +
      '    "code": 499,\n' +
      '    "message": "The operation was cancelled.",\n' +
      '    "errors": [\n' +
      '      {\n' +
      '        "message": "The operation was cancelled.",\n' +
      '        "domain": "global",\n' +
      '        "reason": "backendError"\n' +
      '      }\n' +
      '    ],\n' +
      '    "status": "CANCELLED"\n' +
      '  }\n' +
      '}\n' +
      ']',
    headers: {
      'alt-svc': 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000',
      'content-length': '264',
      'content-type': 'application/json; charset=UTF-8',
      date: 'Thu, 26 Feb 2026 04:07:52 GMT',
      server: 'ESF',
      'server-timing': 'gfet4t7; dur=4870',
      vary: 'Origin, X-Origin, Referer',
      'x-cloudaicompanion-trace-id': 'a354e662fd3608d4',
      'x-content-type-options': 'nosniff',
      'x-frame-options': 'SAMEORIGIN',
      'x-xss-protection': '0'
    },
    status: 499,
    statusText: 'Client Closed Request',
    request: {
      responseURL: 'https://cloudcode-pa.googleapis.com/v1internal:streamGenerateContent?alt=sse'
    }
  },
  error: undefined,
  status: 499,
  [Symbol(gaxios-gaxios-error)]: '6.7.1'
}
An unexpected critical error occurred:[object Object]

