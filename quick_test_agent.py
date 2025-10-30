"""Quick test to verify agent runs"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Importing agent...")
from AgentModule.langgraph_agent import run_scraping_agent

print("Running agent with minimal iterations...")
result = run_scraping_agent(
    url="https://www.flipkart.com/search?q=phone+case",
    platform_name="flipkart", 
    task_description="Test workflow",
    max_iterations=3
)

print(f"\nResult: Success={result.get('success')}, Iterations={result.get('iterations')}")
print(f"Steps: {result.get('completed_steps', [])}")


