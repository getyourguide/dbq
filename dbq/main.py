import os
import sys
import json
import atexit
from argparse import ArgumentParser
from shutil import get_terminal_size
from subprocess import Popen, PIPE
from textwrap import dedent
from pkg_resources import get_distribution

from databricks_dbapi import databricks
from tabulate import tabulate

MAX_ROWS = 100
HISTORY = os.path.join(os.path.expanduser('~'), '.dbq_history')


def read_credentials():
    filename = os.path.join(
        os.path.expanduser('~'), '.databricks-credentials.json'
    )

    try:
        with open(filename) as f:
            return json.load(f)
    except FileNotFoundError:
        print('Databricks credentials missing!', file=sys.stderr)
        print(
            dedent(
                f'''\
                    Please set up {filename} as follows:

                    {{
                        "cluster": "A CLUSTER NAME",
                        "host": "dbc-????????-????.cloud.databricks.com",
                        "token": "YOUR API ACCESS TOKEN"
                    }}'''
            ),
            file=sys.stderr,
        )
        sys.exit(1)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        'query',
        help='query to run, use - to read from stdin or omit for '
        'interactive session',
        metavar='QUERY',
        nargs='?',
    )
    return parser.parse_args()


def render(cursor):
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    table = tabulate(rows[:MAX_ROWS], headers)

    return (
        table
        + '\n\nshowing '
        + (
            f'first {MAX_ROWS} rows'
            if len(rows) > MAX_ROWS
            else f'full result, {len(rows)} row(s)'
        )
    )


def get_text_size(text):
    lines = text.split('\n')
    column_count = max(map(len, lines))
    line_count = len(lines)

    return column_count, line_count


def page(output):
    process = Popen(["less", "-R"], stdin=PIPE)

    try:
        process.communicate(output.encode("utf-8"))
    except IOError:
        pass


def display(text):
    term_columns, term_lines = get_terminal_size()
    text_columns, text_lines = get_text_size(text)

    if (
        text_lines + 2 <= term_lines and text_columns <= term_columns
    ) or not sys.stdout.isatty():
        return print(text)

    page(text)


def sanitize_query(query):
    return query + f' LIMIT {MAX_ROWS + 1}'


def try_extract_error(exception):
    try:
        return exception.args[0].status.errorMessage
    except Exception:
        raise exception


def run_query(cursor, query):
    try:
        cursor.execute(sanitize_query(query))
    except Exception as e:
        print(try_extract_error(e), file=sys.stderr)
        return

    display(render(cursor))


def setup_readline():
    import readline

    try:
        readline.read_history_file(HISTORY)
    except FileNotFoundError:
        pass

    atexit.register(readline.write_history_file, HISTORY)


def run_interactive(cursor):
    setup_readline()
    print(get_distribution('dbq'))
    print('running in interactive mode, go ahead and type some SQL...')

    try:
        while True:
            query = input('> ')
            if query:
                run_query(cursor, query)
    except (EOFError, KeyboardInterrupt):
        print()
        print('Bye!')


def run():
    args = parse_args()
    connection = databricks.connect(**read_credentials())
    cursor = connection.cursor()

    if args.query:
        query = sys.stdin.read() if args.query == '-' else args.query
        run_query(cursor, query)
    else:
        run_interactive(cursor)
