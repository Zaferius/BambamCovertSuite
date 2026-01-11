# update_checker.py
import urllib.request
import json
import threading

# GitHub repository configuration
GITHUB_API_URL = "https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/releases/latest"
GITHUB_REPO_URL = "https://github.com/YOUR_USERNAME/YOUR_REPO"

def get_latest_version(callback):
    """
    Fetch the latest version from GitHub releases in a background thread.
    Calls callback(latest_version, download_url, error) when done.
    
    Args:
        callback: Function to call with (version_string, download_url, error_message)
    """
    def worker():
        try:
            req = urllib.request.Request(GITHUB_API_URL)
            req.add_header('User-Agent', 'BambamConverterSuite')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Extract version from tag_name (e.g., "v1.2.8" -> "1.2.8")
                latest_version = data.get('tag_name', '').lstrip('v')
                download_url = data.get('html_url', GITHUB_REPO_URL)
                
                callback(latest_version, download_url, None)
        except Exception as e:
            callback(None, None, str(e))
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

def compare_versions(current, latest):
    """
    Compare two version strings.
    
    Args:
        current: Current version string (e.g., "1.2.8")
        latest: Latest version string (e.g., "1.3.0")
    
    Returns:
        'newer' if latest > current
        'same' if equal
        'older' if current > latest
        'unknown' if comparison fails
    """
    try:
        # Split versions into parts
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]
        
        # Pad shorter version with zeros
        max_len = max(len(current_parts), len(latest_parts))
        current_parts += [0] * (max_len - len(current_parts))
        latest_parts += [0] * (max_len - len(latest_parts))
        
        # Compare
        if latest_parts > current_parts:
            return 'newer'
        elif latest_parts == current_parts:
            return 'same'
        else:
            return 'older'
    except Exception:
        return 'unknown'
