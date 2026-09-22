# Carbon Auditor Frontend

This is a premium, enterprise-grade Vanilla HTML/CSS/JS frontend for the Carbon Auditor platform. It is designed to match the modern aesthetics of top-tier SaaS products (Stripe, Vercel, Linear) without using any heavy external frameworks or libraries.

## Features
- **No Frameworks:** Pure HTML5, CSS3, and ES6+ JavaScript.
- **Custom Canvas Charts:** A proprietary native HTML Canvas chart engine for Line, Bar, and Pie charts without Chart.js.
- **Fully Responsive:** Adapts seamlessly to Mobile, Tablet, and Desktop.
- **Glassmorphism & Micro-animations:** Professional, subtle UI transitions and skeletons.
- **API Ready:** Uses an intuitive `API.get()` pattern that gracefully falls back to mock JSON files for local development.

## Project Structure
- `assets/css/`: Variables, styles, responsive layouts, components, and animations.
- `assets/js/`: API wrappers, DOM utilities, Custom Canvas renderer, SVG icons injected dynamically.
- `mock-*.json`: API response simulators.

## Setup
No `npm install` needed. Simply double-click `dashboard.html` (or `index.html`) to open the dashboard directly in your browser.
