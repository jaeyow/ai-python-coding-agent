# AI Agent Workflow Architecture Diagram

This diagram visualizes the workflow architecture from `ai_agent_strands.py`, showing how the supervisor agent orchestrates the two tools in an iterative improvement system.

```mermaid
graph TD
    %% User Input
    A[User Requirement] --> B[CodingAgent.run_workflow]
    
    %% Main Workflow Initialization
    B --> C{Initialize Workflow}
    C --> D[Start Iteration Loop<br/>Max: 3 iterations]
    
    %% Iteration Process
    D --> E[Iteration N<br/>Track Start Time]
    E --> F[Strands Agent Execution]
    
    %% Tool Orchestration
    F --> G[generate_code Tool]
    F --> H[validate_code Tool]
    
    %% Tool Details
    G --> G1[AWS Bedrock API Call<br/>Claude 3.5 Sonnet]
    G1 --> G2[Generate Python Code<br/>Type hints, Docstrings, Error handling]
    G2 --> G3[Store in Global Variable<br/>_last_generated_code]
    
    H --> H1[AST Parsing & Analysis]
    H1 --> H2[Static Code Validation<br/>- Syntax check<br/>- Type hints<br/>- Docstrings<br/>- Error handling]
    H2 --> H3[Store in Global Variable<br/>_last_validation_results]
    
    %% Results Processing
    G3 --> I[Extract Tool Results<br/>from Global Storage]
    H3 --> I
    I --> J[Analyze Validation Results<br/>Count Issues by Type]
    
    %% Quality Assessment
    J --> K{Issues > Threshold?<br/>Threshold: 5 issues}
    K -->|Yes| L{Current Iteration < Max?<br/>& No Critical Errors?}
    K -->|No| M[Quality Acceptable]
    
    %% Iteration Decision
    L -->|Yes| N[Create Feedback Summary<br/>Categorize Issues]
    L -->|No| O[Max Iterations Reached]
    N --> P[Prepare Next Iteration<br/>Enhanced User Message]
    P --> E
    
    %% Best Result Tracking
    I --> Q[Update Best Results<br/>if Issues < Previous Best]
    Q --> R[Track Iteration Metrics<br/>- Issues count<br/>- Duration<br/>- Code length<br/>- Validation count]
    
    %% Final Processing
    M --> S[Finalize Results]
    O --> S
    S --> T[Use Best Results<br/>from All Iterations]
    T --> U[Generate Code Metrics<br/>Quality Analysis]
    U --> V[Create Scenario Data<br/>Success/Failure Status]
    
    %% Output Generation
    V --> W[Return Final Results<br/>- Generated Code<br/>- Validation Results<br/>- Execution Metrics<br/>- Iteration Count]
    
    %% Session Management
    V --> X[Store in Session Data<br/>for Reporting]
    X --> Y[Optional: Generate<br/>Session Report]
    
    %% Error Handling
    F -.->|Exception| Z[Error Handling<br/>Store Error Scenario]
    Z --> W
    
    %% Styling
    classDef userInput fill:#e1f5fe
    classDef agent fill:#f3e5f5
    classDef tools fill:#e8f5e8
    classDef decision fill:#fff3e0
    classDef storage fill:#fce4ec
    classDef output fill:#e0f2f1
    classDef error fill:#ffebee
    
    class A userInput
    class B,F agent
    class G,G1,G2,G3,H,H1,H2,H3 tools
    class C,K,L decision
    class G3,H3,I,Q,R,X storage
    class W,Y output
    class Z error
```

## Workflow Components Breakdown

### 1. **Main Components**
- **CodingAgent**: Supervisor agent that orchestrates the workflow
- **generate_code Tool**: Code generation via AWS Bedrock/Claude
- **validate_code Tool**: Static analysis and validation
- **Iterative Loop**: Up to 3 iterations for quality improvement

### 2. **Tool Orchestration**
```mermaid
sequenceDiagram
    participant User
    participant Agent as Strands Agent
    participant GenTool as generate_code
    participant ValTool as validate_code
    participant Bedrock as AWS Bedrock
    participant Storage as Global Storage
    
    User->>Agent: Requirement
    Agent->>GenTool: Generate code request
    GenTool->>Bedrock: API call (Claude 3.5 Sonnet)
    Bedrock-->>GenTool: Generated Python code
    GenTool->>Storage: Store code globally
    
    Agent->>ValTool: Validate generated code
    ValTool->>ValTool: AST parsing & analysis
    ValTool->>Storage: Store validation results
    
    Agent->>Storage: Extract results
    Agent->>Agent: Analyze quality metrics
    
    alt Issues > Threshold
        Agent->>Agent: Prepare feedback
        Agent->>GenTool: Regenerate improved code
    else Quality acceptable
        Agent->>User: Return final code
    end
```

### 3. **Iterative Improvement Process**
```mermaid
flowchart LR
    A[Initial Code] --> B[Validation]
    B --> C{Issues > 5?}
    C -->|Yes| D[Categorize Issues<br/>- Missing docstrings<br/>- Type hints<br/>- Error handling<br/>- Syntax errors]
    D --> E[Create Feedback Summary]
    E --> F[Enhanced Prompt]
    F --> G[Regenerate Code]
    G --> B
    C -->|No| H[Final Code]
    
    style A fill:#e3f2fd
    style H fill:#e8f5e8
    style C fill:#fff3e0
```

### 4. **Quality Metrics Tracking**
Each iteration tracks:
- **Issues Count**: Number of validation problems found
- **Duration**: Time taken for the iteration
- **Code Length**: Character count of generated code
- **Validation Count**: Number of validation checks performed

### 5. **Best Result Preservation**
The system maintains the best result across all iterations:
- Lowest issue count
- Valid code (not empty)
- Complete validation results
- Comprehensive metrics

This architecture ensures robust, high-quality code generation through intelligent feedback loops and continuous improvement.
