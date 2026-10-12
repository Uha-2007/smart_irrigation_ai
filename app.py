
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import joblib
import requests
import os

app = Flask(__name__)
app.secret_key = "smart_irrigation_secret_key_change_this"

# ---------- WEATHER API KEY ----------
WEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"


# ============================================================
# LOAD SENSORLESS MODEL ONLY
# ============================================================

MODEL_PATH = os.path.join(
    "model",
    "sensorless_irrigation_model.pkl"
)

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Sensorless model not found: {MODEL_PATH}. "
        "Run model/train_model.py first."
    )

model_data = joblib.load(MODEL_PATH)

print("Sensorless irrigation model loaded successfully.")

classifier = model_data["classifier"]
regressor = model_data["regressor"]

crop_encoder = model_data["crop_encoder"]
stage_encoder = model_data["stage_encoder"]


# ---------- HOME PAGE ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    farm = session.get("farm_details", {})
    return render_template("dashboard.html", farm=farm)


# ---------- FARM DETAILS ----------
@app.route("/farm-details", methods=["GET", "POST"])
def farm_details():

    if request.method == "POST":
        crop_type = request.form.get("crop_type", "").strip()
        farm_size = request.form.get("farm_size", "").strip()
        soil_type = request.form.get("soil_type", "").strip()
        growth_stage = request.form.get("growth_stage", "").strip()

        if not all([crop_type, farm_size, soil_type, growth_stage]):
            return render_template(
                "farm_details.html",
                error="Please fill in all farm details."
            )

        try:
            size = float(farm_size)

            if size <= 0:
                return render_template(
                    "farm_details.html",
                    error="Farm size must be greater than zero."
                )

        except ValueError:
            return render_template(
                "farm_details.html",
                error="Please enter a valid farm size."
            )

        session["farm_details"] = {
            "crop_type": crop_type,
            "farm_size": size,
            "soil_type": soil_type,
            "growth_stage": growth_stage
        }

        return redirect(url_for("dashboard"))

    return render_template("farm_details.html")


# ---------- PREDICTION PAGE ----------
@app.route("/prediction")
def prediction():
    return render_template("prediction.html", mode="sensorless")


# ---------- HISTORY PAGE ----------
@app.route("/history")
def history():
    return render_template("history.html")


# ---------- SENSORLESS PAGE ----------
@app.route("/sensorless")
def sensorless():
    return render_template("sensorless.html")


# ---------- VOICE ASSISTANT ----------
@app.route("/voice-assistant")
def voice_assistant():
    return render_template("voice_assistance.html")


# ---------- WEATHER PAGE ----------
@app.route("/weather")
def weather_page():
    return render_template("weather.html")


# ---------- AI PREDICTION API ----------
@app.route("/api/predict", methods=["POST"])
def predict():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "status": "error",
            "message": "No valid JSON data received."
        }), 400

    try:
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        rainfall = float(data["rainfall"])
        rain_probability = float(data["rain_probability"])

        crop = str(data["crop"]).strip()
        growth_stage = str(data["growth_stage"]).strip()

        # Supported options shown in the frontend
        allowed_crops = [
            "Rice", "Wheat", "Maize",
            "Tomato", "Cotton", "Chilli"
        ]

        allowed_stages = [
            "Seedling", "Vegetative",
            "Flowering", "Fruiting", "Maturity"
        ]

        # Validate crop
        if crop not in allowed_crops:
            return jsonify({
                "status": "error",
                "message": "Please select a valid crop."
            }), 400

        # Validate growth stage
        if growth_stage not in allowed_stages:
            return jsonify({
                "status": "error",
                "message": "Please select a valid growth stage."
            }), 400

        # Check whether the model was trained on this crop
        if crop not in crop_encoder.classes_:
            return jsonify({
                "status": "error",
                "message": (
                    f"{crop} is not supported by the trained model yet. "
                    "Training data for this crop is required."
                )
            }), 400

        # Check whether the model was trained on this growth stage
        if growth_stage not in stage_encoder.classes_:
            return jsonify({
                "status": "error",
                "message": (
                    f"{growth_stage} is not supported by the trained model yet. "
                    "Training data for this growth stage is required."
                )
            }), 400

        # Encode categorical values
        crop_value = crop_encoder.transform([crop])[0]
        stage_value = stage_encoder.transform([growth_stage])[0]

        # Sensorless model: no soil-moisture sensor input
        features = [[
            temperature,
            humidity,
            rainfall,
            rain_probability,
            crop_value,
            stage_value
        ]]

        irrigation_result = classifier.predict(features)[0]

        if irrigation_result == 1:
            irrigation = "Required"

            water_required = max(
                0,
                round(float(regressor.predict(features)[0]), 2)
            )

            # Example only: assumed pump flow rate is 30 litres/minute
            pump_flow_rate = 30

            pump_duration = round(
                water_required / pump_flow_rate, 2
            )

            recommendation = "Irrigation is recommended."

        else:
            irrigation = "Not Required"
            water_required = 0
            pump_duration = 0

            recommendation = "Irrigation is not required now."

        return jsonify({
            "status": "success",
            "irrigation": irrigation,
            "water_required": water_required,
            "pump_duration": pump_duration,
            "recommendation": recommendation
        })

    except KeyError as e:
        return jsonify({
            "status": "error",
            "message": f"Missing input field: {e}"
        }), 400

    except (ValueError, TypeError) as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid input value: {e}"
        }), 400

    except Exception:
        app.logger.exception("Prediction failed")

        return jsonify({
            "status": "error",
            "message": (
                "Prediction failed. Check the model and input fields."
            )
        }), 500


# ---------- TEST API ----------
@app.route("/api/test")
def test_api():
    return jsonify({
        "status": "success",
        "message": "Smart Irrigation AI backend is working!"
    })


# ---------- WEATHER API ----------
@app.route("/api/weather", methods=["GET"])
def weather():

    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")

    if not latitude or not longitude:
        return jsonify({
            "status": "error",
            "message": "Location is required."
        }), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)

        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90.")

        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180.")

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "rain,"
                "showers,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "hourly": "precipitation_probability",
            "forecast_days": 1,
            "timezone": "auto"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        weather_data = response.json()

        current = weather_data["current"]
        hourly = weather_data["hourly"]

        current_time = current["time"]
        hourly_times = hourly["time"]

        if current_time in hourly_times:
            index = hourly_times.index(current_time)
            rain_probability = (
                hourly["precipitation_probability"][index]
            )
        else:
            rain_probability = 0

        return jsonify({
            "status": "success",
            "temperature": current["temperature_2m"],
            "humidity": current["relative_humidity_2m"],
            "rainfall": current["precipitation"],
            "rain": current["rain"],
            "showers": current["showers"],
            "rain_probability": rain_probability,
            "wind_speed": current["wind_speed_10m"],
            "weather_code": current["weather_code"],
            "time": current["time"]
        })

    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

    except requests.exceptions.RequestException:
        app.logger.exception("Weather API request failed")

        return jsonify({
            "status": "error",
            "message": (
                "Could not retrieve weather data. Please try again."
            )
        }), 502

    except (KeyError, TypeError):
        app.logger.exception("Unexpected weather response")

        return jsonify({
            "status": "error",
            "message": "Unexpected weather data received."
        }), 502


# ---------- RUN APPLICATION ----------
if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )