/**
 * Custom Vanilla JS HTML5 Canvas Chart Engine
 * Lightweight, 0-dependency native charts.
 */
class CustomChart {
    constructor(canvasId, type, data, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.type = type;
        this.data = data;
        
        const rootStyles = getComputedStyle(document.documentElement);
        const primary = rootStyles.getPropertyValue('--clr-primary').trim() || '#2563EB';
        const secondary = rootStyles.getPropertyValue('--clr-secondary').trim() || '#14B8A6';
        const textMuted = rootStyles.getPropertyValue('--clr-text-muted').trim() || '#94A3B8';
        const gridBorder = rootStyles.getPropertyValue('--clr-border').trim() || '#E2E8F0';
        
        this.options = {
            padding: 40,
            primaryColor: primary,
            secondaryColor: secondary,
            textColor: textMuted,
            gridColor: gridBorder,
            font: '12px Inter, sans-serif',
            ...options
        };
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        // Listen for theme changes to redraw grid lines with correct colors
        const observer = new MutationObserver(() => {
            this.updateThemeColors();
            this.draw();
        });
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    }
    
    updateThemeColors() {
        const rootStyles = getComputedStyle(document.documentElement);
        this.options.primaryColor = rootStyles.getPropertyValue('--clr-primary').trim() || '#2563EB';
        this.options.textColor = rootStyles.getPropertyValue('--clr-text-muted').trim() || '#94A3B8';
        this.options.gridColor = rootStyles.getPropertyValue('--clr-border').trim() || '#E2E8F0';
    }
    
