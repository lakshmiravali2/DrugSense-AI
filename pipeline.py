"""
AI / Computer-Vision pipeline for the field drug-test digital companion prototype.

This module implements four stages that mirror the flowchart in the project brief:
  1. Image quality assessment (blur / brightness / exposure)
  2. Reference-colour-card detection + colour calibration (gray-world white balance
     anchored on the reference patch, so lighting differences are compensated for)
  3. AI classification (Positive / Negative / Inconclusive) via colour-distance to
     class centroids -- this is a transparent stand-in for a trained CNN, deliberately
     simple so it is auditable for a hackathon demo. Swap `classify()` for a real
     trained model later; the rest of the pipeline does not need to change.
  4. Confidence + explanation string generation

IMPORTANT: this is a *prototype* decision-support tool. It produces a presumptive,
non-forensic classification and always requires human verification (see app.py).
"""

import json
from pathlib import Path

import cv2
import numpy as np

REFERENCE_CARDS_PATH = Path(__file__).parent / "reference_cards.json"


# ---------------------------------------------------------------------------
# Stage 2: Image quality assessment
# ---------------------------------------------------------------------------

def assess_quality(image: np.ndarray) -> dict:
    """Return a quality score (0-100) plus pass/fail and the reason for failure."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur: variance of the Laplacian. Low variance = blurry.
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

    # Brightness: mean pixel intensity, ideally in a mid-range band.
    brightness = float(np.mean(gray))

    # Contrast: standard deviation of intensity.
    contrast = float(np.std(gray))

    reasons = []
    if blur_score < 50:
        reasons.append("Image is too blurry")
    if brightness < 40:
        reasons.append("Image is too dark")
    if brightness > 220:
        reasons.append("Image is overexposed")
    if contrast < 15:
        reasons.append("Insufficient contrast / possible occlusion")

    # Combine into a single 0-100 score for the dashboard.
    blur_component = min(blur_score / 150.0, 1.0) * 40
    brightness_component = (1.0 - abs(brightness - 130) / 130.0) * 30
    brightness_component = max(brightness_component, 0)
    contrast_component = min(contrast / 60.0, 1.0) * 30
    score = round(blur_component + brightness_component + contrast_component, 1)

    passed = bool(len(reasons) == 0 and score >= 50)
    return {
        "score": float(score),
        "passed": passed,
        "reasons": reasons if not passed else [],
        "metrics": {
            "blur_variance": float(round(blur_score, 1)),
            "brightness": float(round(brightness, 1)),
            "contrast": float(round(contrast, 1)),
        },
    }


# ---------------------------------------------------------------------------
# Stage 3: Reference colour card detection + calibration
# ---------------------------------------------------------------------------

def detect_reference_patch(image: np.ndarray) -> tuple:
    """
    Locate the reference colour card.

    Prototype assumption (documented, not hidden): the operator places a small
    known-white/neutral-gray reference card in the TOP-LEFT corner of the frame
    (this mirrors how physical colour-card kits are used in the field: a fixed
    corner position rather than automatic card detection, which is a stretch
    goal listed in the roadmap). We sample a fixed-size patch from that corner.
    """
    h, w = image.shape[:2]
    patch_h, patch_w = int(h * 0.15), int(w * 0.15)
    patch = image[0:patch_h, 0:patch_w]
    mean_color = patch.reshape(-1, 3).mean(axis=0)  # BGR
    return patch, mean_color


def calibrate_colour(image: np.ndarray, reference_bgr: np.ndarray) -> np.ndarray:
    """
    Gray-world-style calibration anchored on the reference patch.

    We assume the reference card is neutral gray/white. Whatever tint the
    reference patch shows under the current lighting is treated as the lighting
    bias, and we scale each channel to cancel it out.
    """
    target_gray = 200.0  # assumed true value of the neutral reference card
    b, g, r = reference_bgr
    scale = np.array([
        target_gray / max(b, 1e-3),
        target_gray / max(g, 1e-3),
        target_gray / max(r, 1e-3),
    ])
    # Clip scaling factors so a bad detection can't blow out the image
    scale = np.clip(scale, 0.5, 2.0)

    calibrated = image.astype(np.float32) * scale
    calibrated = np.clip(calibrated, 0, 255).astype(np.uint8)
    return calibrated


# ---------------------------------------------------------------------------
# Stage 4: Reference card fetch + AI classification
# ---------------------------------------------------------------------------

# How close (Lab colour distance) a reaction has to be to a reference card to
# be accepted as a match at all, and how confident the top match has to be
# relative to the runner-up. THESE ARE PLACEHOLDER THRESHOLDS for the
# prototype demo -- in a real deployment these are tuned against a labelled
# dataset of the specific test-kit reagent's colour reactions, per the
# problem statement's requirement to report accuracy/precision/recall rather
# than claiming forensic accuracy from defaults.
MATCH_DISTANCE_THRESHOLD = 30.0
MIN_CONFIDENCE = 0.45
MIN_MARGIN = 0.08

REACTION_PATCH_FRACTION = (0.35, 0.65, 0.35, 0.65)  # (y0, y1, x0, x1) as fraction of frame
# Prototype assumption: the reaction spot sits roughly in the centre of frame.


def fetch_reference_cards() -> list:
    """
    Retrieve the library of known reagent colour-reaction reference cards.

    Prototype note: this reads a local JSON file. In a production deployment
    this is the natural place to call an authorized reference-card API (e.g.
    a maintained government/forensic-lab database of reagent colour
    signatures per kit type/batch), so a new or updated reagent kit doesn't
    require redeploying the app -- only refreshing the reference data.
    """
    with open(REFERENCE_CARDS_PATH) as f:
        return json.load(f)


def extract_reaction_colour(calibrated_image: np.ndarray) -> np.ndarray:
    h, w = calibrated_image.shape[:2]
    y0, y1, x0, x1 = REACTION_PATCH_FRACTION
    region = calibrated_image[int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
    mean_bgr = region.reshape(-1, 3).mean(axis=0).astype(np.uint8).reshape(1, 1, 3)
    mean_lab = cv2.cvtColor(mean_bgr, cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)
    # OpenCV Lab: L in [0,255] -> scale to [0,100]; a,b already centred near 128
    l, a, b = mean_lab
    return np.array([l * 100.0 / 255.0, a - 128.0, b - 128.0])


def _build_analysis(final_label: str, matched_card: dict, distance: float,
                     confidence: float, alert: bool) -> str:
    """Human-readable reasoning for *why* this result was reached, tying the
    decision back to the concrete thresholds used -- this is what an officer
    or judge should be able to read and understand without touching code."""
    if alert:
        return (
            f"No reference card matched confidently enough to issue a result. "
            f"Closest match was '{matched_card['name']}' ({matched_card['id']}) "
            f"at a colour distance of {distance:.1f} (accept threshold: "
            f"{MATCH_DISTANCE_THRESHOLD:.0f}) with {confidence*100:.1f}% confidence "
            f"(minimum required: {MIN_CONFIDENCE*100:.0f}%). Per protocol this is "
            f"flagged INCONCLUSIVE and requires immediate officer review -- no "
            f"automatic result is issued."
        )
    return (
        f"Matched reference card '{matched_card['name']}' ({matched_card['id']}) "
        f"at a colour distance of {distance:.1f}, within the accept threshold of "
        f"{MATCH_DISTANCE_THRESHOLD:.0f}, with {confidence*100:.1f}% confidence "
        f"(minimum required: {MIN_CONFIDENCE*100:.0f}%). {matched_card['description']}"
    )


def classify(calibrated_image: np.ndarray) -> dict:
    lab = extract_reaction_colour(calibrated_image)
    reference_cards = fetch_reference_cards()

    distances = {}
    for card in reference_cards:
        centroid = np.array(card["lab"])
        distances[card["id"]] = float(np.linalg.norm(lab - centroid))

    # Convert distances to a softmax-like confidence (smaller distance = higher confidence)
    inv = {k: 1.0 / (1.0 + v) for k, v in distances.items()}
    total = sum(inv.values())
    confidences_by_card = {k: v / total for k, v in inv.items()}

    best_card_id = min(distances, key=distances.get)
    best_card = next(c for c in reference_cards if c["id"] == best_card_id)
    best_distance = distances[best_card_id]
    best_confidence = confidences_by_card[best_card_id]

    sorted_conf = sorted(confidences_by_card.values(), reverse=True)
    margin = sorted_conf[0] - sorted_conf[1] if len(sorted_conf) > 1 else 1.0

    alert = (
        best_distance > MATCH_DISTANCE_THRESHOLD
        or best_confidence < MIN_CONFIDENCE
        or margin < MIN_MARGIN
    )
    final_label = "INCONCLUSIVE" if alert else best_card["label"]
    # Whether the AI landed on INCONCLUSIVE because nothing matched confidently,
    # or because it confidently matched the "ambiguous pattern" reference card
    # itself, either way the officer needs to see an alert -- INCONCLUSIVE
    # always means "stop and get a human," never a silent result.
    alert = final_label == "INCONCLUSIVE"

    analysis = _build_analysis(final_label, best_card, best_distance, best_confidence, alert)

    # Roll per-card confidences up to per-label confidences for the dashboard chart
    confidences_by_label = {"POSITIVE": 0.0, "NEGATIVE": 0.0, "INCONCLUSIVE": 0.0}
    for card in reference_cards:
        confidences_by_label[card["label"]] += confidences_by_card[card["id"]]

    return {
        "result": final_label,
        "confidence": round(best_confidence, 3),
        "confidences": {k: round(v, 3) for k, v in confidences_by_label.items()},
        "explanation": analysis,
        "analysis": analysis,
        "matched_reference": {
            "id": best_card["id"],
            "name": best_card["name"],
            "distance": round(best_distance, 2),
        },
        "reaction_lab": [round(float(x), 2) for x in lab],
        "alert": alert,
        "status": "REQUIRES_HUMAN_VERIFICATION",
    }


# ---------------------------------------------------------------------------
# Full pipeline entry point
# ---------------------------------------------------------------------------

def run_pipeline(image: np.ndarray) -> dict:
    quality = assess_quality(image)
    if not quality["passed"]:
        return {
            "stage_reached": "quality_check",
            "quality": quality,
            "result": None,
        }

    patch, reference_bgr = detect_reference_patch(image)
    calibrated = calibrate_colour(image, reference_bgr)
    classification = classify(calibrated)

    return {
        "stage_reached": "classification",
        "quality": quality,
        "reference_bgr": [round(float(x), 1) for x in reference_bgr],
        "classification": classification,
    }
