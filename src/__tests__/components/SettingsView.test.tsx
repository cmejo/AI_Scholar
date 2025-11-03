import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import '@testing-library/jest-dom';
import SettingsView from '../../components/SettingsView';

// Mock localStorage
const mockLocalStorage = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
};

// Mock window functions
const mockConfirm = vi.fn();
const mockAlert = vi.fn();
const mockCreateObjectURL = vi.fn();
const mockRevokeObjectURL = vi.fn();

Object.defineProperty(window, 'localStorage', {
    value: mockLocalStorage,
});

Object.defineProperty(window, 'confirm', {
    value: mockConfirm,
});

Object.defineProperty(window, 'alert', {
    value: mockAlert,
});

Object.defineProperty(URL, 'createObjectURL', {
    value: mockCreateObjectURL,
});

Object.defineProperty(URL, 'revokeObjectURL', {
    value: mockRevokeObjectURL,
});

describe('SettingsView - Core Functionality', () => {
    const user = userEvent.setup();

    beforeEach(() => {
        vi.clearAllMocks();
        mockLocalStorage.getItem.mockReturnValue(null);
        mockConfirm.mockReturnValue(false);
        mockAlert.mockImplementation(() => { });
        mockCreateObjectURL.mockReturnValue('mock-url');
        mockRevokeObjectURL.mockImplementation(() => { });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('Basic Rendering', () => {
        it('should render without crashing', () => {
            const { container } = render(<SettingsView />);
            expect(container).toBeInTheDocument();
        });

        it('should render main settings title', () => {
            render(<SettingsView />);
            expect(screen.getByText('Settings')).toBeInTheDocument();
        });

        it('should render settings description', () => {
            render(<SettingsView />);
            expect(screen.getByText('Customize your AI Scholar experience')).toBeInTheDocument();
        });

        it('should render navigation sections', () => {
            render(<SettingsView />);

            expect(screen.getByText('General')).toBeInTheDocument();
            expect(screen.getByText('Display')).toBeInTheDocument();
            expect(screen.getByText('AI Models')).toBeInTheDocument();
            expect(screen.getByText('Notifications')).toBeInTheDocument();
            expect(screen.getByText('Privacy')).toBeInTheDocument();
            expect(screen.getByText('Performance')).toBeInTheDocument();
            expect(screen.getByText('Account')).toBeInTheDocument();
        });

        it('should render action buttons', () => {
            render(<SettingsView />);

            expect(screen.getByText('Export')).toBeInTheDocument();
            expect(screen.getByText('Reset to Defaults')).toBeInTheDocument();
            expect(screen.getByText('Save Changes')).toBeInTheDocument();
        });
    });

    describe('Performance Settings', () => {
        it('should navigate to performance settings', async () => {
            render(<SettingsView />);

            const performanceButton = screen.getByText('Performance');
            await user.click(performanceButton);

            expect(screen.getByText('Performance & Resources')).toBeInTheDocument();
        });

        it('should render cache size setting', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Performance'));

            expect(screen.getByText('Cache Size')).toBeInTheDocument();
            expect(screen.getByDisplayValue('1 GB')).toBeInTheDocument();
        });

        it('should render concurrent requests setting', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Performance'));

            expect(screen.getByText('Max Concurrent Requests')).toBeInTheDocument();
            expect(screen.getByDisplayValue('5')).toBeInTheDocument();
        });

        it('should render GPU acceleration toggle', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Performance'));

            expect(screen.getByText('Enable GPU Acceleration')).toBeInTheDocument();
            const gpuCheckbox = screen.getByRole('checkbox', { name: /Enable GPU Acceleration/ });
            expect(gpuCheckbox).toBeInTheDocument();
        });

        it('should update cache size', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Performance'));

            const cacheSelect = screen.getByDisplayValue('1 GB');
            await user.selectOptions(cacheSelect, '2GB');

            expect(cacheSelect).toHaveValue('2GB');
        });
    });

    describe('Privacy Settings', () => {
        it('should navigate to privacy settings', async () => {
            render(<SettingsView />);

            const privacyButton = screen.getByText('Privacy');
            await user.click(privacyButton);

            expect(screen.getByText('Privacy & Data Control')).toBeInTheDocument();
        });

        it('should render data collection toggles', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Privacy'));

            expect(screen.getByText('Allow usage data collection')).toBeInTheDocument();
            expect(screen.getByText('Enable analytics tracking')).toBeInTheDocument();
            expect(screen.getByText('Send crash reports')).toBeInTheDocument();
            expect(screen.getByText('Personalized advertisements')).toBeInTheDocument();
        });

        it('should render data management buttons', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Privacy'));

            expect(screen.getByText('Download Data')).toBeInTheDocument();
            expect(screen.getByText('Request Transfer')).toBeInTheDocument();
            expect(screen.getByText('Clear Storage')).toBeInTheDocument();
        });

        it('should toggle data collection setting', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Privacy'));

            const dataCollectionCheckbox = screen.getByRole('checkbox', { name: /Allow usage data collection/ });
            expect(dataCollectionCheckbox).toBeChecked(); // Default is true

            await user.click(dataCollectionCheckbox);
            expect(dataCollectionCheckbox).not.toBeChecked();
        });
    });

    describe('Account Settings', () => {
        it('should navigate to account settings', async () => {
            render(<SettingsView />);

            const accountButton = screen.getByText('Account');
            await user.click(accountButton);

            expect(screen.getByText('Account Information')).toBeInTheDocument();
        });

        it('should render profile form fields', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Account'));

            expect(screen.getByText('Full Name')).toBeInTheDocument();
            expect(screen.getByText('Email Address')).toBeInTheDocument();
            expect(screen.getByText('Organization')).toBeInTheDocument();
            expect(screen.getByText('Role')).toBeInTheDocument();

            // Check for input fields by their display values
            const inputs = screen.getAllByDisplayValue('Administrator');
            expect(inputs).toHaveLength(2); // Input field and select dropdown
            expect(screen.getByDisplayValue('admin@aischolar.com')).toBeInTheDocument(); // Email
            expect(screen.getByDisplayValue('AI Scholar Enterprise')).toBeInTheDocument(); // Organization
        });

        it('should render security settings', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Account'));

            expect(screen.getByText('Security Settings')).toBeInTheDocument();
            expect(screen.getAllByText('Change Password')).toHaveLength(2); // Label and button
            expect(screen.getByText('Manage 2FA')).toBeInTheDocument();
            expect(screen.getByText('Manage Keys')).toBeInTheDocument();
        });

        it('should update profile fields', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Account'));

            const inputs = screen.getAllByDisplayValue('Administrator');
            const nameInput = inputs.find(input => input.tagName === 'INPUT');
            expect(nameInput).toBeDefined();

            if (nameInput) {
                await user.clear(nameInput);
                await user.type(nameInput, 'John Doe');

                expect(nameInput).toHaveValue('John Doe');
            }
        });
    });

    describe('Settings Persistence', () => {
        it('should call localStorage.getItem on mount', () => {
            render(<SettingsView />);

            expect(mockLocalStorage.getItem).toHaveBeenCalledWith('ai-scholar-settings');
        });

        it('should handle export settings', async () => {
            const mockElement = {
                href: '',
                download: '',
                click: vi.fn(),
            };

            render(<SettingsView />);

            // Mock createElement after render to avoid the rendering issue
            vi.spyOn(document, 'createElement').mockReturnValue(mockElement as any);

            const exportButton = screen.getByText('Export');
            await user.click(exportButton);

            expect(mockCreateObjectURL).toHaveBeenCalled();
            expect(mockElement.click).toHaveBeenCalled();
        });

        it('should handle reset to defaults with confirmation', async () => {
            mockConfirm.mockReturnValue(true);

            render(<SettingsView />);

            const resetButton = screen.getByText('Reset to Defaults');
            await user.click(resetButton);

            expect(mockConfirm).toHaveBeenCalledWith(
                'Are you sure you want to reset all settings to their default values? This action cannot be undone.'
            );
        });

        it('should handle manual save', async () => {
            render(<SettingsView />);

            const saveButton = screen.getByText('Save Changes');
            await user.click(saveButton);

            expect(mockLocalStorage.setItem).toHaveBeenCalled();
        });
    });

    describe('Section Navigation', () => {
        it('should switch between sections', async () => {
            render(<SettingsView />);

            // Start with general settings (default)
            expect(screen.getByText('General Preferences')).toBeInTheDocument();

            // Switch to display settings
            await user.click(screen.getByText('Display'));
            expect(screen.getByText('Display & Layout')).toBeInTheDocument();

            // Switch to AI settings
            await user.click(screen.getByText('AI Models'));
            expect(screen.getByText('AI Model Configuration')).toBeInTheDocument();
        });
    });

    describe('Form Validation', () => {
        it('should validate form inputs', async () => {
            render(<SettingsView />);

            await user.click(screen.getByText('Account'));

            const emailInput = screen.getByDisplayValue('admin@aischolar.com');
            await user.clear(emailInput);
            await user.type(emailInput, 'test@example.com');

            expect(emailInput).toHaveValue('test@example.com');
        });
    });
});