    resize() {
        const parent = this.canvas.parentElement;
        const dpr = window.devicePixelRatio || 1;
        const rect = parent.getBoundingClientRect();
        
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        
        this.ctx.scale(dpr, dpr);
        this.canvas.style.width = `${rect.width}px`;
        this.canvas.style.height = `${rect.height}px`;
        
        this.draw();
    }
    
    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        if (this.type === 'line') this.drawLineChart();
        if (this.type === 'bar') this.drawBarChart();
        if (this.type === 'pie') this.drawPieChart();
    }
    
    drawLineChart() {
        const { labels, datasets } = this.data;
        const { padding, primaryColor, gridColor, textColor, font } = this.options;
        const width = this.canvas.width / (window.devicePixelRatio || 1);
        const height = this.canvas.height / (window.devicePixelRatio || 1);
        
        const chartW = width - padding * 2;
        const chartH = height - padding * 2;
        
        const dataPoints = datasets[0].data;
        let maxVal = Math.max(...dataPoints);
        if (maxVal === 0) maxVal = 100;
        // Add 10% padding to top
        maxVal = maxVal * 1.1; 
        
        // Draw grid lines
        this.ctx.beginPath();
        this.ctx.strokeStyle = gridColor;
        this.ctx.lineWidth = 1;
        const steps = 4;
        for (let i = 0; i <= steps; i++) {
            const y = padding + (chartH / steps) * i;
            this.ctx.moveTo(padding, y);
            this.ctx.lineTo(width - padding, y);
            
            // Y-axis Labels
            this.ctx.fillStyle = textColor;
            this.ctx.font = font;
            this.ctx.textAlign = 'right';
            const val = maxVal - (maxVal / steps) * i;
            this.ctx.fillText(Math.round(val), padding - 10, y + 4);
        }
        this.ctx.stroke();
        
        // Draw Line
        const stepX = dataPoints.length > 1 ? chartW / (dataPoints.length - 1) : chartW;
        
        this.ctx.beginPath();
        this.ctx.strokeStyle = primaryColor;
        this.ctx.lineWidth = 3;
        this.ctx.lineJoin = 'round';
        
        dataPoints.forEach((val, i) => {
            const x = padding + (i * stepX);
            const y = padding + chartH - (val / maxVal * chartH);
            if (i === 0) this.ctx.moveTo(x, y);
            else this.ctx.lineTo(x, y);
            
            // X-axis labels
            this.ctx.fillStyle = textColor;
            this.ctx.textAlign = 'center';
            this.ctx.fillText(labels[i] || '', x, height - padding + 20);
        });
        this.ctx.stroke();
        
        // Draw Gradient Fill
        if (dataPoints.length > 0) {
            this.ctx.lineTo(padding + (dataPoints.length - 1) * stepX, padding + chartH);
            this.ctx.lineTo(padding, padding + chartH);
            this.ctx.closePath();
            
            const gradient = this.ctx.createLinearGradient(0, padding, 0, padding + chartH);
            gradient.addColorStop(0, `${primaryColor}33`); // 20% opacity
            gradient.addColorStop(1, `${primaryColor}00`); // 0% opacity
            
            this.ctx.fillStyle = gradient;
            this.ctx.fill();
        }
    }
    
    drawBarChart() {
        const { labels, datasets } = this.data;
        const { padding, primaryColor, gridColor, textColor, font } = this.options;
        const width = this.canvas.width / (window.devicePixelRatio || 1);
        const height = this.canvas.height / (window.devicePixelRatio || 1);
        
        const chartW = width - padding * 2;
        const chartH = height - padding * 2;
        
        const dataPoints = datasets[0].data;
        let maxVal = Math.max(...dataPoints);
        if (maxVal === 0) maxVal = 100;
        maxVal = maxVal * 1.1;
        
        // Grid
        this.ctx.beginPath();
        this.ctx.strokeStyle = gridColor;
        for (let i = 0; i <= 4; i++) {
            const y = padding + (chartH / 4) * i;
            this.ctx.moveTo(padding, y);
            this.ctx.lineTo(width - padding, y);
            this.ctx.fillStyle = textColor;
            this.ctx.font = font;
            this.ctx.textAlign = 'right';
            this.ctx.fillText(Math.round(maxVal - (maxVal/4)*i), padding - 10, y + 4);
        }
        this.ctx.stroke();
        
        // Bars
        const barW = (chartW / Math.max(dataPoints.length, 1)) * 0.5;
        const gap = (chartW / Math.max(dataPoints.length, 1)) * 0.5;
        
        dataPoints.forEach((val, i) => {
            const barH = (val / maxVal) * chartH;
            const x = padding + (gap / 2) + i * (barW + gap);
            const y = padding + chartH - barH;
            
            this.ctx.fillStyle = primaryColor;
            this.ctx.beginPath();
            this.ctx.roundRect(x, y, barW, barH, [4, 4, 0, 0]);
            this.ctx.fill();
            
            this.ctx.fillStyle = textColor;
            this.ctx.textAlign = 'center';
            this.ctx.fillText(labels[i] || '', x + barW/2, height - padding + 20);
        });
    }
    
    drawPieChart() {
        const { labels, datasets } = this.data;
        const dataPoints = datasets[0].data;
        
        const rootStyles = getComputedStyle(document.documentElement);
        const colors = [
            rootStyles.getPropertyValue('--clr-primary').trim() || '#2563EB',
            rootStyles.getPropertyValue('--clr-secondary').trim() || '#14B8A6',
            rootStyles.getPropertyValue('--clr-warning').trim() || '#F59E0B',
            rootStyles.getPropertyValue('--clr-danger').trim() || '#EF4444'
        ];
        
        const total = dataPoints.reduce((a, b) => a + b, 0) || 1; // Prevent div by 0
        
        const width = this.canvas.width / (window.devicePixelRatio || 1);
        const height = this.canvas.height / (window.devicePixelRatio || 1);
        
        const cx = width / 2;
        const cy = height / 2;
        const radius = Math.min(cx, cy) - this.options.padding + 20;
        
        let startAngle = -0.5 * Math.PI;
        
        dataPoints.forEach((val, i) => {
            const sliceAngle = (val / total) * 2 * Math.PI;
            
            this.ctx.beginPath();
            this.ctx.moveTo(cx, cy);
            this.ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
            this.ctx.closePath();
            
            this.ctx.fillStyle = colors[i % colors.length];
            this.ctx.fill();
            
            startAngle += sliceAngle;
        });
        
        // Inner circle (Donut)
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, radius * 0.65, 0, 2 * Math.PI);
        this.ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--clr-bg-card').trim() || '#fff';
        this.ctx.fill();
        
        // Total Label inside donut
        this.ctx.fillStyle = rootStyles.getPropertyValue('--clr-text-primary').trim() || '#0F172A';
        this.ctx.font = '600 16px Inter, sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(DOM.formatNumber(total), cx, cy);
    }
}
