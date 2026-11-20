# Code Broker: AI-Powered Code Assessment Agent 🤖

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![ADK](https://img.shields.io/badge/Google-ADK-4285F4?logo=google)](https://google.github.io/adk-docs/)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=samiratra95@gmail.com&item_name=Code+Broker+Donation&currency_code=USD)

> **Agents Intensive Capstone Project** - A multi-agent system for comprehensive code analysis and quality assessment

## 🎯 What is Code Broker?

Code Broker is an intelligent multi-agent system built with Google's ADK that automatically analyzes code files, directories, or GitHub repositories and generates detailed assessment reports with actionable improvement recommendations.

Demo Video: [YouTube Link](https://youtu.be/AzqChmFs0oM)

## ✨ Key Features

- 🔍 **Multi-Source Analysis**: Files, directories, or GitHub repositories
- 📊 **Comprehensive Scoring**: Correctness, security, style, and maintainability metrics
- 🤖 **5-Agent System**: Parallel processing with specialized AI agents
- 📝 **Beautiful Reports**: Markdown and HTML formatted assessment reports
- ⚡ **Fast & Reliable**: Async processing with retry mechanisms
- 🛠️ **Deterministic Tool Grounding**:
  - **Pylint**: Automated PEP 8 and Python code quality analysis
  - **Bandit**: AST static application security testing (SAST) and CWE vulnerability detection
  - **Radon**: Quantitative Cyclomatic Complexity (CC) and Maintainability Index (MI) metrics
  - **BugsInPy**: Automated test coverage assessment and fault localization benchmark suites
- 🧪 **Full Test Coverage**: Comprehensive 39-test unit suite across tools, agents, and evaluation modules

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/Samir-atra/agents_intensive_dev.git
cd agents_intensive_dev
pip install -r requirements.txt

# Configure environment (add your GOOGLE_API_KEY and GITHUB_TOKEN)
cp .env.example .env

# Run unit tests
PYTHONPATH=. pytest tests/

# Run the notebook
jupyter notebook notebooks/code_broker_documented.ipynb
```

## 📂 Project Structure

```
agents_intensive_dev/
├── notebooks/
│   ├── code_broker_documented.ipynb          # Main executable multi-agent assessment notebook
│   └── code_broker_report_evaluator.ipynb    # Grounded LLM-as-a-judge meta-evaluator notebook
├── reports/                                  # Generated assessment and tool diagnostic reports
├── src/                                      # Source code modules
│   ├── llm_adk_agent_module.py               # Standalone ADK agent entrypoint
│   └── tools/                                # Analysis tools (lint, security, complexity, git)
├── tests/                                    # Comprehensive unit test suite (39 tests)
├── docs/                                     # Documentation and changelog notes
├── research/                                 # Academic paper submissions & LaTeX manuscripts
├── KAGGLE_WRITEUP.md                         # Detailed competition writeup
├── requirements.txt                          # Python dependencies
└── README.md                                 # This file
```

## 🏗️ Architecture

Code Broker uses a **hierarchical multi-agent architecture**:

- **Report Generator** (Orchestrator): Coordinates the entire workflow
- **Sequential Pipeline Agent**: Manages assessment flow
- **Parallel Assessment Agent**: Runs 3 agents concurrently:
  - Correctness Assessor
  - Style Assessor  
  - Description Generator
- **Improvement Recommender**: Synthesizes findings into actionable recommendations

## 📖 Documentation

For a detailed writeup including architecture, design decisions, and technical details, see:
**[KAGGLE_WRITEUP.md](KAGGLE_WRITEUP.md)**

## 🎓 Competition

This project was created for the **Agents Intensive Capstone Project** on Kaggle:
https://www.kaggle.com/competitions/agents-intensive-capstone-project

## 👨‍💻 Author

**Samer Attrah**
- **GitHub**: [Samir-atra](http://github.com/Samir-atra)
- **Kaggle**: [samerattrah](https://www.kaggle.com/samerattrah)
- **ORCID**: [0009-0006-8090-1256](https://orcid.org/0009-0006-8090-1256)
- **AgentBeats**: [Samir-atra](https://agentbeats.dev/Samir-atra)

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Citation

If you use this project in your research, please cite it as follows:

```bibtex
@misc{attrah2026codebrokermultiagentautomated,
      title={Code Broker: A Multi-Agent System for Automated Code Quality Assessment}, 
      author={Samer Attrah},
      year={2026},
      eprint={2604.23088},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2604.23088}, 
}
```
---

⭐ **Star this repo if you find it helpful and donate if you can!** 
