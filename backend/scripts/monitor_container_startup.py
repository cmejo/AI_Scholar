#!/usr/bin/env python3
"""
Container Startup Monitoring Script
Monitors container startup process and resource usage in real-time
"""

import time
import subprocess
import json
import threading
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests


class ContainerStartupMonitor:
    """Monitor container startup process and performance"""
    
    def __init__(self, container_name: str = "advanced-rag-backend"):
        self.container_name = container_name
        self.monitoring = False
        self.stats_history = []
        self.health_history = []
        self.start_time = None
        
    def get_container_id(self) -> Optional[str]:
        """Get container ID by name"""
        try:
            result = subprocess.run(
                ["docker", "ps", "-q", "--filter", f"name={self.container_name}"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except:
            return None
    
    def get_container_stats(self, container_id: str) -> Optional[Dict]:
        """Get container resource statistics"""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "json", container_id],
                capture_output=True, text=True, check=True, timeout=5
            )
            stats = json.loads(result.stdout.strip())
            
            # Parse percentages
            cpu_percent = float(stats.get("CPUPerc", "0%").replace("%", ""))
            memory_percent = float(stats.get("MemPerc", "0%").replace("%", ""))
            
            return {
                "timestamp": datetime.now(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_usage": stats.get("MemUsage", "N/A"),
                "network_io": stats.get("NetIO", "N/A"),
                "block_io": stats.get("BlockIO", "N/A"),
                "pids": stats.get("PIDs", "N/A")
            }
        except:
            return None
    
    def check_health_endpoint(self) -> Dict:
        """Check container health endpoint"""
        try:
            start_time = time.time()
            response = requests.get("http://localhost:8000/health", timeout=5)
            response_time = time.time() - start_time
            
            return {
                "timestamp": datetime.now(),
                "status_code": response.status_code,
                "response_time": response_time,
                "healthy": response.status_code == 200
            }
        except Exception as e:
            return {
                "timestamp": datetime.now(),
                "status_code": None,
                "response_time": None,
                "healthy": False,
                "error": str(e)
            }
    
    def monitor_stats(self):
        """Monitor container statistics in background thread"""
        container_id = self.get_container_id()
        if not container_id:
            print("Container not found")
            return
        
        print(f"Monitoring container {container_id[:12]}...")
        
        while self.monitoring:
            stats = self.get_container_stats(container_id)
            if stats:
                self.stats_history.append(stats)
                
                # Keep only last 100 entries
                if len(self.stats_history) > 100:
                    self.stats_history.pop(0)
            
            time.sleep(2)  # Check every 2 seconds
    
    def monitor_health(self):
        """Monitor health endpoint in background thread"""
        while self.monitoring:
            health = self.check_health_endpoint()
            self.health_history.append(health)
            
            # Keep only last 100 entries
            if len(self.health_history) > 100:
                self.health_history.pop(0)
            
            time.sleep(5)  # Check every 5 seconds
    
    def print_status(self):
        """Print current status"""
        if not self.stats_history or not self.health_history:
            return
        
        latest_stats = self.stats_history[-1]
        latest_health = self.health_history[-1]
        
        # Calculate uptime
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        # Clear screen and print status
        print("\033[2J\033[H")  # Clear screen and move cursor to top
        print("=" * 70)
        print(f"CONTAINER STARTUP MONITORING - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70)
        print(f"Container: {self.container_name}")
        print(f"Uptime: {uptime:.1f}s")
        print()
        
        # Resource usage
        print("RESOURCE USAGE:")
        print(f"  CPU: {latest_stats['cpu_percent']:.1f}%")
        print(f"  Memory: {latest_stats['memory_percent']:.1f}%")
        print(f"  Memory Usage: {latest_stats['memory_usage']}")
        print(f"  Network I/O: {latest_stats['network_io']}")
        print(f"  Block I/O: {latest_stats['block_io']}")
        print(f"  PIDs: {latest_stats['pids']}")
        print()
        
        # Health status
        print("HEALTH STATUS:")
        if latest_health['healthy']:
            print(f"  ✓ Healthy (response time: {latest_health['response_time']:.3f}s)")
        else:
            print(f"  ✗ Unhealthy (status: {latest_health.get('status_code', 'N/A')})")
            if 'error' in latest_health:
                print(f"    Error: {latest_health['error']}")
        print()
        
        # Statistics over time
        if len(self.stats_history) > 1:
            cpu_values = [s['cpu_percent'] for s in self.stats_history[-10:]]
            memory_values = [s['memory_percent'] for s in self.stats_history[-10:]]
            
            print("RECENT TRENDS (last 10 samples):")
            print(f"  CPU: avg={sum(cpu_values)/len(cpu_values):.1f}%, max={max(cpu_values):.1f}%")
            print(f"  Memory: avg={sum(memory_values)/len(memory_values):.1f}%, max={max(memory_values):.1f}%")
            print()
        
        # Health check success rate
        if len(self.health_history) > 1:
            recent_health = self.health_history[-10:]
            success_rate = sum(1 for h in recent_health if h['healthy']) / len(recent_health) * 100
            print(f"HEALTH SUCCESS RATE (last 10 checks): {success_rate:.1f}%")
            print()
        
        print("Press Ctrl+C to stop monitoring")
        print("-" * 70)
    
    def start_monitoring(self):
        """Start monitoring container startup"""
        self.monitoring = True
        self.start_time = datetime.now()
        
        # Start background threads
        stats_thread = threading.Thread(target=self.monitor_stats, daemon=True)
        health_thread = threading.Thread(target=self.monitor_health, daemon=True)
        
        stats_thread.start()
        health_thread.start()
        
        # Main monitoring loop
        try:
            while self.monitoring:
                self.print_status()
                time.sleep(3)  # Update display every 3 seconds
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            self.monitoring = False
    
    def generate_report(self):
        """Generate monitoring report"""
        if not self.stats_history or not self.health_history:
            print("No monitoring data available")
            return
        
        print("\n" + "=" * 70)
        print("MONITORING REPORT")
        print("=" * 70)
        
        # Time range
        start_time = min(self.stats_history[0]['timestamp'], self.health_history[0]['timestamp'])
        end_time = max(self.stats_history[-1]['timestamp'], self.health_history[-1]['timestamp'])
        duration = (end_time - start_time).total_seconds()
        
        print(f"Monitoring Duration: {duration:.1f} seconds")
        print(f"Stats Samples: {len(self.stats_history)}")
        print(f"Health Samples: {len(self.health_history)}")
        print()
        
        # Resource statistics
        cpu_values = [s['cpu_percent'] for s in self.stats_history]
        memory_values = [s['memory_percent'] for s in self.stats_history]
        
        print("RESOURCE USAGE STATISTICS:")
        print(f"  CPU - Min: {min(cpu_values):.1f}%, Max: {max(cpu_values):.1f}%, Avg: {sum(cpu_values)/len(cpu_values):.1f}%")
        print(f"  Memory - Min: {min(memory_values):.1f}%, Max: {max(memory_values):.1f}%, Avg: {sum(memory_values)/len(memory_values):.1f}%")
        print()
        
        # Health statistics
        healthy_checks = sum(1 for h in self.health_history if h['healthy'])
        health_success_rate = (healthy_checks / len(self.health_history)) * 100
        
        response_times = [h['response_time'] for h in self.health_history if h['response_time'] is not None]
        
        print("HEALTH CHECK STATISTICS:")
        print(f"  Success Rate: {health_success_rate:.1f}% ({healthy_checks}/{len(self.health_history)})")
        if response_times:
            print(f"  Response Time - Min: {min(response_times):.3f}s, Max: {max(response_times):.3f}s, Avg: {sum(response_times)/len(response_times):.3f}s")
        print()
        
        # Assessment
        print("ASSESSMENT:")
        if health_success_rate >= 95:
            print("  ✓ Excellent health check reliability")
        elif health_success_rate >= 80:
            print("  ⚠ Good health check reliability")
        else:
            print("  ✗ Poor health check reliability")
        
        avg_cpu = sum(cpu_values) / len(cpu_values)
        avg_memory = sum(memory_values) / len(memory_values)
        
        if avg_cpu < 30 and avg_memory < 50:
            print("  ✓ Low resource usage")
        elif avg_cpu < 60 and avg_memory < 75:
            print("  ⚠ Moderate resource usage")
        else:
            print("  ✗ High resource usage")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down monitor...")
    sys.exit(0)


def main():
    """Main monitoring function"""
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Container Startup Monitor")
    print("=" * 70)
    
    monitor = ContainerStartupMonitor()
    
    # Check if container exists
    container_id = monitor.get_container_id()
    if not container_id:
        print(f"Container '{monitor.container_name}' not found")
        print("Make sure the container is running")
        return
    
    print(f"Found container: {container_id[:12]}")
    print("Starting monitoring...")
    print()
    
    try:
        monitor.start_monitoring()
    finally:
        monitor.generate_report()


if __name__ == "__main__":
    main()