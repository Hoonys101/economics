🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\design\gemini_output\pr_diff_refine-diagnosis-tool-14525228153841719624.txt
🚀 [GeminiWorker] Running task with manual: git_reviewer.md
❌ Error: Error executing gemini subprocess: Gemini CLI Error (Code 1):
Loaded cached credentials.
Error when talking to Gemini API Full report available at: C:\Users\GRAMPR~1\AppData\Local\Temp\gemini-client-error-Turn.run-sendMessageStream-2026-01-24T03-48-32-830Z.json TerminalQuotaError: You have exhausted your capacity on this model. Your quota will reset after 19h53m56s.
    at classifyGoogleError (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/utils/googleQuotaErrors.js:136:28)
    at retryWithBackoff (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/utils/retry.js:127:37)
    at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
    at async GeminiChat.makeApiCallAndProcessStream (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/geminiChat.js:364:32)
    at async GeminiChat.streamWithRetries (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/geminiChat.js:225:40)
    at async Turn.run (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/turn.js:64:30)
    at async GeminiClient.processTurn (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/client.js:440:26)
    at async GeminiClient.sendMessageStream (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/client.js:536:20)
    at async file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/dist/src/nonInteractiveCli.js:192:34
    at async main (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/dist/src/gemini.js:452:9) {
  cause: {
    code: 429,
    message: 'You have exhausted your capacity on this model. Your quota will reset after 19h53m56s.',
    details: [ [Object], [Object] ]
  },
  retryDelayMs: 71636647.867169
}
An unexpected critical error occurred:[object Object]

