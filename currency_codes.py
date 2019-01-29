import pandas as pd
from flask_sqlalchemy import SQLAlchemy
import * from models

def main():

    # Check for environment variable
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set")
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    df = pd.read_csv('c:\\dev\\Bucketlist\\data_import\\codes.csv',sep=',', engine='python')

