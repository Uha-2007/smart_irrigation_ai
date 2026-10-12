function loadDashboard() {

    const language =
        localStorage.getItem("language") || "English";

    const crop =
        localStorage.getItem("crop") || "Not selected";

    const langElement =
        document.getElementById("language");

    const cropElement =
        document.getElementById("crop");

    if (langElement)
        langElement.textContent = language;

    if (cropElement)
        cropElement.textContent = crop;
}

loadDashboard();