#!/usr/bin/env python3
"""
Performance Monitoring Tool for AI Scholar
"""
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

class PerformanceMonitor:
    """Monitor application performance"""
    
    def __init__(self):
        self.metrics = {}
    
    def collect_system_metrics(self) -> Dict:
        """Collect system performance metrics"""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "available_memory_gb": psutil.virtual_memory().available / (1024**3),
                "timestamp": time.time()
            }
        except ImportError:
            return {
                "error": "psutil not installed - run: pip install psutil",
                "timestamp": time.time()
            }
    
    def monitor_bundle_size(self) -> Dict:
        """Monitor frontend bundle size"""
        dist_dir = Path("dist")
        if not dist_dir.exists():
            return {"error": "No dist directory found - run: npm run build"}
        
        files = {}
        total_size = 0
        
        for file_path in dist_dir.rglob('*'):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                files[str(file_path)] = size
        
        total_size_mb = total_size / (1024 * 1024)
        target_size_mb = 1.5
        
        return {
            "total_size_mb": round(total_size_mb, 2),
            "target_size_mb": target_size_mb,
            "meets_target": total_size_mb <= target_size_mb,
            "improvement_needed_mb": max(0, total_size_mb - target_size_mb),
            "file_count": len(files),
            "largest_files": self._get_largest_files(files, 5)
        }
    
    def _get_largest_files(self, files: Dict[str, int], count: int) -> List[Dict]:
        """Get the largest files"""
        sorted_files = sorted(files.items(), key=lambda x: x[1], reverse=True)
        return [
            {"file": file_path, "size_mb": round(size / (1024 * 1024), 2)}
            for file_path, size in sorted_files[:count]
        ]
    
    def analyze_dependencies(self) -> Dict:
        """Analyze dependency performance impact"""
        package_json = Path("package.json")
        if not package_json.exists():
            return {"error": "No package.json found"}
        
        try:
            with open(package_json) as f:
                package_data = json.load(f)
            
            deps = package_data.get("dependencies", {})
            dev_deps = package_data.get("devDependencies", {})
            
            # Check for heavy dependencies
            heavy_deps = []
            known_heavy = ["react", "react-dom", "lodash", "moment", "antd", "material-ui"]
            
            for dep in deps:
                if any(heavy in dep for heavy in known_heavy):
                    heavy_deps.append(dep)
            
            return {
                "total_dependencies": len(deps),
                "dev_dependencies": len(dev_deps),
                "heavy_dependencies": heavy_deps,
                "recommendations": self._get_dependency_recommendations(heavy_deps)
            }
        except Exception as e:
            return {"error": f"Failed to analyze dependencies: {e}"}
    
    def _get_dependency_recommendations(self, heavy_deps: List[str]) -> List[str]:
        """Get recommendations for dependency optimization"""
        recommendations = []
        
        if "lodash" in heavy_deps:
            recommendations.append("Consider using lodash-es for better tree shaking")
        
        if "moment" in heavy_deps:
            recommendations.append("Consider replacing moment with date-fns for smaller bundle size")
        
        if len(heavy_deps) > 3:
            recommendations.append("Consider code splitting for heavy dependencies")
        
        return recommendations or ["Dependencies look optimized"]
    
    def check_build_performance(self) -> Dict:
        """Check build performance"""
        try:
            print("🔨 Running build performance test...")
            start_time = time.time()
            
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            build_time = time.time() - start_time
            
            return {
                "build_time_seconds": round(build_time, 2),
                "build_success": result.returncode == 0,
                "target_time_seconds": 120,  # 2 minutes target
                "meets_target": build_time <= 120,
                "error": result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                "error": "Build timed out after 5 minutes",
                "build_success": False
            }
        except Exception as e:
            return {
                "error": f"Build test failed: {e}",
                "build_success": False
            }
    
    def analyze_test_performance(self) -> Dict:
        """Analyze test suite performance"""
        try:
            print("🧪 Running test performance analysis...")
            start_time = time.time()
            
            # Try to run a quick test
            result = subprocess.run(
                ["python3", "-m", "pytest", "--tb=no", "-q", "--maxfail=1"],
                cwd="backend" if Path("backend").exists() else ".",
                capture_output=True,
                text=True,
                timeout=60
            )
            
            test_time = time.time() - start_time
            
            return {
                "test_time_seconds": round(test_time, 2),
                "tests_passed": result.returncode == 0,
                "target_time_seconds": 30,
                "meets_target": test_time <= 30,
                "recommendation": "Consider parallel test execution" if test_time > 30 else "Test performance is good"
            }
        except subprocess.TimeoutExpired:
            return {
                "error": "Tests timed out after 60 seconds",
                "recommendation": "Tests are too slow - consider optimization"
            }
        except Exception as e:
            return {
                "error": f"Test analysis failed: {e}",
                "recommendation": "Fix test setup issues"
            }
    
    def generate_report(self) -> str:
        """Generate comprehensive performance report"""
        print("📊 Generating performance report...")
        
        system_metrics = self.collect_system_metrics()
        bundle_metrics = self.monitor_bundle_size()
        dependency_metrics = self.analyze_dependencies()
        build_metrics = self.check_build_performance()
        test_metrics = self.analyze_test_performance()
        
        report = {
            "timestamp": time.time(),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system": system_metrics,
            "bundle": bundle_metrics,
            "dependencies": dependency_metrics,
            "build": build_metrics,
            "tests": test_metrics,
            "overall_score": self._calculate_overall_score(
                bundle_metrics, build_metrics, test_metrics
            )
        }
        
        return json.dumps(report, indent=2)
    
    def _calculate_overall_score(self, bundle_metrics: Dict, build_metrics: Dict, test_metrics: Dict) -> Dict:
        """Calculate overall performance score"""
        score = 10.0
        issues = []
        
        # Bundle size scoring
        if bundle_metrics.get("meets_target"):
            bundle_score = 10
        else:
            improvement_needed = bundle_metrics.get("improvement_needed_mb", 0)
            bundle_score = max(5, 10 - improvement_needed * 2)
            issues.append(f"Bundle size exceeds target by {improvement_needed:.1f}MB")
        
        # Build time scoring
        if build_metrics.get("meets_target"):
            build_score = 10
        elif build_metrics.get("build_success"):
            build_time = build_metrics.get("build_time_seconds", 0)
            build_score = max(5, 10 - (build_time - 120) / 30)
            issues.append(f"Build time is {build_time:.1f}s (target: 120s)")
        else:
            build_score = 0
            issues.append("Build failed")
        
        # Test performance scoring
        if test_metrics.get("meets_target"):
            test_score = 10
        elif not test_metrics.get("error"):
            test_time = test_metrics.get("test_time_seconds", 0)
            test_score = max(5, 10 - (test_time - 30) / 10)
            issues.append(f"Test time is {test_time:.1f}s (target: 30s)")
        else:
            test_score = 5
            issues.append("Test analysis had issues")
        
        overall_score = (bundle_score + build_score + test_score) / 3
        
        return {
            "overall_score": round(overall_score, 1),
            "bundle_score": round(bundle_score, 1),
            "build_score": round(build_score, 1),
            "test_score": round(test_score, 1),
            "grade": self._get_grade(overall_score),
            "issues": issues
        }
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 9:
            return "A+"
        elif score >= 8:
            return "A"
        elif score >= 7:
            return "B"
        elif score >= 6:
            return "C"
        elif score >= 5:
            return "D"
        else:
            return "F"
    
    def generate_markdown_report(self) -> str:
        """Generate markdown performance report"""
        report_data = json.loads(self.generate_report())
        
        md = "# Performance Report\n\n"
        md += f"**Generated:** {report_data['generated_at']}\n\n"
        
        # Overall score
        overall = report_data['overall_score']
        md += f"## Overall Performance: {overall['grade']} ({overall['overall_score']}/10)\n\n"
        
        if overall['issues']:
            md += "### Issues Found\n"
            for issue in overall['issues']:
                md += f"- {issue}\n"
            md += "\n"
        
        # Bundle analysis
        bundle = report_data['bundle']
        if not bundle.get('error'):
            md += "## Bundle Analysis\n"
            md += f"- **Size:** {bundle['total_size_mb']}MB (target: {bundle['target_size_mb']}MB)\n"
            md += f"- **Status:** {'✅ Meets target' if bundle['meets_target'] else '❌ Exceeds target'}\n"
            md += f"- **Files:** {bundle['file_count']}\n\n"
            
            if bundle.get('largest_files'):
                md += "### Largest Files\n"
                for file_info in bundle['largest_files']:
                    md += f"- {file_info['file']}: {file_info['size_mb']}MB\n"
                md += "\n"
        
        # Build performance
        build = report_data['build']
        if not build.get('error'):
            md += "## Build Performance\n"
            md += f"- **Time:** {build['build_time_seconds']}s (target: {build['target_time_seconds']}s)\n"
            md += f"- **Status:** {'✅ Meets target' if build['meets_target'] else '❌ Exceeds target'}\n\n"
        
        # Test performance
        test = report_data['tests']
        if not test.get('error'):
            md += "## Test Performance\n"
            md += f"- **Time:** {test['test_time_seconds']}s (target: {test['target_time_seconds']}s)\n"
            md += f"- **Status:** {'✅ Meets target' if test['meets_target'] else '❌ Exceeds target'}\n"
            md += f"- **Recommendation:** {test['recommendation']}\n\n"
        
        return md

def main():
    monitor = PerformanceMonitor()
    
    # Generate JSON report
    report = monitor.generate_report()
    report_file = Path("performance_report.json")
    report_file.write_text(report)
    
    # Generate Markdown report
    md_report = monitor.generate_markdown_report()
    md_file = Path("performance_report.md")
    md_file.write_text(md_report)
    
    print(f"📊 Performance reports saved:")
    print(f"  JSON: {report_file}")
    print(f"  Markdown: {md_file}")
    
    # Print summary
    report_data = json.loads(report)
    overall = report_data['overall_score']
    print(f"\n🎯 Overall Performance: {overall['grade']} ({overall['overall_score']}/10)")
    
    if overall['issues']:
        print("\n⚠️  Issues to address:")
        for issue in overall['issues']:
            print(f"  - {issue}")
    
    return report_data

if __name__ == "__main__":
    main()