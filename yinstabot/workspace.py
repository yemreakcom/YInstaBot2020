from argparse import ArgumentParser
from .custom import (
    read_account_infos,
    BotMode,
    operate_bot,
    refresh_data
)
import sys
import os
from datetime import datetime
from ypackage.filesystem import read_json

DATE_HEADER = """
--------------------------

{}

--------------------------

"""

TARGET_USERNAME = "cengturkey"


def parse_arg(username=False, password=False, uids=False, hashtags=False, wait=False):
    parser = ArgumentParser(description='Follow users followers')
    parser.add_argument(
        'paths',
        nargs="+",
        metavar='paths',
        help='Accounts json dosyalarının yolu',
    )
    parser.add_argument(
        '--username',
        '-u',
        dest="username",
        help='Username',
        type=str,
        required=username
    )
    parser.add_argument(
        '--password',
        '-p',
        dest="password",
        help='Password',
        type=str,
        required=password
    )
    parser.add_argument(
        '--user-ids',
        '-uids',
        dest="uids",
        nargs="+",
        help='User id',
        type=str,
        required=uids
    )
    parser.add_argument(
        '--hastags',
        '-hts',
        dest="hashtags",
        nargs="+",
        help='Hashtags',
        type=str,
        required=hashtags
    )
    parser.add_argument(
        '--quite',
        '-q',
        dest="quite",
        help='Deactivate debug log',
        action="store_true",
    )
    parser.add_argument(
        '--no-refresh',
        '-nr',
        dest="noRefresh",
        help='Verileri yenilemez',
        action="store_true",
    )
    parser.add_argument(
        '--proxy',
        '-px',
        dest="proxy",
        help="Dosyadaki proxy'i kullanır",
        action="store_true",
    )
    parser.add_argument(
        '--wait',
        '-w',
        dest="wait",
        help='Wait time (minutes)',
        default=5,
        type=int,
        required=wait,
    )

    args = parser.parse_args()
    return args


def main():
    args = parse_arg()

    global DEBUG, WAIT, NO_REFRESH
    DEBUG, WAIT, NO_REFRESH, PATHS = not args.quite, args.wait, args.noRefresh, args.paths

    for PATH in PATHS:
        if not os.path.isfile(PATHS):
            print(f"`{PATH}` dosyaya ait değil.")
            continue

        user_infos = read_json(PATH, debug=DEBUG)

        usernames = []
        priority_id = None
        for ukey in user_infos:
            account_info = user_infos[ukey]

            # İlk önce refresh işlemi yapılmalı
            if account_info['option'] == BotMode.REFRESH_DATA:
                priority_id = ukey

            if "target_usernames" in account_info:
                usernames += account_info['target_usernames']

        if priority_id is not None:
            operate_bot(user_infos[priority_id],
                        usernames=usernames, no_refresh=NO_REFRESH, debug=DEBUG)
        else:
            account_info = next(iter(user_infos.values()))
            refresh_data(account_info, usernames=usernames, no_refresh=NO_REFRESH, debug=DEBUG)

        for username in user_infos.keys():
            account_info = user_infos[username]
            operate_bot(account_info, usernames=usernames,
                        target_username=TARGET_USERNAME, no_refresh=NO_REFRESH, debug=DEBUG)


# TODO: Account dosyasını dışarıdan alacak şekilde yapılandırılacak
# TODO: Session dizini gibi temiz bir yapısı olmalı
if __name__ == "__main__":
    main()
