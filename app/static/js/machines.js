const search = document.getElementById("machineSearch");
const statusFilter = document.getElementById("statusFilter");

function filterMachines() {
    const searchValue = search ? search.value.toLowerCase() : "";
    const filterValue = statusFilter ? statusFilter.value : "all";

    document.querySelectorAll(".machine-row").forEach(row => {
        const textMatches = row.innerText.toLowerCase().includes(searchValue);
        
        let statusMatches = false;
        if (filterValue === "all") {
            statusMatches = true;
        } else {
            const badge = row.querySelector(".status-badge");
            if (badge) {
                // E.g., checks if "🟢 Healthy" contains "Healthy"
                statusMatches = badge.innerText.toLowerCase().includes(filterValue.toLowerCase());
            }
        }

        if (textMatches && statusMatches) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

if (search) {
    search.addEventListener("keyup", filterMachines);
}
if (statusFilter) {
    statusFilter.addEventListener("change", filterMachines);
}