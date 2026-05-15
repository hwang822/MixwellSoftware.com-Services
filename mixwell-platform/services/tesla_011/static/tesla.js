async function loadStatus() {
    const res = await fetch("service/tesla/get_data");
    const data = await res.json();

    document.getElementById("name").innerText = data.name;
    document.getElementById("battery").innerText = data.battery;
    document.getElementById("range").innerText = data.range;
    document.getElementById("charging").innerText = data.charging;
    document.getElementById("locked").innerText = data.locked;
    document.getElementById("inside_temp").innerText = data.inside_temp;
    document.getElementById("outside_temp").innerText = data.outside_temp;
}

loadStatus();