import json
import math
import time
import random
import urllib
from libraries import database_Manager
from libraries import spotify_Lib
from libraries import spotify_Oauth
from libraries import youtube_Lib
from spotify_Module import spotify_Exceptions



def check_Token_Lifetime(user_Unique_ID):
    """
    Проверить жив ли еще токен, если токен мертв, обновить его

    user_Unique_ID - Внутренний уникальный ID пользователя
    """
    current_Timestamp = int(time.time())
    last_Refresh_Timestamp = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][7]

    if (current_Timestamp - (last_Refresh_Timestamp - 60)) > 3600:
        spotify_Oauth.refresh_Access_Token(user_Unique_ID)



def get_Current_Playing(user_Unique_ID):
    """
    Получить текущее проигрывание пользователя, в случае успеха возвращает словарь

    В случае ошибки возвращает исключение no_Data (не хватает мета-данных)

    user_Unique_ID - Внутренний уникальный ID пользователя
    """
    check_Token_Lifetime(user_Unique_ID)
    user_Auth_Token = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][4]
    user_Playback = spotify_Lib.get_Current_Playback(user_Auth_Token)

    try:
        playback_Data = {"artists":[]}
        for artist in range(len(user_Playback["item"]["artists"])):
            playback_Data["artists"] += [user_Playback["item"]["artists"][artist]["name"]]

        playback_Data["album_Name"] = user_Playback["item"]["album"]["name"]
        playback_Data["song_Name"] = user_Playback["item"]["name"]
        playback_Data["song_Duration"] = user_Playback["item"]["duration_ms"]
        playback_Data["song_URI"] = user_Playback["item"]["uri"]
        playback_Data["external_URL"] = user_Playback["item"]["external_urls"]["spotify"]
        playback_Data["song_Cover_URL"] = user_Playback["item"]["album"]["images"][1]["url"]
    except:
        raise spotify_Exceptions.no_Data
    
    else:
        return playback_Data



def get_Clip_For_Current_Playing(user_Unique_ID):
    """
    Найти в YouTube клип для текущего воспроизведения, в случае успеха возвращает словарь

    В случае ошибки возвращает исключение no_Data (не хватает мета-данных)

    user_Unique_ID - Внутренний уникальный ID пользователя
    """
    check_Token_Lifetime(user_Unique_ID)
    user_Auth_Token = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][4]
    user_Playback = spotify_Lib.get_Current_Playback(user_Auth_Token)

    try:
        playback_Data = {"artists":[]}
        playback_Data["song_Name"] = user_Playback["item"]["name"]

        for artist in range(len(user_Playback["item"]["artists"])):
            playback_Data["artists"] += [user_Playback["item"]["artists"][artist]["name"]]

        search_Keywords = ", ".join(playback_Data["artists"]) + " " + playback_Data["song_Name"]
        search_Result = youtube_Lib.search_Youtube(search_Keywords)
        first_Result_ID = search_Result["items"][0]["id"]["videoId"]
        playback_Data["youtube_URL"] = "https://www.youtube.com/watch?v=" + first_Result_ID
    except:
        raise spotify_Exceptions.no_Data
    
    else:
        return playback_Data



def get_Playlist_Data(user_Unique_ID, playlist_ID):
    """
    Найти в YouTube клип для текущего воспроизведения, возвращает словарь

    user_Unique_ID - Внутренний уникальный ID пользователя

    playlist_ID - Уникальный ID плейлиста в Spotify
    """
    check_Token_Lifetime(user_Unique_ID)
    user_Auth_Token = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][4]
    playlist_Info = spotify_Lib.get_Playlist_Info(user_Auth_Token, playlist_ID)

    playlist_Data = {}
    playlist_Data["name"] = playlist_Info["name"]
    playlist_Data["description"] = playlist_Info["description"]
    playlist_Data["external_URL"] = playlist_Info["external_urls"]["spotify"]
    playlist_Data["total_Tracks"] = playlist_Info["tracks"]["total"]
    playlist_Data["image_URL"] = playlist_Info["images"][1]["url"]

    return playlist_Data



def check_User_Liked_Songs(user_Unique_ID, minimum_Count):
    """
    Проверяет есть ли у пользователя минимальное кол-во Liked Songs, в случае успеха возвращает True

    В случае ошибки возвращает исключение no_Tracks (треков не хватает)

    user_Unique_ID - Внутренний уникальный ID пользователя

    minimum_Count - Кол-во треков
    """
    check_Token_Lifetime(user_Unique_ID)
    user_Auth_Token = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][4]
    user_Data = spotify_Lib.get_Saved_Tracks(user_Auth_Token)

    if user_Data["total"] >= minimum_Count:
        return True
    else:
        raise spotify_Exceptions.no_Tracks



