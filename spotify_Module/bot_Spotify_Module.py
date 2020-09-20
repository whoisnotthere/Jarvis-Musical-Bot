import time
import random
from spotify_Module import bot_Spotify_Sender
from spotify_Module import spotify_Service
from spotify_Module import spotify_Exceptions
from spotify_Module.spotify_Logger import logger
from libraries import spotify_Oauth
from libraries import database_Manager

logger.info("Spotify Module Ready")

user_Position_Cache = {}
musicQuiz_User_Songs = {}
musicQuiz_User_Stats = {}


def get_User_Position(user_ID):
    """
    Получить позицию пользователя из базы данных
    """
    search_Data = database_Manager.search_In_Database(user_ID, "bot_Users", "telegram_ID")
    user_Position = search_Data[0][3]
    logger.info(f"Get User Position For User {user_ID}")
    return user_Position



def get_User_UniqueID(user_ID):
    """
    Получить уникальный ID пользователя из базы данных
    """
    search_Data = database_Manager.search_In_Database(user_ID, "bot_Users", "telegram_ID")
    user_UniqueID = search_Data[0][1]
    logger.info(f"Get User Unique ID For User {user_ID}")
    return user_UniqueID



def check_Bot_Reg(user_ID):
    """
    Проверить регистрацию в боте
    """
    logger.info(f"Check Bot Reg For User {user_ID}")
    return database_Manager.search_In_Database(user_ID, "bot_Users", "telegram_ID")



def check_Spotify_Login(user_ID):
    """
    Проверить авторизован ли пользователь в Spotify
    """
    logger.info(f"Check Spotify Login For User {user_ID}")
    return database_Manager.search_In_Database(get_User_UniqueID(user_ID), "spotify_Users", "user_Unique_ID")



def to_Main_Menu(user_ID):
    """
    Вернуть пользователя в главное меню
    """
    logger.info(f"Sending Main Menu Keyboard For User {user_ID}")
    database_Manager.write_User_Position(user_ID, "main_Menu")
    bot_Spotify_Sender.controls_Main_Menu(user_ID)



def in_Work(user_ID):
    """
    Поставить пользователю позицию in Work
    """
    logger.info(f"Sending In Work State For User {user_ID}")
    database_Manager.write_User_Position(user_ID, "work_In_Progress")
    bot_Spotify_Sender.playlist_Preparing(user_ID)



def logout_Command(message):
    """
    Обработка команды выхода

    Удаление пользователя из всех таблиц в базе данных
    """
    user_ID = message.from_user.id
    if check_Bot_Reg(user_ID):
        user_Unique_ID = get_User_UniqueID(user_ID)
        logger.info(f"Preparing Logout For User {user_ID}")
        
        database_Manager.delete_User(user_Unique_ID, "bot_Users")
        database_Manager.delete_User(user_Unique_ID, "spotify_Users")

        logger.info(f"Logout Successful For User {user_ID}")
        bot_Spotify_Sender.user_Leaving(message.from_user.id)



def menu_Command(message):
    """
    Обработка команды меню

    Если пользователь авторизован, вернуть его в главное меню
    """
    user_ID = message.from_user.id

    if check_Spotify_Login(user_ID):
        to_Main_Menu(user_ID)



def contacts_Command(message):
    """
    Обработка команды контактов

    Отправить пользователю контакты разработчика
    """
    user_ID = message.from_user.id

    logger.info(f"Sending Contacts For User {user_ID}")
    bot_Spotify_Sender.send_Developer_Contacts(user_ID)






