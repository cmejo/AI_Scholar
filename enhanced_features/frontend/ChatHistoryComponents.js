// Advanced Chat History Management Components
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { format, formatDistanceToNow } from 'date-fns';

// Custom hook for chat history management
export const useChatHistory = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({});
  const [filters, setFilters] = useState({
    search_query: '',
    date_filter: '',
    sort_by: 'updated_at',
    sort_order: 'desc'
  });

  const fetchSessions = useCallback(async (page = 1) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20',
        ...filters
      });

      const response = await fetch(`/api/chat/sessions?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSessions(data.sessions || []);
      setPagination(data.pagination || {});
    } catch (err) {
      setError(err.message);
      console.error('Error fetching sessions:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const updateSessionName = async (sessionId, newName) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ session_name: newName })
      });

      if (!response.ok) {
        throw new Error('Failed to update session name');
      }

      // Update local state
      setSessions(prev => prev.map(session => 
        session.id === sessionId 
          ? { ...session, session_name: newName }
          : session
      ));

      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      // Remove from local state
      setSessions(prev => prev.filter(session => session.id !== sessionId));
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  const bulkDeleteSessions = async (sessionIds) => {
    try {
      const response = await fetch('/api/chat/sessions/bulk-delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ session_ids: sessionIds })
      });

      if (!response.ok) {
        throw new Error('Failed to delete sessions');
      }

      const result = await response.json();
      
      // Remove deleted sessions from local state
      setSessions(prev => prev.filter(session => !sessionIds.includes(session.id)));
      
      return result;
    } catch (err) {
      setError(err.message);
      return null;
    }
  };

  const searchHistory = async (query, searchType = 'content') => {
    try {
      const params = new URLSearchParams({
        q: query,
        type: searchType,
        limit: '50'
      });

      const response = await fetch(`/api/chat/search?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      return await response.json();
    } catch (err) {
      setError(err.message);
      return null;
    }
  };

  const exportSession = async (sessionId, format = 'json') => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionId}/export?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const data = await response.json();
      
      // Create download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat-session-${sessionId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  return {
    sessions,
    loading,
    error,
    pagination,
    filters,
    setFilters,
    fetchSessions,
    updateSessionName,
    deleteSession,
    bulkDeleteSessions,
    searchHistory,
    exportSession
  };
};

