from flask import Blueprint, render_template, flash, redirect
from app.utils import get_db_connection

bp = Blueprint('main_routes', __name__)

@bp.route('/')
def index():
    connection = get_db_connection()
    tables = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            print("Tables found:", tables)
    finally:
        connection.close()

    return render_template('index.html', tables=tables)


@bp.route('/view/<table_name>')
def view_table(table_name):
    connection = get_db_connection()
    rows = []
    columns = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `{table_name}`;")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
    except Exception as e:
        flash(f"❌ Error viewing table: {e}")
    finally:
        connection.close()

    return render_template('view_table.html', table_name=table_name, rows=rows, columns=columns)

@bp.route('/delete/<table_name>', methods=['POST'])
def delete_table(table_name):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE `{table_name}`;")
        connection.commit()
        flash(f"🗑️ Table '{table_name}' deleted successfully.")
    except Exception as e:
        flash(f"❌ Error deleting table: {e}")
    finally:
        connection.close()

    return redirect('/')


# --------------------------------------------Merged view of all tables---------------------------------------
@bp.route('/merge-view')
def merge_view():
    connection = get_db_connection()
    merged_data = []
    all_columns = []
    table_column_map = {}
    total_upasthiti = 0
    total_rows = 0

    try:
        with connection.cursor() as cursor:
            # Get all tables excluding metadata
            cursor.execute("SHOW TABLES;")
            tables = [list(row.values())[0] for row in cursor.fetchall() if 'metadata' not in list(row.values())[0]]

            # Collect column names in order
            seen_columns = set()
            for table in tables:
                cursor.execute(f"SHOW COLUMNS FROM `{table}`;")
                table_columns = [row['Field'] for row in cursor.fetchall()]
                table_column_map[table] = table_columns
                for col in table_columns:
                    if col not in seen_columns:
                        all_columns.append(col)
                        seen_columns.add(col)

            # Fetch data from tables
            sr_no = 1
            for table in tables:
                cursor.execute(f"SELECT * FROM `{table}`;")
                rows = cursor.fetchall()
                total_rows += len(rows)

                for row in rows:
                    row_data = {}
                    row_data['Sr. No.'] = sr_no
                    row_data['source_table'] = table
                    sr_no += 1

                    for col in all_columns:
                        value = row.get(col, '') if isinstance(row, dict) else ''
                        row_data[col] = value

                        if col == 'उपस्थिति (संख्या)' and isinstance(value, (int, float, str)):
                            try:
                                total_upasthiti += int(str(value).strip())
                            except:
                                pass

                    merged_data.append(row_data)

    finally:
        connection.close()

    
    display_columns = ['Sr. No.', 'source_table'] + all_columns

    return render_template(
        'merged_view.html',
        data=merged_data,
        columns=display_columns,
        total_rows=total_rows,
        total_upasthiti=total_upasthiti
    )




@bp.route('/clear', methods=['POST'])
def clear_table():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            for table in tables:
                cursor.execute(f"DELETE FROM `{table}`")
        connection.commit()
        flash("सभी तालिकाओं से डाटा हटा दिया गया।")
    finally:
        connection.close()
    return redirect('/')
