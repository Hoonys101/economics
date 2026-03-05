🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\gemini-output\review\pr_diff_mission-wave5-stabilization-phase2-9235819225399444347.txt
📖 Attached context: modules\finance\system.py
📖 Attached context: reports\diagnostic_refined.md
📖 Attached context: simulation\initialization\initializer.py
📖 Attached context: simulation\systems\central_bank_system.py
📖 Attached context: simulation\systems\transaction_processor.py
🚀 [GeminiWorker] Running task with manual: git-review.md
❌ Error: Error executing gemini subprocess: Gemini CLI Error (Code 41):
Error authenticating: FatalAuthenticationError: Interactive consent could not be obtained.
Please run Gemini CLI in an interactive terminal to authenticate, or use NO_BROWSER=true for manual authentication.
    at getConsentForOauth (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/utils/authConsent.js:19:19)
    at initOauthClient (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/code_assist/oauth2.js:192:35)
    at async createCodeAssistContentGenerator (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/code_assist/codeAssist.js:14:28)
    at async file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/contentGenerator.js:78:48
    at async createContentGenerator (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/contentGenerator.js:53:23)
    at async Config.refreshAuth (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/config/config.js:571:33)
    at async main (file:///C:/Users/Gram%20Pro/AppData/Roaming/npm/node_modules/@google/gemini-cli/dist/src/gemini.js:245:17) {
  exitCode: 41
}
Hook registry initialized with 0 hook entries
[31mInteractive consent could not be obtained.
Please run Gemini CLI in an interactive terminal to authenticate, or use NO_BROWSER=true for manual authentication.[0m

