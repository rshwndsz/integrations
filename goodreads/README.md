# Goodreads - Notion

## Usage

```bash
git clone https://github.com/rshwndsz/integrations.git
cd integrations

python3 -m venv ./.venv
source ./.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

brew install tor
/usr/local/opt/tor/bin/tor

python -m goodreads.scraper --input input.csv --output output.csv
```

## Tests

```bash
cd tests
pytest
```
