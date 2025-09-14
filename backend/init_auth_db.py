#!/usr/bin/env python3
"""
Initialize authentication database and create admin user
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth.database import init_auth_db, create_admin_user

def main():
    """Initialize authentication database"""
    print("🚀 Initializing Reddit AEO Authentication Database...")
    
    try:
        # Initialize database tables
        print("📊 Creating database tables...")
        init_auth_db()
        print("✅ Database tables created successfully!")
        
        # Create admin user
        print("👤 Creating admin user...")
        admin_data = create_admin_user()
        
        if admin_data:
            print("\n" + "="*50)
            print("🎉 AUTHENTICATION SYSTEM READY!")
            print("="*50)
            print("📧 Admin Email: account@cmejo.com")
            print("🔑 Admin Password: Admin123!")
            print("👤 Admin Name: Christopher Mejo")
            print("👤 Admin Role: admin")
            print("="*50)
            print("\n💡 You can now:")
            print("   • Login to the frontend with these credentials")
            print("   • Access all features including analytics")
            print("   • Create additional users")
            print("   • Manage user roles and permissions")
        else:
            print("ℹ️  Admin user already exists - system ready!")
        
        print("\n🌐 Frontend URL: http://localhost:3002")
        print("🔗 API Documentation: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Error initializing authentication database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()