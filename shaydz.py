import threading
import time
import signal
import sys
from ai_monitor import SelfLearningMonitor
from display import EPDDisplay
from web_ui import run_admin_ui

# Global variables for graceful shutdown
shutdown_event = threading.Event()
monitor = None
display = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    shutdown_event.set()
    if display:
        display.sleep()
    sys.exit(0)

def main():
    global monitor, display
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    monitor = SelfLearningMonitor(window=60)
    display = EPDDisplay()

    # Show welcome logo at startup (optional)
    # display.show_shaydz_welcome()

    web_thread = threading.Thread(target=run_admin_ui, args=(monitor,), daemon=True)
    web_thread.start()

    try:
        while not shutdown_event.is_set():
            monitor.update()
            monitor.learn_baseline()
            status = monitor.status_report()
            
            # Use enhanced anomaly detection if AI is enabled
            if hasattr(monitor, 'enhanced_anomaly_detection') and monitor.ai_config.get("ai_enabled", False):
                anomalies, has_anomaly = monitor.enhanced_anomaly_detection()
            else:
                anomalies, has_anomaly = monitor.detect_anomaly()
            
            lines = status + anomalies[:3]
            display.display_text(lines)
            
            if has_anomaly:
                monitor.trigger_action(anomalies)
            
            monitor.save_baseline()
            
            # Save AI learning data periodically
            if hasattr(monitor, 'save_ai_learning'):
                monitor.save_ai_learning()
            
            # Use wait instead of sleep to allow for graceful shutdown
            if shutdown_event.wait(timeout=5):
                break
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if display:
            display.sleep()

if __name__ == "__main__":
    main()
