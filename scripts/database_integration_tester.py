#!/usr/bin/env python3
"""
Database Integration Testing Suite
Ubuntu-specific database configuration and integration testing
"""

import json
import logging
import time
import os
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import psycopg2
import redis
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DatabaseTestResult:
    """Database test result"""
    test_name: str
    database_type: str
    status: str  # 'passed', 'failed', 'skipped'
    duration: float
    message: str
    details: Dict[str, Any]
    ubuntu_specific: bool = False

@dataclass
class DatabaseConfig:
    """Database configuration"""
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_scholar"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # ChromaDB
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    
    # SQLite (for testing)
    sqlite_path: str = "test_integration.db"

class DatabaseIntegrationTester:
    """Database integration testing implementation"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.results: List[DatabaseTestResult] = []
        
    def run_all_tests(self) -> List[DatabaseTestResult]:
        """Run all database integration tests"""
        logger.info("Starting database integration testing")
        
        # Test categories
        test_methods = [
            ("postgresql_connection", self._test_postgresql_connection),
            ("postgresql_operations", self._test_postgresql_operations),
            ("postgresql_ubuntu_config", self._test_postgresql_ubuntu_config),
            ("redis_connection", self._test_redis_connection),
            ("redis_operations", self._test_redis_operations),
            ("redis_ubuntu_config", self._test_redis_ubuntu_config),
            ("chromadb_connection", self._test_chromadb_connection),
            ("chromadb_operations", self._test_chromadb_operations),
            ("database_migrations", self._test_database_migrations),
            ("cross_database_operations", self._test_cross_database_operations),
            ("ubuntu_file_permissions", self._test_ubuntu_file_permissions),
            ("ubuntu_network_config", self._test_ubuntu_network_config)
        ]
        
        for test_name, test_method in test_methods:
            try:
                logger.info(f"Running {test_name} test")
                test_method()
            except Exception as e:
                logger.error(f"Error in {test_name}: {e}")
                self.results.append(DatabaseTestResult(
                    test_name=test_name,
                    database_type="general",
                    status="failed",
                    duration=0.0,
                    message=f"Test execution failed: {str(e)}",
                    details={"error": str(e)}
                ))
        
        return self.results
    
    def _test_postgresql_connection(self):
        """Test PostgreSQL connection"""
        start_time = time.time()
        test_name = "postgresql_connection"
        
        try:
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database();")
            current_db = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="postgresql",
                status="passed",
                duration=duration,
                message="PostgreSQL connection successful",
                details={
                    "version": version,
                    "database": current_db,
                    "host": self.config.postgres_host,
                    "port": self.config.postgres_port
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="postgresql",
                status="failed",
                duration=duration,
                message=f"PostgreSQL connection failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def _test_postgresql_operations(self):
        """Test PostgreSQL CRUD operations"""
        start_time = time.time()
        test_name = "postgresql_operations"
        
        try:
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password
            )
            
            cursor = conn.cursor()
            
            # Create test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS integration_test (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test data
            cursor.execute(
                "INSERT INTO integration_test (name) VALUES (%s) RETURNING id",
                ("test_record",)
            )
            test_id = cursor.fetchone()[0]
            
            # Read test data
            cursor.execute("SELECT * FROM integration_test WHERE id = %s", (test_id,))
            record = cursor.fetchone()
            
            # Update test data
            cursor.execute(
                "UPDATE integration_test SET name = %s WHERE id = %s",
                ("updated_record", test_id)
            )
            
            # Verify update
            cursor.execute("SELECT name FROM integration_test WHERE id = %s", (test_id,))
            updated_name = cursor.fetchone()[0]
            
            # Delete test data
            cursor.execute("DELETE FROM integration_test WHERE id = %s", (test_id,))
            
            # Clean up
            cursor.execute("DROP TABLE integration_test")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="postgresql",
                status="passed",
                duration=duration,
                message="PostgreSQL CRUD operations successful",
                details={
                    "operations_tested": ["CREATE", "INSERT", "SELECT", "UPDATE", "DELETE"],
                    "test_record_id": test_id,
                    "updated_name": updated_name
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="postgresql",
                status="failed",
                duration=duration,
                message=f"PostgreSQL operations failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_postgresql_ubuntu_config(self):
        """Test PostgreSQL Ubuntu-specific configurations"""
        start_time = time.time()
        test_name = "postgresql_ubuntu_config"
        
        try:
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password
            )
            
            cursor = conn.cursor()
            
            # Check Ubuntu-specific settings
            ubuntu_checks = {
                "data_directory": "SHOW data_directory;",
                "config_file": "SHOW config_file;",
                "hba_file": "SHOW hba_file;",
                "listen_addresses": "SHOW listen_addresses;",
                "port": "SHOW port;",
                "max_connections": "SHOW max_connections;",
                "shared_buffers": "SHOW shared_buffers;",
                "timezone": "SHOW timezone;"
            }
            
            config_details = {}
            for setting, query in ubuntu_checks.items():
                try:
                    cursor.execute(query)
                    value = cursor.fetchone()[0]
                    config_details[setting] = value
                except Exception as e:
                    config_details[setting] = f"Error: {str(e)}"
            
            # Check file permissions (Ubuntu-specific)
            file_permissions = {}
            if config_details.get("data_directory"):
                try:
                    data_dir = config_details["data_directory"]
                    if os.path.exists(data_dir):
                        stat_info = os.stat(data_dir)
                        file_permissions["data_directory"] = oct(stat_info.st_mode)[-3:]
                except Exception as e:
                    file_permissions["data_directory"] = f"Error: {str(e)}"
            
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="postgresql",
                status="passed",
                duration=duration,
                message="PostgreSQL Ubuntu configuration check completed",
                details={
                    "config_settings": config_details,
                    "file_permissions": file_permissions
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="postgresql",
                status="failed",
                duration=duration,
                message=f"PostgreSQL Ubuntu config check failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def _test_redis_connection(self):
        """Test Redis connection"""
        start_time = time.time()
        test_name = "redis_connection"
        
        try:
            r = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                socket_connect_timeout=10
            )
            
            # Test connection
            r.ping()
            
            # Get Redis info
            info = r.info()
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="redis",
                status="passed",
                duration=duration,
                message="Redis connection successful",
                details={
                    "redis_version": info.get("redis_version"),
                    "os": info.get("os"),
                    "arch_bits": info.get("arch_bits"),
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients")
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="redis",
                status="failed",
                duration=duration,
                message=f"Redis connection failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def _test_redis_operations(self):
        """Test Redis operations"""
        start_time = time.time()
        test_name = "redis_operations"
        
        try:
            r = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db
            )
            
            test_key = "integration_test_key"
            test_value = "integration_test_value"
            
            # String operations
            r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved_value = r.get(test_key).decode('utf-8')
            
            if retrieved_value != test_value:
                raise Exception(f"Value mismatch: expected {test_value}, got {retrieved_value}")
            
            # Hash operations
            hash_key = "integration_test_hash"
            r.hset(hash_key, "field1", "value1")
            r.hset(hash_key, "field2", "value2")
            hash_values = r.hgetall(hash_key)
            
            # List operations
            list_key = "integration_test_list"
            r.lpush(list_key, "item1", "item2", "item3")
            list_length = r.llen(list_key)
            
            # Set operations
            set_key = "integration_test_set"
            r.sadd(set_key, "member1", "member2", "member3")
            set_size = r.scard(set_key)
            
            # Clean up
            r.delete(test_key, hash_key, list_key, set_key)
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="redis",
                status="passed",
                duration=duration,
                message="Redis operations successful",
                details={
                    "string_operation": "passed",
                    "hash_fields": len(hash_values),
                    "list_length": list_length,
                    "set_size": set_size
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="redis",
                status="failed",
                duration=duration,
                message=f"Redis operations failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_redis_ubuntu_config(self):
        """Test Redis Ubuntu-specific configurations"""
        start_time = time.time()
        test_name = "redis_ubuntu_config"
        
        try:
            r = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db
            )
            
            # Get Redis configuration
            config = r.config_get()
            
            # Ubuntu-specific checks
            ubuntu_relevant_configs = {
                "dir": config.get("dir"),
                "dbfilename": config.get("dbfilename"),
                "logfile": config.get("logfile"),
                "pidfile": config.get("pidfile"),
                "bind": config.get("bind"),
                "port": config.get("port"),
                "tcp-backlog": config.get("tcp-backlog"),
                "timeout": config.get("timeout"),
                "maxmemory": config.get("maxmemory"),
                "maxmemory-policy": config.get("maxmemory-policy")
            }
            
            # Check file permissions for data directory
            file_permissions = {}
            data_dir = config.get("dir")
            if data_dir and os.path.exists(data_dir):
                try:
                    stat_info = os.stat(data_dir)
                    file_permissions["data_directory"] = oct(stat_info.st_mode)[-3:]
                except Exception as e:
                    file_permissions["data_directory"] = f"Error: {str(e)}"
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="redis",
                status="passed",
                duration=duration,
                message="Redis Ubuntu configuration check completed",
                details={
                    "config_settings": ubuntu_relevant_configs,
                    "file_permissions": file_permissions
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="redis",
                status="failed",
                duration=duration,
                message=f"Redis Ubuntu config check failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def _test_chromadb_connection(self):
        """Test ChromaDB connection"""
        start_time = time.time()
        test_name = "chromadb_connection"
        
        try:
            import requests
            
            # Test ChromaDB health endpoint
            response = requests.get(
                f"http://{self.config.chromadb_host}:{self.config.chromadb_port}/api/v1/heartbeat",
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"ChromaDB health check failed: {response.status_code}")
            
            # Test version endpoint
            version_response = requests.get(
                f"http://{self.config.chromadb_host}:{self.config.chromadb_port}/api/v1/version",
                timeout=10
            )
            
            version_info = {}
            if version_response.status_code == 200:
                version_info = version_response.json()
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="chromadb",
                status="passed",
                duration=duration,
                message="ChromaDB connection successful",
                details={
                    "host": self.config.chromadb_host,
                    "port": self.config.chromadb_port,
                    "version_info": version_info
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="chromadb",
                status="failed",
                duration=duration,
                message=f"ChromaDB connection failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def _test_chromadb_operations(self):
        """Test ChromaDB operations"""
        start_time = time.time()
        test_name = "chromadb_operations"
        
        try:
            import chromadb
            
            # Connect to ChromaDB
            client = chromadb.HttpClient(
                host=self.config.chromadb_host,
                port=self.config.chromadb_port
            )
            
            # Create test collection
            collection_name = "integration_test_collection"
            try:
                client.delete_collection(collection_name)
            except:
                pass  # Collection might not exist
            
            collection = client.create_collection(collection_name)
            
            # Add test documents
            test_documents = [
                "This is a test document for integration testing.",
                "Another test document with different content.",
                "Third document for comprehensive testing."
            ]
            
            test_ids = ["test_doc_1", "test_doc_2", "test_doc_3"]
            test_metadatas = [
                {"source": "test", "type": "integration"},
                {"source": "test", "type": "validation"},
                {"source": "test", "type": "verification"}
            ]
            
            collection.add(
                documents=test_documents,
                ids=test_ids,
                metadatas=test_metadatas
            )
            
            # Query the collection
            query_results = collection.query(
                query_texts=["test document"],
                n_results=2
            )
            
            # Verify results
            if not query_results["documents"] or len(query_results["documents"][0]) == 0:
                raise Exception("No query results returned")
            
            # Clean up
            client.delete_collection(collection_name)
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="chromadb",
                status="passed",
                duration=duration,
                message="ChromaDB operations successful",
                details={
                    "documents_added": len(test_documents),
                    "query_results": len(query_results["documents"][0]),
                    "collection_created": collection_name
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="chromadb",
                status="failed",
                duration=duration,
                message=f"ChromaDB operations failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_database_migrations(self):
        """Test database migration and schema validation"""
        start_time = time.time()
        test_name = "database_migrations"
        
        try:
            # Test with SQLite for migration simulation
            conn = sqlite3.connect(self.config.sqlite_path)
            cursor = conn.cursor()
            
            # Simulate migration steps
            migrations = [
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE documents (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    filename TEXT NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
                """,
                """
                ALTER TABLE users ADD COLUMN name TEXT
                """,
                """
                CREATE INDEX idx_documents_user_id ON documents(user_id)
                """
            ]
            
            # Execute migrations
            for i, migration in enumerate(migrations):
                cursor.execute(migration)
                conn.commit()
            
            # Verify schema
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [row[1] for row in cursor.fetchall()]
            
            cursor.execute("PRAGMA table_info(documents)")
            doc_columns = [row[1] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            # Clean up
            if os.path.exists(self.config.sqlite_path):
                os.remove(self.config.sqlite_path)
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="sqlite",
                status="passed",
                duration=duration,
                message="Database migrations successful",
                details={
                    "migrations_executed": len(migrations),
                    "tables_created": tables,
                    "user_columns": user_columns,
                    "document_columns": doc_columns
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="sqlite",
                status="failed",
                duration=duration,
                message=f"Database migrations failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def _test_cross_database_operations(self):
        """Test operations across multiple databases"""
        start_time = time.time()
        test_name = "cross_database_operations"
        
        try:
            # Test data consistency across PostgreSQL and Redis
            
            # PostgreSQL operation
            pg_conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password
            )
            
            pg_cursor = pg_conn.cursor()
            
            # Create test table
            pg_cursor.execute("""
                CREATE TABLE IF NOT EXISTS cross_db_test (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert data
            pg_cursor.execute(
                "INSERT INTO cross_db_test (data) VALUES (%s) RETURNING id",
                ("cross_database_test_data",)
            )
            test_id = pg_cursor.fetchone()[0]
            pg_conn.commit()
            
            # Redis operation - cache the data
            r = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db
            )
            
            cache_key = f"cross_db_test:{test_id}"
            r.set(cache_key, "cross_database_test_data", ex=300)
            
            # Verify data consistency
            pg_cursor.execute("SELECT data FROM cross_db_test WHERE id = %s", (test_id,))
            pg_data = pg_cursor.fetchone()[0]
            
            redis_data = r.get(cache_key).decode('utf-8')
            
            if pg_data != redis_data:
                raise Exception(f"Data inconsistency: PG={pg_data}, Redis={redis_data}")
            
            # Clean up
            pg_cursor.execute("DELETE FROM cross_db_test WHERE id = %s", (test_id,))
            pg_cursor.execute("DROP TABLE cross_db_test")
            pg_conn.commit()
            pg_cursor.close()
            pg_conn.close()
            
            r.delete(cache_key)
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="multi",
                status="passed",
                duration=duration,
                message="Cross-database operations successful",
                details={
                    "postgresql_data": pg_data,
                    "redis_data": redis_data,
                    "data_consistent": True,
                    "test_id": test_id
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="multi",
                status="failed",
                duration=duration,
                message=f"Cross-database operations failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_ubuntu_file_permissions(self):
        """Test Ubuntu-specific file permissions"""
        start_time = time.time()
        test_name = "ubuntu_file_permissions"
        
        try:
            # Test file creation and permissions
            test_file = "integration_test_permissions.txt"
            
            # Create test file
            with open(test_file, 'w') as f:
                f.write("Test file for permission checking")
            
            # Check initial permissions
            stat_info = os.stat(test_file)
            initial_permissions = oct(stat_info.st_mode)[-3:]
            
            # Change permissions (Ubuntu-specific)
            os.chmod(test_file, 0o644)
            
            # Verify permissions changed
            stat_info = os.stat(test_file)
            new_permissions = oct(stat_info.st_mode)[-3:]
            
            # Test directory permissions
            test_dir = "integration_test_dir"
            os.makedirs(test_dir, exist_ok=True)
            os.chmod(test_dir, 0o755)
            
            dir_stat = os.stat(test_dir)
            dir_permissions = oct(dir_stat.st_mode)[-3:]
            
            # Clean up
            os.remove(test_file)
            os.rmdir(test_dir)
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="filesystem",
                status="passed",
                duration=duration,
                message="Ubuntu file permissions test successful",
                details={
                    "initial_file_permissions": initial_permissions,
                    "modified_file_permissions": new_permissions,
                    "directory_permissions": dir_permissions,
                    "permission_change_successful": new_permissions == "644"
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="filesystem",
                status="failed",
                duration=duration,
                message=f"Ubuntu file permissions test failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def _test_ubuntu_network_config(self):
        """Test Ubuntu-specific network configurations"""
        start_time = time.time()
        test_name = "ubuntu_network_config"
        
        try:
            network_tests = {}
            
            # Test localhost resolution
            import socket
            try:
                socket.gethostbyname('localhost')
                network_tests["localhost_resolution"] = "passed"
            except Exception as e:
                network_tests["localhost_resolution"] = f"failed: {str(e)}"
            
            # Test port availability
            test_ports = [5432, 6379, 8000, 3000]
            port_status = {}
            
            for port in test_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                port_status[port] = "open" if result == 0 else "closed"
                sock.close()
            
            # Test network interface information
            try:
                result = subprocess.run(['ip', 'addr', 'show'], 
                                      capture_output=True, text=True, timeout=10)
                network_interfaces = result.stdout if result.returncode == 0 else "unavailable"
            except Exception:
                network_interfaces = "unavailable"
            
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="network",
                status="passed",
                duration=duration,
                message="Ubuntu network configuration test completed",
                details={
                    "network_tests": network_tests,
                    "port_status": port_status,
                    "interfaces_available": network_interfaces != "unavailable"
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(DatabaseTestResult(
                test_name=test_name,
                database_type="network",
                status="failed",
                duration=duration,
                message=f"Ubuntu network config test failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate database integration test report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "passed"])
        failed_tests = len([r for r in self.results if r.status == "failed"])
        skipped_tests = len([r for r in self.results if r.status == "skipped"])
        ubuntu_specific_tests = len([r for r in self.results if r.ubuntu_specific])
        
        # Group by database type
        by_database = {}
        for result in self.results:
            db_type = result.database_type
            if db_type not in by_database:
                by_database[db_type] = []
            by_database[db_type].append(asdict(result))
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "ubuntu_specific": ubuntu_specific_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "databases_tested": list(by_database.keys())
            },
            "results_by_database": by_database,
            "failed_tests": [
                asdict(result) for result in self.results 
                if result.status == "failed"
            ],
            "configuration": asdict(self.config)
        }
        
        return report

def main():
    """Main function for database integration testing"""
    tester = DatabaseIntegrationTester()
    results = tester.run_all_tests()
    report = tester.generate_report()
    
    # Save report
    os.makedirs("integration_test_results", exist_ok=True)
    with open("integration_test_results/database_integration_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\nDATABASE INTEGRATION TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Skipped: {report['summary']['skipped']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Ubuntu-specific tests: {report['summary']['ubuntu_specific']}")
    print(f"Databases tested: {', '.join(report['summary']['databases_tested'])}")
    
    return report['summary']['failed'] == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)