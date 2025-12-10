# vision_server.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn
import os
import torch
import cv2
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import base64
import logging

# --- SILENCE LOGS ---
torch._logging.set_logs(dynamo=logging.ERROR, inductor=logging.ERROR)
torch.set_float32_matmul_precision('high')

# --- SAM 2 SETUP ---
print("--- IMPORTING SAM 2 ---")
try:
    from sam2.build_sam import build_sam2
    try:
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator as SamAutomaticMaskGenerator
    except ImportError:
        from sam2.automatic_mask_generator import SamAutomaticMaskGenerator
    SAM2_AVAILABLE = True
except ImportError as e:
    print(f"--- SAM 2 IMPORT FAILED: {e} ---")
    SAM2_AVAILABLE = False

app = FastAPI()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"--- SERVER STARTING ON {DEVICE} ---")

# 1. LOAD CLIP
print("--- LOADING CLIP ---")
CLIP_PATH = "hf_models/models--openai--clip-vit-large-patch14"
try:
    clip_model = CLIPModel.from_pretrained(CLIP_PATH).to(DEVICE)
    clip_processor = CLIPProcessor.from_pretrained(CLIP_PATH)
except:
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(DEVICE)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")

# 2. LOAD SAM 2
print("--- LOADING SAM 2 ---")
mask_generator = None
if SAM2_AVAILABLE:
    BASE_DIR = os.path.abspath(os.getcwd())
    SAM_CONFIG = "sam2_hiera_l.yaml" 
    SAM_CHECKPOINT = os.path.join(BASE_DIR, "sam2_hiera_large.pt")

    if os.path.exists(SAM_CHECKPOINT):
        try:
            print("   -> Loading Weights to GPU...")
            sam2 = build_sam2(SAM_CONFIG, SAM_CHECKPOINT, device=DEVICE, apply_postprocessing=False)
            
            print("   -> Compiling Model with 'max-autotune'...")
            try:
                sam2.image_encoder = torch.compile(sam2.image_encoder, mode="max-autotune")
                print("   -> Compilation Active: Triton Kernels Enabled.")
            except Exception as e:
                print(f"   -> Compilation Warning: {e}")

            mask_generator = SamAutomaticMaskGenerator(
                model=sam2,
                points_per_side=12,
                pred_iou_thresh=0.7,
                stability_score_thresh=0.80, 
                crop_n_layers=0,
                min_mask_region_area=100
            )
            print("--- SUCCESS: SAM 2 LOADED (OPTIMIZED) ---")
        except Exception as e:
             print(f"--- ERROR LOADING MODEL: {e} ---")
    else:
        print(f"--- ERROR: Model file missing at {SAM_CHECKPOINT} ---")

# --- HAZARD LABELS ---
HAZARD_LABELS = [
    "clear road", "flood water", "raging fire and smoke", 
    "collapsed building rubble", "military vehicles", "dense forest"
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
        overlay[m] = frame[m] * 0.6 + np.array(color) * 0.4
    return overlay

@app.post("/analyze_frame_fast")
async def analyze_frame_fast(file: UploadFile = File(...)):
    if not SAM2_AVAILABLE or mask_generator is None:
        return JSONResponse({"error": "SAM 2 not loaded"}, status_code=500)

    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # RESIZE (512p)
        height, width = frame.shape[:2]
        target_dim = 512
        scale = target_dim / max(height, width)
        new_size = (int(width * scale), int(height * scale))
        frame_resized = cv2.resize(frame, new_size)
        
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        # INFERENCE
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            # CLIP
            inputs = clip_processor(text=HAZARD_LABELS, images=pil_image, return_tensors="pt", padding=True).to(DEVICE)
            outputs = clip_model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)
            best_idx = probs.argmax().item()
            detected_hazard = HAZARD_LABELS[best_idx]
            confidence = probs[0][best_idx].item()

            # SAM 2
            masks = mask_generator.generate(frame_rgb)

        # --- MATH FIX START ---
        total_area = frame_resized.shape[0] * frame_resized.shape[1]
        
        if len(masks) > 0:
            # 1. Stack all boolean masks into a 3D array
            all_masks = np.stack([m['segmentation'] for m in masks], axis=0)
            # 2. Flatten them: If a pixel is True in ANY mask, it counts as 1 (Logical OR)
            union_mask = np.any(all_masks, axis=0)
            # 3. Sum the unique True pixels
            covered_area = np.sum(union_mask)
        else:
            covered_area = 0
            
        coverage_ratio = round((covered_area / total_area) * 100, 1)
        # --- MATH FIX END ---

        annotated_frame = apply_masks_to_frame(frame_resized, masks)
        
        return JSONResponse({
            "image_base64": mat_to_base64(annotated_frame),
            "stats": {
                "hazard_type": detected_hazard,
                "hazard_confidence": round(confidence, 2),
                "coverage_pct": coverage_ratio,
                "mask_count": len(masks),
                "survivors": "N/A" 
            }
        })
    except Exception as e:
        print(f"Error processing frame: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)