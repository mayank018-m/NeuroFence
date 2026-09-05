# 🛡️ NeuroFence — LLM Weight Poisoning & Backdoor Scanner

A Python-based AI Security and Model Forensics platform designed to analyze machine-learning and LLM models for suspicious weight modifications, potential poisoning, and hidden backdoor behavior before deployment.

---

## 🚀 Project Overview

NeuroFence addresses the security risks associated with compromised AI models by providing a controlled environment for model inspection and security analysis. The platform analyzes model parameters and weights, performs controlled behavioral testing, and identifies indicators that may suggest model manipulation or backdoor activity. It is designed to support security researchers and developers in evaluating model integrity before integrating AI models into trusted environments.

---

## 🧩 Core Features

- 🔍 **Model Security Scanner** — Loads and analyzes supported PyTorch-based model files for potential security anomalies.
- 🧠 **Weight & Parameter Analysis** — Examines model parameters to identify unusual or potentially manipulated weight patterns.
- 🕵️ **Backdoor Analysis** — Performs controlled behavioral testing to identify potential trigger-based malicious behavior.
- 🧪 **Security Test Models** — Generates controlled test models to validate the detection and analysis pipeline.
- 🔐 **Model Sandbox** — Provides an isolated workflow for safely inspecting and testing model behavior.
- 📊 **Forensic Analysis** — Correlates model-level and behavioral indicators to support security assessment.
- 🖥️ **Desktop Interface** — Provides a PyQt5-based GUI for convenient model selection, scanning, and result visualization.

---

## ⚙️ Security Analysis Workflow

NeuroFence follows a structured model-forensics workflow:

**Model Input → Model Validation → Sandbox Analysis → Weight Inspection → Behavioral & Backdoor Testing → Detection Analysis → Security Findings**

This workflow enables potentially compromised models to be assessed before they are introduced into production or other trusted AI environments.

---

## 🛠️ Technology Stack

NeuroFence is developed using **Python, PyTorch, Transformers, Hugging Face, NumPy, Scikit-learn, PyQt5, and Safetensors**. Git and GitHub are used for version control and collaborative project development.

---

## 📁 Project Structure

```text
NeuroFence/
├── main.py
├── create_test_model.py
├── verify_install.py
├── detector/
├── fuzzer/
├── sandbox/
├── report/
├── gui/
├── tests/
├── requirements.txt
├── README.md
└── .gitignore