# Agentic-PhishNet: Multi-Agent Anti-Phishing Framework

## Project Overview

**Agentic-PhishNet** is an innovative Multi-Agent Anti-Phishing (MA2P) Framework designed to combat the evolving threat of phishing attacks. Leveraging the power of Large Language Models (LLMs) and an adversarial self-play training methodology, this system provides a robust, transparent, and adaptive solution for detecting and analyzing suspicious digital communications. Unlike traditional methods that rely on static signatures or opaque black-box models, Agentic-PhishNet employs a committee of specialized AI agents that work in concert to dissect potential threats from multiple angles, offering detailed explanations for their verdicts. This approach significantly enhances detection accuracy and provides users with actionable insights into the nature of the threat.

## Setup and Running Instructions

To get Agentic-PhishNet up and running on your local machine, follow these steps. This setup involves configuring both the Python-based backend (Django) and the JavaScript-based frontend (React).

### 1. Clone the Repository

First, clone the project repository to your local machine using Git:

```bash
git clone https://github.com/your-repo/Agentic-PhishNet.git
cd Agentic-PhishNet
```

### 2. Backend Setup

The backend is built with Django and handles the core logic of the MA2P framework, including agent orchestration and LLM interactions. Navigate into the `Backend` directory and set up its dependencies:

```bash
cd Backend
```

It is highly recommended to create and activate a Python virtual environment to manage dependencies and avoid conflicts with other Python projects:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

**OpenAI API Key Configuration:**

Agentic-PhishNet relies on the OpenAI API for its LLM agents. You must configure your OpenAI API key as an environment variable. The system looks for `OPENAI_API_KEY`. You can set this in your shell environment or, more conveniently, create a `.env` file in the `Backend` directory with the following content:

```
OPENAI_API_KEY="your_api_key_here"
```

Replace `your_api_key_here` with your actual OpenAI API key.

**Run the Backend Server:**

Once the dependencies are installed and your API key is configured, start the Django development server:

```bash
python manage.py runserver 0.0.0.0:8000
```

The backend API will now be running and accessible at `http://localhost:8000`. This server will handle requests from the frontend, process them through the MA2P agents, and return the analysis results.

### 3. Frontend Setup

The frontend is a React.js application that provides the user interface for interacting with the MA2P Framework. It sends user input to the backend API and visualizes the analysis results.

Open a **new terminal window** (keep the backend server running in the first terminal) and navigate to the `Frontend` directory:

```bash
cd Frontend
```

Install the necessary Node.js dependencies:

```bash
npm install
```

**Run the Frontend Development Server:**

Start the React development server:

```bash
npm run dev
```

The frontend application will typically open in your web browser at `http://localhost:3000`. If this port is already in use, Vite (the build tool) will suggest an alternative port.

## Features

Agentic-PhishNet is built with a suite of powerful features designed to provide comprehensive and transparent phishing detection:

*   **Multi-Agent Architecture:** At its core, Agentic-PhishNet employs a sophisticated multi-agent system. An **Orchestrator Agent** acts as the central coordinator, receiving incoming text (e.g., email content) and intelligently distributing it to specialized sub-agents. It then aggregates their individual analyses and confidence scores to form a unified, final verdict. This distributed approach ensures a thorough examination of all aspects of a potential phishing attempt.

*   **Fact-Verification with Retrieval Augmented Generation (RAG):** The **Fact-Verification Agent** is specifically designed to scrutinize the factual claims within the input text. This agent is now significantly enhanced with a **Retrieval Augmented Generation (RAG) system**. This means that beyond its internal knowledge, the agent can perform real-time web lookups to verify information, cross-reference details, and identify inconsistencies. For instance, it can validate company names, contact information, financial figures, and procedural claims against external, credible sources. This RAG capability makes the Fact-Verification Agent exceptionally robust against novel and context-specific phishing lures, as it can adapt its verification process based on the latest available information.

*   **Language Analysis:** The **Language Analysis Agent** focuses on the subtle, yet critical, linguistic and stylistic cues that often betray a phishing attempt. It analyzes elements such as manufactured urgency, threatening or manipulative tone, grammatical anomalies, generic greetings, and various social engineering tactics. By understanding the persuasive and deceptive language patterns, this agent provides a crucial layer of defense against even well-crafted scams.

