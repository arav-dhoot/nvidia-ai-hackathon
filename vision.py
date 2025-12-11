# vision.py

import requests
import base64

SERVER_URL = "http://localhost:9000"

def process_frame_realtime(frame_bytes):
    """
    Sends a single raw frame bytes to the server.
    
    Args:
        frame_bytes: Raw image bytes
    
    Returns:
        tuple: (Annotated Image Bytes or None, Stats Dictionary or None)
        
    Error cases return (None, None) which the caller must handle.
    """
    files = {"file": frame_bytes}
    try:
        # Increase timeout slightly for heavy frames
        response = requests.post(f"{SERVER_URL}/analyze_frame_fast", files=files, timeout=30)
        
        # --- IMPROVED: Check for Server Errors ---
        if response.status_code != 200:
            try:
                error_msg = response.json().get('error', response.text)
            except:
                error_msg = response.text
            print(f"❌ SERVER ERROR ({response.status_code}): {error_msg}")
            return None, None

        data = response.json()
        
        # --- IMPROVED: Verify Data Integrity ---
        if 'image_base64' not in data:
            print(f"❌ INVALID RESPONSE: Missing 'image_base64'. Keys received: {list(data.keys())}")
            return None, None
        
        if 'stats' not in data:
            print(f"❌ INVALID RESPONSE: Missing 'stats'. Keys received: {list(data.keys())}")
            return None, None
            
        # Decode
        try:
            img_bytes = base64.b64decode(data['image_base64'])
        except Exception as e:
            print(f"❌ BASE64 DECODE ERROR: {e}")
            return None, None
            
        stats = data['stats']
        
        return img_bytes, stats
        
    except requests.exceptions.Timeout:
        print(f"⚠️ TIMEOUT: Server took longer than 30 seconds to respond")
        return None, None
    except requests.exceptions.ConnectionError as e:
        print(f"⚠️ CONNECTION ERROR: Cannot reach server at {SERVER_URL}. Is it running?")
        return None, None
    except Exception as e:
        print(f"⚠️ UNEXPECTED ERROR: {e}")
        return None, None