// Session Card Component
export const SessionCard = ({ 
  session, 
  onEdit, 
  onDelete, 
  onSelect, 
  isSelected = false,
  showCheckbox = false 
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(session.session_name);
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSaveEdit = async () => {
    if (editName.trim() && editName !== session.session_name) {
      const success = await onEdit(session.id, editName.trim());
      if (success) {
        setIsEditing(false);
      }
    } else {
      setIsEditing(false);
      setEditName(session.session_name);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setEditName(session.session_name);
    }
  };

  return (
    <div className={`session-card bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${
      isSelected ? 'ring-2 ring-blue-500' : ''
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          {showCheckbox && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onSelect(session.id)}
              className="mt-1 rounded"
            />
          )}
          
          <div className="flex-1 min-w-0">
            {isEditing ? (
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onBlur={handleSaveEdit}
                onKeyPress={handleKeyPress}
                className="w-full p-1 border rounded text-sm font-medium"
                autoFocus
              />
            ) : (
              <h3 
                className="text-sm font-medium text-gray-900 truncate cursor-pointer hover:text-blue-600"
                onClick={() => onSelect && onSelect(session.id)}
              >
                {session.session_name}
              </h3>
            )}
            
            {session.last_message && (
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                {session.last_message.content}
              </p>
            )}
            
            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-400">
              <span>💬 {session.message_count || 0} messages</span>
              <span>🕒 {formatDistanceToNow(new Date(session.updated_at), { addSuffix: true })}</span>
              {session.statistics?.models_used?.length > 0 && (
                <span>🤖 {session.statistics.models_used[0]}</span>
              )}
            </div>
          </div>
        </div>
        
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            ⋮
          </button>
          
          {showMenu && (
            <div className="absolute right-0 top-8 bg-white border rounded-md shadow-lg z-10 min-w-32">
              <button
                onClick={() => {
                  setIsEditing(true);
                  setShowMenu(false);
                }}
                className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-100"
              >
                ✏️ Rename
              </button>
              <button
                onClick={() => {
                  onDelete(session.id);
                  setShowMenu(false);
                }}
                className="block w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                🗑️ Delete
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Search Component
export const ChatHistorySearch = ({ onSearch, onClear }) => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('content');
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    await onSearch(query, searchType);
    setIsSearching(false);
  };

  const handleClear = () => {
    setQuery('');
    onClear();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="search-component bg-white border rounded-lg p-4 mb-4">
      <div className="flex items-center space-x-2 mb-3">
        <div className="flex-1 relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search your chat history..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <div className="absolute left-3 top-2.5 text-gray-400">
            🔍
          </div>
        </div>
        
        <select
          value={searchType}
          onChange={(e) => setSearchType(e.target.value)}
          className="border rounded-lg px-3 py-2"
        >
          <option value="content">Messages</option>
          <option value="sessions">Sessions</option>
          <option value="semantic">Smart Search</option>
        </select>
        
        <button
          onClick={handleSearch}
          disabled={!query.trim() || isSearching}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
        >
          {isSearching ? '⏳' : '🔍'}
        </button>
        
        {query && (
          <button
            onClick={handleClear}
            className="px-3 py-2 text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        )}
      </div>
      
      <div className="text-xs text-gray-500">
        <strong>Tips:</strong> Use "content" to search message text, "sessions" to search session names, 
        or "smart search" for AI-powered semantic search.
      </div>
    </div>
  );
};

// Search Results Component
export const SearchResults = ({ results, onSelectSession, onClear }) => {
  if (!results || results.length === 0) {
    return (
      <div className="search-results bg-gray-50 border rounded-lg p-8 text-center">
        <div className="text-gray-500 mb-2">🔍</div>
        <p className="text-gray-600">No results found</p>
      </div>
    );
  }

  return (
    <div className="search-results bg-white border rounded-lg">
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="font-medium">Search Results ({results.length})</h3>
        <button
          onClick={onClear}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ✕ Clear
        </button>
      </div>
      
      <div className="max-h-96 overflow-y-auto">
        {results.map((result, index) => (
          <div
            key={index}
            className="p-4 border-b last:border-b-0 hover:bg-gray-50 cursor-pointer"
            onClick={() => onSelectSession(result.session_id)}
          >
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {result.type === 'message' ? '💬 Message' : 
                 result.type === 'session' ? '📁 Session' : '🧠 Smart Match'}
              </span>
              <span className="text-xs text-gray-500">
                {format(new Date(result.timestamp), 'MMM dd, yyyy')}
              </span>
            </div>
            
            <h4 className="font-medium text-sm mb-1">{result.session_name}</h4>
            
            {result.content && (
              <p 
                className="text-sm text-gray-600 line-clamp-2"
                dangerouslySetInnerHTML={{ __html: result.content }}
              />
            )}
            
            {result.relevance_score && (
              <div className="mt-2">
                <span className="text-xs text-gray-500">
                  Relevance: {(result.relevance_score * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// Filters Component
export const ChatHistoryFilters = ({ filters, onFiltersChange }) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleFilterChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  return (
    <div className="filters-component bg-white border rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium">Filters</h3>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-blue-500 hover:text-blue-700"
        >
          {showAdvanced ? 'Hide' : 'Show'} Advanced
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Date Range</label>
          <select
            value={filters.date_filter || ''}
            onChange={(e) => handleFilterChange('date_filter', e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="">All Time</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="year">This Year</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">Sort By</label>
          <select
            value={filters.sort_by || 'updated_at'}
            onChange={(e) => handleFilterChange('sort_by', e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="updated_at">Last Updated</option>
            <option value="created_at">Created Date</option>
            <option value="session_name">Name</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">Order</label>
          <select
            value={filters.sort_order || 'desc'}
            onChange={(e) => handleFilterChange('sort_order', e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </select>
        </div>
      </div>
      
      {showAdvanced && (
        <div className="mt-4 pt-4 border-t">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Quick Search</label>
              <input
                type="text"
                value={filters.search_query || ''}
                onChange={(e) => handleFilterChange('search_query', e.target.value)}
                placeholder="Filter sessions..."
                className="w-full border rounded px-3 py-2"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Bulk Actions Component
export const BulkActions = ({ selectedSessions, onBulkDelete, onClearSelection }) => {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleBulkDelete = async () => {
    await onBulkDelete(selectedSessions);
    setShowConfirm(false);
    onClearSelection();
  };

  if (selectedSessions.length === 0) {
    return null;
  }

  return (
    <div className="bulk-actions bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {selectedSessions.length} session{selectedSessions.length !== 1 ? 's' : ''} selected
        </span>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowConfirm(true)}
            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
          >
            🗑️ Delete Selected
          </button>
          <button
            onClick={onClearSelection}
            className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
          >
            Clear Selection
          </button>
        </div>
      </div>
      
      {showConfirm && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-800 mb-2">
            Are you sure you want to delete {selectedSessions.length} session{selectedSessions.length !== 1 ? 's' : ''}? 
            This action cannot be undone.
          </p>
          <div className="flex space-x-2">
            <button
              onClick={handleBulkDelete}
              className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
            >
              Yes, Delete
            </button>
            <button
              onClick={() => setShowConfirm(false)}
              className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Main Chat History Component
export const EnhancedChatHistory = ({ onSelectSession }) => {
  const {
    sessions,
    loading,
    error,
    pagination,
    filters,
    setFilters,
    fetchSessions,
    updateSessionName,
    deleteSession,
    bulkDeleteSessions,
    searchHistory,
    exportSession
  } = useChatHistory();

  const [selectedSessions, setSelectedSessions] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    fetchSessions(currentPage);
  }, [fetchSessions, currentPage]);

  const handleSearch = async (query, searchType) => {
    const results = await searchHistory(query, searchType);
    if (results) {
      setSearchResults(results.results);
    }
  };

  const handleClearSearch = () => {
    setSearchResults(null);
  };

  const handleSelectSession = (sessionId) => {
    if (showBulkActions) {
      setSelectedSessions(prev => 
        prev.includes(sessionId)
          ? prev.filter(id => id !== sessionId)
          : [...prev, sessionId]
      );
    } else {
      onSelectSession(sessionId);
    }
  };

  const handleBulkDelete = async (sessionIds) => {
    const result = await bulkDeleteSessions(sessionIds);
    if (result) {
      console.log(`Deleted ${result.deleted} sessions`);
      fetchSessions(currentPage);
    }
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const toggleBulkActions = () => {
    setShowBulkActions(!showBulkActions);
    setSelectedSessions([]);
  };

  return (
    <div className="enhanced-chat-history max-w-4xl mx-auto p-4">
      <div className="header mb-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">Chat History</h1>
          <div className="flex space-x-2">
            <button
              onClick={toggleBulkActions}
              className={`px-4 py-2 rounded ${
                showBulkActions 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {showBulkActions ? '✓ Bulk Mode' : '☐ Select Multiple'}
            </button>
          </div>
        </div>
        
        <ChatHistorySearch onSearch={handleSearch} onClear={handleClearSearch} />
        
        {!searchResults && (
          <ChatHistoryFilters filters={filters} onFiltersChange={setFilters} />
        )}
      </div>

      {showBulkActions && (
        <BulkActions
          selectedSessions={selectedSessions}
          onBulkDelete={handleBulkDelete}
          onClearSelection={() => setSelectedSessions([])}
        />
      )}

      <div className="content">
        {error && (
          <div className="error-message bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            <strong>Error:</strong> {error}
          </div>
        )}

        {searchResults ? (
          <SearchResults
            results={searchResults}
            onSelectSession={onSelectSession}
            onClear={handleClearSearch}
          />
        ) : (
          <>
            {loading ? (
              <div className="loading text-center py-8">
                <div className="animate-spin text-4xl mb-2">⏳</div>
                <p className="text-gray-600">Loading chat history...</p>
              </div>
            ) : sessions.length === 0 ? (
              <div className="empty-state text-center py-12">
                <div className="text-6xl mb-4">💬</div>
                <h3 className="text-lg font-medium mb-2">No chat sessions yet</h3>
                <p className="text-gray-600">Start a new conversation to see it here!</p>
              </div>
            ) : (
              <>
                <div className="sessions-grid grid gap-4 mb-6">
                  {sessions.map((session) => (
                    <SessionCard
                      key={session.id}
                      session={session}
                      onEdit={updateSessionName}
                      onDelete={deleteSession}
                      onSelect={handleSelectSession}
                      isSelected={selectedSessions.includes(session.id)}
                      showCheckbox={showBulkActions}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {pagination.pages > 1 && (
                  <div className="pagination flex justify-center items-center space-x-2">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage <= 1}
                      className="px-3 py-2 border rounded disabled:opacity-50"
                    >
                      ← Previous
                    </button>
                    
                    <span className="px-4 py-2">
                      Page {currentPage} of {pagination.pages}
                    </span>
                    
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage >= pagination.pages}
                      className="px-3 py-2 border rounded disabled:opacity-50"
                    >
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// CSS for chat history components
export const chatHistoryStyles = `
.session-card {
  transition: all 0.2s ease-in-out;
}

.session-card:hover {
  transform: translateY(-1px);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.search-component input:focus {
  outline: none;
}

.filters-component select:focus,
.filters-component input:focus {
  outline: none;
  ring: 2px;
  ring-color: #3b82f6;
}

.bulk-actions {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.search-results {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.sessions-grid {
  animation: fadeIn 0.5s ease-out;
}

.loading {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.empty-state {
  animation: fadeIn 0.5s ease-out;
}

.pagination button:disabled {
  cursor: not-allowed;
}

.pagination button:not(:disabled):hover {
  background-color: #f3f4f6;
}

/* Responsive design */
@media (max-width: 768px) {
  .enhanced-chat-history {
    padding: 1rem;
  }
  
  .header .flex {
    flex-direction: column;
    gap: 1rem;
  }
  
  .filters-component .grid {
    grid-template-columns: 1fr;
  }
  
  .session-card {
    padding: 0.75rem;
  }
}
`;

export default EnhancedChatHistory;