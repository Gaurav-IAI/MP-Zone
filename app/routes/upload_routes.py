from flask import Blueprint, render_template, request, redirect, flash, current_app
import pandas as pd
import os
import re
import time
from werkzeug.utils import secure_filename
from app.utils import get_db_connection, allowed_file

bp = Blueprint('upload_routes', __name__)

def sanitize_table_name(name):
    """Sanitize table name for MySQL: keep Hindi, alphanumeric, replace others with underscore, and limit to 64 chars."""
    sanitized = re.sub(r'[^\w\u0900-\u097F]', '_', name)  # Keep Hindi + alphanum + underscore
    sanitized = re.sub(r'_+', '_', sanitized)  # Collapse multiple underscores
    sanitized = sanitized.strip('_')
    if len(sanitized) > 64:
        print(f"⚠️ Table name too long ({len(sanitized)}). Truncating to 64 chars.")
        sanitized = sanitized[:60] + "_" + str(int(time.time()))[-3:]  # Keep it unique-ish
    return sanitized or f"table_{int(time.time())}"

@bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    print("📥 upload_file() triggered")

    if request.method == 'GET':
        print("🔎 GET request received, rendering upload.html")
        return render_template('upload.html')

    if 'file' not in request.files:
        print("⚠️ No file part in the request.")
        flash('No file part')
        return redirect('/upload')

    file = request.files['file']
    if file.filename == '':
        print("⚠️ No file selected.")
        flash('No selected file')
        return redirect('/upload')

    if file and allowed_file(file.filename):
        print(f"📁 File '{file.filename}' is valid and allowed.")
        original_filename = os.path.splitext(file.filename)[0]
        timestamp = int(time.time())
        safe_filename = f"{timestamp}_.xlsx"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        print(f"📥 File saved to: {file_path}")

        try:
            df = pd.read_excel(file_path)
            print("✅ Excel file read successfully.")

            # 🧼 Strip whitespace from column headers
            df.columns = df.columns.str.strip()

            # 🧼 Strip whitespace from every string cell value
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            print(f"🧾 Cleaned column names: {df.columns.tolist()}")

            print("✅ Excel file read successfully.")
        except Exception as e:
            print(f"❌ Failed to read Excel file: {e}")
            flash(f"Failed to read Excel file: {e}")
            return redirect('/upload')

        
        print(f"🧾 Cleaned column names: {df.columns.tolist()}")

        connection = get_db_connection()

        # --- DEBUG: Fetch columns from an existing table for comparison ---
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES;")
                all_tables = [row[0] for row in cursor.fetchall()]
                
                # Pick one existing table containing 'क्रमांक_1' or fallback to first available user table
                debug_table = next((t for t in all_tables if "क्रमांक_1" in t), None)
                if not debug_table:
                    debug_table = next((t for t in all_tables if t != 'uploads_metadata'), None)

                if debug_table:
                    cursor.execute(f"SHOW COLUMNS FROM `{debug_table}`;")
                    existing_columns = [row[0] for row in cursor.fetchall()]
                    print(f"🔍 Existing table '{debug_table}' columns: {existing_columns}")
                else:
                    print("⚠️ No suitable existing user table found for debug column print.")
        except Exception as e:
            print(f"⚠️ Failed to fetch existing table columns: {e}")
        # -------------------------------------------------------------------

        # Table naming
        table_name = sanitize_table_name(original_filename)
        print(f"🌐 Using original filename as table name: {original_filename}")
        print(f"🛠 Using sanitized table name: {table_name}")

        try:
            with connection.cursor() as cursor:
                # Create table
                column_defs = [f"`{col}` TEXT" for col in df.columns]
                create_query = f"CREATE TABLE `{table_name}` (id INT AUTO_INCREMENT PRIMARY KEY, {', '.join(column_defs)});"
                print(f"📄 Executing SQL: {create_query}")
                cursor.execute(create_query)
                print(f"✅ Table '{table_name}' created successfully.")

                # Insert data
                columns_str = ', '.join([f"`{col}`" for col in df.columns])
                placeholders = ', '.join(['%s'] * len(df.columns))
                insert_query = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders});"

                for _, row in df.iterrows():
                    cursor.execute(insert_query, tuple(row.fillna("").astype(str)))
                print(f"✅ Data inserted into table '{table_name}' successfully.")

                # Record metadata
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS uploads_metadata (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        original_filename TEXT,
                        table_name TEXT,
                        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    INSERT INTO uploads_metadata (original_filename, table_name)
                    VALUES (%s, %s);
                """, (original_filename, table_name))
                print("🗃️ Metadata recorded.")

            connection.commit()
            print("💾 Transaction committed.")
            flash(f"✅ डेटा '{original_filename}' नाम की तालिका में सफलतापूर्वक डाला गया।")
        except Exception as e:
            print(f"❌ Database error: {e}")
            flash(f"❌ त्रुटि: {str(e)}")
        finally:
            print("🔚 Closing DB connection.")
            connection.close()

        return redirect('/')
    else:
        print("❌ Invalid file format uploaded.")
        flash('❌ अमान्य फ़ाइल स्वरूप। कृपया .xlsx फ़ाइल अपलोड करें।')
        return redirect('/upload')
