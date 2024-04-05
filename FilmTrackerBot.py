import telebot
from telebot import types
import psycopg2
from dotenv import load_dotenv
import os
import requests

# Загружаем переменные окружения
load_dotenv("C:\Programming\Python\API\API.env")

TOKEN = os.getenv("BOT_API")
Db_password = os.getenv("Db_password")
TMDB_API = os.getenv("TMDB_API")

connection = psycopg2.connect(
    host="localhost",
    database="telegram_bot",
    user="postgres",
    password=Db_password
)

bot = telebot.TeleBot(TOKEN)
user_states = {}  # тут типа словарь с айдишками пользователей которые уже что то нажали например Добавить в посмотрел

WATCHED = "watched"  # типа индексы чтоли что он нажал
WANT_TO_WATCH = "want_to_watch"
DELETE_WATCHED = "delete_watched"
DELETE_WANT_TO_WATCH = "delete_want_to_watch"

user_id = 0  # глобальные переменные для хранение этих данных
movie_id = 0

response = requests.get(f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API}&language=ru-RU")
genres_data = response.json()
all_genres_dict = {genre['id']: genre['name'] for genre in genres_data['genres']}#создал словарь с id:name тут находится все жанры с айди и нэйм


def registration(id, name):  # регистрация нового или вход в аккаунт оба в одной функции крч
    global user_id
    with connection.cursor() as cur:
        cur.execute("SELECT user_id FROM users WHERE chat_id = %s", (id,))
        result = cur.fetchone()
        if result is not None:
            user_id = result[0]
        else:
            cur.execute("INSERT INTO users(chat_id,username) VALUES(%s,%s) RETURNING user_id", (id, name))
            user_id = cur.fetchone()[0]
            connection.commit()

def TMDB_ID(title):
    search_url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API}&language=ru-RU&query={title.capitalize()}'
    search_response = requests.get(search_url)
    search_results = search_response.json()
    if search_results['results']:
        movie_tmdb_id = search_results['results'][0]['id']
    else:
        movie_tmdb_id = None
    return movie_tmdb_id
def add_movie(title):  # добавление фильма в бд тут надо бы учесть всех ловер чтоли сделать чтобы он не написал одно и тоже дважды пс учел как капиталайз
    global movie_id
    with connection.cursor() as cur:
        cur.execute("SELECT movie_id FROM movies WHERE title = %s", (title.capitalize(),))
        result = cur.fetchone()
        if result is not None:
            movie_id = result[0]
        else:
            movie_tmdb_id = TMDB_ID(title.capitalize())
            if movie_tmdb_id:
                # Запрашиваем информацию о фильме по его ID
                movie_url = f'https://api.themoviedb.org/3/movie/{movie_tmdb_id}?api_key={TMDB_API}&language=ru-RU'
                movie_response = requests.get(movie_url)
                movie_info = movie_response.json()
                genres = ' '.join([elm['name'] for elm in movie_info.get('genres', [])])# тут мы ищем genres ключ а если его не будет то genres = [] чтоб потом ошибки не было
                cur.execute("INSERT INTO movies(title,genre) VALUES(%s,%s) RETURNING movie_id", (title.capitalize(), genres))
                movie_id = cur.fetchone()[0]
                connection.commit()
            else:
                movie_id = 0


def want_to_watch(user_id, movie_id, reason, chat_id):
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM wantedtowatch WHERE user_id=%s and movie_id = %s", (user_id, movie_id))
        result = cur.fetchone()
        if result is None:
            cur.execute("INSERT INTO wantedtowatch(user_id,movie_id,reason) VALUES(%s,%s,%s)",
                        (user_id, movie_id, reason))
            connection.commit()
            bot.send_message(chat_id, "Успешно добавлено в список желаемых к просмотру фильмов")
        else:
            bot.send_message(chat_id, "Вы уже добавили данных фильм в список желаемых к просмотру")


def watched_movies(user_id, movie_id, rate, opinion, chat_id):
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM watchedmovies WHERE user_id = %s and movie_id = %s", (user_id, movie_id))
        result = cur.fetchone()
        if result is None:
            cur.execute(
                "INSERT INTO watchedmovies(user_id,movie_id,rating,review,watched_date) VALUES(%s,%s,%s,%s,NOW())",
                (user_id, movie_id, rate, opinion))
            connection.commit()
            bot.send_message(chat_id, "Успешно добавлено в просмотренные фильмы")
        else:
            bot.send_message(chat_id, "Вы уже добавили данный фильм в список просмотренных")


