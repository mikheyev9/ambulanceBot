.PHONY: start check_poetry install_poetry install_dependencies run

# Проверить установку Poetry
check_poetry:
	@command -v poetry >/dev/null 2>&1 || { echo "Poetry не установлен. Установите Poetry командой: 'curl -sSL https://install.python-poetry.org | python3 -'"; exit 1; }

# Установить Poetry, если он не установлен
install_poetry:
	@command -v poetry >/dev/null 2>&1 || { echo "Poetry не найден. Устанавливаю Poetry..."; curl -sSL https://install.python-poetry.org | python3 -; }

# Установить зависимости, если Poetry установлен
install_dependencies: check_poetry
	poetry install

# Запустить скрипт main.py
run:
	poetry run python main.py

# Команда по умолчанию для запуска всего процесса
start: install_poetry install_dependencies run
