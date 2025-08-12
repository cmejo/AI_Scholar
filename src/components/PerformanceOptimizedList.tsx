/**
 * Performance optimized list component demonstrating React.memo, useMemo, and virtualization
 */

import React, { useCallback, useMemo } from 'react';
import { useDebounce, useVirtualizedList } from '../hooks/usePerformanceOptimization';

interface ListItem {
  id: string;
  title: string;
  description: string;
  category: string;
  timestamp: Date;
}

interface ListItemProps {
  item: ListItem;
  isSelected: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

// Memoized list item component to prevent unnecessary re-renders
const ListItemComponent: React.FC<ListItemProps> = React.memo(({ 
  item, 
  isSelected, 
  onSelect, 
  onDelete 
}) => {
  const handleSelect = useCallback(() => {
    onSelect(item.id);
  }, [item.id, onSelect]);

  const handleDelete = useCallback(() => {
    onDelete(item.id);
  }, [item.id, onDelete]);

  const formattedDate = useMemo(() => {
    return item.timestamp.toLocaleDateString();
  }, [item.timestamp]);

  return (
    <div 
      className={`p-4 border-b border-gray-700 cursor-pointer transition-colors ${
        isSelected ? 'bg-purple-600/20' : 'hover:bg-gray-800'
      }`}
      onClick={handleSelect}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="font-medium text-white">{item.title}</h3>
          <p className="text-sm text-gray-400 mt-1">{item.description}</p>
          <div className="flex items-center space-x-2 mt-2">
            <span className="text-xs bg-gray-700 px-2 py-1 rounded">
              {item.category}
            </span>
            <span className="text-xs text-gray-500">{formattedDate}</span>
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleDelete();
          }}
          className="text-red-400 hover:text-red-300 text-sm ml-4"
        >
          Delete
        </button>
      </div>
    </div>
  );
});

ListItemComponent.displayName = 'ListItemComponent';

interface PerformanceOptimizedListProps {
  items: ListItem[];
  searchTerm: string;
  selectedCategory: string;
  selectedItems: string[];
  onItemSelect: (id: string) => void;
  onItemDelete: (id: string) => void;
  containerHeight?: number;
}

export const PerformanceOptimizedList: React.FC<PerformanceOptimizedListProps> = React.memo(({
  items,
  searchTerm,
  selectedCategory,
  selectedItems,
  onItemSelect,
  onItemDelete,
  containerHeight = 400,
}) => {
  // Debounce search term to prevent excessive filtering
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Memoize filtered items to prevent recalculation on every render
  const filteredItems = useMemo(() => {
    return items.filter(item => {
      const matchesSearch = !debouncedSearchTerm || 
        item.title.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
        item.description.toLowerCase().includes(debouncedSearchTerm.toLowerCase());
      
      const matchesCategory = !selectedCategory || 
        selectedCategory === 'all' || 
        item.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [items, debouncedSearchTerm, selectedCategory]);

  // Memoize categories for filter dropdown
  const categories = useMemo(() => {
    const categorySet = new Set(items.map(item => item.category));
    return ['all', ...Array.from(categorySet)];
  }, [items]);

  // Use virtualization for large lists
  const {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    visibleRange,
  } = useVirtualizedList({
    items: filteredItems,
    itemHeight: 120, // Approximate height of each item
    containerHeight,
    overscan: 5,
  });

  // Memoize selected items set for O(1) lookup
  const selectedItemsSet = useMemo(() => {
    return new Set(selectedItems);
  }, [selectedItems]);

  // Memoize callbacks to prevent child re-renders
  const memoizedOnSelect = useCallback((id: string) => {
    onItemSelect(id);
  }, [onItemSelect]);

  const memoizedOnDelete = useCallback((id: string) => {
    onItemDelete(id);
  }, [onItemDelete]);

  if (filteredItems.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        <div className="text-center">
          <p className="text-lg mb-2">No items found</p>
          <p className="text-sm">
            {debouncedSearchTerm ? 'Try adjusting your search terms' : 'No items to display'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Performance metrics display (development only) */}
      {typeof window !== 'undefined' && window.location.hostname === 'localhost' && (
        <div className="text-xs text-gray-500 p-2 bg-gray-800 rounded">
          <div>Total items: {items.length}</div>
          <div>Filtered items: {filteredItems.length}</div>
          <div>Visible range: {visibleRange.startIndex} - {visibleRange.endIndex}</div>
          <div>Categories: {categories.length}</div>
        </div>
      )}

      {/* Virtualized list container */}
      <div 
        className="overflow-auto border border-gray-700 rounded-lg"
        style={{ height: containerHeight }}
        onScroll={handleScroll}
      >
        {/* Virtual spacer for total height */}
        <div style={{ height: totalHeight, position: 'relative' }}>
          {/* Visible items container */}
          <div 
            style={{ 
              transform: `translateY(${offsetY}px)`,
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
            }}
          >
            {visibleItems.map((item) => (
              <ListItemComponent
                key={item.id}
                item={item}
                isSelected={selectedItemsSet.has(item.id)}
                onSelect={memoizedOnSelect}
                onDelete={memoizedOnDelete}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="text-sm text-gray-400 text-center">
        Showing {filteredItems.length} of {items.length} items
        {selectedItems.length > 0 && ` (${selectedItems.length} selected)`}
      </div>
    </div>
  );
});

PerformanceOptimizedList.displayName = 'PerformanceOptimizedList';

// Example usage component
export const PerformanceOptimizedListDemo: React.FC = () => {
  const [items] = React.useState<ListItem[]>(() => {
    // Generate sample data
    return Array.from({ length: 10000 }, (_, i) => ({
      id: `item-${i}`,
      title: `Item ${i + 1}`,
      description: `This is the description for item ${i + 1}`,
      category: ['work', 'personal', 'urgent', 'archived'][i % 4] || 'work',
      timestamp: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
    }));
  });

  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedCategory, setSelectedCategory] = React.useState('all');
  const [selectedItems, setSelectedItems] = React.useState<string[]>([]);

  const handleItemSelect = useCallback((id: string) => {
    setSelectedItems(prev => 
      prev.includes(id) 
        ? prev.filter(item => item !== id)
        : [...prev, id]
    );
  }, []);

  const handleItemDelete = useCallback((id: string) => {
    // In a real app, this would delete from the backend
    console.log('Delete item:', id);
  }, []);

  const categories = useMemo(() => {
    const categorySet = new Set(items.map(item => item.category));
    return ['all', ...Array.from(categorySet)];
  }, [items]);

  return (
    <div className="p-6 bg-gray-900 min-h-screen">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6">
          Performance Optimized List Demo
        </h1>

        {/* Controls */}
        <div className="flex space-x-4 mb-6">
          <input
            type="text"
            placeholder="Search items..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
          />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
          >
            {categories.map(category => (
              <option key={category} value={category}>
                {category === 'all' ? 'All Categories' : category}
              </option>
            ))}
          </select>
        </div>

        {/* Optimized List */}
        <PerformanceOptimizedList
          items={items}
          searchTerm={searchTerm}
          selectedCategory={selectedCategory}
          selectedItems={selectedItems}
          onItemSelect={handleItemSelect}
          onItemDelete={handleItemDelete}
          containerHeight={600}
        />
      </div>
    </div>
  );
};