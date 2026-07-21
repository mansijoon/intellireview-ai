# IntelliReview AI

> **AI-Powered Engineering Intelligence Platform for Repository Analysis, Architecture Assessment, Security Review, and Automated Code Intelligence**
>
> > Developed with AI-assisted engineering using Google Gemini and OpenAI GPT-5.6.

IntelliReview AI is an AI-powered **Engineering Intelligence Platform** that analyzes software repositories to help developers understand code quality, architecture, technical debt, maintainability, and security.

Unlike traditional code review tools that focus only on individual files or pull requests, IntelliReview AI performs **repository-wide engineering analysis**, combining static analysis, dependency analysis, architectural insights, technical debt evaluation, repository health metrics, and Large Language Models (Google Gemini) to generate actionable engineering reports.

---

# Features

## Repository Analysis

- Repository ZIP Analysis
- GitHub Repository Analysis
- Repository Health Score
- Repository Executive Summary
- Repository Technical Debt Analysis
- Repository Security Analysis
- Repository Dependency Analysis
- Repository Architecture Analysis
- Repository Risk Ranking
- Repository Refactoring Priority
- Repository Root Cause Analysis

---

## Code Analysis

- Single File Analysis
- Pull Request Review
- Static Code Analysis
- Complexity Analysis
- Code Smell Detection
- Maintainability Analysis

---

## Dependency Intelligence

- Interactive Dependency Graph
- Circular Dependency Detection
- Module Dependency Mapping
- High-Risk Module Identification
- Dependency Visualization (PyVis)

---

## Security Analysis

- Hardcoded Secret Detection
- Repository Security Score
- Security Summary
- Vulnerability Hotspot Identification

---

## Architecture Intelligence

- Architecture Analysis
- Architecture Score
- Layer Dependency Analysis
- High Coupling Detection
- Structural Complexity Assessment

---

## Engineering Intelligence

- Technical Debt Estimation
- Module Risk Ranking
- Complexity Heatmap
- Refactoring Priority Ranking
- Root Cause Analysis
- Repository Health Metrics

---

## AI Features

Powered by **Google Gemini 2.5 Flash**

- AI Code Review
- AI Repository Review
- AI Fix Suggestions
- Engineering Recommendations
- Executive Summaries
- Architecture Recommendations

---

## Reporting

- Executive Summary Dashboard
- Severity Dashboard
- Security Dashboard
- Repository Metrics Dashboard
- PDF Report Generation
- Text Report Generation

---

# Supported Workflows

## Single File Analysis

Analyze individual source files.

Provides:

- Static Analysis
- Security Review
- Complexity Metrics
- AI Review
- Fix Suggestions

---

## Repository Analysis

Analyze an entire software repository.

Provides:

- Repository Health Score
- Architecture Analysis
- Dependency Graph
- Circular Dependency Detection
- Technical Debt Analysis
- Security Analysis
- Risk Ranking
- Complexity Heatmap
- Refactoring Priority
- Root Cause Analysis
- Executive Summary

---

## GitHub Repository Analysis

Analyze public GitHub repositories directly without downloading them manually.

---

## Pull Request Review

Analyze pull request diffs.

Provides:

- Severity Classification
- Security Findings
- AI Review
- Suggested Fixes

---

# Architecture


                     User
                       │
                       ▼
                Streamlit Interface
                       │
                       ▼
        ┌─────────────────────────────────┐
        │ Repository Processing Engine    │
        └─────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
 Static Analysis   Dependency     Repository
     Engine         Analysis        Metrics
        │              │              │
        ▼              ▼              ▼
 Security        Architecture    Technical Debt
 Analysis          Analysis         Analysis
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              Engineering Intelligence
                       │
                       ▼
            Google Gemini 2.5 Flash
                       │
                       ▼
             AI Review & Recommendations
                       │
                       ▼
         Dashboards • Reports • PDF Export


---

# Tech Stack

## Frontend

- Streamlit

## Backend

- Python

## AI

- Google Gemini 2.5 Flash

## Static Analysis

- Python AST
- Custom Static Analysis Engine

## Repository Intelligence

- Dependency Graph Analysis
- Technical Debt Analysis
- Architecture Analysis
- Repository Metrics

## Visualization

- Plotly
- PyVis
- Matplotlib

## Reporting

- ReportLab
- PDF Reports

---

# Installation

Clone the repository


git clone https://github.com/yourusername/intellireview-ai.git
cd intellireview-ai


Create a virtual environment


python -m venv venv


Linux / macOS


source venv/bin/activate


Windows


venv\Scripts\activate


Install dependencies


pip install -r requirements.txt


Create a `.env`


GEMINI_API_KEY=YOUR_API_KEY


Run


streamlit run app.py


---

# Project Structure

intellireview-ai/

├── analyzer/
│   ├── dependency/
│   ├── ...
│
├── tests/
│
├── uploads/
├── reports/
├── assets/
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore




# Engineering Reports

The platform generates insights including:

- Repository Health Score
- Architecture Score
- Security Score
- Technical Debt
- Dependency Graph
- Circular Dependencies
- Module Risk Ranking
- Refactoring Priority
- Complexity Heatmap
- Root Cause Analysis
- AI Review
- AI Fix Suggestions
- Executive Summary
- PDF Engineering Report

---

# Current Capabilities

- Repository Intelligence
- Static Analysis
- Dependency Analysis
- Architecture Analysis
- Technical Debt Analysis
- Security Analysis
- AI Code Review
- AI Repository Review
- Executive Reporting
- Interactive Dependency Visualization

---

# Roadmap (Tier 2)

- Incremental Repository Analysis
- Historical Trend Analysis
- GitHub Webhooks
- CI/CD Integration
- Team Dashboards
- Repository Benchmarking
- Multi-Language Repository Support
- Custom Engineering Rules
- Developer Analytics
- Organization-Level Reporting

---

# License

This project is intended for educational, research, and portfolio purposes.
