from flask import Blueprint, render_template, request, flash
import pandas as pd
import os

bp = Blueprint('samanvayak_routes', __name__)

@bp.route('/samanvayak-details', methods=['GET', 'POST'])
def samanvayak_details():
    if request.method == 'POST':
        filepath = request.form.get('filepath', '').strip()

        if not filepath:
            flash("⚠️ कृपया Excel फ़ाइल का पूरा रास्ता दर्ज करें।")
            return render_template('samanvayak_details.html')

        if not os.path.exists(filepath):
            flash(f"❌ फ़ाइल नहीं मिली: {filepath}")
            return render_template('samanvayak_details.html')

        try:
            # read every sheet into a dict
            all_sheets = pd.read_excel(filepath, engine='openpyxl', sheet_name=None)
        except Exception as e:
            flash(f"❌ Excel फ़ाइल पढ़ने में त्रुटि: {e}")
            return render_template('samanvayak_details.html')

        # build HTML for every sheet
        tables = {}
        for sheet, df in all_sheets.items():
            df = df.fillna('')
            tables[sheet] = df.to_html(classes='table table-bordered',
                                       index=False, escape=False)

        # pass the tables AND the list of sheet names to the template
        return render_template(
            'samanvayak_details.html',
            tables=tables,
            sheet_names=list(tables.keys())        # preserves order
        )

    # GET request
    return render_template('samanvayak_details.html')
