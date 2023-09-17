import sqlite3
from argparse import ArgumentParser


def create_data_base(data_base : str, script : str):
    connection = sqlite3.connect(data_base)
    cursor = connection.cursor()
    for command in script.split(';'):
        cursor.execute(command)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-d', '--database', type=str, metavar="FILE")
    parser.add_argument('-s', '--sql', type=str, metavar="FILE")
    args = parser.parse_args()
    with open(args.sql, 'r') as sqlScript:
        script = sqlScript.read()
    create_data_base(args.database, script)
