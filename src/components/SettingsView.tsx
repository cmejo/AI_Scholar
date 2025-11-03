import React, { useState, useEffect } from 'react';
import {
    Settings, User, Bell, Database,
    Shield, Download, RefreshCw, Save,
    Monitor, Check
} from 'lucide-react';

interface SettingsSection {
    id: string;
    name: string;
    icon: React.ReactNode;
    description: string;
}

interface NotificationSetting {
    id: string;
    name: string;
    description: string;
    email: boolean;
    push: boolean;
    sms: boolean;
}

// Settings persistence constants
const SETTINGS_STORAGE_KEY = 'ai-scholar-settings';
const NOTIFICATIONS_STORAGE_KEY = 'ai-scholar-notifications';

// Default settings fallback
const defaultSettings = {
    // General Settings
    theme: 'dark',
    language: 'en',
    timezone: 'UTC',
    dateFormat: 'MM/DD/YYYY',
    autoSave: true,

    // Display Settings
    sidebarCollapsed: false,
    compactMode: false,
    animations: true,
    highContrast: false,

    // AI Settings
    defaultModel: 'llama3.1:8b',
    defaultDataset: 'ai_scholar',
    responseLength: 'medium',
    temperature: 0.7,

    // Privacy Settings
    dataCollection: true,
    analytics: true,
    crashReports: true,
    personalizedAds: false,

    // Performance Settings
    cacheSize: '1GB',
    maxConcurrentRequests: 5,
    requestTimeout: 30,
    enableGPU: true,

    // Account Settings
    fullName: 'Administrator',
    email: 'admin@aischolar.com',
    organization: 'AI Scholar Enterprise',
    role: 'Administrator'
};

const defaultNotifications = [
    { id: 'workflow_complete', name: 'Workflow Completion', description: 'When a workflow finishes executing', email: true, push: true, sms: false },
    { id: 'security_alerts', name: 'Security Alerts', description: 'Important security notifications', email: true, push: true, sms: true },
    { id: 'system_updates', name: 'System Updates', description: 'New features and updates', email: true, push: false, sms: false },
    { id: 'api_limits', name: 'API Limit Warnings', description: 'When approaching API limits', email: true, push: true, sms: false },
    { id: 'integration_status', name: 'Integration Status', description: 'Integration connection changes', email: false, push: true, sms: false },
    { id: 'document_processing', name: 'Document Processing', description: 'Document upload and processing status', email: false, push: true, sms: false }
];

// Settings persistence utilities
const loadSettingsFromStorage = () => {
    try {
        const storedSettings = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (storedSettings) {
            const parsed = JSON.parse(storedSettings);
            // Merge with defaults to ensure all properties exist
            return { ...defaultSettings, ...parsed };
        }
    } catch (error) {
        console.warn('Failed to load settings from localStorage:', error);
    }
    return defaultSettings;
};

const loadNotificationsFromStorage = () => {
    try {
        const storedNotifications = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
        if (storedNotifications) {
            const parsed = JSON.parse(storedNotifications);
            // Validate structure and merge with defaults
            if (Array.isArray(parsed) && parsed.length > 0) {
                return defaultNotifications.map(defaultNotif => {
                    const stored = parsed.find(n => n.id === defaultNotif.id);
                    return stored ? { ...defaultNotif, ...stored } : defaultNotif;
                });
            }
        }
    } catch (error) {
        console.warn('Failed to load notifications from localStorage:', error);
    }
    return defaultNotifications;
};

const saveSettingsToStorage = (settings: any) => {
    try {
        localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
        return true;
    } catch (error) {
        console.error('Failed to save settings to localStorage:', error);
        // Check if it's a quota exceeded error
        if (error instanceof DOMException && error.code === 22) {
            console.warn('localStorage quota exceeded. Attempting to clear old data...');
            try {
                // Try to clear some space by removing old data
                const keys = Object.keys(localStorage);
                const oldKeys = keys.filter(key => 
                    key.startsWith('ai-scholar-') && 
                    key !== SETTINGS_STORAGE_KEY && 
                    key !== NOTIFICATIONS_STORAGE_KEY
                );
                oldKeys.forEach(key => {
                    try {
                        localStorage.removeItem(key);
                    } catch (cleanupError) {
                        console.warn('Failed to remove old key:', key, cleanupError);
                    }
                });
                
                // Try saving again
                localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
                return true;
            } catch (retryError) {
                console.error('Failed to save settings even after cleanup:', retryError);
                return false;
            }
        }
        return false;
    }
};

const saveNotificationsToStorage = (notifications: any[]) => {
    try {
        localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(notifications));
        return true;
    } catch (error) {
        console.error('Failed to save notifications to localStorage:', error);
        // Check if it's a quota exceeded error
        if (error instanceof DOMException && error.code === 22) {
            console.warn('localStorage quota exceeded for notifications. Attempting to clear old data...');
            try {
                // Try to clear some space by removing old data
                const keys = Object.keys(localStorage);
                const oldKeys = keys.filter(key => 
                    key.startsWith('ai-scholar-') && 
                    key !== SETTINGS_STORAGE_KEY && 
                    key !== NOTIFICATIONS_STORAGE_KEY
                );
                oldKeys.forEach(key => {
                    try {
                        localStorage.removeItem(key);
                    } catch (cleanupError) {
                        console.warn('Failed to remove old key:', key, cleanupError);
                    }
                });
                
                // Try saving again
                localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(notifications));
                return true;
            } catch (retryError) {
                console.error('Failed to save notifications even after cleanup:', retryError);
                return false;
            }
        }
        return false;
    }
};

