import os
import time
from datetime import datetime
from tqdm import tqdm
import huepy

from instabot import Bot

from ypackage.filesystem import read_json, write_file, read_file
from ypackage.common import exit_if_not

# DEV: Daha düzgünbir yapı kurulabilri
# TODO: YEmreAk üzerinde yazısını yaz

WORKDIR = "yinstabot"
SESSION_DIR_NAME = "sessions"
ACCOUNTS_FILE = "accounts.json"
DATA_DIR_NAME = "data"

BASE_DIR = os.path.join(os.getcwd(), WORKDIR)
SESSION_DIR = os.path.join(BASE_DIR, SESSION_DIR_NAME)
DATA_DIR = os.path.join(BASE_DIR, DATA_DIR_NAME)

MEDIA_LIKER_SUFFIX = "_media_likers.txt"

REFRESH_DONE = False


class BotMode(object):
    BATCH_FOLLOW_UNFOLLOW = 1
    UNFOLLOW_NONFOLLOWERS = 2
    UNFOLLOW_EVERYONE = 3
    FOLLOW_USERS = 4
    REFRESH_DATA = 5


def bot_instance(username: str, password: str, random_proxy=False, proxy: str = False, debug: bool = False, is_threaded=False) -> Bot:
    """Bot'u oluşturma

    Arguments:
        username {str} -- Kullanıcı adı
        password {str} -- Şifre

    Keyword Arguments:
        debug {bool} -- Bilgilendirme mesajlarını aktif eder (default: {False})
        proxy {str} -- Proxy metni `IP:PORT` (default: {False})

    Returns:
        Bot -- Oluşturulan bot (oluşturulmazsa `None`)
    """

    outpath = os.path.join(os.path.join(BASE_DIR, SESSION_DIR_NAME), username)
    os.makedirs(outpath, exist_ok=True)
    os.chdir(outpath)

    def bot_initiate() -> Bot:
        return Bot(
            filter_private_users=False,
            max_follows_per_day=300,
            max_unfollows_per_day=300,
            verbosity=debug
        )

    def bot_login(bot: Bot) -> bool:
        return bot.login(username=username, password=password, is_threaded=is_threaded)

    def bot_login_with_proxy(bot: Bot) -> bool:
        return bot.login(username=username, password=password, proxy=proxy)

    def get_logged_bot() -> Bot:
        bot = bot_initiate()

        func_login = bot_login if proxy is None else bot_login_with_proxy
        logged = func_login(bot)

        # DEV: Logger yapısını kullan
        if debug:
            msg, color = (
                f"Giriş başarılı: {username}", "green") if logged else (f"Giriş yapılamadı: {username}\nKimlik bilgileri veya proxy hatalı olabilir", "red")
            bot.console_print(msg, color=color)

        return bot

    return get_logged_bot()


def follow_nonfollowers(bot: Bot, username: str):
    """Kullanıcı adı verilen hesabın takipçilerinden bizi takip etmeyenleri takip eder

    Arguments:
        bot {Bot} -- Bot objesi
        username {str} -- Kullanıcı adı
    """
    followers = bot.followers
    users = bot.get_user_followers(username)
    for user in users:
        if user not in followers:
            bot.follow(user)


def unfollow_all(bot: Bot):
    """Herkesi takip etmeyi bırakır

    Arguments:
        bot {Bot} -- Bot objesi
    """
    following = bot.following
    for user in following:
        bot.unfollow(user)


def bulk_userinfos(bot: Bot, usernames: list) -> dict:
    user_infos = {}
    for username in usernames:
        user_infos[username] = {}
        users = bot.get_user_followers(username)
        for user in users:
            user_info = bot.get_user_info(user)
            user_infos[username].add(user_info)

    return user_infos


def read_account_infos(debug=False) -> dict:
    """Kullanıcı bilgileri dosyasını okur

    Keyword Arguments:
        debug {bool} -- Bilgilendirme mesajlarını aktif eder (default: {False})

    Returns:
        dict -- Hesapların verileri
    """
    filepath = os.path.join(SESSION_DIR, ACCOUNTS_FILE)
    return read_json(filepath, debug=debug)


def read_account_info(username: str, debug=False) -> dict:
    """Kullanıcı bilgileri dosyasından istenen kullanıcının bilgilerini okur

    Keyword Arguments:
        username {str} -- Kullanıcı adı
        debug {bool} -- Bilgilendirme mesajlarını aktif eder (default: {False})

    Returns:
        dict -- Hesabın verileri
    """
    user_infos = read_account_infos(debug=debug)
    if username in user_infos.keys():
        return user_infos[username]
    elif debug:
        print(f"Kullanıcı adı '{username}' bulunamadı")


