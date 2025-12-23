/**
 * UI Module
 * Handles DOM manipulations and Chart.js updates.
 */

export const UI = {
    elements: {
        status: document.getElementById('simStatus'),
        tick: document.getElementById('simTick'),
        gdp: document.getElementById('simGdp'),
        population: document.getElementById('simPopulation'),
        tradeVolume: document.getElementById('simTradeVolume'),
        avgHouseholdWealth: document.getElementById('simAvgHouseholdWealth'),
        avgFirmWealth: document.getElementById('simAvgFirmWealth'),
        householdNeeds: document.getElementById('simHouseholdNeeds'),
        firmNeeds: document.getElementById('simFirmNeeds'),
        topGood: document.getElementById('simTopGood'),
        unemployment: document.getElementById('simUnemployment'),
        transactionList: document.getElementById('transaction-list-container')
    },

    charts: {
        gdp: null
    },

    updateDashboard(data) {
        this.elements.status.textContent = data.status;
        this.elements.tick.textContent = data.tick;
        this.elements.gdp.textContent = data.gdp.toLocaleString();
        this.elements.population.textContent = data.population;
        this.elements.tradeVolume.textContent = data.trade_volume.toLocaleString();
        this.elements.avgHouseholdWealth.textContent = data.average_household_wealth.toFixed(2);
        this.elements.avgFirmWealth.textContent = data.average_firm_wealth.toFixed(2);
        this.elements.householdNeeds.textContent = data.household_avg_needs.toFixed(2);
        this.elements.firmNeeds.textContent = data.firm_avg_needs.toFixed(2);
        this.elements.topGood.textContent = data.top_selling_good;
        this.elements.unemployment.textContent = `${data.unemployment_rate.toFixed(1)}%`;

        if (data.chart_update && data.chart_update.new_gdp_history) {
            this.updateGdpChart(data.chart_update.new_gdp_history, data.tick);
        }
    },

    updateGdpChart(newData, currentTick) {
        // Calculate the starting tick for the new data chunk
        // If newData has length N, and ends at currentTick, it flows backwards
        // But usually newData follows strictly after the last update.
        // Simplified: Just appending.
        const lastTick = this.charts.gdp && this.charts.gdp.data.labels.length > 0
            ? this.charts.gdp.data.labels[this.charts.gdp.data.labels.length - 1]
            : 0;

        const newLabels = Array.from({length: newData.length}, (_, i) => lastTick + i + 1);

        if (!this.charts.gdp) {
            const ctx = document.getElementById('gdpChart').getContext('2d');
            this.charts.gdp = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: newLabels,
                    datasets: [{ 
                        label: 'GDP Over Time', 
                        data: newData, 
                        borderColor: '#0d6efd', 
                        tension: 0.1 
                    }]
                }
            });
        } else {
            this.charts.gdp.data.labels.push(...newLabels);
            this.charts.gdp.data.datasets[0].data.push(...newData);
            this.charts.gdp.update();
        }
    },

    updateTransactionList(transactions) {
        transactions.reverse().forEach(tx => {
            const itemHTML = this.createTransactionItem(tx);
            this.elements.transactionList.insertAdjacentHTML('afterbegin', itemHTML);
            if (this.elements.transactionList.children.length > 50) {
                this.elements.transactionList.lastElementChild.remove();
            }
        });
    },

    createTransactionItem(tx) {
        const isLabor = tx.item_id === 'labor';
        const icon = isLabor ? '💼' : '📦';
        const color = isLabor ? '#1E86FF' : '#00C9A7';
        const name = isLabor ? 'Labor Contract' : `Trade: ${tx.item_id}`;
        const description = `Buyer: ${tx.buyer_id}, Seller: ${tx.seller_id}, Qty: ${tx.quantity.toFixed(1)}, Price: ${tx.price.toFixed(1)}`;

        return `
            <figure class="transaction-item relative mx-auto min-h-fit w-full max-w-[400px] cursor-pointer overflow-hidden rounded-2xl p-4 bg-white dark:bg-transparent dark:backdrop-blur-md dark:[border:1px_solid_rgba(255,255,255,.1)] dark:[box-shadow:0_-20px_80px_-20px_#ffffff1f_inset]">
                <div class="flex flex-row items-center gap-3">
                    <div class="flex size-10 items-center justify-center rounded-2xl" style="background-color: ${color};">
                        <span class="text-lg">${icon}</span>
                    </div>
                    <div class="flex flex-col overflow-hidden">
                        <figcaption class="flex flex-row items-center whitespace-pre text-lg font-medium dark:text-white">
                            <span class="text-sm sm:text-lg">${name}</span>
                            <span class="mx-1">·</span>
                            <span class="text-xs text-gray-500">Tick ${tx.time}</span>
                        </figcaption>
                        <p class="text-sm font-normal dark:text-white/60">${description}</p>
                    </div>
                </div>
            </figure>
        `;
    },
    
    clearTransactions() {
        this.elements.transactionList.innerHTML = '';
    }
};
