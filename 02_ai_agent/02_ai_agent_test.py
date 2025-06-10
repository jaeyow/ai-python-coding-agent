import os
from strands import Agent
import boto3
from strands.models import BedrockModel

# Create a custom boto3 session
session = boto3.Session(
    region_name=os.getenv("AWS_REGION"),
    profile_name=os.getenv("AWS_PROFILE"),
)

# Create a Bedrock model with the custom session
bedrock_model = BedrockModel(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    boto_session=session
)

# Create an agent with default settings
agent = Agent(model=bedrock_model)

# Ask the agent a question
agent("Tell me about agentic AI")