import sys

from team_picker import create_app, parse_app_args


# Default port:
if __name__ == '__main__':
    # parse arguments
    app_args = parse_app_args(sys.argv[1:])

    create_app(args=app_args).run()
