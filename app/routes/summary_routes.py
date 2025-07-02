from flask import Blueprint, render_template, abort
from app.utils import get_db_connection

bp = Blueprint('summary_routes', __name__)


required_columns = ['उपजोन का नाम', 'जिले का नाम', 'तहसील का नाम', 'उपस्थिति (संख्या)']

@bp.route('/summary/<table_name>')
def upzone_summary(table_name):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Get actual columns in table
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`;")
            columns = [row['Field'] for row in cursor.fetchall()]
            print(f"Columns in table '{table_name}': {columns}")

            # Mapping expected columns to actual columns
            # This maps space-separated names to underscore names or themselves if present
            col_map = {}
            for col in required_columns:
                # Try exact match first
                if col in columns:
                    col_map[col] = col
                else:
                    # Replace spaces with underscores and check again
                    col_underscore = col.replace(' ', '_')
                    if col_underscore in columns:
                        col_map[col] = col_underscore
                    else:
                        # Not found - return error
                        return f"तालिका '{table_name}' में आवश्यक कॉलम मौजूद नहीं हैं: {col}", 400

            # Build query dynamically with mapped columns
            jila_expr = f"""
                CASE
                    WHEN TRIM(`{col_map['जिले का नाम']}`) IN ('Umariya', 'Umria') THEN 'Umaria'
                    ELSE TRIM(`{col_map['जिले का नाम']}`)
                END
                """

            query = f"""
                SELECT 
                    `{col_map['उपजोन का नाम']}` AS upzone,
                    COUNT(DISTINCT {jila_expr}) AS jila_count,
                    GROUP_CONCAT(DISTINCT {jila_expr} ORDER BY {jila_expr} SEPARATOR ', ') AS jila_names,
                    COUNT(DISTINCT `{col_map['तहसील का नाम']}`) AS tahsil_count,
                    COUNT(*) AS karyakram_sankhya,
                    SUM(`{col_map['उपस्थिति (संख्या)']}`) AS upasthiti
                FROM `{table_name}`
                GROUP BY `{col_map['उपजोन का नाम']}`
                ORDER BY upzone;
                """


            cursor.execute(query)
            summary = cursor.fetchall()
    except Exception as e:
        return f"त्रुटि: {str(e)}", 500
    finally:
        connection.close()

    total = {
        'upzone': 'कुल योग',
        'jila_count': sum(row['jila_count'] or 0 for row in summary),
        'tahsil_count': sum(row['tahsil_count'] or 0 for row in summary),
        'karyakram_sankhya': sum(row['karyakram_sankhya'] or 0 for row in summary),
        'upasthiti': int(sum(row['upasthiti'] or 0 for row in summary)),
    }


    return render_template('summary.html', summary=summary, total=total, table_name=table_name)


# -------------------------------All tables summary--------------------------------

@bp.route('/summary_all')
def summary_all_tables():
    connection = get_db_connection()
    all_summary = []
    try:
        with connection.cursor() as cursor:
            # Get all user-defined tables (skip system tables if needed)
            cursor.execute("SHOW TABLES;")
            tables = [list(row.values())[0] for row in cursor.fetchall()]

            for table_name in tables:
                try:
                    # Get columns for the current table
                    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`;")
                    columns = [row['Field'] for row in cursor.fetchall()]

                    # Map required columns
                    col_map = {}
                    for col in required_columns:
                        if col in columns:
                            col_map[col] = col
                        else:
                            col_underscore = col.replace(' ', '_')
                            if col_underscore in columns:
                                col_map[col] = col_underscore
                            else:
                                raise ValueError(f"Missing column '{col}' in table '{table_name}'")

                    # Prepare and run the query
                    query = f"""
                        SELECT 
                            `{col_map['उपजोन का नाम']}` AS upzone,
                            COUNT(DISTINCT `{col_map['जिले का नाम']}`) AS jila_count,
                            COUNT(DISTINCT `{col_map['तहसील का नाम']}`) AS tahsil_count,
                            COUNT(*) AS karyakram_sankhya,
                            SUM(`{col_map['उपस्थिति (संख्या)']}`) AS upasthiti,
                            '{table_name}' AS table_name
                        FROM `{table_name}`
                        GROUP BY `{col_map['उपजोन का नाम']}`
                        ORDER BY upzone;
                    """
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    all_summary.extend(rows)

                except Exception as inner_error:
                    print(f"[Skipping] {table_name}: {inner_error}")
                    continue

    except Exception as e:
        return f"त्रुटि: {str(e)}", 500
    finally:
        connection.close()

    # Calculate total row
    total = {
        'upzone': 'कुल योग',
        'jila_count': sum(row['jila_count'] or 0 for row in all_summary),
        'tahsil_count': sum(row['tahsil_count'] or 0 for row in all_summary),
        'karyakram_sankhya': sum(row['karyakram_sankhya'] or 0 for row in all_summary),
        'upasthiti': int(sum(row['upasthiti'] or 0 for row in all_summary)),
        'table_name': ''
    }

    return render_template('summary_all.html', summary=all_summary, total=total)
