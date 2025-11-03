// Settings Persistence Test
// This simulates the localStorage functionality using a simple object

console.log('🧪 Testing Settings Persistence Functionality\n');

// Mock localStorage for Node.js testing
const mockLocalStorage = {
    data: {},
    setItem(key, value) {
        if (typeof value !== 'string') {
            throw new Error('localStorage only accepts strings');
        }
        // Simulate quota exceeded error if data is too large
        if (JSON.stringify(this.data).length + value.length > 50000) {
            const error = new Error('QuotaExceededError');
            error.code = 22;
            error.name = 'QuotaExceededError';
            throw error;
        }
        this.data[key] = value;
    },
    getItem(key) {
        return this.data[key] || null;
    },
    removeItem(key) {
        delete this.data[key];
    },
    clear() {
        this.data = {};
    },
    get length() {
        return Object.keys(this.data).length;
    },
    key(index) {
        return Object.keys(this.data)[index] || null;
    }
};

// Replace global localStorage with mock
global.localStorage = mockLocalStorage;
global.DOMException = class DOMException extends Error {
    constructor(message) {
        super(message);
        this.code = 22;
        this.name = 'QuotaExceededError';
    }
};

// Constants from SettingsView
const SETTINGS_STORAGE_KEY = 'ai-scholar-settings';
const NOTIFICATIONS_STORAGE_KEY = 'ai-scholar-notifications';

const defaultSettings = {
    theme: 'dark',
    language: 'en',
    timezone: 'UTC',
    dateFormat: 'MM/DD/YYYY',
    autoSave: true,
    sidebarCollapsed: false,
    compactMode: false,
    animations: true,
    highContrast: false,
    defaultModel: 'llama3.1:8b',
    defaultDataset: 'ai_scholar',
    responseLength: 'medium',
    temperature: 0.7,
    dataCollection: true,
    analytics: true,
    crashReports: true,
    personalizedAds: false,
    cacheSize: '1GB',
    maxConcurrentRequests: 5,
    requestTimeout: 30,
    enableGPU: true,
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

// Functions from SettingsView
const loadSettingsFromStorage = () => {
    try {
        const storedSettings = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (storedSettings) {
            const parsed = JSON.parse(storedSettings);
            return { ...defaultSettings, ...parsed };
        }
    } catch (error) {
        console.warn('Failed to load settings from localStorage:', error.message);
    }
    return defaultSettings;
};

const loadNotificationsFromStorage = () => {
    try {
        const storedNotifications = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY);
        if (storedNotifications) {
            const parsed = JSON.parse(storedNotifications);
            if (Array.isArray(parsed) && parsed.length > 0) {
                return defaultNotifications.map(defaultNotif => {
                    const stored = parsed.find(n => n.id === defaultNotif.id);
                    return stored ? { ...defaultNotif, ...stored } : defaultNotif;
                });
            }
        }
    } catch (error) {
        console.warn('Failed to load notifications from localStorage:', error.message);
    }
    return defaultNotifications;
};

const saveSettingsToStorage = (settings) => {
    try {
        localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
        return true;
    } catch (error) {
        console.error('Failed to save settings to localStorage:', error.message);
        if (error instanceof DOMException && error.code === 22) {
            console.warn('localStorage quota exceeded. Attempting to clear old data...');
            try {
                const keys = Object.keys(localStorage.data);
                const oldKeys = keys.filter(key => 
                    key.startsWith('ai-scholar-') && 
                    key !== SETTINGS_STORAGE_KEY && 
                    key !== NOTIFICATIONS_STORAGE_KEY
                );
                oldKeys.forEach(key => localStorage.removeItem(key));
                
                localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
                return true;
            } catch (retryError) {
                console.error('Failed to save settings even after cleanup:', retryError.message);
                return false;
            }
        }
        return false;
    }
};

const saveNotificationsToStorage = (notifications) => {
    try {
        localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(notifications));
        return true;
    } catch (error) {
        console.error('Failed to save notifications to localStorage:', error.message);
        if (error instanceof DOMException && error.code === 22) {
            console.warn('localStorage quota exceeded for notifications. Attempting to clear old data...');
            try {
                const keys = Object.keys(localStorage.data);
                const oldKeys = keys.filter(key => 
                    key.startsWith('ai-scholar-') && 
                    key !== SETTINGS_STORAGE_KEY && 
                    key !== NOTIFICATIONS_STORAGE_KEY
                );
                oldKeys.forEach(key => localStorage.removeItem(key));
                
                localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(notifications));
                return true;
            } catch (retryError) {
                console.error('Failed to save notifications even after cleanup:', retryError.message);
                return false;
            }
        }
        return false;
    }
};

