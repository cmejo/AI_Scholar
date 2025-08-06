import React from 'react';

/**
 * SVG filters for color blindness support
 * These filters simulate color vision deficiencies to help with accessibility
 */
export const ColorBlindnessFilters: React.FC = () => {
  return (
    <svg className="colorblind-filters sr-only" aria-hidden="true">
      <defs>
        {/* Protanopia (Red-blind) filter */}
        <filter id="protanopia-filter">
          <feColorMatrix
            type="matrix"
            values="0.567 0.433 0     0 0
                    0.558 0.442 0     0 0
                    0     0.242 0.758 0 0
                    0     0     0     1 0"
          />
        </filter>

        {/* Deuteranopia (Green-blind) filter */}
        <filter id="deuteranopia-filter">
          <feColorMatrix
            type="matrix"
            values="0.625 0.375 0     0 0
                    0.7   0.3   0     0 0
                    0     0.3   0.7   0 0
                    0     0     0     1 0"
          />
        </filter>

        {/* Tritanopia (Blue-blind) filter */}
        <filter id="tritanopia-filter">
          <feColorMatrix
            type="matrix"
            values="0.95  0.05  0     0 0
                    0     0.433 0.567 0 0
                    0     0.475 0.525 0 0
                    0     0     0     1 0"
          />
        </filter>

        {/* Protanomaly (Red-weak) filter */}
        <filter id="protanomaly-filter">
          <feColorMatrix
            type="matrix"
            values="0.817 0.183 0     0 0
                    0.333 0.667 0     0 0
                    0     0.125 0.875 0 0
                    0     0     0     1 0"
          />
        </filter>

        {/* Deuteranomaly (Green-weak) filter */}
        <filter id="deuteranomaly-filter">
          <feColorMatrix
            type="matrix"
            values="0.8   0.2   0     0 0
                    0.258 0.742 0     0 0
                    0     0.142 0.858 0 0
                    0     0     0     1 0"
          />
        </filter>

        {/* Tritanomaly (Blue-weak) filter */}
        <filter id="tritanomaly-filter">
          <feColorMatrix
            type="matrix"
            values="0.967 0.033 0     0 0
                    0     0.733 0.267 0 0
                    0     0.183 0.817 0 0
                    0     0     0     1 0"
          />
        </filter>

        {/* Achromatopsia (Complete color blindness) filter */}
        <filter id="achromatopsia-filter">
          <feColorMatrix
            type="matrix"
            values="0.299 0.587 0.114 0 0
                    0.299 0.587 0.114 0 0
                    0.299 0.587 0.114 0 0
                    0     0     0     1 0"
          />
        </filter>

        {/* Achromatomaly (Partial color blindness) filter */}
        <filter id="achromatomaly-filter">
          <feColorMatrix
            type="matrix"
            values="0.618 0.320 0.062 0 0
                    0.163 0.775 0.062 0 0
                    0.163 0.320 0.516 0 0
                    0     0     0     1 0"
          />
        </filter>
      </defs>
    </svg>
  );
};

export default ColorBlindnessFilters;