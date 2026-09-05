NeuroFence — LLM Weight Poisoning & Backdoor Scanner:

A Python-based AI Security and Model Forensics platform designed to analyze Machine Learning and Large Language Models (LLMs) for suspicious weight modifications, potential weight poisoning, and hidden backdoor behavior before deployment.


🚀 Project Overview:

NeuroFence is a defensive AI security platform developed to assess the integrity and behavior of machine-learning models. It provides a controlled environment where models can be validated, executed in a sandbox, inspected at the weight and parameter level, and tested for suspicious behavioral patterns.

The platform combines model validation, sandbox analysis, weight inspection, behavioral testing, backdoor assessment, and forensic analysis into a structured security workflow. This helps security researchers and AI developers identify potential model-integrity risks before models are introduced into trusted or production environments.


🔍 Core Features:

Model Validation – Validates model files and required components before analysis.
Weight Inspection – Examines model parameters for unusual or suspicious patterns.
Weight Poisoning Analysis – Assesses potential anomalies caused by manipulated model parameters.
Backdoor Detection – Performs controlled behavioral testing to identify potential hidden trigger-based behavior.
Model Sandbox – Provides a controlled environment for secure model execution and analysis.
Security Fuzzing – Tests model behavior using controlled inputs to identify anomalous responses.
Forensic Analysis – Correlates analysis results and behavioral observations into security findings.
Test Model Generation – Creates controlled models for validating detection capabilities.
Desktop GUI – Provides a PyQt5-based interface for performing model security analysis.
Environment Verification – Verifies dependencies and runtime configuration before execution.


⚙️ Security Analysis Workflow:

Stage	Focus Area	Deliverable
1	Model Validation	Verified model input
2	Sandbox Initialization	Controlled execution environment
3	Weight Inspection	Parameter-level analysis
4	Weight Poisoning Analysis	Suspicious modification assessment
5	Behavioral Testing	Anomalous behavior detection
6	Backdoor Analysis	Trigger-based security assessment
7	Forensic Assessment	Security findings
8	Final Analysis	Overall model security evaluation



🛠️ Technology Stack:

Python	     - Core application and security logic
PyTorch	     - Model loading and weight analysis
Transformers - LLM and transformer model support
Hugging Face - Model ecosystem and model integration
NumPy	     - Numerical and parameter analysis
Scikit-learn - Statistical and detection analysis
PyQt5	     - Desktop graphical user interface
Safetensors	 - Secure model weight handling
Git & GitHub - Version control and project management



📁 Project Structure:

NeuroFence/
│
├── detector/              # Model detection and analysis modules
├── sandbox/               # Controlled model execution
├── fuzzer/                # Behavioral security testing
├── report/                # Security analysis and reporting
├── gui/                   # PyQt5 desktop interface
├── tests/                 # Testing utilities
│
├── main.py                # Main scanner entry point
├── create_test_model.py   # Controlled test-model generation
├── verify_install.py      # Environment verification
│
├── requirements.txt       # Project dependencies
├── EXECUTION_GUIDE.md     # Complete execution documentation
├── MAIN_REPORT.pdf        # Detailed project report
└── README.md              # Project documentation



🧪 Testing & Validation:

NeuroFence includes controlled testing utilities to validate the effectiveness of its security-analysis and detection mechanisms.

The validation process includes:
Model file validation
Controlled test-model generation
Model integrity analysis
Suspicious parameter inspection
Weight modification assessment
Behavioral testing
Trigger-based backdoor assessment
Detection verification
Security finding analysis

All security experiments are designed for controlled research, educational, and defensive testing environments.



📋 Engineering Roadmap:

1	Environment Setup  - Validated Python environment
2	Model Analysis	   - Model and weight inspection
3	Security Detection - Poisoning and backdoor analysis
4	Behavioral Testing - Controlled security testing
5	GUI Integration	   - Desktop security-analysis interface
6	Forensic Reporting - Security findings and analysis
7	Documentation	   - Execution guide and final report




📈 Project Outcomes:

NeuroFence demonstrates a practical approach to AI model security and model forensics by combining automated model inspection with controlled behavioral analysis.
The project establishes a foundation for identifying potential model-integrity and behavioral security risks before AI models are deployed into production or trusted environments.


👥 Contributors:
Team lead : Mayank Malakar
Members   :  Etor Wisdom Ayomikun , Aswathy Ronald , Pethani Jensy Milanbhai