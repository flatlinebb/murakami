from collections import OrderedDict
import logging
import os

import configargparse
import tomlkit

import murakami.defaults as defaults
from murakami.server import MurakamiServer

config = None


def load_env():
    """This function loads the local environment into a dict and returns it."""
    acc = {}
    env = {k: v for k, v in os.environ.items() if k.startswith("MURAKAMI_")}

    def recurse(key, value, acc):
        key, *re = key.split("_", 1)
        if re:
            recurse(re[0], value, acc.setdefault(key.lower(), {}))
        else:
            acc[key.lower()] = value

    for k, v in env.items():
        recurse(k, v, acc)
    if "murakami" in acc:
        return acc["murakami"]
    else:
        return {}


class TomlConfigFileParser(configargparse.ConfigFileParser):
    """
    This custom parser uses Tomlkit to parse a .toml configuration file,
    and then merges matching environment variables, and then puts then saves
    the result while passing back just the settings portion to configargparse.
    """
    def get_syntax_description(self):
        """Returns a description of the file format parsed by the class."""
        msg = ("Parses a TOML-format configuration file "
               "(see https://github.com/toml-lang/toml for the spec).")
        return msg

    def parse(self, stream):
        """
        Takes a TOML file stream and parses it, merging it with the
        environment, and then passes back just the settings portion.
        """
        global config
        config_file = tomlkit.parse(stream.read())
        config_env = load_env()
        config = {**config_file, **config_env}
        settings = OrderedDict()
        if "settings" in config:
            for key, value in config["settings"].items():
                settings[key] = str(value)

        return settings


def main():
    """ The main function for Murakami."""
    parser = configargparse.ArgParser(
        auto_env_var_prefix="murakami_settings_",
        config_file_parser_class=TomlConfigFileParser,
        default_config_files=defaults.CONFIG_FILES,
        description="The Murakami network test runner.",
        ignore_unknown_config_file_keys=True,
    )
    parser.add(
        "-c",
        "--config",
        is_config_file=True,
        required=False,
        help="Configuration file path (default: /etc/murakami/murakami.toml).",
    )
    parser.add(
        "-p",
        "--port",
        type=int,
        default=defaults.HTTP_PORT,
        help="The port to listen on for incoming connections (default: 80).",
    )
    parser.add("-n",
               "--hostname",
               help="The mDNS hostname for WebThings (default: automatic).")
    parser.add(
        "-s",
        "--ssl-options",
        nargs="?",
        dest="ssl_options",
        help="SSL options for the WebThings server (default: none).",
    )
    parser.add(
        "-r",
        "--additional-routes",
        nargs="?",
        dest="additional_routes",
        help="Additional routes for the WebThings server (default: none).",
    )
    parser.add(
        "-b",
        "--base-path",
        default="",
        dest="base_path",
        help="Base URL path to use, rather than '/' (default: '').",
    )
    parser.add(
        "-l",
        "--log",
        dest="loglevel",
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add(
        "-t",
        "--tests-per-day",
        dest="tests_per_day",
        type=int,
        default=defaults.TESTS_PER_DAY,
        help="Set the number of tests per day.",
    )
    parser.add(
        "-i",
        "--immediate",
        action="store_true",
        dest="immediate",
        default=False,
        help="Immediately run available tests on startup.",
    )
    settings = parser.parse_args()

    logging.basicConfig(
        level=settings.loglevel,
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s",
    )

    global config
    if not config:
        config = load_env()

    server = MurakamiServer(
        port=settings.port,
        hostname=settings.hostname,
        ssl_options=settings.ssl_options,
        additional_routes=settings.additional_routes,
        base_path=settings.base_path,
        tests_per_day=settings.tests_per_day,
        immediate=settings.immediate,
        config=config,
    )

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
