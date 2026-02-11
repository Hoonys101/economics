🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\design\_archive\gemini_output\pr_diff_fix-settlement-finance-tests-integers-11228986551796741239.txt
🚀 [GeminiWorker] Running task with manual: git_reviewer.md
❌ Error: Error executing gemini subprocess: Gemini CLI Error (Code 1):
Loaded cached credentials.
Hook registry initialized with 0 hook entries
Error when talking to Gemini API Full report available at: C:\Users\GRAMPR~1\AppData\Local\Temp\gemini-client-error-Turn.run-sendMessageStream-2026-02-11T06-55-40-542Z.json TerminalQuotaError: You have exhausted your capacity on this model. Your quota will reset after 1h5m45s.
    at classifyGoogleError (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/utils/googleQuotaErrors.js:214:28)
    at retryWithBackoff (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/utils/retry.js:130:37)
    at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
    at async GeminiChat.makeApiCallAndProcessStream (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/geminiChat.js:421:32)
    at async GeminiChat.streamWithRetries (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/geminiChat.js:253:40)
    at async Turn.run (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/turn.js:66:30)
    at async GeminiClient.processTurn (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/client.js:458:26)
    at async GeminiClient.sendMessageStream (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/client.js:554:20)
    at async file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/dist/src/nonInteractiveCli.js:177:34
    at async main (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/dist/src/gemini.js:474:9) {
  cause: {
    code: 429,
    message: 'You have exhausted your capacity on this model. Your quota will reset after 1h5m45s.',
    details: [ [Object], [Object] ]
  },
  retryDelayMs: 3945782.758322
}
An unexpected critical error occurred:[object Object]

