import argparse
import sys

from team_picker import create_app, parse_app_args

# INIT_DB_ARG_LONG = "initdb"
# INIT_DB_ARG_SHORT = "idb"
# POSTMAN_TEST_ARG_LONG = "postman_test"
# POSTMAN_TEST_ARG_SHORT = "pt"
# GENERATE_API_ARG_LONG = "generate_api"
# GENERATE_API_ARG_SHORT = "ga"
#
#
# def parse_app_args(argv: list):
#     # parse arguments
#     parser = argparse.ArgumentParser(prog='TeamPicker')
#     parser.add_argument(f"-{INIT_DB_ARG_SHORT}", f"--{INIT_DB_ARG_LONG}",
#                         help="Initialise the database, default no",
#                         action="store_true")
#     parser.add_argument(f"-{POSTMAN_TEST_ARG_SHORT}",
#                         f"--{POSTMAN_TEST_ARG_LONG}",
#                         help="Disable server-side sessions, default no",
#                         action="store_true")
#     parser.add_argument(f"-{GENERATE_API_ARG_SHORT}",
#                         f"--{GENERATE_API_ARG_LONG}",
#                         help="Generate API markdown documentation, "
#                              "as specified file",
#                         type=str)
#
#     args = parser.parse_args(argv)
#     return args


# Default port:
if __name__ == '__main__':
    # parse arguments
    app_args = parse_app_args(sys.argv[1:])

    create_app(args=app_args).run()
