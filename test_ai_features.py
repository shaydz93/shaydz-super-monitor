"""
Enhanced Test Script for S h a y d Z Super Monitor with AI Features

Run with: python3 test_ai_features.py
"""

def test_ai_monitor():
    print("Testing AI-enhanced monitor...")
    try:
        from ai_monitor import SelfLearningMonitor
        monitor = SelfLearningMonitor(window=5)
        
        # Test basic functionality
        monitor.update()
        monitor.learn_baseline()
        report = monitor.status_report()
        
        # Test AI configuration
        ai_status = monitor.get_ai_status()
        print(f"  AI Status: {ai_status}")
        
        # Test AI config updates
        monitor.update_ai_config(ai_enabled=True, use_cloud_ai=False, learning_enabled=True)
        print("  AI configuration updated")
        
        # Test enhanced anomaly detection
        anomalies, flag = monitor.enhanced_anomaly_detection()
        print(f"  Enhanced anomalies: {anomalies}")
        
        # Test AI insights
        insights = monitor.get_ai_insights()
        print(f"  AI insights: {insights}")
        
        # Test false positive marking
        monitor.mark_false_positive("cpu", 50.0, "test context")
        print("  False positive marked")
        
        assert isinstance(report, list)
        assert isinstance(anomalies, list)
        assert isinstance(ai_status, dict)
        print("  ai_monitor.py with AI features: OK")
        
    except Exception as e:
        print(f"  ai_monitor.py AI features: ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_ai_config():
    print("Testing AI configuration...")
    try:
        from ai_monitor import SelfLearningMonitor
        monitor = SelfLearningMonitor(window=5)
        
        # Test configuration loading
        config = monitor.load_ai_config()
        print(f"  Default config: {config}")
        
        # Test configuration updates
        monitor.update_ai_config(
            ai_enabled=True,
            use_cloud_ai=False,
            learning_enabled=True,
            pattern_analysis=True
        )
        
        new_config = monitor.load_ai_config()
        assert new_config["ai_enabled"] == True
        assert new_config["use_cloud_ai"] == False
        assert new_config["learning_enabled"] == True
        
        print("  AI configuration: OK")
        
    except Exception as e:
        print(f"  AI configuration: ERROR: {e}")

def test_pattern_analysis():
    print("Testing pattern analysis...")
    try:
        from ai_monitor import SelfLearningMonitor
        monitor = SelfLearningMonitor(window=5)
        
        # Enable AI features
        monitor.update_ai_config(ai_enabled=True, pattern_analysis=True)
        
        # Generate some test data
        for i in range(10):
            monitor.update()
            monitor.learn_baseline()
        
        # Test local pattern analysis
        metrics_data = {"cpu": 50.0, "ram": 60.0, "timestamp": 1234567890}
        patterns = monitor.analyze_pattern_locally(metrics_data)
        print(f"  Local patterns: {patterns}")
        
        # Test pattern history
        print(f"  Pattern history length: {len(monitor.pattern_history)}")
        
        print("  Pattern analysis: OK")
        
    except Exception as e:
        print(f"  Pattern analysis: ERROR: {e}")

def test_web_ui_ai():
    print("Testing AI web UI features...")
    try:
        import web_ui
        
        # Test that AI templates are defined
        assert hasattr(web_ui, 'TEMPLATE_AI_DASHBOARD')
        assert hasattr(web_ui, 'TEMPLATE_SETTINGS')
        
        # Test template content
        assert "AI Configuration" in web_ui.TEMPLATE_SETTINGS
        assert "AI Dashboard" in web_ui.TEMPLATE_AI_DASHBOARD
        
        print("  AI web UI templates: OK")
        
    except Exception as e:
        print(f"  AI web UI: ERROR: {e}")

def test_ai_learning():
    print("Testing AI learning features...")
    try:
        from ai_monitor import SelfLearningMonitor
        monitor = SelfLearningMonitor(window=5)
        
        # Enable learning
        monitor.update_ai_config(ai_enabled=True, learning_enabled=True)
        
        # Generate some data for learning
        for i in range(25):  # Need enough data for learning
            monitor.update()
            monitor.learn_baseline()
        
        # Test learning from patterns
        monitor.learn_from_patterns()
        
        # Test AI learning data
        learning_data = monitor.ai_learning_data
        print(f"  Learning data: {learning_data}")
        
        # Test saving/loading learning data
        monitor.save_ai_learning()
        monitor.load_ai_learning()
        
        print("  AI learning: OK")
        
    except Exception as e:
        print(f"  AI learning: ERROR: {e}")

def test_privacy_mode():
    print("Testing privacy mode...")
    try:
        from ai_monitor import SelfLearningMonitor
        monitor = SelfLearningMonitor(window=5)
        
        # Test local mode (privacy mode)
        monitor.update_ai_config(ai_enabled=True, use_cloud_ai=False)
        
        # Should work without API key
        anomalies, _ = monitor.enhanced_anomaly_detection()
        insights = monitor.get_ai_insights()
        
        print(f"  Local mode anomalies: {len(anomalies)}")
        print(f"  Local mode insights: {len(insights)}")
        
        # Test cloud mode (should work without API key but not call external API)
        monitor.update_ai_config(use_cloud_ai=True, api_key="")
        
        # Should fall back to local analysis
        anomalies, _ = monitor.enhanced_anomaly_detection()
        print(f"  Cloud mode fallback anomalies: {len(anomalies)}")
        
        print("  Privacy mode: OK")
        
    except Exception as e:
        print(f"  Privacy mode: ERROR: {e}")

if __name__ == "__main__":
    print("=== S h a y d Z Super Monitor AI Features Test Suite ===")
    test_ai_monitor()
    test_ai_config()
    test_pattern_analysis()
    test_web_ui_ai()
    test_ai_learning()
    test_privacy_mode()
    print("=== All AI tests complete ===")
