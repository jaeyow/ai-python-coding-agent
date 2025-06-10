#!/usr/bin/env python3
"""
Enhanced Test Script for Iterative Improvement System
Tests the improved system with per-iteration metrics tracking and reporting.
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(__file__))

from ai_agent_strands import CodingAgent

async def test_enhanced_iterative_improvement():
    """Test the enhanced iterative improvement system with detailed metrics tracking."""
    
    print("🚀 Testing Enhanced Iterative Improvement System")
    print("=" * 60)
    
    # Initialize the agent
    agent = CodingAgent()
    
    # Test scenarios designed to trigger multiple iterations
    test_scenarios = [
        {
            "name": "Complex Data Processing",
            "requirement": """Create a function that processes a large dataset with multiple data validation steps, 
            statistical analysis, error handling, and generates visualizations. The function should handle missing data,
            outliers, and provide comprehensive reporting with detailed logging and type hints throughout."""
        },
        {
            "name": "Advanced Web Scraper", 
            "requirement": """Implement a sophisticated web scraper with rate limiting, authentication handling,
            session management, robots.txt compliance, and comprehensive error handling. Include detailed logging,
            type hints, proper documentation, and unit tests for all functionality."""
        },
        {
            "name": "Machine Learning Pipeline",
            "requirement": """Build a complete ML pipeline with data preprocessing, feature engineering, model training,
            hyperparameter tuning, cross-validation, and model persistence. Include comprehensive error handling,
            logging, type hints, and detailed documentation for all components."""
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test Scenario {i}: {scenario['name']}")
        print("-" * 50)
        
        try:
            # Run the workflow with iterative improvement
            result = await agent.run_workflow(scenario['requirement'])
            
            # Extract results
            success = result.get('success', False)
            iterations = result.get('iterations_used', 1)
            final_issues = result.get('final_issues_count', 0)
            code_length = len(result.get('generated_code', ''))
            execution_time = result.get('execution_time', 0)
            
            print(f"✅ Scenario completed:")
            print(f"   Success: {success}")
            print(f"   Iterations used: {iterations}")
            print(f"   Final issues count: {final_issues}")
            print(f"   Code length: {code_length} characters")
            print(f"   Execution time: {execution_time:.2f}s")
            
            results.append({
                'scenario': scenario['name'],
                'success': success,
                'iterations': iterations,
                'final_issues': final_issues,
                'code_length': code_length,
                'execution_time': execution_time
            })
            
        except Exception as e:
            print(f"❌ Scenario failed: {str(e)}")
            results.append({
                'scenario': scenario['name'],
                'success': False,
                'error': str(e),
                'iterations': 0,
                'final_issues': float('inf'),
                'code_length': 0,
                'execution_time': 0
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 ENHANCED ITERATIVE IMPROVEMENT TEST SUMMARY")
    print("=" * 60)
    
    total_scenarios = len(results)
    successful_scenarios = sum(1 for r in results if r['success'])
    total_iterations = sum(r['iterations'] for r in results)
    avg_iterations = total_iterations / total_scenarios if total_scenarios > 0 else 0
    scenarios_with_improvement = sum(1 for r in results if r['iterations'] > 1)
    
    print(f"Total scenarios tested: {total_scenarios}")
    print(f"Successful scenarios: {successful_scenarios}/{total_scenarios} ({successful_scenarios/total_scenarios*100:.1f}%)")
    print(f"Total iterations used: {total_iterations}")
    print(f"Average iterations per scenario: {avg_iterations:.1f}")
    print(f"Scenarios requiring improvement: {scenarios_with_improvement}")
    
    print("\nDetailed Results:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['scenario']}: {result['iterations']} iterations, {result['final_issues']} final issues")
    
    # Generate session report
    print(f"\n📝 Generating comprehensive session report...")
    report_path = agent.save_session_report()
    if report_path:
        print(f"✅ Session report saved to: {report_path}")
    else:
        print("❌ Failed to generate session report")
    
    print(f"\n🎯 Enhanced Iterative Improvement System Test Complete!")
    return results

if __name__ == "__main__":
    asyncio.run(test_enhanced_iterative_improvement())