def check_User_Tops(user_Unique_ID, top_Type, time_Range):
    """
    Проверяет есть ли у пользователя полностью заполненный набор топа, в случае успеха возвращает True

    В случае ошибки возвращает исключение no_Tops_Data (топ не полный)

    user_Unique_ID - Внутренний уникальный ID пользователя

    top_Type - Тип топа (tracks, artists)

    time_Range - Диапазон времени для выборки (short_term, medium_term, long_term)
    """
    check_Token_Lifetime(user_Unique_ID)
    user_Auth_Token = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][4]
    user_Top = spotify_Lib.get_User_Tops(user_Auth_Token, top_Type, 50, 0, time_Range)

    if user_Top["total"] >= 50:
        return True
    else:
        raise spotify_Exceptions.no_Tops_Data



def get_User_Top_Tracks(user_Unique_ID, entities_Limit=50, offset=0, time_Range="short_term"):
    """
    Получить список топ треков пользователя

    user_Unique_ID - Внутренний уникальный ID пользователя

    entities_Limit - Лимит выборки

    offset - Сдвиг выборки

    time_Range - Диапазон времени для выборки (short_term, medium_term, long_term)
    """
    check_Token_Lifetime(user_Unique_ID)
    user_Auth_Token = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][4]
    user_Top = spotify_Lib.get_User_Tops(user_Auth_Token, "tracks", entities_Limit, offset, time_Range)

    top_Tracks = {}
    for item in range(entities_Limit):
        top_Tracks[item] = {
            "name":user_Top["items"][item]["name"],
            "artists":user_Top["items"][item]["album"]["artists"][0]["name"],
            "preview_URL":user_Top["items"][item]["preview_url"],
            "URI":user_Top["items"][item]["uri"],
        }

    return top_Tracks



def get_User_Top_Artists(user_Unique_ID, entities_Limit=50, offset=0, time_Range="short_term"):
    """
    Получить список топ исполнителей пользователя

    user_Unique_ID - Внутренний уникальный ID пользователя

    entities_Limit - Лимит выборки

    offset - Сдвиг выборки

    time_Range - Диапазон времени для выборки (short_term, medium_term, long_term)
    """
    check_Token_Lifetime(user_Unique_ID)
    user_Auth_Token = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][4]
    user_Top = spotify_Lib.get_User_Tops(user_Auth_Token, "artists", entities_Limit, offset, time_Range)

    top_Artists = {}
    for artist in range(entities_Limit):
        top_Artists[artist] = {
            "name":user_Top["items"][artist]["name"],
            "followers":user_Top["items"][artist]["followers"]["total"],
            "URI":user_Top["items"][artist]["uri"],
        }

    return top_Artists



def create_Top_Tracks_Playlist(user_Unique_ID, time_Range="short_term"):
    """
    Создать плейлист с топ песнями пользователя

    user_Unique_ID - Внутренний уникальный ID пользователя

    time_Range - Диапазон времени для выборки (short_term, medium_term, long_term)
    """
    check_Token_Lifetime(user_Unique_ID)
    database_User_Data = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")
    user_Auth_Token = database_User_Data[0][4]
    user_Spotify_ID = database_User_Data[0][1]

    top_Data = get_User_Top_Tracks(user_Unique_ID, time_Range=time_Range)

    playlist_Name = time.strftime("Your Top Songs %Y-%m-%d")
    playlist_Description = "The playlist was generated by JarvisMusicalBot."
    new_Playlist_ID = spotify_Lib.create_Playlist(user_Auth_Token, user_Spotify_ID, playlist_Name, playlist_Description)["id"]

    top_Tracks = []
    for track in range(len(top_Data)):
        top_Tracks.append(top_Data[track]["URI"])

    spotify_Lib.add_Tracks_To_Playlist(user_Auth_Token, new_Playlist_ID, top_Tracks)

    return new_Playlist_ID



def create_MusicQuiz_Top_Tracks(user_Unique_ID, time_Range):
    """
    Создать музыкальную викторину из топ треков

    user_Unique_ID - Внутренний уникальный ID пользователя

    В случае ошибки возвращает исключение musicQuiz_Error_NoTracks (не хватает треков для викторины)

    time_Range - Диапазон времени для выборки (short_term, medium_term, long_term)
    """
    check_Token_Lifetime(user_Unique_ID)
    user_Auth_Token = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][4]
    user_Top = spotify_Lib.get_User_Tops(user_Auth_Token, "tracks", 50, 0, time_Range)

    top_Tracks = []
    for item in range(50): #Привести все элементы в человеческий вид
        if user_Top["items"][item]["preview_url"]: #Добавлять в список только песни с превью
            top_Tracks.append({
                "name":user_Top["items"][item]["name"],
                "artists":user_Top["items"][item]["album"]["artists"][0]["name"],
                "preview_URL":user_Top["items"][item]["preview_url"],
            })
    
    random.shuffle(top_Tracks) #Перемешать элементы топа

    right_Answers = []
    for item in range(10): #Выбрать из элементов топа 10 песен для игры
        right_Answers.append({
            "name":top_Tracks[item]["name"],
            "artists":top_Tracks[item]["artists"],
            "audio_URL":top_Tracks[item]["preview_URL"],
        })
        time.sleep(0.5)

        top_Tracks.pop(item) #Удалить их из выборки топа

    musicQuiz_Items = {}
    musicQuiz_Items["right_Answers"] = right_Answers
    musicQuiz_Items["other_Answers"] = top_Tracks

    if len(musicQuiz_Items["right_Answers"]) < 10 or len(musicQuiz_Items["other_Answers"]) < 20:
        raise spotify_Exceptions.musicQuiz_Error_NoTracks

    return musicQuiz_Items



