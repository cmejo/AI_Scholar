import React, { useState, useRef, useEffect } from 'react';
import { LucideIcon, Eye, EyeOff } from 'lucide-react';

interface MobileInputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  onSubmit?: () => void;
  disabled?: boolean;
  error?: string;
  label?: string;
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  clearable?: boolean;
  autoFocus?: boolean;
  maxLength?: number;
  className?: string;
  inputClassName?: string;
  multiline?: boolean;
  rows?: number;
  resize?: boolean;
}

export const MobileInput: React.FC<MobileInputProps> = ({
  type = 'text',
  placeholder,
  value = '',
  onChange,
  onFocus,
  onBlur,
  onSubmit,
  disabled = false,
  error,
  label,
  icon: Icon,
  iconPosition = 'left',
  clearable = false,
  autoFocus = false,
  maxLength,
  className = '',
  inputClassName = '',
  multiline = false,
  rows = 3,
  resize = false
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (onChange) {
      onChange(e.target.value);
    }
  };

  const handleFocus = () => {
    setIsFocused(true);
    if (onFocus) {
      onFocus();
    }
  };

  const handleBlur = () => {
    setIsFocused(false);
    if (onBlur) {
      onBlur();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !multiline && onSubmit) {
      e.preventDefault();
      onSubmit();
    }
  };

  const handleClear = () => {
    if (onChange) {
      onChange('');
    }
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const inputType = type === 'password' && showPassword ? 'text' : type;

  const baseClasses = `
    w-full px-4 py-3 bg-gray-700 border rounded-lg text-white placeholder-gray-400 
    transition-all duration-200 touch-manipulation min-h-touch-target
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900
    disabled:opacity-50 disabled:cursor-not-allowed
    ${error ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:border-purple-500 focus:ring-purple-500'}
    ${isFocused ? 'ring-2' : ''}
    ${Icon && iconPosition === 'left' ? 'pl-12' : ''}
    ${Icon && iconPosition === 'right' || type === 'password' || clearable ? 'pr-12' : ''}
    ${multiline && !resize ? 'resize-none' : ''}
  `;

  const InputComponent = multiline ? 'textarea' : 'input';

  return (
    <div className={`relative ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-300 mb-2">
          {label}
          {error && <span className="text-red-400 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        {/* Left Icon */}
        {Icon && iconPosition === 'left' && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
            <Icon size={20} />
          </div>
        )}

        {/* Input/Textarea */}
        <InputComponent
          ref={inputRef as any}
          type={multiline ? undefined : inputType}
          placeholder={placeholder}
          value={value}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyPress={handleKeyPress}
          disabled={disabled}
          maxLength={maxLength}
          rows={multiline ? rows : undefined}
          className={`${baseClasses} ${inputClassName}`}
          style={{
            fontSize: '16px', // Prevent zoom on iOS
            WebkitAppearance: 'none', // Remove iOS styling
          }}
        />

        {/* Right Icons */}
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
          {/* Clear Button */}
          {clearable && value && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="text-gray-400 hover:text-gray-300 transition-colors touch-manipulation"
              aria-label="Clear input"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          )}

          {/* Password Toggle */}
          {type === 'password' && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-gray-400 hover:text-gray-300 transition-colors touch-manipulation"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          )}

          {/* Right Icon */}
          {Icon && iconPosition === 'right' && type !== 'password' && (
            <div className="text-gray-400">
              <Icon size={20} />
            </div>
          )}
        </div>
      </div>

      {/* Character Count */}
      {maxLength && (
        <div className="mt-1 text-xs text-gray-400 text-right">
          {value.length}/{maxLength}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-2 text-sm text-red-400 flex items-center space-x-1">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};