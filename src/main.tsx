import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// Add SVG filters for color blindness support
const addColorBlindnessFilters = () => {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.style.position = 'absolute';
  svg.style.width = '0';
  svg.style.height = '0';
  svg.innerHTML = `
    <defs>
      <!-- Protanopia (Red-blind) filter -->
      <filter id="protanopia-filter">
        <feColorMatrix type="matrix" values="0.567 0.433 0 0 0
                                           0.558 0.442 0 0 0
                                           0 0.242 0.758 0 0
                                           0 0 0 1 0"/>
      </filter>
      
      <!-- Deuteranopia (Green-blind) filter -->
      <filter id="deuteranopia-filter">
        <feColorMatrix type="matrix" values="0.625 0.375 0 0 0
                                           0.7 0.3 0 0 0
                                           0 0.3 0.7 0 0
                                           0 0 0 1 0"/>
      </filter>
      
      <!-- Tritanopia (Blue-blind) filter -->
      <filter id="tritanopia-filter">
        <feColorMatrix type="matrix" values="0.95 0.05 0 0 0
                                           0 0.433 0.567 0 0
                                           0 0.475 0.525 0 0
                                           0 0 0 1 0"/>
      </filter>
    </defs>
  `;
  document.body.appendChild(svg);
};

// Initialize accessibility features
addColorBlindnessFilters();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
