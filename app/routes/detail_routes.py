from flask import Blueprint, render_template
from collections import defaultdict
import unicodedata
from app.utils import get_db_connection

bp = Blueprint('detail_routes', __name__)

@bp.route('/tehsils/<table_name>')
def all_tehsils(table_name):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `{table_name}` ORDER BY `उपजोन का नाम`, `जिले का नाम`, `तहसील का नाम`;")
            rows = cursor.fetchall()
    finally:
        connection.close()

    grouped_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    def is_row_empty(row):
        return all(
            val is None or (isinstance(val, str) and val.strip() == '')
            for val in row.values()
        )

    for row in rows:
        if is_row_empty(row):
            continue

        upzone = unicodedata.normalize('NFKC', row['उपजोन का नाम'] or '').strip()
        district = unicodedata.normalize('NFKC', row['जिले का नाम'] or '').strip()
        tehsil = unicodedata.normalize('NFKC', row['तहसील का नाम'] or '').strip()

        grouped_data[upzone][district][tehsil].append(row)


    return render_template('tehsils.html', grouped_data=grouped_data)


@bp.route('/upzone/<table_name>/<upzone_name>')
def upzone_detail(table_name, upzone_name):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = f"SELECT * FROM `{table_name}` WHERE `उपजोन का नाम` = %s"
            cursor.execute(query, (upzone_name,))
            # cursor.execute("SELECT * FROM `{table_name}` WHERE `उपजोन का नाम` = %s", (upzone_name,))
            data = cursor.fetchall()
    finally:
        connection.close()
    return render_template('upzone_detail.html', upzone_name=upzone_name,table_name=table_name, data=data)

@bp.route('/jila/<table_name>/<jila_name>')
def jila_detail(table_name, jila_name):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = f"SELECT * FROM `{table_name}` WHERE `जिले का नाम` = %s"
            cursor.execute(query, (jila_name,))
            # cursor.execute("SELECT * FROM `{table_name}` WHERE `जिले का नाम` = %s", (jila_name,))
            data = cursor.fetchall()
    finally:
        connection.close()
    return render_template('jila_detail.html', jila_name=jila_name, table_name=table_name, data=data)

@bp.route('/tehsil/<table_name>/<tehsil_name>')
def tehsil_detail(table_name, tehsil_name):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = f"SELECT * FROM `{table_name}` WHERE `तहसील का नाम` = %s"
            cursor.execute(query, (tehsil_name,))
            # cursor.execute("SELECT * FROM `{table_name}` WHERE `तहसील का नाम` = %s", (tehsil_name,))
            data = cursor.fetchall()
    finally:
        connection.close()
    return render_template('tehsil_detail.html', tehsil_name=tehsil_name, table_name=table_name, data=data)