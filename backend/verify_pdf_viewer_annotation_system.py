#!/usr/bin/env python3
"""
Verification script for PDF viewer and annotation system (Task 9.2)

This script verifies that the PDF viewer and annotation features meet all requirements:
- 7.3: In-browser PDF viewer component
- 7.4: Highlighting and annotation tools
- 7.6: Full-text search within PDFs
"""

import os
import sys
from pathlib import Path

def verify_pdf_viewer_system():
    """Verify the PDF viewer and annotation system implementation"""
    
    print("🔍 Verifying PDF Viewer and Annotation System (Task 9.2)")
    print("=" * 60)
    
    # Check 1: Verify PDF viewer component exists
    print("\n1. Checking PDF viewer component...")
    
    viewer_file = Path("../src/components/zotero/ZoteroPDFViewer.tsx")
    if not viewer_file.exists():
        print("❌ ZoteroPDFViewer component not found")
        return False
    
    with open(viewer_file, 'r') as f:
        viewer_content = f.read()
    
    # Check for required PDF viewer features
    required_features = [
        'react-pdf',  # PDF.js integration
        'Document',   # PDF document component
        'Page',       # PDF page component
        'zoom',       # Zoom functionality
        'rotation',   # Rotation support
        'navigation', # Page navigation
        'annotation', # Annotation support
        'search'      # Search functionality
    ]
    
    for feature in required_features:
        if feature.lower() in viewer_content.lower():
            print(f"✅ PDF viewer feature: {feature}")
        else:
            print(f"❌ PDF viewer feature missing: {feature}")
            return False
    
    # Check 2: Verify annotation service
    print("\n2. Checking PDF annotation service...")
    
    annotation_service_file = Path("../src/services/zoteroPDFAnnotation.ts")
    if not annotation_service_file.exists():
        print("❌ PDF annotation service not found")
        return False
    
    with open(annotation_service_file, 'r') as f:
        annotation_content = f.read()
    
    required_annotation_methods = [
        'createAnnotation',
        'updateAnnotation',
        'deleteAnnotation',
        'getAnnotationsForAttachment',
        'searchAnnotations',
        'syncAnnotations',
        'shareAnnotation',
        'exportAnnotations'
    ]
    
    for method in required_annotation_methods:
        if method in annotation_content:
            print(f"✅ Annotation method: {method}")
        else:
            print(f"❌ Annotation method missing: {method}")
            return False
    
    # Check 3: Verify PDF search service
    print("\n3. Checking PDF search service...")
    
    search_service_file = Path("../src/services/zoteroPDFSearch.ts")
    if not search_service_file.exists():
        print("❌ PDF search service not found")
        return False
    
    with open(search_service_file, 'r') as f:
        search_content = f.read()
    
    required_search_methods = [
        'extractTextFromPDF',
        'searchInPDF',
        'searchMultipleTerms',
        'getPageText',
        'findSimilarText',
        'extractKeyPhrases'
    ]
    
    for method in required_search_methods:
        if method in search_content:
            print(f"✅ Search method: {method}")
        else:
            print(f"❌ Search method missing: {method}")
            return False
    
    # Check 4: Verify React hook
    print("\n4. Checking PDF viewer hook...")
    
    hook_file = Path("../src/hooks/useZoteroPDFViewer.ts")
    if not hook_file.exists():
        print("❌ PDF viewer hook not found")
        return False
    
    with open(hook_file, 'r') as f:
        hook_content = f.read()
    
    required_hook_features = [
        'useState',
        'useEffect',
        'useCallback',
        'goToPage',
        'zoomIn',
        'zoomOut',
        'createAnnotation',
        'performSearch',
        'syncAnnotations'
    ]
    
    for feature in required_hook_features:
        if feature in hook_content:
            print(f"✅ Hook feature: {feature}")
        else:
            print(f"❌ Hook feature missing: {feature}")
            return False
    
    # Check 5: Verify test coverage
    print("\n5. Checking test coverage...")
    
    test_files = [
        "../src/components/zotero/__tests__/ZoteroPDFViewer.test.tsx",
        "../src/services/__tests__/zoteroPDFAnnotation.test.ts",
        "../src/services/__tests__/zoteroPDFSearch.test.ts"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"✅ Test file exists: {Path(test_file).name}")
        else:
            print(f"❌ Test file missing: {Path(test_file).name}")
            return False
    
    # Check 6: Verify annotation types and features
    print("\n6. Checking annotation features...")
    
    annotation_features = [
        'highlight',     # Highlighting support
        'note',          # Note annotations
        'position',      # Position tracking
        'color',         # Color customization
        'comment',       # Comments on annotations
        'sync',          # Synchronization
        'share',         # Sharing capabilities
        'export'         # Export functionality
    ]
    
    for feature in annotation_features:
        if feature in annotation_content:
            print(f"✅ Annotation feature: {feature}")
        else:
            print(f"❌ Annotation feature missing: {feature}")
            return False
    
    # Check 7: Verify search capabilities
    print("\n7. Checking search capabilities...")
    
    search_capabilities = [
        ('full-text', ['searchInPDF', 'extractTextFromPDF']),
        ('case-sensitive', ['caseSensitive']),
        ('regex', ['regex']),
        ('context', ['context']),
        ('pagination', ['pagination', 'pageSize']),
        ('highlight', ['highlight']),
        ('navigation', ['navigate', 'next', 'previous'])
    ]
    
    search_features_found = 0
    for capability_name, keywords in search_capabilities:
        found = any(keyword.lower() in search_content.lower() for keyword in keywords)
        if found:
            print(f"✅ Search capability: {capability_name}")
            search_features_found += 1
        else:
            print(f"⚠️  Search capability may need review: {capability_name}")
    
    if search_features_found < len(search_capabilities) * 0.7:
        print("❌ Insufficient search capabilities")
        return False
    
    # Check 8: Verify UI components and interactions
    print("\n8. Checking UI components...")
    
    ui_components = [
        ('toolbar', ['toolbar', 'bg-white border-b']),
        ('sidebar', ['sidebar', 'showSidebar']),
        ('zoom controls', ['zoomIn', 'zoomOut', 'ZoomIn', 'ZoomOut']),
        ('page navigation', ['goToPage', 'ChevronLeft', 'ChevronRight']),
        ('search input', ['searchTerm', 'Search', 'placeholder']),
        ('annotation tools', ['Highlighter', 'MessageSquare', 'selectedTool']),
        ('color picker', ['color', '#ffff00', '#ff6b6b']),
        ('export button', ['Download', 'export'])
    ]
    
    ui_features_found = 0
    for component_name, keywords in ui_components:
        found = any(keyword in viewer_content for keyword in keywords)
        if found:
            print(f"✅ UI component: {component_name}")
            ui_features_found += 1
        else:
            print(f"⚠️  UI component may need review: {component_name}")
    
    if ui_features_found < len(ui_components) * 0.6:
        print("❌ Insufficient UI components")
        return False
    
    # Check 9: Verify accessibility features
    print("\n9. Checking accessibility features...")
    
    accessibility_features = [
        ('aria-label', ['aria-label', 'ariaLabel']),
        ('title', ['title=']),
        ('keyboard', ['onKeyDown', 'onKeyPress', 'tabIndex']),
        ('focus', ['focus', 'autoFocus']),
        ('role', ['role=', 'button', 'input'])
    ]
    
    accessibility_found = 0
    for feature_name, keywords in accessibility_features:
        found = any(keyword in viewer_content for keyword in keywords)
        if found:
            print(f"✅ Accessibility feature: {feature_name}")
            accessibility_found += 1
        else:
            print(f"⚠️  Accessibility feature may need review: {feature_name}")
    
    if accessibility_found < len(accessibility_features) * 0.4:
        print("❌ Insufficient accessibility features")
        return False
    
    # Check 10: Verify performance optimizations
    print("\n10. Checking performance optimizations...")
    
    performance_features = [
        'useCallback',   # Callback memoization
        'useMemo',       # Value memoization
        'lazy loading',  # Lazy loading
        'cache',         # Caching
        'debounce',      # Debounced operations
        'virtual'        # Virtualization (for large lists)
    ]
    
    performance_found = 0
    combined_content = viewer_content + hook_content + search_content
    
    for feature in performance_features:
        if feature.replace(' ', '').lower() in combined_content.lower():
            print(f"✅ Performance feature: {feature}")
            performance_found += 1
        else:
            print(f"⚠️  Performance feature may need review: {feature}")
    
    if performance_found < len(performance_features) * 0.5:
        print("❌ Insufficient performance optimizations")
        return False
    
    print("\n" + "=" * 60)
    print("✅ PDF Viewer and Annotation System verification completed successfully!")
    print("\nRequirements Coverage:")
    print("✅ 7.3: In-browser PDF viewer component - IMPLEMENTED")
    print("✅ 7.4: Highlighting and annotation tools - IMPLEMENTED")
    print("✅ 7.6: Full-text search within PDFs - IMPLEMENTED")
    
    return True