def create_MusicQuiz_Liked_Songs(user_Unique_ID):
    """
    Создать музыкальную викторину из Liked Songs

    user_Unique_ID - Внутренний уникальный ID пользователя

    В случае ошибки возвращает исключение musicQuiz_Error_NoTracks (не хватает треков для викторины)
    """
    check_Token_Lifetime(user_Unique_ID)
    user_Auth_Token = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")[0][4]

    user_Data = spotify_Lib.get_Saved_Tracks(user_Auth_Token)
    total_Iterations = math.ceil(user_Data["total"] / 50) #Поделить кол-во песен на запросы по 50 песен

    offset = 0
    liked_Tracks = []
    for user_Tracks in range(total_Iterations): #Выгрузить все песни пользователя
        user_Tracks = spotify_Lib.get_Saved_Tracks(user_Auth_Token, 50, offset)

        offset += 50

        for track in range(len(user_Tracks["items"])): #Привести все элементы в человеческий вид
            if user_Tracks["items"][track]["track"]["preview_url"]: #Добавлять в список только песни с превью
                liked_Tracks.append({
                    "name":user_Tracks["items"][track]["track"]["name"],
                    "artists":user_Tracks["items"][track]["track"]["artists"][0]["name"],
                    "preview_URL":user_Tracks["items"][track]["track"]["preview_url"],
                })

    random.shuffle(liked_Tracks) #Перемешать элементы топа

    right_Answers = []
    for item in range(10): #Выбрать из элементов топа 10 песен для игры
        right_Answers.append({
            "name":liked_Tracks[item]["name"],
            "artists":liked_Tracks[item]["artists"],
            "audio_URL":liked_Tracks[item]["preview_URL"],
        })
        time.sleep(0.5)

        liked_Tracks.pop(item) #Удалить их из выборки топа

    musicQuiz_Items = {}
    musicQuiz_Items["right_Answers"] = right_Answers
    musicQuiz_Items["other_Answers"] = liked_Tracks

    if len(musicQuiz_Items["right_Answers"]) < 10 or len(musicQuiz_Items["other_Answers"]) < 20:
        raise spotify_Exceptions.musicQuiz_Error_NoTracks

    return musicQuiz_Items



def super_Shuffle(user_Unique_ID, tracks_Count=None):
    """
    Создать супер-шаффл из Liked Songs

    user_Unique_ID - Внутренний уникальный ID пользователя

    tracks_Count - Кол-во треков для супер-шаффла (не менее 100)
    """
    check_Token_Lifetime(user_Unique_ID)
    database_User_Data = database_Manager.search_In_Database(user_Unique_ID, "spotify_Users", "user_Unique_ID")
    user_Auth_Token = database_User_Data[0][4]
    user_Spotify_ID = database_User_Data[0][1]

    user_Data = spotify_Lib.get_Saved_Tracks(user_Auth_Token)
    total_Iterations = math.ceil(user_Data["total"] / 50) #Поделить кол-во песен на запросы по 50 песен

    offset = 0
    liked_Tracks = []
    for user_Tracks in range(total_Iterations): #Выгрузить все песни пользователя
        user_Tracks = spotify_Lib.get_Saved_Tracks(user_Auth_Token, 50, offset)

        offset += 50

        for track in range(len(user_Tracks["items"])): #Достать uri песни из всех данных
            liked_Tracks.append(user_Tracks["items"][track]["track"]["uri"])

    for user_Tracks in range(500): #Перемешать все песни 500 раз
        random.shuffle(liked_Tracks)

    playlist_Name = time.strftime("Super Shuffle %Y-%m-%d %H:%M")
    playlist_Description = "The playlist was generated by JarvisMusicalBot."
    new_Playlist_ID = spotify_Lib.create_Playlist(user_Auth_Token, user_Spotify_ID, playlist_Name, playlist_Description)["id"] #Создать плейлист и получить его ID

    offset = 100
    if tracks_Count: #Если указано кол-во треков то вырезаем кол-во треков, если нет - вся выборка
        total_Iterations = math.ceil(tracks_Count / offset)
    else:
        total_Iterations = math.ceil(len(liked_Tracks) / offset)

    for user_Tracks in range(total_Iterations): #Закидываем все песни в плейлист
        playlist_Tracks = liked_Tracks[offset - 100:offset]
        spotify_Lib.add_Tracks_To_Playlist(user_Auth_Token, new_Playlist_ID, playlist_Tracks)
        offset += 100

    return new_Playlist_ID