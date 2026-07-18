document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("prediction-form");
    const button = document.querySelector(".btn-predict");

    form.addEventListener("submit", async function (e) {

        e.preventDefault();

        clearErrors();

        let valid = true;

        // Read Values
        const air = parseFloat(document.getElementById("air_temperature").value);
        const process = parseFloat(document.getElementById("process_temperature").value);
        const rpm = parseFloat(document.getElementById("rotational_speed").value);
        const torque = parseFloat(document.getElementById("torque").value);
        const wear = parseFloat(document.getElementById("tool_wear").value);

        // Validation
        if (isNaN(air) || air < 200 || air > 400) {
            showError("air_temperature", "Enter a value between 200 and 400 K");
            valid = false;
        }

        if (isNaN(process) || process < 200 || process > 400) {
            showError("process_temperature", "Enter a value between 200 and 400 K");
            valid = false;
        }

        if (isNaN(rpm) || rpm <= 0 || rpm > 10000) {
            showError("rotational_speed", "Enter a valid RPM");
            valid = false;
        }

        if (isNaN(torque) || torque < 0 || torque > 500) {
            showError("torque", "Enter a value between 0 and 500 Nm");
            valid = false;
        }

        if (isNaN(wear) || wear < 0 || wear > 1000) {
            showError("tool_wear", "Enter a value between 0 and 1000 min");
            valid = false;
        }

        if (!valid) return;

        // Disable button
        button.disabled = true;
        button.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Predicting...';

        try {

            const formData = new FormData(form);

            const response = await fetch("/predict", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            const result = data.Results[0];

            // Update Dashboard
            document.getElementById("health-status").innerText =
                result["Health Status"];

            document.getElementById("prediction-label").innerText =
                result["Prediction Label"];

            document.getElementById("failure-probability").innerText =
                (result["Failure Probability"] * 100).toFixed(2) + "%";

            document.getElementById("confidence").innerText =
                result["Confidence"];

            document.getElementById("model-used").innerText =
                data["Model Used"];

            document.getElementById("prediction-time").innerText =
                new Date().toLocaleTimeString();

            // Progress Bars
            document.getElementById("failure-bar").style.width =
                (result["Failure Probability"] * 100) + "%";

            document.getElementById("confidence-bar").style.width =
                parseFloat(result["Confidence"]) + "%";

            // Status Icon
            const icon = document.getElementById("status-icon");

            icon.className = "status-icon";

            if (result["Prediction Label"] === "Healthy") {

                icon.innerHTML =
                    '<i class="fas fa-check-circle"></i>';

            } else {

                icon.classList.add("danger");

                icon.innerHTML =
                    '<i class="fas fa-exclamation-triangle"></i>';

            }

        } catch (error) {

            console.error(error);
            alert("Prediction failed. Please try again.");

        } finally {

            button.disabled = false;
            button.innerHTML =
                '<i class="fas fa-bolt"></i> Predict Failure';

        }

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
const searchInput = document.getElementById("historySearch");

searchInput.addEventListener("keyup", function(){

    const value = this.value.toLowerCase();

    document.querySelectorAll(".history-row").forEach(row=>{

        row.style.display =
            row.innerText.toLowerCase().includes(value)
            ? ""
            : "none";

    });

});
const filter=document.getElementById("statusFilter");

filter.addEventListener("change",function(){

    const value=this.value;

    document.querySelectorAll(".history-row").forEach(row=>{

        if(value==="all"){

            row.style.display="";

            return;

        }

        row.style.display =
            row.innerText.includes(value)
            ? ""
            : "none";

    });

});