def filter(chat_id, user_id, rating):
    with connection.cursor() as cur:
        cur.execute(f"SELECT * FROM watchedmovies WHERE rating>=%s and rating<=%s and user_id = %s",
                    (rating, rating + 2, user_id))
        all = cur.fetchall()
        for i in range(0, len(all)):
            movie_id = all[i][2]
            cur.execute("SELECT title FROM movies where movie_id = %s", (movie_id,))
            movie_title = cur.fetchone()[0]
            bot.send_message(chat_id, f"Названиe: {movie_title}\nОценка: {all[i][3]}\nМнение: {all[i][4]}")
        if len(all) == 0:
            bot.send_message(chat_id, "История отсутствует")


def show_watched_history(user_id, chat_id):
    with connection.cursor() as cur:
        cur.execute(f"SELECT * FROM watchedmovies WHERE user_id = %s",
                    (user_id,))
        all = cur.fetchall()
        for i in range(0, len(all)):
            movie_id = all[i][2]
            cur.execute("SELECT title FROM movies where movie_id = %s", (movie_id,))
            movie_title = cur.fetchone()[0]
            bot.send_message(chat_id,
                             f"Названиe: {movie_title}\nОценка: {all[i][3]}\nМнение: {all[i][4]}\nДата добавление: {all[i][-1]}")
        if len(all) == 0:
            bot.send_message(chat_id, "История отсутствует")


def show_want_history(user_id, chat_id):
    with connection.cursor() as cur:
        cur.execute(f"SELECT movie_id,reason FROM wantedtowatch WHERE user_id =%s", (user_id,))
        all = cur.fetchall()
        for i in range(0, len(all)):
            movie_id = all[i][0]
            cur.execute("SELECT title FROM movies where movie_id = %s", (movie_id,))
            movie_title = cur.fetchone()[0]
            bot.send_message(chat_id, f"Название: {movie_title}\nПричина: {all[i][1]}")
        if len(all) == 0:
            bot.send_message(chat_id, "История отсутствует")


def delete_watched(user_id, movie_id):
    with connection.cursor() as cur:
        cur.execute("DELETE FROM watchedmovies WHERE user_id = %s and movie_id = %s", (user_id, movie_id))
        connection.commit()


def delete_want_watch(user_id, movie_id):
    with connection.cursor() as cur:
        cur.execute("DELETE FROM wantedtowatch WHERE user_id = %s and movie_id = %s", (user_id, movie_id))
        connection.commit()

def recommendation_review(user_id, chat_id):
    # Предполагается, что connection, TMDB_ID, TMDB_API, requests уже импортированы и настроены

    with connection.cursor() as cur:
        cur.execute("""
            SELECT movie_id 
            FROM watchedmovies 
            WHERE user_id=%s 
            AND rating=(SELECT MAX(rating) FROM watchedmovies WHERE user_id=%s)
            """, (user_id, user_id,))
        movie_id = cur.fetchone()[0]
        cur.execute("SELECT title FROM movies WHERE movie_id = %s", (movie_id,))
        movie_title = cur.fetchone()[0]

    tmdb_id = TMDB_ID(movie_title)
    response = requests.get(
        f"https://api.themoviedb.org/3/movie/{tmdb_id}/recommendations?api_key={TMDB_API}&language=ru-RU&page=1")
    data = response.json()

    # Формируем рекомендации
    recommendations = []
    for movie in data['results'][:5]:  # Для первых 5 рекомендаций
        genres = [all_genres_dict[genre_id] for genre_id in movie["genre_ids"]]#тут находится все названия жанров как массив.
        #Короч сперва фором берет каждый айди из 5 фильмов и после дает новый элемент как genres_dict[genre_id] тут он просто берет элемент с ключом genre_id
        recommendations.append((movie["title"], genres))

    for title, genres in recommendations:
        bot.send_message(chat_id,f"Фильм: {title}\nЖанры: {', '.join(genres)}")

def recommendation_world(chat_id):
    response=requests.get(f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API}&language=ru-RU&page=1")
    data=response.json()
    good_ones = {movie["title"]: movie["genre_ids"] for movie in data["results"] if movie["vote_average"] > 7.5}
    for title, genre_ids in good_ones.items():
        genres = [all_genres_dict[genre_id] for genre_id in genre_ids if genre_id in all_genres_dict]
        bot.send_message(chat_id,f"Название: {title}\nЖанры: {', '.join(genres)}")



