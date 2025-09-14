#!/usr/bin/env python3
"""
Simple test to verify ChromaDB connection
"""

import chromadb

def test_chromadb_connection():
    """Test ChromaDB connection with different configurations"""
    
    print("🧪 Testing ChromaDB Connection")
    print("=" * 40)
    
    # Test configurations
    configs = [
        {"host": "localhost", "port": 8082},
        {"host": "127.0.0.1", "port": 8082},
        {"host": "chromadb", "port": 8000},
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n{i}. Testing {config['host']}:{config['port']}")
        try:
            client = chromadb.HttpClient(
                host=config['host'],
                port=config['port']
            )
            
            # Test heartbeat
            client.heartbeat()
            print(f"   ✅ Connection successful!")
            
            # Test basic operations
            collections = client.list_collections()
            print(f"   📋 Collections: {len(collections)}")
            
            return client, config
            
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
    
    print("\n❌ All connection attempts failed")
    return None, None

if __name__ == "__main__":
    client, config = test_chromadb_connection()
    
    if client:
        print(f"\n🎉 ChromaDB is accessible at {config['host']}:{config['port']}")
        print("You can now run the RAG services with this configuration.")
    else:
        print("\n💡 Suggestions:")
        print("1. Check if ChromaDB container is running: docker ps")
        print("2. Check ChromaDB logs: docker logs advanced-rag-chromadb")
        print("3. Verify port mapping in docker-compose.yml")