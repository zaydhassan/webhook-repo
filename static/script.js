async function fetchEvents() {
    try {
        const response = await fetch("/events");
        const data = await response.json();

        const list = document.getElementById("events");
        list.innerHTML = "";

        data.forEach(item => {
            const li = document.createElement("li");
            li.textContent = item;
            list.appendChild(li);
        });
    } catch (error) {
        console.error("Error fetching events");
    }
}

fetchEvents();
setInterval(fetchEvents, 15000);