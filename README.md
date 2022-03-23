# Emath


## Create database

### MariaDB
```mysql
CREATE DATABASE emath DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;

GRANT ALL PRIVILEGES ON emath.* to 'tmath'@'localhost' IDENTIFIED BY 'emath123@';
```

### MySQL Server
```mysql
CREATE DATABASE emath DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;

CREATE USER 'tmath'@'localhost' IDENTIFIED BY 'emath123@';

GRANT ALL PRIVILEGES ON emath.* to 'tmath'@'localhost';
```

## Update reversion

```python
python3 manage.py createinitialrevisions

python3 manage.py deleterevisions --days=30
```