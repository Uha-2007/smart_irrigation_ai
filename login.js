function selectLanguage(language) {
    localStorage.setItem("language", language);
}

function login() {
    const mobile = document.getElementById("mobile").value;

    if (mobile.length !== 10) {
        alert("Please enter a valid mobile number.");
        return;
    }

    localStorage.setItem("loggedIn", "true");

    window.location.href = "/dashboard";
}