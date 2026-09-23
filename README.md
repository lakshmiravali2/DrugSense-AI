<<<<<<< HEAD
# AI-Powered Digital Companion for Field Drug Testing — Working Prototype

SIH26231 · Ministry of Home Affairs / Narcotics Control Bureau

A minimal but fully functional implementation of the pipeline described in the
project brief: capture → image quality check → reference-card colour
calibration → AI classification → confidence/explanation → officer
verification → tamper-evident secure record → searchable history.

**This is a decision-support prototype, not a forensic instrument.** Every
result requires human officer verification and is explicitly non-confirmatory.

## Run it

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## Live camera capture (new)

The **New Test** page now has two modes:
- **📷 Live capture** — uses `getUserMedia` to open your device camera in the
  browser, grabs a frame on demand, and stamps the exact client-side instant
  of capture (`new Date().toISOString()`) before anything is uploaded. This
  timestamp is what gets stored as the record's official timestamp, and the
  record is tagged `LIVE_CAPTURE`.
- **📁 Upload a photo** — the original file-picker flow, kept as a fallback.
  These records fall back to server-received time and are tagged
  `FILE_UPLOAD`, which is shown clearly on the detail page so nobody mistakes
  it for a precise capture timestamp.

**Note:** `getUserMedia` only works over `https://` or on `localhost` — it
will silently fail if you access the app from another device via a local
network IP (e.g. `http://192.168.x.x:5000`). For a real field deployment,
this means the mobile app needs either HTTPS or to be a native camera
integration rather than a browser page served over plain HTTP.

The test ID itself is still generated automatically server-side (`T-XXXXXXXX`,
a UUID fragment) at insert time, regardless of which capture mode was used —
this hasn't changed.

## Global alert badge (new)

A pulsing 🔔 badge showing the count of pending inconclusive alerts now
appears in the navbar on **every** page — dashboard, new test, history, and
test detail — not only the dashboard's stat box. It appears the instant an
inconclusive result is submitted and disappears once an officer verifies it.

## Important: how positive/negative relates to legal vs illegal substances