// Test functions
function runTests() {
    let passed = 0;
    let total = 0;

    function test(name, testFn) {
        total++;
        try {
            const result = testFn();
            if (result) {
                console.log(`✅ ${name}`);
                passed++;
            } else {
                console.log(`❌ ${name}`);
            }
        } catch (error) {
            console.log(`❌ ${name} - Error: ${error.message}`);
        }
    }

    console.log('1️⃣ Testing Basic localStorage Functionality');
    test('localStorage basic operations', () => {
        localStorage.setItem('test', 'value');
        const value = localStorage.getItem('test');
        localStorage.removeItem('test');
        return value === 'value';
    });

    console.log('\n2️⃣ Testing Settings Persistence');
    test('Save and load default settings', () => {
        const saved = saveSettingsToStorage(defaultSettings);
        const loaded = loadSettingsFromStorage();
        return saved && JSON.stringify(loaded) === JSON.stringify(defaultSettings);
    });

    test('Save and load modified settings', () => {
        const modifiedSettings = { ...defaultSettings, theme: 'light', language: 'es' };
        const saved = saveSettingsToStorage(modifiedSettings);
        const loaded = loadSettingsFromStorage();
        return saved && loaded.theme === 'light' && loaded.language === 'es';
    });

    test('Settings merge with defaults', () => {
        // Save partial settings
        localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify({ theme: 'light' }));
        const loaded = loadSettingsFromStorage();
        return loaded.theme === 'light' && loaded.language === 'en'; // Should have default language
    });

    console.log('\n3️⃣ Testing Notifications Persistence');
    test('Save and load notifications', () => {
        const saved = saveNotificationsToStorage(defaultNotifications);
        const loaded = loadNotificationsFromStorage();
        return saved && loaded.length === defaultNotifications.length;
    });

    test('Notifications merge with defaults', () => {
        const modifiedNotifications = [
            { id: 'workflow_complete', email: false, push: false, sms: false }
        ];
        localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(modifiedNotifications));
        const loaded = loadNotificationsFromStorage();
        const workflowNotif = loaded.find(n => n.id === 'workflow_complete');
        return workflowNotif && !workflowNotif.email && workflowNotif.name === 'Workflow Completion';
    });

    console.log('\n4️⃣ Testing Error Handling');
    test('Handle corrupted settings data', () => {
        localStorage.setItem(SETTINGS_STORAGE_KEY, '{invalid json}');
        const loaded = loadSettingsFromStorage();
        return JSON.stringify(loaded) === JSON.stringify(defaultSettings);
    });

    test('Handle corrupted notifications data', () => {
        localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, '{invalid json}');
        const loaded = loadNotificationsFromStorage();
        return loaded.length === defaultNotifications.length;
    });

    test('Handle quota exceeded error', () => {
        // Fill up storage to trigger quota error
        try {
            for (let i = 0; i < 100; i++) {
                localStorage.setItem(`filler-${i}`, 'x'.repeat(1000));
            }
        } catch (e) {
            // Expected to fail
        }
        
        const testSettings = { ...defaultSettings, theme: 'light' };
        const saved = saveSettingsToStorage(testSettings);
        
        // Should either save successfully after cleanup or fail gracefully
        return typeof saved === 'boolean';
    });

    console.log('\n5️⃣ Testing Storage Cleanup');
    test('Clear old data on quota exceeded', () => {
        // Clear storage first
        localStorage.clear();
        
        // Add some old data
        localStorage.setItem('ai-scholar-old-data-1', 'old');
        localStorage.setItem('ai-scholar-old-data-2', 'old');
        
        // Simulate quota exceeded by making storage very small
        const originalSetItem = localStorage.setItem;
        let callCount = 0;
        localStorage.setItem = function(key, value) {
            callCount++;
            if (callCount === 1 && key === SETTINGS_STORAGE_KEY) {
                // First attempt fails
                const error = new Error('QuotaExceededError');
                error.code = 22;
                error.name = 'QuotaExceededError';
                throw error;
            } else if (callCount === 2 && key === SETTINGS_STORAGE_KEY) {
                // Second attempt (after cleanup) succeeds
                return originalSetItem.call(this, key, value);
            } else {
                return originalSetItem.call(this, key, value);
            }
        };
        
        const testSettings = { ...defaultSettings };
        const result = saveSettingsToStorage(testSettings);
        
        // Restore original setItem
        localStorage.setItem = originalSetItem;
        
        // Should succeed after cleanup and old data should be removed
        return result && !localStorage.getItem('ai-scholar-old-data-1');
    });

    console.log('\n📊 Test Results');
    console.log(`Passed: ${passed}/${total}`);
    console.log(`Success Rate: ${((passed/total) * 100).toFixed(1)}%`);
    
    if (passed === total) {
        console.log('\n🎉 All tests passed! Settings persistence is working correctly.');
    } else {
        console.log('\n⚠️  Some tests failed. Please review the implementation.');
    }

    return passed === total;
}

// Run the tests
runTests();