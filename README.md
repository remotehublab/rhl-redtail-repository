# RHL-Redtail-Repository

REDTAIL is an open-source repository of simulations, digital twins, and teaching materials for remote laboratory learning, developed by [RHLab at the University of Washington](https://rhlab.ece.uw.edu/) with [LabsLand](https://labsland.com/).

## Software Setup
- Install MySQL: [Download Link](https://www.mysql.com/downloads/)
  - The enterprise edition is free
  - Among the five versions given you only need the commercial version

- Python 3.12: [Download Link](https://www.python.org/downloads/)
  - Some of the packages at the moment don't work with newer versions like "greenlit"

- Node: [Download Link](https://nodejs.org/en/download)


## Setup Environment
Once Python is installed you'll want to set up a virtual environment (venv) to manage your packages

```
python3.12 -m venv .venv
```
Note: You could set this up without the 3.12 attached, but this specifies that the environment will be setup with 3.12 rather than other versions you may have installed.

Activate the environment with

```
source .venv/bin/activate
```

To deactivate it you can just type `deactivate`, but keep activate whenever you want to work on the project

To install the required packages you'll want to run this command within the environment

```
pip install -r requirements.txt
```

## Setup MySQL

```
# mysql -uroot -p
mysql> create database redtail;
Query OK, 1 row affected, 1 warning (0.00 sec)

mysql> create user redtail@localhost identified by 'redtail';
Query OK, 0 rows affected (0.02 sec)

mysql> grant all privileges on redtail.* to redtail@localhost;
Query OK, 0 rows affected (0.00 sec)

mysql> flush privileges;
Query OK, 0 rows affected (0.02 sec)

```

## Running the App:
Only need to perform these steps on the first install
```
$ cd redtail_repository/static
$ npm install
```

Perform these steps to run the app locally
```
$ source devrc
$ flask db upgrade head
$ flask run
```

## Development commands

Requires pandoc:
```
sudo apt install pandoc         # Linux
brew install pandoc             # macOS
choco install pandoc            # Windows
```


```
$ source devrc
$ flask db revision --autogenerate -m "Whatever change"
$ flask db upgrade head
```

## Test system

The fast suite uses an isolated in-memory SQLite database and temporary public,
private, and upload directories. It does not read or write the development or
production database.

Install the development dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
npm ci
npx playwright install chromium firefox webkit
cd redtail_repository/static && npm ci && cd ../..
```

Run the Python unit and functional tests with the enforced coverage gates:

```bash
pytest -m "not mysql" \
  --cov=redtail_repository \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-report=json
python scripts/check_coverage.py --line 95 --branch 95
diff-cover coverage.xml --compare-branch=origin/main --fail-under=100
ruff check redtail_repository tests scripts
```

Coverage is gated independently at 95% for lines and branches. Changed Python
lines must be fully covered.

Run the real-browser functional and accessibility suite on Chromium, Firefox,
and WebKit:

```bash
npm run test:browser
```

Run the desktop and mobile visual regression suite:

```bash
npm run test:visual
```

When a deliberate UI change alters the screenshots, review the rendered result
first, then update and re-run the baselines:

```bash
npm run test:visual:update
npm run test:visual
```

The committed baselines are under `tests/browser/__screenshots__/`. Do not
update them solely to make a failing comparison pass.

MySQL tests require a disposable database that the suite is allowed to empty:

```bash
export MYSQL_TEST_DATABASE_URL='mysql+pymysql://root:password@127.0.0.1/redtail_test'
pytest -m mysql tests/integration
```

To validate the migration history from a blank MySQL schema, configure the same
database through `TEST_DATABASE_URL` and run:

```bash
FLASK_APP=autoapp FLASK_CONFIG=testing flask db upgrade head
```

GitHub Actions runs Python 3.10 compatibility, Python 3.12 coverage, MySQL 8
migrations/integration, cross-browser flows, WCAG A/AA scans, and desktop/mobile
visual regression as separate required-check candidates.

## Production response policies

Production Apache serves `/static/` and `/public/` directly instead of proxying
those paths to Flask. The REDTAIL TLS virtual host must therefore include the
tracked response-policy file:

```apache
Include /home/redtail/rhl-redtail-repository/ops/apache/redtail-response-policies.conf
```

After changing the virtual host, validate the configuration before reloading:

```bash
sudo apache2ctl configtest
sudo systemctl reload apache2
```

Verify the deployed headers on a generated asset, a regular static asset, and a
raw file under `/public/`. The raw file must include `X-Robots-Tag: noindex,
nofollow`; uploaded files remain proxied to Flask and use `private, no-store`.