This system does **not** decide what is legal or illegal — that judgment is
baked into the chemistry of whichever reagent kit the officer physically
uses (e.g. Marquis, Mecke, Simon's reagent), which is established forensic
science outside this software's scope.

- **POSITIVE** = the captured colour matches the reference pattern this
  specific reagent produces for the specific illegal-substance class it's
  designed to detect.
- **NEGATIVE** = this specific reagent did not produce that reaction. This
  does **not** mean "no drugs of any kind are present" — a different reagent
  targeting a different substance class could still react. This is a known
  limitation of colorimetric testing in general, not something this software
  claims to fix.
- **INCONCLUSIVE** = no reference pattern matched confidently — always
  forces a mandatory alert and blocks the record until an officer reviews it.

## Video recording of the reaction (new)

The **New Test** page's camera tab is now "🎥 Record reaction" instead of a
single snapshot:
1. Start the camera and frame the kit + reference card.
2. Press **Start recording** right as you add the reagent.
3. Press **Stop & capture result** once the colour has settled — this grabs
   the *entire* colour-change as a video clip (`MediaRecorder` API, saved as
   `.webm`) **and** extracts the final, settled frame at that exact instant
   for AI analysis.

The recorded video plays back on the test detail page under "🎥 Reaction
recording" — this is your strongest demo moment for judges, since they can
watch the actual colour change happen rather than trust a single static
photo. The AI still only classifies the one settled final frame (a video
isn't fed into the classifier — a specific analyzable frame is).

**Browser support note:** `MediaRecorder` is supported in Chrome, Edge, and
Firefox. Safari support is inconsistent for `video/webm`; if recording fails
there, the code falls back to whatever MIME type the browser reports as
supported, or the person can use "Upload a photo" instead.

## What's new in this version

- **Reference card library** (`reference_cards.json`) — the AI now matches the
  captured reaction colour against a named library of reference patterns
  instead of bare hardcoded numbers. `fetch_reference_cards()` in
  `pipeline.py` reads this locally today; swap it for a real API call to a
  maintained reagent reference database in production, without touching
  anything downstream.
- **Reasoned analysis** — every result now includes a "Why this result" write-up:
  which reference card matched, the colour distance, the confidence, and the
  thresholds it was checked against. This is what your positive/negative
  screen should show judges as the model's justification.
- **Inconclusive → alert** — if nothing matches confidently, the result is
  forced to INCONCLUSIVE and a visible ⚠️ ALERT banner appears on the test
  page until a supervising officer reviews it. The dashboard now has a live
  "Alerts pending" counter.

## What's real vs. what's a placeholder

| Component | Status |
|---|---|
| Image quality check (blur/brightness/contrast) | Real, using OpenCV Laplacian variance + intensity stats |
| Reference colour card handling | Simplified: assumes card is placed in the top-left corner (documented in `pipeline.py`). Automatic card detection is listed as a roadmap item. |
| Colour calibration | Real gray-world correction anchored on the reference patch |
| AI classification | **Placeholder centroids**, not a trained model — see `CLASS_CENTROIDS_LAB` in `pipeline.py`. Swap in a trained classifier before claiming any real accuracy; the rest of the pipeline is unaffected. |
| SHA-256 image hashing | Real |
| Record signing / tamper detection | Real HMAC-SHA256 (swap for per-officer PKI signatures in production) |
| Role-based access control | Not implemented in this prototype — add before any real deployment |
| GPS capture | Manual text field in this prototype; wire up to device geolocation for a mobile build |

## Demo script (for judges)

1. Go to **New Test**, upload a photo of a completed colour-change test with
   the reference card in the top-left corner.
2. Show the AI result, confidence breakdown, and explanation.
3. As a "supervising officer", verify or reject the result.
4. Open the record and click **Check image for tampering** — it passes.
5. Manually modify the stored image file, click the check again — it now
   flags a hash mismatch. This is the strongest, most visual proof point of
   the security layer.
6. Show **History** with search/filtering.

## Project structure

```
app.py            Flask routes
pipeline.py       Image quality, calibration, AI classification (CV pipeline)
security.py       SHA-256 hashing + HMAC record signing
database.py       SQLite persistence + search
templates/        Jinja2 HTML pages
static/style.css  Styling
```

## Honest limitations to state in your pitch

- The classifier is a distance-based stand-in, not a trained model — be
  explicit that a real deployment needs a labelled dataset per reagent kit
  and reported accuracy/precision/recall/F1, per the brief's own guidance.
- No authentication/RBAC yet — a real field deployment needs this before
  going anywhere near production data.
- Reference-card detection assumes a fixed frame position rather than
  automatic detection.
=======
# AI Drug Sense

## 📌 Overview

**AI Drug Sense** is an AI-powered digital companion designed to assist with **field drug testing** by analyzing colorimetric test results using computer vision and providing a more objective, consistent, and digitally traceable assessment.

The system combines **AI-based color analysis, reference-card calibration, human verification, and secure digital records** into a single field-testing workflow.

> **Note:** AI Drug Sense is intended as a field-screening and decision-support system. It does not replace laboratory confirmation or authorized forensic analysis.

---

## 🎯 Key Features

### 🤖 AI-Based Test Analysis

* Captures the test result using a smartphone camera or authorized device.
* Analyzes the observed color using computer vision.
* Classifies the result as:

  * **Positive**
  * **Negative**
  * **Inconclusive**

### 🎨 Color Calibration

* Uses a reference color card for calibration.
* Helps reduce variations caused by different lighting conditions and cameras.
* Improves consistency in color-based analysis.

### 👤 Human Verification

* Provides an option for authorized operators to verify the AI-generated result.
* Helps handle uncertain or inconclusive results.

### 🔐 Secure Digital Records

Records can include:

* Timestamp
* Location
* Operator ID
* Test result
* Digital hash

Hashing helps make records **tamper-evident** and supports traceability.

### 📱 Field-Friendly Workflow

The system is designed to work with:

* Smartphone cameras
* Existing authorized testing devices
* Existing colorimetric field-testing kits

---

## 🔄 How It Works

```text
Test Sample
     ↓
Colorimetric Test Kit
     ↓
Capture Test Result
     ↓
Reference Card Calibration
     ↓
Image / Color Analysis
     ↓
AI Classification
     ↓
Positive / Negative / Inconclusive
     ↓
Human Verification
     ↓
Secure Digital Record
```

---

## 🧠 AI & Computer Vision

The system uses computer vision and machine learning techniques to analyze the color produced by a field test.

The general workflow includes:

1. Image capture
2. Image quality checking
3. Color calibration
4. Color feature extraction
5. AI/ML-based classification
6. Result confidence assessment
7. Human verification when required

Potential technologies include:

* **OpenCV**
* **NumPy**
* **PyTorch / TensorFlow**
* **Scikit-learn**

---

## 🛠️ Technology Stack

| Area                 | Technologies                          |
| -------------------- | ------------------------------------- |
| Programming          | Python, Dart                          |
| Mobile Application   | Flutter                               |
| Backend              | FastAPI                               |
| Computer Vision      | OpenCV                                |
| Numerical Processing | NumPy                                 |
| Machine Learning     | PyTorch / TensorFlow, Scikit-learn    |
| Database             | SQLite / PostgreSQL                   |
| Authentication       | JWT                                   |
| Security             | SHA-256                               |
| Access Control       | Role-Based Access Control (RBAC)      |
| Hardware             | Smartphone camera / authorized device |

The technology stack is based on the project's proposed implementation architecture.

---

## 🔐 Security

AI Drug Sense incorporates security mechanisms to protect digital test records.

### SHA-256 Hashing

A cryptographic hash can be generated for important records to help detect unauthorized modification.

### JWT Authentication

JSON Web Tokens can be used for authenticated communication between users and the backend.

### Role-Based Access Control

Different users can be given different permissions depending on their role.

Example:

```text
Administrator
      ↓
Manage users / records

Authorized Operator
      ↓
Perform tests / verify results

Viewer
      ↓
View permitted records
```

---

## 🗄️ Data Management

The system can use:

* **SQLite** for lightweight/local deployments
* **PostgreSQL** for larger deployments

A test record may contain information such as:

```text
Test ID
Operator ID
Timestamp
Location
AI Result
Verification Status
Hash
```

This allows test information to be searched and tracked digitally.

---

## ⚙️ Feasibility

The proposed system can be implemented using commonly available software frameworks and existing field-testing equipment.

The main implementation challenges include:

* AI classification accuracy
* Different lighting conditions
* Image quality
* Availability of suitable training data
* Security
* Network connectivity

Possible mitigation strategies include:

* Color calibration
* Diverse training datasets
* Image-quality checks
* Encryption
* Human verification
* Offline functionality

These feasibility considerations and mitigation strategies are included in the project proposal.

---

## 📊 Result Categories

The system produces one of three primary outcomes:

| Result          | Meaning                                            |
| --------------- | -------------------------------------------------- |
| 🟢 Positive     | AI analysis indicates a positive test result       |
| 🔴 Negative     | AI analysis indicates a negative test result       |
| 🟡 Inconclusive | The system cannot confidently determine the result |

An **inconclusive** result can be sent for additional human verification rather than forcing an uncertain classification.

---

## 🚀 Future Improvements

Possible future improvements include:

* Larger and more diverse training datasets
* Improved lighting normalization
* Better image-quality detection
* More robust AI models
* Offline-first operation
* Cloud synchronization
* Advanced analytics and reporting
* Improved audit trails
* Integration with authorized laboratory workflows

---

## 📚 References

The project research considered established references related to field-testing kits and seized-drug analysis, including:

* **UNODC – Drug and Precursor Field Test Kits**
* **SWGDRUG – Recommendations for Seized Drug Analysis**

Color-based field tests are useful for preliminary field screening, while laboratory analysis may be required for definitive identification.

---

## ⚠️ Disclaimer

AI Drug Sense is designed as a **digital field-screening and decision-support tool**.

AI-generated classifications should not be treated as a substitute for authorized laboratory testing, forensic procedures, or applicable legal requirements.

---

## 👩‍💻 Project

**AI Drug Sense**

An AI + Computer Vision solution for more consistent, verifiable, and digitally traceable field-test analysis.
