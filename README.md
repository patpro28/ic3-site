# Emath


## Create database

```mysql
CREATE DATABASE emath DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;

GRANT ALL PRIVILEGES ON emath.* to 'tmath'@'localhost' IDENTIFIED BY 'tmath123@';
```

## Update reversion

```python
python3 manage.py createinitialrevisions

python3 manage.py deleterevisions --days=30
```