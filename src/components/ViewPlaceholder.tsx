import React from 'react';
import { LucideIcon } from 'lucide-react';

interface ViewPlaceholderProps {
  title: string;
  description: string;
  icon: LucideIcon;
  comingSoon?: boolean;
}

export const ViewPlaceholder: React.FC<ViewPlaceholderProps> = ({ 
  title, 
  description, 
  icon: Icon, 
  comingSoon = true 
}) => {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <Icon className="w-16 h-16 text-purple-500 mx-auto mb-4" />
        
        <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
        
        <p className="text-gray-400 mb-4">{description}</p>
        
        {comingSoon && (
          <div className="bg-purple-600/20 border border-purple-600/30 rounded-lg p-4">
            <p className="text-purple-300 font-medium">Coming Soon</p>
            <p className="text-purple-400 text-sm mt-1">
              This feature is currently under development and will be available in a future update.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};