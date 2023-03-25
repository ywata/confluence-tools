import argparse
from requests.auth import HTTPBasicAuth
import datetime
import sys
import yaml
import logging
import json
import pprint as pp

from confluence.api import get_space, get_children, rename_page, \
    copy_page, update_page, find_page_by_path, get_page_by_id
from confluence.content import update_tree


def parse_args():
    top_parser = argparse.ArgumentParser()
    top_parser.add_argument('--yaml', help='email and token', type=str, required=True)
    top_parser.add_argument('--log-level', default="ERROR", choices=["NOTEST", "INFO", "DEBUG", "ERROR", "CRITICAL"],
                            help="TRACE, INFO, DEBUG, ERROR, CRITICAL are available")

    cmd_parser = top_parser.add_subparsers(dest='command')
    daily_update_parser = cmd_parser.add_parser('daily-update', help='copy page on confluence')
    daily_update_parser.add_argument('--space', help='space name', required=True)
    daily_update_parser.add_argument('--from', dest='frm', help='page to be copied from', required=True)
    daily_update_parser.add_argument('--into', help='page to be copied int0', required=True)
    daily_update_parser.add_argument('--title-format', help='page title', required=True)

    new_month_parser = cmd_parser.add_parser('new-month', help='prepare for new month')
    new_month_parser.add_argument('--space', help='space name', required=True)
    new_month_parser.add_argument('--from', dest='frm', help='page to be copied from', required=True)
    new_month_parser.add_argument('--title-format', help='page title', required=True)

    download_adf_parser = cmd_parser.add_parser('download-adf', help='download atlassian doc format data')
    download_adf_parser.add_argument('--page-id', help='page id', required=True)
    download_adf_parser.add_argument('--file', help='file name', required=True)

    validate_adf_parser = cmd_parser.add_parser('validate-adf', help='validate atlassian doc format data')
    validate_adf_parser.add_argument('--schema-file', help='file name of atlassian doc format json schema', required=True)
    validate_adf_parser.add_argument('--adf-file', help='file name of atlassian doc format', required=True)

    args = top_parser.parse_args()

    with open(args.yaml, "r") as f:
        dic = yaml.safe_load(f)
        for k in ["url", "email", "token"]:
            if k in dic['confluence']:
                setattr(args, k, dic['confluence'][k])

    log_dict = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARN": logging.WARN,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "NOTEST": logging.NOTSET
    }
    if args.log_level in log_dict:
        logging.getLogger().setLevel(log_dict[args.log_level])
    else:
        logging.getLogger().setLevel(logging.INFO)

    return args


# As newer date should get higher priority, the function
# rturns matched datetime. If title and fmt is same,
# it will get maximum priority.
def dummy_name(format, dt):
    return dt.strftime(dt, f"{format}-%f")

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
            sapces = list(filter(lambda dic: dic['name'] == space_name, res['results']))
            if len(sapces) != 1:
                logging.error(f"multiple {space_name} found")
                sys.exit(1)
            space_id = sapces[0]['id']

            homepage_id = sapces[0]['homepageId']
            top_pages = get_children(url, auth, homepage_id)
            if not top_pages:
                logging.error(f"getting children of homepage failed")
                sys.exit(1)

            logging.info(f"get page down through {args.frm}")
            src_page = find_page_by_path(url, auth, top_pages, args.frm.split('/'))
            if src_page is None:
                logging.error(f"src page not found:{args.frm}")
                sys.exit(1)

            old_title = src_page['title']
            new_title = now.strftime(args.title_format)
            tmp_title = now.strftime(f"{args.title_format}-%f")

            logging.info(f"find a page to be copied in")
            to_page = find_page_by_path(url, auth, top_pages, args.into.split('/'))
            if to_page is None:
                logging.error(f"destination parent not found:{args.into}")
                sys.exit(1)

            logging.info(f"copy page from {old_title} to {new_title} in {to_page['title']}")
            (sc_copy, res_copy) = copy_page(url, auth, src_page, to_page, tmp_title)
            dst_page = res_copy
            if sc_copy != 200:
                logging.error(f"copy page failed:{src_page}")
                sys.exit(1)
            # TODO: after copy_page() is succeeded, any error can cause to\
            #  leave a temporary file named with dummy_title. It has to be deleted.
            logging.info(f"update body of new page")
            (sc_update, res_update) = update_page(url, auth, src_page['id'], update_tree, space_id, new_title)
            if sc_update != 200:
                logging.error("update_page() failed")

            logging.info(f"Rename title from {tmp_title} to {old_title}")
            (sc_rename, res_rename) = rename_page(url, auth, dst_page['id'], old_title)
            if sc_rename != 200:
                logging.error("rename_page() failed")
        except Exception as ex:
            logging.error(ex)
            sys.exit(1)
    elif args.command == 'download-adf':
        (sc,rsp) = get_page_by_id(url, auth, args.page_id, "atlas_doc_format")
        import pprint as pp
        json_str = rsp['body']['atlas_doc_format']['value']
        json_obj = json.loads(json_str)
        with open(args.file, "w") as f:
            json.dump(json_obj, f)
    elif args.command == 'validate-adf':
        schema = None
        adf = None
        with open(args.schema_file, "r") as f:
            json_schema = json.load(f)
        import confluence.adf
        adf_schema = confluence.adf.parse_json_schema(json_schema)
        with open(args.adf_file, "r") as f:
            adf = json.load(f)
        doc_schema = adf_schema.ref_map[adf_schema.ref]
        parsed_adf = confluence.adf.parse_structure(adf_schema, doc_schema, adf)
        pp.pprint(parsed_adf)

    elif args.command == 'new-month':
        sys.exit('not implemented yet')

    else:
        print(f"{args.command} unhandled")
        logging.error(f"{args.command} not handled")
        sys.exit(1)
