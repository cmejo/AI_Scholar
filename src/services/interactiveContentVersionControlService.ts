/**
 * Interactive Content Version Control Service
 * 
 * This service provides client-side functionality for version control
 * of interactive content including notebooks and visualizations.
 */

export interface ContentVersion {
  version_id: string;
  content_id: string;
  content_type: string;
  version_number: number;
  commit_hash: string;
  author_id: string;
  commit_message: string;
  created_at: string;
  parent_versions: string[];
  tags: string[];
  metadata: Record<string, any>;
}

export interface ContentDiff {
  diff_id: string;
  from_version: string;
  to_version: string;
  content_id: string;
  changes: Array<{
    type: 'added' | 'modified' | 'deleted';
    path: string;
    old_value?: any;
    new_value?: any;
  }>;
  summary: {
    added: number;
    modified: number;
    deleted: number;
  };
  created_at: string;
}

export interface Branch {
  branch_id: string;
  content_id: string;
  branch_name: string;
  head_version: string;
  created_from: string;
  created_by: string;
  created_at: string;
  is_active: boolean;
  description: string;
}

export interface MergeRequest {
  merge_id: string;
  content_id: string;
  source_branch: string;
  target_branch: string;
  title: string;
  description: string;
  author_id: string;
  status: 'success' | 'conflict' | 'failed';
  conflicts: Array<{
    path: string;
    source_value: any;
    target_value: any;
    conflict_type: string;
  }>;
  created_at: string;
  merged_at?: string;
  merged_by?: string;
}

export interface BackupRecord {
  backup_id: string;
  content_id: string;
  backup_type: string;
  version_snapshot: string;
  created_at: string;
  retention_until: string;
}

export interface InitializeVersioningRequest {
  content_type: 'notebook' | 'visualization' | 'dataset' | 'script';
  initial_data: Record<string, any>;
  commit_message?: string;
}

export interface CommitChangesRequest {
  updated_data: Record<string, any>;
  commit_message: string;
  branch_name?: string;
}

export interface CreateBranchRequest {
  branch_name: string;
  from_version: string;
  description?: string;
}

export interface MergeBranchesRequest {
  source_branch: string;
  target_branch: string;
  merge_message: string;
}

export interface RevertToVersionRequest {
  version_id: string;
  branch_name?: string;
}

export interface CreateBackupRequest {
  backup_type?: string;
}

export interface RestoreFromBackupRequest {
  backup_id: string;
}

class InteractiveContentVersionControlService {
  private baseUrl = '/api/content/version-control';

  /**
   * Initialize version control for new content
   */
  async initializeVersioning(
    contentId: string,
    request: InitializeVersioningRequest
  ): Promise<ContentVersion> {
    const response = await fetch(`${this.baseUrl}/${contentId}/initialize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to initialize version control');
    }

    return response.json();
  }

  /**
   * Commit changes to content
   */
  async commitChanges(
    contentId: string,
    request: CommitChangesRequest
  ): Promise<ContentVersion> {
    const response = await fetch(`${this.baseUrl}/${contentId}/commit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to commit changes');
    }

    return response.json();
  }

  /**
   * Get version history for content
   */
  async getVersionHistory(
    contentId: string,
    branchName?: string
  ): Promise<ContentVersion[]> {
    const url = new URL(`${this.baseUrl}/${contentId}/history`, window.location.origin);
    if (branchName) {
      url.searchParams.set('branch_name', branchName);
    }

    const response = await fetch(url.toString());

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get version history');
    }

