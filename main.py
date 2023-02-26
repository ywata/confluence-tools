import argparse
from requests.auth import HTTPBasicAuth
import datetime
import sys
import yaml
import logging

from confluence.api import get_page_by_title, get_space, get_top_pages, rename_page, \
    copy_page, update_page, find_page_by_path
from confluence.content import update_tree


def parse_args():
    top_parser = argparse.ArgumentParser()
    top_parser.add_argument('--yaml', help='email and token', type=str, required=True)
    top_parser.add_argument('--log-level', default="ERROR", choices=["NOTEST", "INFO", "DEBUG", "ERROR", "CRITICAL"], help="TRACE, INFO, DEBUG, ERROR, CRITICAL are available")

    cmd_parser = top_parser.add_subparsers(dest='command')
    daily_update_parser = cmd_parser.add_parser('daily-update', help='copy page on confluence')
    daily_update_parser.add_argument('--space', help='space name', required=True)
    daily_update_parser.add_argument('--from', dest='frm', help='page to be copied from', required=True)
    daily_update_parser.add_argument('--into', help='page to be copied int0', required=True)
    daily_update_parser.add_argument('--title-format', help='page title', required=True)

    update_page_parser = cmd_parser.add_parser('update-page', help='update page ')
    update_page_parser.add_argument('--page-id', help='page-id')

    new_month_parser = cmd_parser.add_parser('new-month', help='prepare for new month')
    new_month_parser.add_argument('--space', help='space name', required=True)
    new_month_parser.add_argument('--from', dest='frm', help='page to be copied from', required=True)
    new_month_parser.add_argument('--title-format', help='page title', required=True)

    args = top_parser.parse_args()

    with open(args.yaml, "r") as f:
        dic = yaml.safe_load(f)
        for k in ["url", "email", "token"]:
            if k in dic['confluence']:
                setattr(args, k, dic['confluence'][k])

    log_dict = {
        "CRITICAL":logging.CRITICAL,
        "ERROR":logging.ERROR,
        "WARN":logging.WARN,
        "DEBUG":logging.DEBUG,
        "INFO":logging.INFO,
        "NOTEST":logging.NOTSET
    }
    if args.log_level in log_dict:
        logging.getLogger().setLevel(log_dict[args.log_level])
    else:
        logging.getLogger().setLevel(logging.INFO)

    return args


# As newer date should get higher priority, the function
# rturns matched datetime. If title and fmt is same,
# it will get maximum priority.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = parse_args()
    url = args.url
    email = args.email
    token = args.token
    auth = HTTPBasicAuth(email, token)
    now = datetime.datetime.now()

    if args.command == "daily-update":
        try:
            space_name = args.space
            logging.info("get space name")
            (sc, res) = get_space(url, auth)
            if sc != 200:
                logging.error(f"get_space() error")
                sys.exit(1)
            res2 = list(filter(lambda dic: dic['name'] == space_name, res['results']))
            if len(res2) != 1:
                logging.error(f"multiple {space_name} found")
                sys.exit(1)

            space_key = res2[0]['key']
            logging.info(f"get top pages of {space_key}")
            (sc3, res3) = get_top_pages(url, auth, space_key)
            if sc != 200:
                sys.exit('getting top page error')
            top_pages = res3['results']

            logging.info(f"get page down through {args.frm}")
            src_page = find_page_by_path(url, auth, top_pages, args.frm.split('/'))
            if src_page is None:
                logging.error(f"src page not found:{args.frm}")
                sys.exit(1)
            old_title = src_page['title']

            logging.info(f"get page to be copied in")
            to_page = find_page_by_path(url, auth, top_pages, args.into.split('/'))
            if to_page is None:
                logging.error(f"destination parent not found:{args.into}")
                sys.exit(1)

            new_title = now.strftime(args.title_format)
            logging.info(f"copy page from {old_title} to {new_title}")
            (status_code, res5, dummy_title) = copy_page(url, auth, src_page, to_page, new_title)
            if status_code == 202:
                task_id = res5['id']
                # This might be necessary in some situation.
                #(sc, r6) = get_long_running_task_by_id(url, auth, task_id)
            else:
                logging.error(f"copy page failed:{src_page}")
                sys.exit(1)
            # TODO: after copy_page() is succeeded, any error can cause to\
            #  leave a temporary file named with dummy_title. It has to be deleted.
            logging.info(f"update {old_title} with new title {new_title}")
            (sc_up, resp_up) = update_page(url, auth, src_page['id'], update_tree, new_title)
            if sc_up != 200:
                logging.error("update_page() failed")

            logging.info(f"get id of {dummy_title}")
            (sc_dummy, res_dummy) = get_page_by_title(url, auth, space_key, dummy_title)
            if sc_dummy != 200:
                print(sc_dummy, res_dummy)
                logging.error('copied page not found')
                sys.exit(1)
            for p in res_dummy['results']:
                if p['title']== dummy_title:
                    dummy_page_id = p['id']
                    logging.info(f"rename {dummy_title} to {old_title}")
                    (sc_ren, res_ren) = rename_page(url, auth, p, old_title)
                    if sc_ren != 200:
                        logging.error(f"rename {dummy_title} to {old_title} failed.")

        except Exception as ex:
            logging.error(ex)
            sys.exit(1)
    elif args.command == 'update-page':
        try:
            resp = update_page(url, auth, 98793, update_tree, "2023-02-24-xyz")
        except Exception as ex:
            logging.error(f"{ex}")
            sys.exit(1)
    elif args.command == 'new-month':
        sys.exit('not implemented yet')
    else:
        print(f"{args.command} unhandled")
        logging.error(f"{args.command} not handled")
        sys.exit(1)
