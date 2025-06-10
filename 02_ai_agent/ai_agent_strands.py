"""
Python Coding Agent using Strands SDK

This agent orchestrates code generation and validation tools to create high-quality Python code
based on user requirements.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
import boto3
from dotenv import load_dotenv
import ast
from datetime import datetime
from pathlib import Path

# Import Strands SDK
from strands import tool, Agent

# Load environment variables
load_dotenv()

# Global storage for tool results (temporary solution)
_last_generated_code = ""
_last_validation_results = []

@tool
def generate_code(requirement: str) -> str:
    """
    Generates Python code based on a functional requirement using AI.
    
    Args:
        requirement: The functional requirement to implement in Python
    
    Returns:
        Generated Python code as a string
    """
    # Create a boto session for code generation
    session = boto3.Session(
        region_name=os.getenv("AWS_REGION"),
        profile_name=os.getenv("AWS_PROFILE"),
    )
    
    # Create bedrock runtime client
    bedrock_runtime = session.client('bedrock-runtime')
    
    # Construct the prompt for code generation
    prompt = f"""
Human: Please generate Python code that implements the following requirement:

{requirement}

Requirements for the generated code:
1. Include proper type hints
2. Add comprehensive docstrings following Google/Sphinx style
3. Implement proper error handling where appropriate
4. Follow PEP 8 style guidelines
5. Include input validation where necessary
6. Make the code production-ready and well-documented

Please provide only the Python code without any additional explanation or markdown formatting.
Assistant:"""
    
    # Call the Bedrock AI model for code generation using the Invoke Model API
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "temperature": 0.1,
            "top_p": 0.9,
            "messages": [
                {
                    "role": "user",
                    "content": f"""Please generate Python code that implements the following requirement:

{requirement}

Requirements for the generated code:
1. Include proper type hints
2. Add comprehensive docstrings following Google/Sphinx style
3. Implement proper error handling where appropriate
4. Follow PEP 8 style guidelines
5. Include input validation where necessary
6. Make the code production-ready and well-documented

Please provide only the Python code without any additional explanation or markdown formatting."""
                }
            ]
        })
        
        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        # Extract the generated code from the response
        response_body = json.loads(response['body'].read())
        code = response_body['content'][0]['text']
        
        # Store globally for access after agent call
        global _last_generated_code
        _last_generated_code = code.strip()
        
        return code
        
    except Exception as e:
        error_msg = f"Error calling Bedrock model: {str(e)}"
        print(f"❌ {error_msg}")
        # Return a fallback simple implementation for basic requirements
        if "add" in requirement.lower() and "number" in requirement.lower():
            return """def add_numbers(a: float, b: float) -> float:
    \"\"\"Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of the two numbers
    \"\"\"
    return a + b"""
        else:
            raise Exception(error_msg)

@tool
def validate_code(code: str, requirement: str) -> List[str]:
    """
    Validates the generated Python code against the functional requirement.
    
    Args:
        code: The generated Python code to validate
        requirement: The functional requirement to validate against
    
    Returns:
        A list of validation messages (errors or warnings)
    """
    messages = []
    
    # Perform static analysis on the code
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        messages.append(f"Syntax error in generated code: {e}")
        return messages
    
    # Store validation results globally
    global _last_validation_results
    _last_validation_results = []
    
    # Check for missing docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not ast.get_docstring(node):
            messages.append(f"Missing docstring for {node.name}")
    
    # Check for type hints
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not node.returns:
                messages.append(f"Missing return type hint for function '{node.name}'")
            for arg in node.args.args:
                if not arg.annotation:
                    messages.append(f"Missing type hint for parameter '{arg.arg}' in function '{node.name}'")
    
    # Check for error handling
    has_try_except = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    if not has_try_except and "error" not in requirement.lower():
        messages.append("Consider adding error handling with try/except blocks")
    
    # Test execution if possible (but don't run unit tests automatically)
    try:
        compile(code, '<string>', 'exec')
        messages.append("Code compiled successfully")
    except Exception as e:
        messages.append(f"Compilation error: {e}")
    
    # Store results globally and return
    _last_validation_results = messages
    return messages

class CodingAgent:
    """Supervisor agent that orchestrates code generation and validation tools."""
    
    def __init__(self):
        self.session_data = {
            "agent_config": {
                "framework": "Strands SDK",
                "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "max_tokens": "4096",
                "max_retries": "3"
            },
            "scenarios": []
        }
        
        # Create the agent using Strands SDK with explicit model configuration
        from strands.models import BedrockModel
        
        # Configure Bedrock model with the correct model ID
        bedrock_model = BedrockModel(
            boto_session=boto3.Session(
                region_name=os.getenv("AWS_REGION"),
                profile_name=os.getenv("AWS_PROFILE"),
            ),
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            max_tokens=4000,
            temperature=0.1,
            streaming=True
        )
        
        self.agent = Agent(
            model=bedrock_model,
            system_prompt="""
        You are an advanced Python Coding Agent with iterative improvement capabilities. You help users implement high-quality Python code through an intelligent feedback loop system.
        
        Your enhanced workflow:
        1. Analyze the user's requirement thoroughly
        2. Generate Python code using the generate_code tool
        3. Validate the code using the validate_code tool
        4. If more than 5 validation issues are found, automatically improve and regenerate
        5. Continue iterating until code quality meets high standards
        6. Provide the final, production-ready code to the user
        
        Quality Standards:
        - Write clean, efficient, and well-documented Python code
        - Include comprehensive error handling with specific exception types
        - Use type hints throughout the code
        - Follow PEP 8 style guidelines and Python best practices
        - Add detailed docstrings for all functions and classes
        - Ensure code is production-ready and maintainable
        
        Iterative Improvement Process:
        - When validation finds >5 issues, focus on the most critical problems first
        - Address syntax/compilation errors immediately
        - Prioritize missing docstrings and type hints
        - Enhance error handling and code structure
        - Aim to reduce validation issues with each iteration
        
        When presenting the final code, explain:
        - How the code works and its key features
        - Any design decisions and architectural choices
        - How to use the code with examples
        - Any improvements made during the iterative process
        """,
            tools=[generate_code, validate_code]
        )
    
    async def run_workflow(self, requirement: str) -> Dict[str, Any]:
        """
        Run the Python coding agent workflow with integrated reporting and iterative improvement.
        
        Args:
            requirement: The functional requirement to implement in Python
        
        Returns:
            Dictionary containing the final code and process information
        """
        start_time = time.time()
        
        # Initialize iteration tracking
        max_iterations = 3
        current_iteration = 0
        improvement_threshold = 5  # Regenerate if more than 5 issues
        
        # Variables to track the best results across iterations
        best_generated_code = ""
        best_validation_results = []
        best_issues_count = float('inf')
        
        # Run the agent workflow with iterative improvement
        try:
            user_message = f"""
        I need you to implement the following Python requirement: {requirement}
        
        Please use the generate_code tool to create the code, then use the validate_code tool to check it.
        If there are any issues, please fix them and validate again.
        Present the final working code with a clear explanation.
        """
            
            while current_iteration < max_iterations:
                current_iteration += 1
                print(f"🔄 Starting iteration {current_iteration}/{max_iterations}")
                
                # Add iteration context to the message
                if current_iteration > 1:
                    user_message = f"""
        I need you to improve the previous Python implementation for: {requirement}
        
        The previous validation found issues that need to be addressed. Please:
        1. Generate improved code using the generate_code tool that addresses all validation feedback
        2. Validate the improved code using the validate_code tool
        3. Present the final working code with explanations of improvements made
        
        Focus on creating production-ready, high-quality Python code.
        """
                
                response = self.agent(user_message)
                
                # Calculate execution time for this iteration
                iteration_time = time.time() - start_time
                
                # Extract response content
                response_content = ""
                
                # Handle Strands AgentResult response structure
                if hasattr(response, 'message') and isinstance(response.message, dict):
                    if 'content' in response.message and isinstance(response.message['content'], list):
                        # Extract text from content list
                        content_parts = []
                        for item in response.message['content']:
                            if isinstance(item, dict) and 'text' in item:
                                content_parts.append(item['text'])
                        response_content = ' '.join(content_parts)
                    else:
                        response_content = str(response.message)
                else:
                    # Fallback to string representation
                    response_content = str(response)
                
                # Extract generated code from global storage (set by tools during execution)
                global _last_generated_code, _last_validation_results
                generated_code = _last_generated_code
                validation_results = _last_validation_results
                
                print(f"🔍 Iteration {current_iteration} - Extracted from global storage:")
                print(f"  Generated code: {len(generated_code)} chars")
                print(f"  Validation results: {len(validation_results)} items")
                
                # Analyze validation results to count actual issues
                issues_count = 0
                syntax_errors = 0
                compilation_errors = 0
                
                for msg in validation_results:
                    msg_lower = msg.lower()
                    if "syntax error" in msg_lower:
                        syntax_errors += 1
                        issues_count += 1
                    elif "compilation error" in msg_lower:
                        compilation_errors += 1
                        issues_count += 1
                    elif any(issue_type in msg_lower for issue_type in [
                        "missing docstring", "missing type hint", "missing return type hint",
                        "consider adding error handling"
                    ]):
                        issues_count += 1
                
                print(f"📊 Validation Analysis:")
                print(f"  Total issues found: {issues_count}")
                print(f"  Syntax errors: {syntax_errors}")
                print(f"  Compilation errors: {compilation_errors}")
                print(f"  Improvement threshold: {improvement_threshold}")
                
                # Preserve the best results (lowest issue count with valid code)
                if generated_code and (issues_count < best_issues_count or not best_generated_code):
                    best_generated_code = generated_code
                    best_validation_results = validation_results.copy()
                    best_issues_count = issues_count
                    print(f"🏆 New best result: {issues_count} issues, {len(generated_code)} chars code")
                
                # Check if we should continue iterating
                should_continue = (
                    issues_count > improvement_threshold and 
                    current_iteration < max_iterations and
                    syntax_errors == 0 and compilation_errors == 0  # Don't iterate on critical errors
                )
                
                if should_continue:
                    print(f"🔄 Issues ({issues_count}) exceed threshold ({improvement_threshold})")
                    print(f"   Continuing to iteration {current_iteration + 1} for improvement...")
                    
                    # Prepare feedback for next iteration
                    feedback_summary = self._create_feedback_summary(validation_results, issues_count)
                    user_message = f"""
        The previous code for requirement: {requirement}
        
        Validation found {issues_count} issues that need improvement:
        {feedback_summary}
        
        Please generate improved code that addresses these specific issues:
        1. Use the generate_code tool to create better code
        2. Use the validate_code tool to verify improvements
        3. Focus on reducing the number of validation issues
        
        Target: Reduce issues to {improvement_threshold} or fewer.
        """
                    continue
                else:
                    print(f"✅ Stopping iteration - Issues ({issues_count}) within acceptable range")
                    break
            
            # Final extraction - use the best results from all iterations
            final_generated_code = best_generated_code if best_generated_code else generated_code
            final_validation_results = best_validation_results if best_validation_results else validation_results
            final_issues_count = best_issues_count if best_issues_count != float('inf') else issues_count
            
            print(f"🔍 Final extraction after {current_iteration} iterations:")
            print(f"  Best generated code: {len(final_generated_code)} chars")
            print(f"  Best validation results: {len(final_validation_results)} items")
            print(f"  Best issues count: {final_issues_count}")
            
            execution_time = time.time() - start_time
            scenario_data = {
                "requirement": requirement,
                "generated_code": final_generated_code,
                "validation_results": final_validation_results,
                "execution_time": execution_time,
                "success": bool(final_generated_code) and len([msg for msg in final_validation_results if "syntax error" in msg.lower() or "compilation error" in msg.lower()]) == 0,
                "code_metrics": self.analyze_code_quality(final_generated_code) if final_generated_code else {},
                "iterations_used": current_iteration,
                "final_issues_count": final_issues_count
            }
            
            self.session_data["scenarios"].append(scenario_data)
            
            return {
                "success": bool(final_generated_code),
                "generated_code": final_generated_code,
                "validation_results": final_validation_results,
                "execution_time": execution_time,
                "explanation": response_content,
                "code_metrics": scenario_data["code_metrics"],
                "iterations_used": current_iteration,
                "final_issues_count": final_issues_count
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_scenario = {
                "requirement": requirement,
                "error": str(e),
                "execution_time": execution_time,
                "success": False,
                "iterations_used": current_iteration
            }
            self.session_data["scenarios"].append(error_scenario)
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "iterations_used": current_iteration
            }
    
    def _create_feedback_summary(self, validation_results: List[str], issues_count: int) -> str:
        """Create a structured feedback summary for iterative improvement."""
        feedback_categories = {
            "Missing Documentation": [],
            "Type Hint Issues": [],
            "Error Handling": [],
            "Code Quality": [],
            "Syntax/Compilation": []
        }
        
        for msg in validation_results:
            msg_lower = msg.lower()
            if "missing docstring" in msg_lower:
                feedback_categories["Missing Documentation"].append(msg)
            elif "missing type hint" in msg_lower or "missing return type hint" in msg_lower:
                feedback_categories["Type Hint Issues"].append(msg)
            elif "error handling" in msg_lower:
                feedback_categories["Error Handling"].append(msg)
            elif "syntax error" in msg_lower or "compilation error" in msg_lower:
                feedback_categories["Syntax/Compilation"].append(msg)
            else:
                feedback_categories["Code Quality"].append(msg)
        
        feedback_summary = f"Total Issues: {issues_count}\n\n"
        
        for category, issues in feedback_categories.items():
            if issues:
                feedback_summary += f"**{category}:**\n"
                for issue in issues[:3]:  # Limit to top 3 issues per category
                    feedback_summary += f"  - {issue}\n"
                if len(issues) > 3:
                    feedback_summary += f"  - ... and {len(issues) - 3} more\n"
                feedback_summary += "\n"
        
        return feedback_summary
    
    def analyze_code_quality(self, code: str) -> Dict[str, Any]:
        """Analyze the quality and characteristics of generated code."""
        if not code:
            return {}
        
        metrics = {
            "lines_of_code": len(code.split('\n')),
            "has_docstring": '"""' in code or "'''" in code,
            "has_type_hints": ':' in code and '->' in code,
            "has_error_handling": 'try:' in code or 'except' in code or 'raise' in code,
            "function_count": code.count('def '),
            "class_count": code.count('class '),
            "import_count": code.count('import ') + code.count('from '),
        }
        
        # Advanced metrics
        try:
            tree = ast.parse(code)
            metrics.update({
                "conditional_statements": code.count('if ') + code.count('elif ') + code.count('else:'),
                "loops": code.count('for ') + code.count('while '),
                "nested_blocks": code.count('    ') // 4  # Rough estimate
            })
            
            # Check syntax validity
            ast.parse(code)
            metrics["syntax_valid"] = True
        except SyntaxError as e:
            metrics["syntax_valid"] = False
            metrics["syntax_error"] = str(e)
        
        return metrics
    
    def generate_session_report(self) -> Optional[str]:
        """Generate a comprehensive session report."""
        if not self.session_data["scenarios"]:
            return None
        
        # Generate report directly without        # Generate report directly without external dependencieses
        scenarios = self.session_data["scenarios"]
        agent_config = self.session_data["agent_config"]
        
        # Calculate metrics
        total_scenarios = len(scenarios)
        successful_scenarios = sum(1 for s in scenarios if s.get("success", False))
        success_rate = (successful_scenarios / total_scenarios) * 100 if total_scenarios > 0 else 0
        
        total_execution_time = sum(s.get("execution_time", 0) for s in scenarios)
        avg_execution_time = total_execution_time / total_scenarios if total_scenarios > 0 else 0
        
        # Quality metrics
        total_lines = sum(s.get("code_metrics", {}).get("lines_of_code", 0) for s in scenarios if s.get("success"))
        docstring_count = sum(1 for s in scenarios if s.get("success") and s.get("code_metrics", {}).get("has_docstring", False))
        type_hints_count = sum(1 for s in scenarios if s.get("success") and s.get("code_metrics", {}).get("has_type_hints", False))
        error_handling_count = sum(1 for s in scenarios if s.get("success") and s.get("code_metrics", {}).get("has_error_handling", False))
        
        # Iterative improvement metrics
        total_iterations = sum(s.get("iterations_used", 1) for s in scenarios)
        avg_iterations = total_iterations / total_scenarios if total_scenarios > 0 else 0
        scenarios_with_improvement = sum(1 for s in scenarios if s.get("iterations_used", 1) > 1)
        improvement_rate = (scenarios_with_improvement / total_scenarios) * 100 if total_scenarios > 0 else 0
        
        # Generate markdown report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Strands Python Coding Agent - Session Report

**Generated:** {timestamp}  
**Framework:** {agent_config.get('framework', 'Strands SDK')}  
**Model:** {agent_config.get('model_id', 'Claude 3.5 Sonnet')}  
**Status:** {'🟢 SUCCESS' if success_rate >= 80 else '🟡 PARTIAL' if success_rate >= 50 else '🔴 NEEDS IMPROVEMENT'}

---

## 📊 Executive Summary

| Metric | Value | Status |
|--------|--------|--------|
| **Total Scenarios** | {total_scenarios} | - |
| **Successful** | {successful_scenarios}/{total_scenarios} | {success_rate:.1f}% |
| **Total Execution Time** | {total_execution_time:.2f}s | - |
| **Average Time per Scenario** | {avg_execution_time:.2f}s | - |
| **Total Lines Generated** | {total_lines:,} | - |
| **Average Iterations** | {avg_iterations:.1f} | - |
| **Scenarios with Improvement** | {scenarios_with_improvement}/{total_scenarios} | {improvement_rate:.1f}% |

---

## 🏆 Quality Metrics

| Quality Aspect | Count | Percentage |
|----------------|-------|------------|
| **Docstring Coverage** | {docstring_count}/{successful_scenarios} | {(docstring_count/successful_scenarios*100) if successful_scenarios > 0 else 0:.1f}% |
| **Type Hints Usage** | {type_hints_count}/{successful_scenarios} | {(type_hints_count/successful_scenarios*100) if successful_scenarios > 0 else 0:.1f}% |
| **Error Handling** | {error_handling_count}/{successful_scenarios} | {(error_handling_count/successful_scenarios*100) if successful_scenarios > 0 else 0:.1f}% |

---

## 🔄 Iterative Improvement Analysis

| Metric | Value |
|--------|--------|
| **Total Iterations Used** | {total_iterations} |
| **Average Iterations per Scenario** | {avg_iterations:.1f} |
| **Scenarios Requiring Improvement** | {scenarios_with_improvement} |
| **Improvement Success Rate** | {improvement_rate:.1f}% |

---

## 📝 Scenario Details

"""
        
        for i, scenario in enumerate(scenarios, 1):
            status_emoji = "✅" if scenario.get("success", False) else "❌"
            exec_time = scenario.get("execution_time", 0)
            iterations = scenario.get("iterations_used", 1)
            final_issues = scenario.get("final_issues_count", 0)
            
            report += f"""### Scenario {i}: {status_emoji}
**Requirement:** {scenario.get("requirement", "N/A")[:100]}...  
**Execution Time:** {exec_time:.2f}s  
**Iterations Used:** {iterations}  
**Final Issues Count:** {final_issues}  
**Status:** {'SUCCESS' if scenario.get("success", False) else 'FAILED'}  

"""
            
            if scenario.get("success") and scenario.get("code_metrics"):
                metrics = scenario["code_metrics"]
                report += f"""**Code Metrics:**
- Lines of Code: {metrics.get("lines_of_code", 0)}
- Functions: {metrics.get("function_count", 0)}
- Classes: {metrics.get("class_count", 0)}
- Has Docstring: {'✅' if metrics.get("has_docstring", False) else '❌'}
- Type Hints: {'✅' if metrics.get("has_type_hints", False) else '❌'}
- Error Handling: {'✅' if metrics.get("has_error_handling", False) else '❌'}

