"""Global state management for API endpoints."""

_global_monitor = None

def get_monitor():
    """Get or create the global monitor instance."""
    global _global_monitor
    
    if _global_monitor is None:
        from monitor import PKMMonitor
        from utils import load_config
        from config import get_project_root
        import os
        
        config = load_config(os.path.join(get_project_root(), 'config', 'config.yaml'))
        _global_monitor = PKMMonitor(
            base_url=config.get('base_url', 'https://shde.pkm.gov.gr'),
            urls=config.get('urls', {}),
            api_params=config.get('api_params', {}),
            login_params=config.get('login_params', {}),
            check_interval=config.get('check_interval', 300),
            username=config.get('username'),
            password=config.get('password'),
            session_cookies=config.get('session_cookies')
        )
        
        # Try to login
        if not _global_monitor.login():
            print("[WARNING] Failed to login monitor in get_monitor()")
    
    return _global_monitor
