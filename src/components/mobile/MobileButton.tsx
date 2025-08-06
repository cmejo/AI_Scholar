import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MobileButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  onLongPress?: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  disabled?: boolean;
  loading?: boolean;
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const MobileButton: React.FC<MobileButtonProps> = ({
  children,
  onClick,
  onLongPress,
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  disabled = false,
  loading = false,
  icon: Icon,
  iconPosition = 'left',
  className = '',
  type = 'button'
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 touch-manipulation tap-highlight-none focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed min-h-touch-target';

  const variantClasses = {
    primary: 'bg-gradient-to-r from-purple-600 to-emerald-600 text-white hover:from-purple-700 hover:to-emerald-700 active:scale-95 focus:ring-purple-500 shadow-lg',
    secondary: 'bg-gray-700 text-white hover:bg-gray-600 active:bg-gray-800 active:scale-95 focus:ring-gray-500',
    outline: 'border-2 border-gray-600 text-gray-300 hover:bg-gray-700 hover:border-gray-500 active:scale-95 focus:ring-gray-500',
    ghost: 'text-gray-300 hover:bg-gray-700 active:bg-gray-600 active:scale-95 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 active:scale-95 focus:ring-red-500 shadow-lg'
  };

  const sizeClasses = {
    small: 'px-3 py-2 text-sm gap-2',
    medium: 'px-4 py-3 text-base gap-2',
    large: 'px-6 py-4 text-lg gap-3'
  };

  const widthClasses = fullWidth ? 'w-full' : '';

  const combinedClasses = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${sizeClasses[size]}
    ${widthClasses}
    ${disabled || loading ? 'pointer-events-none' : ''}
    ${className}
  `.trim();

  const handleClick = () => {
    if (!disabled && !loading && onClick) {
      onClick();
    }
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    if (onLongPress && !disabled && !loading) {
      e.preventDefault();
      onLongPress();
    }
  };

  return (
    <button
      type={type}
      className={combinedClasses}
      onClick={handleClick}
      onContextMenu={handleContextMenu}
      disabled={disabled || loading}
      aria-disabled={disabled || loading}
    >
      {loading && (
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
      )}
      
      {!loading && Icon && iconPosition === 'left' && (
        <Icon size={size === 'small' ? 16 : size === 'large' ? 24 : 20} />
      )}
      
      {!loading && (
        <span className={loading ? 'opacity-0' : ''}>{children}</span>
      )}
      
      {!loading && Icon && iconPosition === 'right' && (
        <Icon size={size === 'small' ? 16 : size === 'large' ? 24 : 20} />
      )}
    </button>
  );
};