# rhl-redtail-repository

RHL REDTAIL Repository

## Installation

```
# mysql -uroot
mysql> create database redtail;
Query OK, 1 row affected, 1 warning (0.00 sec)

mysql> create user redtail@localhost identified by 'redtail';
Query OK, 0 rows affected (0.02 sec)

mysql> grant all privileges on redtail.* to redtail@localhost;
Query OK, 0 rows affected (0.00 sec)

mysql> flush privileges;
Query OK, 0 rows affected (0.02 sec)

```

Then:
```
$ cd redtail_repository/static
$ npm install
````

```
$ source devrc
$ flask db upgrade head
$ flask run
```

## Development commands



```
$ source devrc
$ flask db revision --autogenerate -m "Whatever change"
$ flask db upgrade head
```



