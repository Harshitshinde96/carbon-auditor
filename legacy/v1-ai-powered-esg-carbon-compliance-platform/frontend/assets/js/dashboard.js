document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});

async function loadDashboardData() {
    try {
        const data = await API.get('dashboard?userId=user143', 'mock-dashboard.json');
        
        renderStats(data.summary);
        renderCharts(data);
        renderTable(data.recentBills);
    } catch (error) {
        console.error("Failed to load dashboard data", error);
        DOM.el('#stats-container').innerHTML = `<div class="text-error col-span-3 text-center py-4 font-bold">Failed to load data. Please check your backend connection.</div>`;
    }
}

function renderStats(summary) {
    const container = DOM.el('#stats-container');
    container.innerHTML = `
<div class="bg-surface-container-lowest border border-outline-variant p-4 flex flex-col justify-between hover:shadow-sm transition-shadow">
<div class="flex justify-between items-start">
<span class="font-label text-[10px] uppercase tracking-wider text-on-surface-variant font-bold">Total Carbon Emissions</span>
<span class="material-symbols-outlined text-sm text-on-surface-variant">co2</span>
</div>
<div class="mt-4 flex items-baseline gap-2">
<h2 class="text-2xl font-black tracking-tighter">${DOM.formatNumber(summary.totalCarbonEmission)}</h2>
<span class="text-xs text-on-surface-variant font-medium">kgCO2e</span>
</div>
</div>

<div class="bg-surface-container-lowest border border-outline-variant p-4 flex flex-col justify-between hover:shadow-sm transition-shadow">
<div class="flex justify-between items-start">
<span class="font-label text-[10px] uppercase tracking-wider text-on-surface-variant font-bold">Total Spend</span>
<span class="material-symbols-outlined text-sm text-on-surface-variant">payments</span>
</div>
<div class="mt-4 flex items-baseline gap-2">
<h2 class="text-2xl font-black tracking-tighter">${DOM.formatCurrency(summary.totalAmountPaid)}</h2>
<span class="text-xs text-on-surface-variant font-medium">USD</span>
</div>
</div>

<div class="bg-surface-container-lowest border border-outline-variant p-4 flex flex-col justify-between hover:shadow-sm transition-shadow">
<div class="flex justify-between items-start">
<span class="font-label text-[10px] uppercase tracking-wider text-on-surface-variant font-bold">Avg Monthly Carbon</span>
<span class="material-symbols-outlined text-sm text-on-surface-variant">calendar_month</span>
</div>
<div class="mt-4 flex items-baseline gap-2">
<h2 class="text-2xl font-black tracking-tighter">${DOM.formatNumber(summary.averageMonthlyCarbon)}</h2>
<span class="text-xs text-on-surface-variant font-medium">kgCO2e</span>
</div>
</div>
    `;
}

function renderCharts(data) {
    // Check if data is coming from Live API (which uses monthlyEmission array) or Mock (which uses carbonTrend object)
    let carbonTrendData = data.carbonTrend;
    let distributionData = data.billDistribution;

    if (!carbonTrendData && data.monthlyEmission) {
        // Transform Live API data to CustomChart format
        carbonTrendData = {
            labels: data.monthlyEmission.map(item => item.month),
            datasets: [{ data: data.monthlyEmission.map(item => item.carbon) }]
        };
    }

    if (Array.isArray(distributionData)) {
        // Transform Live API bill distribution array to CustomChart format
        distributionData = {
            labels: data.billDistribution.map(item => item.type),
            datasets: [{ data: data.billDistribution.map(item => item.count) }]
        };
    }

    // Default to empty structure to prevent crashes if no data
    if (!carbonTrendData) carbonTrendData = { labels: [], datasets: [{data: []}] };
    if (!distributionData || !distributionData.labels) distributionData = { labels: [], datasets: [{data: []}] };

    new CustomChart('carbonTrendChart', 'line', carbonTrendData);
    new CustomChart('sourcePieChart', 'pie', distributionData);
}

function renderTable(bills) {
    const tbody = DOM.el('#recent-bills-body');
    tbody.innerHTML = ''; 
    
    if (!bills || bills.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-on-surface-variant py-4 text-xs font-medium">No recent bills found.</td></tr>`;
        return;
    }
    
    bills.forEach(bill => {
        let statusBadge = '';
        if (bill.processingStatus === 'COMPLETED') {
            statusBadge = `<span class="inline-block px-2 py-0.5 bg-black text-white text-[9px] font-black uppercase rounded tracking-tighter border border-black">Completed</span>`;
        } else if (bill.processingStatus === 'FAILED') {
            statusBadge = `<span class="inline-block px-2 py-0.5 bg-error-container text-on-error-container text-[9px] font-black uppercase rounded tracking-tighter border border-error">Failed</span>`;
        } else {
            statusBadge = `<span class="inline-block px-2 py-0.5 bg-surface-container-highest text-on-surface-variant text-[9px] font-black uppercase rounded tracking-tighter border border-outline-variant">Processing</span>`;
        }
        
        const dateStr = bill.updatedAt ? new Date(bill.updatedAt).toLocaleDateString() : bill.billingMonth;
        
        const tr = document.createElement('tr');
        tr.className = "hover:bg-surface-container-low transition-colors group";
        tr.innerHTML = `
            <td class="px-4 py-3 text-[11px] font-medium">${dateStr}</td>
            <td class="px-4 py-3">
                <div class="flex flex-col">
                    <span class="text-[11px] font-black uppercase">${bill.billId.split('-')[0]}</span>
                    <span class="text-[9px] text-on-surface-variant font-medium uppercase tracking-widest">${bill.billType} • ${DOM.formatNumber(bill.carbonEmission)} kgCO2e</span>
                </div>
            </td>
            <td class="px-4 py-3 text-[11px] font-black text-right">${DOM.formatCurrency(bill.billAmount, bill.currency || 'USD')}</td>
            <td class="px-4 py-3 text-center">
                ${statusBadge}
            </td>
            <td class="px-4 py-3 text-right">
                <span class="material-symbols-outlined text-sm cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity">more_vert</span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
