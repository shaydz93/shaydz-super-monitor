import threading
import time
from ai_monitor import SelfLearningMonitor
from display import EPDDisplay
from web_ui import run_admin_ui

monitor = SelfLearningMonitor(window=60)
display = EPDDisplay()

# Show welcome logo at startup (optional)
# display.show_shaydz_welcome()

web_thread = threading.Thread(target=run_admin_ui, args=(monitor,), daemon=True)
web_thread.start()

while True:
    monitor.update()
    monitor.learn_baseline()
    status = monitor.status_report()
    anomalies, has_anomaly = monitor.detect_anomaly()
    lines = status + anomalies[:3]
    display.display_text(lines)
    if has_anomaly:
        monitor.trigger_action(anomalies)
    monitor.save_baseline()
    time.sleep(5)
