document.addEventListener("DOMContentLoaded", () => {
    // ----------------- DOM ELEMENTS -----------------
    const filterMachine = document.getElementById("filterMachine");
    const filterDepartment = document.getElementById("filterDepartment");
    const filterStartDate = document.getElementById("filterStartDate");
    const filterEndDate = document.getElementById("filterEndDate");
    const filterStatus = document.getElementById("filterStatus");
    const btnResetFilters = document.getElementById("btnResetFilters");

    // ----------------- CHART INSTANCES -----------------
    let healthTrendChart = null;
    let volumeChart = null;
    let deptHealthChart = null;
    let utilizationChart = null;

    // ----------------- TELEMETRY STATS AVERAGES -----------------
    function updateTelemetryAverages(filteredData) {
        const healthyRuns = filteredData.filter(d => d.prediction === "Healthy");
        const failedRuns = filteredData.filter(d => d.prediction === "Failure");

        const calcAvg = (arr, key) => {
            if (arr.length === 0) return "--";
            const sum = arr.reduce((acc, curr) => acc + curr[key], 0);
            return (sum / arr.length).toFixed(1);
        };

        document.getElementById("avgAirHealthy").innerText = calcAvg(healthyRuns, "air_temp") + " K";
        document.getElementById("avgAirFailed").innerText = calcAvg(failedRuns, "air_temp") + " K";

        document.getElementById("avgProcessHealthy").innerText = calcAvg(healthyRuns, "process_temp") + " K";
        document.getElementById("avgProcessFailed").innerText = calcAvg(failedRuns, "process_temp") + " K";

        document.getElementById("avgSpeedHealthy").innerText = calcAvg(healthyRuns, "rotational_speed") + " RPM";
        document.getElementById("avgSpeedFailed").innerText = calcAvg(failedRuns, "rotational_speed") + " RPM";

        document.getElementById("avgTorqueHealthy").innerText = calcAvg(healthyRuns, "torque") + " Nm";
        document.getElementById("avgTorqueFailed").innerText = calcAvg(failedRuns, "torque") + " Nm";

        document.getElementById("avgWearHealthy").innerText = calcAvg(healthyRuns, "tool_wear") + " min";
        document.getElementById("avgWearFailed").innerText = calcAvg(failedRuns, "tool_wear") + " min";
    }

    // ----------------- TOP RISK MACHINES TABLE -----------------
    function updateTopRiskMachines(filteredData) {
        const tableBody = document.getElementById("topRiskTableBody");
        tableBody.innerHTML = "";

        // Group predictions by machine
        const machinesMap = {};
        filteredData.forEach(d => {
            if (!machinesMap[d.machine_code]) {
                machinesMap[d.machine_code] = {
                    code: d.machine_code,
                    name: d.machine_name,
                    probs: []
                };
            }
            machinesMap[d.machine_code].probs.push(d.failure_probability);
        });

        // Calculate average failure probability
        const machinesList = Object.values(machinesMap).map(m => {
            const avg = m.probs.reduce((a, b) => a + b, 0) / m.probs.length;
            return {
                code: m.code,
                name: m.name,
                avgProb: avg
            };
        });

        // Sort by probability descending
        machinesList.sort((a, b) => b.avgProb - a.avgProb);

        // Take top 5
        const top5 = machinesList.slice(0, 5);

        if (top5.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">No risk profiles found</td></tr>`;
            return;
        }

        top5.forEach(m => {
            const pct = (m.avgProb * 100).toFixed(1);
            let badgeClass = "low";
            let category = "Low Risk";

            if (m.avgProb > 0.70) {
                badgeClass = "high";
                category = "Critical Risk";
            } else if (m.avgProb > 0.30) {
                badgeClass = "medium";
                category = "Moderate Risk";
            }

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><code>${m.code}</code></td>
                <td><a href="/machine/${m.code}" style="color: var(--primary-blue); text-decoration: none; font-weight: 500;">${m.name}</a></td>
                <td style="font-weight: 700;">${pct}%</td>
                <td><span class="risk-badge ${badgeClass}">${category}</span></td>
            `;
            tableBody.appendChild(tr);
        });
    }

    // ----------------- CHARTS RENDERING -----------------
    function drawCharts(filteredData) {
        // Group predictions by date (YYYY-MM-DD)
        const datesMap = {};
        filteredData.forEach(d => {
            const date = d.prediction_time.substring(0, 10);
            if (!datesMap[date]) {
                datesMap[date] = { healthy: 0, warning: 0, critical: 0, total: 0 };
            }
            datesMap[date].total++;
            if (d.health_status.includes("Healthy")) datesMap[date].healthy++;
            else if (d.health_status.includes("Warning")) datesMap[date].warning++;
            else if (d.health_status.includes("Critical")) datesMap[date].critical++;
        });

        const sortedDates = Object.keys(datesMap).sort();
        const healthyTrendData = [];
        const warningTrendData = [];
        const criticalTrendData = [];
        const volumeTrendData = [];

        sortedDates.forEach(d => {
            const counts = datesMap[d];
            healthyTrendData.push(counts.healthy);
            warningTrendData.push(counts.warning);
            criticalTrendData.push(counts.critical);
            volumeTrendData.push(counts.total);
        });

        // 1. Health Trend Chart (Line)
        if (healthTrendChart) healthTrendChart.destroy();
        const ctxTrend = document.getElementById("healthTrendChart").getContext("2d");
        healthTrendChart = new Chart(ctxTrend, {
            type: "line",
            data: {
                labels: sortedDates,
                datasets: [
                    {
                        label: "Healthy",
                        data: healthyTrendData,
                        borderColor: "#10b981",
                        backgroundColor: "rgba(16, 185, 129, 0.1)",
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: "Warning",
                        data: warningTrendData,
                        borderColor: "#f59e0b",
                        backgroundColor: "rgba(245, 158, 11, 0.1)",
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: "Critical",
                        data: criticalTrendData,
                        borderColor: "#ef4444",
                        backgroundColor: "rgba(239, 68, 68, 0.1)",
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: "#94a3b8", font: { family: "Outfit" } } }
                },
                scales: {
                    x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8", font: { family: "Outfit" }, stepSize: 1 } }
                }
            }
        });

        // 2. Predictions Volume Chart (Bar)
        if (volumeChart) volumeChart.destroy();
        const ctxVol = document.getElementById("predictionsVolumeChart").getContext("2d");
        volumeChart = new Chart(ctxVol, {
            type: "bar",
            data: {
                labels: sortedDates,
                datasets: [{
                    label: "Diagnostic Checks",
                    data: volumeTrendData,
                    backgroundColor: "#3b82f6",
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { grid: { display: false }, ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8", font: { family: "Outfit" }, stepSize: 1 } }
                }
            }
        });

        // 3. Department Health Chart (Stacked Bar)
        const deptsMap = {};
        filteredData.forEach(d => {
            const dept = d.department || "Unassigned";
            if (!deptsMap[dept]) {
                deptsMap[dept] = { healthy: 0, warning: 0, critical: 0 };
            }
            if (d.health_status.includes("Healthy")) deptsMap[dept].healthy++;
            else if (d.health_status.includes("Warning")) deptsMap[dept].warning++;
            else if (d.health_status.includes("Critical")) deptsMap[dept].critical++;
        });

        const deptsList = Object.keys(deptsMap);
        const deptHealthy = [];
        const deptWarning = [];
        const deptCritical = [];

        deptsList.forEach(dept => {
            deptHealthy.push(deptsMap[dept].healthy);
            deptWarning.push(deptsMap[dept].warning);
            deptCritical.push(deptsMap[dept].critical);
        });

        if (deptHealthChart) deptHealthChart.destroy();
        const ctxDept = document.getElementById("deptHealthChart").getContext("2d");
        deptHealthChart = new Chart(ctxDept, {
            type: "bar",
            data: {
                labels: deptsList,
                datasets: [
                    { label: "Healthy", data: deptHealthy, backgroundColor: "#10b981" },
                    { label: "Warning", data: deptWarning, backgroundColor: "#f59e0b" },
                    { label: "Critical", data: deptCritical, backgroundColor: "#ef4444" }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: "#94a3b8", font: { family: "Outfit" } } }
                },
                scales: {
                    x: { stacked: true, grid: { display: false }, ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { stacked: true, grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8", font: { family: "Outfit" } } }
                }
            }
        });

        // 4. Machine Utilization (Horizontal Bar)
        // Group predictions by machine code and find max tool wear
        const usageMap = {};
        filteredData.forEach(d => {
            if (!usageMap[d.machine_code]) {
                usageMap[d.machine_code] = 0;
            }
            if (d.tool_wear > usageMap[d.machine_code]) {
                usageMap[d.machine_code] = d.tool_wear;
            }
        });

        const sortedUsageMachines = Object.keys(usageMap).sort((a, b) => usageMap[b] - usageMap[a]);
        const usageValues = sortedUsageMachines.map(m => usageMap[m]);

        if (utilizationChart) utilizationChart.destroy();
        const ctxUtil = document.getElementById("utilizationChart").getContext("2d");
        utilizationChart = new Chart(ctxUtil, {
            type: "bar",
            data: {
                labels: sortedUsageMachines,
                datasets: [{
                    label: "Peak Tool Wear Operating Log (min)",
                    data: usageValues,
                    backgroundColor: "rgba(59, 130, 246, 0.7)",
                    borderColor: "#3b82f6",
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { grid: { display: false }, ticks: { color: "#94a3b8", font: { family: "Outfit" } } }
                }
            }
        });
    }

    // ----------------- UPDATE CONTROL CENTER -----------------
    function updateDashboard() {
        const machine = filterMachine.value;
        const dept = filterDepartment.value;
        const start = filterStartDate.value;
        const end = filterEndDate.value;
        const status = filterStatus.value;

        // Apply filters
        const filtered = predictionsDataset.filter(item => {
            if (machine !== "all" && item.machine_code !== machine) return false;
            if (dept !== "all" && item.department !== dept) return false;
            if (status !== "all" && !item.health_status.toLowerCase().includes(status.toLowerCase())) return false;

            if (start || end) {
                const dateStr = item.prediction_time.substring(0, 10);
                if (start && dateStr < start) return false;
                if (end && dateStr > end) return false;
            }
            return true;
        });

        // Compute KPIs
        const totalRuns = filtered.length;
        document.getElementById("kpiTotalRuns").innerText = totalRuns;

        let healthyCount = 0;
        let maxWear = 0;
        let sumFailureProb = 0;

        filtered.forEach(item => {
            if (item.prediction === "Healthy") healthyCount++;
            if (item.tool_wear > maxWear) maxWear = item.tool_wear;
            sumFailureProb += item.failure_probability;
        });

        const reliability = totalRuns > 0 ? ((healthyCount / totalRuns) * 100).toFixed(1) + "%" : "100.0%";
        const avgFailure = totalRuns > 0 ? ((sumFailureProb / totalRuns) * 100).toFixed(1) + "%" : "0.0%";

        document.getElementById("kpiReliability").innerText = reliability;
        document.getElementById("kpiMaxWear").innerText = maxWear + " min";
        document.getElementById("kpiAvgFailure").innerText = avgFailure;

        // Recalculate Averages table
        updateTelemetryAverages(filtered);

        // Recalculate Top Risk Machines
        updateTopRiskMachines(filtered);

        // Redraw Charts
        drawCharts(filtered);
    }

    // ----------------- ATTACH EVENTS -----------------
    filterMachine.addEventListener("change", updateDashboard);
    filterDepartment.addEventListener("change", updateDashboard);
    filterStartDate.addEventListener("change", updateDashboard);
    filterEndDate.addEventListener("change", updateDashboard);
    filterStatus.addEventListener("change", updateDashboard);

    btnResetFilters.addEventListener("click", () => {
        filterMachine.value = "all";
        filterDepartment.value = "all";
        filterStartDate.value = "";
        filterEndDate.value = "";
        filterStatus.value = "all";
        updateDashboard();
    });

    // ----------------- INITIAL EXECUTION -----------------
    updateDashboard();
});
