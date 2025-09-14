fmt:
    autoflake .
    black .
    isort .

dev:
    python3 manage.py runserver 0.0.0.0:8000

inst group="main":
    poetry install --only {{group}}

mmgt:
    python3 manage.py makemigrations

mgt:
    python3 manage.py migrate

collectstatic:
    python3 manage.py collectstatic --noinput
    python3 manage.py compress

makemessages:
    python3 manage.py makemessages -a
    python3 manage.py compilemessages

makeautocompletions:
    mkdir -p ~/.zsh/completions
    just --completions zsh > ~/.zsh/completions/_just
    if ! grep -q 'fpath=(~/.zsh/completions $fpath)' ~/.zshrc; then \
        echo '\nfpath=(~/.zsh/completions $fpath)\nautoload -Uz compinit\ncompinit' >> ~/.zshrc; \
    fi
    echo "✅ Just autocompletions installed. Run 'source ~/.zshrc' to activate."
