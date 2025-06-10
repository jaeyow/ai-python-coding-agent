# AI Python Coding Agent

An intelligent Python code generation system featuring two distinct implementation approaches, each demonstrating different architectural patterns for AI-driven development workflows.

## 🎯 Project Overview

This project showcases two complementary approaches to AI-powered code generation:

### 🔄 **01_ai_workflow** - Structured Workflow Approach
A **graph-based workflow system** built with Apache Burr that follows a predefined state machine pattern. The workflow is explicitly structured with clear transitions and deterministic paths through code generation, validation, and improvement cycles.

**Key Characteristics:**
- **Predefined workflow graph** with explicit state transitions
- **Deterministic flow** through generation → validation → improvement
- **Structured retry logic** with configurable thresholds
- **Comprehensive quality gates** enforced at each step
- **Workflow visualisation** and state tracking

### 🤖 **02_ai_agent** - AI-Driven Agent Approach  
A **model-driven agent system** built with Strands SDK where the AI foundation model dynamically determines the workflow flow. The agent autonomously decides when to generate code, validate results, and iterate based on contextual understanding.

**Key Characteristics:**
- **AI-driven decision making** with dynamic workflow paths
- **Contextual flow control** determined by the foundation model
- **Adaptive iteration strategies** based on real-time assessment
- **Intelligent tool orchestration** guided by AI reasoning
- **Emergent workflow patterns** that adapt to task complexity

## 🚀 Quick Start

### Prerequisites

```bash
# System Requirements
# - Python >= 3.12
# - AWS Account with Bedrock access
# - Claude 3.5 Sonnet model enabled

# Project Setup
git clone <repository-url>
cd ai-python-coding-agent
```

### Environment Setup

```bash
# Initialize project with uv
uv init

# Configure AWS credentials
aws configure sso
aws sso login

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Choose Your Implementation

#### 🔄 Structured Workflow (Apache Burr)
```bash
cd 01_ai_workflow

# Run predefined tasks
uv run 01_ai_workflow.py simple    # Basic factorial function
uv run 01_ai_workflow.py moderate  # CSV analysis with statistics
uv run 01_ai_workflow.py complex   # Multi-threaded web scraper
uv run 01_ai_workflow.py all       # All tasks sequentially

# Test the workflow framework
uv run 00_test.py
```

#### 🤖 AI-Driven Agent (Strands SDK)
```bash
cd 02_ai_agent

# Run interactive agent sessions
uv run ai_agent_strands.py

# Test with predefined scenarios
uv run 02_ai_agent_test.py
```

## 📋 Implementation Comparison

| Feature | 01_ai_workflow (Burr) | 02_ai_agent (Strands) |
|---------|----------------------|----------------------|
| **Architecture** | Graph-based workflow | Agent-driven system |
| **Flow Control** | Predefined transitions | AI-determined paths |
| **Decision Making** | Rule-based logic | Model-driven reasoning |
| **Retry Strategy** | Threshold-based | Contextual assessment |
| **Workflow Visibility** | Visual state machine | Agent reasoning logs |
| **Predictability** | Deterministic paths | Adaptive responses |
| **Customisation** | Modify graph structure | Configure agent behaviour |
| **Best For** | Structured processes | Dynamic problem solving |

## 🛠️ Technology Stack

### Core Dependencies
- **Python 3.12+** - Modern Python with latest features
- **AWS Bedrock** - Claude 3.5 Sonnet foundation model
- **Instructor** - Structured output from language models
- **Pydantic** - Data validation and type safety

### Framework-Specific
- [Apache Burr](https://burr.dagworks.io/) (`01_ai_workflow`) - Workflow orchestration and state management
- [Strands SDK](https://strandsagents.com/latest/) (`02_ai_agent`) - Agent framework and tool orchestration

### Development Tools
- **uv** - Fast Python package manager
- **pytest** - Testing framework
- **boto3** - AWS SDK for Python

## 📚 Documentation

Each implementation includes comprehensive documentation:

### 🔄 [01_ai_workflow Documentation](01_ai_workflow/README.md)
Detailed guide covering:
- Apache Burr workflow architecture
- State machine design patterns
- Quality threshold configuration
- Workflow visualisation
- Performance optimisation
- Custom task creation

### 🤖 [02_ai_agent Documentation](02_ai_agent/README.md)
Complete reference including:
- Strands SDK agent architecture
- AI-driven tool orchestration
- Iterative improvement patterns
- Session management
- Agent reasoning and decision making
- Advanced configuration options

## ⚙️ Configuration

### AWS Setup
```bash
# Configure AWS SSO (recommended)
aws configure sso --profile your-profile-name
aws sso login --profile your-profile-name

# Set environment variables
export AWS_PROFILE=your-profile-name
export AWS_REGION=us-east-1  # Your preferred region
```

### Environment Variables
Create a `.env` file in the project root:
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=your-profile-name

# Model Configuration
MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0

# Optional: Workflow Configuration
MAX_RETRIES=5
WARNING_THRESHOLD=5
ENABLE_CODE_EXECUTION=true
```

## 🎯 Use Cases

### When to Use 01_ai_workflow (Structured Workflow)
- **Standardised processes** requiring consistent quality gates
- **Regulatory compliance** with auditable workflow steps
- **Team environments** where workflow transparency is crucial
- **Production systems** needing predictable execution paths
- **Performance-critical** applications requiring optimised flows

### When to Use 02_ai_agent (AI-Driven Agent)
- **Research and exploration** with unknown problem complexity
- **Dynamic requirements** that change during execution
- **Creative problem solving** requiring adaptive strategies
- **Prototype development** with evolving specifications
- **Complex reasoning** tasks benefiting from AI autonomy

## 📊 Performance Benchmarks

### Workflow Implementation (01_ai_workflow)
| Task Type | Avg Duration | Token Usage | Success Rate |
|-----------|-------------|-------------|--------------|
| Simple | 30s | 1,500 | 95% |
| Moderate | 90s | 4,500 | 85% |
| Complex | 300s | 12,000 | 75% |

### Agent Implementation (02_ai_agent)
| Task Type | Avg Duration | Token Usage | Success Rate |
|-----------|-------------|-------------|--------------|
| Simple | 45s | 2,000 | 90% |
| Moderate | 120s | 6,000 | 80% |
| Complex | 400s | 15,000 | 70% |

*Note: Agent implementation typically uses more tokens due to reasoning overhead but provides more adaptive solutions.*

## 🔍 Troubleshooting

### Common Setup Issues

1. **AWS Authentication**
   ```bash
   # Verify AWS configuration
   aws sts get-caller-identity
   aws bedrock list-foundation-models --region us-east-1
   ```

2. **Python Environment**
   ```bash
   # Check Python version
   python --version  # Should be 3.12+
   
   # Verify dependencies
   uv tree
   ```

3. **Model Access**
   ```bash
   # Test Bedrock access
   aws bedrock get-foundation-model \
     --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
     --region us-east-1
   ```

### Getting Help

- **Workflow Issues**: See [01_ai_workflow troubleshooting](01_ai_workflow/README.md#troubleshooting)
- **Agent Issues**: See [02_ai_agent troubleshooting](02_ai_agent/README.md#troubleshooting)
- **General Setup**: Check AWS Bedrock service availability in your region

### Development Guidelines
- **Workflow contributions**: Focus on graph structure, state management, and deterministic flows
- **Agent contributions**: Enhance reasoning capabilities, tool orchestration, and adaptive behaviours
- **Shared components**: Improve AWS integration, model interactions, and quality validation

**Choose your approach: Structured workflows or AI-driven agents - both paths lead to intelligent code generation! 🚀**