    return response.json();
  }

  /**
   * Generate diff between two versions
   */
  async getVersionDiff(
    contentId: string,
    fromVersion: string,
    toVersion: string
  ): Promise<ContentDiff> {
    const response = await fetch(
      `${this.baseUrl}/${contentId}/diff/${fromVersion}/${toVersion}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate diff');
    }

    return response.json();
  }

  /**
   * Create a new branch
   */
  async createBranch(
    contentId: string,
    request: CreateBranchRequest
  ): Promise<Branch> {
    const response = await fetch(`${this.baseUrl}/${contentId}/branches`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create branch');
    }

    return response.json();
  }

  /**
   * Get all branches for content
   */
  async getBranches(contentId: string): Promise<Branch[]> {
    const response = await fetch(`${this.baseUrl}/${contentId}/branches`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get branches');
    }

    return response.json();
  }

  /**
   * Merge branches
   */
  async mergeBranches(
    contentId: string,
    request: MergeBranchesRequest
  ): Promise<MergeRequest> {
    const response = await fetch(`${this.baseUrl}/${contentId}/merge`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to merge branches');
    }

    return response.json();
  }

  /**
   * Get merge requests for content
   */
  async getMergeRequests(contentId: string): Promise<MergeRequest[]> {
    const response = await fetch(`${this.baseUrl}/${contentId}/merge-requests`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get merge requests');
    }

    return response.json();
  }

  /**
   * Revert to a specific version
   */
  async revertToVersion(
    contentId: string,
    request: RevertToVersionRequest
  ): Promise<ContentVersion> {
    const response = await fetch(`${this.baseUrl}/${contentId}/revert`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to revert to version');
    }

    return response.json();
  }

  /**
   * Create backup
   */
  async createBackup(
    contentId: string,
    request: CreateBackupRequest = {}
  ): Promise<BackupRecord> {
    const response = await fetch(`${this.baseUrl}/${contentId}/backup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create backup');
    }

    return response.json();
  }

  /**
   * Get backups for content
   */
  async getBackups(contentId: string): Promise<BackupRecord[]> {
    const response = await fetch(`${this.baseUrl}/${contentId}/backups`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get backups');
    }

    return response.json();
  }

  /**
   * Restore from backup
   */
  async restoreFromBackup(
    contentId: string,
    request: RestoreFromBackupRequest
  ): Promise<ContentVersion> {
    const response = await fetch(`${this.baseUrl}/${contentId}/restore`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to restore from backup');
    }

    return response.json();
  }

  /**
   * Format version for display
   */
  formatVersion(version: ContentVersion): string {
    const date = new Date(version.created_at).toLocaleDateString();
    return `v${version.version_number} - ${version.commit_message} (${date})`;
  }

  /**
   * Format diff summary for display
   */
  formatDiffSummary(diff: ContentDiff): string {
    const { added, modified, deleted } = diff.summary;
    const parts = [];
    
    if (added > 0) parts.push(`+${added} added`);
    if (modified > 0) parts.push(`~${modified} modified`);
    if (deleted > 0) parts.push(`-${deleted} deleted`);
    
    return parts.join(', ') || 'No changes';
  }

  /**
   * Get status color for merge request
   */
  getMergeStatusColor(status: string): string {
    switch (status) {
      case 'success':
        return 'green';
      case 'conflict':
        return 'orange';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  }

  /**
   * Check if branch can be merged
   */
  canMergeBranch(mergeRequest: MergeRequest): boolean {
    return mergeRequest.status === 'success' || mergeRequest.conflicts.length === 0;
  }

  /**
   * Get relative time string
   */
  getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;
    
    return date.toLocaleDateString();
  }

  /**
   * Validate branch name
   */
  validateBranchName(name: string): { valid: boolean; error?: string } {
    if (!name || name.trim().length === 0) {
      return { valid: false, error: 'Branch name is required' };
    }

    if (name.length > 50) {
      return { valid: false, error: 'Branch name must be 50 characters or less' };
    }

    if (!/^[a-zA-Z0-9/_-]+$/.test(name)) {
      return { valid: false, error: 'Branch name can only contain letters, numbers, /, _, and -' };
    }

    if (name.startsWith('/') || name.endsWith('/')) {
      return { valid: false, error: 'Branch name cannot start or end with /' };
    }

    return { valid: true };
  }

  /**
   * Validate commit message
   */
  validateCommitMessage(message: string): { valid: boolean; error?: string } {
    if (!message || message.trim().length === 0) {
      return { valid: false, error: 'Commit message is required' };
    }

    if (message.length > 200) {
      return { valid: false, error: 'Commit message must be 200 characters or less' };
    }

    return { valid: true };
  }
}

// Export singleton instance
export const interactiveContentVersionControlService = new InteractiveContentVersionControlService();
export default interactiveContentVersionControlService;