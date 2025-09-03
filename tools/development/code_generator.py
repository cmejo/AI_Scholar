"""
AI-Powered Code Generator for AI Scholar
Intelligent code generation with context awareness and best practices
"""
import asyncio
import json
import logging
import ast
import inspect
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CodeGenerationRequest:
    """Code generation request structure"""
    description: str
    language: str
    framework: Optional[str] = None
    context: Dict[str, Any] = None
    requirements: List[str] = None
    style_preferences: Dict[str, Any] = None
    target_file: Optional[str] = None

@dataclass
class GeneratedCode:
    """Generated code result"""
    code: str
    language: str
    explanation: str
    tests: Optional[str] = None
    documentation: Optional[str] = None
    dependencies: List[str] = None
    confidence_score: float = 0.0
    suggestions: List[str] = None

class CodeAnalyzer:
    """Analyzes existing code for context and patterns"""
    
    def __init__(self):
        self.patterns = {}
        self.style_guide = {}
    
    async def analyze_codebase_patterns(self, project_path: str) -> Dict[str, Any]:
        """Analyze existing codebase to understand patterns and style"""
        patterns = {
            "naming_conventions": {},
            "import_patterns": {},
            "class_structures": {},
            "function_patterns": {},
            "documentation_style": {},
            "testing_patterns": {}
        }
        
        # Analyze Python files
        python_files = list(Path(project_path).rglob("*.py"))
        for file_path in python_files[:20]:  # Limit for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                file_patterns = self._analyze_python_file(tree, content)
                self._merge_patterns(patterns, file_patterns)
                
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Analyze TypeScript/JavaScript files
        ts_files = list(Path(project_path).rglob("*.ts")) + list(Path(project_path).rglob("*.tsx"))
        for file_path in ts_files[:20]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_patterns = self._analyze_typescript_file(content)
                self._merge_patterns(patterns, file_patterns)
                
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        return patterns
    
    def _analyze_python_file(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze Python file patterns"""
        patterns = {
            "naming_conventions": {"classes": [], "functions": [], "variables": []},
            "import_patterns": {"standard": [], "third_party": [], "local": []},
            "class_structures": [],
            "function_patterns": {"async": 0, "sync": 0, "decorators": []},
            "documentation_style": {"docstring_style": None, "type_hints": 0}
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                patterns["naming_conventions"]["classes"].append(node.name)
                patterns["class_structures"].append({
                    "name": node.name,
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                })
            
            elif isinstance(node, ast.FunctionDef):
                patterns["naming_conventions"]["functions"].append(node.name)
                if node.returns:
                    patterns["documentation_style"]["type_hints"] += 1
                
                if any(isinstance(d, ast.Name) and d.id == 'asyncio' for d in ast.walk(node)):
                    patterns["function_patterns"]["async"] += 1
                else:
                    patterns["function_patterns"]["sync"] += 1
            
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    patterns["import_patterns"]["standard"].append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    patterns["import_patterns"]["third_party"].append(node.module)
        
        # Analyze docstring style
        docstring_pattern = re.search(r'"""([^"]*?)"""', content)
        if docstring_pattern:
            patterns["documentation_style"]["docstring_style"] = "triple_quotes"
        
        return patterns
    
    def _analyze_typescript_file(self, content: str) -> Dict[str, Any]:
        """Analyze TypeScript file patterns"""
        patterns = {
            "naming_conventions": {"interfaces": [], "classes": [], "functions": []},
            "import_patterns": {"imports": [], "exports": []},
            "type_patterns": {"interfaces": 0, "types": 0, "generics": 0}
        }
        
        # Extract interfaces
        interface_matches = re.findall(r'interface\s+(\w+)', content)
        patterns["naming_conventions"]["interfaces"].extend(interface_matches)
        patterns["type_patterns"]["interfaces"] = len(interface_matches)
        
        # Extract classes
        class_matches = re.findall(r'class\s+(\w+)', content)
        patterns["naming_conventions"]["classes"].extend(class_matches)
        
        # Extract functions
        function_matches = re.findall(r'(?:function\s+(\w+)|const\s+(\w+)\s*=)', content)
        for match in function_matches:
            name = match[0] or match[1]
            if name:
                patterns["naming_conventions"]["functions"].append(name)
        
        # Extract imports
        import_matches = re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content)
        patterns["import_patterns"]["imports"].extend(import_matches)
        
        return patterns
    
    def _merge_patterns(self, main_patterns: Dict[str, Any], file_patterns: Dict[str, Any]):
        """Merge file patterns into main patterns"""
        for category, data in file_patterns.items():
            if category not in main_patterns:
                main_patterns[category] = {}
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if key not in main_patterns[category]:
                        main_patterns[category][key] = []
                    
                    if isinstance(value, list):
                        main_patterns[category][key].extend(value)
                    elif isinstance(value, (int, float)):
                        if not isinstance(main_patterns[category][key], (int, float)):
                            main_patterns[category][key] = 0
                        main_patterns[category][key] += value
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return "unknown"

class CodeGenerator:
    """AI-powered code generator"""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Load code templates"""
        self.templates = {
            "python": {
                "class": '''class {class_name}:
    """
    {description}
    """
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}
''',
                "function": '''def {function_name}({parameters}) -> {return_type}:
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {return_doc}
    """
    {body}
''',
                "async_function": '''async def {function_name}({parameters}) -> {return_type}:
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {return_doc}
    """
    {body}
''',
                "test": '''def test_{function_name}():
    """Test {function_name} function"""
    # Arrange
    {arrange}
    
    # Act
    {act}
    
    # Assert
    {assert_statements}
'''
            },
            "typescript": {
                "interface": '''interface {interface_name} {{
    {properties}
}}''',
                "class": '''class {class_name} {{
    {properties}
    
    constructor({constructor_params}) {{
        {constructor_body}
    }}
    
    {methods}
}}''',
                "function": '''function {function_name}({parameters}): {return_type} {{
    {body}
}}''',
                "react_component": '''interface {component_name}Props {{
    {props}
}}

const {component_name}: React.FC<{component_name}Props> = ({{
    {prop_destructuring}
}}) => {{
    {hooks}
    
    return (
        {jsx}
    );
}};

export default {component_name};'''
            }
        }
    
    async def generate_code(self, request: CodeGenerationRequest) -> GeneratedCode:
        """Generate code based on request"""
        # Analyze context if provided
        context_patterns = {}
        if request.context and request.context.get("project_path"):
            context_patterns = await self.analyzer.analyze_codebase_patterns(
                request.context["project_path"]
            )
        
        # Generate code based on language and type
        if request.language.lower() == "python":
            return await self._generate_python_code(request, context_patterns)
        elif request.language.lower() in ["typescript", "javascript"]:
            return await self._generate_typescript_code(request, context_patterns)
        else:
            raise ValueError(f"Unsupported language: {request.language}")
    
    async def _generate_python_code(
        self, 
        request: CodeGenerationRequest, 
        patterns: Dict[str, Any]
    ) -> GeneratedCode:
        """Generate Python code"""
        description = request.description.lower()
        
        # Determine code type
        if "class" in description:
            return await self._generate_python_class(request, patterns)
        elif "function" in description or "method" in description:
            return await self._generate_python_function(request, patterns)
        elif "api" in description or "endpoint" in description:
            return await self._generate_python_api(request, patterns)
        elif "test" in description:
            return await self._generate_python_test(request, patterns)
        else:
            return await self._generate_python_general(request, patterns)
    
    async def _generate_python_class(
        self, 
        request: CodeGenerationRequest, 
        patterns: Dict[str, Any]
    ) -> GeneratedCode:
        """Generate Python class"""
        # Extract class name from description
        class_name = self._extract_class_name(request.description)
        
        # Determine naming convention from patterns
        if patterns.get("naming_conventions", {}).get("classes"):
            existing_classes = patterns["naming_conventions"]["classes"]
            # Analyze naming pattern (PascalCase, snake_case, etc.)
            if all(c[0].isupper() for c in existing_classes[:5]):
                class_name = self._to_pascal_case(class_name)
        
        # Generate methods based on requirements
        methods = []
        if request.requirements:
            for req in request.requirements:
                if "method" in req.lower():
                    method_code = self._generate_method_from_requirement(req)
                    methods.append(method_code)
        
        # Use template
        template = self.templates["python"]["class"]
        code = template.format(
            class_name=class_name,
            description=request.description,
            init_params=self._generate_init_params(request.requirements or []),
            init_body=self._generate_init_body(request.requirements or []),
            methods="\n    ".join(methods) if methods else "pass"
        )
        
        # Generate tests
        test_code = self._generate_class_tests(class_name, methods)
        
        # Generate documentation
        doc = f"# {class_name}\n\n{request.description}\n\n## Usage\n\n```python\n{class_name.lower()} = {class_name}()\n```"
        
        return GeneratedCode(
            code=code,
            language="python",
            explanation=f"Generated {class_name} class with {len(methods)} methods",
            tests=test_code,
            documentation=doc,
            dependencies=self._extract_dependencies(code),
            confidence_score=0.85,
            suggestions=[
                "Add type hints for better code clarity",
                "Consider adding docstrings to methods",
                "Add error handling where appropriate"
            ]
        )
    
    async def _generate_python_function(
        self, 
        request: CodeGenerationRequest, 
        patterns: Dict[str, Any]
    ) -> GeneratedCode:
        """Generate Python function"""
        function_name = self._extract_function_name(request.description)
        
        # Determine if async based on context
        is_async = (
            "async" in request.description.lower() or
            "await" in request.description.lower() or
            (request.context and request.context.get("async_context", False))
        )
        
        # Generate parameters
        parameters = self._generate_function_parameters(request.requirements or [])
        
        # Generate function body
        body = self._generate_function_body(request.description, request.requirements or [])
        
        # Use appropriate template
        template = self.templates["python"]["async_function" if is_async else "function"]
        
        code = template.format(
            function_name=function_name,
            parameters=parameters,
            return_type=self._infer_return_type(request.description),
            description=request.description,
            args_doc=self._generate_args_documentation(parameters),
            return_doc=self._generate_return_documentation(request.description),
            body=body
        )
        
        # Generate tests
        test_code = self._generate_function_tests(function_name, parameters, is_async)
        
        return GeneratedCode(
            code=code,
            language="python",
            explanation=f"Generated {'async ' if is_async else ''}{function_name} function",
            tests=test_code,
            dependencies=self._extract_dependencies(code),
            confidence_score=0.90,
            suggestions=[
                "Add input validation",
                "Consider error handling",
                "Add logging for debugging"
            ]
        )
    
    async def _generate_typescript_code(
        self, 
        request: CodeGenerationRequest, 
        patterns: Dict[str, Any]
    ) -> GeneratedCode:
        """Generate TypeScript code"""
        description = request.description.lower()
        
        if "component" in description or "react" in description:
            return await self._generate_react_component(request, patterns)
        elif "interface" in description or "type" in description:
            return await self._generate_typescript_interface(request, patterns)
        elif "class" in description:
            return await self._generate_typescript_class(request, patterns)
        else:
            return await self._generate_typescript_function(request, patterns)
    
    async def _generate_react_component(
        self, 
        request: CodeGenerationRequest, 
        patterns: Dict[str, Any]
    ) -> GeneratedCode:
        """Generate React component"""
        component_name = self._extract_component_name(request.description)
        
        # Generate props interface
        props = self._generate_component_props(request.requirements or [])
        
        # Generate hooks
        hooks = self._generate_component_hooks(request.requirements or [])
        
        # Generate JSX
        jsx = self._generate_component_jsx(component_name, request.requirements or [])
        
        template = self.templates["typescript"]["react_component"]
        code = template.format(
            component_name=component_name,
            props=props,
            prop_destructuring=self._generate_prop_destructuring(props),
            hooks=hooks,
            jsx=jsx
        )
        
        # Generate tests
        test_code = self._generate_component_tests(component_name)
        
        return GeneratedCode(
            code=code,
            language="typescript",
            explanation=f"Generated {component_name} React component",
            tests=test_code,
            dependencies=["react", "@types/react"],
            confidence_score=0.88,
            suggestions=[
                "Add prop validation",
                "Consider memoization for performance",
                "Add accessibility attributes"
            ]
        )
    
    # Helper methods
    def _extract_class_name(self, description: str) -> str:
        """Extract class name from description"""
        # Simple extraction - in real implementation, use NLP
        words = description.split()
        for i, word in enumerate(words):
            if word.lower() in ["class", "create", "implement"]:
                if i + 1 < len(words):
                    return self._to_pascal_case(words[i + 1])
        return "GeneratedClass"
    
    def _extract_function_name(self, description: str) -> str:
        """Extract function name from description"""
        # Simple extraction
        words = description.split()
        for i, word in enumerate(words):
            if word.lower() in ["function", "method", "create", "implement"]:
                if i + 1 < len(words):
                    return self._to_snake_case(words[i + 1])
        return "generated_function"
    
    def _extract_component_name(self, description: str) -> str:
        """Extract component name from description"""
        words = description.split()
        for i, word in enumerate(words):
            if word.lower() in ["component", "create", "implement"]:
                if i + 1 < len(words):
                    return self._to_pascal_case(words[i + 1])
        return "GeneratedComponent"
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert to PascalCase"""
        return ''.join(word.capitalize() for word in re.findall(r'\w+', text))
    
    def _to_snake_case(self, text: str) -> str:
        """Convert to snake_case"""
        return '_'.join(re.findall(r'\w+', text.lower()))
    
    def _generate_init_params(self, requirements: List[str]) -> str:
        """Generate __init__ parameters"""
        params = []
        for req in requirements:
            if "parameter" in req.lower() or "attribute" in req.lower():
                # Extract parameter name
                words = req.split()
                for word in words:
                    if word.isidentifier():
                        params.append(f"{word}: Any = None")
                        break
        return ", " + ", ".join(params) if params else ""
    
    def _generate_init_body(self, requirements: List[str]) -> str:
        """Generate __init__ body"""
        assignments = []
        for req in requirements:
            if "attribute" in req.lower():
                words = req.split()
                for word in words:
                    if word.isidentifier():
                        assignments.append(f"self.{word} = {word}")
                        break
        return "\n        ".join(assignments) if assignments else "pass"
    
    def _generate_method_from_requirement(self, requirement: str) -> str:
        """Generate method from requirement"""
        method_name = self._extract_function_name(requirement)
        return f'''def {method_name}(self) -> Any:
        """
        {requirement}
        """
        # TODO: Implement {method_name}
        pass'''
    
    def _generate_function_parameters(self, requirements: List[str]) -> str:
        """Generate function parameters"""
        params = []
        for req in requirements:
            if "parameter" in req.lower() or "input" in req.lower():
                words = req.split()
                for word in words:
                    if word.isidentifier() and word not in ["parameter", "input"]:
                        params.append(f"{word}: Any")
                        break
        return ", ".join(params) if params else ""
    
    def _generate_function_body(self, description: str, requirements: List[str]) -> str:
        """Generate function body"""
        # Simple implementation - in real version, use AI
        if "return" in description.lower():
            return "# TODO: Implement function logic\n    return None"
        else:
            return "# TODO: Implement function logic\n    pass"
    
    def _infer_return_type(self, description: str) -> str:
        """Infer return type from description"""
        description_lower = description.lower()
        if "list" in description_lower:
            return "List[Any]"
        elif "dict" in description_lower:
            return "Dict[str, Any]"
        elif "bool" in description_lower or "true" in description_lower or "false" in description_lower:
            return "bool"
        elif "int" in description_lower or "number" in description_lower:
            return "int"
        elif "str" in description_lower or "string" in description_lower:
            return "str"
        else:
            return "Any"
    
    def _generate_args_documentation(self, parameters: str) -> str:
        """Generate arguments documentation"""
        if not parameters:
            return "None"
        
        params = parameters.split(", ")
        docs = []
        for param in params:
            param_name = param.split(":")[0].strip()
            docs.append(f"{param_name}: Description of {param_name}")
        
        return "\n        ".join(docs)
    
    def _generate_return_documentation(self, description: str) -> str:
        """Generate return documentation"""
        return f"Description of return value based on: {description}"
    
    def _generate_function_tests(self, function_name: str, parameters: str, is_async: bool) -> str:
        """Generate function tests"""
        test_template = self.templates["python"]["test"]
        
        # Generate test data
        arrange = "# Set up test data"
        if parameters:
            param_names = [p.split(":")[0].strip() for p in parameters.split(", ")]
            arrange = "\n    ".join([f"{name} = None  # TODO: Set test value" for name in param_names])
        
        act = f"result = {'await ' if is_async else ''}{function_name}({', '.join(parameters.split(', ')) if parameters else ''})"
        assert_statements = "assert result is not None  # TODO: Add proper assertions"
        
        return test_template.format(
            function_name=function_name,
            arrange=arrange,
            act=act,
            assert_statements=assert_statements
        )
    
    def _generate_class_tests(self, class_name: str, methods: List[str]) -> str:
        """Generate class tests"""
        test_code = f'''def test_{class_name.lower()}_creation():
    """Test {class_name} instantiation"""
    instance = {class_name}()
    assert instance is not None

'''
        
        for method in methods:
            method_name = method.split("def ")[1].split("(")[0] if "def " in method else "method"
            test_code += f'''def test_{class_name.lower()}_{method_name}():
    """Test {class_name}.{method_name}"""
    instance = {class_name}()
    # TODO: Add test implementation
    pass

'''
        
        return test_code
    
    def _generate_component_props(self, requirements: List[str]) -> str:
        """Generate React component props"""
        props = []
        for req in requirements:
            if "prop" in req.lower() or "property" in req.lower():
                words = req.split()
                for word in words:
                    if word.isidentifier() and word not in ["prop", "property"]:
                        props.append(f"  {word}: string;")
                        break
        
        return "\n".join(props) if props else "  // No props defined"
    
    def _generate_component_hooks(self, requirements: List[str]) -> str:
        """Generate React hooks"""
        hooks = []
        for req in requirements:
            if "state" in req.lower():
                hooks.append("const [state, setState] = useState();")
            elif "effect" in req.lower():
                hooks.append("useEffect(() => {\n    // TODO: Implement effect\n  }, []);")
        
        return "\n  ".join(hooks) if hooks else "// No hooks needed"
    
    def _generate_component_jsx(self, component_name: str, requirements: List[str]) -> str:
        """Generate JSX for component"""
        return f'''<div className="{component_name.lower()}">
      <h1>{component_name}</h1>
      {{/* TODO: Implement component UI */}}
    </div>'''
    
    def _generate_prop_destructuring(self, props: str) -> str:
        """Generate prop destructuring"""
        if "No props" in props:
            return ""
        
        prop_names = []
        for line in props.split("\n"):
            if ":" in line:
                prop_name = line.split(":")[0].strip()
                if prop_name and not prop_name.startswith("//"):
                    prop_names.append(prop_name)
        
        return ", ".join(prop_names)
    
    def _generate_component_tests(self, component_name: str) -> str:
        """Generate React component tests"""
        return f'''import {{ render, screen }} from '@testing-library/react';
import {component_name} from './{component_name}';

describe('{component_name}', () => {{
  it('renders without crashing', () => {{
    render(<{component_name} />);
    expect(screen.getByText('{component_name}')).toBeInTheDocument();
  }});
  
  // TODO: Add more specific tests
}});'''
    
    def _extract_dependencies(self, code: str) -> List[str]:
        """Extract dependencies from generated code"""
        dependencies = []
        
        # Python imports
        import_matches = re.findall(r'from\s+(\w+)', code)
        dependencies.extend(import_matches)
        
        import_matches = re.findall(r'import\s+(\w+)', code)
        dependencies.extend(import_matches)
        
        # Remove standard library modules
        standard_libs = {'os', 'sys', 'json', 'datetime', 'typing', 'asyncio', 'logging'}
        dependencies = [dep for dep in dependencies if dep not in standard_libs]
        
        return list(set(dependencies))

# Global code generator instance
code_generator = CodeGenerator()

# Convenience functions
async def generate_code(
    description: str,
    language: str,
    **kwargs
) -> GeneratedCode:
    """Generate code from description"""
    request = CodeGenerationRequest(
        description=description,
        language=language,
        **kwargs
    )
    return await code_generator.generate_code(request)

async def analyze_project_patterns(project_path: str) -> Dict[str, Any]:
    """Analyze project patterns"""
    return await code_generator.analyzer.analyze_codebase_patterns(project_path)

if __name__ == "__main__":
    # Example usage
    async def test_code_generator():
        print("🧪 Testing Code Generator...")
        
        # Test Python class generation
        result = await generate_code(
            "Create a UserManager class with methods to add, remove, and find users",
            "python",
            requirements=[
                "Method to add user with validation",
                "Method to remove user by ID", 
                "Method to find user by email"
            ]
        )
        
        print(f"Generated Python class:")
        print(result.code[:200] + "...")
        print(f"Confidence: {result.confidence_score}")
        print(f"Dependencies: {result.dependencies}")
        
        # Test React component generation
        result = await generate_code(
            "Create a UserProfile React component",
            "typescript",
            framework="react",
            requirements=[
                "Props for user data",
                "State for editing mode",
                "Effect to load user data"
            ]
        )
        
        print(f"\nGenerated React component:")
        print(result.code[:200] + "...")
        print(f"Tests generated: {len(result.tests) if result.tests else 0} characters")
    
    asyncio.run(test_code_generator())