def follow_from_hastags(bot: Bot, hastags: list):
    """Hastags (#yemreak) üzerinden kullanıcıları takip etme

    Arguments:
        bot {Bot} -- Bot objesi
        hastags {list} -- Hastag listesi
    """
    for hastag in hastags:
        followers = bot.followers
        users = bot.get_hashtag_users(hastag)
        for user in users:
            if user not in followers:
                bot.follow(user)


def follow_users_from_user_medias(bot: Bot, username: str):
    """Kullanıcının medyalarını beğenen kişileri takip etme

    Arguments:
        bot {Bot} -- Bot objesi
        username {str} -- Medyalarından takip yapılacak kullanıcının adı
    """
    user_id = bot.get_user_id_from_username(username)
    medias = bot.get_user_medias(user_id, filtration=False)
    for media in medias:
        likers = bot.get_media_likers(media)
        for liker in tqdm(likers):
            bot.follow(liker)


def get_users_from_user_medias(bot: Bot, username: str, media_count: int = 0) -> list:
    """Kullanıcının medyalarını beğenen kişileri takip etme

    Arguments:
        bot {Bot} -- Bot objesi
        username {str} -- Medyalarından takip yapılacak kullanıcının adı

    Returns:
        list -- Kullanıcı id'leri
    """
    user_ids = []
    user_id = bot.get_user_id_from_username(username)
    medias = bot.get_user_medias(user_id, filtration=False)

    for i in range(len(medias)):
        if i < media_count:
            likers = bot.get_media_likers(medias[i])
            for liker in tqdm(likers):
                user_ids.append(liker)
        else:
            break

    return user_ids


def get_user_media_liker_datapath(username: str):
    """Verilen kullanıcının paylaşımlarını beğenenlerin saklandıüı dosyanın yolunu döndürür

    Arguments:
        username {str} -- Kullanıcı adı
    """
    return os.path.join(DATA_DIR, username + MEDIA_LIKER_SUFFIX)


def export_users_from_user_medias(bot: Bot, username: str, media_count: int = 0, debug=False):
    """Kullanıcının medyalarını beğenen kişileri dosyaya aktarma

    Arguments:
        bot {Bot} -- Bot objesi
        username {str} -- Medyalarından takip yapılacak kullanıcının adı
    """
    user_ids = get_users_from_user_medias(
        bot, username, media_count=media_count)
    write_file(get_user_media_liker_datapath(
        username), "\n".join(user_ids), debug=debug)


def read_data(filepath: str, debug=False):
    return read_file(filepath, debug=debug).split("\n")


def get_filenames_exported_users_from_user_medias_data() -> list:
    """Kullanıcının medyalarını beğenen kişilerin olduğu dosyaların isimlerini alma

    Returns:
        list -- Dosya isimleri
    """
    filenames = []
    for data in os.listdir(DATA_DIR):
        if MEDIA_LIKER_SUFFIX in data:
            filenames.append(data)
    return filenames


def get_usernames_exported_users_from_user_medias_data() -> list:
    """Kullanıcının medyalarını beğenen kişilerin olduğu dosyaların hangi kullanıcılara ait olduğunu döndürür

    Returns:
        list -- Kullanıcı isimleri
    """
    filenames = get_filenames_exported_users_from_user_medias_data()
    return list(map(lambda filename: filename.replace(
        MEDIA_LIKER_SUFFIX, ""), filenames))


def import_users_from_user_medias(bot: Bot, username: str, debug=False) -> list:
    """Kullanıcının medyalarını beğenen kişileri dosyaya aktarma

    Arguments:
        bot {Bot} -- Bot objesi
        username {str} -- Medyalarından takip yapılacak kullanıcının adı
    """
    user_ids = []
    filepath = get_user_media_liker_datapath(username)
    if os.path.isfile(filepath):
        user_ids = read_data(filepath, debug=debug)

    return user_ids


def import_users_from_all_users_medias(bot: Bot, debug=False) -> list:
    """Tüm saklanan kullanıcının medyalarını beğenen kişileri dosyaya aktarma

    Arguments:
        bot {Bot} -- Giriş yapmış bot objesi

    Keyword Arguments:
        debug {bool} -- Bilgileri ekrana basma (default: {False})

    Returns:
        list -- Eşsiz kullanıcı id'leri
    """
    unique_uids = []

    usernames = get_usernames_exported_users_from_user_medias_data()
    for username in usernames:
        uids = import_users_from_user_medias(bot, username, debug=debug)
        for uid in uids:
            if not uid in unique_uids:
                unique_uids.append(uid)

    return unique_uids


