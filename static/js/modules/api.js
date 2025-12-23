/**
 * API Module
 * Handles all network requests to the simulation backend.
 */

export const API = {
    /**
     * Get the authentication header with the token from localStorage
     */
    getAuthHeader() {
        const token = localStorage.getItem('secretToken');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },

    /**
     * Send a control command to the simulation (start, stop, pause, etc.)
     * @param {string} command - The command to send
     */
    async sendControlCommand(command) {
        const response = await fetch(`/api/simulation/${command}`, { 
            method: 'POST',
            headers: this.getAuthHeader()
        });
        
        if (response.status === 401) {
            throw new Error('AUTH_FAILED');
        }
        
        return await response.json();
    },

    /**
     * Fetch the current simulation configuration
     */
    async getConfig() {
        const response = await fetch('/api/config');
        return await response.json();
    },

    /**
     * Save the new configuration
     * @param {Object} newConfig - Configuration object
     */
    async saveConfig(newConfig) {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { ...this.getAuthHeader(), 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        });

        if (response.status === 401) {
            throw new Error('AUTH_FAILED');
        }
        return await response.json();
    },

    /**
     * Poll for dashboard updates
     * @param {number} sinceTick - The last tick received
     */
    /**
     * Advance the simulation by one tick and get the update
     */
    async advanceTick() {
        const response = await fetch('/api/simulation/tick', {
            method: 'POST',
            headers: this.getAuthHeader()
        });
        
        if (response.status === 401) throw new Error('AUTH_FAILED');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        return await response.json();
    },

    /**
     * Poll for dashboard updates (Legacy/View-only mode)
     * @param {number} sinceTick - The last tick received
     */
    async getUpdates(sinceTick) {
        // Kept for compatibility if we want to just view without ticking
        const response = await fetch(`/api/simulation/update?since=${sinceTick}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    },

    /**
     * Poll for recent transactions
     * @param {number} sinceTick - The last transaction tick received
     */
    async getTransactions(sinceTick) {
        const response = await fetch(`/api/market/transactions?since=${sinceTick}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    }
};
