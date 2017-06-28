#!/usr/bin/python3

import argparse
import os
from bptc import init_logger

__version__ = '0.1'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8000,
                        help='Porting for pulling information from other members and the registry')
    parser.add_argument('-o', '--output', type=str, default='data',
                        help='Output directory for the sqlite3 database and log files')
    parser.add_argument('-cli', '--console', action='store_true', help='Use the interactive shell')
    parser.add_argument('-auto', '--auto', action='store_true', help='Self organizing client')
    parser.add_argument('-r', '--register', type=str, default='localhost:9000', help='Automatically register at given address')
    parser.add_argument('-qm', '--query-members', type=str, default='localhost:9001', help='Adress for querying members automatically')
    return parser.parse_args()

if __name__ == '__main__':
    # Right now there is only one app designed for mobile devices
    cl_args = parse_args()
    os.makedirs(cl_args.output, exist_ok=True)
    init_logger(cl_args.output)
    if cl_args.console:
        from bptc.client.console_app import ConsoleApp
        ConsoleApp(cl_args)()
    elif cl_args.auto:
        from bptc.client.auto_app import AutoApp
        AutoApp(cl_args)()
    else:
        from bptc.client.kivy_app import KivyApp
        KivyApp(cl_args).run()
