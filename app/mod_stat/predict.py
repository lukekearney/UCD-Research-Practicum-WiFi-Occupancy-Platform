import pandas as pd
import statsmodels.formula.api as sm
import numpy as np
from sklearn.externals import joblib
from app.mod_db import *
import sqlite3

def predict(csv):
    """
    Generates new predictions from an uploaded CSV file and returns a pandas dataframe. 
    """

    # Loads the serialised analytic models.
    if csv.endswith(".csv"):
        lrm = joblib.load("app/mod_stat/model_linear.pkl")
        log = joblib.load("app/mod_stat/model_binary.pkl")

        # Reads the CSV file.
        df = pd.read_csv(csv)

        # Generates predicted values in new columns.
        df["predicted"] = list(map(lambda x: int(lrm.predict(x)[0]), df["associated"]))
        df["predicted_is_occupied"] = list(map(lambda x: log.predict(x)[0], df["associated"]))

    return df

def generate_scores():
    """
    Populates the "classes" and "rooms" tables of the database with aggregate scores. 
    rooms_occupancy_score represents the percentage of open hours (9am-5pm) during which the room is occupied in the dataset. 
    classes_attendance_score represents average attendance of the module during open hours relative to its size. 
    """

    # Creates a direct SQL connection to database.
    con = sqlite3.connect("database.db")        
    
    # Queries each unique room from the database. 
    results = Rooms.select(Rooms.room_number).distinct()
    print(results)
    rooms = []
    for room in results:
        rooms.append(room.get_result()["room_number"]) 
    
    # Iterates over rooms. 
    for room in rooms:
        # Queries counts from 9AM to 5PM for that room.
        df = pd.read_sql_query(
        "SELECT * FROM counts WHERE counts_room_number = '" + room + "' AND counts_time LIKE '%09:__:%' \
        UNION SELECT * FROM counts WHERE counts_room_number = '" + room + "' AND counts_time LIKE '%10:__:%'\
        UNION SELECT * FROM counts WHERE counts_room_number = '" + room + "' AND counts_time LIKE '%11:__:%'\
        UNION SELECT * FROM counts WHERE counts_room_number = '" + room + "' AND counts_time LIKE '%12:__:%'\
        UNION SELECT * FROM counts WHERE counts_room_number = '" + room + "' AND counts_time LIKE '%13:__:%'\
        UNION SELECT * FROM counts WHERE counts_room_number = '" + room + "' AND counts_time LIKE '%14:__:%'\
        UNION SELECT * FROM counts WHERE counts_room_number = '" + room + "' AND counts_time LIKE '%15:__:%'\
        UNION SELECT * FROM counts WHERE counts_room_number = '" + room + "' AND counts_time LIKE '%16:__:%'", con)

        # Ignores empty dataframes. 
        if df["counts_predicted_is_occupied"].count() != 0:
            # Calculates the room score, equal to the number of rows with predicted occupancy divided by the total number of (non-null) rows. 
            room_score = df[df["counts_predicted_is_occupied"] == 1.0]["counts_predicted_is_occupied"].count() / df["counts_predicted_is_occupied"].count()

            # Records the score in the database. 
            query = Rooms.update(room_occupancy_score = room_score).where(Rooms.room_number == room)
            query.execute()
    
    """
    # Queries each unique module from the database. 
    results = Classes.select(Classes.classes_module_code).distinct()
    print(results)
    modules = []
    for module in results:
        modules.append(module.get_result()["classes_module_code"]) 
    
    # Iterates over modules. 
    for module in modules:
        # Gets the module's size.
        results = Classes.select(Classes.classes_size).where(Classes.classes_module_code == module)
        size = results.get_result()

        # Queries counts from 9AM to 5PM for that room.
        df = pd.read_sql_query(
        "SELECT * FROM counts WHERE counts_module_code = '" + module + "' AND counts_time LIKE '%09:__:%' \
        UNION SELECT * FROM counts WHERE counts_module_code = '" + module + "' AND counts_time LIKE '%10:__:%'\
        UNION SELECT * FROM counts WHERE counts_module_code = '" + module + "' AND counts_time LIKE '%11:__:%'\
        UNION SELECT * FROM counts WHERE counts_module_code = '" + module + "' AND counts_time LIKE '%12:__:%'\
        UNION SELECT * FROM counts WHERE counts_module_code = '" + module + "' AND counts_time LIKE '%13:__:%'\
        UNION SELECT * FROM counts WHERE counts_module_code = '" + module + "' AND counts_time LIKE '%14:__:%'\
        UNION SELECT * FROM counts WHERE counts_module_code = '" + module + "' AND counts_time LIKE '%15:__:%'\
        UNION SELECT * FROM counts WHERE counts_module_code = '" + module + "' AND counts_time LIKE '%16:__:%'", con)
        
        # Ignores null values. 
        df_obs = df[pd.notnull(df["counts_predicted"])]    

        # Ignores empty dataframes. 
        if df["counts_predicted"].count() != 0:
            # Calculates the attendance score, equal to the number of rows with predicted occupancy divided by the total number of (non-null) rows. 
            attendance_score = df[df["counts_predicted_is_occupied"] == 1.0]["counts_predicted_is_occupied"].count() / df["counts_predicted_is_occupied"].count()
            print(attendance_score)

            # Records the score in the database. 
    """


def predict_all():
    """ 
    Populates all rows of the database with predicted occupancy 
    generated by the models (if they contain log data).
    Only intended to be run once; further predictions are generated by 
    predict() whenever a new file is uploaded. 
    """
    
    # Loads the serialised analytic models. 
    lrm = joblib.load("app/mod_stat/model_linear.pkl")    
    log = joblib.load("app/mod_stat/model_binary.pkl")
    
    # Queries each unique associated count value from the database.
    results = Counts.select(Counts.counts_associated).distinct()
    
    count_values = []
    for result in results:
        if result.get_result()["counts_associated"] != "None":
            count_values.append(result.get_result()["counts_associated"])

    # For each unique associated count value:
    for count in count_values:
        # Updates every row of the database having that value with a corresponding predicted count. 
        query = Counts.update(counts_predicted=int(lrm.predict(int(count))[0])).where(Counts.counts_associated == count)
        query.execute()

        # Updates every row of the database having that value with a corresponding binary estimation. 
        query = Counts.update(counts_predicted_is_occupied=log.predict(int(count))[0]).where(Counts.counts_associated == count)
        query.execute()

