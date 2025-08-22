import subprocess
import threading
import time
import requests
import json
from datetime import datetime
import psutil
import os
import signal

class AgenticFlaskOrchestrator:
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Define your Flask applications
        self.applications = {
            'inventory_dashboard': {
                'name': 'Inventory Management Dashboard',
                'script_path': 'main.py',  # Your first Flask app
                'port': 5000,
                'working_directory': '.',
                'health_endpoint': '/api/stats',
                'process': None,
                'status': 'stopped',
                'auto_restart': True,
                'priority': 1
            },
            'analytics_engine': {
                'name': 'Inventra AI Analytics Engine', 
                'script_path': './dataanalysis/app.py',  # Your second Flask app
                'port': 5001,
                'working_directory': '.',
                'health_endpoint': '/',
                'process': None,
                'status': 'stopped',
                'auto_restart': True,
                'priority': 2
            }
        }
        
        print("🤖 Agentic Flask Orchestrator initialized")
        print("Available applications:", list(self.applications.keys()))

    def analyze_startup_strategy(self, user_request="Start all applications"):
        """Simple startup strategy without AI dependency"""
        
        print("🧠 Analyzing startup strategy...")
        
        # Simple rule-based strategy
        strategy = {
            "startup_order": ["inventory_dashboard", "analytics_engine"],  # Start dashboard first
            "reasoning": "Starting inventory dashboard first (port 5000) as primary system, then analytics engine (port 5001)",
            "health_check_interval": 30,
            "restart_strategy": "immediate",
            "resource_allocation": "Sequential startup to avoid port conflicts"
        }
        
        return strategy

    def start_application(self, app_id):
        """Autonomously start a Flask application"""
        
        if app_id not in self.applications:
            print(f"❌ Unknown application: {app_id}")
            return False
            
        config = self.applications[app_id]
        
        if config['status'] == 'running':
            print(f"✅ {config['name']} is already running on port {config['port']}")
            return True
            
        try:
            print(f"🚀 Starting {config['name']} on port {config['port']}...")
            
            # Prepare environment variables
            env = os.environ.copy()
            env['FLASK_RUN_PORT'] = str(config['port'])
            env['FLASK_ENV'] = 'development'
            
            # Start the application
            process = subprocess.Popen(
                ['python', config['script_path']],
                cwd=config['working_directory'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for startup
            print("⏳ Waiting for application to start...")
            time.sleep(8)  # Increased wait time
            
            # Verify the process is running
            if process.poll() is None:
                config['process'] = process
                config['status'] = 'running'
                
                # Check if server is responding
                print(f"🔍 Checking if server is responding on port {config['port']}...")
                server_responding = False
                
                for attempt in range(10):  # Try for 10 seconds
                    try:
                        response = requests.get(f"http://localhost:{config['port']}", timeout=2)
                        if response.status_code in [200, 404, 302, 500]:  # Any HTTP response means server is up
                            server_responding = True
                            break
                    except requests.exceptions.RequestException:
                        pass
                    time.sleep(1)
                
                if server_responding:
                    print(f"✅ {config['name']} started successfully!")
                    print(f"🌐 Server is LIVE on http://localhost:{config['port']}")
                    return True
                else:
                    print(f"⚠️ {config['name']} process started but server not responding yet")
                    print(f"🌐 Server should be LIVE on http://localhost:{config['port']} (may take a moment)")
                    return True  # Process started
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Failed to start {config['name']}")
                print(f"Error: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Exception starting {app_id}: {str(e)}")
            return False

    def stop_application(self, app_id):
        """Stop a running Flask application"""
        
        if app_id not in self.applications:
            return False
            
        config = self.applications[app_id]
        
        if config['status'] == 'stopped':
            print(f"ℹ️ {config['name']} is already stopped")
            return True
            
        try:
            if config['process']:
                print(f"🛑 Stopping {config['name']}...")
                
                # Try graceful shutdown first
                config['process'].terminate()
                
                # Wait for graceful shutdown
                try:
                    config['process'].wait(timeout=10)
                    print(f"✅ {config['name']} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    print(f"⚡ Force stopping {config['name']}...")
                    config['process'].kill()
                    config['process'].wait()
                    print(f"✅ {config['name']} stopped forcefully")
                
                config['process'] = None
                config['status'] = 'stopped'
                return True
                
        except Exception as e:
            print(f"❌ Error stopping {app_id}: {str(e)}")
            return False

    def health_check(self, app_id):
        """Check application health"""
        
        config = self.applications[app_id]
        
        if config['status'] != 'running':
            return False
            
        try:
            url = f"http://localhost:{config['port']}{config['health_endpoint']}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def autonomous_monitoring(self):
        """Continuously monitor all applications and restart if needed"""
        
        print("🔍 Starting autonomous monitoring system...")
        monitor_count = 0
        
        while self.is_monitoring:
            monitor_count += 1
            
            # Print monitoring status every 10 cycles (5 minutes)
            if monitor_count % 10 == 0:
                print(f"🔄 Monitoring cycle #{monitor_count} - Checking all systems...")
            
            for app_id, config in self.applications.items():
                if config['status'] == 'running':
                    
                    # Check if process is still alive
                    if config['process'] and config['process'].poll() is not None:
                        print(f"💀 {config['name']} process died unexpectedly")
                        config['status'] = 'stopped'
                        config['process'] = None
                        
                        if config['auto_restart']:
                            print(f"🔄 Auto-restarting {config['name']}...")
                            time.sleep(3)
                            self.start_application(app_id)
                    
                    # Basic connectivity check
                    elif monitor_count % 5 == 0:  # Every 5th cycle
                        try:
                            response = requests.get(f"http://localhost:{config['port']}", timeout=3)
                            print(f"💚 {config['name']} - Server LIVE on port {config['port']}")
                        except:
                            print(f"⚠️ {config['name']} - Server not responding on port {config['port']}")
                            
                            if config['auto_restart']:
                                print(f"🔄 Restarting unresponsive application {config['name']}...")
                                self.stop_application(app_id)
                                time.sleep(3)
                                self.start_application(app_id)
                            
            time.sleep(30)  # Monitor every 30 seconds

    def start_monitoring(self):
        """Start the autonomous monitoring system"""
        
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self.autonomous_monitoring)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            print("✅ Autonomous monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring system"""
        
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            print("🛑 Autonomous monitoring stopped")

    def get_system_status(self):
        """Get comprehensive system status"""
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'monitoring_active': self.is_monitoring,
            'applications': {}
        }
        
        for app_id, config in self.applications.items():
            app_status = {
                'name': config['name'],
                'status': config['status'],
                'port': config['port'],
                'health_check': self.health_check(app_id) if config['status'] == 'running' else False,
                'auto_restart': config['auto_restart']
            }
            
            if config['process']:
                try:
                    process = psutil.Process(config['process'].pid)
                    app_status.update({
                        'cpu_usage': f"{process.cpu_percent():.1f}%",
                        'memory_usage': f"{process.memory_info().rss / 1024 / 1024:.1f} MB",
                        'uptime': str(datetime.now() - datetime.fromtimestamp(process.create_time()))
                    })
                except:
                    app_status.update({
                        'cpu_usage': 'N/A',
                        'memory_usage': 'N/A', 
                        'uptime': 'N/A'
                    })
            
            status['applications'][app_id] = app_status
            
        return status

    def execute_agentic_startup(self, user_request="Start all applications"):
        """Main agentic function to start applications intelligently"""
        
        print("🤖 Agentic Flask Orchestrator executing startup sequence...")
        
        # Step 1: Analyze strategy (without AI dependency)
        strategy = self.analyze_startup_strategy(user_request)
        print(f"📋 Strategy: {strategy['reasoning']}")
        
        # Step 2: Execute startup in determined order
        startup_results = []
        for i, app_id in enumerate(strategy['startup_order'], 1):
            print(f"\n[{i}/{len(strategy['startup_order'])}] Processing: {self.applications[app_id]['name']}")
            result = self.start_application(app_id)
            startup_results.append({
                'app_id': app_id,
                'name': self.applications[app_id]['name'],
                'success': result,
                'port': self.applications[app_id]['port']
            })
            
            # Wait between startups to avoid resource conflicts
            if result and i < len(strategy['startup_order']):
                print("⏳ Waiting before starting next application...")
                time.sleep(4)
        
        # Step 3: Start autonomous monitoring
        self.start_monitoring()
        
        # Step 4: Generate final report
        self.print_status_report()
        
        return startup_results

    def print_status_report(self):
        """Print a comprehensive status report"""
        
        print("\n" + "="*80)
        print("🤖 AGENTIC FLASK ORCHESTRATOR STATUS REPORT")
        print("="*80)
        
        status = self.get_system_status()
        
        print(f"📊 System Status: {'🟢 Active' if self.is_monitoring else '🔴 Inactive'}")
        print(f"🕐 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Monitoring: {'✅ Active' if status['monitoring_active'] else '❌ Inactive'}")
        
        print(f"\n📱 APPLICATIONS STATUS:")
        print("-" * 80)
        
        running_count = 0
        for app_id, app_info in status['applications'].items():
            status_icon = "🟢" if app_info['status'] == 'running' else "🔴"
            
            print(f"{status_icon} {app_info['name']}")
            print(f"   📍 Port: {app_info['port']}")
            print(f"   📊 Status: {app_info['status'].upper()}")
            
            if app_info['status'] == 'running':
                running_count += 1
                # Check server responsiveness
                try:
                    response = requests.get(f"http://localhost:{app_info['port']}", timeout=2)
                    print(f"   🌐 Server: 🟢 LIVE on http://localhost:{app_info['port']}")
                except:
                    print(f"   🌐 Server: 🟡 Starting on http://localhost:{app_info['port']}")
                
                print(f"   💾 CPU: {app_info.get('cpu_usage', 'N/A')}")
                print(f"   🧠 Memory: {app_info.get('memory_usage', 'N/A')}")
                print(f"   ⏰ Uptime: {app_info.get('uptime', 'N/A')}")
            else:
                print(f"   🌐 Server: 🔴 OFFLINE")
            
            print(f"   🔄 Auto Restart: {'✅ Enabled' if app_info['auto_restart'] else '❌ Disabled'}")
            print()
        
        print("🌐 LIVE SERVERS:")
        print("-" * 80)
        live_servers = []
        for app_id, config in self.applications.items():
            if self.applications[app_id]['status'] == 'running':
                live_servers.append(f"🔗 {config['name']}: http://localhost:{config['port']}")
        
        if live_servers:
            for server in live_servers:
                print(server)
        else:
            print("⚠️  No servers are currently running")
        
        print(f"\n📈 SUMMARY: {running_count}/{len(self.applications)} applications running")
        
        if running_count == len(self.applications):
            print("🎉 ALL SYSTEMS OPERATIONAL!")
            print("🚀 Both Flask servers are LIVE:")
            print("   📊 Dashboard: http://localhost:5000")
            print("   🤖 Analytics: http://localhost:5001")
        elif running_count > 0:
            print(f"⚠️  Partial system operation ({running_count}/{len(self.applications)} apps)")
        else:
            print("🔴 No applications running")
        
        print("="*80)

    def shutdown_all(self):
        """Gracefully shutdown all applications"""
        
        print("\n🛑 Initiating graceful shutdown of all applications...")
        
        self.stop_monitoring()
        
        for app_id in self.applications.keys():
            self.stop_application(app_id)
        
        print("✅ All applications stopped successfully")
        print("🌐 Servers on ports 5000 and 5001 are now OFFLINE")

# Main execution
if __name__ == '__main__':
    orchestrator = AgenticFlaskOrchestrator()
    
    try:
        print("🤖 AGENTIC FLASK ORCHESTRATOR")
        print("="*50)
        print("🎯 Goal: Start both Flask applications")
        print("📊 Target: Dashboard on port 5000")
        print("🤖 Target: Analytics on port 5001")
        print()
        
        # Start all applications using agentic strategy
        results = orchestrator.execute_agentic_startup("Start both Flask applications for development")
        
        print(f"\n🎯 STARTUP RESULTS:")
        print("-" * 50)
        success_count = 0
        
        for result in results:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            if result['success']:
                success_count += 1
                print(f"{status} | {result['name']}")
                print(f"         🌐 LIVE on http://localhost:{result['port']}")
            else:
                print(f"{status} | {result['name']}")
                print(f"         🔴 OFFLINE on port {result['port']}")
            print()
        
        if success_count == len(results):
            print("🎉 ALL APPLICATIONS STARTED SUCCESSFULLY!")
            print("🌐 Flask servers are LIVE on ports 5000 and 5001")
        else:
            print(f"⚠️  {success_count}/{len(results)} applications started successfully")
        
        print(f"\n🔄 System is now under autonomous monitoring...")
        print(f"💡 Applications will auto-restart if they fail")
        print(f"🛑 Press Ctrl+C to stop all applications")
        print(f"🔍 Status updates will appear every few minutes...")
        print()
        
        # Keep the orchestrator running with periodic status
        while True:
            time.sleep(180)  # Print status every 3 minutes
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"\n🔄 System Status Check: {current_time}")
            
            running_count = 0
            for app_id, config in orchestrator.applications.items():
                if config['status'] == 'running':
                    running_count += 1
                    try:
                        requests.get(f"http://localhost:{config['port']}", timeout=2)
                        print(f"  🟢 {config['name']}: LIVE on port {config['port']}")
                    except:
                        print(f"  🟡 {config['name']}: Starting on port {config['port']}")
                else:
                    print(f"  🔴 {config['name']}: OFFLINE on port {config['port']}")
            
            print(f"📊 Status: {running_count}/{len(orchestrator.applications)} servers running")
            
    except KeyboardInterrupt:
        print(f"\n🛑 Shutdown signal received...")
        orchestrator.shutdown_all()
        print("👋 Agentic Flask Orchestrator terminated")
