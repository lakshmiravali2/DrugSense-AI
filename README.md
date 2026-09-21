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
