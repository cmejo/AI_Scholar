import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Info, 
  RefreshCw,
  Eye,
  Monitor
} from 'lucide-react';
import { accessibilityService } from '../services/accessibilityService';

interface ValidationIssue {
  type: string;
  element: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
}

interface ValidationResult {
  issues: ValidationIssue[];
  score: number;
}

export const AccessibilityValidator: React.FC = () => {
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [lastValidated, setLastValidated] = useState<Date | null>(null);

  const runValidation = async () => {
    setIsValidating(true);
    
    try {
      // Small delay to show loading state
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const result = accessibilityService.validateSemanticStructure();
      setValidationResult(result);
      setLastValidated(new Date());
      
      accessibilityService.announce(
        `Accessibility validation complete. Score: ${result.score}%, ${result.issues.length} issues found`,
        'polite'
      );
    } catch (error) {
      console.error('Validation error:', error);
      accessibilityService.announce('Accessibility validation failed', 'assertive');
    } finally {
      setIsValidating(false);
    }
  };

  const enhanceStructure = () => {
    accessibilityService.enhanceSemanticStructure();
    // Re-run validation after enhancement
    setTimeout(runValidation, 1000);
  };

  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-400';
    if (score >= 70) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreDescription = (score: number): string => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Needs Improvement';
    return 'Poor';
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <XCircle className="text-red-400" size={16} />;
      case 'warning':
        return <AlertTriangle className="text-yellow-400" size={16} />;
      case 'info':
        return <Info className="text-blue-400" size={16} />;
      default:
        return <Info className="text-gray-400" size={16} />;
    }
  };

  const groupIssuesByType = (issues: ValidationIssue[]) => {
    return issues.reduce((groups, issue) => {
      const type = issue.type;
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(issue);
      return groups;
    }, {} as Record<string, ValidationIssue[]>);
  };

  useEffect(() => {
    // Run initial validation
    runValidation();
  }, []);

  return (
    <div className="accessibility-validator bg-gray-800 rounded-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Eye className="text-blue-400" size={24} />
          <div>
            <h3 className="text-lg font-semibold text-white">
              Accessibility Validator
            </h3>
            <p className="text-sm text-gray-400">
              WCAG compliance and semantic structure analysis
            </p>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={enhanceStructure}
            disabled={isValidating}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            aria-label="Enhance accessibility structure"
          >
            <Monitor size={16} />
            <span>Enhance</span>
          </button>
          
          <button
            onClick={runValidation}
            disabled={isValidating}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            aria-label="Run accessibility validation"
          >
            <RefreshCw className={`${isValidating ? 'animate-spin' : ''}`} size={16} />
            <span>Validate</span>
          </button>
        </div>
      </div>

      {/* Validation Results */}
      {validationResult && (
        <div className="space-y-4">
          {/* Score Display */}
          <div className="bg-gray-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-white font-medium">Accessibility Score</h4>
              {lastValidated && (
                <span className="text-xs text-gray-400">
                  Last validated: {lastValidated.toLocaleTimeString()}
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              <div className={`text-3xl font-bold ${getScoreColor(validationResult.score)}`}>
                {validationResult.score}%
              </div>
              <div>
                <div className={`text-sm font-medium ${getScoreColor(validationResult.score)}`}>
                  {getScoreDescription(validationResult.score)}
                </div>
                <div className="text-xs text-gray-400">
                  {validationResult.issues.length} issues found
                </div>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="mt-3 bg-gray-600 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  validationResult.score >= 90 ? 'bg-green-400' :
                  validationResult.score >= 70 ? 'bg-yellow-400' : 'bg-red-400'
                }`}
                style={{ width: `${validationResult.score}%` }}
                role="progressbar"
                aria-valuenow={validationResult.score}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Accessibility score: ${validationResult.score}%`}
              />
            </div>
          </div>

          {/* Issues List */}
          {validationResult.issues.length > 0 && (
            <div className="bg-gray-700/50 rounded-lg p-4">
              <h4 className="text-white font-medium mb-3">Issues Found</h4>
              
              <div className="space-y-3">
                {Object.entries(groupIssuesByType(validationResult.issues)).map(([type, issues]) => (
                  <div key={type} className="space-y-2">
                    <h5 className="text-sm font-medium text-gray-300 capitalize">
                      {type} Issues ({issues.length})
                    </h5>
                    
                    <div className="space-y-1">
                      {issues.map((issue, index) => (
                        <div
                          key={`${type}-${index}`}
                          className="flex items-start space-x-3 p-2 bg-gray-800/50 rounded text-sm"
                        >
                          {getSeverityIcon(issue.severity)}
                          <div className="flex-1">
                            <div className="text-white">{issue.message}</div>
                            <div className="text-gray-400 text-xs">
                              Element: {issue.element}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No Issues */}
          {validationResult.issues.length === 0 && (
            <div className="bg-green-900/20 border border-green-700 rounded-lg p-4 flex items-center space-x-3">
              <CheckCircle className="text-green-400" size={20} />
              <div>
                <div className="text-green-300 font-medium">
                  No accessibility issues found!
                </div>
                <div className="text-green-400 text-sm">
                  Your page follows accessibility best practices.
                </div>
              </div>
            </div>
          )}

          {/* Recommendations */}
          <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
            <h4 className="text-blue-300 font-medium mb-2 flex items-center space-x-2">
              <Info size={16} />
              <span>Accessibility Tips</span>
            </h4>
            
            <ul className="text-blue-200 text-sm space-y-1">
              <li>• Use semantic HTML elements (header, nav, main, footer)</li>
              <li>• Provide alt text for all meaningful images</li>
              <li>• Ensure proper heading hierarchy (h1, h2, h3...)</li>
              <li>• Label all form controls with associated labels</li>
              <li>• Maintain sufficient color contrast ratios</li>
              <li>• Make all interactive elements keyboard accessible</li>
              <li>• Use ARIA labels for complex components</li>
            </ul>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isValidating && !validationResult && (
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center space-x-3">
            <RefreshCw className="animate-spin text-blue-400" size={20} />
            <span className="text-gray-300">Running accessibility validation...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccessibilityValidator;