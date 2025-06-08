import logging
import os
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

MAX_RETRIES = 3

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
    
    production_readiness: bool = Field(
        description="Whether the code is ready for production deployment"
    )
    
    detailed_feedback: str = Field(
        description="Comprehensive feedback explaining the analysis and recommendations"
    )

class PythonCodeGenerationResponse(BaseModel):
    """Structured response for Python code generation that ensures high-quality, well-tested, and maintainable code."""
    
    function_name: str = Field(
        description="The name of the generated Python function"
    )
    
    code: str = Field(
        description="The complete Python function code with comprehensive docstring, type hints, and error handling"
    )
    
    explanation: str = Field(
        description="A detailed explanation of what the function does, how it works, and design decisions"
    )
    
    dependencies: Optional[List[str]] = Field(
        default=None,
        description="List of required imports or dependencies for the function"
    )
    
    test_code: str = Field(
        description="Complete unit test code using pytest that thoroughly tests the function including edge cases"
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

@action(reads=["not_good_enough", "retries", "check_results", "ai_analysis"], writes=["generated_python_response", "retries"])
def code_generator(state: State, instructor_client: Instructor, task: str) -> State:
    retries = state["retries"]
    not_good_enough = state["not_good_enough"]
    check_results = state.get("check_results", "")
    ai_analysis = state.get("ai_analysis", "")
    
    if not_good_enough:
        logger.info(f"🔄 Code Generator Step (Retry {retries}) - Regenerating code based on quality feedback")
        
        # Enhanced visual output for retries with emojis and ASCII art
        print("\n" + "🚨" + "=" * 78 + "🚨")
        print("🔥 🔄 ⚡ ⭐ RETRY MODE ACTIVATED - LEARNING FROM MISTAKES ⭐ ⚡ 🔄 🔥")
        print("🚨" + "=" * 78 + "🚨")
        print(f"🔢 ATTEMPT NUMBER: {retries + 1} of {MAX_RETRIES + 1}")
        print(f"💥 MISSION: Fix quality issues and generate superior code")
        print(f"🧠 LEARNING SOURCE: Previous quality feedback + AI analysis")
        print(f"🎯 TARGET: Production-ready, bulletproof code")
        print("🚨" + "=" * 78 + "🚨")
        print("⚠️  PREVIOUS ATTEMPT FAILED QUALITY GATES - ADAPTING STRATEGY...")
        print("🔧 Applying hard-learned lessons to generate better code...")
        print("💪 This time will be different - incorporating ALL feedback!")
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
    
    # Build user prompt - include feedback if this is a retry
    if not_good_enough and (check_results or ai_analysis):
        user_prompt = f"""Write a Python function that performs the following: {task}.

IMPORTANT: This is a retry attempt. The previous code generation failed quality checks. Please address the following issues:

QUALITY FEEDBACK FROM PREVIOUS ATTEMPT:
{check_results}

{ai_analysis if ai_analysis else ""}

Please generate improved code that specifically addresses these quality issues while maintaining all the original requirements."""
        
        print(f"🔄 Incorporating previous quality feedback into generation...")
    else:
        user_prompt = f"Write a Python function that performs the following: {task}."
    
    try:
        generated_response = instructor_client.chat.completions.create(
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            response_model=PythonCodeGenerationResponse,
        )
        
        # Display comprehensive output
        print(f"\n🎯 === GENERATED CODE ARTIFACTS ===")
        print(f"\n📝 Function Name: {generated_response.function_name}")
        
        print(f"\n💡 Explanation:")
        print(f"{generated_response.explanation}")
        
        print(f"\n💻 Generated Code:")
        print(f"```python")
        print(f"{generated_response.code}")
        print(f"```")
        
        if generated_response.dependencies:
            print(f"\n📦 Dependencies:")
            for dep in generated_response.dependencies:
                print(f"  • {dep}")
        
        print(f"\n🧪 Test Code:")
        print(f"```python")
        print(f"{generated_response.test_code}")
        print(f"```")
        
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
            retries=retries
        )
    
    return state.update(
        generated_python_response=generated_response,
        retries=retries
    )


@action(reads=["generated_python_response"], writes=["not_good_enough", "check_results", "ai_analysis"])
def code_checker(state: State, instructor_client: Instructor) -> State:
    """
    Comprehensive code quality checker that validates generated Python code for production use.
    Checks for syntax, security, performance, maintainability, and best practices.
    """
    logger.info("Code Checker Step - Analyzing generated code quality")
    
    generated_response = state["generated_python_response"]
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
        
        # Check if dependencies are valid (if provided)
        if generated_response.dependencies:
            for dep in generated_response.dependencies:
                try:
                    # Basic check if import statement is valid
                    if dep.startswith('import ') or dep.startswith('from '):
                        ast.parse(dep)
                    check_results.append(f"✓ Dependency '{dep}' is syntactically valid")
                except:
                    check_results.append(f"⚠ Warning: Dependency '{dep}' may have issues")
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
    
    # 3. Security Checks
    security_risks = ['eval(', 'exec(', 'os.system(', 'subprocess.call(', '__import__']
    for risk in security_risks:
        if risk in code_content:
            check_results.append(f"✗ CRITICAL: Security risk detected - {risk}")
            critical_issues += 1
    
    if critical_issues == 0:
        check_results.append("✓ No security risks detected")
    
    # 4. Performance and Best Practices
    performance_checks = {
        'global ': "Global variables detected - consider encapsulation",
        'while True:': "Infinite loop detected - ensure proper exit conditions",
        'import *': "Wildcard imports detected - use specific imports",
    }
    
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
    
    # 8. AI-Powered Code Analysis (only if no critical syntax errors)
    ai_detailed_analysis = ""
    
    if critical_issues == 0:  # Only run AI analysis if no critical syntax/security issues
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
        
        Provide a comprehensive analysis focusing on:
        1. Code quality and adherence to Python best practices
        2. Security vulnerabilities and potential risks
        3. Performance considerations and optimization opportunities
        4. Test coverage and quality
        5. Maintainability and readability
        6. Production readiness assessment
        """
        
        try:
            ai_analysis = instructor_client.chat.completions.create(
                system="You are an expert Python code reviewer specializing in production-ready code assessment. Provide thorough, actionable feedback.",
                messages=[{"role": "user", "content": ai_analysis_prompt}],
                response_model=CodeAnalysisResponse,
            )
            
            # Incorporate AI analysis into quality assessment
            ai_quality_score = ai_analysis.overall_quality_score
            ai_maintainability = ai_analysis.maintainability_score
            ai_production_ready = ai_analysis.production_readiness
            
            check_results.append(f"🤖 AI Overall Quality Score: {ai_quality_score}/10")
            check_results.append(f"🤖 AI Maintainability Score: {ai_maintainability}/10")
            check_results.append(f"🤖 AI Production Ready: {'✓' if ai_production_ready else '✗'}")
            
            # Add AI-identified issues
            if ai_analysis.code_smells:
                check_results.append("🤖 AI-Identified Code Smells:")
                for smell in ai_analysis.code_smells:
                    check_results.append(f"  • {smell}")
                    warnings += 1
            
            # Add AI positive feedback
            if ai_analysis.positive_aspects:
                check_results.append("🤖 AI-Identified Strengths:")
                for aspect in ai_analysis.positive_aspects:
                    check_results.append(f"  ✓ {aspect}")
            
            # AI-based critical assessment
            if not ai_production_ready or ai_quality_score < 6:
                critical_issues += 1
                check_results.append("✗ CRITICAL: AI assessment indicates code not ready for production")
            
            # Store detailed AI analysis for later display
            ai_detailed_analysis = f"""
🤖 === AI-POWERED CODE ANALYSIS ===

Security Assessment:
{ai_analysis.security_assessment}

Performance Analysis:
{ai_analysis.performance_analysis}

Test Coverage Assessment:
{ai_analysis.test_coverage_assessment}

Improvement Suggestions:
{chr(10).join(f'• {suggestion}' for suggestion in ai_analysis.improvement_suggestions)}

Detailed Feedback:
{ai_analysis.detailed_feedback}
"""
            
        except Exception as e:
            check_results.append(f"⚠ Warning: AI analysis failed - {e}")
            warnings += 1
            ai_detailed_analysis = "AI analysis was not available due to an error."
    else:
        # Skip AI analysis due to critical issues
        check_results.append("⚠ Skipping AI analysis due to critical syntax/security errors")
        ai_detailed_analysis = "AI analysis was skipped due to critical syntax or security errors that prevent code analysis."
    
    # Final Assessment
    total_issues = critical_issues + warnings
    check_summary = f"\n=== CODE QUALITY ASSESSMENT ===\n"
    check_summary += f"Critical Issues: {critical_issues}\n"
    check_summary += f"Warnings: {warnings}\n"
    check_summary += f"Total Issues: {total_issues}\n\n"
    check_summary += "\n".join(check_results)
    
    # Determine if code is good enough for production
    # STRICT RULE: ANY critical issues = automatic rejection
    # Additional rule: Too many warnings (>5) = rejection for production use
    not_good_enough = critical_issues > 0 or warnings > 5
    
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
        
    elif warnings > 5:
        rejection_reason = f"TOO MANY WARNINGS ({warnings} warnings exceed threshold of 5)"
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
        print(f"💚 Quality Score: {warnings} warnings (within tolerance)")
        print(f"🎯 Status: Ready for production deployment!")
        print(f"🏆 Achievement: Passed all quality gates!")
        print(f"🎉" + "=" * 64 + "🎉")
    
    logger.info(f"Code Checker Results:\n{check_summary}")
    
    return state.update(
        not_good_enough=not_good_enough,
        check_results=check_summary,
        ai_analysis=ai_detailed_analysis
    )
  
@action(reads=["generated_python_response", "check_results", "ai_analysis"], writes=[])
def end(state: State) -> State:
    """Final action that displays the results of the code generation workflow."""
    logger.info("=== WORKFLOW COMPLETED ===")
    
    generated_response = state.get("generated_python_response")
    check_results = state.get("check_results", "")
    ai_analysis = state.get("ai_analysis", "")
    
    # Grand finale visual output
    print(f"\n🏁" + "=" * 76 + "🏁")
    print("🎊 🏆 ⭐ AI PYTHON CODING WORKFLOW COMPLETED! ⭐ 🏆 🎊")
    print(f"🏁" + "=" * 76 + "🏁")
    
    if generated_response:
        print(f"\n🎯 === FINAL GENERATED ARTIFACTS ===")
        print(f"📝 Function Name: {generated_response.function_name}")
        print(f"🎪 Status: Workflow completed with generated code")
        
        print(f"\n💡 === EXPLANATION ===")
        print(f"{generated_response.explanation}")
        
        print(f"\n💻 === PRODUCTION CODE ===")
        print(f"```python")
        print(f"{generated_response.code}")
        print(f"```")
        
        if generated_response.dependencies:
            print(f"\n📦 === DEPENDENCIES ===")
            for dep in generated_response.dependencies:
                print(f"  📌 {dep}")
        
        print(f"\n🧪 === TEST SUITE ===")
        print(f"```python")
        print(f"{generated_response.test_code}")
        print(f"```")
        
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
    
    return state
  
def instructor_client() -> Instructor:
    MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    anthropic_client = anthropic.AnthropicBedrock(
        aws_profile=os.getenv("AWS_PROFILE"),
        aws_region=os.getenv("AWS_REGION"),
    )

    instructor_client = instructor.from_anthropic(
        anthropic_client,
        max_tokens=4096,
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
        )
        .with_entrypoint("code_generator")
        .build()
    )


if __name__ == "__main__":
  app = application()
  app.visualize(
      include_conditions=True,
      format="png",
      output_file_path="ai_workflow",
  )
  
  # simple task to test the workflow
  # app.run(
  #     halt_after=["end"],
  #     inputs={"task": """Create a Python function that calculates the factorial of a number using recursion.
  #             The function should handle edge cases like negative numbers and zero, and include comprehensive unit tests
  #             to validate its correctness."""})
  
  # moderately complex task to test the workflow
  # app.run(
  #   halt_after=["end"],
  #   inputs={"task": """Create a function that analyzes a CSV file containing student grades and calculates comprehensive statistics
  #           including mean, median, standard deviation, letter grade distribution, and identifies students who need academic intervention
  #           (below 70% average). The function should handle missing data, validate input formats, and return a detailed report
  #           with visualizations.
  #           """})
  
  # very complex task to test the workflow
  app.run(
    halt_after=["end"],
    inputs={"task": """Create a Python function that implements a multi-threaded web scraper to extract product prices
            from an e-commerce website. The scraper should handle pagination, respect robots.txt rules, and implement error handling
            for network issues. It should return a structured JSON object with product names, prices, and URLs.
            Additionally, include comprehensive unit tests to validate the scraper's functionality and performance under load.
            The function should also log its activity and handle rate limiting to avoid being blocked by the website.
            """})