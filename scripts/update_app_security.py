#!/usr/bin/env python3
"""
Update Backend App with Security Fixes
Updates the main FastAPI app to use enhanced security features.
"""

import re
from pathlib import Path

def update_app_security():
    """Update app.py with security improvements"""
    app_path = Path("backend/app.py")
    
    if not app_path.exists():
        print("❌ backend/app.py not found")
        return
    
    # Create backup
    backup_path = app_path.with_suffix('.py.backup')
    content = app_path.read_text()
    backup_path.write_text(content)
    
    print(f"📁 Created backup: {backup_path}")
    
    # Add security imports at the top
    security_imports = '''from core.config import (
    ALLOWED_FILE_TYPES, MAX_FILE_SIZE_MB, MAX_BATCH_FILES,
    ENABLE_MAGIC_BYTE_VALIDATION
)
from core.exceptions import (
    FileValidationError, DocumentNotFoundError, 
    DocumentProcessingError, AuthenticationError,
    ValidationError, BaseAPIException
)
from utils.file_validation import FileValidator
'''
    
    # Find FastAPI imports and add security imports after
    fastapi_import_pattern = r'(from fastapi import[^\\n]+\\n)'
    if re.search(fastapi_import_pattern, content):
        content = re.sub(
            fastapi_import_pattern,
            r'\\1' + security_imports + '\\n',
            content,
            count=1
        )
        print("✅ Added security imports")
    
    # Replace hardcoded allowed_types with config
    hardcoded_pattern = r"allowed_types = \\['application/pdf'[^\\]]+\\]"
    if re.search(hardcoded_pattern, content):
        content = re.sub(hardcoded_pattern, "allowed_types = ALLOWED_FILE_TYPES", content)
        print("✅ Replaced hardcoded file types with configuration")
    
    # Enhance file validation in upload_document
    old_validation = r'if file\\.content_type not in allowed_types:\\s*raise HTTPException\\(status_code=400, detail="Unsupported file type"\\)'
    new_validation = '''# Enhanced file validation with security checks
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        validation_result = FileValidator.validate_upload_file(
            filename=file.filename or "unknown",
            file_content=file_content,
            declared_mime_type=file.content_type or ""
        )
        
        if not validation_result['is_valid']:
            raise FileValidationError(
                message="; ".join(validation_result['errors']),
                filename=file.filename,
                validation_errors=validation_result['errors']
            )'''
    
    if re.search(old_validation, content):
        content = re.sub(old_validation, new_validation, content)
        print("✅ Enhanced file validation with security checks")
    
    # Improve exception handling in upload_document
    generic_exception = r'except Exception as e:\\s*logger\\.error\\(f"Document upload error: \\{str\\(e\\)\\}"\\)\\s*raise HTTPException\\(status_code=500, detail=f"Document processing failed: \\{str\\(e\\)\\}"\\)'
    specific_exception = '''except FileValidationError:
        raise  # Re-raise validation errors as-is
    except DocumentProcessingError:
        raise  # Re-raise processing errors as-is
    except Exception as e:
        logger.error(f"Unexpected document processing error: {str(e)}")
        raise DocumentProcessingError(
            message="An unexpected error occurred during document processing",
            processing_stage="upload"
        )'''
    
    if re.search(generic_exception, content):
        content = re.sub(generic_exception, specific_exception, content, flags=re.DOTALL)
        print("✅ Improved exception handling with specific error types")
    
    # Add exception handlers for FastAPI
    exception_handlers = '''
# Custom exception handlers
@app.exception_handler(BaseAPIException)
async def base_api_exception_handler(request, exc: BaseAPIException):
    """Handle custom API exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

@app.exception_handler(FileValidationError)
async def file_validation_exception_handler(request, exc: FileValidationError):
    """Handle file validation errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.extra_data
            }
        }
    )
'''
    
    # Add exception handlers before the first route
    first_route_pattern = r'(@app\\.(get|post|put|delete))'
    if re.search(first_route_pattern, content):
        content = re.sub(
            first_route_pattern,
            exception_handlers + '\\n\\1',
            content,
            count=1
        )
        print("✅ Added custom exception handlers")
    
    # Update batch upload with same security improvements
    batch_validation_pattern = r'if file\\.content_type not in allowed_types:\\s*failed_uploads\\.append\\(\\{[^}]+\\}\\)\\s*continue'
    batch_new_validation = '''# Enhanced batch file validation
                try:
                    file_content = await file.read()
                    await file.seek(0)
                    
                    validation_result = FileValidator.validate_upload_file(
                        filename=file.filename or "unknown",
                        file_content=file_content,
                        declared_mime_type=file.content_type or ""
                    )
                    
                    if not validation_result['is_valid']:
                        failed_uploads.append({
                            "filename": file.filename,
                            "error": "; ".join(validation_result['errors']),
                            "validation_details": validation_result['errors']
                        })
                        continue
                        
                except Exception as validation_error:
                    failed_uploads.append({
                        "filename": file.filename,
                        "error": f"Validation failed: {str(validation_error)}"
                    })
                    continue'''
    
    if re.search(batch_validation_pattern, content):
        content = re.sub(batch_validation_pattern, batch_new_validation, content, flags=re.DOTALL)
        print("✅ Enhanced batch upload validation")
    
    # Add rate limiting middleware (placeholder)
    rate_limiting_middleware = '''
# Rate limiting middleware (implement with slowapi or similar)
# @app.middleware("http")
# async def rate_limit_middleware(request: Request, call_next):
#     # Implement rate limiting logic here
#     response = await call_next(request)
#     return response
'''
    
    # Add after imports
    content = content.replace(
        security_imports + '\\n',
        security_imports + rate_limiting_middleware + '\\n'
    )
    
    # Write updated content
    app_path.write_text(content)
    print(f"✅ Updated {app_path} with security enhancements")
    
    # Add JSONResponse import if not present
    if "JSONResponse" not in content:
        content = content.replace(
            "from fastapi import",
            "from fastapi import JSONResponse,"
        )
        app_path.write_text(content)
        print("✅ Added JSONResponse import")

