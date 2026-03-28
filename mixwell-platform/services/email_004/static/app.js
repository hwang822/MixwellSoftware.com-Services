let emails = [];
let selected = null;

async function loadEmails() {
    const res = await fetch("/api/emails");
    emails = await res.json();

    const list = document.getElementById("emailList");
    list.innerHTML = "";

    emails.forEach((m, i) => {
        const div = document.createElement("div");
        div.innerHTML = `<b>${m.from}</b><br>${m.subject}`;
        div.onclick = () => showEmail(i);
        list.appendChild(div);
    });
}

function showEmail(i) {
    selected = emails[i];

    document.getElementById("subject").innerText = selected.subject;
    document.getElementById("from").innerText = selected.from;
    document.getElementById("body").innerText = selected.body;
}

function openCompose() {
    document.getElementById("composeModal").style.display = "block";
}

function closeCompose() {
    document.getElementById("composeModal").style.display = "none";
}

async function sendEmail() {
    const to = document.getElementById("to").value;
    const subject = document.getElementById("subjectInput").value;
    const body = document.getElementById("bodyInput").value;

    await fetch("/api/send", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({to, subject, body})
    });

    alert("Sent!");
    closeCompose();
}

function reply() {
    if (!selected) return;

    openCompose();
    document.getElementById("to").value = selected.from;
    document.getElementById("subjectInput").value = "Re: " + selected.subject;
}

function forward() {
    if (!selected) return;

    openCompose();
    document.getElementById("subjectInput").value = "Fwd: " + selected.subject;
    document.getElementById("bodyInput").value = selected.body;
}

async function deleteEmail() {
    if (!selected) return;

    const confirmDelete = confirm("Delete this email?");
    if (!confirmDelete) return;

    await fetch("/api/delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ id: selected.id })
    });

    alert("Deleted");

    // Refresh inbox
    loadEmails();

    // Clear right panel
    document.getElementById("subject").innerText = "";
    document.getElementById("from").innerText = "";
    document.getElementById("body").innerText = "";
}

loadEmails();