def create_Super_Shuffle(user_ID, tracks_Count=None):
    """
    Создать супер-шаффл для пользователя

    user_ID - Telegram ID пользователя

    tracks_Count - Количество треков для супер-шафла (необязательный параметр, если параметра нет - выбираются все песни из Liked Songs)
    """
    try:
        in_Work(user_ID)

        user_Unique_ID = get_User_UniqueID(user_ID)
        spotify_Service.check_User_Liked_Songs(user_Unique_ID, 200)
        playlist_ID = spotify_Service.super_Shuffle(user_Unique_ID, tracks_Count=tracks_Count)
        playlist_Data = spotify_Service.get_Playlist_Data(user_Unique_ID, playlist_ID)
        
        logger.info(f"Creating Super Shuffle For User {user_ID}")

    except spotify_Exceptions.no_Tracks:
        bot_Spotify_Sender.insufficient_Data_For_Shuffle(user_ID)

    except spotify_Exceptions.oauth_Http_Error:
        bot_Spotify_Sender.cannot_Authorize(user_ID)
        logger.error(f"HTTP ERROR OCCURED WHEN PREPARING SUPER SHUFFLE FOR USER {user_ID}")

    except spotify_Exceptions.oauth_Connection_Error:
        bot_Spotify_Sender.servers_Link_Error(user_ID)
        logger.error(f"CONNECTION ERROR OCCURED WHEN PREPARING SUPER SHUFFLE FOR USER {user_ID}")

    except:
        bot_Spotify_Sender.unknown_Error(user_ID)
        logger.error(f"UNKNOWN ERROR OCCURED WHEN PREPARING SUPER SHUFFLE FOR USER {user_ID}")

    else:
        bot_Spotify_Sender.playlist_Ready(user_ID, playlist_Data)
        logger.info(f"Super Shuffle Created Successfuly For User {user_ID}")

    finally:
        to_Main_Menu(user_ID)



