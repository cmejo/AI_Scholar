import React from 'react';

interface MobileCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  onLongPress?: () => void;
  variant?: 'default' | 'elevated' | 'outlined';
  size?: 'small' | 'medium' | 'large';
  interactive?: boolean;
}

export const MobileCard: React.FC<MobileCardProps> = ({
  children,
  className = '',
  onClick,
  onLongPress,
  variant = 'default',
  size = 'medium',
  interactive = false
}) => {
  const baseClasses = 'rounded-lg transition-all duration-200 touch-manipulation';
  
  const variantClasses = {
    default: 'bg-gray-800 border border-gray-700',
    elevated: 'bg-gray-800 shadow-lg border border-gray-700 backdrop-blur-sm',
    outlined: 'bg-transparent border-2 border-gray-600'
  };

  const sizeClasses = {
    small: 'p-3',
    medium: 'p-4',
    large: 'p-6'
  };

  const interactiveClasses = interactive || onClick ? 
    'active:scale-98 active:opacity-80 hover:bg-gray-750 cursor-pointer' : '';

  const combinedClasses = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${sizeClasses[size]}
    ${interactiveClasses}
    ${className}
  `.trim();

  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    if (onLongPress) {
      e.preventDefault();
      onLongPress();
    }
  };

  if (onClick || onLongPress) {
    return (
      <div
        className={combinedClasses}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick();
          }
        }}
      >
        {children}
      </div>
    );
  }

  return (
    <div className={combinedClasses}>
      {children}
    </div>
  );
};