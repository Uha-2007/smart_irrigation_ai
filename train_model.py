
import os
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder


# ============================================================
# LOAD DATASET
# ============================================================

DATASET_PATH = "data/irrigation_dataset.csv"

if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError(
        f"Dataset not found: {DATASET_PATH}"
    )

# Create model folder if it does not exist
os.makedirs("model", exist_ok=True)

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully.")
print("Total rows:", len(df))


# ============================================================
# CHECK REQUIRED DATASET COLUMNS
# ============================================================

required_columns = [
    "mode",
    "temperature",
    "humidity",
    "rainfall",
    "rain_probability",
    "crop",
    "growth_stage",
    "irrigation_required",
    "water_required"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns in dataset: {missing_columns}"
    )

# Soil moisture is required for the sensor model
if "soil_moisture" not in df.columns:
    raise ValueError(
        "Missing 'soil_moisture' column required "
        "for sensor model training."
    )


# ============================================================
# FUNCTION TO TRAIN A MODEL
# ============================================================

def train_model(data, mode):

    print("\n====================================")
    print("Training:", mode)
    print("====================================")

    # --------------------------------------------------------
    # Select features
    # --------------------------------------------------------

    if mode == "sensor":

        features = [
            "temperature",
            "humidity",
            "rainfall",
            "rain_probability",
            "soil_moisture",
            "crop",
            "growth_stage"
        ]

    else:

        features = [
            "temperature",
            "humidity",
            "rainfall",
            "rain_probability",
            "crop",
            "growth_stage"
        ]

    # --------------------------------------------------------
    # Select mode data
    # --------------------------------------------------------

    data = data[
        data["mode"].astype(str).str.strip().str.lower()
        == mode.lower()
    ].copy()

    print("Rows used:", len(data))

    if data.empty:
        raise ValueError(
            f"No dataset rows found for mode '{mode}'. "
            "Check the values in the mode column."
        )

    # --------------------------------------------------------
    # Clean required data
    # --------------------------------------------------------

    required_for_mode = [
        "temperature",
        "humidity",
        "rainfall",
        "rain_probability",
        "crop",
        "growth_stage",
        "irrigation_required",
        "water_required"
    ]

    if mode == "sensor":
        required_for_mode.append("soil_moisture")

    data = data.dropna(subset=required_for_mode).copy()

    # Normalize text values
    data["crop"] = data["crop"].astype(str).str.strip()
    data["growth_stage"] = (
        data["growth_stage"].astype(str).str.strip()
    )

    data["irrigation_required"] = (
        data["irrigation_required"]
        .astype(str)
        .str.strip()
        .str.capitalize()
    )

    # Keep only valid classification labels
    data = data[
        data["irrigation_required"].isin(["Yes", "No"])
    ].copy()

    if data.empty:
        raise ValueError(
            f"No valid training rows remain for '{mode}'. "
            "Check missing values and irrigation_required labels."
        )

    # Ensure numerical columns contain valid numbers
    numeric_columns = [
        "temperature",
        "humidity",
        "rainfall",
        "rain_probability",
        "water_required"
    ]

    if mode == "sensor":
        numeric_columns.append("soil_moisture")

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    data = data.dropna(subset=numeric_columns).copy()

    if data.empty:
        raise ValueError(
            f"No valid numeric training data for '{mode}'."
        )

    if (data["water_required"] < 0).any():
        raise ValueError(
            "'water_required' must not contain negative values."
        )

    print("Valid rows after cleaning:", len(data))

    # --------------------------------------------------------
    # Encode crop
    # --------------------------------------------------------

    crop_encoder = LabelEncoder()

    data["crop_encoded"] = crop_encoder.fit_transform(
        data["crop"]
    )

    # --------------------------------------------------------
    # Encode growth stage
    # --------------------------------------------------------

    stage_encoder = LabelEncoder()

    data["stage_encoded"] = stage_encoder.fit_transform(
        data["growth_stage"]
    )

    # --------------------------------------------------------
    # Prepare X
    # --------------------------------------------------------

    if mode == "sensor":

        X = data[
            [
                "temperature",
                "humidity",
                "rainfall",
                "rain_probability",
                "soil_moisture",
                "crop_encoded",
                "stage_encoded"
            ]
        ]

    else:

        X = data[
            [
                "temperature",
                "humidity",
                "rainfall",
                "rain_probability",
                "crop_encoded",
                "stage_encoded"
            ]
        ]

    # --------------------------------------------------------
    # Classification target
    # --------------------------------------------------------

    y_classification = data[
        "irrigation_required"
    ].map({
        "Yes": 1,
        "No": 0
    })

    # --------------------------------------------------------
    # Regression target
    # --------------------------------------------------------

    y_water = data["water_required"]

    # Check target values
    if y_classification.isna().any():
        raise ValueError(
            "Invalid values found in irrigation_required."
        )

    if y_classification.nunique() < 2:
        raise ValueError(
            f"'{mode}' data must contain both Yes and No "
            "in irrigation_required to train the classifier."
        )

    # --------------------------------------------------------
    # Random Forest Classifier
    # --------------------------------------------------------

    classifier = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )

    classifier.fit(
        X,
        y_classification
    )

    # --------------------------------------------------------
    # Random Forest Regressor
    # --------------------------------------------------------

    regressor = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    regressor.fit(
        X,
        y_water
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    model = {
        "classifier": classifier,
        "regressor": regressor,
        "crop_encoder": crop_encoder,
        "stage_encoder": stage_encoder,
        "mode": mode,
        "features": features
    }

    filename = f"model/{mode}_irrigation_model.pkl"

    joblib.dump(
        model,
        filename
    )

    print("Model saved:")
    print(filename)

    print("Crops:", list(crop_encoder.classes_))

    print("Growth stages:", list(stage_encoder.classes_))


# ============================================================
# TRAIN SENSOR MODEL
# ============================================================

train_model(
    df,
    "sensor"
)


# ============================================================
# TRAIN SENSORLESS MODEL
# ============================================================

train_model(
    df,
    "sensorless"
)


print("\n====================================")
print("ALL MODELS TRAINED SUCCESSFULLY")
print("====================================")

