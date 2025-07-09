"""
Test Script for S h a y d Z Super Monitor Modules

Run with: python3 test_shaydz.py
"""

def test_ai_monitor():
    print("Testing ai_monitor...")
    try:
        from ai_monitor import SelfLearningMonitor
        monitor = SelfLearningMonitor(window=5)
        monitor.update()
        monitor.learn_baseline()
        report = monitor.status_report()
        anomalies, flag = monitor.detect_anomaly()
        print("  Status:", report)
        print("  Anomalies:", anomalies)
        assert isinstance(report, list)
        assert isinstance(anomalies, list)
        print("  ai_monitor.py: OK")
    except Exception as e:
        print("  ai_monitor.py: ERROR:", e)

def test_display():
    print("Testing display...")
    try:
        from display import EPDDisplay
        display = EPDDisplay()
        display.display_text(["Test 1", "Test 2", "Test 3"])
        display.show_shaydz_welcome()
        print("  display.py: OK (if not on Pi, simulated output is fine)")
    except Exception as e:
        print("  display.py: ERROR:", e)

def test_threat_intel():
    print("Testing threat_intel...")
    try:
        from threat_intel import ThreatIntelAggregator
        agg = ThreatIntelAggregator()
        data = agg.fetch_all()
        print("  Feeds:", list(data.keys()))
        assert isinstance(data, dict)
        print("  threat_intel.py: OK")
    except Exception as e:
        print("  threat_intel.py: ERROR:", e)

def test_web_ui():
    print("Testing web_ui (import only)...")
    try:
        import web_ui
        print("  web_ui.py: OK (full Flask test requires running app)")
    except Exception as e:
        print("  web_ui.py: ERROR:", e)

if __name__ == "__main__":
    print("=== S h a y d Z Super Monitor Test Suite ===")
    test_ai_monitor()
    test_display()
    test_threat_intel()
    test_web_ui()
    print("=== All tests complete ===")