"""
            
            if scenario.get("error"):
                report += f"""**Error:** {scenario["error"]}

"""
            
            report += "---\n\n"
        
        # Add generated code samples section
        successful_scenarios_with_code = [s for s in scenarios if s.get("success") and s.get("generated_code")]
        if successful_scenarios_with_code:
            report += f"""## 🎯 Generated Code Samples

"""
            for i, scenario in enumerate(successful_scenarios_with_code, 1):
                code = scenario.get("generated_code", "")
                requirement = scenario.get("requirement", "")
                
                # Truncate requirement for header
                req_header = requirement.replace('\n', ' ')[:50] + "..." if len(requirement) > 50 else requirement
                
                report += f"""### Sample {i}: {req_header}

**Requirement:** {requirement}

**Generated Code:**
```python
{code}
```

**Code Metrics:**
- Lines of Code: {scenario.get("code_metrics", {}).get("lines_of_code", 0)}
- Functions: {scenario.get("code_metrics", {}).get("function_count", 0)}
- Classes: {scenario.get("code_metrics", {}).get("class_count", 0)}

---

"""
        
        # Add recommendations
        report += f"""## 💡 Recommendations

### Performance
- **Overall Success Rate:** {success_rate:.1f}% - {'Excellent' if success_rate >= 90 else 'Good' if success_rate >= 70 else 'Needs Improvement'}
- **Average Execution Time:** {avg_execution_time:.2f}s per scenario

### Code Quality Improvements
"""
        
        if successful_scenarios > 0:
            docstring_rate = (docstring_count/successful_scenarios*100)
            type_hints_rate = (type_hints_count/successful_scenarios*100)
            error_handling_rate = (error_handling_count/successful_scenarios*100)
            
            if docstring_rate < 80:
                report += f"- **Docstring Coverage:** {docstring_rate:.1f}% - Consider improving documentation\n"
            if type_hints_rate < 70:
                report += f"- **Type Hints:** {type_hints_rate:.1f}% - Add more type annotations for better code clarity\n"
            if error_handling_rate < 60:
                report += f"- **Error Handling:** {error_handling_rate:.1f}% - Implement more robust error handling\n"
        
        report += f"""
### Next Steps
1. Review failed scenarios and analyze common failure patterns
2. Optimize prompts for better code generation quality  
3. Consider increasing validation strictness for production readiness
4. Monitor execution times and optimize for performance

---

**Report Generated:** {timestamp}  
**Agent Version:** Strands SDK v1.0  
**Total Scenarios Processed:** {total_scenarios}
"""
        
        return report
    
    def save_session_report(self, filename: Optional[str] = None) -> Optional[str]:
        """Save the session report to a file."""
        report = self.generate_session_report()
        if not report:
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"strands_agent_session_report_{timestamp}.md"
        
        reports_dir = Path(__file__).parent
        filepath = reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(filepath)

# Main execution function
async def main():
    """Main function to test the coding agent with comprehensive reporting."""
    print("🚀 Strands Python Coding Agent with Integrated Reporting")
    print("=" * 65)
    
    agent = CodingAgent()
    
    # Test scenarios from 01_ai_workflow.py with different difficulty levels
    test_scenarios = [
        # Simple task
        """Create a Python function that calculates the factorial of a number using recursion.
        The function should handle edge cases like negative numbers and zero, and include comprehensive unit tests
        to validate its correctness.""",
        
        # Moderate task  
        """Create a function that analyzes a CSV file containing student grades and calculates comprehensive statistics
        including mean, median, standard deviation, letter grade distribution, and identifies students who need academic intervention
        (below 70% average). The function should handle missing data, validate input formats, and return a detailed report
        with visualizations.""",
        
        # Complex task
        """Create a Python function that implements a multi-threaded web scraper to extract product prices
        from an e-commerce website. The scraper should handle pagination, respect robots.txt rules, and implement error handling
        for network issues. It should return a structured JSON object with product names, prices, and URLs.
        Additionally, include comprehensive unit tests to validate the scraper's functionality and performance under load.
        The function should also log its activity and handle rate limiting to avoid being blocked by the website."""
    ]
    
    print(f"📝 Running {len(test_scenarios)} comprehensive test scenarios...")
    print(f"🔧 Agent Configuration:")
    print(f"   - Model: Claude 3.5 Sonnet (via AWS Bedrock)")
    print(f"   - Max Tokens: 4096")
    print(f"   - Framework: Strands SDK")
    print(f"   - Real-time Reporting: Enabled")
    
    # Run each test scenario with real-time feedback
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*20} Scenario {i}/{len(test_scenarios)} {'='*20}")
        print(f"📋 Requirement: {scenario}")
        print(f"⏱️  Starting execution...")
        
        try:
            result = await agent.run_workflow(scenario)
            
            # Check if result is properly structured before accessing keys
            if not isinstance(result, dict):
                print(f"❌ Error: Expected dict result but got {type(result)}: {result}")
                continue
                
            # Safely access result keys with defaults
            exec_time = result.get('execution_time', 0)
            generated_code = result.get('generated_code', '')
            status = "✅ SUCCESS" if generated_code else "❌ FAILED"
            
            print(f"🎯 Result: {status}")
            print(f"⚡ Execution Time: {exec_time:.2f}s")
            
            if generated_code:
                code_length = len(generated_code)
                lines_count = len(generated_code.split('\n'))
                print(f"📄 Code Generated: {code_length} characters, {lines_count} lines")
                
                # Quick quality indicators
                has_docstring = '"""' in generated_code or "'''" in generated_code
                has_type_hints = ':' in generated_code and '->' in generated_code
                has_error_handling = 'try:' in generated_code or 'except' in generated_code or 'raise' in generated_code
                
                print(f"📊 Quick Quality Check:")
                print(f"   - Docstring: {'✅' if has_docstring else '❌'}")
                print(f"   - Type Hints: {'✅' if has_type_hints else '❌'}")
                print(f"   - Error Handling: {'✅' if has_error_handling else '❌'}")
                
                validation_results = result.get("validation_results", [])
                if validation_results:
                    print(f"\n🔍 Validation Results:")
                    for msg in validation_results:
                        print(f"  • {msg}")
            else:
                print("❌ No code was generated")
                print(f"🔍 Debug - Full result structure: {result}")
                
        except Exception as e:
            import traceback
            print(f"❌ Error in scenario {i}:")
            print(f"   Error Type: {type(e).__name__}")
            print(f"   Error Message: {str(e)}")
            print(f"   Full Traceback:")
            print(f"   {traceback.format_exc()}")
            
            # Try to provide more context about where the error occurred
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"   Root Cause: {e.__cause__}")
            
            # Add debugging info for common issues
            if "generated_code" in str(e):
                print(f"   💡 This appears to be a KeyError for 'generated_code'")
                print(f"   💡 The issue is likely in the response parsing logic")
            elif "AWS" in str(e) or "bedrock" in str(e).lower():
                print(f"   💡 This appears to be an AWS/Bedrock configuration issue")
                print(f"   💡 Check your AWS credentials and region settings")
            elif "strands" in str(e).lower():
                print(f"   💡 This appears to be a Strands SDK issue")
                print(f"   💡 Check if the Strands SDK is properly installed and configured")
    
    # Generate comprehensive report with enhanced metrics
    print(f"\n{'='*20} GENERATING COMPREHENSIVE REPORT {'='*20}")
    
    try:
        report_path = agent.save_session_report()
        
        if report_path:
            print(f"✅ Comprehensive report generated successfully!")
            print(f"📁 Report Location: {report_path}")
            
            # Display final summary metrics
            session_data = agent.session_data
            scenarios = session_data.get("scenarios", [])
            successful = sum(1 for s in scenarios if s.get("success", False))
            total_time = sum(s.get("execution_time", 0) for s in scenarios)
            avg_time = total_time / len(scenarios) if scenarios else 0
            
            print(f"\n📈 FINAL SESSION SUMMARY:")
            print(f"   📊 Total Scenarios: {len(scenarios)}")
            print(f"   ✅ Successful: {successful}/{len(scenarios)} ({successful/len(scenarios)*100:.1f}%)")
            print(f"   ⏱️  Total Execution Time: {total_time:.2f}s")
            print(f"   📈 Average Time per Scenario: {avg_time:.2f}s")
            
            # Calculate and display quality metrics
            if scenarios:
                # Quick quality analysis
                total_lines = 0
                docstring_count = 0
                type_hints_count = 0
                error_handling_count = 0
                
                for scenario in scenarios:
                    if scenario.get("success") and scenario.get("code_metrics"):
                        metrics = scenario["code_metrics"]
                        total_lines += metrics.get("lines_of_code", 0)
                        if metrics.get("has_docstring", False):
                            docstring_count += 1
                        if metrics.get("has_type_hints", False):
                            type_hints_count += 1
                        if metrics.get("has_error_handling", False):
                            error_handling_count += 1
                
                print(f"\n🏆 QUALITY METRICS:")
                print(f"   📝 Total Lines Generated: {total_lines}")
                if successful > 0:
                    print(f"   📚 Docstring Coverage: {docstring_count}/{successful} ({docstring_count/successful*100:.1f}%)")
                    print(f"   🔤 Type Hints Usage: {type_hints_count}/{successful} ({type_hints_count/successful*100:.1f}%)")
                    print(f"   🛡️  Error Handling: {error_handling_count}/{successful} ({error_handling_count/successful*100:.1f}%)")
            
            print(f"\n📖 Open the report file to see detailed analysis, code samples, and recommendations!")
            
        else:
            print("❌ Failed to generate comprehensive report")
            
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
    
    print(f"\n🏁 Agent session completed! Check the generated report for full analysis.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
