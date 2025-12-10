# vision.py (Client Mode)
import requests
import base64

SERVER_URL = "http://localhost:9000"

def analyze_image_file(image_path):
    """Sends image to Vision Server for Text Analysis"""
    with open(image_path, "rb") as f:
        files = {"file": f}
        try:
            response = requests.post(f"{SERVER_URL}/analyze", files=files)
            data = response.json()
            return f"Visual scan detects {data['survivors']} survivors. The environment shows {data['environment']}."
        except Exception as e:
            return f"Error connecting to Vision Server: {e}"

def run_sam_visualization(image_path, output_path="sam_output.png"):
    """Sends image to Vision Server for Segmentation"""
    with open(image_path, "rb") as f:
        files = {"file": f}
        try:
            response = requests.post(f"{SERVER_URL}/segment", files=files)
            if response.status_code == 200:
                with open(output_path, "wb") as out_f:
                    out_f.write(response.content)
                return output_path
            else:
                print("Server Error:", response.text)
                return image_path
        except Exception as e:
            print(f"Error connecting to Vision Server: {e}")
            return image_path
        
    

def process_frame_realtime(frame_bytes):
    """
    Sends a single raw frame bytes to the server.
    Returns: (Annotated Image Bytes, Stats Dictionary)
    """
    files = {"file": frame_bytes}
    try:
        response = requests.post(f"{SERVER_URL}/analyze_frame_fast", files=files, timeout=5)
        data = response.json()
        
        # Decode the image back to bytes for Streamlit
        img_bytes = base64.b64decode(data['image_base64'])
        stats = data['stats']
        
        return img_bytes, stats
    except Exception as e:
        print(f"Frame Error: {e}")
        return None, None