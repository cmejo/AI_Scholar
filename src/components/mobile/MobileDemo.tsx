import React, { useState } from 'react';
import { 
  MessageCircle, 
  FileText, 
  Settings, 
  Search, 
  Heart,
  Star,
  Share,
  Download,
  Plus,
  Filter
} from 'lucide-react';
import { MobileCard } from './MobileCard';
import { MobileGrid, MobileGridItem } from './MobileGrid';
import { MobileButton } from './MobileButton';
import { MobileInput } from './MobileInput';
import { useMobileDetection } from '../../hooks/useMobileDetection';

export const MobileDemo: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const { isMobile, isTablet, orientation, screenSize } = useMobileDetection();

  const demoCards = [
    {
      id: 1,
      title: 'Research Paper Analysis',
      description: 'AI-powered analysis of academic papers with citation tracking and knowledge graph integration.',
      category: 'research',
      likes: 42,
      shares: 12
    },
    {
      id: 2,
      title: 'Document Collaboration',
      description: 'Real-time collaborative editing with version control and comment system.',
      category: 'collaboration',
      likes: 38,
      shares: 8
    },
    {
      id: 3,
      title: 'Voice Interface',
      description: 'Natural language voice commands for hands-free research assistance.',
      category: 'voice',
      likes: 56,
      shares: 23
    },
    {
      id: 4,
      title: 'Mobile Sync',
      description: 'Seamless synchronization between mobile and desktop with offline support.',
      category: 'mobile',
      likes: 34,
      shares: 15
    }
  ];

  const filters = [
    { id: 'all', label: 'All', count: demoCards.length },
    { id: 'research', label: 'Research', count: 1 },
    { id: 'collaboration', label: 'Collaboration', count: 1 },
    { id: 'voice', label: 'Voice', count: 1 },
    { id: 'mobile', label: 'Mobile', count: 1 }
  ];

  const filteredCards = selectedFilter === 'all' 
    ? demoCards 
    : demoCards.filter(card => card.category === selectedFilter);

  return (
    <div className="p-4 space-y-6 max-w-4xl mx-auto">
      {/* Device Info Header */}
      <MobileCard variant="elevated" className="bg-gradient-to-r from-purple-600/20 to-emerald-600/20">
        <div className="text-center space-y-2">
          <h1 className="text-responsive-xl font-bold">Mobile Interface Demo</h1>
          <div className="text-responsive text-gray-300 space-y-1">
            <p>Device: {isMobile ? 'Mobile' : isTablet ? 'Tablet' : 'Desktop'}</p>
            <p>Orientation: {orientation}</p>
            <p>Screen Size: {screenSize}</p>
          </div>
        </div>
      </MobileCard>

      {/* Search and Filter Section */}
      <div className="space-y-4">
        <MobileInput
          type="search"
          placeholder="Search features..."
          value={searchQuery}
          onChange={setSearchQuery}
          icon={Search}
          clearable
          className="w-full"
        />

        {/* Filter Buttons */}
        <div className="flex flex-wrap gap-2">
          {filters.map((filter) => (
            <MobileButton
              key={filter.id}
              variant={selectedFilter === filter.id ? 'primary' : 'outline'}
              size="small"
              onClick={() => setSelectedFilter(filter.id)}
              className="flex-shrink-0"
            >
              {filter.label} ({filter.count})
            </MobileButton>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <MobileGrid columns={2} gap="medium">
        <MobileGridItem>
          <MobileButton
            variant="primary"
            fullWidth
            icon={Plus}
            onClick={() => alert('Add new feature')}
          >
            Add Feature
          </MobileButton>
        </MobileGridItem>
        <MobileGridItem>
          <MobileButton
            variant="secondary"
            fullWidth
            icon={Filter}
            onClick={() => alert('Advanced filters')}
          >
            Filters
          </MobileButton>
        </MobileGridItem>
      </MobileGrid>

      {/* Feature Cards Grid */}
      <MobileGrid 
        columns={isMobile ? 1 : isTablet ? 2 : 3} 
        gap="large"
        responsive={true}
      >
        {filteredCards.map((card) => (
          <MobileGridItem key={card.id}>
            <MobileCard
              variant="elevated"
              interactive
              onClick={() => alert(`Viewing ${card.title}`)}
              onLongPress={() => alert(`Long pressed ${card.title}`)}
              className="h-full"
            >
              <div className="space-y-4">
                {/* Card Header */}
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-responsive-lg font-semibold truncate">
                      {card.title}
                    </h3>
                    <span className="inline-block px-2 py-1 text-xs bg-purple-600/20 text-purple-300 rounded-full mt-1 capitalize">
                      {card.category}
                    </span>
                  </div>
                  <div className="flex-shrink-0 ml-2">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-emerald-600 rounded-lg flex items-center justify-center">
                      {card.category === 'research' && <FileText size={20} />}
                      {card.category === 'collaboration' && <MessageCircle size={20} />}
                      {card.category === 'voice' && <Settings size={20} />}
                      {card.category === 'mobile' && <Search size={20} />}
                    </div>
                  </div>
                </div>

                {/* Card Content */}
                <p className="text-responsive text-gray-300 leading-relaxed">
                  {card.description}
                </p>

                {/* Card Actions */}
                <div className="flex items-center justify-between pt-2 border-t border-gray-700">
                  <div className="flex items-center space-x-4">
                    <button className="flex items-center space-x-1 text-gray-400 hover:text-red-400 transition-colors touch-manipulation">
                      <Heart size={16} />
                      <span className="text-sm">{card.likes}</span>
                    </button>
                    <button className="flex items-center space-x-1 text-gray-400 hover:text-blue-400 transition-colors touch-manipulation">
                      <Share size={16} />
                      <span className="text-sm">{card.shares}</span>
                    </button>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="p-2 text-gray-400 hover:text-yellow-400 transition-colors touch-manipulation rounded-lg hover:bg-gray-700">
                      <Star size={16} />
                    </button>
                    <button className="p-2 text-gray-400 hover:text-green-400 transition-colors touch-manipulation rounded-lg hover:bg-gray-700">
                      <Download size={16} />
                    </button>
                  </div>
                </div>
              </div>
            </MobileCard>
          </MobileGridItem>
        ))}
      </MobileGrid>

      {/* Touch Gesture Info */}
      <MobileCard variant="outlined" className="border-blue-600/50">
        <div className="text-center space-y-2">
          <h3 className="text-responsive-lg font-semibold text-blue-300">Touch Gestures</h3>
          <div className="text-responsive text-gray-300 space-y-1">
            <p>• Tap cards to view details</p>
            <p>• Long press for context menu</p>
            <p>• Swipe right to open navigation</p>
            <p>• Swipe left to close navigation</p>
            <p>• Pinch to zoom (where supported)</p>
          </div>
        </div>
      </MobileCard>

      {/* Responsive Features Info */}
      <MobileCard variant="outlined" className="border-emerald-600/50">
        <div className="text-center space-y-2">
          <h3 className="text-responsive-lg font-semibold text-emerald-300">Responsive Features</h3>
          <div className="text-responsive text-gray-300 space-y-1">
            <p>• Adaptive grid layouts</p>
            <p>• Touch-optimized buttons (44px min)</p>
            <p>• Responsive typography</p>
            <p>• Safe area support for notched devices</p>
            <p>• Keyboard-aware layouts</p>
            <p>• Orientation change handling</p>
          </div>
        </div>
      </MobileCard>
    </div>
  );
};