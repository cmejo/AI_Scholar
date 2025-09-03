"""
Interactive API Documentation Generator for AI Scholar
Creates comprehensive, interactive API documentation with examples and testing
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import inspect
import ast
from pathlib import Path
import re
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
import yaml

logger = logging.getLogger(__name__)

@dataclass
class APIEndpoint:
    """API endpoint documentation"""
    path: str
    method: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    examples: List[Dict[str, Any]]
    tags: List[str]
    deprecated: bool = False

@dataclass
class APIDocumentation:
    """Complete API documentation"""
    title: str
    version: str
    description: str
    base_url: str
    endpoints: List[APIEndpoint]
    schemas: Dict[str, Any]
    security: Dict[str, Any]
    generated_at: datetime

class APIDocumentationGenerator:
    """Generates comprehensive API documentation"""
    
    def __init__(self, app: FastAPI = None):
        self.app = app
        self.custom_examples = {}
        self.custom_descriptions = {}
    
    async def generate_documentation(self, output_format: str = "html") -> str:
        """Generate complete API documentation"""
        if not self.app:
            raise ValueError("FastAPI app instance required")
        
        # Extract API information
        openapi_schema = get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description,
            routes=self.app.routes,
        )
        
        # Parse endpoints
        endpoints = await self._parse_endpoints(openapi_schema)
        
        # Create documentation object
        documentation = APIDocumentation(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description or "API Documentation",
            base_url="http://localhost:8000",  # Default, should be configurable
            endpoints=endpoints,
            schemas=openapi_schema.get("components", {}).get("schemas", {}),
            security=openapi_schema.get("components", {}).get("securitySchemes", {}),
            generated_at=datetime.now()
        )
        
        # Generate output based on format
        if output_format == "html":
            return await self._generate_html_docs(documentation)
        elif output_format == "markdown":
            return await self._generate_markdown_docs(documentation)
        elif output_format == "json":
            return json.dumps(asdict(documentation), indent=2, default=str)
        elif output_format == "yaml":
            return yaml.dump(asdict(documentation), default_flow_style=False)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    async def _parse_endpoints(self, openapi_schema: Dict[str, Any]) -> List[APIEndpoint]:
        """Parse endpoints from OpenAPI schema"""
        endpoints = []
        
        paths = openapi_schema.get("paths", {})
        for path, path_info in paths.items():
            for method, method_info in path_info.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = await self._create_endpoint_doc(
                        path, method.upper(), method_info
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    async def _create_endpoint_doc(
        self, 
        path: str, 
        method: str, 
        method_info: Dict[str, Any]
    ) -> APIEndpoint:
        """Create endpoint documentation"""
        # Extract parameters
        parameters = []
        if "parameters" in method_info:
            for param in method_info["parameters"]:
                parameters.append({
                    "name": param.get("name"),
                    "in": param.get("in"),
                    "required": param.get("required", False),
                    "type": param.get("schema", {}).get("type", "string"),
                    "description": param.get("description", ""),
                    "example": param.get("example")
                })
        
        # Extract request body
        request_body = None
        if "requestBody" in method_info:
            request_body = method_info["requestBody"]
        
        # Extract responses
        responses = {}
        if "responses" in method_info:
            for status_code, response_info in method_info["responses"].items():
                responses[status_code] = {
                    "description": response_info.get("description", ""),
                    "schema": response_info.get("content", {})
                }
        
        # Generate examples
        examples = await self._generate_examples(path, method, method_info)
        
        return APIEndpoint(
            path=path,
            method=method,
            summary=method_info.get("summary", ""),
            description=method_info.get("description", ""),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            examples=examples,
            tags=method_info.get("tags", []),
            deprecated=method_info.get("deprecated", False)
        )
    
    async def _generate_examples(
        self, 
        path: str, 
        method: str, 
        method_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate examples for endpoint"""
        examples = []
        
        # Check for custom examples
        endpoint_key = f"{method}:{path}"
        if endpoint_key in self.custom_examples:
            return self.custom_examples[endpoint_key]
        
        # Generate basic examples
        if method == "GET":
            examples.append({
                "title": "Basic GET request",
                "description": f"Retrieve data from {path}",
                "request": {
                    "method": method,
                    "url": path,
                    "headers": {"Accept": "application/json"}
                },
                "response": {
                    "status": 200,
                    "body": {"message": "Success", "data": {}}
                }
            })
        
        elif method == "POST":
            examples.append({
                "title": "Create new resource",
                "description": f"Create new resource at {path}",
                "request": {
                    "method": method,
                    "url": path,
                    "headers": {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    "body": {"name": "example", "value": "test"}
                },
                "response": {
                    "status": 201,
                    "body": {"id": 1, "name": "example", "value": "test"}
                }
            })
        
        return examples
    
    async def _generate_html_docs(self, documentation: APIDocumentation) -> str:
        """Generate HTML documentation"""
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - API Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 0;
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .endpoint {{
            background: white;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .endpoint-header {{
            padding: 20px;
            border-bottom: 1px solid #eee;
        }}
        .method {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.8em;
            margin-right: 10px;
        }}
        .method.get {{ background-color: #28a745; color: white; }}
        .method.post {{ background-color: #007bff; color: white; }}
        .method.put {{ background-color: #ffc107; color: black; }}
        .method.delete {{ background-color: #dc3545; color: white; }}
        .method.patch {{ background-color: #6f42c1; color: white; }}
        .endpoint-path {{
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 1.1em;
        }}
        .endpoint-body {{
            padding: 20px;
        }}
        .section {{
            margin-bottom: 20px;
        }}
        .section h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .parameters {{
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 15px;
        }}
        .parameter {{
            margin-bottom: 10px;
            padding: 10px;
            background: white;
            border-radius: 4px;
            border-left: 4px solid #007bff;
        }}
        .parameter-name {{
            font-weight: bold;
            color: #007bff;
        }}
        .parameter-type {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .required {{
            color: #dc3545;
            font-size: 0.8em;
        }}
        .example {{
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .code {{
            background-color: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }}
        .try-it {{
            background-color: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }}
        .try-it:hover {{
            background-color: #218838;
        }}
        .nav {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .nav h3 {{
            margin: 0 0 15px 0;
        }}
        .nav ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .nav li {{
            margin-bottom: 5px;
        }}
        .nav a {{
            color: #007bff;
            text-decoration: none;
            padding: 5px 10px;
            border-radius: 4px;
            display: block;
        }}
        .nav a:hover {{
            background-color: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>{title}</h1>
            <p>Version {version} | Generated on {generated_at}</p>
            <p>{description}</p>
        </div>
    </div>
    
    <div class="container">
        <div class="nav">
            <h3>📋 Endpoints</h3>
            <ul>
                {nav_items}
            </ul>
        </div>
        
        {endpoints_html}
    </div>
    
    <script>
        function tryEndpoint(path, method) {{
            const baseUrl = '{base_url}';
            const fullUrl = baseUrl + path;
            
            // This would integrate with actual API testing
            alert(`Testing ${{method}} ${{fullUrl}}`);
            
            // In a real implementation, this would make actual API calls
            // and display the results in a modal or dedicated section
        }}
        
        // Add smooth scrolling for navigation
        document.querySelectorAll('.nav a').forEach(link => {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});
    </script>
</body>
</html>'''
        
        # Generate navigation items
        nav_items = []
        for endpoint in documentation.endpoints:
            nav_items.append(
                f'<li><a href="#endpoint-{endpoint.method.lower()}-{endpoint.path.replace("/", "-").replace("{", "").replace("}", "")}">'
                f'<span class="method {endpoint.method.lower()}">{endpoint.method}</span> {endpoint.path}</a></li>'
            )
        
        # Generate endpoints HTML
        endpoints_html = []
        for endpoint in documentation.endpoints:
            endpoint_id = f"endpoint-{endpoint.method.lower()}-{endpoint.path.replace('/', '-').replace('{', '').replace('}', '')}"
            
            # Parameters section
            parameters_html = ""
            if endpoint.parameters:
                params_list = []
                for param in endpoint.parameters:
                    required_badge = '<span class="required">*required</span>' if param.get("required") else ""
                    params_list.append(f'''
                    <div class="parameter">
                        <div class="parameter-name">{param["name"]} {required_badge}</div>
                        <div class="parameter-type">Type: {param.get("type", "string")} | Location: {param.get("in", "query")}</div>
                        <div>{param.get("description", "No description available")}</div>
                    </div>
                    ''')
                parameters_html = f'<div class="parameters">{"".join(params_list)}</div>'
            
            # Examples section
            examples_html = ""
            if endpoint.examples:
                examples_list = []
                for example in endpoint.examples:
                    request_code = json.dumps(example.get("request", {}), indent=2)
                    response_code = json.dumps(example.get("response", {}), indent=2)
                    
                    examples_list.append(f'''
                    <div class="example">
                        <h5>{example.get("title", "Example")}</h5>
                        <p>{example.get("description", "")}</p>
                        <div class="section">
                            <h6>Request:</h6>
                            <div class="code">{request_code}</div>
                        </div>
                        <div class="section">
                            <h6>Response:</h6>
                            <div class="code">{response_code}</div>
                        </div>
                    </div>
                    ''')
                examples_html = "".join(examples_list)
            
            endpoint_html = f'''
            <div class="endpoint" id="{endpoint_id}">
                <div class="endpoint-header">
                    <span class="method {endpoint.method.lower()}">{endpoint.method}</span>
                    <span class="endpoint-path">{endpoint.path}</span>
                    <button class="try-it" onclick="tryEndpoint('{endpoint.path}', '{endpoint.method}')">
                        🧪 Try it out
                    </button>
                </div>
                <div class="endpoint-body">
                    <div class="section">
                        <h4>📝 Description</h4>
                        <p>{endpoint.description or endpoint.summary or "No description available"}</p>
                    </div>
                    
                    {f'<div class="section"><h4>📋 Parameters</h4>{parameters_html}</div>' if endpoint.parameters else ''}
                    
                    {f'<div class="section"><h4>💡 Examples</h4>{examples_html}</div>' if endpoint.examples else ''}
                </div>
            </div>
            '''
            endpoints_html.append(endpoint_html)
        
        return html_template.format(
            title=documentation.title,
            version=documentation.version,
            description=documentation.description,
            generated_at=documentation.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            base_url=documentation.base_url,
            nav_items="".join(nav_items),
            endpoints_html="".join(endpoints_html)
        )
    
    async def _generate_markdown_docs(self, documentation: APIDocumentation) -> str:
        """Generate Markdown documentation"""
        md_content = f"""# {documentation.title}

**Version:** {documentation.version}  
**Generated:** {documentation.generated_at.strftime("%Y-%m-%d %H:%M:%S")}

{documentation.description}

## Base URL
```
{documentation.base_url}
```

## Authentication
{self._generate_auth_docs(documentation.security)}

## Endpoints

"""
        
        # Group endpoints by tags
        endpoints_by_tag = {}
        for endpoint in documentation.endpoints:
            tags = endpoint.tags or ["General"]
            for tag in tags:
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append(endpoint)
        
        # Generate documentation for each tag
        for tag, endpoints in endpoints_by_tag.items():
            md_content += f"### {tag}\n\n"
            
            for endpoint in endpoints:
                md_content += f"#### {endpoint.method} {endpoint.path}\n\n"
                
                if endpoint.summary:
                    md_content += f"**Summary:** {endpoint.summary}\n\n"
                
                if endpoint.description:
                    md_content += f"{endpoint.description}\n\n"
                
                # Parameters
                if endpoint.parameters:
                    md_content += "**Parameters:**\n\n"
                    md_content += "| Name | Type | Location | Required | Description |\n"
                    md_content += "|------|------|----------|----------|-------------|\n"
                    
                    for param in endpoint.parameters:
                        required = "✅" if param.get("required") else "❌"
                        md_content += f"| {param['name']} | {param.get('type', 'string')} | {param.get('in', 'query')} | {required} | {param.get('description', '')} |\n"
                    
                    md_content += "\n"
                
                # Examples
                if endpoint.examples:
                    md_content += "**Examples:**\n\n"
                    for i, example in enumerate(endpoint.examples, 1):
                        md_content += f"**Example {i}: {example.get('title', 'Request')}**\n\n"
                        
                        if example.get('description'):
                            md_content += f"{example['description']}\n\n"
                        
                        if example.get('request'):
                            md_content += "Request:\n```json\n"
                            md_content += json.dumps(example['request'], indent=2)
                            md_content += "\n```\n\n"
                        
                        if example.get('response'):
                            md_content += "Response:\n```json\n"
                            md_content += json.dumps(example['response'], indent=2)
                            md_content += "\n```\n\n"
                
                md_content += "---\n\n"
        
        return md_content
    
    def _generate_auth_docs(self, security: Dict[str, Any]) -> str:
        """Generate authentication documentation"""
        if not security:
            return "No authentication required."
        
        auth_docs = []
        for scheme_name, scheme_info in security.items():
            scheme_type = scheme_info.get("type", "unknown")
            
            if scheme_type == "http":
                auth_docs.append(f"- **{scheme_name}**: HTTP {scheme_info.get('scheme', 'bearer')} authentication")
            elif scheme_type == "apiKey":
                location = scheme_info.get("in", "header")
                name = scheme_info.get("name", "api_key")
                auth_docs.append(f"- **{scheme_name}**: API Key in {location} ({name})")
            elif scheme_type == "oauth2":
                auth_docs.append(f"- **{scheme_name}**: OAuth 2.0")
        
        return "\n".join(auth_docs) if auth_docs else "Authentication details not specified."
    
    def add_custom_example(self, method: str, path: str, example: Dict[str, Any]):
        """Add custom example for endpoint"""
        endpoint_key = f"{method}:{path}"
        if endpoint_key not in self.custom_examples:
            self.custom_examples[endpoint_key] = []
        self.custom_examples[endpoint_key].append(example)
    
    def add_custom_description(self, method: str, path: str, description: str):
        """Add custom description for endpoint"""
        endpoint_key = f"{method}:{path}"
        self.custom_descriptions[endpoint_key] = description

class InteractiveAPITester:
    """Interactive API testing interface"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_headers = {}
        self.test_results = []
    
    async def test_endpoint(
        self, 
        method: str, 
        path: str, 
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Test an API endpoint"""
        import aiohttp
        
        url = f"{self.base_url}{path}"
        headers = {**self.session_headers, **(headers or {})}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data
                ) as response:
                    
                    response_data = {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "body": await response.text()
                    }
                    
                    # Try to parse JSON
                    try:
                        response_data["json"] = await response.json()
                    except:
                        pass
                    
                    test_result = {
                        "timestamp": datetime.now().isoformat(),
                        "method": method,
                        "url": url,
                        "request_headers": headers,
                        "request_params": params,
                        "request_body": json_data,
                        "response": response_data,
                        "success": 200 <= response.status < 400
                    }
                    
                    self.test_results.append(test_result)
                    return test_result
                    
            except Exception as e:
                error_result = {
                    "timestamp": datetime.now().isoformat(),
                    "method": method,
                    "url": url,
                    "error": str(e),
                    "success": False
                }
                
                self.test_results.append(error_result)
                return error_result
    
    def set_auth_header(self, auth_type: str, token: str):
        """Set authentication header"""
        if auth_type.lower() == "bearer":
            self.session_headers["Authorization"] = f"Bearer {token}"
        elif auth_type.lower() == "api_key":
            self.session_headers["X-API-Key"] = token
        else:
            self.session_headers["Authorization"] = token
    
    def get_test_history(self) -> List[Dict[str, Any]]:
        """Get test history"""
        return self.test_results
    
    def generate_test_report(self) -> str:
        """Generate test report"""
        if not self.test_results:
            return "No tests have been run."
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.get("success"))
        success_rate = (successful_tests / total_tests) * 100
        
        report = f"""# API Test Report

**Total Tests:** {total_tests}  
**Successful:** {successful_tests}  
**Failed:** {total_tests - successful_tests}  
**Success Rate:** {success_rate:.1f}%

## Test Results

"""
        
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            report += f"### Test {i}: {result['method']} {result.get('url', 'N/A')} - {status}\n\n"
            
            if result.get("response"):
                report += f"**Status Code:** {result['response'].get('status')}\n"
                report += f"**Response Time:** {result.get('response_time', 'N/A')}\n\n"
            
            if result.get("error"):
                report += f"**Error:** {result['error']}\n\n"
            
            report += "---\n\n"
        
        return report

# Global instances
doc_generator = APIDocumentationGenerator()
api_tester = InteractiveAPITester("http://localhost:8000")

# Convenience functions
async def generate_api_docs(app: FastAPI, format: str = "html") -> str:
    """Generate API documentation"""
    doc_generator.app = app
    return await doc_generator.generate_documentation(format)

async def test_api_endpoint(method: str, path: str, **kwargs) -> Dict[str, Any]:
    """Test API endpoint"""
    return await api_tester.test_endpoint(method, path, **kwargs)

if __name__ == "__main__":
    # Example usage
    async def test_api_docs():
        print("🧪 Testing API Documentation Generator...")
        
        # This would normally use a real FastAPI app
        # For demo purposes, we'll create a mock structure
        
        # Test API endpoint
        result = await test_api_endpoint(
            "GET", 
            "/api/health",
            headers={"Accept": "application/json"}
        )
        
        print(f"Test result: {result.get('success')}")
        print(f"Status: {result.get('response', {}).get('status')}")
        
        # Generate test report
        report = api_tester.generate_test_report()
        print(f"Test report generated: {len(report)} characters")
    
    asyncio.run(test_api_docs())