## 🛡️ NeuroFence — LLM Weight Poisoning & Backdoor Scanner

A Python-based **AI Security and Model Forensics platform** designed to analyze Machine Learning and Large Language Models (LLMs) for suspicious weight modifications, potential weight poisoning, and hidden backdoor behavior before deployment.

---

### 🚀 Project Overview

NeuroFence is a defensive AI security platform developed to assess the **integrity and behavior of machine-learning models**.

It provides a controlled environment where models can be:

- Validated
- Executed in a sandbox
- Inspected at the weight and parameter level
- Tested for suspicious behavioral patterns

The platform combines **model validation, sandbox analysis, weight inspection, behavioral testing, backdoor assessment, and forensic analysis** into a structured security workflow.

---

### 🔍 Core Features

**1. Model Validation**  
Validates model files, configurations, required components, and runtime dependencies before security analysis.

**2. Model Sandbox**  
Provides a controlled environment for loading and executing models during security analysis.

**3. Weight & Parameter Inspection**  
Inspects model parameters and weights to identify unusual values, distributions, or suspicious modifications.

**4. Weight Poisoning Analysis**  
Analyzes model weights for potential signs of malicious or unintended modifications that may affect model integrity.

**5. Neuron-Level Analysis**  
Examines individual layers and neurons to investigate abnormal activation patterns and potentially compromised components.

**6. Backdoor Analysis**  
Performs controlled behavioral analysis to identify potential trigger-based or hidden backdoor behavior.

**7. Security Fuzzing**  
Uses controlled inputs to test model behavior and identify unexpected or anomalous responses.

**8. Test Model Generation**  
Generates controlled test models and security scenarios for validating NeuroFence detection capabilities.

**9. Forensic Analysis & Reporting**  
Correlates model, weight, neuron, and behavioral analysis results into structured security findings.

**10. Desktop GUI**  
Provides a PyQt5-based graphical interface for model loading, scanning, analysis, and reviewing security findings.

**11. Environment Verification**  
Checks the Python environment, dependencies, and required components before running the security-analysis pipeline.

---

### ⚙️ Security Analysis Workflow

| Stage | Focus Area | Deliverable |
|---:|---|---|
| 1 | Model Validation | Verified model input |
| 2 | Sandbox Initialization | Controlled execution environment |
| 3 | Weight Inspection | Parameter-level analysis |
| 4 | Weight Poisoning Analysis | Suspicious modification assessment |
| 5 | Behavioral Testing | Anomalous behavior detection |
| 6 | Backdoor Analysis | Trigger-based security assessment |
| 7 | Forensic Assessment | Security findings |
| 8 | Final Analysis | Overall model security evaluation |

---

### 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Core application and security logic |
| **PyTorch** | Model loading and weight analysis |
| **Transformers** | LLM and transformer model support |
| **Hugging Face** | Model ecosystem and integration |
| **NumPy** | Numerical and parameter analysis |
| **Scikit-learn** | Statistical and detection analysis |
| **PyQt5** | Desktop graphical interface |
| **Safetensors** | Model weight handling |
| **Git & GitHub** | Version control and project management |

---

### 🧪 Testing & Validation

NeuroFence includes controlled testing utilities to validate the effectiveness of its **security-analysis and detection mechanisms**.

The validation process includes:

1. Model file validation
2. Controlled test-model generation
3. Model integrity analysis
4. Suspicious parameter inspection
5. Weight modification assessment
6. Behavioral testing
7. Trigger-based backdoor assessment
8. Detection verification
9. Security finding analysis

All security experiments are designed for **controlled research, educational, and defensive testing environments**.

---


### 👥 Team

**Team Lead:** Mayank Malakar

**Team Members:**
- Etor Wisdom Ayomikun
- Aswathy Ronald
- Pethani Jensy Milanbhai

---

### ⚠️ Disclaimer

NeuroFence is developed for **educational, defensive security research, and authorized testing purposes only**.

All model security experiments and backdoor testing should be performed only in controlled environments and on models for which appropriate authorization has been obtained.



