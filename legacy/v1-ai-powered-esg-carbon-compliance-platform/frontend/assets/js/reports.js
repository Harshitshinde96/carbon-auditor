document.addEventListener('DOMContentLoaded', () => {
    loadReports();
});

async function loadReports() {
    try {
        const data = await API.get('reports?userId=user143', 'mock-reports.json');
        renderReports(data.reports);
    } catch (error) {
        console.error("Failed to load reports", error);
        DOM.el('#reports-body').innerHTML = `<tr><td colspan="6" class="text-center text-error py-4 font-bold text-[11px]">Failed to load reports.</td></tr>`;
    }
}

function renderReports(reports) {
    const tbody = DOM.el('#reports-body');
    tbody.innerHTML = '';
    
    if (!reports || reports.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-on-surface-variant py-4 font-medium text-[11px]">No reports found.</td></tr>`;
        return;
    }
    
    reports.forEach((report, index) => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-surface-container-low transition-colors group";
        
        let statusBadge = '';
        if (report.status === 'Ready') {
            statusBadge = `<span class="inline-block px-2 py-0.5 bg-black text-white text-[9px] font-black uppercase rounded tracking-tighter border border-black">Ready</span>`;
        } else {
            statusBadge = `<span class="inline-block px-2 py-0.5 bg-surface-container-highest text-on-surface-variant text-[9px] font-black uppercase rounded tracking-tighter border border-outline-variant">${report.status}</span>`;
        }
        
        tr.innerHTML = `
            <td class="px-4 py-3 text-[11px] font-black">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-sm">folder</span>
                    ${report.title}
                </div>
            </td>
            <td class="px-4 py-3 text-[11px] font-medium">${report.type}</td>
            <td class="px-4 py-3 text-[11px] font-medium">${DOM.formatDate(report.date)}</td>
            <td class="px-4 py-3 text-[11px] font-medium">${report.size}</td>
            <td class="px-4 py-3 text-center">${statusBadge}</td>
            <td class="px-4 py-3 text-right">
                <button class="text-[9px] font-black uppercase border border-outline-variant px-2 py-1 hover:bg-primary hover:text-white transition-colors rounded">Download PDF</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