def user_Top_Tracks(user_ID, time_Range):
    """
    Создать топ треков для пользователя

    user_ID - Telegram ID пользователя

    time_Range - Диапазон времени для выборки (short_term, medium_term, long_term)
    """
    try:
        top_Data = spotify_Service.get_User_Top_Tracks(get_User_UniqueID(user_ID), entities_Limit=10, time_Range=time_Range)
        logger.info(f"Get User Top Tracks For User {user_ID}")

    except spotify_Exceptions.no_Tops_Data:
        bot_Spotify_Sender.insufficient_Data_For_Top(user_ID)
        to_Main_Menu(user_ID)

    except spotify_Exceptions.oauth_Http_Error:
        bot_Spotify_Sender.cannot_Authorize(user_ID)
        logger.error(f"HTTP ERROR OCCURED WHEN PREPARING TOP TRACKS LIST FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    except spotify_Exceptions.oauth_Connection_Error:
        bot_Spotify_Sender.servers_Link_Error(user_ID)
        logger.error(f"CONNECTION ERROR OCCURED WHEN PREPARING TOP TRACKS LIST FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    except:
        bot_Spotify_Sender.unknown_Error(user_ID)
        logger.error(f"UNKNOWN ERROR OCCURED WHEN PREPARING TOP TRACKS LIST FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    else:
        bot_Spotify_Sender.tracks_Top(user_ID, top_Data)
        logger.info(f"Top Tracks Prepared Successfuly For User {user_ID}")



def user_Top_Artists(user_ID, time_Range):
    """
    Создать топ исполнителей для пользователя

    user_ID - Telegram ID пользователя

    time_Range - Диапазон времени для выборки (short_term, medium_term, long_term)
    """
    try:
        top_Data = spotify_Service.get_User_Top_Artists(get_User_UniqueID(user_ID), entities_Limit=10, time_Range=time_Range)
        logger.info(f"Get User Top Artists For User {user_ID}")

    except spotify_Exceptions.no_Tops_Data:
        bot_Spotify_Sender.insufficient_Data_For_Top(user_ID)

    except spotify_Exceptions.oauth_Http_Error:
        bot_Spotify_Sender.cannot_Authorize(user_ID)
        logger.error(f"HTTP ERROR OCCURED WHEN PREPARING TOP ARTISTS LIST FOR USER {user_ID}")

    except spotify_Exceptions.oauth_Connection_Error:
        bot_Spotify_Sender.servers_Link_Error(user_ID)
        logger.error(f"CONNECTION ERROR OCCURED WHEN PREPARING TOP ARTISTS LIST FOR USER {user_ID}")

    except:
        bot_Spotify_Sender.unknown_Error(user_ID)
        logger.error(f"UNKNOWN ERROR OCCURED WHEN PREPARING TOP ARTISTS LIST FOR USER {user_ID}")

    else:
        bot_Spotify_Sender.artists_Top(user_ID, top_Data)
        logger.info(f"Top Artists Prepared Successfuly For User {user_ID}")
    
    finally:
        to_Main_Menu(user_ID)



def create_Top_Playlist(user_ID, time_Range):
    """
    Создать плейлист из топ треков для пользователя

    user_ID - Telegram ID пользователя

    time_Range - Диапазон времени для выборки (short_term, medium_term, long_term)
    """
    try:
        in_Work(user_ID)
        user_Unique_ID = get_User_UniqueID(user_ID)
        playlist_ID = spotify_Service.create_Top_Tracks_Playlist(user_Unique_ID, time_Range=time_Range)
        playlist_Data = spotify_Service.get_Playlist_Data(user_Unique_ID, playlist_ID)
        logger.info(f"Creating Top Tracks Playlist For User {user_ID}")

    except spotify_Exceptions.oauth_Http_Error:
        bot_Spotify_Sender.cannot_Authorize(user_ID)
        logger.error(f"HTTP ERROR OCCURED WHEN PREPARING TOP TRACKS PLAYLIST FOR USER {user_ID}")

    except spotify_Exceptions.oauth_Connection_Error:
        bot_Spotify_Sender.servers_Link_Error(user_ID)
        logger.error(f"CONNECTION ERROR OCCURED WHEN PREPARING TOP TRACKS PLAYLIST FOR USER {user_ID}")

    except:
        bot_Spotify_Sender.unknown_Error(user_ID)
        logger.error(f"UNKNOWN ERROR OCCURED WHEN PREPARING TOP TRACKS PLAYLIST FOR USER {user_ID}")

    else:
        bot_Spotify_Sender.playlist_Ready(user_ID, playlist_Data)
        logger.info(f"Top Tracks Playlist Created Successfuly For User {user_ID}")
    
    finally:
        to_Main_Menu(user_ID)



def process_MusicQuiz_Round(user_ID, game_Round):
    """
    Подготовить массив данных для раунда музыкальной викторины

    user_ID - Telegram ID пользователя

    game_Round - Номер раунда музыкальной викторины
    """
    try:
        musicQuiz_Keyboard_Items = []
        musicQuiz_Keyboard_Items.append(musicQuiz_User_Songs[user_ID]["right_Answers"][game_Round])

        list_Size = len(musicQuiz_User_Songs[user_ID]["other_Answers"]) - 1

        key_Indexes = [] #Генерация массива из 3 цифр для поиска 3 случайных ключей в клавиатуру
        while len(key_Indexes) < 3:
            index = random.randint(10, list_Size)
            if index not in key_Indexes:
                key_Indexes.append(index)

        for index in range(3): #Добавление 3 случачйных вариантов ответа в клавиатуру
            answer_Item = key_Indexes[index]
            musicQuiz_Keyboard_Items.append(musicQuiz_User_Songs[user_ID]["other_Answers"][answer_Item])

        random.shuffle(musicQuiz_Keyboard_Items) #Перемешивание клавиатуры

        musicQuiz_Round_Data = {
            "current_Round":game_Round,
            "audio_URL":musicQuiz_User_Songs[user_ID]["right_Answers"][game_Round]["audio_URL"],
        }

        keyboard_Keys = []
        for key in range(4): #Перевод данных клавиатуры в человеческий вид
            keyboard_Keys.append(musicQuiz_Keyboard_Items[key]["artists"] + " - " + musicQuiz_Keyboard_Items[key]["name"])

        musicQuiz_Round_Data["keyboard"] = keyboard_Keys
        musicQuiz_User_Stats[user_ID].update({
            "game_Round":game_Round,
            "round_Prepared_Timestamp":int(time.time()),
            "round_Answer":musicQuiz_User_Songs[user_ID]["right_Answers"][game_Round]["artists"] + " - " + musicQuiz_User_Songs[user_ID]["right_Answers"][game_Round]["name"],
        })
        
    except:
        logger.error(f"ERROR OCCURED WHEN PROCESSING MUSIC QUIZ FOR USER {user_ID}")
        bot_Spotify_Sender.musicQuiz_Error_RoundProcess(user_ID)
        to_Main_Menu(user_ID)

    else:
        bot_Spotify_Sender.send_MusicQuiz_Round(user_ID, musicQuiz_Round_Data)



def create_MusicQuiz_Top_Tracks(user_ID, time_Range):
    """
    Подготовить выборку из топ треков для музыкальной викторины

    user_ID - Telegram ID пользователя

    time_Range - Диапазон времени для выборки (short_term, medium_term, long_term)
    """
    try:
        database_Manager.write_User_Position(user_ID, "work_In_Progress")
        user_Unique_ID = get_User_UniqueID(user_ID)
        spotify_Service.check_User_Tops(user_Unique_ID, "tracks", time_Range)
        musicQuiz_Data = spotify_Service.create_MusicQuiz_Top_Tracks(user_Unique_ID, time_Range)
        logger.info(f"Creating Top Tracks Music Quiz For User {user_ID}")

    except spotify_Exceptions.no_Tops_Data:
        bot_Spotify_Sender.insufficient_Data_For_MusicQuiz(user_ID)
        to_Main_Menu(user_ID)

    except spotify_Exceptions.oauth_Http_Error:
        bot_Spotify_Sender.cannot_Authorize(user_ID)
        logger.error(f"HTTP ERROR OCCURED WHEN PREPARING TOP TRACKS MUSIC QUIZ FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    except spotify_Exceptions.oauth_Connection_Error:
        bot_Spotify_Sender.servers_Link_Error(user_ID)
        logger.error(f"CONNECTION ERROR OCCURED WHEN PREPARING TOP TRACKS MUSIC QUIZ FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    except spotify_Exceptions.musicQuiz_Error_NoTracks:
        bot_Spotify_Sender.musicQuiz_Error_NoTracks(user_ID)
        logger.error(f"MUSIC QUIZ ERROR WHEN PREPARING GAME FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    except:
        bot_Spotify_Sender.unknown_Error(user_ID)
        logger.error(f"UNKNOWN ERROR OCCURED WHEN PREPARING TOP TRACKS MUSIC QUIZ FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    else:
        musicQuiz_User_Songs[user_ID] = musicQuiz_Data
        musicQuiz_User_Stats[user_ID] = {
            "game_Round":0,
            "round_Prepared_Timestamp":0,
            "round_Answer":"",
            "correct_Answers":0,
            "total_Rounds":10,
        }
        database_Manager.write_User_Position(user_ID, "user_MusicQuiz_inGame")
        process_MusicQuiz_Round(user_ID, 0)



def create_MusicQuiz_Liked_Songs(user_ID):
    """
    Подготовить выборку из Liked Songs для музыкальной викторины

    user_ID - Telegram ID пользователя
    """
    try:
        database_Manager.write_User_Position(user_ID, "work_In_Progress")
        user_Unique_ID = get_User_UniqueID(user_ID)
        spotify_Service.check_User_Liked_Songs(user_Unique_ID, 50)
        musicQuiz_Data = spotify_Service.create_MusicQuiz_Liked_Songs(user_Unique_ID)
        logger.info(f"Creating Liked Songs Music Quiz For User {user_ID}")

    except spotify_Exceptions.no_Tracks:
        bot_Spotify_Sender.insufficient_Data_For_MusicQuiz(user_ID)
        to_Main_Menu(user_ID)

    except spotify_Exceptions.oauth_Http_Error:
        bot_Spotify_Sender.cannot_Authorize(user_ID)
        logger.error(f"HTTP ERROR OCCURED WHEN PREPARING LIKED SONGS MUSIC QUIZ FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    except spotify_Exceptions.oauth_Connection_Error:
        bot_Spotify_Sender.servers_Link_Error(user_ID)
        logger.error(f"CONNECTION ERROR OCCURED WHEN PREPARING LIKED SONGS MUSIC QUIZ FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    except spotify_Exceptions.musicQuiz_Error_NoTracks:
        bot_Spotify_Sender.musicQuiz_Error_NoTracks(user_ID)
        logger.error(f"MUSIC QUIZ ERROR WHEN PREPARING GAME FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    except:
        bot_Spotify_Sender.unknown_Error(user_ID)
        logger.error(f"UNKNOWN ERROR OCCURED WHEN PREPARING LIKED SONGS MUSIC QUIZ FOR USER {user_ID}")
        to_Main_Menu(user_ID)

    else:
        musicQuiz_User_Songs[user_ID] = musicQuiz_Data
        musicQuiz_User_Stats[user_ID] = {
            "game_Round":0,
            "round_Prepared_Timestamp":0,
            "round_Answer":"",
            "correct_Answers":0,
            "total_Rounds":10,
        }
        database_Manager.write_User_Position(user_ID, "user_MusicQuiz_inGame")
        process_MusicQuiz_Round(user_ID, 0)



def chat_Messages_Handler(message):
    user_ID = message.from_user.id
    logger.info(f"New Message: {message.text} From: {message.from_user.id}")

    if not check_Bot_Reg(user_ID): #Если в базе данных его нет, предлагаем зарегистрироваться
        logger.info(f"User {user_ID} Not In Reg Table. Registration...")
        reg_Timestamp = int(time.time())
        generated_Unique_ID = database_Manager.generate_Unique_ID()
        database_Manager.register_User(user_ID, generated_Unique_ID, reg_Timestamp)

    if not check_Spotify_Login(user_ID): #Если пользователь еще не вошел в Spotify, предлагаем войти
        logger.info(f"User {user_ID} Not In Spotify Table. Sending Offer For Login")
        user_Unique_ID = get_User_UniqueID(user_ID)
        spotify_Auth_Link = spotify_Oauth.generate_Auth_Link(user_Unique_ID)
        bot_Spotify_Sender.spotify_Login_Offer(user_ID, spotify_Auth_Link)



    user_Position_Cache[user_ID] = get_User_Position(user_ID) #Записать в словарь позицию пользователя, для уменьшения кол-ва запросов к БД

    #Заглушка если in Work позиция

    if check_Spotify_Login(user_ID):
        logger.info(f"User {user_ID} Have Spotify Login")
        if user_Position_Cache[user_ID] == "work_In_Progress":
            bot_Spotify_Sender.denied_Work_Reason(user_ID)


        #ГЛАВНОЕ МЕНЮ


        if user_Position_Cache[user_ID] == "main_Menu":
            if message.text == "Now Playing": #Пункт Now Playing
                logger.info(f"User {user_ID} Entered To Now Playing")
                try:
                    user_Data = spotify_Service.get_Current_Playing(get_User_UniqueID(user_ID))

                except spotify_Exceptions.no_Playback:
                    bot_Spotify_Sender.nowplaying_Nothing(user_ID)

                except spotify_Exceptions.no_Data:
                    bot_Spotify_Sender.now_Playing_Error(user_ID)

                except spotify_Exceptions.oauth_Http_Error:
                    bot_Spotify_Sender.cannot_Authorize(user_ID)
                    logger.error(f"HTTP ERROR OCCURED WHEN SENDING NOW PLAYING FOR USER {user_ID}")

                except spotify_Exceptions.oauth_Connection_Error:
                    bot_Spotify_Sender.servers_Link_Error(user_ID)
                    logger.error(f"CONNECTION ERROR OCCURED WHEN WHEN SENDING NOW PLAYING FOR USER {user_ID}")

                except:
                    bot_Spotify_Sender.unknown_Error(user_ID)
                    logger.error(f"UNKNOWN ERROR OCCURED WHEN WHEN SENDING NOW PLAYING FOR USER {user_ID}")

                else:
                    bot_Spotify_Sender.now_Playing(user_ID, user_Data)
                    logger.info(f"Sending Now Playing For User {user_ID}")

            elif message.text == "Super Shuffle": #Пункт Супер-шаффла
                logger.info(f"User {user_ID} Entered To Super Shuffle")
                database_Manager.write_User_Position(user_ID, "user_Super_Shuffle")
                bot_Spotify_Sender.shuffle_Tracks_Count(user_ID)
                logger.info(f"Sending Super Shuffle Selector For User {user_ID}")

            elif message.text == "Your Tops": #Пункт топов
                logger.info(f"User {user_ID} Entered To Your Tops")
                database_Manager.write_User_Position(user_ID, "user_Your_Tops")
                bot_Spotify_Sender.tops_Type_Select(user_ID)
                logger.info(f"Sending Your Tops Selector For User {user_ID}")

            elif message.text == "Other": #Пунк разное
                logger.info(f"User {user_ID} Entered To Other")
                database_Manager.write_User_Position(user_ID, "user_Other_Main")
                bot_Spotify_Sender.other_Menu(user_ID)
                logger.info(f"Sending Other For User {user_ID}")

            else:
                bot_Spotify_Sender.astray_Notification(user_ID)


        #ПУНКТ СУПЕР-ШАФФЛА


        if user_Position_Cache[user_ID] == "user_Super_Shuffle":
            if message.text == "100 Tracks":
                create_Super_Shuffle(user_ID, 100)

            elif message.text == "200 Tracks":
                create_Super_Shuffle(user_ID, 200)

            elif message.text == "All Tracks":
                create_Super_Shuffle(user_ID)

            elif message.text == "Back to Menu":
                to_Main_Menu(user_ID)
            
            else:
                bot_Spotify_Sender.astray_Notification(user_ID)


        #ПУНКТ ТОПОВ


        if user_Position_Cache[user_ID] == "user_Your_Tops":
            if message.text == "Tracks":
                bot_Spotify_Sender.tops_Time_Period(user_ID)
                database_Manager.write_User_Position(user_ID, "user_Top_Tracks_Time")

            elif message.text == "Artists":
                bot_Spotify_Sender.tops_Time_Period(user_ID)
                database_Manager.write_User_Position(user_ID, "user_Top_Artists_Time")

            elif message.text == "Back to Menu":
                to_Main_Menu(user_ID)

            else:
                bot_Spotify_Sender.astray_Notification(user_ID)



        if user_Position_Cache[user_ID] == "user_Top_Tracks_Time":
            if message.text == "4 Weeks":
                database_Manager.write_User_Position(user_ID, "user_Top_Tracks_4Weeks")
                user_Top_Tracks(user_ID, time_Range="short_term")

            elif message.text == "6 Months":
                database_Manager.write_User_Position(user_ID, "user_Top_Tracks_6Months")
                user_Top_Tracks(user_ID, time_Range="medium_term")

            elif message.text == "All Time":
                database_Manager.write_User_Position(user_ID, "user_Top_Tracks_AllTime")
                user_Top_Tracks(user_ID, time_Range="long_term")

            else:
                bot_Spotify_Sender.astray_Notification(user_ID)



        if user_Position_Cache[user_ID] == "user_Top_Artists_Time":
            if message.text == "4 Weeks":
                user_Top_Artists(user_ID, time_Range="short_term")

            elif message.text == "6 Months":
                user_Top_Artists(user_ID, time_Range="medium_term")

            elif message.text == "All Time":
                user_Top_Artists(user_ID, time_Range="long_term")

            else:
                bot_Spotify_Sender.astray_Notification(user_ID)



        if user_Position_Cache[user_ID] == "user_Top_Tracks_4Weeks":
            if message.text == "Yes, Create Playlist":
                create_Top_Playlist(user_ID, time_Range="short_term")

            elif message.text == "No, Thanks":
                to_Main_Menu(user_ID)
            
            else:
                bot_Spotify_Sender.astray_Notification(user_ID)

        elif user_Position_Cache[user_ID] == "user_Top_Tracks_6Months":
            if message.text == "Yes, Create Playlist":
                create_Top_Playlist(user_ID, time_Range="medium_term")

            elif message.text == "No, Thanks":
                to_Main_Menu(user_ID)

            else:
                bot_Spotify_Sender.astray_Notification(user_ID)

        elif user_Position_Cache[user_ID] == "user_Top_Tracks_AllTime":
            if message.text == "Yes, Create Playlist":
                create_Top_Playlist(user_ID, time_Range="long_term")

            elif message.text == "No, Thanks":
                to_Main_Menu(user_ID)

            else:
                bot_Spotify_Sender.astray_Notification(user_ID)


        #ПУНКТ ОСТАЛЬНОГО


        if user_Position_Cache[user_ID] == "user_Other_Main":
            if message.text == "YouTube Clip":
                try:
                    database_Manager.write_User_Position(user_ID, "work_In_Progress")
                    bot_Spotify_Sender.search_Clip(user_ID)
                    user_Data = spotify_Service.get_Clip_For_Current_Playing(get_User_UniqueID(user_ID))

                except spotify_Exceptions.no_Playback:
                    bot_Spotify_Sender.nowplaying_Nothing(user_ID)

                except spotify_Exceptions.no_Data:
                    bot_Spotify_Sender.now_Playing_Error(user_ID)

                except spotify_Exceptions.oauth_Http_Error:
                    bot_Spotify_Sender.cannot_Authorize(user_ID)
                    logger.error(f"HTTP ERROR OCCURED WHEN SENDING YOUTUBE CLIP FOR USER {user_ID}")

                except spotify_Exceptions.oauth_Connection_Error:
                    bot_Spotify_Sender.servers_Link_Error(user_ID)
                    logger.error(f"CONNECTION ERROR OCCURED WHEN WHEN SENDING YOUTUBE CLIP FOR USER {user_ID}")

                except:
                    bot_Spotify_Sender.unknown_Error(user_ID)
                    logger.error(f"UNKNOWN ERROR OCCURED WHEN WHEN SENDING YOUTUBE CLIP FOR USER {user_ID}")

                else:
                    bot_Spotify_Sender.clip_Message(user_ID, user_Data)
                    logger.info(f"Sending YouTube Clip For User {user_ID}")

                finally:
                    to_Main_Menu(user_ID)
            
            elif message.text == "Music Quiz":
                logger.info(f"User {user_ID} Entered To Music Quiz")
                database_Manager.write_User_Position(user_ID, "user_MusicQuiz_Type")
                bot_Spotify_Sender.musicQuiz_Rules(user_ID)
                bot_Spotify_Sender.musicQuiz_Type_Select(user_ID)
                logger.info(f"Sending Music Quiz Type Selector For User {user_ID}")

            elif message.text == "Back to Menu":
                to_Main_Menu(user_ID)

            else:
                bot_Spotify_Sender.astray_Notification(user_ID)



        #ПУНКТ МУЗЫКАЛЬНОЙ ВИКТОРИНЫ



        if user_Position_Cache[user_ID] == "user_MusicQuiz_Type":
            if message.text == "Liked Songs":
                bot_Spotify_Sender.musicQuiz_Preparing(user_ID)
                create_MusicQuiz_Liked_Songs(user_ID)

            elif message.text == "Top Tracks":
                database_Manager.write_User_Position(user_ID, "user_MusicQuiz_Time")
                bot_Spotify_Sender.tops_Time_Period(user_ID)

            else:
                bot_Spotify_Sender.astray_Notification(user_ID)

        if user_Position_Cache[user_ID] == "user_MusicQuiz_Time":
            if message.text == "4 Weeks":
                bot_Spotify_Sender.musicQuiz_Preparing(user_ID)
                create_MusicQuiz_Top_Tracks(user_ID, time_Range="short_term")

            elif message.text == "6 Months":
                bot_Spotify_Sender.musicQuiz_Preparing(user_ID)
                create_MusicQuiz_Top_Tracks(user_ID, time_Range="medium_term")

            elif message.text == "All Time":
                bot_Spotify_Sender.musicQuiz_Preparing(user_ID)
                create_MusicQuiz_Top_Tracks(user_ID, time_Range="long_term")

            else:
                bot_Spotify_Sender.astray_Notification(user_ID)
        
        if user_Position_Cache[user_ID] == "user_MusicQuiz_inGame":
            if message.text == musicQuiz_User_Stats[user_ID]["round_Answer"]: #Если сообщение пользователя = правильный ответ
                if (int(time.time()) - musicQuiz_User_Stats[user_ID]["round_Prepared_Timestamp"]) <= 10: #Если с момента создания раунда прошло не более 10 секунд включительно
                    bot_Spotify_Sender.musicQuiz_Correct_Answer(user_ID, musicQuiz_User_Stats[user_ID]) #Засчитать ответ
                    musicQuiz_User_Stats[user_ID]["correct_Answers"] += 1
                else:
                    bot_Spotify_Sender.musicQuiz_Answer_Timeout(user_ID, musicQuiz_User_Stats[user_ID]) #Иначе поражение

            else:
                bot_Spotify_Sender.musicQuiz_Incorrect_Answer(user_ID, musicQuiz_User_Stats[user_ID]) #Поражение если ответ неправильный



            musicQuiz_User_Stats[user_ID]["game_Round"] += 1



            if musicQuiz_User_Stats[user_ID]["game_Round"] < musicQuiz_User_Stats[user_ID]["total_Rounds"]: #Пока раунд < кол-во раундов, отправлять раунды, иначе отправить конец викторины и вернуть в главное меню
                process_MusicQuiz_Round(user_ID, musicQuiz_User_Stats[user_ID]["game_Round"])
            else:
                bot_Spotify_Sender.musicQuiz_End(user_ID, musicQuiz_User_Stats[user_ID])
                to_Main_Menu(user_ID)