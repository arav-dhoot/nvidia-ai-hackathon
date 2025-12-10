# vision.py

import requests
import base64

SERVER_URL = "http://localhost:9000"

def process_frame_realtime(frame_bytes):
    """
    Sends a single raw frame bytes to the server.
    Returns: (Annotated Image Bytes, Stats Dictionary)
    """
    files = {"file": frame_bytes}
    try:
        # Increase timeout slightly for heavy frames
        response = requests.post(f"{SERVER_URL}/analyze_frame_fast", files=files, timeout=30)
        
        # --- NEW: Check for Server Errors ---
        if response.status_code != 200:
            try:
                error_msg = response.json().get('error', response.text)
            except:
                error_msg = response.text
            print(f"❌ SERVER ERROR ({response.status_code}): {error_msg}")
            return None, None

        data = response.json()
        
        # --- NEW: Verify Data Integrity ---
        if 'image_base64' not in data:
            print(f"❌ INVALID RESPONSE: Missing 'image_base64'. Keys received: {list(data.keys())}")
            return None, None
            
        # Decode
        img_bytes = base64.b64decode(data['image_base64'])
        stats = data['stats']
        
        return img_bytes, stats
        
    except Exception as e:
        print(f"⚠️ CONNECTION ERROR: {e}")
        return None, None