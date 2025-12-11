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
    print("   -> CLIP loaded from local cache")
except:
    print("   -> Local cache not found, downloading CLIP...")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(DEVICE)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
    print("   -> CLIP loaded from HuggingFace")

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
            mask_generator = None
    else:
        print(f"--- ERROR: Model file missing at {SAM_CHECKPOINT} ---")

# --- HAZARD LABELS ---
HAZARD_LABELS = [
    "clear road", "flood water", "raging fire and smoke", 
    "collapsed building rubble", "military vehicles", "dense forest"
]

def mat_to_base64(mat):
    """Convert OpenCV image matrix to base64 string"""
    _, buffer = cv2.imencode('.jpg', mat)
    return base64.b64encode(buffer).decode('utf-8')

def apply_masks_to_frame(frame, masks):
    """Apply colored overlay masks to frame for visualization"""
    if len(masks) == 0: 
        return frame
    
    sorted_anns = sorted(masks, key=(lambda x: x['area']), reverse=True)
    overlay = frame.copy()
    
    for ann in sorted_anns:
        m = ann['segmentation']
        color = np.random.randint(0, 255, (3,)).tolist()
        overlay[m] = frame[m] * 0.6 + np.array(color) * 0.4
    
    return overlay

@app.post("/analyze_frame_fast")
async def analyze_frame_fast(file: UploadFile = File(...)):
    """
    Analyze a single frame with CLIP (hazard classification) and SAM2 (segmentation).
    
    Returns JSON with:
    - image_base64: Annotated image with colored masks
    - stats: Dictionary containing hazard info and coverage metrics
    """
    if not SAM2_AVAILABLE or mask_generator is None:
        return JSONResponse({
            "error": "SAM 2 not loaded. Check server logs for details."
        }, status_code=500)

    try:
        # Read and decode frame
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JSONResponse({
                "error": "Failed to decode image. Invalid format or corrupted data."
            }, status_code=400)

        # RESIZE (512p for faster processing)
        height, width = frame.shape[:2]
        target_dim = 512
        scale = target_dim / max(height, width)
        new_size = (int(width * scale), int(height * scale))
        frame_resized = cv2.resize(frame, new_size)
        
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        # INFERENCE
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            # CLIP - Hazard Classification
            try:
                inputs = clip_processor(
                    text=HAZARD_LABELS, 
                    images=pil_image, 
                    return_tensors="pt", 
                    padding=True
                ).to(DEVICE)
                outputs = clip_model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)
                best_idx = probs.argmax().item()
                detected_hazard = HAZARD_LABELS[best_idx]
                confidence = probs[0][best_idx].item()
            except Exception as clip_error:
                print(f"CLIP Error: {clip_error}")
                return JSONResponse({
                    "error": f"CLIP classification failed: {str(clip_error)}"
                }, status_code=500)

            # SAM 2 - Segmentation with error handling
            try:
                masks = mask_generator.generate(frame_rgb)
            except torch.cuda.OutOfMemoryError:
                print("SAM2 OOM Error: GPU memory exhausted")
                return JSONResponse({
                    "error": "GPU out of memory during segmentation. Try smaller image or restart server."
                }, status_code=500)
            except Exception as sam_error:
                print(f"SAM2 Generation Error: {sam_error}")
                return JSONResponse({
                    "error": f"SAM2 mask generation failed: {str(sam_error)}"
                }, status_code=500)

        # --- IMPROVED MASK AREA CALCULATION ---
        # Calculate true coverage by combining overlapping masks
        total_area = frame_resized.shape[0] * frame_resized.shape[1]
        
        if len(masks) > 0:
            # Stack all boolean masks into a 3D array [num_masks, height, width]
            all_masks = np.stack([m['segmentation'] for m in masks], axis=0)
            # Logical OR across mask dimension: pixel is True if ANY mask covers it
            union_mask = np.any(all_masks, axis=0)
            # Sum unique covered pixels
            covered_area = np.sum(union_mask)
        else:
            covered_area = 0
            
        coverage_ratio = round((covered_area / total_area) * 100, 1)

        # Apply visual annotations
        annotated_frame = apply_masks_to_frame(frame_resized, masks)
        
        return JSONResponse({
            "image_base64": mat_to_base64(annotated_frame),
            "stats": {
                "hazard_type": detected_hazard,
                "hazard_confidence": round(confidence, 2),
                "coverage_pct": coverage_ratio,
                "mask_count": len(masks),
                "survivors": "N/A"  # Placeholder for future person detection
            }
        })
        
    except Exception as e:
        print(f"Unexpected error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "error": f"Unexpected server error: {str(e)}"
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "online",
        "device": DEVICE,
        "sam2_loaded": mask_generator is not None,
        "clip_loaded": clip_model is not None
    }

if __name__ == "__main__":
    print("--- VISION SERVER READY ---")
    print(f"    Listening on: http://0.0.0.0:9000")
    print(f"    Device: {DEVICE}")
    print(f"    SAM2: {'✓ Loaded' if mask_generator else '✗ Not Available'}")
    print(f"    CLIP: {'✓ Loaded' if clip_model else '✗ Not Available'}")
    uvicorn.run(app, host="0.0.0.0", port=9000)