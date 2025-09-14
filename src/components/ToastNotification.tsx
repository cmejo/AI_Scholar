import React, { useState, useEffect } from 'react';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

interface ToastNotificationProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

export const ToastNotification: React.FC<ToastNotificationProps> = ({ toast, onRemove }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    // Slide in animation
    setTimeout(() => setIsVisible(true), 10);

    // Auto dismiss
    const timer = setTimeout(() => {
      setIsLeaving(true);
      setTimeout(() => onRemove(toast.id), 300);
    }, toast.duration || 3000);

    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onRemove]);

  const getToastStyles = () => {
    const baseStyles = {
      position: 'fixed' as const,
      top: '20px',
      right: isVisible && !isLeaving ? '20px' : '-400px',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      border: `1px solid ${getColorByType().border}`,
      borderRadius: '12px',
      padding: '16px 20px',
      minWidth: '300px',
      maxWidth: '400px',
      boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
      zIndex: 10000,
      transition: 'all 0.3s ease',
      transform: isLeaving ? 'translateX(100%)' : 'translateX(0)',
      opacity: isVisible && !isLeaving ? 1 : 0
    };
    return baseStyles;
  };

  const getColorByType = () => {
    switch (toast.type) {
      case 'success':
        return { color: '#4ade80', border: 'rgba(74, 222, 128, 0.3)', bg: 'rgba(74, 222, 128, 0.1)' };
      case 'error':
        return { color: '#ef4444', border: 'rgba(239, 68, 68, 0.3)', bg: 'rgba(239, 68, 68, 0.1)' };
      case 'warning':
        return { color: '#f59e0b', border: 'rgba(245, 158, 11, 0.3)', bg: 'rgba(245, 158, 11, 0.1)' };
      case 'info':
      default:
        return { color: '#60a5fa', border: 'rgba(96, 165, 250, 0.3)', bg: 'rgba(96, 165, 250, 0.1)' };
    }
  };

  const getIcon = () => {
    switch (toast.type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return 'ℹ️';
    }
  };

  const colors = getColorByType();

  return (
    <div style={getToastStyles()}>
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px'
      }}>
        <div style={{
          background: colors.bg,
          padding: '8px',
          borderRadius: '8px',
          fontSize: '16px'
        }}>
          {getIcon()}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{
            color: 'white',
            fontSize: '14px',
            fontWeight: '600',
            marginBottom: '4px'
          }}>
            {toast.type.charAt(0).toUpperCase() + toast.type.slice(1)}
          </div>
          <div style={{
            color: '#cbd5e1',
            fontSize: '13px',
            lineHeight: '1.4'
          }}>
            {toast.message}
          </div>
        </div>
        <button
          onClick={() => {
            setIsLeaving(true);
            setTimeout(() => onRemove(toast.id), 300);
          }}
          style={{
            background: 'none',
            border: 'none',
            color: '#9ca3af',
            cursor: 'pointer',
            fontSize: '18px',
            padding: '4px',
            borderRadius: '4px',
            transition: 'color 0.2s ease'
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = colors.color}
          onMouseLeave={(e) => e.currentTarget.style.color = '#9ca3af'}
        >
          ×
        </button>
      </div>
    </div>
  );
};

// Toast Container Component
interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemove }) => {
  return (
    <>
      {toasts.map((toast, index) => (
        <div key={toast.id} style={{ top: `${20 + index * 80}px` }}>
          <ToastNotification toast={toast} onRemove={onRemove} />
        </div>
      ))}
    </>
  );
};

// Hook for using toasts
export const useToast = () => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (message: string, type: Toast['type'] = 'info', duration?: number) => {
    const id = Date.now().toString();
    const newToast: Toast = { id, message, type, duration };
    setToasts(prev => [...prev, newToast]);
  };

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  const showSuccess = (message: string, duration?: number) => addToast(message, 'success', duration);
  const showError = (message: string, duration?: number) => addToast(message, 'error', duration);
  const showWarning = (message: string, duration?: number) => addToast(message, 'warning', duration);
  const showInfo = (message: string, duration?: number) => addToast(message, 'info', duration);

  return {
    toasts,
    addToast,
    removeToast,
    showSuccess,
    showError,
    showWarning,
    showInfo
  };
};