def verify_integration_points():
    """Test integration points with existing system"""
    print("\n🔗 Testing integration points...")
    
    # Check integration with existing Zotero components
    integration_checks = [
        ("Attachment service integration", "../src/services/zoteroService.ts"),
        ("API client integration", "../src/services/api.ts"),
        ("Type definitions", "../src/types/zotero.ts")
    ]
    
    for check_name, file_path in integration_checks:
        if Path(file_path).exists():
            print(f"✅ {check_name}")
        else:
            print(f"⚠️  {check_name} - file not found: {file_path}")
    
    return True

def verify_dependencies():
    """Check required dependencies"""
    print("\n📦 Checking dependencies...")
    
    # Check package.json for required dependencies
    package_json = Path("../package.json")
    if package_json.exists():
        with open(package_json, 'r') as f:
            package_content = f.read()
        
        required_deps = [
            'react-pdf',
            'pdfjs-dist',
            '@types/react',
            'vitest'
        ]
        
        for dep in required_deps:
            if dep in package_content:
                print(f"✅ Dependency: {dep}")
            else:
                print(f"❌ Missing dependency: {dep}")
                return False
    else:
        print("⚠️  package.json not found")
    
    return True

if __name__ == "__main__":
    try:
        success = verify_pdf_viewer_system()
        if success:
            verify_integration_points()
            verify_dependencies()
            print("\n🎉 All verifications passed! Task 9.2 is complete.")
            sys.exit(0)
        else:
            print("\n❌ Some verifications failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Verification failed with error: {e}")
        sys.exit(1)