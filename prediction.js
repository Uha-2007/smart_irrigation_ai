async function predict() {

    const crop = document.getElementById("crop").value;
    const stage = document.getElementById("stage").value;
    const mode = document.getElementById("mode").value;
    const soil = document.getElementById("soilMoisture").value;

    if (crop === "Select Crop" || stage === "Select Stage") {
        alert("Please select crop and growth stage.");
        return;
    }

    if (mode === "sensor" && soil === "") {
        alert("Please enter soil moisture.");
        return;
    }

    // Get location saved from Farm Details
    const city = localStorage.getItem("location");

    if (!city) {
        alert("Please enter your farm location first.");
        return;
    }

    try {

        // Get weather automatically
        const weatherResponse =
            await fetch(`/api/weather?city=${city}`);

        const weather = await weatherResponse.json();

        if (weather.status !== "success") {
            alert("Weather data could not be loaded.");
            return;
        }

        // Send data to AI model
        const response = await fetch("/api/predict", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                temperature: weather.temperature,
                humidity: weather.humidity,
                rainfall: weather.rainfall,

                // Temporary value.
                // Forecast probability will be added later.
                rain_probability: 0,

                soil_moisture:
                    mode === "sensor"
                    ? Number(soil)
                    : null,

                crop: crop,
                growth_stage: stage
            })
        });

        const result = await response.json();

        if (result.status === "success") {

            document.getElementById("irrigation")
                .textContent = result.irrigation;

            document.getElementById("recommendation")
                .textContent = result.recommendation;

            document.getElementById("water")
                .textContent =
                result.water_required + " L";

            document.getElementById("pump")
                .textContent =
                result.pump_duration + " minutes";

        } else {

            alert(result.message);
        }

    } catch (error) {

        alert("Something went wrong. Please check the server.");

        console.error(error);
    }
}