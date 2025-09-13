#!/usr/bin/zsh

# 📋 Массив папок для обработки
DIRS=("blumenhorizon_paris" "blumenhorizon_monaco" "blumenhorizon_cannes")

# 📂 Переход в корневую директорию
cd /var/www/

# 🔄 Проходим по каждой папке
for dir in "${DIRS[@]}"; do
    echo "================================"
    echo "🔍 Обработка директории: $dir"
    echo "================================"
    
    # 📁 Переход в директорию
    cd "/var/www/$dir"
    
    # 🌿 Определение ветки в зависимости от директории
    if [ "$dir" = "blumenhorizon_paris" ]; then
        BRANCH="main-paris"
    elif [ "$dir" = "blumenhorizon_cannes" ]; then
        BRANCH="main-cannes"
    elif [ "$dir" = "blumenhorizon_monaco" ]; then
        BRANCH="main-monaco"
    fi
    
    # ⚙️ Выполнение команд
    echo "🔄 Выполнение git pull origin $BRANCH"
    git pull origin $BRANCH
    
    echo "🔮 Активация виртуального окружения"
    source .venv/bin/activate
    
    echo "🔄 Выполнение миграций"
    python3 manage.py migrate
    
    echo "📝 Компиляция сообщений"
    python3 manage.py compilemessages
    
    echo "📦 Сбор статических файлов"
    python3 manage.py collectstatic --noinput

    echo "📦 Сжатие статических файлов"
    python3 manage.py compress
    
    echo "✅ Готово с $dir"
    echo ""
done

echo "🔄 Перезагрузка приложений..."
service gunicorn_monaco restart
service gunicorn_paris restart
service gunicorn_cannes restart

echo "🎉 Все операции выполнены!"