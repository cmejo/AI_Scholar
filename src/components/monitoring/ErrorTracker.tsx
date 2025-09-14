import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';

interface ErrorEvent {
  id: string;
  timestamp: Date;
  message: string;
  stack?: string;
  component?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  resolved: boolean;
}

interface ErrorTrackerProps {
  isVisible: boolean;
  onToggle: () => void;
}

export const ErrorTracker: React.FC<ErrorTrackerProps> = ({ isVisible, onToggle }) => {
  const [errors, setErrors] = useState<ErrorEvent[]>([]);
  const [filter, setFilter] = useState<'all' | 'unresolved'>('unresolved');

  useEffect(() => {
    // Global error handler
    const handleError = (event: ErrorEvent) => {
      console.error('Global Error:', event);
      
      const errorEvent: ErrorEvent = {
        id: Date.now().toString(),
        timestamp: new Date(),
        message: event.message || 'Unknown error',
        stack: event.stack,
        component: event.component,
        severity: determineSeverity(event.message),
        resolved: false
      };

      setErrors(prev => [errorEvent, ...prev.slice(0, 49)]); // Keep last 50 errors
    };

    // Listen for custom error events
    window.addEventListener('app-error' as any, handleError);
    
    // Global error boundary fallback
    window.addEventListener('error', (event) => {
      handleError({
        id: '',
        timestamp: new Date(),
        message: event.message,
        stack: event.error?.stack,
        severity: 'high',
        resolved: false
      });
    });

    return () => {
      window.removeEventListener('app-error' as any, handleError);
      window.removeEventListener('error', handleError);
    };
  }, []);

  const determineSeverity = (message: string): ErrorEvent['severity'] => {
    if (message.includes('critical') || message.includes('fatal')) return 'critical';
    if (message.includes('error') || message.includes('failed')) return 'high';
    if (message.includes('warning') || message.includes('deprecated')) return 'medium';
    return 'low';
  };

  const markResolved = (id: string) => {
    setErrors(prev => prev.map(error => 
      error.id === id ? { ...error, resolved: true } : error
    ));
  };

  const clearErrors = () => {
    setErrors([]);
  };

  const filteredErrors = errors.filter(error => 
    filter === 'all' || !error.resolved
  );

  const getSeverityColor = (severity: ErrorEvent['severity']) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-blue-600 bg-blue-50';
    }
  };

  if (!isVisible) {
    return (
      <Button
        onClick={onToggle}
        className="fixed bottom-4 right-20 z-50 bg-red-500 hover:bg-red-600 text-white"
        size="sm"
      >
        Errors ({errors.filter(e => !e.resolved).length})
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-4 right-4 w-96 max-h-96 z-50 shadow-lg">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-sm">Error Tracker</CardTitle>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFilter(filter === 'all' ? 'unresolved' : 'all')}
            >
              {filter === 'all' ? 'Show Unresolved' : 'Show All'}
            </Button>
            <Button variant="outline" size="sm" onClick={clearErrors}>
              Clear
            </Button>
            <Button variant="outline" size="sm" onClick={onToggle}>
              ×
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="overflow-y-auto max-h-64">
        {filteredErrors.length === 0 ? (
          <p className="text-sm text-gray-500">No errors to display</p>
        ) : (
          <div className="space-y-2">
            {filteredErrors.map((error) => (
              <div
                key={error.id}
                className={`p-2 rounded text-xs ${getSeverityColor(error.severity)} ${
                  error.resolved ? 'opacity-50' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-medium">{error.message}</div>
                    <div className="text-xs opacity-75">
                      {error.timestamp.toLocaleTimeString()}
                      {error.component && ` • ${error.component}`}
                    </div>
                  </div>
                  {!error.resolved && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => markResolved(error.id)}
                      className="ml-2 h-6 w-6 p-0"
                    >
                      ✓
                    </Button>
                  )}
                </div>
                {error.stack && (
                  <details className="mt-1">
                    <summary className="cursor-pointer text-xs">Stack trace</summary>
                    <pre className="text-xs mt-1 whitespace-pre-wrap">{error.stack}</pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Utility function to report errors
export const reportError = (message: string, component?: string, stack?: string) => {
  const event = new CustomEvent('app-error', {
    detail: { message, component, stack }
  });
  window.dispatchEvent(event);
};