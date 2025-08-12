# Developer Onboarding Guide

Welcome to the AI Scholar RAG chatbot project! This guide will help you get up to speed with our development environment, coding standards, and workflows.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Code Quality Standards](#code-quality-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation Standards](#documentation-standards)
8. [Common Tasks](#common-tasks)
9. [Troubleshooting](#troubleshooting)
10. [Resources and Support](#resources-and-support)

## Project Overview

### What is AI Scholar?

AI Scholar is an advanced RAG (Retrieval-Augmented Generation) chatbot designed to assist researchers, students, and academics with intelligent document analysis, research assistance, and knowledge discovery.

### Key Features

- **Intelligent Document Processing**: Upload and analyze academic papers, research documents, and educational materials
- **Advanced Search**: Hybrid search capabilities combining semantic and keyword search
- **Multi-modal Support**: Handle text, images, charts, and tables in documents
- **Real-time Analytics**: Comprehensive analytics and performance monitoring
- **Voice Interaction**: Voice commands and speech-to-text capabilities
- **Personalization**: Adaptive learning and personalized recommendations

### Technology Stack

#### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Query** for data fetching
- **React Router** for navigation
- **Vitest** for testing

#### Backend
- **Python 3.11** with FastAPI
- **PostgreSQL** for primary database
- **Redis** for caching and sessions
- **Elasticsearch** for search capabilities
- **Docker** for containerization

#### Infrastructure
- **GitHub Actions** for CI/CD
- **Docker Compose** for local development
- **Nginx** for reverse proxy
- **Prometheus & Grafana** for monitoring

## Development Environment Setup

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 18+** and npm
- **Python 3.11+** and pip
- **Docker** and Docker Compose
- **Git**
- **VS Code** (recommended) with extensions

### Required VS Code Extensions

Install these extensions for the best development experience:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.test-adapter-converter",
    "hbenl.vscode-test-explorer"
  ]
}
```

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/ai-scholar-chatbot.git
   cd ai-scholar-chatbot
   ```

2. **Install frontend dependencies**:
   ```bash
   npm install
   ```

3. **Set up Python environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

4. **Copy environment files**:
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   ```

5. **Start development services**:
   ```bash
   docker-compose up -d postgres redis elasticsearch
   ```

6. **Initialize the database**:
   ```bash
   cd backend
   python init_enhanced_db.py
   ```

7. **Start the development servers**:
   ```bash
   # Terminal 1: Frontend
   npm run dev

   # Terminal 2: Backend
   cd backend
   python app.py
   ```

8. **Verify setup**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Environment Configuration

#### Frontend Environment Variables

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENVIRONMENT=development
VITE_ENABLE_ANALYTICS=true
VITE_LOG_LEVEL=debug
```

#### Backend Environment Variables

```bash
# backend/.env
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_scholar
REDIS_URL=redis://localhost:6379
ELASTICSEARCH_URL=http://localhost:9200
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=DEBUG
```

## Project Structure

### Frontend Structure

```
src/
├── components/          # React components
│   ├── ui/             # Reusable UI components
│   ├── forms/          # Form components
│   └── __tests__/      # Component tests
├── services/           # API services and business logic
├── hooks/              # Custom React hooks
├── utils/              # Utility functions
├── types/              # TypeScript type definitions
├── contexts/           # React contexts
├── pages/              # Page components
└── test/               # Test utilities and setup
```

### Backend Structure

```
backend/
├── api/                # API endpoints
├── core/               # Core configuration and database
├── services/           # Business logic services
├── models/             # Data models and schemas
├── middleware/         # Custom middleware
├── tests/              # Test files
└── data/               # Data files and migrations
```

### Key Files and Directories

- **`package.json`**: Frontend dependencies and scripts
- **`backend/requirements.txt`**: Python dependencies
- **`docker-compose.yml`**: Development services configuration
- **`eslint.config.js`**: ESLint configuration
- **`backend/pyproject.toml`**: Python project configuration
- **`.github/workflows/`**: CI/CD pipeline definitions
- **`docs/`**: Project documentation

## Development Workflow

### Git Workflow

We use a feature branch workflow with the following conventions:

1. **Branch Naming**:
   - Feature: `feature/description-of-feature`
   - Bug fix: `fix/description-of-bug`
   - Hotfix: `hotfix/description-of-hotfix`
   - Documentation: `docs/description-of-docs`

2. **Commit Messages**:
   Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
   ```
   type(scope): description

   feat(auth): add user authentication
   fix(api): resolve user profile update issue
   docs(readme): update installation instructions
   test(utils): add tests for date utilities
   ```

3. **Pull Request Process**:
   - Create feature branch from `main`
   - Make changes and commit with descriptive messages
   - Push branch and create pull request
   - Ensure all CI checks pass
   - Request review from team members
   - Address feedback and merge when approved

### Daily Development Workflow

1. **Start your day**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**:
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Before committing**:
   ```bash
   # Run linting and formatting
   npm run lint:fix
   npm run format

   # Run tests
   npm test
   cd backend && pytest
   ```

4. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat(component): add new feature"
   git push origin feature/your-feature-name
   ```

5. **Create pull request**:
   - Use the PR template
   - Add descriptive title and description
   - Link related issues
   - Request appropriate reviewers

## Code Quality Standards

### TypeScript/JavaScript Standards

#### ESLint Configuration

Our ESLint configuration enforces:
- TypeScript strict mode
- React best practices
- Import/export conventions
- Code complexity limits
- Accessibility rules

#### Key Rules

```typescript
// ✅ Good: Proper type definitions
interface UserProfile {
  id: string;
  name: string;
  email: string;
  preferences: UserPreferences;
}

// ✅ Good: Explicit return types for functions
const getUserProfile = async (userId: string): Promise<UserProfile> => {
  const response = await api.get(`/users/${userId}`);
  return response.data;
};

// ❌ Bad: Using any type
const processData = (data: any): any => {
  return data.someProperty;
};

// ✅ Good: Proper error handling
try {
  const result = await riskyOperation();
  return result;
} catch (error) {
  if (error instanceof ValidationError) {
    throw new UserFriendlyError('Please check your input');
  }
  throw error;
}
```

### Python Standards

#### Code Formatting

We use **Black** for code formatting and **flake8** for linting:

```python
# ✅ Good: Proper type hints and docstrings
from typing import Optional, List
from datetime import datetime

async def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieve user by email address.
    
    Args:
        email: User's email address
        
    Returns:
        User object if found, None otherwise
        
    Raises:
        ValidationError: If email format is invalid
        DatabaseError: If database operation fails
    """
    if not is_valid_email(email):
        raise ValidationError("Invalid email format")
    
    try:
        user_data = await database.fetch_user_by_email(email)
        return User(**user_data) if user_data else None
    except Exception as e:
        logger.error(f"Failed to fetch user by email {email}: {e}")
        raise DatabaseError("Database operation failed")
```

### Component Standards

#### React Component Structure

```typescript
/**
 * UserDashboard Component
 * 
 * Displays user dashboard with profile information and recent activity
 */
interface UserDashboardProps {
  userId: string;
  onProfileUpdate?: (profile: UserProfile) => void;
}

const UserDashboard: React.FC<UserDashboardProps> = ({ 
  userId, 
  onProfileUpdate 
}) => {
  // State
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Custom hooks
  const { user } = useAuth();
  const { showNotification } = useNotifications();
  
  // Memoized values
  const canEdit = useMemo(() => {
    return user?.id === userId || user?.role === 'admin';
  }, [user, userId]);
  
  // Callbacks
  const handleProfileUpdate = useCallback(async (updatedProfile: UserProfile) => {
    try {
      await updateUserProfile(userId, updatedProfile);
      setProfile(updatedProfile);
      onProfileUpdate?.(updatedProfile);
      showNotification('Profile updated successfully');
    } catch (error) {
      showNotification('Failed to update profile', 'error');
    }
  }, [userId, onProfileUpdate, showNotification]);
  
  // Effects
  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        const profileData = await fetchUserProfile(userId);
        setProfile(profileData);
      } catch (error) {
        setError('Failed to load profile');
      } finally {
        setLoading(false);
      }
    };
    
    loadProfile();
  }, [userId]);
  
  // Render
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!profile) return <EmptyState message="Profile not found" />;
  
  return (
    <div className="user-dashboard">
      <ProfileSection 
        profile={profile}
        canEdit={canEdit}
        onUpdate={handleProfileUpdate}
      />
      <ActivitySection userId={userId} />
    </div>
  );
};

export default UserDashboard;
```

## Testing Guidelines

### Frontend Testing

#### Unit Tests

```typescript
// UserProfile.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserProfile } from './UserProfile';
import { mockUser } from '../__mocks__/userData';

describe('UserProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('renders user profile correctly', async () => {
    render(<UserProfile userId="user123" />);
    
    await waitFor(() => {
      expect(screen.getByText(mockUser.name)).toBeInTheDocument();
      expect(screen.getByText(mockUser.email)).toBeInTheDocument();
    });
  });
  
  it('handles profile update', async () => {
    const onUpdate = jest.fn();
    render(<UserProfile userId="user123" onUpdate={onUpdate} />);
    
    // Wait for profile to load
    await waitFor(() => {
      expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    });
    
    // Click edit button
    fireEvent.click(screen.getByText('Edit Profile'));
    
    // Update name
    const nameInput = screen.getByDisplayValue(mockUser.name);
    fireEvent.change(nameInput, { target: { value: 'Updated Name' } });
    
    // Save changes
    fireEvent.click(screen.getByText('Save'));
    
    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Updated Name' })
      );
    });
  });
});
```

#### Integration Tests

```typescript
// api.integration.test.ts
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { apiService } from '../services/apiService';

const server = setupServer(
  rest.get('/api/users/:id', (req, res, ctx) => {
    return res(ctx.json({ id: req.params.id, name: 'Test User' }));
  })
);

describe('API Integration', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());
  
  it('fetches user data', async () => {
    const user = await apiService.getUser('user123');
    expect(user).toEqual({ id: 'user123', name: 'Test User' });
  });
});
```

### Backend Testing

#### Unit Tests

```python
# test_user_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from services.user_service import UserService
from models.user import User

class TestUserService:
    @pytest.fixture
    def mock_database(self):
        return Mock()
    
    @pytest.fixture
    def user_service(self, mock_database):
        return UserService(mock_database)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_service, mock_database):
        # Arrange
        user_data = {
            'id': 'user123',
            'name': 'Test User',
            'email': 'test@example.com'
        }
        mock_database.fetch_user = AsyncMock(return_value=user_data)
        
        # Act
        result = await user_service.get_user_by_id('user123')
        
        # Assert
        assert result is not None
        assert result.id == 'user123'
        assert result.name == 'Test User'
        mock_database.fetch_user.assert_called_once_with('user123')
```

### Test Coverage Requirements

- **Minimum Coverage**: 80% line coverage
- **Critical Features**: 95% coverage for authentication, payments, security
- **New Code**: 90% coverage for all new features

### Running Tests

```bash
# Frontend tests
npm test                    # Run all tests
npm run test:watch         # Watch mode
npm run test:coverage      # With coverage report

# Backend tests
cd backend
pytest                     # Run all tests
pytest --cov=.            # With coverage
pytest -v tests/test_user_service.py  # Specific test file
```

## Documentation Standards

### Code Documentation

#### JSDoc for TypeScript

```typescript
/**
 * Calculates the similarity score between two documents
 * 
 * @param doc1 - First document to compare
 * @param doc2 - Second document to compare
 * @param options - Comparison options
 * @param options.algorithm - Algorithm to use ('cosine' | 'jaccard')
 * @param options.threshold - Minimum similarity threshold
 * 
 * @returns Promise resolving to similarity score (0-1)
 * 
 * @throws {ValidationError} When documents are invalid
 * @throws {ProcessingError} When similarity calculation fails
 * 
 * @example
 * ```typescript
 * const score = await calculateSimilarity(doc1, doc2, {
 *   algorithm: 'cosine',
 *   threshold: 0.5
 * });
 * console.log(`Similarity: ${score}`);
 * ```
 */
export async function calculateSimilarity(
  doc1: Document,
  doc2: Document,
  options: SimilarityOptions = {}
): Promise<number> {
  // Implementation
}
```

#### Python Docstrings

```python
def process_document(
    document: Document, 
    options: ProcessingOptions = None
) -> ProcessedDocument:
    """
    Process a document for analysis and indexing.
    
    This function extracts text, images, and metadata from various
    document formats and prepares them for search indexing.
    
    Args:
        document: Document object to process
        options: Processing configuration options
            - extract_images: Whether to extract images (default: True)
            - extract_tables: Whether to extract tables (default: True)
            - language: Document language for processing (default: 'en')
    
    Returns:
        ProcessedDocument with extracted content and metadata
    
    Raises:
        ValidationError: If document format is not supported
        ProcessingError: If document processing fails
        
    Example:
        >>> doc = Document(path='research_paper.pdf')
        >>> processed = process_document(doc, ProcessingOptions(
        ...     extract_images=True,
        ...     language='en'
        ... ))
        >>> print(f"Extracted {len(processed.text_chunks)} text chunks")
        
    Note:
        Large documents may take significant time to process.
        Consider using async processing for better performance.
    """
    # Implementation
```

### README Files

Each major component should have a README with:

1. **Purpose and Overview**
2. **Installation/Setup Instructions**
3. **Usage Examples**
4. **API Reference**
5. **Configuration Options**
6. **Testing Instructions**
7. **Contributing Guidelines**

## Common Tasks

### Adding a New Feature

1. **Create feature branch**:
   ```bash
   git checkout -b feature/new-feature-name
   ```

2. **Frontend component**:
   ```bash
   # Create component file
   touch src/components/NewFeature.tsx
   
   # Create test file
   touch src/components/__tests__/NewFeature.test.tsx
   
   # Create types if needed
   touch src/types/newFeature.ts
   ```

3. **Backend endpoint**:
   ```bash
   # Create API endpoint
   touch backend/api/new_feature_endpoints.py
   
   # Create service
   touch backend/services/new_feature_service.py
   
   # Create tests
   touch backend/tests/test_new_feature.py
   ```

4. **Add tests and documentation**
5. **Update relevant README files**
6. **Create pull request**

### Adding a New API Endpoint

1. **Define the endpoint**:
   ```python
   # backend/api/new_endpoints.py
   from fastapi import APIRouter, Depends
   from services.new_service import NewService
   
   router = APIRouter(prefix="/api/new", tags=["new"])
   
   @router.get("/items")
   async def get_items(service: NewService = Depends()):
       """Get all items."""
       return await service.get_all_items()
   ```

2. **Add to main app**:
   ```python
   # backend/app.py
   from api.new_endpoints import router as new_router
   
   app.include_router(new_router)
   ```

3. **Create frontend service**:
   ```typescript
   // src/services/newService.ts
   export const newService = {
     async getItems(): Promise<Item[]> {
       const response = await api.get('/api/new/items');
       return response.data;
     }
   };
   ```

4. **Add tests for both frontend and backend**

### Debugging Common Issues

#### Frontend Issues

1. **TypeScript errors**:
   ```bash
   npm run type-check
   ```

2. **ESLint errors**:
   ```bash
   npm run lint:fix
   ```

3. **Build issues**:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

#### Backend Issues

1. **Python import errors**:
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. **Database connection issues**:
   ```bash
   docker-compose restart postgres
   python init_enhanced_db.py
   ```

3. **Type checking errors**:
   ```bash
   mypy .
   ```

## Troubleshooting

### Common Development Issues

#### Port Already in Use

```bash
# Find process using port
lsof -i :5173  # Frontend
lsof -i :8000  # Backend

# Kill process
kill -9 <PID>
```

#### Database Connection Issues

```bash
# Reset database
docker-compose down
docker-compose up -d postgres
cd backend && python init_enhanced_db.py
```

#### Node Modules Issues

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

#### Python Environment Issues

```bash
# Recreate virtual environment
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Getting Help

1. **Check existing documentation**
2. **Search GitHub issues**
3. **Ask in team chat**
4. **Create GitHub issue with details**

## Resources and Support

### Documentation

- [Code Quality Guidelines](./CODE_QUALITY_GUIDELINES.md)
- [API Documentation](./api/)
- [Component Documentation](../src/components/README.md)
- [Services Documentation](../src/services/README.md)

### External Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### Development Tools

- [VS Code](https://code.visualstudio.com/)
- [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/)
- [Postman](https://www.postman.com/) for API testing
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Team Communication

- **Daily Standups**: 9:00 AM EST
- **Code Reviews**: Within 24 hours
- **Team Chat**: Slack #ai-scholar-dev
- **Documentation**: GitHub Wiki

### Next Steps

After completing this onboarding:

1. **Complete your first task**: Look for issues labeled "good first issue"
2. **Attend team meetings**: Join daily standups and weekly planning
3. **Set up your development environment**: Ensure all tools are working
4. **Read the codebase**: Familiarize yourself with existing code
5. **Ask questions**: Don't hesitate to ask for help or clarification

Welcome to the team! We're excited to have you contribute to AI Scholar.