@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Добавить в Посмотрел", callback_data="Add_watched")
    btn2 = types.InlineKeyboardButton("Добавить в Хочу посмотреть", callback_data="Add_want_watch")
    markup.add(btn1, btn2)
    btn4 = types.InlineKeyboardButton("Удалить фильм из 'Хочу посмотреть'", callback_data="Delete_want_watch")
    btn5 = types.InlineKeyboardButton("Удалить фильм из 'Посмотрел'", callback_data="Delete_watched")
    markup.add(btn5, btn4)
    btn6 = types.InlineKeyboardButton("Ваши Рекомендации",callback_data="Recom_review")
    btn7 = types.InlineKeyboardButton("Всемирные Рекомендации",callback_data="Recom_world")
    markup.add(btn6,btn7)
    btn3 = types.InlineKeyboardButton("История", callback_data="History")
    markup.add(btn3)
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_message(call):
    chat_id = call.message.chat.id
    registration(chat_id, call.message.from_user.first_name)
    if call.data == "Add_watched":
        bot.send_message(chat_id,
                         "Введите информацию о фильме в формате: \nНазвание фильма, Оценка(2-10), Описание(мнение)")
        user_states[chat_id] = WATCHED
    elif call.data == "Add_want_watch":
        bot.send_message(chat_id, "Введите информацию о фильме в формате:\nНазвание фильма, Причина")
        user_states[chat_id] = WANT_TO_WATCH
    elif call.data == "History":
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("История просмотров", callback_data="watched_history")
        btn2 = types.InlineKeyboardButton("История 'Хочу посмотреть'", callback_data="want_watch_history")
        markup.add(btn1, btn2)
        bot.send_message(chat_id, "Какую историю вы хотите просмотреть?", reply_markup=markup)
    elif call.data == "Delete_watched":
        show_watched_history(user_id, chat_id)
        bot.send_message(chat_id, "Введи название фильма которую хотите удалить из истории")
        user_states[chat_id] = DELETE_WATCHED
    elif call.data == "Delete_want_watch":
        show_want_history(user_id, chat_id)
        bot.send_message(chat_id, "Введи название фильма которую хотите удалить из истории")
        user_states[chat_id] = DELETE_WANT_TO_WATCH

    elif call.data == "watched_history":
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("8-10", callback_data="8-10")
        btn2 = types.InlineKeyboardButton("6-8", callback_data="6-8")
        markup.add(btn1, btn2)
        btn3 = types.InlineKeyboardButton("4-6", callback_data="4-6")
        btn4 = types.InlineKeyboardButton("2-4", callback_data="2-4")
        markup.add(btn3, btn4)
        btn5 = types.InlineKeyboardButton("Просмотреть все с датами", callback_data="ALL")
        markup.add(btn5)
        bot.send_message(chat_id, "С каким рейтингом вы хотели бы посмотреть?", reply_markup=markup)

    elif call.data == "want_watch_history":
        show_want_history(user_id, chat_id)
        start(call.message)

    elif call.data == "Recom_review":
        recommendation_review(user_id,chat_id)
        start(call.message)

    elif call.data == "Recom_world":
        recommendation_world(chat_id)

    elif call.data == "8-10":
        filter(chat_id, user_id, 8)
        start(call.message)
    elif call.data == "6-8":
        filter(chat_id, user_id, 6)
        start(call.message)
    elif call.data == "4-6":
        filter(chat_id, user_id, 4)
        start(call.message)
    elif call.data == "2-4":
        filter(chat_id, user_id, 2)
        start(call.message)

    elif call.data == "ALL":
        show_watched_history(user_id, chat_id)
        start(call.message)


@bot.message_handler(func=lambda message: True)
def add_db(message):
    chat_id = message.chat.id
    user_input = [item.strip() for item in
                  message.text.split(
                      ",")]  # сперва разделяем по запятым потом убираем пробелы в начале и в конце слов или предложение
    if chat_id in user_states:
        add_movie(user_input[0])  # тут movie_id получаем

    if chat_id in user_states and movie_id != 0:
        if user_states[chat_id] == WATCHED:
            if len(user_input) < 3:
                watched_movies(user_id, movie_id, user_input[1], ".", chat_id)
            else:
                watched_movies(user_id, movie_id, user_input[1], user_input[2], chat_id)
            del user_states[chat_id]  # сброс состояния
        elif user_states[chat_id] == WANT_TO_WATCH:
            want_to_watch(user_id, movie_id, user_input[1], chat_id)
            del user_states[chat_id]  # сброс состояния
        elif user_states[chat_id] == DELETE_WATCHED:
            delete_watched(user_id, movie_id)
            bot.send_message(chat_id, f"Успешно удален фильм {user_input[0]} из истории Просмотренных фильмов")
            del user_states[chat_id]
        elif user_states[chat_id] == DELETE_WANT_TO_WATCH:
            delete_want_watch(user_id, movie_id)
            bot.send_message(chat_id, f"Успешно удален фильм {user_input[0]} из истории Хочу посмотреть")
            del user_states[chat_id]
    elif chat_id in user_states and movie_id == 0:
        bot.send_message(chat_id, "Пж введите корректное название фильма и все остальное")

    start(message)

bot.polling()