const SettingsView: React.FC = () => {
    const [activeSection, setActiveSection] = useState('general');
    const [settings, setSettings] = useState(loadSettingsFromStorage);
    const [notifications, setNotifications] = useState<NotificationSetting[]>(loadNotificationsFromStorage);
    const [showSaveConfirmation, setShowSaveConfirmation] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [focusedElement, setFocusedElement] = useState<string | null>(null);
    const [announcements, setAnnouncements] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [operationInProgress, setOperationInProgress] = useState<string | null>(null);
    const [retryCount, setRetryCount] = useState(0);
    const [lastError, setLastError] = useState<{message: string, timestamp: number} | null>(null);
    const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});
    const [networkError, setNetworkError] = useState<string | null>(null);
    const [criticalError, setCriticalError] = useState<string | null>(null);

    // Load settings on component mount with comprehensive error handling
    useEffect(() => {
        const loadInitialSettings = async () => {
            try {
                setIsLoading(true);
                setCriticalError(null);
                
                const loadedSettings = loadSettingsFromStorage();
                const loadedNotifications = loadNotificationsFromStorage();
                
                // Validate loaded data
                if (!loadedSettings || typeof loadedSettings !== 'object') {
                    throw new Error('Settings data is corrupted. Using defaults.');
                }
                
                if (!loadedNotifications || !Array.isArray(loadedNotifications)) {
                    throw new Error('Notifications data is corrupted. Using defaults.');
                }
                
                setSettings(loadedSettings);
                setNotifications(loadedNotifications);
                
                announceToScreenReader('Settings loaded successfully');
                
            } catch (error) {
                const errorMessage = handleError(error, 'load initial settings', false);
                setCriticalError(`Failed to load settings: ${errorMessage}. Using default values.`);
                
                // Fallback to defaults
                setSettings(defaultSettings);
                setNotifications(defaultNotifications);
                
                announceToScreenReader('Settings loaded with defaults due to error');
            } finally {
                setIsLoading(false);
            }
        };
        
        loadInitialSettings();
    }, []);

    // Accessibility helper functions
    const announceToScreenReader = (message: string) => {
        setAnnouncements(prev => [...prev, message]);
        // Clear announcement after a short delay
        setTimeout(() => {
            setAnnouncements(prev => prev.slice(1));
        }, 1000);
    };

    // Keyboard navigation handler
    const handleKeyDown = (event: React.KeyboardEvent, sectionId?: string) => {
        switch (event.key) {
            case 'ArrowUp':
            case 'ArrowDown':
                if (sectionId) {
                    event.preventDefault();
                    const sections = ['general', 'display', 'ai', 'notifications', 'performance', 'privacy', 'account'];
                    const currentIndex = sections.indexOf(sectionId);
                    const nextIndex = event.key === 'ArrowDown' 
                        ? (currentIndex + 1) % sections.length
                        : (currentIndex - 1 + sections.length) % sections.length;
                    
                    setActiveSection(sections[nextIndex]);
                    announceToScreenReader(`Navigated to ${sections[nextIndex]} settings`);
                }
                break;
            case 'Enter':
            case ' ':
                if (sectionId && sectionId !== activeSection) {
                    event.preventDefault();
                    setActiveSection(sectionId);
                    announceToScreenReader(`Opened ${sectionId} settings`);
                }
                break;
            case 'Escape':
                event.preventDefault();
                setFocusedElement(null);
                announceToScreenReader('Focus cleared');
                break;
        }
    };

    // Enhanced section change with accessibility
    const handleSectionChange = (sectionId: string) => {
        setActiveSection(sectionId);
        setFocusedElement(sectionId);
        announceToScreenReader(`Switched to ${sectionId} settings section`);
    };

    // Enhanced error handling functions with user-friendly messages
    const handleError = (error: any, operation: string, showToUser = true) => {
        console.error(`Error in ${operation}:`, error);
        
        let errorMessage: string;
        let userFriendlyMessage: string;
        
        // Determine error type and create appropriate messages
        if (error instanceof Error) {
            errorMessage = error.message;
            
            // Create user-friendly messages based on error type
            if (error.message.includes('localStorage') || error.message.includes('storage')) {
                userFriendlyMessage = 'Unable to save settings. Your browser storage may be full. Try clearing some data.';
            } else if (error.message.includes('network') || error.message.includes('fetch')) {
                userFriendlyMessage = 'Network connection issue. Please check your internet connection and try again.';
                setNetworkError(userFriendlyMessage);
            } else if (error.message.includes('validation') || error.message.includes('invalid')) {
                userFriendlyMessage = 'Invalid input detected. Please check your entries and try again.';
            } else if (error.message.includes('permission') || error.message.includes('access')) {
                userFriendlyMessage = 'Permission denied. You may not have the required access rights.';
            } else {
                userFriendlyMessage = `Settings operation failed: ${error.message}`;
            }
        } else if (typeof error === 'string') {
            errorMessage = error;
            userFriendlyMessage = error;
        } else {
            errorMessage = `An unexpected error occurred during ${operation}`;
            userFriendlyMessage = 'Something went wrong. Please try again or contact support if the problem persists.';
        }
        
        setLastError({
            message: errorMessage,
            timestamp: Date.now()
        });
        
        if (showToUser) {
            setSaveError(userFriendlyMessage);
            announceToScreenReader(`Error: ${userFriendlyMessage}`);
            
            // Auto-clear error after 8 seconds for user-friendly messages
            setTimeout(() => {
                setSaveError(null);
                setNetworkError(null);
            }, 8000);
        }
        
        return errorMessage;
    };

    // Retry mechanism for failed operations
    const withRetry = async <T>(
        operation: () => Promise<T>, 
        operationName: string, 
        maxRetries = 3
    ): Promise<T | null> => {
        let lastError: any = null;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                setRetryCount(attempt - 1);
                return await operation();
            } catch (error) {
                lastError = error;
                console.warn(`${operationName} attempt ${attempt} failed:`, error);
                
                if (attempt < maxRetries) {
                    // Exponential backoff: wait 1s, 2s, 4s between retries
                    const delay = Math.pow(2, attempt - 1) * 1000;
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
        
        // All retries failed
        handleError(lastError, operationName);
        setRetryCount(0);
        return null;
    };

    // Safe async operation wrapper
    const safeAsyncOperation = async (
        operation: () => Promise<void>,
        operationName: string,
        loadingMessage?: string
    ) => {
        try {
            setIsLoading(true);
            setOperationInProgress(loadingMessage || operationName);
            setSaveError(null);
            
            await withRetry(operation, operationName);
            
        } catch (error) {
            handleError(error, operationName);
        } finally {
            setIsLoading(false);
            setOperationInProgress(null);
        }
    };

    // Auto-save functionality when autoSave is enabled
    useEffect(() => {
        if (settings.autoSave) {
            const timeoutId = setTimeout(() => {
                const settingsSaved = saveSettingsToStorage(settings);
                const notificationsSaved = saveNotificationsToStorage(notifications);
                
                if (!settingsSaved || !notificationsSaved) {
                    setSaveError('Failed to auto-save settings. Storage may be full.');
                    setTimeout(() => setSaveError(null), 5000);
                }
            }, 1000); // Debounce auto-save by 1 second

            return () => clearTimeout(timeoutId);
        }
        // Return undefined when autoSave is disabled (no cleanup needed)
        return undefined;
    }, [settings, notifications]);

    const sections: SettingsSection[] = [
        { id: 'general', name: 'General', icon: <Settings size={20} />, description: 'Basic application settings' },
        { id: 'display', name: 'Display', icon: <Monitor size={20} />, description: 'Appearance and layout options' },
        { id: 'ai', name: 'AI Models', icon: <Database size={20} />, description: 'AI model and behavior settings' },
        { id: 'notifications', name: 'Notifications', icon: <Bell size={20} />, description: 'Notification preferences' },
        { id: 'privacy', name: 'Privacy', icon: <Shield size={20} />, description: 'Data and privacy controls' },
        { id: 'performance', name: 'Performance', icon: <RefreshCw size={20} />, description: 'Performance and resource settings' },
        { id: 'account', name: 'Account', icon: <User size={20} />, description: 'Account and profile settings' }
    ];

    // Enhanced setting validation
    const validateSetting = (key: string, value: any): string | null => {
        try {
            switch (key) {
                case 'theme':
                    if (!['dark', 'light', 'auto'].includes(value)) {
                        return 'Theme must be dark, light, or auto';
                    }
                    break;
                case 'language':
                    if (!['en', 'es', 'fr', 'de', 'zh'].includes(value)) {
                        return 'Invalid language selection';
                    }
                    break;
                case 'cacheSize':
                    if (!['256MB', '512MB', '1GB', '2GB', '4GB'].includes(value)) {
                        return 'Cache size must be between 256MB and 4GB';
                    }
                    break;
                case 'maxConcurrentRequests':
                    if (typeof value !== 'number' || value < 1 || value > 20) {
                        return 'Concurrent requests must be between 1 and 20';
                    }
                    break;
                case 'requestTimeout':
                    if (typeof value !== 'number' || value < 5 || value > 300) {
                        return 'Request timeout must be between 5 and 300 seconds';
                    }
                    break;
                case 'temperature':
                    if (typeof value !== 'number' || value < 0 || value > 2) {
                        return 'Temperature must be between 0 and 2';
                    }
                    break;
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (typeof value === 'string' && value.trim() && !emailRegex.test(value)) {
                        return 'Please enter a valid email address';
                    }
                    break;
                case 'fullName':
                    if (typeof value === 'string' && value.trim().length > 0 && value.trim().length < 2) {
                        return 'Full name must be at least 2 characters long';
                    }
                    break;
            }
            return null;
        } catch (error) {
            return `Validation error: ${error instanceof Error ? error.message : 'Unknown error'}`;
        }
    };

    const updateSetting = (key: string, value: any) => {
        try {
            // Clear previous validation errors for this field
            setValidationErrors(prev => {
                const newErrors = { ...prev };
                delete newErrors[key];
                return newErrors;
            });
            
            // Validate the setting value
            if (value === undefined || value === null) {
                throw new Error(`Invalid value for setting ${key}: ${value}`);
            }
            
            // Perform field-specific validation
            const validationError = validateSetting(key, value);
            if (validationError) {
                setValidationErrors(prev => ({
                    ...prev,
                    [key]: validationError
                }));
                announceToScreenReader(`Validation error for ${key}: ${validationError}`);
                return;
            }
            
            const newSettings = { ...settings, [key]: value };
            setSettings(newSettings);
            
            announceToScreenReader(`Updated ${key} setting`);
            
            // If auto-save is disabled, save immediately for critical settings
            if (!settings.autoSave) {
                safeAsyncOperation(
                    async () => {
                        const saved = saveSettingsToStorage(newSettings);
                        if (!saved) {
                            throw new Error('Failed to save setting. Storage may be full or unavailable.');
                        }
                    },
                    `save ${key} setting`,
                    'Saving setting...'
                );
            }
        } catch (error) {
            handleError(error, `update ${key} setting`);
            // Revert the setting change on error
            setSettings(prevSettings => prevSettings);
            
            // Set validation error for display
            setValidationErrors(prev => ({
                ...prev,
                [key]: error instanceof Error ? error.message : 'Failed to update setting'
            }));
        }
    };

    const updateNotification = (id: string, type: 'email' | 'push' | 'sms', value: boolean) => {
        try {
            // Validate notification parameters
            if (!id || !type || typeof value !== 'boolean') {
                throw new Error(`Invalid notification parameters: id=${id}, type=${type}, value=${value}`);
            }
            
            const notificationExists = notifications.some(notif => notif.id === id);
            if (!notificationExists) {
                throw new Error(`Notification with id ${id} not found`);
            }
            
            const newNotifications = notifications.map(notif =>
                notif.id === id ? { ...notif, [type]: value } : notif
            );
            setNotifications(newNotifications);
            
            announceToScreenReader(`Updated ${type} notification for ${id}`);
            
            // If auto-save is disabled, save immediately
            if (!settings.autoSave) {
                safeAsyncOperation(
                    async () => {
                        const saved = saveNotificationsToStorage(newNotifications);
                        if (!saved) {
                            throw new Error('Failed to save notification setting. Storage may be full or unavailable.');
                        }
                    },
                    `save ${type} notification setting`,
                    'Saving notification setting...'
                );
            }
        } catch (error) {
            handleError(error, `update ${type} notification for ${id}`);
            // Revert the notification change on error
            setNotifications(prevNotifications => prevNotifications);
        }
    };

    const saveSettings = () => {
        safeAsyncOperation(
            async () => {
                // Validate settings before saving
                if (!settings || typeof settings !== 'object') {
                    throw new Error('Invalid settings data');
                }
                
                if (!notifications || !Array.isArray(notifications)) {
                    throw new Error('Invalid notifications data');
                }
                
                const settingsSaved = saveSettingsToStorage(settings);
                const notificationsSaved = saveNotificationsToStorage(notifications);
                
                if (!settingsSaved) {
                    throw new Error('Failed to save settings to storage');
                }
                
                if (!notificationsSaved) {
                    throw new Error('Failed to save notifications to storage');
                }
                
                setShowSaveConfirmation(true);
                setSaveError(null);
                announceToScreenReader('Settings saved successfully');
                
                setTimeout(() => setShowSaveConfirmation(false), 2000);
            },
            'save settings',
            'Saving settings...'
        );
    };

    const exportSettings = () => {
        safeAsyncOperation(
            async () => {
                // Validate data before export
                if (!settings || typeof settings !== 'object') {
                    throw new Error('Invalid settings data - cannot export');
                }
                
                if (!notifications || !Array.isArray(notifications)) {
                    throw new Error('Invalid notifications data - cannot export');
                }
                
                const settingsData = {
                    settings,
                    notifications,
                    exportDate: new Date().toISOString(),
                    version: '1.0',
                    metadata: {
                        userAgent: navigator.userAgent,
                        timestamp: Date.now(),
                        settingsCount: Object.keys(settings).length,
                        notificationsCount: notifications.length
                    }
                };

                // Validate JSON serialization
                const jsonString = JSON.stringify(settingsData, null, 2);
                if (!jsonString || jsonString === '{}') {
                    throw new Error('Failed to serialize settings data');
                }

                // Check if browser supports blob creation
                if (!window.Blob) {
                    throw new Error('Your browser does not support file downloads');
                }

                const blob = new Blob([jsonString], { type: 'application/json' });
                
                // Check if blob was created successfully
                if (blob.size === 0) {
                    throw new Error('Failed to create export file');
                }

                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ai-scholar-settings-${new Date().toISOString().split('T')[0]}.json`;
                
                // Ensure the download link is accessible
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                // Clean up the URL object
                setTimeout(() => URL.revokeObjectURL(url), 100);
                
                announceToScreenReader('Settings exported successfully');
            },
            'export settings',
            'Preparing settings export...'
        );
    };

    const resetToDefaults = () => {
        if (window.confirm('Are you sure you want to reset all settings to their default values? This action cannot be undone.')) {
            safeAsyncOperation(
                async () => {
                    // Validate default settings before applying
                    if (!defaultSettings || typeof defaultSettings !== 'object') {
                        throw new Error('Default settings are corrupted');
                    }
                    
                    if (!defaultNotifications || !Array.isArray(defaultNotifications)) {
                        throw new Error('Default notifications are corrupted');
                    }
                    
                    // Create deep copies to avoid reference issues
                    const resetSettings = JSON.parse(JSON.stringify(defaultSettings));
                    const resetNotifications = JSON.parse(JSON.stringify(defaultNotifications));
                    
                    setSettings(resetSettings);
                    setNotifications(resetNotifications);
                    
                    // Save the reset settings
                    const settingsSaved = saveSettingsToStorage(resetSettings);
                    const notificationsSaved = saveNotificationsToStorage(resetNotifications);
                    
                    if (!settingsSaved) {
                        throw new Error('Failed to save reset settings to storage');
                    }
                    
                    if (!notificationsSaved) {
                        throw new Error('Failed to save reset notifications to storage');
                    }
                    
                    setShowSaveConfirmation(true);
                    announceToScreenReader('All settings reset to defaults successfully');
                    setTimeout(() => setShowSaveConfirmation(false), 2000);
                },
                'reset settings to defaults',
                'Resetting settings...'
            );
        }
    };

    const clearAllData = () => {
        if (window.confirm('Are you sure you want to clear all stored settings data? This will reset everything to defaults.')) {
            safeAsyncOperation(
                async () => {
                    try {
                        // Attempt to clear localStorage
                        localStorage.removeItem(SETTINGS_STORAGE_KEY);
                        localStorage.removeItem(NOTIFICATIONS_STORAGE_KEY);
                        
                        // Verify removal was successful
                        const settingsStillExist = localStorage.getItem(SETTINGS_STORAGE_KEY);
                        const notificationsStillExist = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
                        
                        if (settingsStillExist || notificationsStillExist) {
                            throw new Error('Failed to completely clear stored data. Some data may still exist.');
                        }
                        
                        // Reset to defaults with validation
                        if (!defaultSettings || typeof defaultSettings !== 'object') {
                            throw new Error('Default settings are corrupted');
                        }
                        
                        if (!defaultNotifications || !Array.isArray(defaultNotifications)) {
                            throw new Error('Default notifications are corrupted');
                        }
                        
                        setSettings(JSON.parse(JSON.stringify(defaultSettings)));
                        setNotifications(JSON.parse(JSON.stringify(defaultNotifications)));
                        
                        // Clear any existing errors
                        setValidationErrors({});
                        setCriticalError(null);
                        setNetworkError(null);
                        
                        setShowSaveConfirmation(true);
                        announceToScreenReader('All settings data cleared and reset to defaults');
                        setTimeout(() => setShowSaveConfirmation(false), 3000);
                        
                    } catch (storageError) {
                        // If localStorage fails, still try to reset in-memory state
                        console.warn('localStorage clear failed, resetting in-memory state:', storageError);
                        
                        setSettings(JSON.parse(JSON.stringify(defaultSettings)));
                        setNotifications(JSON.parse(JSON.stringify(defaultNotifications)));
                        
                        throw new Error(`Partial clear completed: ${storageError instanceof Error ? storageError.message : 'Storage operation failed'}`);
                    }
                },
                'clear all settings data',
                'Clearing all data...'
            );
        }
    };

    // Enhanced data management operations
    const downloadUserData = () => {
        safeAsyncOperation(
            async () => {
                // Validate data before download
                if (!settings || typeof settings !== 'object') {
                    throw new Error('Settings data is invalid and cannot be downloaded');
                }
                
                if (!notifications || !Array.isArray(notifications)) {
                    throw new Error('Notifications data is invalid and cannot be downloaded');
                }
                
                const userData = {
                    settings,
                    notifications,
                    exportDate: new Date().toISOString(),
                    version: '1.0',
                    metadata: {
                        userAgent: navigator.userAgent,
                        timestamp: Date.now(),
                        settingsCount: Object.keys(settings).length,
                        notificationsCount: notifications.length,
                        validationErrors: Object.keys(validationErrors).length > 0 ? validationErrors : null
                    }
                };

                const jsonString = JSON.stringify(userData, null, 2);
                if (!jsonString || jsonString === '{}') {
                    throw new Error('Failed to serialize user data');
                }

                const blob = new Blob([jsonString], { type: 'application/json' });
                if (blob.size === 0) {
                    throw new Error('Generated file is empty');
                }

                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ai-scholar-user-data-${new Date().toISOString().split('T')[0]}.json`;
                
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                setTimeout(() => URL.revokeObjectURL(url), 100);
                
                announceToScreenReader('User data downloaded successfully');
            },
            'download user data',
            'Preparing data download...'
        );
    };

    const deleteUserData = () => {
        if (window.confirm('Are you sure you want to permanently delete all your user data? This action cannot be undone.')) {
            safeAsyncOperation(
                async () => {
                    try {
                        // Clear all localStorage data
                        const keysToRemove = Object.keys(localStorage).filter(key => 
                            key.startsWith('ai-scholar-')
                        );
                        
                        keysToRemove.forEach(key => {
                            try {
                                localStorage.removeItem(key);
                            } catch (keyError) {
                                console.warn(`Failed to remove key ${key}:`, keyError);
                            }
                        });
                        
                        // Reset to minimal defaults
                        const minimalSettings = {
                            theme: 'dark',
                            language: 'en',
                            autoSave: true
                        };
                        
                        const minimalNotifications = defaultNotifications.map(notif => ({
                            ...notif,
                            email: false,
                            push: false,
                            sms: false
                        }));
                        
                        setSettings(minimalSettings);
                        setNotifications(minimalNotifications);
                        
                        // Clear all error states
                        setValidationErrors({});
                        setCriticalError(null);
                        setNetworkError(null);
                        setSaveError(null);
                        
                        announceToScreenReader('All user data has been permanently deleted');
                        
                    } catch (error) {
                        throw new Error(`Failed to delete user data: ${error instanceof Error ? error.message : 'Unknown error'}`);
                    }
                },
                'delete user data',
                'Deleting user data...'
            );
        }
    };

    const renderGeneralSettings = () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
                <h3 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>
                    General Preferences
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Theme
                        </label>
                        <select
                            value={settings.theme}
                            onChange={(e) => updateSetting('theme', e.target.value)}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '8px',
                                color: 'white',
                                fontSize: '14px',
                                outline: 'none'
                            }}
                        >
                            <option value="dark" style={{ background: '#1a1a2e' }}>Dark</option>
                            <option value="light" style={{ background: '#1a1a2e' }}>Light</option>
                            <option value="auto" style={{ background: '#1a1a2e' }}>Auto</option>
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Language
                        </label>
                        <select
                            value={settings.language}
                            onChange={(e) => updateSetting('language', e.target.value)}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '8px',
                                color: 'white',
                                fontSize: '14px',
                                outline: 'none'
                            }}
                        >
                            <option value="en" style={{ background: '#1a1a2e' }}>English</option>
                            <option value="es" style={{ background: '#1a1a2e' }}>Español</option>
                            <option value="fr" style={{ background: '#1a1a2e' }}>Français</option>
                            <option value="de" style={{ background: '#1a1a2e' }}>Deutsch</option>
                            <option value="zh" style={{ background: '#1a1a2e' }}>中文</option>
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Timezone
                        </label>
                        <select
                            value={settings.timezone}
                            onChange={(e) => updateSetting('timezone', e.target.value)}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '8px',
                                color: 'white',
                                fontSize: '14px',
                                outline: 'none'
                            }}
                        >
                            <option value="UTC" style={{ background: '#1a1a2e' }}>UTC</option>
                            <option value="America/New_York" style={{ background: '#1a1a2e' }}>Eastern Time</option>
                            <option value="America/Los_Angeles" style={{ background: '#1a1a2e' }}>Pacific Time</option>
                            <option value="Europe/London" style={{ background: '#1a1a2e' }}>London</option>
                            <option value="Asia/Tokyo" style={{ background: '#1a1a2e' }}>Tokyo</option>
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Date Format
                        </label>
                        <select
                            value={settings.dateFormat}
                            onChange={(e) => updateSetting('dateFormat', e.target.value)}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '8px',
                                color: 'white',
                                fontSize: '14px',
                                outline: 'none'
                            }}
                        >
                            <option value="MM/DD/YYYY" style={{ background: '#1a1a2e' }}>MM/DD/YYYY</option>
                            <option value="DD/MM/YYYY" style={{ background: '#1a1a2e' }}>DD/MM/YYYY</option>
                            <option value="YYYY-MM-DD" style={{ background: '#1a1a2e' }}>YYYY-MM-DD</option>
                        </select>
                    </div>
                </div>

                <div style={{ marginTop: '20px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', marginBottom: '12px' }}>
                        <input
                            type="checkbox"
                            checked={settings.autoSave}
                            onChange={(e) => updateSetting('autoSave', e.target.checked)}
                            style={{ marginRight: '12px' }}
                        />
                        <div>
                            <span style={{ color: 'white', fontSize: '14px' }}>
                                Auto-save settings changes
                            </span>
                            <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                Automatically save changes as you make them
                            </div>
                        </div>
                    </label>
                    
                    <div style={{
                        background: 'rgba(255,255,255,0.05)',
                        borderRadius: '8px',
                        padding: '12px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                    }}>
                        <div>
                            <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                Settings Persistence
                            </span>
                            <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                {(() => {
                                    try {
                                        localStorage.setItem('test', 'test');
                                        localStorage.removeItem('test');
                                        return 'Local storage is available and working';
                                    } catch {
                                        return 'Local storage is not available';
                                    }
                                })()}
                            </div>
                        </div>
                        <div style={{
                            width: '12px',
                            height: '12px',
                            borderRadius: '50%',
                            background: (() => {
                                try {
                                    localStorage.setItem('test', 'test');
                                    localStorage.removeItem('test');
                                    return 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
                                } catch {
                                    return 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
                                }
                            })()
                        }} />
                    </div>
                </div>
            </div>
        </div>
    );

    const renderDisplaySettings = () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
                <h3 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>
                    Display & Layout
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={settings.sidebarCollapsed}
                            onChange={(e) => updateSetting('sidebarCollapsed', e.target.checked)}
                            style={{ marginRight: '12px' }}
                        />
                        <div>
                            <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                Collapse sidebar by default
                            </span>
                            <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                Start with the sidebar collapsed to save space
                            </div>
                        </div>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={settings.compactMode}
                            onChange={(e) => updateSetting('compactMode', e.target.checked)}
                            style={{ marginRight: '12px' }}
                        />
                        <div>
                            <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                Compact mode
                            </span>
                            <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                Reduce spacing and padding for more content
                            </div>
                        </div>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={settings.animations}
                            onChange={(e) => updateSetting('animations', e.target.checked)}
                            style={{ marginRight: '12px' }}
                        />
                        <div>
                            <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                Enable animations
                            </span>
                            <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                Smooth transitions and hover effects
                            </div>
                        </div>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={settings.highContrast}
                            onChange={(e) => updateSetting('highContrast', e.target.checked)}
                            style={{ marginRight: '12px' }}
                        />
                        <div>
                            <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                High contrast mode
                            </span>
                            <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                Improve visibility with higher contrast colors
                            </div>
                        </div>
                    </label>
                </div>
            </div>
        </div>
    );

    const renderAISettings = () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
                <h3 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>
                    AI Model Configuration
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Default Model
                        </label>
                        <select
                            value={settings.defaultModel}
                            onChange={(e) => updateSetting('defaultModel', e.target.value)}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '8px',
                                color: 'white',
                                fontSize: '14px',
                                outline: 'none'
                            }}
                        >
                            <option value="llama3.1:8b" style={{ background: '#1a1a2e' }}>Llama 3.1 8B</option>
                            <option value="llama3.1:70b" style={{ background: '#1a1a2e' }}>Llama 3.1 70B</option>
                            <option value="qwen2:72b" style={{ background: '#1a1a2e' }}>Qwen2 72B</option>
                            <option value="codellama:34b" style={{ background: '#1a1a2e' }}>CodeLlama 34B</option>
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Default Dataset
                        </label>
                        <select
                            value={settings.defaultDataset}
                            onChange={(e) => updateSetting('defaultDataset', e.target.value)}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '8px',
                                color: 'white',
                                fontSize: '14px',
                                outline: 'none'
                            }}
                        >
                            <option value="ai_scholar" style={{ background: '#1a1a2e' }}>AI Scholar</option>
                            <option value="quant_finance" style={{ background: '#1a1a2e' }}>Quant Scholar</option>
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Response Length
                        </label>
                        <select
                            value={settings.responseLength}
                            onChange={(e) => updateSetting('responseLength', e.target.value)}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '8px',
                                color: 'white',
                                fontSize: '14px',
                                outline: 'none'
                            }}
                        >
                            <option value="short" style={{ background: '#1a1a2e' }}>Short</option>
                            <option value="medium" style={{ background: '#1a1a2e' }}>Medium</option>
                            <option value="long" style={{ background: '#1a1a2e' }}>Long</option>
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Temperature: {settings.temperature}
                        </label>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={settings.temperature}
                            onChange={(e) => updateSetting('temperature', parseFloat(e.target.value))}
                            style={{
                                width: '100%',
                                height: '6px',
                                borderRadius: '3px',
                                background: 'rgba(255,255,255,0.2)',
                                outline: 'none'
                            }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                            <span>Conservative</span>
                            <span>Creative</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderPerformanceSettings = () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
                <h3 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>
                    Performance & Resources
                </h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Cache Size
                        </label>
                        <select
                            value={settings.cacheSize}
                            onChange={(e) => updateSetting('cacheSize', e.target.value)}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '8px',
                                color: 'white',
                                fontSize: '14px',
                                outline: 'none'
                            }}
                        >
                            <option value="256MB" style={{ background: '#1a1a2e' }}>256 MB</option>
                            <option value="512MB" style={{ background: '#1a1a2e' }}>512 MB</option>
                            <option value="1GB" style={{ background: '#1a1a2e' }}>1 GB</option>
                            <option value="2GB" style={{ background: '#1a1a2e' }}>2 GB</option>
                            <option value="4GB" style={{ background: '#1a1a2e' }}>4 GB</option>
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Max Concurrent Requests
                        </label>
                        <select
                            value={settings.maxConcurrentRequests}
                            onChange={(e) => updateSetting('maxConcurrentRequests', parseInt(e.target.value))}
                            style={{
                                width: '100%',
                                padding: '12px',
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '8px',
                                color: 'white',
                                fontSize: '14px',
                                outline: 'none'
                            }}
                        >
                            <option value="1" style={{ background: '#1a1a2e' }}>1</option>
                            <option value="3" style={{ background: '#1a1a2e' }}>3</option>
                            <option value="5" style={{ background: '#1a1a2e' }}>5</option>
                            <option value="10" style={{ background: '#1a1a2e' }}>10</option>
                            <option value="20" style={{ background: '#1a1a2e' }}>20</option>
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                            Request Timeout (seconds): {settings.requestTimeout}
                        </label>
                        <input
                            type="range"
                            min="5"
                            max="300"
                            step="5"
                            value={settings.requestTimeout}
                            onChange={(e) => updateSetting('requestTimeout', parseInt(e.target.value))}
                            style={{
                                width: '100%',
                                height: '6px',
                                borderRadius: '3px',
                                background: 'rgba(255,255,255,0.2)',
                                outline: 'none'
                            }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                            <span>5s</span>
                            <span>300s</span>
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center' }}>
                        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                checked={settings.enableGPU}
                                onChange={(e) => updateSetting('enableGPU', e.target.checked)}
                                style={{ marginRight: '12px' }}
                            />
                            <div>
                                <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                    Enable GPU Acceleration
                                </span>
                                <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                    Use GPU for faster AI model inference
                                </div>
                            </div>
                        </label>
                    </div>
                </div>

                {/* GPU Information Display */}
                {settings.enableGPU && (
                    <div style={{ marginTop: '24px' }}>
                        <h4 style={{ color: 'white', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '500' }}>
                            GPU Information
                        </h4>
                        <div style={{
                            background: 'rgba(255,255,255,0.05)',
                            borderRadius: '8px',
                            padding: '16px'
                        }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                                <div>
                                    <span style={{ color: '#9ca3af', fontSize: '14px' }}>GPU Model</span>
                                    <div style={{ color: 'white', fontSize: '14px', fontWeight: '500', marginTop: '4px' }}>
                                        NVIDIA RTX 4090
                                    </div>
                                </div>
                                <div>
                                    <span style={{ color: '#9ca3af', fontSize: '14px' }}>Driver Version</span>
                                    <div style={{ color: 'white', fontSize: '14px', fontWeight: '500', marginTop: '4px' }}>
                                        545.29.06
                                    </div>
                                </div>
                                <div>
                                    <span style={{ color: '#9ca3af', fontSize: '14px' }}>CUDA Version</span>
                                    <div style={{ color: 'white', fontSize: '14px', fontWeight: '500', marginTop: '4px' }}>
                                        12.3
                                    </div>
                                </div>
                                <div>
                                    <span style={{ color: '#9ca3af', fontSize: '14px' }}>Compute Capability</span>
                                    <div style={{ color: 'white', fontSize: '14px', fontWeight: '500', marginTop: '4px' }}>
                                        8.9
                                    </div>
                                </div>
                            </div>
                            
                            <div style={{ marginTop: '16px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                    <span style={{ color: '#9ca3af', fontSize: '14px' }}>VRAM Usage</span>
                                    <span style={{ color: 'white', fontSize: '14px' }}>18.2 GB / 24.0 GB</span>
                                </div>
                                <div style={{
                                    width: '100%',
                                    height: '8px',
                                    background: 'rgba(255,255,255,0.2)',
                                    borderRadius: '4px',
                                    overflow: 'hidden'
                                }}>
                                    <div style={{
                                        width: '76%',
                                        height: '100%',
                                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                        transition: 'width 0.3s ease'
                                    }} />
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                                    <span>Available: 5.8 GB</span>
                                    <span>Temperature: 72°C</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* System Resources */}
                <div style={{ marginTop: '24px' }}>
                    <h4 style={{ color: 'white', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '500' }}>
                        System Resources
                    </h4>
                    <div style={{
                        background: 'rgba(255,255,255,0.05)',
                        borderRadius: '8px',
                        padding: '16px'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                            <span style={{ color: '#9ca3af', fontSize: '14px' }}>Cache Usage</span>
                            <span style={{ color: 'white', fontSize: '14px' }}>
                                {settings.cacheSize === '256MB' ? '192 MB' : 
                                 settings.cacheSize === '512MB' ? '384 MB' :
                                 settings.cacheSize === '1GB' ? '756 MB' :
                                 settings.cacheSize === '2GB' ? '1.5 GB' : '3.2 GB'} / {settings.cacheSize}
                            </span>
                        </div>
                        <div style={{
                            width: '100%',
                            height: '6px',
                            background: 'rgba(255,255,255,0.2)',
                            borderRadius: '3px',
                            overflow: 'hidden'
                        }}>
                            <div style={{
                                width: '75%',
                                height: '100%',
                                background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
                                transition: 'width 0.3s ease'
                            }} />
                        </div>
                        
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px', marginBottom: '8px' }}>
                            <span style={{ color: '#9ca3af', fontSize: '14px' }}>Active Requests</span>
                            <span style={{ color: 'white', fontSize: '14px' }}>
                                {Math.min(3, settings.maxConcurrentRequests)} / {settings.maxConcurrentRequests}
                            </span>
                        </div>
                        <div style={{
                            width: '100%',
                            height: '6px',
                            background: 'rgba(255,255,255,0.2)',
                            borderRadius: '3px',
                            overflow: 'hidden'
                        }}>
                            <div style={{
                                width: `${(Math.min(3, settings.maxConcurrentRequests) / settings.maxConcurrentRequests) * 100}%`,
                                height: '100%',
                                background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                                transition: 'width 0.3s ease'
                            }} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

  const renderPrivacySettings = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h3 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>
          Privacy & Data Control
        </h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <h4 style={{ color: 'white', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '500' }}>
              Data Collection
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={settings.dataCollection}
                  onChange={(e) => updateSetting('dataCollection', e.target.checked)}
                  style={{ marginRight: '12px' }}
                />
                <div>
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    Allow usage data collection
                  </span>
                  <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                    Help improve AI Scholar by sharing anonymous usage statistics
                  </div>
                </div>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={settings.analytics}
                  onChange={(e) => updateSetting('analytics', e.target.checked)}
                  style={{ marginRight: '12px' }}
                />
                <div>
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    Enable analytics tracking
                  </span>
                  <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                    Track feature usage and performance metrics
                  </div>
                </div>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={settings.crashReports}
                  onChange={(e) => updateSetting('crashReports', e.target.checked)}
                  style={{ marginRight: '12px' }}
                />
                <div>
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    Send crash reports
                  </span>
                  <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                    Automatically send error reports to help fix bugs
                  </div>
                </div>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={settings.personalizedAds}
                  onChange={(e) => updateSetting('personalizedAds', e.target.checked)}
                  style={{ marginRight: '12px' }}
                />
                <div>
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    Personalized advertisements
                  </span>
                  <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                    Show relevant ads based on your usage patterns
                  </div>
                </div>
              </label>
            </div>
          </div>

          <div>
            <h4 style={{ color: 'white', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '500' }}>
              Data Management
            </h4>
            <div style={{
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    Clear Chat History
                  </span>
                  <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                    Delete all stored chat conversations
                  </div>
                </div>
                <button style={{
                  padding: '8px 16px',
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '6px',
                  color: '#ef4444',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}>
                  Clear History
                </button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    Download My Data
                  </span>
                  <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                    Download all your data in JSON format
                  </div>
                </div>
                <button 
                  onClick={() => {
                    // Simulate data download
                    const userData = {
                      profile: { name: 'User', email: 'user@example.com' },
                      settings: settings,
                      exportDate: new Date().toISOString()
                    };
                    const blob = new Blob([JSON.stringify(userData, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'my-data-export.json';
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                  style={{
                    padding: '8px 16px',
                    background: 'rgba(96, 165, 250, 0.2)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                    borderRadius: '6px',
                    color: '#60a5fa',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Download Data
                </button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    Data Portability
                  </span>
                  <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                    Transfer your data to another service
                  </div>
                </div>
                <button 
                  onClick={() => {
                    alert('Data portability request initiated. You will receive an email with instructions within 24 hours.');
                  }}
                  style={{
                    padding: '8px 16px',
                    background: 'rgba(168, 85, 247, 0.2)',
                    border: '1px solid rgba(168, 85, 247, 0.3)',
                    borderRadius: '6px',
                    color: '#a855f7',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Request Transfer
                </button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    Clear Local Storage
                  </span>
                  <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                    Clear all locally stored settings and data
                  </div>
                </div>
                <button 
                  onClick={clearAllData}
                  style={{
                    padding: '8px 16px',
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '6px',
                    color: '#ef4444',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Clear Storage
                </button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                    Storage Status
                  </span>
                  <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                    Local storage usage for settings and preferences
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: 'white', fontSize: '12px', fontWeight: '500' }}>
                    {(() => {
                      try {
                        const settingsSize = localStorage.getItem(SETTINGS_STORAGE_KEY)?.length || 0;
                        const notificationsSize = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY)?.length || 0;
                        const totalSize = settingsSize + notificationsSize;
                        return `${(totalSize / 1024).toFixed(1)} KB`;
                      } catch {
                        return 'Unknown';
                      }
                    })()}
                  </div>
                  <div style={{ color: '#9ca3af', fontSize: '10px' }}>
                    Settings data
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

    const renderAccountSettings = () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
                <h3 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>
                    Account Information
                </h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <div>
                        <h4 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '16px', fontWeight: '500' }}>
                            Profile Details
                        </h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                                    Full Name
                                </label>
                                <input
                                    type="text"
                                    value={settings.fullName}
                                    onChange={(e) => updateSetting('fullName', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        background: 'rgba(255,255,255,0.1)',
                                        border: validationErrors.fullName 
                                            ? '2px solid #ef4444' 
                                            : '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '8px',
                                        color: 'white',
                                        fontSize: '14px',
                                        outline: 'none'
                                    }}
                                    aria-invalid={validationErrors.fullName ? 'true' : 'false'}
                                    aria-describedby={validationErrors.fullName ? 'fullName-error' : undefined}
                                />
                                {validationErrors.fullName && (
                                    <div 
                                        id="fullName-error"
                                        style={{
                                            color: '#ef4444',
                                            fontSize: '12px',
                                            marginTop: '4px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px'
                                        }}
                                        role="alert"
                                    >
                                        ⚠️ {validationErrors.fullName}
                                    </div>
                                )}
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                                    Email Address
                                </label>
                                <input
                                    type="email"
                                    value={settings.email}
                                    onChange={(e) => updateSetting('email', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        background: 'rgba(255,255,255,0.1)',
                                        border: validationErrors.email 
                                            ? '2px solid #ef4444' 
                                            : '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '8px',
                                        color: 'white',
                                        fontSize: '14px',
                                        outline: 'none'
                                    }}
                                    aria-invalid={validationErrors.email ? 'true' : 'false'}
                                    aria-describedby={validationErrors.email ? 'email-error' : undefined}
                                />
                                {validationErrors.email && (
                                    <div 
                                        id="email-error"
                                        style={{
                                            color: '#ef4444',
                                            fontSize: '12px',
                                            marginTop: '4px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px'
                                        }}
                                        role="alert"
                                    >
                                        ⚠️ {validationErrors.email}
                                    </div>
                                )}
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                                    Organization
                                </label>
                                <input
                                    type="text"
                                    value={settings.organization}
                                    onChange={(e) => updateSetting('organization', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        background: 'rgba(255,255,255,0.1)',
                                        border: '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '8px',
                                        color: 'white',
                                        fontSize: '14px',
                                        outline: 'none'
                                    }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                                    Role
                                </label>
                                <select
                                    value={settings.role}
                                    onChange={(e) => updateSetting('role', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        background: 'rgba(255,255,255,0.1)',
                                        border: '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '8px',
                                        color: 'white',
                                        fontSize: '14px',
                                        outline: 'none'
                                    }}
                                >
                                    <option value="Administrator" style={{ background: '#1a1a2e' }}>Administrator</option>
                                    <option value="Researcher" style={{ background: '#1a1a2e' }}>Researcher</option>
                                    <option value="Analyst" style={{ background: '#1a1a2e' }}>Analyst</option>
                                    <option value="User" style={{ background: '#1a1a2e' }}>User</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div>
                        <h4 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '16px', fontWeight: '500' }}>
                            Security Settings
                        </h4>
                        <div style={{
                            background: 'rgba(255,255,255,0.05)',
                            borderRadius: '8px',
                            padding: '16px'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                <div>
                                    <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                        Change Password
                                    </span>
                                    <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                        Last changed 30 days ago
                                    </div>
                                </div>
                                <button 
                                    onClick={() => {
                                        alert('Password change dialog would open here');
                                    }}
                                    style={{
                                        padding: '8px 16px',
                                        background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
                                        border: 'none',
                                        borderRadius: '6px',
                                        color: 'white',
                                        cursor: 'pointer',
                                        fontSize: '12px',
                                        fontWeight: '500'
                                    }}
                                >
                                    Change Password
                                </button>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                <div>
                                    <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                        Two-Factor Authentication
                                    </span>
                                    <div style={{ color: '#10b981', fontSize: '12px', marginTop: '2px' }}>
                                        Enabled via Authenticator App
                                    </div>
                                </div>
                                <button 
                                    onClick={() => {
                                        alert('2FA management dialog would open here');
                                    }}
                                    style={{
                                        padding: '8px 16px',
                                        background: 'rgba(255,255,255,0.1)',
                                        border: '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '6px',
                                        color: 'white',
                                        cursor: 'pointer',
                                        fontSize: '12px'
                                    }}
                                >
                                    Manage 2FA
                                </button>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                        API Keys
                                    </span>
                                    <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                        Manage your API access keys
                                    </div>
                                </div>
                                <button 
                                    onClick={() => {
                                        alert('API key management dialog would open here');
                                    }}
                                    style={{
                                        padding: '8px 16px',
                                        background: 'rgba(255,255,255,0.1)',
                                        border: '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '6px',
                                        color: 'white',
                                        cursor: 'pointer',
                                        fontSize: '12px'
                                    }}
                                >
                                    Manage Keys
                                </button>
                            </div>
                        </div>
                    </div>

                    <div>
                        <h4 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '16px', fontWeight: '500' }}>
                            Account Actions
                        </h4>
                        <div style={{
                            background: 'rgba(255,255,255,0.05)',
                            borderRadius: '8px',
                            padding: '16px'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                <div>
                                    <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                        Deactivate Account
                                    </span>
                                    <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                        Temporarily disable your account (can be reactivated)
                                    </div>
                                </div>
                                <button 
                                    onClick={() => {
                                        if (window.confirm('Are you sure you want to deactivate your account? You can reactivate it later by logging in.')) {
                                            alert('Account deactivation request submitted. Your account will be deactivated within 24 hours.');
                                        }
                                    }}
                                    style={{
                                        padding: '8px 16px',
                                        background: 'rgba(251, 191, 36, 0.2)',
                                        border: '1px solid rgba(251, 191, 36, 0.3)',
                                        borderRadius: '6px',
                                        color: '#fbbf24',
                                        cursor: 'pointer',
                                        fontSize: '12px',
                                        fontWeight: '500'
                                    }}
                                >
                                    Deactivate
                                </button>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <span style={{ color: 'white', fontSize: '14px', fontWeight: '500' }}>
                                        Delete Account
                                    </span>
                                    <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>
                                        Permanently delete your account and all associated data
                                    </div>
                                </div>
                                <button 
                                    onClick={() => {
                                        if (window.confirm('Are you sure you want to permanently delete your account? This action cannot be undone and all your data will be lost.')) {
                                            if (window.confirm('This is your final warning. Deleting your account will permanently remove all your data, workflows, and settings. Are you absolutely sure?')) {
                                                alert('Account deletion request submitted. Your account and all data will be permanently deleted within 30 days.');
                                            }
                                        }
                                    }}
                                    style={{
                                        padding: '8px 16px',
                                        background: 'rgba(239, 68, 68, 0.2)',
                                        border: '1px solid rgba(239, 68, 68, 0.3)',
                                        borderRadius: '6px',
                                        color: '#ef4444',
                                        cursor: 'pointer',
                                        fontSize: '12px',
                                        fontWeight: '500'
                                    }}
                                >
                                    Delete Account
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

  const renderNotificationSettings = () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
                <h3 style={{ color: 'white', margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>
                    Notification Preferences
                </h3>

                <div style={{
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '12px',
                    overflow: 'hidden'
                }}>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: '2fr 1fr 1fr 1fr',
                        padding: '12px 20px',
                        background: 'rgba(255,255,255,0.1)',
                        fontSize: '12px',
                        color: '#9ca3af',
                        fontWeight: '500'
                    }}>
                        <div>Notification Type</div>
                        <div style={{ textAlign: 'center' }}>Email</div>
                        <div style={{ textAlign: 'center' }}>Push</div>
                        <div style={{ textAlign: 'center' }}>SMS</div>
                    </div>

                    {notifications.map((notification, index) => (
                        <div
                            key={notification.id}
                            style={{
                                display: 'grid',
                                gridTemplateColumns: '2fr 1fr 1fr 1fr',
                                padding: '16px 20px',
                                borderBottom: index < notifications.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none',
                                alignItems: 'center'
                            }}
                        >
                            <div>
                                <div style={{ color: 'white', fontSize: '14px', fontWeight: '500', marginBottom: '2px' }}>
                                    {notification.name}
                                </div>
                                <div style={{ color: '#9ca3af', fontSize: '12px' }}>
                                    {notification.description}
                                </div>
                            </div>

                            <div style={{ textAlign: 'center' }}>
                                <input
                                    type="checkbox"
                                    checked={notification.email}
                                    onChange={(e) => updateNotification(notification.id, 'email', e.target.checked)}
                                />
                            </div>

                            <div style={{ textAlign: 'center' }}>
                                <input
                                    type="checkbox"
                                    checked={notification.push}
                                    onChange={(e) => updateNotification(notification.id, 'push', e.target.checked)}
                                />
                            </div>

                            <div style={{ textAlign: 'center' }}>
                                <input
                                    type="checkbox"
                                    checked={notification.sms}
                                    onChange={(e) => updateNotification(notification.id, 'sms', e.target.checked)}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

    const renderSection = () => {
        switch (activeSection) {
            case 'general': return renderGeneralSettings();
            case 'display': return renderDisplaySettings();
            case 'ai': return renderAISettings();
            case 'notifications': return renderNotificationSettings();
            case 'privacy': return renderPrivacySettings();
            case 'performance': return renderPerformanceSettings();
            case 'account': return renderAccountSettings();
            default:
                return (
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '300px',
                        color: '#9ca3af'
                    }}>
                        <Settings size={48} style={{ marginBottom: '16px' }} />
                        <h3 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>
                            {sections.find(s => s.id === activeSection)?.name} Settings
                        </h3>
                        <p style={{ margin: 0, textAlign: 'center' }}>
                            {sections.find(s => s.id === activeSection)?.description}
                        </p>
                        <p style={{ margin: '16px 0 0 0', fontSize: '14px' }}>
                            Coming soon...
                        </p>
                    </div>
                );
        }
    };

    return (
        <div 
            style={{
                padding: '24px',
                height: '100%',
                overflow: 'auto'
            }}
            role="main"
            aria-label="Settings page"
        >
            {/* Screen Reader Announcements */}
            <div 
                aria-live="polite" 
                aria-atomic="true" 
                style={{ 
                    position: 'absolute', 
                    left: '-10000px', 
                    width: '1px', 
                    height: '1px', 
                    overflow: 'hidden' 
                }}
            >
                {announcements.map((announcement, index) => (
                    <div key={index}>{announcement}</div>
                ))}
            </div>

            {/* Critical Error Display */}
            {criticalError && (
                <div style={{
                    background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
                    border: '1px solid #ef4444',
                    borderRadius: '12px',
                    padding: '16px',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    animation: 'fadeIn 0.3s ease-in-out'
                }} role="alert" aria-live="assertive">
                    <div style={{
                        width: '24px',
                        height: '24px',
                        background: 'rgba(255,255,255,0.2)',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                    }}>
                        ⚠️
                    </div>
                    <div style={{ flex: 1 }}>
                        <div style={{ color: 'white', fontWeight: '600', marginBottom: '4px' }}>
                            Critical Error
                        </div>
                        <div style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>
                            {criticalError}
                        </div>
                    </div>
                    <button
                        onClick={() => setCriticalError(null)}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: 'rgba(255,255,255,0.8)',
                            cursor: 'pointer',
                            padding: '4px',
                            borderRadius: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                        aria-label="Dismiss critical error"
                    >
                        ✕
                    </button>
                </div>
            )}

            {/* Network Error Display */}
            {networkError && (
                <div style={{
                    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    border: '1px solid #fbbf24',
                    borderRadius: '12px',
                    padding: '16px',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    animation: 'fadeIn 0.3s ease-in-out'
                }} role="alert" aria-live="polite">
                    <div style={{
                        width: '24px',
                        height: '24px',
                        background: 'rgba(255,255,255,0.2)',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                    }}>
                        🌐
                    </div>
                    <div style={{ flex: 1 }}>
                        <div style={{ color: 'white', fontWeight: '600', marginBottom: '4px' }}>
                            Network Issue
                        </div>
                        <div style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>
                            {networkError}
                        </div>
                    </div>
                    <button
                        onClick={() => setNetworkError(null)}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: 'rgba(255,255,255,0.8)',
                            cursor: 'pointer',
                            padding: '4px',
                            borderRadius: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                        aria-label="Dismiss network error"
                    >
                        ✕
                    </button>
                </div>
            )}

            {/* Loading State Display */}
            {isLoading && operationInProgress && (
                <div style={{
                    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                    border: '1px solid #60a5fa',
                    borderRadius: '12px',
                    padding: '16px',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    animation: 'fadeIn 0.3s ease-in-out'
                }} role="status" aria-live="polite">
                    <div style={{
                        width: '24px',
                        height: '24px',
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTop: '2px solid white',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                        flexShrink: 0
                    }}></div>
                    <div style={{ flex: 1 }}>
                        <div style={{ color: 'white', fontWeight: '600', marginBottom: '4px' }}>
                            Processing...
                        </div>
                        <div style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>
                            {operationInProgress}
                            {retryCount > 0 && ` (Retry ${retryCount}/3)`}
                        </div>
                    </div>
                </div>
            )}

            {/* Header */}
            <header style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '24px'
            }}>
                <div>
                    <h1 style={{
                        color: 'white',
                        margin: 0,
                        fontSize: '24px',
                        fontWeight: '600'
                    }}>
                        Settings
                    </h1>
                    <p style={{
                        color: '#9ca3af',
                        margin: '4px 0 0 0',
                        fontSize: '14px'
                    }}>
                        Customize your AI Scholar experience
                    </p>
                </div>

                <div style={{ display: 'flex', gap: '12px' }} role="toolbar" aria-label="Settings actions">
                    <button
                        onClick={exportSettings}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '12px 16px',
                            background: 'rgba(255,255,255,0.1)',
                            border: '1px solid rgba(255,255,255,0.2)',
                            borderRadius: '8px',
                            color: 'white',
                            cursor: 'pointer',
                            fontSize: '14px'
                        }}
                        aria-label="Export settings to file"
                        title="Export your current settings to a JSON file"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                exportSettings();
                            }
                        }}
                    >
                        <Download size={16} aria-hidden="true" />
                        Export
                    </button>

                    <button
                        onClick={resetToDefaults}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '12px 16px',
                            background: 'rgba(251, 191, 36, 0.2)',
                            border: '1px solid rgba(251, 191, 36, 0.3)',
                            borderRadius: '8px',
                            color: '#fbbf24',
                            cursor: 'pointer',
                            fontSize: '14px'
                        }}
                        aria-label="Reset all settings to default values"
                        title="This will reset all settings to their default values"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                resetToDefaults();
                            }
                        }}
                    >
                        <RefreshCw size={16} aria-hidden="true" />
                        Reset to Defaults
                    </button>

                    <button
                        onClick={saveSettings}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '12px 16px',
                            background: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
                            border: 'none',
                            borderRadius: '8px',
                            color: 'white',
                            cursor: 'pointer',
                            fontSize: '14px',
                            fontWeight: '500'
                        }}
                        aria-label="Save all settings changes"
                        title="Save your current settings"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                saveSettings();
                            }
                        }}
                    >
                        <Save size={16} aria-hidden="true" />
                        Save Changes
                    </button>
                </div>
            </div>

            <div style={{
                display: 'grid',
                gridTemplateColumns: '280px 1fr',
                gap: '24px',
                height: 'calc(100% - 100px)'
            }}>
                {/* Settings Navigation */}
                <nav 
                    style={{
                        background: 'rgba(255,255,255,0.05)',
                        borderRadius: '12px',
                        padding: '16px',
                        height: 'fit-content'
                    }}
                    role="navigation"
                    aria-label="Settings navigation"
                >
                    <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                        {sections.map((section, index) => (
                            <li key={section.id} style={{ marginBottom: '4px' }}>
                                <button
                                    onClick={() => handleSectionChange(section.id)}
                                    onKeyDown={(e) => handleKeyDown(e, section.id)}
                                    style={{
                                        width: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '12px',
                                        padding: '12px 16px',
                                        background: activeSection === section.id ? 'rgba(96, 165, 250, 0.2)' : 'transparent',
                                        border: activeSection === section.id ? '2px solid rgba(96, 165, 250, 0.5)' : '2px solid transparent',
                                        borderRadius: '8px',
                                        color: activeSection === section.id ? 'white' : '#9ca3af',
                                        cursor: 'pointer',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        transition: 'all 0.2s ease',
                                        textAlign: 'left'
                                    }}
                                    aria-current={activeSection === section.id ? 'page' : undefined}
                                    aria-label={`${section.name} settings - ${section.description}`}
                                    title={`Navigate to ${section.name} settings`}
                                    tabIndex={activeSection === section.id ? 0 : -1}
                                    onMouseEnter={(e) => {
                                        if (activeSection !== section.id) {
                                            e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                                            e.currentTarget.style.color = 'white';
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (activeSection !== section.id) {
                                            e.currentTarget.style.background = 'transparent';
                                            e.currentTarget.style.color = '#9ca3af';
                                        }
                                    }}
                                    onFocus={(e) => {
                                        e.currentTarget.style.outline = '2px solid rgba(96, 165, 250, 0.8)';
                                        e.currentTarget.style.outlineOffset = '2px';
                                    }}
                                    onBlur={(e) => {
                                        e.currentTarget.style.outline = 'none';
                                    }}
                                >
                                    <span aria-hidden="true">{section.icon}</span>
                                    <div>
                                        <div>{section.name}</div>
                                        <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>
                                            {section.description}
                                        </div>
                                    </div>
                                </button>
                            </li>
                        ))}
                    </ul>
                    
                    {/* Keyboard navigation help */}
                    <div style={{
                        marginTop: '16px',
                        padding: '12px',
                        background: 'rgba(96, 165, 250, 0.1)',
                        borderRadius: '8px',
                        fontSize: '11px',
                        color: '#9ca3af'
                    }}>
                        <div style={{ fontWeight: '600', marginBottom: '4px', color: '#60a5fa' }}>
                            Keyboard Navigation:
                        </div>
                        <div>↑↓ Navigate sections</div>
                        <div>Enter/Space Select</div>
                        <div>Esc Clear focus</div>
                    </div>
                </div>

                {/* Settings Content */}
                <main 
                    style={{
                        background: 'rgba(255,255,255,0.05)',
                        borderRadius: '12px',
                        padding: '24px',
                        overflow: 'auto'
                    }}
                    role="region"
                    aria-label={`${activeSection} settings content`}
                    aria-live="polite"
                    tabIndex={-1}
                    id="settings-content"
                >
                    {renderSection()}
                </main>
            </div>

            {/* Save Confirmation */}
            {showSaveConfirmation && (
                <div 
                    style={{
                        position: 'fixed',
                        bottom: '20px',
                        right: '20px',
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        color: 'white',
                        padding: '12px 20px',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
                        zIndex: 1000
                    }}
                    role="status"
                    aria-live="polite"
                    aria-label="Settings saved successfully"
                >
                    <Check size={16} aria-hidden="true" />
                    Settings saved successfully!
                </div>
            )}

            {/* Loading State */}
            {isLoading && (
                <div 
                    style={{
                        position: 'fixed',
                        bottom: '20px',
                        right: '20px',
                        background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                        color: 'white',
                        padding: '12px 20px',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
                        zIndex: 1000
                    }}
                    role="status"
                    aria-live="polite"
                    aria-label={operationInProgress || 'Loading...'}
                >
                    <div style={{
                        width: '16px',
                        height: '16px',
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTop: '2px solid white',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }} aria-hidden="true" />
                    {operationInProgress || 'Loading...'}
                    {retryCount > 0 && (
                        <span style={{ fontSize: '12px', opacity: 0.8 }}>
                            (Retry {retryCount})
                        </span>
                    )}
                </div>
            )}

            {/* Save Error */}
            {saveError && (
                <div 
                    style={{
                        position: 'fixed',
                        bottom: '20px',
                        right: '20px',
                        background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                        color: 'white',
                        padding: '12px 20px',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
                        zIndex: 1000,
                        maxWidth: '400px'
                    }}
                    role="alert"
                    aria-live="assertive"
                    aria-label={`Error: ${saveError}`}
                >
                    <Shield size={16} aria-hidden="true" />
                    <div style={{ flex: 1 }}>
                        {saveError}
                        {retryCount > 0 && (
                            <div style={{ fontSize: '12px', marginTop: '4px', opacity: 0.8 }}>
                                Failed after {retryCount} attempts
                            </div>
                        )}
                    </div>
                    <button
                        onClick={() => {
                            setSaveError(null);
                            setRetryCount(0);
                            announceToScreenReader('Error dismissed');
                        }}
                        style={{
                            background: 'rgba(255,255,255,0.2)',
                            border: 'none',
                            borderRadius: '4px',
                            color: 'white',
                            padding: '4px 8px',
                            fontSize: '12px',
                            cursor: 'pointer'
                        }}
                        aria-label="Dismiss error message"
                        title="Dismiss this error"
                    >
                        ✕
                    </button>
                </div>
            )}
        </div>
    );
};

export default SettingsView;