# RHL-Redtail-Repository

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



