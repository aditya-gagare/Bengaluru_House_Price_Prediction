
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# Build paths relative to this file
BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "processed" / "Cleaned_data.csv"
MODEL_PATH = BASE_DIR / "models" / "RidgeModel.pkl"

# Load dataset and trained model
data = pd.read_csv(DATA_PATH)

with open(MODEL_PATH, "rb") as file:
    pipe = pickle.load(file)

# Prepare valid locations for the dropdown and validation
locations = sorted(data["location"].dropna().unique().tolist())
location_set = set(locations)


@app.route("/")
def index():
    return render_template("index.html", locations=locations)


@app.route("/predict", methods=["POST"])
def predict():
    try:
        location = request.form.get("location", "").strip()
        bhk = float(request.form.get("bhk", ""))
        bath = float(request.form.get("bath", ""))
        sqft = float(request.form.get("total_sqft", ""))

        # Validate inputs
        if location not in location_set:
            return "Please select a valid location.", 400

        if not all(np.isfinite(value) for value in [bhk, bath, sqft]):
            return "Enter valid numerical values.", 400

        if bhk <= 0 or bath <= 0 or sqft <= 0:
            return "BHK, bathrooms and square feet must be positive.", 400

        # Keep the feature names and order consistent with training
        input_data = pd.DataFrame(
            [[location, sqft, bath, bhk]],
            columns=["location", "total_sqft", "bath", "bhk"]
        )

        prediction = float(pipe.predict(input_data)[0])

        # Use this conversion ONLY if the model predicts price in lakhs.
        prediction = prediction * 100000

        return str(round(prediction, 2))

    except (TypeError, ValueError):
        return "Please enter valid numerical values in all fields.", 400

    except Exception:
        app.logger.exception("House price prediction failed")
        return "Prediction failed. Check the server logs.", 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
