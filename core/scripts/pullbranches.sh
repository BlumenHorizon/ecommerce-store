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
    
    # ⚙️ Инициализация проекта (установка зависимостей и т.д.)
    just init
    
    echo "✅ Готово с $dir"
    echo ""
done

echo "🔄 Перезагрузка приложений..."
service gunicorn_monaco restart
service gunicorn_paris restart
service gunicorn_cannes restart

echo "🎉 Все операции выполнены!"