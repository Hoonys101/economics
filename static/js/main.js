import { API } from './modules/api.js';
import { UI } from './modules/ui.js';

let isRunning = false;
let lastTick = 0;
let lastTransactionTick = 0;
let gameLoopTimeout = null;
let txPollInterval = null;

// Game Loop Configuration
const TICK_INTERVAL = 1000; // ms per tick

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    // Initial status check (mainly to see if we ended up in a weird state, 
    // but in client-driven, we default to stopped/paused unless we persist state)
    // We can just fetch the current tick to init UI
    fetchInitialState();
});

function setupEventListeners() {
    document.getElementById('startBtn').addEventListener('click', () => handleControlCommand('start'));
    document.getElementById('pauseBtn').addEventListener('click', () => handleControlCommand('pause'));
    document.getElementById('stopBtn').addEventListener('click', () => handleControlCommand('stop'));
    document.getElementById('resetBtn').addEventListener('click', () => handleControlCommand('reset'));
    document.getElementById('stopServerBtn').addEventListener('click', () => handleControlCommand('shutdown'));
    
    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    document.getElementById('settingsModal').addEventListener('show.bs.modal', loadSettings);

    const toggleBtn = document.getElementById('toggleSecretToken');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTokenVisibility);
    }
}

function toggleTokenVisibility() {
    const input = document.getElementById('secretToken');
    const btn = document.getElementById('toggleSecretToken');
    const isPassword = input.type === 'password';

    input.type = isPassword ? 'text' : 'password';

    // Update aria-label
    btn.setAttribute('aria-label', isPassword ? 'Hide secret token' : 'Show secret token');

    // Update icon
    if (isPassword) {
        // Switch to "Eye Slash" (Hidden) icon to indicate clicking it will hide the token
        btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye-slash" viewBox="0 0 16 16">
                <path d="M13.359 11.238C15.06 9.72 16 8 16 8s-3-5.5-8-5.5a7.028 7.028 0 0 0-2.79.588l.77.771A5.944 5.944 0 0 1 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.134 13.134 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755-.165.165-.337.328-.517.486l.708.709z"/>
                <path d="M11.297 9.176a3.5 3.5 0 0 0-4.474-4.474l.823.823a2.5 2.5 0 0 1 2.829 2.829l.822.822zm-2.943 1.299.822.822a3.5 3.5 0 0 1-4.474-4.474l.823.823a2.5 2.5 0 0 0 2.829 2.829z"/>
                <path d="M3.35 5.47c-.18.16-.353.322-.518.487A13.134 13.134 0 0 0 1.172 8l.195.288c.335.48.83 1.12 1.465 1.755C4.121 11.332 5.881 12.5 8 12.5c.716 0 1.39-.133 2.02-.36l.77.772A7.029 7.029 0 0 1 8 13.5C3 13.5 0 8 0 8s.939-1.721 2.641-3.238l.708.709zm10.296 8.884-12-12 .708-.708 12 12-.708.708z"/>
            </svg>
        `;
    } else {
        // Switch back to "Eye"
        btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye" viewBox="0 0 16 16">
                <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 0 1 1.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.134 13.134 0 0 1 1.172 8z"/>
                <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM4.5 8a3.5 3.5 0 1 1 7 0 3.5 3.5 0 0 1-7 0z"/>
            </svg>
        `;
    }
}

async function fetchInitialState() {
    try {
        // Just get the current update without ticking to populate UI
        const data = await API.getUpdates(0);
        if (data && data.status !== 'no_update') {
            UI.updateDashboard(data);
            lastTick = data.tick;
            lastTransactionTick = data.tick; // Sync tx
        }
    } catch (error) {
        console.error('Initial state fetch error:', error);
    }
}

async function handleControlCommand(command) {
    try {
        // We still send commands to backend for logging or future hybrid states,
        // but the core logic is now client-side `isRunning`.
        const result = await API.sendControlCommand(command);
        console.log(result.message);
        
        if (command === 'start') {
            startGameLoop();
        } else if (['stop', 'pause', 'shutdown'].includes(command)) {
            stopGameLoop();
            if (command === 'stop') {
                 // Stop implies fully stopping? In this context, pause and stop are similar
                 // unless stop resets something. Backend stop clears instance.
                 // So we should re-fetch state or reset UI?
                 // Let's just pause client loop.
            }
        } else if (command === 'reset') {
            stopGameLoop();
            resetUI();
        }
    } catch (error) {
        if (error.message === 'AUTH_FAILED') {
            alert('Authentication failed. Please check settings.');
        } else {
            console.error(`Error sending ${command}:`, error);
        }
    }
}

function startGameLoop() {
    if (isRunning) return;
    isRunning = true;
    UI.updateDashboard({ ...getCurrentUIState(), status: 'running' }); // Optimistic update
    updateControlButtons('running');
    runTick();
    startTxPolling(); // Keep TX polling separate or integrate? Separate is fine for now.
}

