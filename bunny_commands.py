from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from functools import wraps
from requests.models import Request

GOOGLE_MAIL = 'https://mail.google.com/mail/u/'

class ResultType(object):
    REDIRECTION = 'redirection'
    CONTENT = 'content'


class BunnyCommands(object):
    def __init__(self, cmd_list):
        self.cmd_list = cmd_list

class CommandFactory(object):
    REGISTERED_COMMANDS = {}
    CONFIG_PATH = None

    @classmethod
    def export(cls, cmd_list=None, config_path=None):
        # TODO: Use cmd_list to have configurable command list
        # commands = [x for x in cls.REGISTERED_COMMANDS if x.__name__ in cmd_list]
        cls.CONFIG_PATH = config_path
        process_config(cls.CONFIG_PATH)
        commands = cls.REGISTERED_COMMANDS
        print("All registered commands:\n{}".format("\n".join(sorted(commands.keys()))))
        return BunnyCommands(commands)


def register_dynamic_command(command_name, url_format):
    def cmd_impl(*args, **kwargs):
         # use default empty string args if not enough args provided, str.format ignored extra args
        url_args = list(args[:])
        url_args.extend([''] * 10)
        url = url_format.format(*url_args)
        return Request(url=url).prepare().url, ResultType.REDIRECTION
    CommandFactory.REGISTERED_COMMANDS[command_name] = cmd_impl


def process_config(config_path):
    if not config_path:
        print("No config provided for commands..")
        return
    with open(config_path, 'r') as fp:
        for line in fp:
            line = line.strip()
            if len(line) == 0 or line.startswith("#"):
                continue
            command_info_list = line.split()
            print("Processing command from config: {}", command_info_list)
            if len(command_info_list) != 2:
                print("Could not process command (potentially invalid): {}".format(line))
                continue
            register_dynamic_command(command_info_list[0], command_info_list[1])


def register_command(cmd):
    CommandFactory.REGISTERED_COMMANDS[cmd.__name__] = cmd
    return cmd


def register_redirection_command(cmd):
    @wraps(cmd)
    def wrapped(*args, **kwargs):
        ret = cmd(*args, **kwargs)
        return ret, ResultType.REDIRECTION
    register_command(wrapped)
    return wrapped

def register_content_command(cmd):
    @wraps(cmd)
    def wrapped(*args, **kwargs):
        ret = cmd(*args, **kwargs)
        return ret, ResultType.CONTENT
    register_command(wrapped)
    return wrapped


@register_content_command
def _debug(*args, **kwargs):
    try:
        method, margs = args[0].split(None, 1)
        margs = [margs] + list(args[1:])
    except ValueError:
        method = args[0]
        margs = args[1:]
    real_cmd = CommandFactory.REGISTERED_COMMANDS.get(method, None)
    if not callable(real_cmd):
        return 'Error, {method} not found!'.format(method=method)
    else:
        result, _ = real_cmd(*margs, **kwargs)
        return "<code><b>poorbunny</b><br/> DEBUG: redirect to <a href='{url}'>{url}</a></code>".format(url=result)


@register_content_command
def _ls(*args, **kwargs):
    '''list all available commands'''
    supported_commands = "<br/>".join(sorted(CommandFactory.REGISTERED_COMMANDS.keys()))
    return "Supported Commands: <br/> {}".format(supported_commands)


@register_content_command
def _help(*args, **kwargs):
    config_path = CommandFactory.CONFIG_PATH
    if not config_path:
        raise "No config found"
    content = ["Filepath: {}".format(config_path)]
    with open(config_path, 'r') as fp:
        x = list(fp)
        x = map(lambda l: l.strip(), x)
        x = filter(lambda l: len(l) > 0 and not l.startswith('#'), x)
        x = map(lambda l: l.replace(" ", " ------->    ", 1), x)
        content.extend(sorted(x))
    return "<br/><br/>".join(content)
