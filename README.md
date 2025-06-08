```bash
mkdir ai-python-coding-agent
cd ai-python-coding-agent
uv init

aws configure sso
aws sso login

uv add <library-name>
source .venv/bin/activate # Activate the virtual environment
# now, we are ready to rock and roll

cd 01_ai_workflow
uv run 001_test.py

```