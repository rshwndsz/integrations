# Integrations

Connecting APIs for lulz.

## Usage

```bash
git clone https://github.com/rshwndsz/integrations.git
cd integrations

python3 -m venv ./.venv
source ./.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .

brew install tor
/usr/local/opt/tor/bin/tor
```

## Tests

```bash
cd tests
pytest
```
