import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
    AlertCircle,
    Bug,
    CheckCircle,
    Lightbulb,
    MessageSquare,
    Send,
    X
} from 'lucide-react';
import React, { useState } from 'react';
import { useErrorTracking } from '../hooks/useErrorTracking';

interface UserFeedbackFormProps {
  isOpen: boolean;
  onClose: () => void;
  featureName?: string;
  initialType?: 'bug_report' | 'feature_request' | 'general';
}

const UserFeedbackForm: React.FC<UserFeedbackFormProps> = ({
  isOpen,
  onClose,
  featureName,
  initialType = 'general'
}) => {
  const [feedbackType, setFeedbackType] = useState<'bug_report' | 'feature_request' | 'general'>(initialType);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [email, setEmail] = useState('');
  const [severity, setSeverity] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const { submitFeedback } = useErrorTracking({ featureName });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !description.trim()) {
      setErrorMessage('Please fill in all required fields');
      setSubmitStatus('error');
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus('idle');
    setErrorMessage('');

    try {
      const feedbackId = await submitFeedback({
        type: feedbackType,
        title: title.trim(),
        description: description.trim(),
        severity,
        email: email.trim() || undefined
      });

      if (feedbackId) {
        setSubmitStatus('success');
        // Reset form
        setTitle('');
        setDescription('');
        setEmail('');
        setSeverity('medium');
        
        // Close form after a delay
        setTimeout(() => {
          onClose();
          setSubmitStatus('idle');
        }, 2000);
      } else {
        setSubmitStatus('error');
        setErrorMessage('Failed to submit feedback. Please try again.');
      }
    } catch (error) {
      setSubmitStatus('error');
      setErrorMessage('An error occurred while submitting feedback.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getFeedbackTypeIcon = (type: string) => {
    switch (type) {
      case 'bug_report': return <Bug className="h-4 w-4" />;
      case 'feature_request': return <Lightbulb className="h-4 w-4" />;
      default: return <MessageSquare className="h-4 w-4" />;
    }
  };

  const getSeverityColor = (sev: string) => {
    switch (sev) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="flex items-center">
            <MessageSquare className="h-5 w-5 mr-2" />
            Submit Feedback
            {featureName && (
              <Badge variant="outline" className="ml-2">
                {featureName}
              </Badge>
            )}
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <CardContent>
          {submitStatus === 'success' && (
            <Alert className="mb-4 border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                Thank you for your feedback! We'll review it and get back to you if needed.
              </AlertDescription>
            </Alert>
          )}

          {submitStatus === 'error' && (
            <Alert className="mb-4 border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                {errorMessage}
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Feedback Type */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Feedback Type *
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'bug_report', label: 'Bug Report', icon: Bug },
                  { value: 'feature_request', label: 'Feature Request', icon: Lightbulb },
                  { value: 'general', label: 'General', icon: MessageSquare }
                ].map(({ value, label, icon: Icon }) => (
                  <Button
                    key={value}
                    type="button"
                    variant={feedbackType === value ? 'default' : 'outline'}
                    className="flex items-center justify-center"
                    onClick={() => setFeedbackType(value as any)}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium mb-2">
                Title *
              </label>
              <Input
                id="title"
                value={title}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
                placeholder="Brief description of your feedback"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium mb-2">
                Description *
              </label>
              <Textarea
                id="description"
                value={description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDescription(e.target.value)}
                placeholder={
                  feedbackType === 'bug_report'
                    ? 'Please describe the bug, steps to reproduce, and expected vs actual behavior...'
                    : feedbackType === 'feature_request'
                    ? 'Please describe the feature you would like to see and how it would help you...'
                    : 'Please provide your feedback or suggestions...'
                }
                rows={6}
                required
              />
            </div>

            {/* Severity (for bug reports) */}
            {feedbackType === 'bug_report' && (
              <div>
                <label className="block text-sm font-medium mb-2">
                  Severity
                </label>
                <Select value={severity} onValueChange={(value: string) => setSeverity(value as 'low' | 'medium' | 'high')}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">
                      <div className="flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${getSeverityColor('low')}`} />
                        Low - Minor issue
                      </div>
                    </SelectItem>
                    <SelectItem value="medium">
                      <div className="flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${getSeverityColor('medium')}`} />
                        Medium - Moderate impact
                      </div>
                    </SelectItem>
                    <SelectItem value="high">
                      <div className="flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${getSeverityColor('high')}`} />
                        High - Significant impact
                      </div>
                    </SelectItem>
                    <SelectItem value="critical">
                      <div className="flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${getSeverityColor('critical')}`} />
                        Critical - System unusable
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-2">
                Email (optional)
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                placeholder="your.email@example.com"
              />
              <p className="text-xs text-gray-500 mt-1">
                We'll only use this to follow up on your feedback if needed
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-2 pt-4">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={isSubmitting || submitStatus === 'success'}
                className="flex items-center"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Submitting...
                  </>
                ) : submitStatus === 'success' ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Submitted!
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Submit Feedback
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default UserFeedbackForm;