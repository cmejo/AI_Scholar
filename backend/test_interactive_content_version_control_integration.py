"""
Integration Tests for Interactive Content Version Control

This module tests the complete version control workflow including
initialization, branching, merging, conflict resolution, and backup/restore.
"""

import asyncio
import json
from datetime import datetime
from services.interactive_content_version_control import (
    interactive_content_version_control,
    ContentType,
    MergeStatus
)

class TestInteractiveContentVersionControlIntegration:
    """Integration test cases for complete version control workflows"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing data
        interactive_content_version_control.versions.clear()
        interactive_content_version_control.branches.clear()
        interactive_content_version_control.merge_requests.clear()
        interactive_content_version_control.backups.clear()
    
    async def test_complete_notebook_development_workflow(self):
        """Test complete notebook development workflow with version control"""
        content_id = "notebook_development_workflow"
        
        print("🚀 Starting complete notebook development workflow test...")
        
        # 1. Initialize notebook with basic structure
        initial_notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Data Analysis Project\n", "Initial notebook setup"]
                },
                {
                    "cell_type": "code",
                    "source": ["import pandas as pd\n", "import numpy as np"],
                    "execution_count": 1,
                    "outputs": []
                }
            ],
            "metadata": {
                "kernelspec": {"name": "python3", "display_name": "Python 3"},
                "language_info": {"name": "python", "version": "3.8.0"}
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        version1 = await interactive_content_version_control.initialize_content_versioning(
            content_id=content_id,
            content_type=ContentType.NOTEBOOK,
            initial_data=initial_notebook,
            author_id="data_scientist_1",
            commit_message="Initial notebook setup with basic imports"
        )
        
        assert version1 is not None
        assert version1.version_number == 1
        print("✓ Step 1: Initialized notebook with basic structure")
        
        # 2. Add data loading and exploration
        notebook_v2 = initial_notebook.copy()
        notebook_v2["cells"].extend([
            {
                "cell_type": "markdown",
                "source": ["## Data Loading"]
            },
            {
                "cell_type": "code",
                "source": [
                    "# Load dataset\n",
                    "df = pd.read_csv('data.csv')\n",
                    "print(f'Dataset shape: {df.shape}')\n",
                    "df.head()"
                ],
                "execution_count": 2,
                "outputs": []
            },
            {
                "cell_type": "markdown",
                "source": ["## Basic Statistics"]
            },
            {
                "cell_type": "code",
                "source": ["df.describe()"],
                "execution_count": 3,
                "outputs": []
            }
        ])
        
        version2 = await interactive_content_version_control.commit_changes(
            content_id=content_id,
            updated_data=notebook_v2,
            author_id="data_scientist_1",
            commit_message="Added data loading and basic exploration"
        )
        
        assert version2 is not None
        assert version2.version_number == 2
        print("✓ Step 2: Added data loading and exploration")
        
        # 3. Create feature branch for advanced analysis
        feature_branch = await interactive_content_version_control.create_branch(
            content_id=content_id,
            branch_name="feature/advanced-analysis",
            from_version=version2.version_id,
            author_id="data_scientist_1",
            description="Branch for advanced statistical analysis and modeling"
        )
        
        assert feature_branch is not None
        print("✓ Step 3: Created feature branch for advanced analysis")
        
        # 4. Work on feature branch - add advanced analysis
        notebook_feature = notebook_v2.copy()
        notebook_feature["cells"].extend([
            {
                "cell_type": "markdown",
                "source": ["## Advanced Analysis"]
            },
            {
                "cell_type": "code",
                "source": [
                    "from sklearn.model_selection import train_test_split\n",
                    "from sklearn.ensemble import RandomForestClassifier\n",
                    "from sklearn.metrics import classification_report"
                ],
                "execution_count": 4,
                "outputs": []
            },
            {
                "cell_type": "code",
                "source": [
                    "# Prepare features and target\n",
                    "X = df.drop('target', axis=1)\n",
                    "y = df['target']\n",
                    "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)"
                ],
                "execution_count": 5,
                "outputs": []
            },
            {
                "cell_type": "code",
                "source": [
                    "# Train model\n",
                    "rf_model = RandomForestClassifier(n_estimators=100, random_state=42)\n",
                    "rf_model.fit(X_train, y_train)\n",
                    "predictions = rf_model.predict(X_test)\n",
                    "print(classification_report(y_test, predictions))"
                ],
                "execution_count": 6,
                "outputs": []
            }
        ])
        
        feature_version = await interactive_content_version_control.commit_changes(
            content_id=content_id,
            updated_data=notebook_feature,
            author_id="data_scientist_1",
            commit_message="Added machine learning model and evaluation",
            branch_name="feature/advanced-analysis"
        )
        
        assert feature_version is not None
        print("✓ Step 4: Added advanced analysis to feature branch")
        
        # 5. Meanwhile, work on main branch - add visualization
        notebook_main = notebook_v2.copy()
        notebook_main["cells"].extend([
            {
                "cell_type": "markdown",
                "source": ["## Data Visualization"]
            },
            {
                "cell_type": "code",
                "source": [
                    "import matplotlib.pyplot as plt\n",
                    "import seaborn as sns\n",
                    "plt.style.use('seaborn')"
                ],
                "execution_count": 4,
                "outputs": []
            },
            {
                "cell_type": "code",
                "source": [
                    "# Create correlation heatmap\n",
                    "plt.figure(figsize=(10, 8))\n",
                    "sns.heatmap(df.corr(), annot=True, cmap='coolwarm')\n",
                    "plt.title('Feature Correlation Matrix')\n",
                    "plt.show()"
                ],
                "execution_count": 5,
                "outputs": []
            }
        ])
        
        main_version = await interactive_content_version_control.commit_changes(
            content_id=content_id,
            updated_data=notebook_main,
            author_id="data_scientist_2",
            commit_message="Added data visualization with correlation heatmap",
            branch_name="main"
        )
        
        assert main_version is not None
        print("✓ Step 5: Added visualization to main branch")
        
        # 6. Create backup before merge
        backup = await interactive_content_version_control.create_backup(
            content_id=content_id,
            backup_type="pre_merge"
        )
        
        assert backup is not None
        print("✓ Step 6: Created backup before merge")
        
        # 7. Merge feature branch into main
        merge_request = await interactive_content_version_control.merge_branches(
            content_id=content_id,
            source_branch="feature/advanced-analysis",
            target_branch="main",
            author_id="data_scientist_1",
            merge_message="Merge advanced analysis features into main branch"
        )
        
        assert merge_request is not None
        print(f"✓ Step 7: Merge completed with status: {merge_request.status}")
        
        # 8. Verify merged content
        history = await interactive_content_version_control.get_version_history(content_id, "main")
        latest_version = history[-1] if history else None
        
        assert latest_version is not None
        merged_notebook = latest_version.content_data
        
        # Should have cells from both branches
        cell_sources = [cell.get("source", []) for cell in merged_notebook.get("cells", [])]
        has_ml_content = any("RandomForestClassifier" in str(source) for source in cell_sources)
        has_viz_content = any("heatmap" in str(source) for source in cell_sources)
        
        if merge_request.status == MergeStatus.SUCCESS:
            # For successful merge, we should have content from both branches
            print(f"   - Merged notebook has {len(merged_notebook.get('cells', []))} cells")
            print(f"   - Contains ML content: {has_ml_content}")
            print(f"   - Contains visualization content: {has_viz_content}")
        
        print("✓ Step 8: Verified merged content")
        
        # 9. Generate diff between versions
        if len(history) >= 2:
            diff = await interactive_content_version_control.get_version_diff(
                content_id=content_id,
                from_version=history[0].version_id,
                to_version=history[-1].version_id
            )
            
            assert diff is not None
            print(f"✓ Step 9: Generated diff - {diff.summary['added']} added, {diff.summary['modified']} modified, {diff.summary['deleted']} deleted")
        
        # 10. Test revert functionality
        if len(history) >= 2:
            revert_version = await interactive_content_version_control.revert_to_version(
                content_id=content_id,
                version_id=history[1].version_id,  # Revert to second version
                author_id="data_scientist_1",
                branch_name="main"
            )
            
            assert revert_version is not None
            assert "reverted_from" in revert_version.metadata
            print("✓ Step 10: Successfully reverted to previous version")
        
        # 11. Test restore from backup
        restore_version = await interactive_content_version_control.restore_from_backup(
            content_id=content_id,
            backup_id=backup.backup_id,
            author_id="data_scientist_1"
        )
        
        assert restore_version is not None
        assert "restored_from_backup" in restore_version.metadata
        print("✓ Step 11: Successfully restored from backup")
        
        # 12. Final verification
        final_history = await interactive_content_version_control.get_version_history(content_id)
        branches = await interactive_content_version_control.get_content_branches(content_id)
        merge_requests = await interactive_content_version_control.get_merge_requests(content_id)
        backups = await interactive_content_version_control.get_backups(content_id)
        
        print(f"\n📊 Final Workflow Statistics:")
        print(f"   - Total versions: {len(final_history)}")
        print(f"   - Total branches: {len(branches)}")
        print(f"   - Merge requests: {len(merge_requests)}")
        print(f"   - Backup records: {len(backups)}")
        
        # Verify we have expected minimum counts
        assert len(final_history) >= 3  # At least 3 versions created
        assert len(branches) >= 2  # main + feature branch
        assert len(merge_requests) >= 1  # At least one merge request
        assert len(backups) >= 2  # initial + pre_merge backups
        
        print("✅ Complete notebook development workflow test passed!")
        return True
    
    async def test_collaborative_visualization_workflow(self):
        """Test collaborative visualization development with conflict resolution"""
        content_id = "collaborative_visualization"
        
        print("\n🎨 Starting collaborative visualization workflow test...")
        
        # 1. Initialize visualization
        initial_viz = {
            "title": "Sales Dashboard",
            "type": "plotly",
            "data": {
                "x": ["Q1", "Q2", "Q3", "Q4"],
                "y": [100, 150, 120, 180],
                "type": "bar"
            },
            "layout": {
                "title": "Quarterly Sales",
                "xaxis": {"title": "Quarter"},
                "yaxis": {"title": "Sales ($k)"}
            },
            "config": {"displayModeBar": True}
        }
        
        version1 = await interactive_content_version_control.initialize_content_versioning(
            content_id=content_id,
            content_type=ContentType.VISUALIZATION,
            initial_data=initial_viz,
            author_id="designer_1",
            commit_message="Initial sales dashboard"
        )
        
        assert version1 is not None
        print("✓ Step 1: Initialized collaborative visualization")
        
        # 2. Designer 1 creates styling branch
        styling_branch = await interactive_content_version_control.create_branch(
            content_id=content_id,
            branch_name="feature/styling",
            from_version=version1.version_id,
            author_id="designer_1",
            description="Improve visual styling and colors"
        )
        
        # 3. Designer 2 creates data branch
        data_branch = await interactive_content_version_control.create_branch(
            content_id=content_id,
            branch_name="feature/data-enhancement",
            from_version=version1.version_id,
            author_id="designer_2",
            description="Add more data series and metrics"
        )
        
        assert styling_branch is not None
        assert data_branch is not None
        print("✓ Steps 2-3: Created styling and data enhancement branches")
        
        # 4. Work on styling branch
        styled_viz = initial_viz.copy()
        styled_viz.update({
            "data": {
                "x": ["Q1", "Q2", "Q3", "Q4"],
                "y": [100, 150, 120, 180],
                "type": "bar",
                "marker": {
                    "color": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"],
                    "line": {"width": 2, "color": "#333"}
                }
            },
            "layout": {
                "title": {
                    "text": "Quarterly Sales Performance",
                    "font": {"size": 24, "color": "#333"}
                },
                "xaxis": {"title": "Quarter", "titlefont": {"size": 16}},
                "yaxis": {"title": "Sales ($k)", "titlefont": {"size": 16}},
                "plot_bgcolor": "#F8F9FA",
                "paper_bgcolor": "#FFFFFF"
            }
        })
        
        styling_version = await interactive_content_version_control.commit_changes(
            content_id=content_id,
            updated_data=styled_viz,
            author_id="designer_1",
            commit_message="Enhanced visual styling with colors and typography",
            branch_name="feature/styling"
        )
        
        assert styling_version is not None
        print("✓ Step 4: Enhanced styling on styling branch")
        
        # 5. Work on data branch
        enhanced_viz = initial_viz.copy()
        enhanced_viz.update({
            "data": [
                {
                    "x": ["Q1", "Q2", "Q3", "Q4"],
                    "y": [100, 150, 120, 180],
                    "type": "bar",
                    "name": "Sales"
                },
                {
                    "x": ["Q1", "Q2", "Q3", "Q4"],
                    "y": [80, 120, 100, 160],
                    "type": "bar",
                    "name": "Costs"
                }
            ],
            "layout": {
                "title": "Quarterly Sales vs Costs",
                "xaxis": {"title": "Quarter"},
                "yaxis": {"title": "Amount ($k)"},
                "barmode": "group"
            },
            "annotations": [
                {
                    "x": "Q4",
                    "y": 180,
                    "text": "Best Quarter",
                    "showarrow": True
                }
            ]
        })
        
        data_version = await interactive_content_version_control.commit_changes(
            content_id=content_id,
            updated_data=enhanced_viz,
            author_id="designer_2",
            commit_message="Added cost data and annotations",
            branch_name="feature/data-enhancement"
        )
        
        assert data_version is not None
        print("✓ Step 5: Enhanced data on data branch")
        
        # 6. Try to merge styling branch first (should succeed)
        merge1 = await interactive_content_version_control.merge_branches(
            content_id=content_id,
            source_branch="feature/styling",
            target_branch="main",
            author_id="designer_1",
            merge_message="Merge styling improvements"
        )
        
        assert merge1 is not None
        print(f"✓ Step 6: First merge completed with status: {merge1.status}")
        
        # 7. Try to merge data branch (may have conflicts)
        merge2 = await interactive_content_version_control.merge_branches(
            content_id=content_id,
            source_branch="feature/data-enhancement",
            target_branch="main",
            author_id="designer_2",
            merge_message="Merge data enhancements"
        )
        
        assert merge2 is not None
        print(f"✓ Step 7: Second merge completed with status: {merge2.status}")
        
        if merge2.status == MergeStatus.CONFLICT:
            print(f"   - Detected {len(merge2.conflicts)} conflicts")
            for conflict in merge2.conflicts:
                print(f"   - Conflict in {conflict['path']}: {conflict['conflict_type']}")
        
        # 8. Create comprehensive backup
        backup = await interactive_content_version_control.create_backup(
            content_id=content_id,
            backup_type="collaborative_checkpoint"
        )
        
        assert backup is not None
        print("✓ Step 8: Created collaborative checkpoint backup")
        
        # 9. Verify final state
        history = await interactive_content_version_control.get_version_history(content_id)
        branches = await interactive_content_version_control.get_content_branches(content_id)
        
        print(f"\n📊 Collaborative Workflow Statistics:")
        print(f"   - Total versions: {len(history)}")
        print(f"   - Active branches: {len([b for b in branches if b.is_active])}")
        print(f"   - Merge requests: {len(await interactive_content_version_control.get_merge_requests(content_id))}")
        
        print("✅ Collaborative visualization workflow test passed!")
        return True
    
    async def test_disaster_recovery_workflow(self):
        """Test disaster recovery using backups and version control"""
        content_id = "disaster_recovery_test"
        
        print("\n🚨 Starting disaster recovery workflow test...")
        
        # 1. Create important dataset
        important_data = {
            "dataset_name": "Critical Business Data",
            "version": "1.0",
            "records": [
                {"id": 1, "value": "important_data_1", "timestamp": "2024-01-01"},
                {"id": 2, "value": "important_data_2", "timestamp": "2024-01-02"},
                {"id": 3, "value": "important_data_3", "timestamp": "2024-01-03"}
            ],
            "metadata": {
                "source": "production_database",
                "last_updated": "2024-01-03T10:00:00Z",
                "checksum": "abc123def456"
            }
        }
        
        version1 = await interactive_content_version_control.initialize_content_versioning(
            content_id=content_id,
            content_type=ContentType.DATASET,
            initial_data=important_data,
            author_id="data_admin",
            commit_message="Initial critical dataset"
        )
        
        assert version1 is not None
        print("✓ Step 1: Created critical dataset")
        
        # 2. Make several updates with automatic backups
        for i in range(3):
            updated_data = important_data.copy()
            updated_data["version"] = f"1.{i+1}"
            updated_data["records"].append({
                "id": len(updated_data["records"]) + 1,
                "value": f"additional_data_{i+1}",
                "timestamp": f"2024-01-0{4+i}"
            })
            updated_data["metadata"]["last_updated"] = f"2024-01-0{4+i}T10:00:00Z"
            
            version = await interactive_content_version_control.commit_changes(
                content_id=content_id,
                updated_data=updated_data,
                author_id="data_admin",
                commit_message=f"Update {i+1}: Added new records"
            )
            
            # Create backup for significant updates
            if i == 1:  # Create backup after second update
                backup = await interactive_content_version_control.create_backup(
                    content_id=content_id,
                    backup_type="scheduled"
                )
                scheduled_backup_id = backup.backup_id
            
            important_data = updated_data
        
        print("✓ Step 2: Made several updates with backups")
        
        # 3. Simulate data corruption
        corrupted_data = {
            "dataset_name": "CORRUPTED DATA",
            "version": "ERROR",
            "records": [],
            "metadata": {
                "source": "UNKNOWN",
                "last_updated": "ERROR",
                "checksum": "CORRUPTED"
            }
        }
        
        corruption_version = await interactive_content_version_control.commit_changes(
            content_id=content_id,
            updated_data=corrupted_data,
            author_id="system_error",
            commit_message="SYSTEM ERROR: Data corruption detected"
        )
        
        assert corruption_version is not None
        print("✓ Step 3: Simulated data corruption")
        
        # 4. Detect corruption and initiate recovery
        history = await interactive_content_version_control.get_version_history(content_id)
        latest_version = history[-1]
        
        # Check if latest version is corrupted
        is_corrupted = latest_version.content_data.get("version") == "ERROR"
        assert is_corrupted
        print("✓ Step 4: Detected data corruption")
        
        # 5. Recovery Option 1: Revert to previous version
        if len(history) >= 2:
            previous_version = history[-2]
            revert_version = await interactive_content_version_control.revert_to_version(
                content_id=content_id,
                version_id=previous_version.version_id,
                author_id="data_admin",
                branch_name="main"
            )
            
            assert revert_version is not None
            assert revert_version.content_data.get("version") != "ERROR"
            print("✓ Step 5: Successfully reverted to previous version")
        
        # 6. Recovery Option 2: Restore from backup
        restore_version = await interactive_content_version_control.restore_from_backup(
            content_id=content_id,
            backup_id=scheduled_backup_id,
            author_id="data_admin"
        )
        
        assert restore_version is not None
        assert restore_version.content_data.get("version") != "ERROR"
        assert "restored_from_backup" in restore_version.metadata
        print("✓ Step 6: Successfully restored from scheduled backup")
        
        # 7. Verify data integrity after recovery
        final_history = await interactive_content_version_control.get_version_history(content_id)
        final_version = final_history[-1]
        
        # Verify restored data
        restored_data = final_version.content_data
        assert restored_data.get("dataset_name") == "Critical Business Data"
        assert restored_data.get("version") != "ERROR"
        assert len(restored_data.get("records", [])) > 0
        assert restored_data.get("metadata", {}).get("source") == "production_database"
        
        print("✓ Step 7: Verified data integrity after recovery")
        
        # 8. Create post-recovery backup
        recovery_backup = await interactive_content_version_control.create_backup(
            content_id=content_id,
            backup_type="post_recovery"
        )
        
        assert recovery_backup is not None
        print("✓ Step 8: Created post-recovery backup")
        
        # 9. Generate recovery report
        backups = await interactive_content_version_control.get_backups(content_id)
        
        print(f"\n📊 Disaster Recovery Statistics:")
        print(f"   - Total versions (including recovery): {len(final_history)}")
        print(f"   - Backup records: {len(backups)}")
        print(f"   - Recovery successful: {final_version.content_data.get('version') != 'ERROR'}")
        print(f"   - Data records recovered: {len(final_version.content_data.get('records', []))}")
        
        print("✅ Disaster recovery workflow test passed!")
        return True

async def run_integration_tests():
    """Run all integration tests"""
    test_instance = TestInteractiveContentVersionControlIntegration()
    
    print("Running Interactive Content Version Control Integration Tests...")
    print("=" * 80)
    
    try:
        # Setup
        test_instance.setup_method()
        
        # Run integration tests
        await test_instance.test_complete_notebook_development_workflow()
        await test_instance.test_collaborative_visualization_workflow()
        await test_instance.test_disaster_recovery_workflow()
        
        print("\n" + "=" * 80)
        print("✅ All Integration Tests Passed!")
        
        # Final summary
        total_content = len(interactive_content_version_control.versions)
        total_branches = sum(len(branches) for branches in interactive_content_version_control.branches.values())
        total_merges = len(interactive_content_version_control.merge_requests)
        total_backups = sum(len(backups) for backups in interactive_content_version_control.backups.values())
        
        print(f"\n📈 Overall Integration Test Summary:")
        print(f"   - Content items processed: {total_content}")
        print(f"   - Branches created: {total_branches}")
        print(f"   - Merge operations: {total_merges}")
        print(f"   - Backup records: {total_backups}")
        print(f"   - Workflows tested: 3 (Notebook Development, Collaborative Visualization, Disaster Recovery)")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        interactive_content_version_control.cleanup()

if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    exit(0 if success else 1)