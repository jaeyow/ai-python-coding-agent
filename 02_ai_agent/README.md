```bash
pyenv versions
pyenv install 3.12.8
pyenv local 3.12.8
python --version # to confirm the version
eval "$(pyenv init -)" # if the version is not 3.12.2
python -m venv .venv
source .venv/bin/activate
```