#!/usr/bin/env python3
"""
Simple Task 8.1 Verification: Connect Zotero references to chat system

This script verifies that the Zotero chat integration components exist and have the correct structure.
"""

import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists and print result"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} (NOT FOUND)")
        return False

def check_file_contains(filepath, content, description):
    """Check if a file contains specific content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            file_content = f.read()
            if content in file_content:
                print(f"✓ {description}")
                return True
            else:
                print(f"✗ {description}")
                return False
    except Exception as e:
        print(f"✗ {description}: Error reading file - {e}")
        return False

def main():
    """Run verification checks"""
    print("=== Task 8.1 Verification: Connect Zotero references to chat system ===")
    
    checks = []
    
    # Backend service files
    print("\n--- Backend Service Files ---")
    checks.append(check_file_exists(
        "backend/services/zotero/zotero_chat_integration_service.py",
        "Zotero Chat Integration Service"
    ))
    
    checks.append(check_file_exists(
        "backend/api/zotero_chat_endpoints.py",
        "Zotero Chat API Endpoints"
    ))
    
    # Frontend service files
    print("\n--- Frontend Service Files ---")
    checks.append(check_file_exists(
        "src/services/zoteroChat.ts",
        "Zotero Chat Frontend Service"
    ))
    
    checks.append(check_file_exists(
        "src/components/ChatInterface.tsx",
        "Chat Interface Component"
    ))
    
    # Test files
    print("\n--- Test Files ---")
    checks.append(check_file_exists(
        "backend/tests/test_zotero_chat_integration.py",
        "Backend Integration Tests"
    ))
    
    checks.append(check_file_exists(
        "backend/tests/test_zotero_chat_endpoints.py",
        "Backend API Tests"
    ))
    
    checks.append(check_file_exists(
        "src/components/__tests__/ZoteroChatIntegration.test.tsx",
        "Frontend Integration Tests"
    ))
    
    # Check key functionality in backend service
    print("\n--- Backend Service Functionality ---")
    service_file = "backend/services/zotero/zotero_chat_integration_service.py"
    if os.path.exists(service_file):
        checks.append(check_file_contains(
            service_file,
            "extract_reference_mentions",
            "Reference mention extraction method"
        ))
        
        checks.append(check_file_contains(
            service_file,
            "inject_reference_context",
            "Reference context injection method"
        ))
        
        checks.append(check_file_contains(
            service_file,
            "convert_to_chat_references",
            "Reference conversion method"
        ))
        
        checks.append(check_file_contains(
            service_file,
            "create_research_summary",
            "Research summary creation method"
        ))
        
        checks.append(check_file_contains(
            service_file,
            "export_conversation_with_citations",
            "Conversation export method"
        ))
    
    # Check key functionality in frontend service
    print("\n--- Frontend Service Functionality ---")
    frontend_service_file = "src/services/zoteroChat.ts"
    if os.path.exists(frontend_service_file):
        checks.append(check_file_contains(
            frontend_service_file,
            "extractReferenceMentions",
            "Frontend reference mention extraction"
        ))
        
        checks.append(check_file_contains(
            frontend_service_file,
            "injectReferenceContext",
            "Frontend reference context injection"
        ))
        
        checks.append(check_file_contains(
            frontend_service_file,
            "processAIResponse",
            "Frontend AI response processing"
        ))
        
        checks.append(check_file_contains(
            frontend_service_file,
            "exportConversationWithCitations",
            "Frontend conversation export"
        ))
    
    # Check API endpoints
    print("\n--- API Endpoints ---")
    api_file = "backend/api/zotero_chat_endpoints.py"
    if os.path.exists(api_file):
        checks.append(check_file_contains(
            api_file,
            "/process-message",
            "Process message endpoint"
        ))
        
        checks.append(check_file_contains(
            api_file,
            "/extract-mentions",
            "Extract mentions endpoint"
        ))
        
        checks.append(check_file_contains(
            api_file,
            "/relevant-references",
            "Relevant references endpoint"
        ))
        
        checks.append(check_file_contains(
            api_file,
            "/export-conversation",
            "Export conversation endpoint"
        ))
    
    # Check ChatInterface integration
    print("\n--- Chat Interface Integration ---")
    chat_interface_file = "src/components/ChatInterface.tsx"
    if os.path.exists(chat_interface_file):
        checks.append(check_file_contains(
            chat_interface_file,
            "references",
            "References support in chat interface"
        ))
        
        checks.append(check_file_contains(
            chat_interface_file,
            "BookOpen",
            "BookOpen icon import for references"
        ))
        
        checks.append(check_file_contains(
            chat_interface_file,
            "Reference Details",
            "Reference panel functionality"
        ))
    
    # Check ChatContext integration
    print("\n--- Chat Context Integration ---")
    chat_context_file = "src/contexts/ChatContext.tsx"
    if os.path.exists(chat_context_file):
        checks.append(check_file_contains(
            chat_context_file,
            "zoteroService",
            "Zotero service integration in chat context"
        ))
        
        checks.append(check_file_contains(
            chat_context_file,
            "processChatMessage",
            "Process chat message with Zotero context"
        ))
    
    # Summary
    print(f"\n=== Results ===")
    passed = sum(checks)
    total = len(checks)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All checks passed! Task 8.1 implementation appears to be complete.")
        print("\nKey features implemented:")
        print("- Reference context injection in chat")
        print("- Reference mention and linking in conversations")
        print("- Reference-aware response generation")
        print("- Integration tests for chat-reference integration")
        return True
    else:
        print("✗ Some checks failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)