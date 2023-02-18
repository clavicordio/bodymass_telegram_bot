import os
import csv
import uuid
from datetime import datetime, timedelta
import aiosqlite
import sqlite3
from matplotlib.dates import date2num
from matplotlib import pyplot
import numpy as np
from typing import Optional
import requests
from codecs import iterdecode

sqlite_db_path = 'data/bodymass.sqlite'
sqlite_db_users_mass = 'users_mass'

sql_header_path = 'data/bodymass.sql'

csv_tmp_folder = 'data/tmp/'
csv_tmp_filename_template = 'bodymass_{user_id}_{hash}.csv'
csv_uploaded_tmp_filename_template = 'uploaded_{user_id}_{hash}.csv'

plot_tmp_folder = 'data/tmp/'
plot_tmp_filename_template = '{user_id}_{hash}.png'

date_format = "%Y/%m/%d"


if not os.path.exists(sqlite_db_path):
    with sqlite3.connect(sqlite_db_path) as db:
        with open(sql_header_path, 'r') as sql_header:
            for command in sql_header.read().split(';'):
                db.execute(command)


async def add_record_now(user_id: int, body_mass: float) -> None:
    await add_record(user_id, datetime.now().date(), body_mass)


async def add_record(user_id: int, date: datetime.date, body_mass: float) -> None:
    async with aiosqlite.connect(sqlite_db_path) as db:
        query = f"INSERT INTO {sqlite_db_users_mass} (user_id, date, body_mass) " \
                f"VALUES ('{user_id}', '{date.strftime(date_format)}', {body_mass}); "

        await db.execute(query)
        await db.commit()


async def delete_user_data(user_id: int) -> None:
    async with aiosqlite.connect(sqlite_db_path) as db:
        await db.execute(f"DELETE FROM {sqlite_db_users_mass} WHERE user_id = '{user_id}'")
        await db.commit()


async def fetch_user_data(user_id: int):
    async with aiosqlite.connect(sqlite_db_path) as db:
        async with db.cursor() as cursor:
            await cursor.execute(f"SELECT date, body_mass FROM {sqlite_db_users_mass} " 
                                 f"WHERE user_id = '{user_id}' ORDER BY date ASC")
            while row := await cursor.fetchone():
                yield row


def random_hash() -> str:
    """Returns a random 8-piece hash"""
    return uuid.uuid4().hex[:8]


async def plot_user_data(user_id: int, only_two_weeks: bool = False) -> tuple[str, Optional[np.array]]:
    """Plot user data to an image.

    Keyword arguments:
    :param user_id: user id
    :param only_two_weeks: draw progress only for the past 2 weeks

    :return: image temporary file path, speed kg/week
    """
    os.makedirs(plot_tmp_folder, exist_ok=True)
    plot_file_path = os.path.join(plot_tmp_folder,
                                  plot_tmp_filename_template.format(user_id=user_id, hash=random_hash()))

    date_list: list[datetime] = []
    mass_list: list[float] = []
    async for (date_str, body_mass) in fetch_user_data(user_id):
        datetime_object = datetime.strptime(date_str, date_format)
        if only_two_weeks:
            if datetime.now() - datetime_object > timedelta(days=14):
                continue

        date_list.append(datetime_object)
        mass_list.append(body_mass)

    regression_coef = draw_plot_mass(date_list, mass_list, plot_file_path)
    speed_kg_week = round(regression_coef[0] * 7, 2) if regression_coef is not None else None

    return plot_file_path, speed_kg_week


def draw_plot_mass(date: list[datetime], mass: list[float], file_path: str) -> Optional[np.array]:
    x = list(map(date2num, date))
    y = mass

    regression_coef = np.polyfit(x, y, 1) if len(x) > 1 else None
    regression_func = np.poly1d(regression_coef) if len(x) > 1 else None

    pyplot.scatter(x, y)
    if len(x) > 1:
        pyplot.plot(x, regression_func(x))
    pyplot.xticks(x, map(lambda i: i.date(), date), rotation='vertical')
    pyplot.grid()
    pyplot.tight_layout()
    pyplot.savefig(file_path)
    pyplot.close('all')

    return regression_coef


async def user_data_to_csv(user_id: int) -> str:
    """Save user data from the database to a csv file.

    Keyword arguments:
    :param user_id: user id

    :return csv temporary file path
    """

    os.makedirs(csv_tmp_folder, exist_ok=True)
    csv_file_path = os.path.join(csv_tmp_folder,
                                 csv_tmp_filename_template.format(user_id=user_id, hash=random_hash()))
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file_object:
        csv_writer = csv.writer(csv_file_object)
        async for row in fetch_user_data(user_id):
            csv_writer.writerow(row)

    return csv_file_path


class CSVParsingError(Exception):
    pass


async def user_data_from_csv_url(user_id: int, csv_url: str, max_body_weight: int) -> None:
    with requests.get(csv_url) as request:
        csv_reader = csv.reader(iterdecode(request.iter_lines(), 'utf-8'))
        for row in csv_reader:
            try:
                date, body_weight = row
                date = datetime.strptime(date, date_format)
                body_weight = float(body_weight)
                assert 0 < body_weight < max_body_weight
            except Exception:
                raise CSVParsingError()

            await add_record(user_id, date, body_weight)