def create_auth_service_stub():
    """Create authentication service stub for frontend"""
    auth_service_path = Path("src/services/authService.ts")
    auth_service_path.parent.mkdir(parents=True, exist_ok=True)
    
    auth_service_content = '''// Authentication Service
// TODO: Implement proper authentication integration

import { User, AuthResponse, LoginCredentials, RegisterData } from '../types/auth';

class AuthService {
  private baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  async getCurrentUser(): Promise<User | null> {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        return null;
      }
      
      const response = await fetch(`${this.baseURL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          this.logout();
          return null;
        }
        throw new Error('Failed to get current user');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }
  
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(credentials)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Login failed');
    }
    
    const authResponse: AuthResponse = await response.json();
    
    // Store tokens
    localStorage.setItem('authToken', authResponse.token);
    localStorage.setItem('refreshToken', authResponse.refreshToken);
    
    return authResponse;
  }
  
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }
    
    const authResponse: AuthResponse = await response.json();
    
    // Store tokens
    localStorage.setItem('authToken', authResponse.token);
    localStorage.setItem('refreshToken', authResponse.refreshToken);
    
    return authResponse;
  }
  
  logout(): void {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    // Redirect to login page or update app state
    window.location.href = '/login';
  }
  
  async refreshToken(): Promise<string | null> {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        return null;
      }
      
      const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refreshToken })
      });
      
      if (!response.ok) {
        this.logout();
        return null;
      }
      
      const { token } = await response.json();
      localStorage.setItem('authToken', token);
      
      return token;
    } catch (error) {
      console.error('Error refreshing token:', error);
      this.logout();
      return null;
    }
  }
}

export const authService = new AuthService();
export default authService;
'''
    
    auth_service_path.write_text(auth_service_content)
    print(f"✅ Created authentication service stub: {auth_service_path}")

if __name__ == "__main__":
    print("Updating backend app with security enhancements...")
    update_app_security()
    create_auth_service_stub()
    print("\\n🎉 Security updates completed!")
    print("\\n📋 Next steps:")
    print("1. Implement proper authentication endpoints in backend")
    print("2. Install python-magic for enhanced file validation: pip install python-magic")
    print("3. Configure rate limiting with slowapi: pip install slowapi")
    print("4. Set up proper JWT secret keys in environment variables")
    print("5. Test file upload endpoints with various file types")
    print("6. Implement proper error logging and monitoring")