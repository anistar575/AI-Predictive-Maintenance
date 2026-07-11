document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("prediction-form");
    const button = document.querySelector(".btn-predict");

    form.addEventListener("submit", function (e) {

        clearErrors();

        let valid = true;

        // Read Values
        const air = parseFloat(document.getElementById("air_temperature").value);
        const process = parseFloat(document.getElementById("process_temperature").value);
        const rpm = parseFloat(document.getElementById("rotational_speed").value);
        const torque = parseFloat(document.getElementById("torque").value);
        const wear = parseFloat(document.getElementById("tool_wear").value);

        // Air Temperature
        if (isNaN(air) || air < 200 || air > 400) {
            showError("air_temperature", "Enter a value between 200 and 400 K");
            valid = false;
        }

        // Process Temperature
        if (isNaN(process) || process < 200 || process > 400) {
            showError("process_temperature", "Enter a value between 200 and 400 K");
            valid = false;
        }

        // RPM
        if (isNaN(rpm) || rpm <= 0 || rpm > 10000) {
            showError("rotational_speed", "Enter a valid RPM");
            valid = false;
        }

        // Torque
        if (isNaN(torque) || torque < 0 || torque > 500) {
            showError("torque", "Enter a value between 0 and 500 Nm");
            valid = false;
        }

        // Tool Wear
        if (isNaN(wear) || wear < 0 || wear > 1000) {
            showError("tool_wear", "Enter a value between 0 and 1000 min");
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
            return;
        }

        // Disable button while prediction runs
        button.disabled = true;
        button.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Predicting...';
    });

    function showError(id, message) {

        const input = document.getElementById(id);

        input.style.border = "2px solid red";

        const error = document.createElement("small");
        error.className = "error";
        error.style.color = "red";
        error.style.display = "block";
        error.style.marginTop = "5px";
        error.innerText = message;

        input.parentNode.appendChild(error);
    }

    function clearErrors() {

        document.querySelectorAll(".error").forEach(e => e.remove());

        document.querySelectorAll("input, select").forEach(input => {
            input.style.border = "1px solid #cfcfcf";
        });

    }

});
