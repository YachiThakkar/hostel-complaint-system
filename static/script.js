// Confirm before deleting complaint
function confirmDelete() {
    return confirm("Are you sure you want to delete this complaint?");
}

// Confirm before updating status
function confirmUpdate() {
    return confirm("Are you sure you want to update the status?");
}

// Color code status text
document.addEventListener("DOMContentLoaded", function() {
    let statuses = document.querySelectorAll(".status");

    statuses.forEach(function(status) {
        let text = status.innerText.trim();

        if (text === "Pending") {
            status.style.color = "orange";
            status.style.fontWeight = "bold";
        } 
        else if (text === "In-Progress") {
            status.style.color = "blue";
            status.style.fontWeight = "bold";
        } 
        else if (text === "Resolved") {
            status.style.color = "green";
            status.style.fontWeight = "bold";
        }
    });
});

// Show success message after complaint submission
function showSuccess() {
    alert("Complaint submitted successfully!");
}

// Character counter for description
document.addEventListener("DOMContentLoaded", function () {

    let textarea = document.querySelector("textarea");
    if (textarea) {

        let counter = document.createElement("small");
        counter.style.display = "block";
        counter.style.marginTop = "5px";
        textarea.parentNode.insertBefore(counter, textarea.nextSibling);

        textarea.addEventListener("input", function () {
            counter.innerText = "Characters: " + textarea.value.length;
        });
    }
});

function validateLogin() {

    let email = document.querySelector("input[name='email']").value;
    let password = document.querySelector("input[name='password']").value;

    if (email === "" || password === "") {
        alert("Please fill all fields!");
        return false;
    }

    return true;
}