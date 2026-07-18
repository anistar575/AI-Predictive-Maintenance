const search = document.getElementById("machineSearch");

search.addEventListener("keyup", function(){

    const value = this.value.toLowerCase();

    document.querySelectorAll(".machine-row").forEach(row=>{

        row.style.display =
            row.innerText.toLowerCase().includes(value)
            ? ""
            : "none";

    });

});