*   **Adversarial Self-Play Training:** A key innovation of Agentic-PhishNet is its continuous learning mechanism. Our agents are not trained on static datasets but are instead refined through an **adversarial self-play methodology**, inspired by the SELF-REDTEAM framework [Liu et al., 2025](https://arxiv.org/abs/2506.07468). In this paradigm, an 'Attacker' LLM continuously generates increasingly sophisticated phishing scenarios, while our 'Defender' agents (Fact-Verification and Language Analysis) learn to detect them. This iterative process ensures that the system constantly adapts and improves its detection capabilities against novel and evolving phishing techniques, staying ahead of malicious actors.

*   **Transparent & Explainable AI:** Agentic-PhishNet prioritizes transparency. The user interface provides detailed reasoning for its verdicts, going beyond a simple phishing/non-phishing label. It highlights suspicious phrases directly within the input text and offers agent-specific insights into *why* certain content was flagged. This explainability builds user trust and educates them on how to identify sophisticated phishing attempts.

*   **Intuitive Web Interface:** The project includes a user-friendly web interface developed with React.js. This interface allows users to easily submit text for analysis, view the real-time processing by the agents, and visualize the detailed analysis results, including highlighted sections and confidence scores. The design focuses on clarity and ease of use, making advanced phishing detection accessible.

*   **Scalable & Modular Design:** Agentic-PhishNet is built with a modular architecture, allowing for easy integration of new agents or enhancements to existing ones. This design ensures that the framework can adapt to future threats and expand its capabilities to cover various forms of digital communication beyond email, such as text messages, social media posts, or document analysis.

## Technical Stack

Agentic-PhishNet is a full-stack application, leveraging a combination of robust technologies for its backend processing, LLM interactions, and user interface.

### Backend (Python)

The backend serves as the computational core, handling API requests, orchestrating agent interactions, and managing LLM calls.

*   **Django:** A high-level Python web framework that enables rapid development of secure and maintainable websites. In Agentic-PhishNet, Django is used to build the RESTful API that interfaces with the frontend, manages incoming requests, and routes them to the appropriate agent logic.
*   **`openai` Library:** The official Python client library for the OpenAI API. This library is crucial for making requests to OpenAI's large language models, which serve as the foundation for our Fact-Verification and Language Analysis Agents.
*   **`numpy`:** A fundamental package for scientific computing with Python. It is used for numerical operations, particularly in processing and aggregating confidence scores and other quantitative data from the LLM agents.
*   **`requests`:** A popular HTTP library for Python, used for making web requests. This is particularly relevant for the RAG system within the Fact-Verification Agent, enabling it to fetch information from external web sources.
*   **`dotenv`:** A Python library that loads environment variables from a `.env` file. This is used for securely managing sensitive information such as API keys without hardcoding them into the codebase.
*   **`concurrent.futures`:** Part of Python's standard library, this module provides a high-level interface for asynchronously executing callables. Specifically, `ThreadPoolExecutor` is utilized in the Orchestrator Agent to run the Fact-Verification and Language Analysis Agents in parallel, significantly speeding up the analysis process.

### Frontend (JavaScript/React)

The frontend provides the interactive user interface, allowing users to submit content for analysis and visualize the results.

*   **React.js:** A declarative, component-based JavaScript library for building user interfaces. React enables the creation of dynamic and responsive web applications, providing a smooth and intuitive experience for users interacting with Agentic-PhishNet.
*   **Vite:** A next-generation frontend tooling that provides an extremely fast development experience. Vite is used as the build tool for the React application, offering rapid hot module replacement (HMR) and optimized production builds.
*   **Prettier:** An opinionated code formatter. It ensures consistent code style across the entire frontend codebase, improving readability and maintainability for developers.

### LLM Models

*   **`gpt-4o-mini`:** This specific OpenAI model is configured as the default base model for both the Fact-Verification and Language Analysis Agents. Its efficiency and performance make it suitable for real-time analysis within the framework. The choice of LLM is configurable, allowing for flexibility to integrate other models as they become available or as specific performance requirements dictate.

## Project Structure

The repository is organized into distinct directories for the backend, frontend, and sample data, reflecting a clear separation of concerns and facilitating development and deployment:

```
Agentic-PhishNet/
├── Backend/                  # Contains the Django backend application and its components.
│   ├── app/                  # The main Django application, including URL routing, views, and middleware.
│   ├── manage.py             # Django's command-line utility for administrative tasks.
│   ├── requirements.txt      # Lists all Python dependencies required for the backend.
│   ├── server/               # Django project-level settings and URL configurations.
│   └── src/                  # Core Python source code for the MA2P framework.
│       ├── Agents/           # Implementations of the LLM agents (FactModel, LangModel, Orchestrator).
│       │   └── Train/        # Scripts and JSON files related to the adversarial training process, including optimized agent strategies.
│       ├── LLM/              # Wrappers for interacting with different LLM APIs.
│       ├── Util/             # Utility functions, data models (Email, Evaluation), API handlers, and the web RAG component.
│       └── main.py           # The primary entry point for the backend application logic.
├── Frontend/                 # Houses the React.js web application.
│   ├── public/               # Static assets served directly by the web server.
│   ├── src/                  # Source code for the React application.
│   │   └── ui/               # Reusable UI components and pages (e.g., App.jsx, EmailViewer.jsx).
│   ├── package.json          # Defines Node.js project metadata and lists all JavaScript dependencies.
│   └── vite.config.js        # Configuration file for the Vite build tool.
└── Sample/                   # Contains example email texts for testing and demonstration purposes.
    ├── positive/             # Examples of legitimate emails.
    └── scams/                # Examples of phishing emails.
```

## Citation

```bibtex
@misc{liu2025chasingmovingtargetsonline,
      title={Chasing Moving Targets with Online Self-Play Reinforcement Learning for Safer Language Models}, 
      author={Mickel Liu and Liwei Jiang and Yancheng Liang and Simon Shaolei Du and Yejin Choi and Tim Althoff and Natasha Jaques},
      year={2025},
      eprint={2506.07468},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2506.07468}, 
}
