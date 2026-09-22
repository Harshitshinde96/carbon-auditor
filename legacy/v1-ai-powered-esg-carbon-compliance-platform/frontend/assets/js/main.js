document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initSidebar();
    injectIcons();
});

function initTheme() {
    const toggleBtn = DOM.el('#theme-toggle');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const storedTheme = localStorage.getItem('theme');
    
    let currentTheme = storedTheme || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    if (toggleBtn) {
        toggleBtn.innerHTML = currentTheme === 'dark' ? Icons.sun : Icons.moon;
        
        toggleBtn.addEventListener('click', () => {
            currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', currentTheme);
            localStorage.setItem('theme', currentTheme);
            toggleBtn.innerHTML = currentTheme === 'dark' ? Icons.sun : Icons.moon;
        });
    }
}

function initSidebar() {
    const sidebar = DOM.el('.sidebar');
    const menuBtn = DOM.el('#mobile-menu-btn');
    let overlay = DOM.el('.overlay');
    
    if (!overlay) {
        overlay = DOM.create('div', 'overlay');
        document.body.appendChild(overlay);
    }

    if (menuBtn && sidebar) {
        menuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        });
        
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }
}

function injectIcons() {
    document.querySelectorAll('[data-icon]').forEach(el => {
        const iconName = el.getAttribute('data-icon');
        if (Icons[iconName]) {
            el.innerHTML = Icons[iconName];
        }
    });
}
