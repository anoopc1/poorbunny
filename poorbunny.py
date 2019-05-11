from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import argparse
import os

import cherrypy

from bunny_commands import CommandFactory, ResultType


DEFAULT_PORT = 10086
DETAULT_CMD = 'g'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class PoorBunny(object):
    def __init__(self, commands=None, config_path=None):
        if not commands:
            commands = CommandFactory.export(config_path=config_path)
        self.commands = commands

    @cherrypy.expose
    def default(self, *args, **kwargs):
        return self.do_command(*args, **kwargs)

    def do_command(self, *args, **kwargs):
        if args:
            args_list = args[0].strip().split(None, 1)
            if len(args_list) < 1 or args_list[0] not in self.commands.cmd_list:
                method = DETAULT_CMD
                margs = args[0:]
            else:
                method = args_list[0]
                margs = args_list[1:]
            cmd = self.commands.cmd_list.get(method, None)
            result, rtype = cmd(*margs)
            print("\n\nRequest (method: '{}', args: {})".format(method, margs))
            print("Resolution: result: '{}', rtype: '{}'\n".format(result, rtype))
            if rtype == ResultType.REDIRECTION:
                raise cherrypy.HTTPRedirect(result)
            elif rtype == ResultType.CONTENT:
                # TODO: Add support to directly rendering content BEAUTIFULLY..
                return result


def start_bunny_server(bunny, port=None, host='0.0.0.0', errorlog=None, accesslog=None):
    cherrypy.server.socket_host = host
    cherrypy.server.socket_port = port
    cherrypy.config['log.error_file'] = errorlog
    cherrypy.config['log.access_file'] = accesslog
    return cherrypy.quickstart(bunny)


def parse_args():
    default_config_path = os.path.join(CURRENT_DIR, "config.txt")
    parser = argparse.ArgumentParser(description='Poor Bunny Server.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--port', type=int, required=False,
                        help='Port to run', default=DEFAULT_PORT)
    parser.add_argument('--host', type=str, required=False,
                        help='accesslog path', default='127.0.0.1')
    parser.add_argument('--errorlog', type=str, required=False,
                        help='errorlog path')
    parser.add_argument('--accesslog', type=str, required=False,
                        help='accesslog path')
    parser.add_argument('--config_path', type=str, required=False,
                        help='command config path', default=default_config_path)
    return parser.parse_args()


def main():
    args = parse_args()
    start_bunny_server(PoorBunny(config_path=args.config_path), args.port, args.host, args.errorlog, args.accesslog)


if __name__ == '__main__':
    main()

