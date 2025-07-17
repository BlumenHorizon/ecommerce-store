⚠️ License & Usage

This code is proprietary and all rights are reserved © 2025 Vitalii Melnykov / BlumenHorizon (Einzelunternehmen).  
The source code is published for **reference purposes only**.  
**Commercial or public use is strictly prohibited** without written permission.  
For licensing inquiries, contact: [service@blumenhorizon.de](mailto:service@blumenhorizon.de)

*It is Public deprecated version*

# Документация по установке и инициализации

## Установка

1. **Обновление cтандартных пакетов:**
   Перед началом установки рекомендуется обновить все пакеты на вашей системе, чтобы убедиться, что у вас установлены последние версии.

   ```bash
   sudo apt update -y && sudo apt upgrade -y
   ```

2. **Установка необходимых пакетов:**

    ```bash
    sudo apt install -y htop tree wget nginx mysql-server neovim zsh python3-dev default-libmysqlclient-dev build-essential pkg-config gettext

    # Oh My Zsh (можете добавить свою конфигурацию в ~/.zshrc config. файл)
    sh -c "$(wget https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)"

    # Redis
    sudo apt-get install lsb-release curl gpg
    curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
    sudo chmod 644 /usr/share/keyrings/redis-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
    sudo apt-get update
    sudo apt-get install redis

    # Check healthness
    redis-cli -c ping

    # Poetry
    curl -sSL https://install.python-poetry.org | python3 -
    echo 'export PATH="/root/.local/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
    poetry config virtualenvs.in-project true
    ```

3. **Создание рабочей директории и инициализация в неё исходного кода проекта:**

    ```bash
    mkdir /var/www/blumenhorizon/
    cd /var/www/blumenhorizon/

    git init .
    git config --global init.defaultBranch main
    ```

    Запросите у наставника Ваш Fine-grained PAT-token, чтобы иметь возможность запуллить код проекта на Ваш VPS.
    Для следующих разрешений будет доступ чтения/записи: Commit statuses, Contents.
    Для Metadata только чтение.

    ```bash
    git remote add origin https://(вставить сюда выданный PAT TOKEN без скобочек)@github.com/Leviinson/BlumenHorizon.git
    git pull origin main
    poetry shell
    poetry install --only main
    ```

    Запросите у Вашего наставника .env файл и поместите его содержимое в `.env` в `/var/www/blumenhorizon/.env`

    ```bash
    scp .env root@0.0.0.0:/var/www/blumenhorizon/.env
    ```

    Запросите у Вашего наставника папку с ssl и его сертификатами, перенесите папку чтобы в итоге получился такой результат: `/root/ssl/`

    ```bash
    scp -r /путь/к/ssl root@0.0.0.0:/root/
    ```

    Перенесите конфиг системного менеджера для gunicorn и конфиги nginx в соответствующие стандартные директории на VPS:

    ```bash
    cp /var/www/blumenhorizon/core/systemd/gunicorn.service /etc/systemd/system/
    cp /var/www/blumenhorizon/core/nginx/nginx.conf /etc/nginx/nginx.conf
    rm -rf /etc/nginx/sites-enabled/
    cp -r /var/www/blumenhorizon/core/nginx/sites-enabled /etc/nginx/sites-enabled
    ```

    Создайте директории для log-файлов:

    ```bash
    cd /var/www/blumenhorizon
    mkdir logs logs/django logs/gunicorn logs/nginx logs/stripe logs/telegram logs/celery logs/mysql logs/redis
    ```

    Примените миграции Django:

    ```bash
    python3 manage.py migrate
    ```

    Создайте супер-пользователя:

    ```bash
    python3 manage.py createsuperuser
    ```

    Активируйте запуск nginx и gunicorn на старте:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable nginx
    sudo systemctl enable gunicorn
    sudo systemctl enable redis-server
    sudo service gunicorn start
    sudo service nginx start
    ```

    Соберите статические файлы проекта:

    ```bash
    python3 manage.py collectstatic --noinput
    ```

    Перенесите все медиафайлы проекта в `/var/www/blumenhorizon/media/`, запросив их предварительно у наставника.

    ```bash
    scp -r /путь/к/ьувшф root@0.0.0.0:/var/www/blumenhorizon/
    ```

4. **Инициализация и настройка базы данных:**

    ```mysql
    CREATE DATABASE (значение переменной MYSQL_NAME в .env);
    CREATE USER '(MYSQL_USER в .env)'@'(MYSQL_HOST в .env)' IDENTIFIED BY '(MYSQL_PASSWORD в .env)';
    GRANT ALL PRIVILEGES ON (MYSQL_NAME в .env).* TO '(MYSQL_USER в .env)'@'(MYSQL_HOST в .env)';
    ALTER DATABASE (MYSQL_NAME в .env) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    \q
    ```

    Попросите у наставника дамп базы данных, поместите его в корневую директорию таким образом:
    `/var/www/blumenhorizon/blumenhorizon_dump.sql`

    ```bash
    mysql -u root -p blumenhorizon < /var/www/blumenhorizon/blumenhorizon_dump.sql
    ```
