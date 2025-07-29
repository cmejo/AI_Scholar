import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Star, MessageSquare, Send, CheckCircle, X } from 'lucide-react';

interface FeedbackData {
  rating: number;
  helpful: boolean;
  corrections?: string;
}

interface FeedbackCollectorProps {
  messageId: string;
  currentFeedback?: FeedbackData;
  onFeedback: (messageId: string, feedback: FeedbackData) => void;
}

export const FeedbackCollector: React.FC<FeedbackCollectorProps> = ({
  messageId,
  currentFeedback,
  onFeedback
}) => {
  const [showDetailedFeedback, setShowDetailedFeedback] = useState(false);
  const [rating, setRating] = useState(currentFeedback?.rating || 0);
  const [corrections, setCorrections] = useState(currentFeedback?.corrections || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showThankYou, setShowThankYou] = useState(false);

  const handleQuickFeedback = async (helpful: boolean) => {
    setIsSubmitting(true);
    
    const feedback: FeedbackData = {
      rating: helpful ? 5 : 2,
      helpful,
      corrections: corrections || undefined
    };

    onFeedback(messageId, feedback);
    
    // Show thank you message
    setShowThankYou(true);
    setTimeout(() => {
      setShowThankYou(false);
      setIsSubmitting(false);
    }, 2000);
  };

  const handleDetailedFeedback = async () => {
    if (rating === 0) return;
    
    setIsSubmitting(true);
    
    const feedback: FeedbackData = {
      rating,
      helpful: rating >= 3,
      corrections: corrections || undefined
    };

    onFeedback(messageId, feedback);
    
    // Show thank you message and close detailed feedback
    setShowThankYou(true);
    setTimeout(() => {
      setShowThankYou(false);
      setShowDetailedFeedback(false);
      setIsSubmitting(false);
    }, 2000);
  };

  const handleRatingClick = (selectedRating: number) => {
    setRating(selectedRating);
  };

  if (showThankYou) {
    return (
      <div className="mt-3 pt-3 border-t border-gray-600">
        <div className="flex items-center space-x-2 text-green-400 text-sm">
          <CheckCircle size={16} />
          <span>Thank you for your feedback! This helps me improve.</span>
        </div>
      </div>
    );
  }

  if (currentFeedback && !showDetailedFeedback) {
    return (
      <div className="mt-3 pt-3 border-t border-gray-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-sm text-gray-400">
            <CheckCircle size={14} className="text-green-400" />
            <span>Feedback submitted</span>
            <div className="flex items-center space-x-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  size={12}
                  className={star <= currentFeedback.rating ? 'text-yellow-400 fill-current' : 'text-gray-600'}
                />
              ))}
            </div>
          </div>
          <button
            onClick={() => setShowDetailedFeedback(true)}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            Update feedback
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-600">
      {!showDetailedFeedback ? (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400">Was this helpful?</span>
            <div className="flex items-center space-x-1">
              <button
                onClick={() => handleQuickFeedback(true)}
                disabled={isSubmitting}
                className="p-1 hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
                title="Helpful"
              >
                <ThumbsUp size={14} className="text-green-400 hover:text-green-300" />
              </button>
              <button
                onClick={() => handleQuickFeedback(false)}
                disabled={isSubmitting}
                className="p-1 hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
                title="Not helpful"
              >
                <ThumbsDown size={14} className="text-red-400 hover:text-red-300" />
              </button>
            </div>
          </div>
          
          <button
            onClick={() => setShowDetailedFeedback(true)}
            className="flex items-center space-x-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            <MessageSquare size={12} />
            <span>Detailed feedback</span>
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-200">Provide Feedback</span>
            <button
              onClick={() => setShowDetailedFeedback(false)}
              className="p-1 hover:bg-gray-700 rounded transition-colors"
            >
              <X size={14} className="text-gray-400" />
            </button>
          </div>
          
          {/* Star Rating */}
          <div>
            <div className="text-xs text-gray-400 mb-2">Rate this response:</div>
            <div className="flex items-center space-x-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => handleRatingClick(star)}
                  className="p-1 hover:bg-gray-700 rounded transition-colors"
                >
                  <Star
                    size={16}
                    className={
                      star <= rating 
                        ? 'text-yellow-400 fill-current' 
                        : 'text-gray-600 hover:text-gray-500'
                    }
                  />
                </button>
              ))}
              {rating > 0 && (
                <span className="ml-2 text-xs text-gray-400">
                  {rating === 1 && 'Poor'}
                  {rating === 2 && 'Fair'}
                  {rating === 3 && 'Good'}
                  {rating === 4 && 'Very Good'}
                  {rating === 5 && 'Excellent'}
                </span>
              )}
            </div>
          </div>

          {/* Corrections/Comments */}
          <div>
            <div className="text-xs text-gray-400 mb-2">
              Comments or corrections (optional):
            </div>
            <div className="relative">
              <textarea
                value={corrections}
                onChange={(e) => setCorrections(e.target.value)}
                placeholder="Help me improve by sharing what was wrong or what could be better..."
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={3}
              />
            </div>
          </div>

          {/* Quick Feedback Options */}
          <div>
            <div className="text-xs text-gray-400 mb-2">Quick feedback:</div>
            <div className="flex flex-wrap gap-2">
              {[
                'Too technical',
                'Not detailed enough',
                'Inaccurate information',
                'Missing sources',
                'Great explanation',
                'Very helpful'
              ].map((option) => (
                <button
                  key={option}
                  onClick={() => setCorrections(prev => 
                    prev ? `${prev}, ${option}` : option
                  )}
                  className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-gray-300 transition-colors"
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-between">
            <div className="text-xs text-gray-500">
              Your feedback helps improve the AI's responses
            </div>
            <button
              onClick={handleDetailedFeedback}
              disabled={rating === 0 || isSubmitting}
              className="flex items-center space-x-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:opacity-50 rounded text-sm text-white transition-colors"
            >
              <Send size={12} />
              <span>{isSubmitting ? 'Submitting...' : 'Submit Feedback'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};