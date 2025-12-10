# vision_server.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn
import shutil
import os
import torch
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from transformers import CLIPProcessor, CLIPModel
import base64

# --- SAM 2 SETUP ---
try:
    from sam2.build_sam import build_sam2
    from sam2.automatic_mask_generator import SamAutomaticMaskGenerator
    SAM2_AVAILABLE = True
except ImportError:
    SAM2_AVAILABLE = False

app = FastAPI()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"--- SERVER STARTING ON {DEVICE} ---")

# 1. LOAD MODELS
yolo_model = YOLO("yolov8x.pt")

CLIP_PATH = "hf_models/models--openai--clip-vit-large-patch14"
try:
    clip_model = CLIPModel.from_pretrained(CLIP_PATH).to(DEVICE)
    clip_processor = CLIPProcessor.from_pretrained(CLIP_PATH)
except:
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(DEVICE)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")

# 2. SAM 2 LOAD
mask_generator = None
if SAM2_AVAILABLE:
    # ADJUST PATH IF NEEDED
    SAM_CHECKPOINT = "hf_models/models--facebook--sam2-hiera-large/sam2_hiera_large.pt"
    SAM_CONFIG = "sam2_hiera_l.yaml" 
    if os.path.exists(SAM_CHECKPOINT):
        sam2 = build_sam2(SAM_CONFIG, SAM_CHECKPOINT, device=DEVICE, apply_postprocessing=False)
        mask_generator = SamAutomaticMaskGenerator(sam2)
        print("--- SAM 2 LOADED ---")

# --- HAZARD DEFINITIONS ---
# This list allows the system to work in ANY environment
HAZARD_LABELS = [
    "clear road", 
    "flood water", 
    "raging fire and smoke", 
    "collapsed building rubble", 
    "military vehicles",
    "dense forest",
    "snow avalanche"
]

def mat_to_base64(mat):
    _, buffer = cv2.imencode('.jpg', mat)
    return base64.b64encode(buffer).decode('utf-8')

def apply_masks_to_frame(frame, masks):
    if len(masks) == 0: return frame
    sorted_anns = sorted(masks, key=(lambda x: x['area']), reverse=True)
    overlay = frame.copy()
    for ann in sorted_anns:
        m = ann['segmentation']
        color = np.random.randint(0, 255, (3,)).tolist()
        overlay[m] = frame[m] * 0.5 + np.array(color) * 0.5
    return overlay

@app.post("/analyze_frame_fast")
async def analyze_frame_fast(file: UploadFile = File(...)):
    """
    Universal Real-Time Endpoint.
    1. Resizes frame (Speed).
    2. Runs CLIP (Identify Hazard Type).
    3. Runs SAM 2 (Map Hazard Area).
    4. Returns Image + Stats.
    """
    if not SAM2_AVAILABLE or mask_generator is None:
        return JSONResponse({"error": "SAM 2 not loaded"}, status_code=500)

    # A. READ & RESIZE
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Resize to 640p for Real-Time performance on GB10
    height, width = frame.shape[:2]
    scale = 640 / max(height, width)
    new_size = (int(width * scale), int(height * scale))
    frame_resized = cv2.resize(frame, new_size)
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)

    # B. IDENTIFY HAZARD (CLIP)
    # We ask CLIP: "Which label best describes this scene?"
    inputs = clip_processor(text=HAZARD_LABELS, images=pil_image, return_tensors="pt", padding=True).to(DEVICE)
    with torch.no_grad():
        outputs = clip_model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
    
    best_idx = probs.argmax().item()
    detected_hazard = HAZARD_LABELS[best_idx]
    confidence = probs[0][best_idx].item()

    # C. MAP HAZARD (SAM 2)
    masks = mask_generator.generate(frame_rgb)
    
    # Calculate Coverage Stats
    total_area = frame_resized.shape[0] * frame_resized.shape[1]
    covered_area = sum([m['area'] for m in masks])
    coverage_ratio = round((covered_area / total_area) * 100, 1)

    # D. VISUALIZE
    annotated_frame = apply_masks_to_frame(frame_resized, masks)
    
    # E. OPTIONAL: Count People (YOLO)
    # Only run if you have GPU headroom, otherwise skip for FPS
    # yolo_res = yolo_model(frame_resized, verbose=False)
    # person_count = sum(1 for box in yolo_res[0].boxes if int(box.cls) == 0)
    person_count = "N/A" # Placeholder for speed

    return JSONResponse({
        "image_base64": mat_to_base64(annotated_frame),
        "stats": {
            "hazard_type": detected_hazard,
            "hazard_confidence": round(confidence, 2),
            "coverage_pct": coverage_ratio,
            "mask_count": len(masks),
            "survivors": person_count
        }
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)