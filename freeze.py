from main import app  # Import your Flask app from main.py

# Set Frozen-Flask options before creating the freezer:
app.config['FREEZER_IGNORE_MISSING'] = True
app.config['FREEZER_RELATIVE_URLS'] = True  # Optional: makes URL generation relative

from flask_frozen import Freezer
freezer = Freezer(app)

if __name__ == '__main__':
    freezer.freeze()
