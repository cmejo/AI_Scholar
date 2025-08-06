/**
 * Interactive Content Version Control Component
 * 
 * This component provides a user interface for version control
 * of interactive content including notebooks and visualizations.
 */

import React, { useState, useEffect } from 'react';
import {
  ContentVersion,
  ContentDiff,
  Branch,
  MergeRequest,
  BackupRecord,
  interactiveContentVersionControlService
} from '../services/interactiveContentVersionControlService';

interface InteractiveContentVersionControlProps {
  contentId: string;
  contentType: 'notebook' | 'visualization' | 'dataset' | 'script';
  currentData: Record<string, any>;
  onVersionChange?: (version: ContentVersion) => void;
  onDataUpdate?: (data: Record<string, any>) => void;
}

const InteractiveContentVersionControl: React.FC<InteractiveContentVersionControlProps> = ({
  contentId,
  contentType,
  currentData,
  onVersionChange,
  onDataUpdate
}) => {
  const [activeTab, setActiveTab] = useState<'history' | 'branches' | 'diff' | 'backups'>('history');
  const [versions, setVersions] = useState<ContentVersion[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [mergeRequests, setMergeRequests] = useState<MergeRequest[]>([]);
  const [backups, setBackups] = useState<BackupRecord[]>([]);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [diff, setDiff] = useState<ContentDiff | null>(null);
  const [currentBranch, setCurrentBranch] = useState<string>('main');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCommitModal, setShowCommitModal] = useState(false);
  const [showBranchModal, setShowBranchModal] = useState(false);
  const [showMergeModal, setShowMergeModal] = useState(false);
  const [showRevertModal, setShowRevertModal] = useState(false);

  // Form states
  const [commitMessage, setCommitMessage] = useState('');
  const [branchName, setBranchName] = useState('');
  const [branchDescription, setBranchDescription] = useState('');
  const [mergeBranches, setMergeBranches] = useState({ source: '', target: 'main' });
  const [mergeMessage, setMergeMessage] = useState('');
  const [revertVersionId, setRevertVersionId] = useState('');

  useEffect(() => {
    loadData();
  }, [contentId, currentBranch]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [versionsData, branchesData, mergeRequestsData, backupsData] = await Promise.all([
        interactiveContentVersionControlService.getVersionHistory(contentId, currentBranch),
        interactiveContentVersionControlService.getBranches(contentId),
        interactiveContentVersionControlService.getMergeRequests(contentId),
        interactiveContentVersionControlService.getBackups(contentId)
      ]);

      setVersions(versionsData);
      setBranches(branchesData);
      setMergeRequests(mergeRequestsData);
      setBackups(backupsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load version control data');
    } finally {
      setLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!commitMessage.trim()) {
      setError('Commit message is required');
      return;
    }

    try {
      setLoading(true);
      const version = await interactiveContentVersionControlService.commitChanges(contentId, {
        updated_data: currentData,
        commit_message: commitMessage,
        branch_name: currentBranch
      });

      setCommitMessage('');
      setShowCommitModal(false);
      await loadData();
      
      if (onVersionChange) {
        onVersionChange(version);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to commit changes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBranch = async () => {
    const validation = interactiveContentVersionControlService.validateBranchName(branchName);
    if (!validation.valid) {
      setError(validation.error || 'Invalid branch name');
      return;
    }

    if (!versions.length) {
      setError('No versions available to branch from');
      return;
    }

    try {
      setLoading(true);
      await interactiveContentVersionControlService.createBranch(contentId, {
        branch_name: branchName,
        from_version: versions[versions.length - 1].version_id,
        description: branchDescription
      });

      setBranchName('');
      setBranchDescription('');
      setShowBranchModal(false);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create branch');
    } finally {
      setLoading(false);
    }
  };

  const handleMerge = async () => {
    if (!mergeBranches.source || !mergeBranches.target) {
      setError('Please select source and target branches');
      return;
    }

    if (!mergeMessage.trim()) {
      setError('Merge message is required');
      return;
    }

    try {
      setLoading(true);
      const mergeRequest = await interactiveContentVersionControlService.mergeBranches(contentId, {
        source_branch: mergeBranches.source,
        target_branch: mergeBranches.target,
        merge_message: mergeMessage
      });

      setMergeMessage('');
      setShowMergeModal(false);
      await loadData();

      if (mergeRequest.status === 'conflict') {
        setError(`Merge conflicts detected: ${mergeRequest.conflicts.length} conflicts need resolution`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to merge branches');
    } finally {
      setLoading(false);
    }
  };

  const handleRevert = async () => {
    if (!revertVersionId) {
      setError('Please select a version to revert to');
      return;
    }

    try {
      setLoading(true);
      const version = await interactiveContentVersionControlService.revertToVersion(contentId, {
        version_id: revertVersionId,
        branch_name: currentBranch
      });

      setRevertVersionId('');
      setShowRevertModal(false);
      await loadData();

      if (onVersionChange) {
        onVersionChange(version);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revert to version');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDiff = async () => {
    if (selectedVersions.length !== 2) {
      setError('Please select exactly 2 versions to compare');
      return;
    }

    try {
      setLoading(true);
      const diffData = await interactiveContentVersionControlService.getVersionDiff(
        contentId,
        selectedVersions[0],
        selectedVersions[1]
      );
      setDiff(diffData);
      setActiveTab('diff');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate diff');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    try {
      setLoading(true);
      await interactiveContentVersionControlService.createBackup(contentId, {
        backup_type: 'manual'
      });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create backup');
    } finally {
      setLoading(false);
    }
  };

  const handleRestoreBackup = async (backupId: string) => {
    try {
      setLoading(true);
      const version = await interactiveContentVersionControlService.restoreFromBackup(contentId, {
        backup_id: backupId
      });
      
      await loadData();
      
      if (onVersionChange) {
        onVersionChange(version);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restore from backup');
    } finally {
      setLoading(false);
    }
  };

  const renderVersionHistory = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Version History</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCommitModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Commit Changes
          </button>
          <button
            onClick={handleGenerateDiff}
            disabled={selectedVersions.length !== 2}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            Compare Selected
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {versions.map((version) => (
          <div
            key={version.version_id}
            className={`p-4 border rounded-lg cursor-pointer transition-colors ${
              selectedVersions.includes(version.version_id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => {
              if (selectedVersions.includes(version.version_id)) {
                setSelectedVersions(selectedVersions.filter(id => id !== version.version_id));
              } else if (selectedVersions.length < 2) {
                setSelectedVersions([...selectedVersions, version.version_id]);
              }
            }}
          >
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium">v{version.version_number}</h4>
                <p className="text-sm text-gray-600">{version.commit_message}</p>
                <p className="text-xs text-gray-500">
                  {interactiveContentVersionControlService.getRelativeTime(version.created_at)} by {version.author_id}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setRevertVersionId(version.version_id);
                    setShowRevertModal(true);
                  }}
                  className="text-sm px-2 py-1 text-orange-600 hover:bg-orange-50 rounded"
                >
                  Revert
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderBranches = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Branches</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setShowBranchModal(true)}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            New Branch
          </button>
          <button
            onClick={() => setShowMergeModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
          >
            Merge Branches
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {branches.map((branch) => (
          <div
            key={branch.branch_id}
            className={`p-4 border rounded-lg ${
              branch.branch_name === currentBranch
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200'
            }`}
          >
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium flex items-center gap-2">
                  {branch.branch_name}
                  {branch.branch_name === currentBranch && (
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      Current
                    </span>
                  )}
                </h4>
                <p className="text-sm text-gray-600">{branch.description}</p>
                <p className="text-xs text-gray-500">
                  Created {interactiveContentVersionControlService.getRelativeTime(branch.created_at)} by {branch.created_by}
                </p>
              </div>
              {branch.branch_name !== currentBranch && (
                <button
                  onClick={() => setCurrentBranch(branch.branch_name)}
                  className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Switch
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {mergeRequests.length > 0 && (
        <div className="mt-6">
          <h4 className="font-medium mb-2">Merge Requests</h4>
          <div className="space-y-2">
            {mergeRequests.map((mr) => (
              <div key={mr.merge_id} className="p-3 border rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <h5 className="font-medium">{mr.title}</h5>
                    <p className="text-sm text-gray-600">
                      {mr.source_branch} → {mr.target_branch}
                    </p>
                    <p className="text-xs text-gray-500">
                      {interactiveContentVersionControlService.getRelativeTime(mr.created_at)}
                    </p>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded text-white`}
                    style={{
                      backgroundColor: interactiveContentVersionControlService.getMergeStatusColor(mr.status)
                    }}
                  >
                    {mr.status}
                  </span>
                </div>
                {mr.conflicts.length > 0 && (
                  <div className="mt-2 text-sm text-orange-600">
                    {mr.conflicts.length} conflicts need resolution
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderDiff = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Version Comparison</h3>
      
      {diff ? (
        <div>
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium">Summary</h4>
            <p className="text-sm text-gray-600">
              {interactiveContentVersionControlService.formatDiffSummary(diff)}
            </p>
          </div>

          <div className="space-y-2">
            {diff.changes.map((change, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border-l-4 ${
                  change.type === 'added'
                    ? 'bg-green-50 border-green-500'
                    : change.type === 'deleted'
                    ? 'bg-red-50 border-red-500'
                    : 'bg-yellow-50 border-yellow-500'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <span className="font-medium">{change.path}</span>
                    <span
                      className={`ml-2 text-xs px-2 py-1 rounded ${
                        change.type === 'added'
                          ? 'bg-green-100 text-green-800'
                          : change.type === 'deleted'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {change.type}
                    </span>
                  </div>
                </div>
                
                {change.type === 'modified' && (
                  <div className="mt-2 text-sm">
                    <div className="text-red-600">- {JSON.stringify(change.old_value)}</div>
                    <div className="text-green-600">+ {JSON.stringify(change.new_value)}</div>
                  </div>
                )}
                
                {change.type === 'added' && (
                  <div className="mt-2 text-sm text-green-600">
                    + {JSON.stringify(change.new_value)}
                  </div>
                )}
                
                {change.type === 'deleted' && (
                  <div className="mt-2 text-sm text-red-600">
                    - {JSON.stringify(change.old_value)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          Select two versions from the History tab to compare them
        </div>
      )}
    </div>
  );

  const renderBackups = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Backups</h3>
        <button
          onClick={handleCreateBackup}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Create Backup
        </button>
      </div>

      <div className="space-y-2">
        {backups.map((backup) => (
          <div key={backup.backup_id} className="p-4 border rounded-lg">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-medium">{backup.backup_type} backup</h4>
                <p className="text-sm text-gray-600">
                  Created {interactiveContentVersionControlService.getRelativeTime(backup.created_at)}
                </p>
                <p className="text-xs text-gray-500">
                  Expires {interactiveContentVersionControlService.getRelativeTime(backup.retention_until)}
                </p>
              </div>
              <button
                onClick={() => handleRestoreBackup(backup.backup_id)}
                className="text-sm px-3 py-1 bg-orange-600 text-white rounded hover:bg-orange-700"
              >
                Restore
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-2">Version Control</h2>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>Content: {contentId}</span>
          <span>Type: {contentType}</span>
          <span>Branch: {currentBranch}</span>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-red-500 hover:text-red-700"
          >
            ×
          </button>
        </div>
      )}

      <div className="mb-6">
        <div className="flex border-b">
          {[
            { key: 'history', label: 'History' },
            { key: 'branches', label: 'Branches' },
            { key: 'diff', label: 'Compare' },
            { key: 'backups', label: 'Backups' }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`px-4 py-2 font-medium ${
                activeTab === tab.key
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {!loading && (
        <div>
          {activeTab === 'history' && renderVersionHistory()}
          {activeTab === 'branches' && renderBranches()}
          {activeTab === 'diff' && renderDiff()}
          {activeTab === 'backups' && renderBackups()}
        </div>
      )}

      {/* Modals */}
      {showCommitModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Commit Changes</h3>
            <textarea
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              placeholder="Enter commit message..."
              className="w-full p-3 border rounded-lg resize-none"
              rows={3}
            />
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => setShowCommitModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleCommit}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Commit
              </button>
            </div>
          </div>
        </div>
      )}

      {showBranchModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Create New Branch</h3>
            <input
              type="text"
              value={branchName}
              onChange={(e) => setBranchName(e.target.value)}
              placeholder="Branch name (e.g., feature/new-feature)"
              className="w-full p-3 border rounded-lg mb-3"
            />
            <textarea
              value={branchDescription}
              onChange={(e) => setBranchDescription(e.target.value)}
              placeholder="Branch description (optional)"
              className="w-full p-3 border rounded-lg resize-none"
              rows={2}
            />
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => setShowBranchModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateBranch}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Create Branch
              </button>
            </div>
          </div>
        </div>
      )}

      {showMergeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Merge Branches</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Source Branch</label>
                <select
                  value={mergeBranches.source}
                  onChange={(e) => setMergeBranches({ ...mergeBranches, source: e.target.value })}
                  className="w-full p-2 border rounded-lg"
                >
                  <option value="">Select source branch</option>
                  {branches.filter(b => b.branch_name !== mergeBranches.target).map(branch => (
                    <option key={branch.branch_id} value={branch.branch_name}>
                      {branch.branch_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Target Branch</label>
                <select
                  value={mergeBranches.target}
                  onChange={(e) => setMergeBranches({ ...mergeBranches, target: e.target.value })}
                  className="w-full p-2 border rounded-lg"
                >
                  {branches.filter(b => b.branch_name !== mergeBranches.source).map(branch => (
                    <option key={branch.branch_id} value={branch.branch_name}>
                      {branch.branch_name}
                    </option>
                  ))}
                </select>
              </div>
              <textarea
                value={mergeMessage}
                onChange={(e) => setMergeMessage(e.target.value)}
                placeholder="Merge message..."
                className="w-full p-3 border rounded-lg resize-none"
                rows={2}
              />
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => setShowMergeModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleMerge}
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
              >
                Merge
              </button>
            </div>
          </div>
        </div>
      )}

      {showRevertModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Revert to Version</h3>
            <p className="text-sm text-gray-600 mb-4">
              This will create a new version with the content from the selected version.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowRevertModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleRevert}
                className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
              >
                Revert
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveContentVersionControl;