import logging
import logging
import os
import time
import datetime
from typing import Optional, List

import anthropic
from instructor import Instructor
import instructor
from pydantic import BaseModel, Field

from burr.core import ApplicationBuilder, State, action, Application, expr
from burr.core.graph import GraphBuilder

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_RETRIES = 5
WARNING_THRESHOLD = 5
ENABLE_AI_ANALYSIS = False  # Set to False to disable AI analysis step
ENABLE_CODE_EXECUTION = True  # Set to True to enable actual Python code execution testing

class CodeAnalysisResponse(BaseModel):
    """AI-powered code analysis response with detailed quality assessment."""
    
    overall_quality_score: int = Field(
        description="Overall code quality score from 1-10 (10 being perfect production-ready code)"
    )
    
    security_assessment: str = Field(
        description="Detailed security analysis identifying potential vulnerabilities and security best practices"
    )
    
    performance_analysis: str = Field(
        description="Performance evaluation including time/space complexity, bottlenecks, and optimization suggestions"
    )
    
    maintainability_score: int = Field(
        description="Maintainability score from 1-10 based on readability, modularity, and code organization"
    )
    
    test_coverage_assessment: str = Field(
        description="Analysis of test completeness, edge cases covered, and testing best practices"
    )
    
    code_smells: List[str] = Field(
        description="List of code smells, anti-patterns, or areas for improvement"
    )
    
    positive_aspects: List[str] = Field(
        description="List of well-implemented aspects and good practices found in the code"
    )
    
    improvement_suggestions: List[str] = Field(
        description="Specific, actionable suggestions for improving the code quality"
    )
    
    # production_readiness: bool = Field(
    #     description="Whether the code is ready for production deployment"
    # )
    
    detailed_feedback: str = Field(
        description="Comprehensive feedback explaining the analysis and recommendations"
    )

class PythonCodeGenerationResponse(BaseModel):
    """Structured response for Python code generation that ensures high-quality, well-tested, and maintainable code."""
    
    function_name: str = Field(
        description="The name of the generated Python function"
    )
    
    code: str = Field(
        description="""The complete Python function code with comprehensive docstring, type hints, and error handling.
        Do not include markdown backticks like ```python and ``` at the start or end of the code block."""
    )
    
    explanation: str = Field(
        description="A detailed explanation of what the function does, how it works, and design decisions"
    )
    
    dependencies: Optional[List[str]] = Field(
        default=None,
        description="List of required imports or dependencies for the function"
    )
    
    test_code: str = Field(
        description="""Complete unit test code using pytest that thoroughly tests the function including edge cases.
        Do not include markdown backticks like ```python and ``` at the start or end of the code block."""
    )
    
    usage_examples: List[str] = Field(
        description="Multiple practical usage examples demonstrating the function's capabilities"
    )
    
    # complexity_analysis: str = Field(
    #     description="Detailed time and space complexity analysis with Big O notation"
    # )
    
    # maintainability_notes: str = Field(
    #     description="Notes on code maintainability, potential improvements, and best practices followed"
    # )
    
    # efficiency_considerations: str = Field(
    #     description="Explanation of efficiency optimizations and performance considerations"
    # )

@action(reads=["not_good_enough", "retries", "check_results", "ai_analysis", "workflow_start_time", "total_tokens_used", "generation_tokens", "api_call_count", "generation_times"], writes=["generated_python_response", "retries", "task", "workflow_start_time", "total_tokens_used", "generation_tokens", "api_call_count", "generation_times"])
def code_generator(state: State, instructor_client: Instructor, task: str) -> State:
    # Initialize workflow timing on first run
    workflow_start_time = state.get("workflow_start_time")
    if workflow_start_time is None:
        workflow_start_time = time.time()
    
    # Track generation start time
    generation_start_time = time.time()
    
    retries = state["retries"]
    not_good_enough = state["not_good_enough"]
    check_results = state.get("check_results", "")
    ai_analysis = state.get("ai_analysis", "")
    
    # Get existing tracking data
    total_tokens_used = state.get("total_tokens_used", 0)
    generation_tokens = state.get("generation_tokens", 0)
    api_call_count = state.get("api_call_count", 0)
    generation_times = state.get("generation_times", [])
    
    # On retries, read task from state; on first run, use the parameter
    if not_good_enough and state.get("task"):
        task = state["task"]  # Use task from state for retries
    # else: use the task parameter passed to the function (first run)
    
    if not_good_enough:
        logger.info(f"🔄 Code Generator Step (Retry {retries}) - Regenerating code based on quality feedback")
        
        # Get preview of why retry was triggered for better context
        retry_reasons = []
        if check_results:
            critical_count = check_results.count('✗ CRITICAL:')
            warning_count = check_results.count('⚠ Warning:') + check_results.count('⚠️ Warning:')
            if critical_count > 0:
                retry_reasons.append(f"{critical_count} critical issues")
            elif warning_count > WARNING_THRESHOLD:
                retry_reasons.append(f"{warning_count} warnings (exceeds limit of {WARNING_THRESHOLD})")
        
        retry_reason_text = " + ".join(retry_reasons) if retry_reasons else "quality issues detected"
        
        # Enhanced visual output for retries with emojis and ASCII art
        print("\n" + "🚨" + "=" * 78 + "🚨")
        print("🔥 🔄 ⚡ ⭐ RETRY MODE ACTIVATED - LEARNING FROM MISTAKES ⭐ ⚡ 🔄 🔥")
        print("🚨" + "=" * 78 + "🚨")
        print(f"🔢 ATTEMPT NUMBER: {retries + 1} of {MAX_RETRIES}")
        print(f"🚨 RETRY REASON: Previous code failed due to {retry_reason_text}")
        print(f"💥 MISSION: Fix quality issues and generate superior code")
        print(f"🧠 LEARNING SOURCE: Previous quality feedback + AI analysis")
        print(f"🎯 TARGET: Production-ready, bulletproof code")
        print("🚨" + "=" * 78 + "🚨")
        print("⚠️  PREVIOUS ATTEMPT FAILED QUALITY GATES - ADAPTING STRATEGY...")
        print("🔧 Applying hard-learned lessons to generate better code...")
        print("💪 This time will be different - incorporating ALL feedback!")
        print(f"🎪 FOCUS: Addressing {retry_reason_text} with targeted improvements")
        print("🚨" + "=" * 78 + "🚨")
    else:
        logger.info(f"✨ Code Generator Step - Generating code for the first time")
        print("\n" + "✨" + "=" * 68 + "✨")
        print("🚀 ⭐ 🎯 INITIAL CODE GENERATION SEQUENCE INITIATED 🎯 ⭐ 🚀")
        print("✨" + "=" * 68 + "✨")

    print(f"📋 Task: {task}")
    print(f"🤖 AI Model: Claude 3.5 Sonnet via AWS Bedrock")
    print(f"⚙️ Generating: Structured Python code with comprehensive testing")
    print(f"🎪 Expected Output: Function + Tests + Documentation + Examples")
    
    if not_good_enough:
        print("🔥" + "-" * 78 + "🔥")
    else:
        print("✨" + "-" * 68 + "✨")

    retries = state["retries"] + 1 if not_good_enough else 0
    
    system_prompt = """You are an expert Python software engineer specializing in developing highly efficient,
      readable, well-tested, and maintainable Python functions. Your primary goal is to assist a user in
      generating high-quality Python code snippets or complete functions based on their specified requirements.
    """
    
    # Build user prompt - include targeted feedback if this is a retry
    if not_good_enough and (check_results or ai_analysis):
        # Extract ALL feedback types for comprehensive retry prompting
        critical_issues_list = []
        warnings_list = []
        ai_feedback_list = []
        all_quality_issues = []
        
        if check_results:
            lines = check_results.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Extract critical issues
                if '✗ CRITICAL:' in line:
                    issue = line.replace('✗ CRITICAL:', '').strip()
                    critical_issues_list.append(issue)
                    all_quality_issues.append(f"CRITICAL: {issue}")
                
                # Extract ALL warning patterns (more comprehensive)
                elif any(pattern in line for pattern in ['⚠ Warning:', '⚠️ Warning:', '⚠', 'Warning:']):
                    # Clean up the warning text
                    warning = line
                    for pattern in ['⚠ Warning:', '⚠️ Warning:', '⚠️', '⚠']:
                        warning = warning.replace(pattern, '').strip()
                    if warning and warning not in warnings_list:
                        warnings_list.append(warning)
                        all_quality_issues.append(f"WARNING: {warning}")
                
                # Extract AI assessment issues (only if AI analysis is enabled)
                elif ENABLE_AI_ANALYSIS and '🤖 AI' in line and ('Score:' in line or 'Ready:' in line):
                    ai_feedback_list.append(line.replace('🤖', '').strip())
                    all_quality_issues.append(f"AI ASSESSMENT: {line.replace('🤖', '').strip()}")
        
        # Enhanced AI analysis parsing - extract ALL relevant sections (only if AI analysis is enabled)
        if ENABLE_AI_ANALYSIS and ai_analysis:
            lines = ai_analysis.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identify sections
                if any(section in line for section in ['Security Assessment:', 'Performance Analysis:', 'Code Smells Identified:', 'Improvement Suggestions:', 'Test Coverage Assessment:']):
                    current_section = line
                    continue
                
                # Extract actionable items from each section
                elif line.startswith('• ') and current_section:
                    feedback_item = line.replace('• ', '').strip()
                    if feedback_item and feedback_item not in ai_feedback_list:
                        ai_feedback_list.append(f"{current_section.replace(':', '')} - {feedback_item}")
                        all_quality_issues.append(f"AI INSIGHT: {feedback_item}")
                
                # Extract direct quality scores and assessments
                elif any(keyword in line.lower() for keyword in ['score:', 'ready:', 'quality:', 'issue', 'problem', 'improve', 'fix', 'error']):
                    if line not in ai_feedback_list:
                        ai_feedback_list.append(line)
                        all_quality_issues.append(f"AI ASSESSMENT: {line}")
        
        # Construct COMPREHENSIVE retry prompt with ALL feedback
        user_prompt = f"""Write a Python function that performs the following: {task}.

🚨 CRITICAL: This is retry attempt #{retries + 1}. The previous code generation FAILED quality checks with {len(critical_issues_list)} critical issues and {len(warnings_list)} warnings.

🔥 COMPLETE FEEDBACK FROM PREVIOUS ATTEMPT:"""

        if critical_issues_list:
            user_prompt += f"""

🛑 CRITICAL ISSUES THAT MUST BE FIXED:"""
            for i, issue in enumerate(critical_issues_list, 1):
                user_prompt += f"""
{i}. {issue}"""

        if warnings_list:
            user_prompt += f"""

⚠️ ALL QUALITY WARNINGS TO ADDRESS:"""
            for i, warning in enumerate(warnings_list, 1):
                user_prompt += f"""
{i}. {warning}"""

        if ai_feedback_list and ENABLE_AI_ANALYSIS:
            user_prompt += f"""

🤖 AI EXPERT ANALYSIS & RECOMMENDATIONS:"""
            for i, feedback in enumerate(ai_feedback_list, 1):
                user_prompt += f"""
{i}. {feedback}"""

        # Include a comprehensive summary of ALL issues
        if all_quality_issues:
            user_prompt += f"""

📋 COMPLETE ISSUE SUMMARY ({len(all_quality_issues)} total issues):"""
            for i, issue in enumerate(all_quality_issues, 1):
                user_prompt += f"""
{i}. {issue}"""

        user_prompt += f"""

🎯 ENHANCED REQUIREMENTS FOR THIS RETRY:
1. ✅ Fix EVERY single critical issue listed above - zero tolerance for critical failures
2. ✅ Address ALL {len(warnings_list)} quality warnings to achieve production standards"""
        
        if ENABLE_AI_ANALYSIS:
            user_prompt += """
3. ✅ Implement ALL AI recommendations and expert suggestions"""
            
        ai_offset = 1 if ENABLE_AI_ANALYSIS else 0
        user_prompt += f"""
{3 + ai_offset}. ✅ Include comprehensive error handling with specific exception types
{4 + ai_offset}. ✅ Add complete type hints for all parameters, return values, and variables
{5 + ai_offset}. ✅ Write detailed Google-style docstrings with examples and parameter descriptions
{6 + ai_offset}. ✅ Create exhaustive unit tests covering ALL edge cases, errors, and normal operations
{7 + ai_offset}. ✅ Follow ALL Python best practices (PEP 8, security, performance, maintainability)
{8 + ai_offset}. ✅ Ensure ALL dependencies are properly declared and imported
{9 + ai_offset}. ✅ Make the code 100% production-ready with comprehensive documentation

💡 SUCCESS CRITERIA FOR THIS RETRY:
- ✅ ZERO critical issues (non-negotiable)
- ✅ Maximum {WARNING_THRESHOLD} warnings (significant improvement from {len(warnings_list)} warnings)
- ✅ High-quality, production-ready code that passes all quality gates
- ✅ Comprehensive test coverage with multiple test scenarios
- ✅ Clear, professional documentation and usage examples
- ✅ Addressing ALL specific feedback points from the previous attempt

⚡ CRITICAL SUCCESS FACTORS:
- Learn from EVERY piece of feedback above
- Generate code that specifically addresses each identified issue
- Implement superior error handling and input validation
- Create tests that cover scenarios mentioned in the feedback"""
        
        if ENABLE_AI_ANALYSIS:
            user_prompt += """
- Use the exact improvements suggested by the AI analysis"""
            
        user_prompt += f"""
- Ensure the function name, structure, and implementation follow all best practices

🎖️ QUALITY STANDARD: This retry must produce enterprise-grade, production-ready code that addresses every single point of feedback from the previous attempt."""
        
        print(f"🔄 Providing COMPREHENSIVE feedback:")
        print(f"   💥 {len(critical_issues_list)} critical issues to fix")
        print(f"   ⚠️ {len(warnings_list)} quality warnings to address")
        if ENABLE_AI_ANALYSIS:
            print(f"   🤖 {len(ai_feedback_list)} AI recommendations to implement")
        print(f"   📋 {len(all_quality_issues)} total feedback points provided")
        print(f"🎯 Target: Reduce {len(warnings_list)} warnings to ≤ {WARNING_THRESHOLD} and eliminate all critical issues")
    else:
        user_prompt = f"""Write a Python function that performs the following: {task}.

🎯 REQUIREMENTS:
- Include comprehensive error handling and input validation
- Add proper type hints for all parameters and return values  
- Write detailed docstrings following Google/NumPy style
- Create thorough unit tests covering edge cases and error conditions
- Follow Python best practices (PEP 8, security, performance)
- Ensure all dependencies are properly imported and used correctly
- Make the code production-ready with clear documentation and examples"""
    
    try:
        # Track API call timing and tokens
        api_start_time = time.time()
        
        generated_response = instructor_client.chat.completions.create(
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            response_model=PythonCodeGenerationResponse,
        )
        
        api_end_time = time.time()
        api_duration = api_end_time - api_start_time
        
        # Track token usage (approximate based on character count since instructor doesn't return usage)
        prompt_tokens = len(system_prompt + user_prompt) // 4  # Rough estimation: 4 chars per token
        completion_tokens = len(str(generated_response)) // 4  # Rough estimation for response
        total_call_tokens = prompt_tokens + completion_tokens
        
        # Update tracking data
        api_call_count += 1
        total_tokens_used += total_call_tokens
        generation_tokens += total_call_tokens
        generation_times.append(api_duration)
        
        logger.info(f"API Call {api_call_count}: {api_duration:.2f}s, ~{total_call_tokens} tokens")
        
        # Display comprehensive output
        print(f"\n🎯 === GENERATED CODE ARTIFACTS ===")
        print(f"⏱️ Generation Time: {api_duration:.2f}s | 🔢 Tokens: ~{total_call_tokens}")
        print(f"\n📝 Function Name: {generated_response.function_name}")
        
        print(f"\n💡 Explanation:")
        print(f"{generated_response.explanation}")
        
        print(f"\n💻 Generated Code:")
        print("```python")
        print(f"{generated_response.code}")
        print("```")
        
        if generated_response.dependencies:
            print(f"\n📦 Dependencies:")
            for dep in generated_response.dependencies:
                print(f"  • {dep}")
        
        print(f"\n🧪 Test Code:")
        print("```python")
        print(f"{generated_response.test_code}")
        print("```")
        
        print(f"\n💡 Usage Examples:")
        for i, example in enumerate(generated_response.usage_examples, 1):
            print(f"  {i}. {example}")
        
        print(f"\n✅ Code generation completed successfully!")
        logger.info(f"Successfully generated {generated_response.function_name} with comprehensive artifacts")
        
    except Exception as e:
        error_msg = f"❌ Code generation failed: {str(e)}"
        print(f"\n{error_msg}")
        logger.error(error_msg)
        return state.update(
            generated_python_response=None,
            retries=retries,
            task=task,
            workflow_start_time=workflow_start_time,
            total_tokens_used=total_tokens_used,
            generation_tokens=generation_tokens,
            api_call_count=api_call_count,
            generation_times=generation_times,
        )
    
    return state.update(
        generated_python_response=generated_response,
        retries=retries,
        task=task,
        workflow_start_time=workflow_start_time,
        total_tokens_used=total_tokens_used,
        generation_tokens=generation_tokens,
        api_call_count=api_call_count,
        generation_times=generation_times,
    )


@action(reads=["generated_python_response", "task", "total_tokens_used", "analysis_tokens", "api_call_count", "analysis_times"], writes=["not_good_enough", "check_results", "ai_analysis", "total_tokens_used", "analysis_tokens", "api_call_count", "analysis_times"])
def code_checker(state: State, instructor_client: Instructor) -> State:
    """
    Comprehensive code quality checker that validates generated Python code for production use.
    Checks for syntax, security, performance, maintainability, and best practices.
    """
    logger.info("Code Checker Step - Analyzing generated code quality")
    
    # Track analysis start time
    analysis_start_time = time.time()
    
    # Get existing tracking data
    total_tokens_used = state.get("total_tokens_used", 0)
    analysis_tokens = state.get("analysis_tokens", 0)
    api_call_count = state.get("api_call_count", 0)
    analysis_times = state.get("analysis_times", [])
    
    generated_response = state["generated_python_response"]
    task = state["task"]
    if not generated_response:
        logger.error("No generated code found in state")
        return state.update(
            not_good_enough=True,
            check_results="Error: No generated code to check"
        )
    
    check_results = []
    critical_issues = 0
    warnings = 0
    
    # 1. Syntax and Import Validation
    try:
        import ast
        import importlib.util
        
        # Parse the generated code for syntax errors
        try:
            ast.parse(generated_response.code)
            check_results.append("✓ Syntax validation passed")
        except SyntaxError as e:
            check_results.append(f"✗ CRITICAL: Syntax error - {e}")
            critical_issues += 1
        
        # Enhanced dependency validation
        if generated_response.dependencies:
            for dep in generated_response.dependencies:
                try:
                    # Basic check if import statement is valid
                    if dep.startswith('import ') or dep.startswith('from '):
                        ast.parse(dep)
                        check_results.append(f"✓ Dependency '{dep}' is syntactically valid")
                    else:
                        check_results.append(f"⚠ Warning: Dependency '{dep}' should be a proper import statement")
                        warnings += 1
                except:
                    check_results.append(f"⚠ Warning: Dependency '{dep}' may have syntax issues")
                    warnings += 1
        else:
            # Check if code uses common libraries without declaring dependencies
            common_imports = ['requests', 'pandas', 'numpy', 'matplotlib', 'beautifulsoup4', 'selenium', 'threading', 'json', 'csv', 'os', 'sys']
            missing_deps = []
            code_content = generated_response.code  # Get code content for analysis
            for lib in common_imports:
                if lib in code_content and (not generated_response.dependencies or lib not in str(generated_response.dependencies)):
                    missing_deps.append(lib)
            
            if missing_deps:
                check_results.append(f"⚠ Warning: Code uses libraries but dependencies not declared: {', '.join(missing_deps)}")
                warnings += 1
    except Exception as e:
        check_results.append(f"✗ CRITICAL: Failed to validate syntax - {e}")
        critical_issues += 1
    
    # 2. Code Quality Checks
    code_content = generated_response.code
    
    # Check for type hints
    if 'def ' in code_content and '->' not in code_content:
        check_results.append("⚠ Warning: Function missing return type hint")
        warnings += 1
    elif '->' in code_content:
        check_results.append("✓ Return type hints present")
    
    # Check for docstring
    if '"""' in code_content or "'''" in code_content:
        check_results.append("✓ Docstring present")
    else:
        check_results.append("⚠ Warning: Missing docstring")
        warnings += 1
    
    # Check for error handling
    if 'try:' in code_content and 'except' in code_content:
        check_results.append("✓ Error handling implemented")
    elif 'raise' in code_content:
        check_results.append("✓ Explicit error raising found")
    else:
        check_results.append("⚠ Warning: No error handling detected")
        warnings += 1
    
    # 3. Enhanced Security Checks
    security_risks = {
        'eval(': "eval() function detected - major security vulnerability",
        'exec(': "exec() function detected - major security vulnerability", 
        'os.system(': "os.system() detected - use subprocess instead",
        'subprocess.call(': "subprocess.call() without shell=False - potential security risk",
        '__import__': "__import__ detected - use proper import statements",
        'pickle.load': "pickle.load detected - potential code execution vulnerability",
        'input(': "input() without validation detected - potential security risk"
    }
    
    security_found = False
    for risk, message in security_risks.items():
        if risk in code_content:
            check_results.append(f"✗ CRITICAL: {message}")
            critical_issues += 1
            security_found = True
    
    if not security_found:
        check_results.append("✓ No major security risks detected")
    
    # 4. Enhanced Performance and Best Practices Checks
    performance_checks = {
        'global ': "Global variables detected - consider encapsulation",
        'while True:': "Infinite loop detected - ensure proper exit conditions", 
        'import *': "Wildcard imports detected - use specific imports",
        'time.sleep(': "time.sleep() in main logic - consider async alternatives",
        'requests.get(': "requests.get() without timeout - add timeout parameter",
        'open(': "File operations without context manager - use 'with open()'"
    }
    
    # Additional critical checks for web scraping task
    if 'scraper' in task.lower() or 'scraping' in task.lower():
        web_scraping_checks = {
            'requests.get(': "HTTP requests detected - ensure proper error handling and timeouts",
            'BeautifulSoup': "Web scraping detected - ensure robots.txt compliance",
            'selenium': "Browser automation detected - ensure proper resource cleanup",
            'threading': "Threading detected - ensure thread safety and proper synchronization"
        }
        performance_checks.update(web_scraping_checks)
    
    for pattern, message in performance_checks.items():
        if pattern in code_content:
            check_results.append(f"⚠ Warning: {message}")
            warnings += 1
    
    # 5. Test Code Validation
    test_content = generated_response.test_code
    if test_content:
        try:
            ast.parse(test_content)
            check_results.append("✓ Test code syntax is valid")
            
            # Check for proper test structure
            if 'def test_' in test_content:
                check_results.append("✓ Test functions follow naming convention")
            else:
                check_results.append("⚠ Warning: Test functions should start with 'test_'")
                warnings += 1
                
            if 'assert' in test_content:
                check_results.append("✓ Test assertions present")
            else:
                check_results.append("⚠ Warning: No test assertions found")
                warnings += 1
        except SyntaxError:
            check_results.append("✗ CRITICAL: Test code has syntax errors")
            critical_issues += 1
    else:
        check_results.append("✗ CRITICAL: No test code provided")
        critical_issues += 1
    
    # 6. Documentation Quality
    if len(generated_response.explanation) < 50:
        check_results.append("⚠ Warning: Explanation is too brief")
        warnings += 1
    else:
        check_results.append("✓ Detailed explanation provided")
    
    if not generated_response.usage_examples:
        check_results.append("⚠ Warning: No usage examples provided")
        warnings += 1
    elif len(generated_response.usage_examples) < 2:
        check_results.append("⚠ Warning: Should provide multiple usage examples")
        warnings += 1
    else:
        check_results.append("✓ Multiple usage examples provided")
    
    # 7. Function Name Validation
    function_name = generated_response.function_name
    if not function_name.islower() or not function_name.replace('_', '').isalnum():
        check_results.append("⚠ Warning: Function name should follow snake_case convention")
        warnings += 1
    else:
        check_results.append("✓ Function name follows Python conventions")
    
    # 7.5. Python Code Execution Testing (configurable)
    if ENABLE_CODE_EXECUTION and critical_issues == 0:  # Only execute if no critical syntax errors
        logger.info("Performing Python code execution testing...")
        
        try:
            import subprocess
            import tempfile
            import os
            import sys
            
            # Create a temporary file with the generated code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                # Prepare the code for execution
                execution_code = generated_response.code
                
                # Add basic import handling if dependencies are specified
                if generated_response.dependencies:
                    import_statements = []
                    for dep in generated_response.dependencies:
                        if dep.startswith('import ') or dep.startswith('from '):
                            import_statements.append(dep)
                    
                    if import_statements:
                        execution_code = '\n'.join(import_statements) + '\n\n' + execution_code
                
                # Add a simple test execution at the end to verify the function can be called
                function_name = generated_response.function_name
                execution_code += f"""

# Simple execution test
if __name__ == "__main__":
    try:
        # Test if function is defined and callable
        if '{function_name}' in globals() and callable(globals()['{function_name}']):
            print("✓ Function '{function_name}' is defined and callable")
        else:
            print("✗ Function '{function_name}' is not properly defined")
    except Exception as e:
        print(f"✗ Error during execution test: {{e}}")
"""
                
                temp_file.write(execution_code)
                temp_file_path = temp_file.name
            
            # Execute the code in a subprocess with timeout
            try:
                result = subprocess.run(
                    [sys.executable, temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=10,  # 10 second timeout
                    cwd=os.path.dirname(temp_file_path)
                )
                
                # Check execution results
                if result.returncode == 0:
                    check_results.append("✓ Code execution completed successfully")
                    
                    # Check for any error messages in stdout
                    if "✗" in result.stdout:
                        check_results.append("⚠ Warning: Execution test found issues:")
                        for line in result.stdout.split('\n'):
                            if line.strip() and "✗" in line:
                                check_results.append(f"  {line.strip()}")
                                warnings += 1
                    elif "✓" in result.stdout:
                        check_results.append("✓ Function definition and callability verified")
                    
                    # Check for any warnings or issues in stdout
                    if result.stdout.strip():
                        execution_output = result.stdout.strip()
                        if execution_output and not execution_output.startswith("✓"):
                            check_results.append(f"📋 Execution output: {execution_output}")
                
                else:
                    check_results.append(f"✗ CRITICAL: Code execution failed with return code {result.returncode}")
                    critical_issues += 1
                    
                    if result.stderr:
                        error_lines = result.stderr.strip().split('\n')
                        # Show only the most relevant error lines
                        relevant_errors = [line for line in error_lines if line.strip() and not line.startswith('  File')]
                        if relevant_errors:
                            check_results.append(f"✗ CRITICAL: Execution error - {relevant_errors[-1]}")
                    
            except subprocess.TimeoutExpired:
                check_results.append("✗ CRITICAL: Code execution timed out (>10 seconds)")
                critical_issues += 1
            except Exception as subprocess_error:
                check_results.append(f"✗ CRITICAL: Failed to execute code - {subprocess_error}")
                critical_issues += 1
            
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass  # Ignore cleanup errors
                
        except Exception as e:
            check_results.append(f"⚠ Warning: Code execution testing failed - {e}")
            warnings += 1
            
    elif ENABLE_CODE_EXECUTION and critical_issues > 0:
        check_results.append("⚠ Skipping code execution due to critical syntax errors")
    elif not ENABLE_CODE_EXECUTION:
        check_results.append("ℹ️ Code execution testing disabled by configuration")

    # 8. Function Name Validation
    function_name = generated_response.function_name
    if not function_name.islower() or not function_name.replace('_', '').isalnum():
        check_results.append("⚠ Warning: Function name should follow snake_case convention")
        warnings += 1
    else:
        check_results.append("✓ Function name follows Python conventions")
    
    # 9. AI-Powered Code Analysis (only if no critical syntax errors and AI analysis is enabled)
    ai_detailed_analysis = ""
    
    if critical_issues == 0 and ENABLE_AI_ANALYSIS:  # Only run AI analysis if no critical syntax/security issues and enabled
        logger.info("Performing AI-powered code analysis...")
        
        ai_analysis_prompt = f"""
        You are a senior software engineer and code reviewer with expertise in Python best practices, 
        security, performance, and production-ready code standards. 
        
        Please analyze the following Python function and its test code for production readiness:
        
        FUNCTION CODE:
        {generated_response.code}
        
        TEST CODE:
        {generated_response.test_code}
        
        FUNCTION EXPLANATION:
        {generated_response.explanation}
        
        DEPENDENCIES:
        {generated_response.dependencies or 'None specified'}
        
        CURRENT QUALITY STATUS:
        - Critical Issues Found: {critical_issues}
        - Warnings Found: {warnings}
        
        Provide a comprehensive analysis focusing on:
        1. Code quality and adherence to Python best practices
        2. Security vulnerabilities and potential risks  
        3. Performance considerations and optimization opportunities
        4. Test coverage and quality assessment
        5. Maintainability and readability evaluation
        6. Production readiness assessment
        
        IMPORTANT: Focus on providing specific, actionable improvement suggestions that can be directly 
        implemented in a retry attempt. Be concrete about what changes are needed.
        """
        
        try:
            # Track AI analysis API call timing and tokens
            ai_api_start_time = time.time()
            
            ai_analysis = instructor_client.chat.completions.create(
                system="You are an expert Python code reviewer specializing in production-ready code assessment. Provide thorough, actionable feedback.",
                messages=[{"role": "user", "content": ai_analysis_prompt}],
                response_model=CodeAnalysisResponse,
            )
            
            ai_api_end_time = time.time()
            ai_api_duration = ai_api_end_time - ai_api_start_time
            
            # Track token usage for AI analysis
            ai_prompt_tokens = len(ai_analysis_prompt) // 4  # Rough estimation
            ai_completion_tokens = len(str(ai_analysis)) // 4  # Rough estimation
            ai_total_tokens = ai_prompt_tokens + ai_completion_tokens
            
            # Update tracking data
            api_call_count += 1
            total_tokens_used += ai_total_tokens
            analysis_tokens += ai_total_tokens
            analysis_times.append(ai_api_duration)
            
            logger.info(f"AI Analysis Call {api_call_count}: {ai_api_duration:.2f}s, ~{ai_total_tokens} tokens")
            
            # Incorporate AI analysis into quality assessment
            ai_quality_score = ai_analysis.overall_quality_score
            ai_maintainability = ai_analysis.maintainability_score
            # ai_production_ready = ai_analysis.production_readiness
            
            check_results.append(f"🤖 AI Overall Quality Score: {ai_quality_score}/10")
            check_results.append(f"🤖 AI Maintainability Score: {ai_maintainability}/10")
            # check_results.append(f"🤖 AI Production Ready: {'✓' if ai_production_ready else '✗'}")
            
            # Add AI-identified issues
            if ai_analysis.code_smells:
                check_results.append("🤖 AI-Identified Code Smells:")
                for smell in ai_analysis.code_smells:
                    check_results.append(f"⚠ Warning: AI Code Smell - {smell}")
                    warnings += 1
            
            # Add AI positive feedback
            if ai_analysis.positive_aspects:
                check_results.append("🤖 AI-Identified Strengths:")
                for aspect in ai_analysis.positive_aspects:
                    check_results.append(f"  ✓ {aspect}")
            
            # # AI-based critical assessment
            # if not ai_production_ready or ai_quality_score < 6:
            #     critical_issues += 1
            #     check_results.append("✗ CRITICAL: AI assessment indicates code not ready for production")
            
            # Store detailed AI analysis for later display and retry feedback
            ai_detailed_analysis = f"""
🤖 === AI-POWERED CODE ANALYSIS REPORT ===

Overall Quality Score: {ai_quality_score}/10
Maintainability Score: {ai_maintainability}/10

Security Assessment:
{ai_analysis.security_assessment}

Performance Analysis:
{ai_analysis.performance_analysis}

Test Coverage Assessment:
{ai_analysis.test_coverage_assessment}

Code Smells Identified:
{chr(10).join(f'• {smell}' for smell in ai_analysis.code_smells) if ai_analysis.code_smells else '• None identified'}

Positive Aspects:
{chr(10).join(f'• {aspect}' for aspect in ai_analysis.positive_aspects) if ai_analysis.positive_aspects else '• None identified'}

Improvement Suggestions:
{chr(10).join(f'• {suggestion}' for suggestion in ai_analysis.improvement_suggestions) if ai_analysis.improvement_suggestions else '• None provided'}

Detailed Expert Feedback:
{ai_analysis.detailed_feedback}

🎯 RETRY GUIDANCE: The above improvement suggestions should be directly addressed in any retry attempt.
"""
            
        except Exception as e:
            check_results.append(f"⚠ Warning: AI analysis failed - {e}")
            warnings += 1
            ai_detailed_analysis = "AI analysis was not available due to an error." + f" Error details: {str(e)}"
    else:
        # Skip AI analysis due to critical issues or configuration
        if critical_issues > 0:
            check_results.append("⚠ Skipping AI analysis due to critical syntax/security errors")
            ai_detailed_analysis = "AI analysis was skipped due to critical syntax or security errors that prevent code analysis."
        else:
            check_results.append("ℹ️ AI analysis disabled by configuration setting")
            ai_detailed_analysis = "AI analysis was disabled by configuration setting. To enable detailed AI code analysis, set ENABLE_AI_ANALYSIS=True in the configuration constants."
    
    # Final Assessment with structured feedback
    total_issues = critical_issues + warnings
    
    # Create structured feedback for better retry processing
    check_summary = f"""
=== CODE QUALITY ASSESSMENT REPORT ===
Critical Issues: {critical_issues}
Warnings: {warnings} 
Total Issues: {total_issues}

=== DETAILED FINDINGS ===
"""
    
    # Categorize results for better feedback parsing
    critical_findings = [result for result in check_results if '✗ CRITICAL:' in result]
    warning_findings = [result for result in check_results if '⚠ Warning:' in result or '⚠️ Warning:' in result]
    success_findings = [result for result in check_results if '✓' in result]
    ai_findings = [result for result in check_results if '🤖' in result and 'Warning:' not in result]  # Exclude AI warnings from AI section
    
    if critical_findings:
        check_summary += "\n🚨 CRITICAL ISSUES BLOCKING PRODUCTION:\n"
        for finding in critical_findings:
            check_summary += f"{finding}\n"
    
    if warning_findings:
        check_summary += "\n⚠️ QUALITY WARNINGS:\n"
        for finding in warning_findings:
            check_summary += f"{finding}\n"
        
        # Debug info to track warning discrepancy
        check_summary += f"\n📊 WARNING ANALYSIS: Found {len(warning_findings)} warning items in detailed findings vs {warnings} total warnings counted\n"
    
    if ai_findings:
        check_summary += "\n🤖 AI ASSESSMENT:\n"
        for finding in ai_findings:
            check_summary += f"{finding}\n"
    
    if success_findings:
        check_summary += "\n✅ QUALITY CHECKS PASSED:\n"
        for finding in success_findings:
            check_summary += f"{finding}\n"
    
    # Determine if code is good enough for production
    # STRICT RULE: ANY critical issues = automatic rejection
    # Additional rule: Too many warnings (> WARNING_THRESHOLD) = rejection for production use
    not_good_enough = critical_issues > 0 or warnings > WARNING_THRESHOLD
    
    # Enhanced logging and display with dramatic visual feedback
    if critical_issues > 0:
        rejection_reason = f"CRITICAL ISSUES DETECTED ({critical_issues} critical issues)"
        logger.error(f"❌ Code REJECTED for production: {rejection_reason}")
        
        print(f"\n🚨" + "=" * 70 + "🚨")
        print("💥 🚫 ❌ PRODUCTION READINESS: HARD REJECTION ❌ 🚫 💥")
        print(f"🚨" + "=" * 70 + "🚨")
        print(f"🔥 CRITICAL FAILURE: {rejection_reason}")
        print(f"⛔ SEVERITY: Code cannot proceed to production")
        print(f"🛠️  REQUIRED ACTION: Fix critical issues immediately")
        print(f"🔄 RETRY STATUS: Will attempt regeneration with feedback")
        print(f"🚨" + "=" * 70 + "🚨")
        
    elif warnings > WARNING_THRESHOLD:
        rejection_reason = f"TOO MANY WARNINGS ({warnings} warnings exceed threshold of {WARNING_THRESHOLD})"
        logger.warning(f"⚠️ Code REJECTED for production: {rejection_reason}")
        
        print(f"\n⚠️" + "=" * 68 + "⚠️")
        print("📋 🛑 ⚠️  PRODUCTION READINESS: QUALITY REJECTION ⚠️  🛑 📋")
        print(f"⚠️" + "=" * 68 + "⚠️")
        print(f"📊 QUALITY ISSUE: {rejection_reason}")
        print(f"📈 STANDARD: Code quality below production threshold")
        print(f"🔧 REQUIRED ACTION: Address warnings for production deployment")
        print(f"🔄 RETRY STATUS: Will regenerate with quality improvements")
        print(f"⚠️" + "=" * 68 + "⚠️")
        
    else:
        logger.info(f"✅ Code APPROVED for production with {warnings} warnings")
        
        print(f"\n🎉" + "=" * 64 + "🎉")
        print("🚀 ✅ 🌟 PRODUCTION READINESS: APPROVED! 🌟 ✅ 🚀")
        print(f"🎉" + "=" * 64 + "🎉")
        print(f"💚 Quality Score: {warnings} warnings (within tolerance of {WARNING_THRESHOLD})")
        print(f"🎯 Status: Ready for production deployment!")
        print(f"🏆 Achievement: Passed all quality gates!")
        print(f"🎉" + "=" * 64 + "🎉")
    
    logger.info(f"Code Checker Results:\n{check_summary}")
    
    return state.update(
        not_good_enough=not_good_enough,
        check_results=check_summary,
        ai_analysis=ai_detailed_analysis,
        total_tokens_used=total_tokens_used,
        analysis_tokens=analysis_tokens,
        api_call_count=api_call_count,
        analysis_times=analysis_times,
    )
  
@action(reads=["generated_python_response", "check_results", "ai_analysis", "task", "retries", "not_good_enough", "workflow_start_time", "total_tokens_used", "generation_tokens", "analysis_tokens", "api_call_count", "generation_times", "analysis_times"], writes=["workflow_end_time"])
def end(state: State) -> State:
    """Final action that displays the results and generates a comprehensive markdown report."""
    logger.info("=== WORKFLOW COMPLETED ===")
    
    # Record workflow end time
    workflow_end_time = time.time()
    
    generated_response = state.get("generated_python_response")
    check_results = state.get("check_results", "")
    ai_analysis = state.get("ai_analysis", "")
    task = state.get("task", "")
    retries = state.get("retries", 0)
    not_good_enough = state.get("not_good_enough", False)
    
    # Get timing and token data
    workflow_start_time = state.get("workflow_start_time", workflow_end_time)
    total_tokens_used = state.get("total_tokens_used", 0)
    generation_tokens = state.get("generation_tokens", 0)
    analysis_tokens = state.get("analysis_tokens", 0)
    api_call_count = state.get("api_call_count", 0)
    generation_times = state.get("generation_times", [])
    analysis_times = state.get("analysis_times", [])
    
    # Calculate timing metrics
    total_duration = workflow_end_time - workflow_start_time
    avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0
    avg_analysis_time = sum(analysis_times) / len(analysis_times) if analysis_times else 0
    
    # Grand finale visual output
    print(f"\n🏁" + "=" * 76 + "🏁")
    print("🎊 🏆 ⭐ AI PYTHON CODING WORKFLOW COMPLETED! ⭐ 🏆 🎊")
    print(f"🏁" + "=" * 76 + "🏁")
    
    # Display performance metrics
    print(f"\n📊 === WORKFLOW PERFORMANCE METRICS ===")
    print(f"⏱️ Total Duration: {total_duration:.2f}s")
    print(f"🔢 Total API Calls: {api_call_count}")
    print(f"🎯 Total Tokens Used: ~{total_tokens_used:,}")
    print(f"📝 Generation Tokens: ~{generation_tokens:,}")
    print(f"🤖 Analysis Tokens: ~{analysis_tokens:,}")
    if generation_times:
        print(f"⚡ Avg Generation Time: {avg_generation_time:.2f}s")
    if analysis_times:
        print(f"🧠 Avg Analysis Time: {avg_analysis_time:.2f}s")
    
    # Generate comprehensive markdown report
    report_content = _generate_comprehensive_report(
        generated_response, check_results, ai_analysis, task, retries, not_good_enough,
        total_duration, api_call_count, total_tokens_used, generation_tokens, analysis_tokens,
        generation_times, analysis_times
    )
    
    # Save report to file
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"ai_coding_workflow_report_{timestamp}.md"
    report_path = f"/Users/josereyes/Dev/ai-python-coding-agent/01_ai_workflow/{report_filename}"
    
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"📋 Comprehensive report saved: {report_filename}")
        logger.info(f"Report generated successfully: {report_path}")
    except Exception as e:
        print(f"⚠️ Failed to save report: {e}")
        logger.error(f"Failed to save report: {e}")
    
    if generated_response:
        print(f"\n🎯 === FINAL GENERATED ARTIFACTS ===")
        print(f"📝 Function Name: {generated_response.function_name}")
        print(f"🎪 Status: Workflow completed with generated code")
        
        print(f"\n💡 === EXPLANATION ===")
        print(f"{generated_response.explanation}")
        
        print(f"\n💻 === PRODUCTION CODE ===")
        print("```python")
        print(f"{generated_response.code}")
        print("```")
        
        if generated_response.dependencies:
            print(f"\n📦 === DEPENDENCIES ===")
            for dep in generated_response.dependencies:
                print(f"  📌 {dep}")
        
        print(f"\n🧪 === TEST SUITE ===")
        print("```python")
        print(f"{generated_response.test_code}")
        print("```")
        
        print(f"\n💡 === USAGE EXAMPLES ===")
        for i, example in enumerate(generated_response.usage_examples, 1):
            print(f"  🔸 Example {i}: {example}")
    else:
        print(f"\n❌ === WORKFLOW FAILED ===")
        print(f"🚨 No final code artifacts were generated")
        print(f"💔 Maximum retry attempts exceeded")
    
    if check_results:
        print(f"\n🔍 === QUALITY ASSESSMENT SUMMARY ===")
        print(f"{check_results}")
    
    if ai_analysis:
        print(f"\n{ai_analysis}")
    
    print(f"\n🏁" + "=" * 76 + "🏁")
    print("🎉 Thank you for using the AI Python Coding Agent! 🎉")
    print(f"🏁" + "=" * 76 + "🏁")
    
    return state.update(workflow_end_time=workflow_end_time)


def _generate_comprehensive_report(generated_response, check_results, ai_analysis, task, retries, not_good_enough, 
                                 total_duration, api_call_count, total_tokens_used, generation_tokens, analysis_tokens,
                                 generation_times, analysis_times):
    """Generate a comprehensive markdown report of the entire workflow."""
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine workflow outcome
    if generated_response and not not_good_enough:
        outcome_status = "✅ SUCCESS"
        outcome_color = "🟢"
        outcome_description = "Code generation completed successfully and passed all quality gates"
    elif generated_response and not_good_enough:
        outcome_status = "⚠️ PARTIAL SUCCESS"
        outcome_color = "🟡"
        outcome_description = "Code generation completed but failed final quality assessment"
    else:
        outcome_status = "❌ FAILURE"
        outcome_color = "🔴"
        outcome_description = "Code generation failed or maximum retry limit exceeded"
    
    # Parse quality metrics from check_results
    critical_issues = check_results.count('✗ CRITICAL:') if check_results else 0
    warnings = check_results.count('⚠ Warning:') + check_results.count('⚠️ Warning:') if check_results else 0
    passed_checks = check_results.count('✓') if check_results else 0
    
    # Extract AI metrics if available
    ai_quality_score = "N/A"
    ai_maintainability_score = "N/A"
    if ai_analysis and "Overall Quality Score:" in ai_analysis:
        try:
            quality_line = [line for line in ai_analysis.split('\n') if 'Overall Quality Score:' in line][0]
            ai_quality_score = quality_line.split(':')[1].strip().split('/')[0]
        except:
            pass
    
    if ai_analysis and "Maintainability Score:" in ai_analysis:
        try:
            maintainability_line = [line for line in ai_analysis.split('\n') if 'Maintainability Score:' in line][0]
            ai_maintainability_score = maintainability_line.split(':')[1].strip().split('/')[0]
        except:
            pass
    
    report = f"""# AI Python Coding Agent - Comprehensive Workflow Report

---

## 📊 Executive Summary

**Generated on:** {timestamp}  
**Workflow Status:** {outcome_color} {outcome_status}  
**Description:** {outcome_description}  
**Total Attempts:** {retries + 1} / {MAX_RETRIES}  
**Quality Threshold:** ≤ {WARNING_THRESHOLD} warnings  

---

## 🎯 Task Overview

**Original Request:**
```
{task}
```

---

## ⚡ Performance Metrics

### Timing Analysis
- **Total Workflow Duration:** {total_duration:.2f} seconds
- **API Calls Made:** {api_call_count} calls
- **Average Generation Time:** {sum(generation_times) / len(generation_times) if generation_times else 0:.2f}s per call
- **Average Analysis Time:** {sum(analysis_times) / len(analysis_times) if analysis_times else 0:.2f}s per call
- **Total Generation Time:** {sum(generation_times):.2f}s ({len(generation_times)} calls)
- **Total Analysis Time:** {sum(analysis_times):.2f}s ({len(analysis_times)} calls)

### Token Usage Analysis
- **Total Tokens Consumed:** ~{total_tokens_used:,} tokens
- **Code Generation Tokens:** ~{generation_tokens:,} tokens ({generation_tokens/total_tokens_used*100 if total_tokens_used > 0 else 0:.1f}%)
- **Quality Analysis Tokens:** ~{analysis_tokens:,} tokens ({analysis_tokens/total_tokens_used*100 if total_tokens_used > 0 else 0:.1f}%)
- **Average Tokens per API Call:** ~{total_tokens_used/api_call_count if api_call_count > 0 else 0:,.0f} tokens
- **Estimated Cost:** ~${total_tokens_used * 0.00001:.4f} USD (approximate)

### Efficiency Metrics
- **Tokens per Second:** ~{total_tokens_used/total_duration if total_duration > 0 else 0:,.0f} tokens/sec
- **API Calls per Minute:** {api_call_count/(total_duration/60) if total_duration > 0 else 0:.1f} calls/min
- **Retry Efficiency:** {((retries + 1 - retries) / (retries + 1)) * 100:.1f}% success rate
- **Quality Gate Performance:** {'PASSED' if not not_good_enough else 'FAILED'} on attempt #{retries + 1}

---

## 📈 Quality Metrics Summary

| Metric | Count | Status |
|--------|--------|--------|
| **Critical Issues** | {critical_issues} | {'🔴 BLOCKING' if critical_issues > 0 else '🟢 CLEAR'} |
| **Quality Warnings** | {warnings} | {'🔴 EXCEEDS LIMIT' if warnings > WARNING_THRESHOLD else '🟡 WITHIN LIMITS' if warnings > 0 else '🟢 CLEAN'} |
| **Passed Checks** | {passed_checks} | {'🟢 GOOD' if passed_checks > 5 else '🟡 ACCEPTABLE' if passed_checks > 0 else '🔴 POOR'} |
| **AI Quality Score** | {ai_quality_score}/10 | {'🟢 EXCELLENT' if ai_quality_score != 'N/A' and int(ai_quality_score) >= 8 else '🟡 GOOD' if ai_quality_score != 'N/A' and int(ai_quality_score) >= 6 else '🔴 NEEDS IMPROVEMENT' if ai_quality_score != 'N/A' else 'N/A'} |
| **AI Maintainability** | {ai_maintainability_score}/10 | {'🟢 EXCELLENT' if ai_maintainability_score != 'N/A' and int(ai_maintainability_score) >= 8 else '🟡 GOOD' if ai_maintainability_score != 'N/A' and int(ai_maintainability_score) >= 6 else '🔴 NEEDS IMPROVEMENT' if ai_maintainability_score != 'N/A' else 'N/A'} |

---

## 🔄 Workflow Journey

### Attempt History
"""

    # Add attempt history
    if retries == 0:
        report += """
**Attempt 1:** ✅ **FIRST TRY SUCCESS** - Code generated and passed all quality gates on the first attempt
"""
    else:
        for attempt in range(retries + 1):
            if attempt == 0:
                report += f"""
**Attempt {attempt + 1}:** 🔴 **INITIAL FAILURE** - Code generated but failed quality assessment
"""
            elif attempt < retries:
                report += f"""
**Attempt {attempt + 1}:** 🔄 **RETRY #{attempt}** - Applied feedback and regenerated code, still failed
"""
            else:
                if not_good_enough:
                    report += f"""
**Attempt {attempt + 1}:** ⚠️ **FINAL ATTEMPT** - Applied comprehensive feedback, partial success
"""
                else:
                    report += f"""
**Attempt {attempt + 1}:** ✅ **SUCCESS** - Applied comprehensive feedback and passed all quality gates
"""

    # Add generated artifacts section
    if generated_response:
        report += f"""

---

## 🎯 Generated Artifacts

### Function Overview
- **Function Name:** `{generated_response.function_name}`
- **Generated Dependencies:** {len(generated_response.dependencies or [])} packages
- **Usage Examples:** {len(generated_response.usage_examples or [])} provided
- **Test Coverage:** Comprehensive unit tests included

### Function Explanation
{generated_response.explanation}

### Production Code
```python
{generated_response.code}
```

### Dependencies
"""
        if generated_response.dependencies:
            for dep in generated_response.dependencies:
                report += f"- `{dep}`\n"
        else:
            report += "- No external dependencies required\n"

        report += f"""
### Test Suite
```python
{generated_response.test_code}
```

### Usage Examples
"""
        for i, example in enumerate(generated_response.usage_examples or [], 1):
            report += f"{i}. `{example}`\n"

    else:
        report += """

---

## ❌ Generation Failure

**Status:** Code generation failed or was incomplete  
**Reason:** Maximum retry attempts exceeded without producing acceptable code  
**Recommendation:** Review task complexity and consider simplifying requirements  

"""

    # Add detailed quality assessment
    report += f"""

---

## 🔍 Detailed Quality Assessment

### Quality Check Results
"""
    
    if check_results:
        # Format the check results for markdown
        formatted_results = check_results.replace("=== CODE QUALITY ASSESSMENT REPORT ===", "")
        formatted_results = formatted_results.replace("=== DETAILED FINDINGS ===", "")
        
        # Convert to markdown format
        lines = formatted_results.split('\n')
        in_section = False
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('🚨 CRITICAL ISSUES'):
                report += "\n#### 🚨 Critical Issues Found\n"
                in_section = True
            elif line.startswith('⚠️ QUALITY WARNINGS'):
                report += "\n#### ⚠️ Quality Warnings\n"
                in_section = True
            elif line.startswith('🤖 AI ASSESSMENT'):
                report += "\n#### 🤖 AI Assessment\n"
                in_section = True
            elif line.startswith('✅ QUALITY CHECKS PASSED'):
                report += "\n#### ✅ Passed Quality Checks\n"
                in_section = True
            elif line.startswith('📊 WARNING ANALYSIS'):
                report += f"\n**Debug Info:** {line}\n"
            elif in_section and (line.startswith('✗') or line.startswith('⚠') or line.startswith('✓') or line.startswith('🤖')):
                report += f"- {line}\n"
            elif line.startswith('Critical Issues:') or line.startswith('Warnings:') or line.startswith('Total Issues:'):
                report += f"**{line}**\n"
    else:
        report += "No quality assessment data available.\n"

    # Add AI analysis section
    if ai_analysis and ai_analysis.strip() and "AI analysis was" not in ai_analysis:
        report += f"""

---

## 🤖 AI Expert Analysis

{ai_analysis}
"""

    # Add recommendations section
    report += f"""

---

## 💡 Recommendations & Next Steps

### Immediate Actions
"""

    if critical_issues > 0:
        report += f"""
1. **🚨 CRITICAL:** Address all {critical_issues} critical issues before deploying to production
2. **🔒 SECURITY:** Review security vulnerabilities and implement proper safeguards
3. **🧪 TESTING:** Ensure comprehensive test coverage for all critical paths
"""

    if warnings > WARNING_THRESHOLD:
        report += f"""
1. **⚠️ QUALITY:** Reduce {warnings} warnings to below {WARNING_THRESHOLD} threshold
2. **📚 STANDARDS:** Apply Python best practices and PEP 8 guidelines
3. **🔧 REFACTOR:** Consider code refactoring for better maintainability
"""

    if retries > 0:
        report += f"""
1. **📝 PROCESS:** Review task complexity - required {retries + 1} attempts
2. **🎯 CLARITY:** Consider providing more specific requirements
3. **🔄 FEEDBACK:** The retry mechanism successfully improved code quality
"""

    if generated_response and not not_good_enough:
        report += f"""
1. **✅ DEPLOYMENT:** Code is ready for production deployment
2. **📊 MONITORING:** Implement proper logging and monitoring
3. **🔧 MAINTENANCE:** Schedule regular code reviews and updates
"""

    report += f"""

### Long-term Improvements
- **Documentation:** Ensure comprehensive API documentation
- **Performance:** Profile code in production environment
- **Scalability:** Test with larger datasets and concurrent users
- **Monitoring:** Implement health checks and error tracking
- **Maintenance:** Establish regular code review processes

---

## 📋 Workflow Configuration

- **AI Model:** Claude 3.5 Sonnet (via AWS Bedrock)
- **Framework:** Burr Workflow Engine
- **Max Retries:** {MAX_RETRIES}
- **Warning Threshold:** {WARNING_THRESHOLD}
- **Quality Gates:** Syntax, Security, Performance, Testing, Documentation
- **Feedback Loop:** Comprehensive AI-powered analysis with targeted improvements

---

## 📊 Performance Summary

### Resource Utilization
- **Total Execution Time:** {total_duration:.2f} seconds
- **Total Token Consumption:** ~{total_tokens_used:,} tokens
- **API Efficiency:** {total_tokens_used/api_call_count if api_call_count > 0 else 0:,.0f} tokens per call
- **Processing Speed:** {total_tokens_used/total_duration if total_duration > 0 else 0:,.0f} tokens/second

### Workflow Efficiency
- **Attempts Required:** {retries + 1} of {MAX_RETRIES} maximum
- **Success Rate:** {100 if not not_good_enough else 0:.0f}% final quality gate pass
- **Retry Overhead:** {retries * 100 / (retries + 1) if retries > 0 else 0:.1f}% additional processing
- **Quality Improvement:** {'Successful' if not not_good_enough else 'Partial'} through iterative feedback

### Cost Analysis
- **Estimated Cost:** ~${total_tokens_used * 0.00001:.4f} USD
- **Cost per Attempt:** ~${total_tokens_used * 0.00001 / (retries + 1):.4f} USD
- **Token Efficiency:** {(generation_tokens + analysis_tokens) / total_tokens_used * 100 if total_tokens_used > 0 else 0:.1f}% productive usage

---

## 🏁 Summary

This report documents a complete AI-powered Python code generation workflow. The system {'successfully generated production-ready code' if not not_good_enough else 'attempted code generation with' + (' partial success' if generated_response else ' failure')} using an iterative approach with comprehensive quality checking and intelligent retry mechanisms.

**Key Achievements:**
- Automated code generation with Claude 3.5 Sonnet
- Multi-layered quality assessment (syntax, security, performance)
- AI-powered code analysis and improvement suggestions
- Iterative feedback loop for continuous improvement
- Comprehensive documentation and testing

**Performance Highlights:**
- **Duration:** {total_duration:.2f}s total execution time
- **Efficiency:** ~{total_tokens_used:,} tokens consumed across {api_call_count} API calls
- **Quality:** {'✅ Passed' if not not_good_enough else '⚠️ Failed'} final quality gates
- **Attempts:** {retries + 1} of {MAX_RETRIES} maximum attempts used

**Generated:** {timestamp}  
**Report Version:** 1.0  
**Workflow Engine:** Burr v0.40.2+
"""

    return report
  
def instructor_client() -> Instructor:
    MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    anthropic_client = anthropic.AnthropicBedrock(
        aws_profile=os.getenv("AWS_PROFILE"),
        aws_region=os.getenv("AWS_REGION"),
    )

    instructor_client = instructor.from_anthropic(
      anthropic_client,
      max_tokens=8192,
      model=MODEL,
    )

    return instructor_client
  
instructor_client = instructor_client()  
  
graph = (
    GraphBuilder()
        .with_actions(
            code_generator.bind(instructor_client=instructor_client),
            code_checker.bind(instructor_client=instructor_client),
            end,
        )
        .with_transitions(
            ("code_generator", "code_checker"),
            ("code_checker", "code_generator", expr("not_good_enough == True and retries < max_retries")),
            ("code_checker", "end"),
        )
    .build()
)

def application() -> Application:
    return (
        ApplicationBuilder()
        .with_graph(graph)
        .with_state(
          not_good_enough=False,
          retries=0,
          max_retries=MAX_RETRIES,
          generated_python_response=None,
          check_results="",
          ai_analysis="",
          task="",  # Will be set when app.run() is called with inputs
          workflow_start_time=None,
          workflow_end_time=None,
          total_tokens_used=0,
          generation_tokens=0,
          analysis_tokens=0,
          api_call_count=0,
          generation_times=[],
          analysis_times=[],
        )
        .with_entrypoint("code_generator")
        .with_tracker("local", project="ai_workflow")
        .build()
    )


if __name__ == "__main__":
    import sys
    
    # Define the three sample tasks
    tasks = {
        "simple": """Create a Python function that calculates the factorial of a number using recursion.
                The function should handle edge cases like negative numbers and zero, and include comprehensive unit tests
                to validate its correctness.""",
        
        "moderate": """Create a function that analyzes a CSV file containing student grades and calculates comprehensive statistics
                including mean, median, standard deviation, letter grade distribution, and identifies students who need academic intervention
                (below 70% average). The function should handle missing data, validate input formats, and return a detailed report
                with visualizations.""",
        
        "complex": """Create a Python function that implements a multi-threaded web scraper to extract product prices
                from an e-commerce website. The scraper should handle pagination, respect robots.txt rules, and implement error handling
                for network issues. It should return a structured JSON object with product names, prices, and URLs.
                Additionally, include comprehensive unit tests to validate the scraper's functionality and performance under load.
                The function should also log its activity and handle rate limiting to avoid being blocked by the website."""
    }
    
    app = application()
    app.visualize(
        include_conditions=True,
        format="png",
        output_file_path="ai_workflow",
    )
    
    # Check command line arguments
    if len(sys.argv) > 1:
        task_type = sys.argv[1].lower()
        if task_type in tasks:
            print(f"\n🎯 Running {task_type.upper()} task...")
            app.run(
                halt_after=["end"],
                inputs={"task": tasks[task_type]}
            )
        elif task_type == "all":
            print("\n🚀 Running ALL three tasks sequentially...")
            for task_name, task_description in tasks.items():
                print(f"\n{'='*80}")
                print(f"🎯 Starting {task_name.upper()} task...")
                print(f"{'='*80}")
                
                # Create a new app instance for each task to ensure clean state
                task_app = application()
                task_app.run(
                    halt_after=["end"],
                    inputs={"task": task_description}
                )
                
                print(f"\n✅ Completed {task_name.upper()} task!")
                print(f"{'='*80}")
        else:
            print(f"❌ Unknown task type: {task_type}")
            print("Available options: simple, moderate, complex, all")
            sys.exit(1)
    else:
        # Default behavior - show options
        print("\n🤖 AI Python Coding Agent - Task Runner")
        print("="*50)
        print("Usage: python 01_ai_workflow.py <task_type>")
        print("\nAvailable task types:")
        print("  simple   - Factorial function with recursion")
        print("  moderate - CSV student grades analysis")
        print("  complex  - Multi-threaded web scraper")
        print("  all      - Run all three tasks sequentially")
        print("\nExamples:")
        print("  python 01_ai_workflow.py simple")
        print("  python 01_ai_workflow.py moderate")
        print("  python 01_ai_workflow.py complex")
        print("  python 01_ai_workflow.py all")
        print("\nRunning moderate task by default...")
        
        # Run moderate task as default
        app.run(
            halt_after=["end"],
            inputs={"task": tasks["moderate"]}
        )