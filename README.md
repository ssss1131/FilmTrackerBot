# FilmTrackerBot


FilmTrackerBot — это Telegram бот, который помогает пользователям отслеживать фильмы, которые они посмотрели или хотят посмотреть, а также получать рекомендации на основе их предпочтений. Бот использует API TMDB для получения информации о фильмах и PostgreSQL для хранения данных.

## Описание
FilmTrackerBot — это инструмент для управления списками фильмов, которые вы посмотрели или хотите посмотреть. С его помощью можно добавлять фильмы в эти списки, удалять их, а также получать рекомендации на основе уже просмотренных фильмов. Бот предоставляет подробную информацию о фильмах, включая жанры, описания и трейлеры.

## Установка
Склонируйте репозиторий:
```bash
  git clone https://github.com/ssss1131/FilmTrackerBot.git
```

Создайте файл .env и добавьте туда свои API ключи и данные для подключения к базе данных:
```bash
BOT_API=ваш_токен_бота
Db_password=ваш_пароль_от_базы_данных
TMDB_API=ваш_ключ_от_TMDB_API
Создайте базу данных и таблицы:
```

```sql
CREATE DATABASE telegram_bot;
\c telegram_bot;
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    username TEXT NOT NULL
);
CREATE TABLE movies (
    movie_id SERIAL PRIMARY KEY,
    title TEXT UNIQUE NOT NULL,
    genre TEXT
);
CREATE TABLE watchedmovies (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    movie_id INT REFERENCES movies(movie_id),
    rating INT,
    review TEXT,
    watched_date TIMESTAMP
);
CREATE TABLE wantedtowatch (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    movie_id INT REFERENCES movies(movie_id),
    reason TEXT
);
```

Запустите бота:
```bash
python bot.py
```
## Использование
После запуска бота, вы можете использовать следующие команды:

- `/start`: Начальное приветствие и главное меню с кнопками для добавления фильмов, удаления и просмотра истории.
- `Добавить в Посмотрел`: Добавление фильма в список просмотренных.
- `Добавить в Хочу посмотреть`: Добавление фильма в список желаемых к просмотру.
- `Удалить фильм из 'Хочу посмотреть'`: Удаление фильма из списка желаемых к просмотру.
- `Удалить фильм из 'Посмотрел'`: Удаление фильма из списка просмотренных.
-  `Ваши Рекомендации`: Получение рекомендаций на основе просмотренных фильмов.
- `Всемирные Рекомендации`: Получение топ-рекомендаций фильмов по версии TMDB.
- `История`: Просмотр истории фильмов, которые вы посмотрели или хотите посмотреть.

![image](https://github.com/ssss1131/Telegram_bot/assets/115891255/dd8cf158-8754-469c-8072-12e00f99d7c5)


## Структура проекта
- bot.py: Основной файл с логикой работы бота.
- .env: Файл с конфиденциальными данными (не включен в репозиторий).
