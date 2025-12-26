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
        transactionList: document.getElementById('transaction-list-container'),
        orderBookBody: document.getElementById('order-book-body') // Need to add this to HTML
    },

    charts: {
        gdp: null,
        wealthDist: null,
        householdNeeds: null,
        firmNeeds: null,
        salesByGood: null
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

        if (data.chart_update) {
            if (data.chart_update.new_gdp_history) {
                this.updateGdpChart(data.chart_update.new_gdp_history, data.tick);
            }
            if (data.chart_update.wealth_distribution) {
                this.updateWealthDistributionChart(data.chart_update.wealth_distribution);
            }
            if (data.chart_update.household_needs_distribution) {
                this.updateHouseholdNeedsChart(data.chart_update.household_needs_distribution);
            }
            if (data.chart_update.firm_needs_distribution) {
                this.updateFirmNeedsChart(data.chart_update.firm_needs_distribution);
            }
            if (data.chart_update.sales_by_good) {
                this.updateSalesChart(data.chart_update.sales_by_good);
            }
        }

        if (data.market_update) {
            if (data.market_update.open_orders) {
                this.updateMarketOrderBook(data.market_update.open_orders);
            }
            // Transactions handled by separate poll usually, but if sent here:
            if (data.market_update.transactions && data.market_update.transactions.length > 0) {
                 this.updateTransactionList(data.market_update.transactions);
            }
        }
    },

    updateGdpChart(newData, currentTick) {
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

    updateWealthDistributionChart(data) {
        if (!this.charts.wealthDist) {
            const ctx = document.getElementById('wealthDistChart').getContext('2d');
            this.charts.wealthDist = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Wealth Distribution',
                        data: data.data,
                        backgroundColor: '#198754'
                    }]
                }
            });
        } else {
            this.charts.wealthDist.data.labels = data.labels;
            this.charts.wealthDist.data.datasets[0].data = data.data;
            this.charts.wealthDist.update();
        }
    },

    updateHouseholdNeedsChart(data) {
        // data is object {need_name: avg_value}
        const labels = Object.keys(data);
        const values = Object.values(data);

        if (!this.charts.householdNeeds) {
            const ctx = document.getElementById('householdNeedsChart').getContext('2d');
            this.charts.householdNeeds = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Avg Household Needs',
                        data: values,
                        backgroundColor: 'rgba(255, 193, 7, 0.2)',
                        borderColor: '#ffc107',
                        pointBackgroundColor: '#ffc107'
                    }]
                },
                options: {
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        } else {
            this.charts.householdNeeds.data.labels = labels;
            this.charts.householdNeeds.data.datasets[0].data = values;
            this.charts.householdNeeds.update();
        }
    },

    updateFirmNeedsChart(data) {
        // data is object {need_name: avg_value}
        // Likely mainly liquidity need
        const labels = Object.keys(data);
        const values = Object.values(data);

        if (!this.charts.firmNeeds) {
            const ctx = document.getElementById('firmNeedsChart').getContext('2d');
            this.charts.firmNeeds = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Avg Firm Needs',
                        data: values,
                        backgroundColor: '#dc3545'
                    }]
                },
                options: {
                   scales: {
                       y: { beginAtZero: true }
                   }
                }
            });
        } else {
            this.charts.firmNeeds.data.labels = labels;
            this.charts.firmNeeds.data.datasets[0].data = values;
            this.charts.firmNeeds.update();
        }
    },

    updateSalesChart(data) {
        // data is {item_id: quantity}
        const labels = Object.keys(data);
        const values = Object.values(data);

        if (!this.charts.salesByGood) {
            const ctx = document.getElementById('salesByGoodChart').getContext('2d');
            this.charts.salesByGood = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Sales Volume',
                        data: values,
                        backgroundColor: [
                            '#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545', '#fd7e14'
                        ]
                    }]
                }
            });
        } else {
            this.charts.salesByGood.data.labels = labels;
            this.charts.salesByGood.data.datasets[0].data = values;
            this.charts.salesByGood.update();
        }
    },

    updateMarketOrderBook(orders) {
        // Update table
        const tbody = document.getElementById('order-book-body');
        if (!tbody) return; // Must ensure HTML exists

        tbody.innerHTML = '';
        // Sort by Type then Item then Price
        // Bids descending price, Asks ascending price
        orders.sort((a, b) => {
            if (a.type !== b.type) return a.type.localeCompare(b.type);
            if (a.item_id !== b.item_id) return a.item_id.localeCompare(b.item_id);
            if (a.type === 'BID') return b.price - a.price;
            return a.price - b.price;
        });

        orders.forEach(order => {
            const row = `
                <tr class="${order.type === 'BID' ? 'table-success' : 'table-danger'}">
                    <td>${order.type}</td>
                    <td>${order.item_id}</td>
                    <td>${order.price.toFixed(2)}</td>
                    <td>${order.quantity.toFixed(1)}</td>
                    <td>${order.agent_id}</td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', row);
        });
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
        if (this.charts.gdp) {
             this.charts.gdp.destroy();
             this.charts.gdp = null;
        }
        if (this.charts.wealthDist) {
             this.charts.wealthDist.destroy();
             this.charts.wealthDist = null;
        }
        if (this.charts.householdNeeds) {
             this.charts.householdNeeds.destroy();
             this.charts.householdNeeds = null;
        }
        if (this.charts.firmNeeds) {
             this.charts.firmNeeds.destroy();
             this.charts.firmNeeds = null;
        }
        if (this.charts.salesByGood) {
             this.charts.salesByGood.destroy();
             this.charts.salesByGood = null;
        }
    }
};