function stopGameLoop() {
    isRunning = false;
    clearTimeout(gameLoopTimeout);
    clearTimeout(txPollInterval);
    UI.updateDashboard({ ...getCurrentUIState(), status: 'paused' });
    updateControlButtons('paused');
}

function resetUI() {
    lastTick = 0;
    lastTransactionTick = 0;
    UI.clearTransactions();
    UI.updateDashboard({
        status: 'paused', tick: 0, gdp: 0, population: 0, 
        trade_volume: 0, average_household_wealth: 0, average_firm_wealth: 0,
        household_avg_needs: 0, firm_avg_needs: 0, top_selling_good: '-', unemployment_rate: 0
    });
    updateControlButtons('paused');
}

function updateControlButtons(state) {
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const stopBtn = document.getElementById('stopBtn');
    const resetBtn = document.getElementById('resetBtn');

    if (state === 'running') {
        startBtn.disabled = true;
        pauseBtn.disabled = false;
        stopBtn.disabled = false;
        resetBtn.disabled = true;
    } else {
        // paused or stopped
        startBtn.disabled = false;
        pauseBtn.disabled = true;
        stopBtn.disabled = false; // Stop resets sim on backend sometimes, or just stops.
        resetBtn.disabled = false;
    }
}

function getCurrentUIState() {
    // Helper to get current text values if needed, 
    // but better to just rely on next update.
    return {
        status: isRunning ? 'running' : 'paused',
        tick: document.getElementById('simTick').textContent,
        // ... fills rest if necessary, but UI module handles partial updates usually? 
        // Actually UI.updateDashboard expects full object.
        // We will just let the next tick update it or rely on the fetch.
        // Mocking minimal for status update:
        gdp: parseNum('simGdp'), population: parseNum('simPopulation'),
        trade_volume: parseNum('simTradeVolume'),
        average_household_wealth: parseFloat(document.getElementById('simAvgHouseholdWealth').textContent),
        average_firm_wealth: parseFloat(document.getElementById('simAvgFirmWealth').textContent),
        household_avg_needs: parseFloat(document.getElementById('simHouseholdNeeds').textContent),
        firm_avg_needs: parseFloat(document.getElementById('simFirmNeeds').textContent),
        top_selling_good: document.getElementById('simTopGood').textContent,
        unemployment_rate: parseFloat(document.getElementById('simUnemployment').textContent)
    };
}
function parseNum(id) { return parseFloat(document.getElementById(id).textContent.replace(/,/g, '')); }


/**
 * The Main Game Loop
 * Advances one tick, updates UI, schedules next.
 */
async function runTick() {
    if (!isRunning) return;

    try {
        const data = await API.advanceTick();
        UI.updateDashboard(data);
        lastTick = data.tick;
    } catch (error) {
        console.error('Tick error:', error);
        // If error, maybe pause? Or retry?
        // stopGameLoop(); 
    }

    if (isRunning) {
        gameLoopTimeout = setTimeout(runTick, TICK_INTERVAL);
    }
}


/**
 * Transaction Polling
 * Still useful to poll separately if we don't return TXs in the tick response.
 */
async function startTxPolling() {
    pollTransactions();
}

async function pollTransactions() {
    if (!isRunning) return;
    try {
        const transactions = await API.getTransactions(lastTransactionTick);
        if (transactions.length > 0) {
            lastTransactionTick = transactions[transactions.length - 1].time;
            UI.updateTransactionList(transactions);
        }
    } catch (error) {
        console.error('Transaction polling error:', error);
    }
    txPollInterval = setTimeout(pollTransactions, 1500);
}


// Settings Logic (Reuse)
async function loadSettings() {
    try {
        document.getElementById('secretToken').value = localStorage.getItem('secretToken') || '';
        const config = await API.getConfig();
        for (const [key, value] of Object.entries(config)) {
            const input = document.getElementById(key);
            if (input) input.value = value;
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

async function saveSettings() {
    const tokenInput = document.getElementById('secretToken');
    if (tokenInput.value) {
        localStorage.setItem('secretToken', tokenInput.value);
    }

    const form = document.getElementById('settingsForm');
    const newConfig = {};
    for (const child of form.children) {
        const input = child.querySelector('input');
        if (input && input.id !== 'secretToken') {
            newConfig[input.id] = input.value;
        }
    }

    try {
        const result = await API.saveConfig(newConfig);
        console.log(result.message);
        
        const modalEl = document.getElementById('settingsModal');
        const modal = bootstrap.Modal.getInstance(modalEl); 
        modal.hide();

        handleControlCommand('reset'); 
    } catch (error) {
        if (error.message === 'AUTH_FAILED') {
            alert('Authentication failed.');
        } else {
            console.error('Error saving settings:', error);
        }
    }
}