def get_nonfollowers(bot: Bot, following=None) -> list:
    if following is None:
        following = bot.following

    followers = bot.followers

    return list(set(following) - set(followers))


def get_nonfollowing(bot: Bot, user_ids: list, following=None) -> list:
    if following is None:
        following = bot.following

    return [uid for uid in user_ids if uid not in set(following)]


def batch_follow_unfollow_users(bot: Bot, user_ids: list, debug=False, delay_limit=49):
    following = bot.following
    nonfollowers = get_nonfollowers(bot)
    total_following = len(nonfollowers)

    user_ids = get_nonfollowing(bot, user_ids, following=following)
    total_user_ids = len(user_ids)

    count_index = 0
    follow_index = 0
    unfollow_index = 0

    follow_active = unfollow_active = True
    while follow_active or unfollow_active:
        follow_active = follow_active and not bot.reached_limit("follows")
        if follow_active:
            while follow_index < total_user_ids:
                response = bot.follow(user_ids[follow_index])
                if response == bot.api.TRUE:
                    follow_index += 1
                    count_index += 1
                    break
                elif response == bot.api.FEEDBACK_REQUIRED:
                    follow_active = False
                    break

                follow_index += 1

        unfollow_active = unfollow_active and not bot.reached_limit(
            "unfollows")
        if unfollow_active:
            while unfollow_index < total_following:
                response = bot.unfollow(nonfollowers[unfollow_index])
                if response == bot.api.TRUE:
                    unfollow_index += 1
                    count_index += 1
                    break
                elif response == bot.api.FEEDBACK_REQUIRED:
                    unfollow_active = False
                    break

                unfollow_index += 1

        if count_index == delay_limit:
            sleep()
            count_index = 0


def batch_follow_unfollow_users_with_usernames_data(bot: Bot, usernames: list, debug=False, delay_limit=50):
    user_ids = []
    for username in usernames:
        user_ids += import_users_from_user_medias(bot, username)

    batch_follow_unfollow_users(
        bot, list(set(user_ids)), debug=debug, delay_limit=delay_limit)


def sleep(wait=30, debug=False):
    """Botu bekletmek için kullanılır

    Keyword Arguments:
        wait {int} -- Bekleme süresi (dk) (default: {30})
        debug {bool} -- Bilgilendirme mesajlarını aktif eder (default: {False})
    """
    Bot().console_print(
        f"Biraz mola verelim: {wait}dk...", "grey")
    time.sleep(wait * 60)


def initate_bot(account_info, debug, is_threaded=False) -> Bot:
    bot = bot_instance(
        account_info['username'],
        account_info['password'],
        debug=debug,
        is_threaded=is_threaded
    )
    exit_if_not(bot)

    return bot


def terminate_bot(bot: Bot):
    bot.logout()
    exit()


def refresh_data(account_info: dict, debug=False, usernames: list = [], no_refresh: bool = False):
    global REFRESH_DONE
    REFRESH_DONE = no_refresh or REFRESH_DONE
    if not REFRESH_DONE and len(usernames) > 0:
        bot = initate_bot(account_info, debug, is_threaded=True)
        for username in usernames:
            export_users_from_user_medias(
                bot, username, media_count=1)
        bot.logout()

        REFRESH_DONE = True  # Birden fazla yenilemeyi kapatır


def operate_bot(account_info: dict, debug=False, usernames: list = [], target_username: str = None, no_refresh: bool = False):
    bot_mode = account_info['option']
    if bot_mode == BotMode.REFRESH_DATA:
        refresh_data(account_info, debug=debug, usernames=usernames, no_refresh=no_refresh)
        return

    if bot_mode in [1, 2, 3, 4]:
        bot = initate_bot(account_info, debug, is_threaded=True)
    else:
        if bot_mode != 0:
            print("\n-------------------------------------------------------")
            print(
                f"JSON error, there is no `option: {bot_mode}` for `{account_info['username']}`")
            print("-------------------------------------------------------\n")
        return

    try:
        if bot_mode == BotMode.BATCH_FOLLOW_UNFOLLOW:
            batch_follow_unfollow_users_with_usernames_data(
                bot, account_info['target_usernames'], debug=debug)
        elif bot_mode == BotMode.UNFOLLOW_NONFOLLOWERS:
            bot.unfollow_non_followers()
        elif bot_mode == BotMode.UNFOLLOW_EVERYONE:
            bot.unfollow_everyone()
        elif bot_mode == BotMode.FOLLOW_USERS:
            if target_username is not None:
                user_ids = import_users_from_user_medias(bot, target_username)
                bot.follow_users(user_ids)

        bot.logout()
    except KeyboardInterrupt:
        terminate_bot(bot)
