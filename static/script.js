document.getElementById("astrology-form").addEventListener("submit", function(event) {
    event.preventDefault();

    // Get user input
    const birthdate = document.getElementById("birthdate").value;
    const birthtime = document.getElementById("birthtime").value;
    const birthplace = document.getElementById("birthplace").value;
    const interests = Array.from(document.getElementById("interests").selectedOptions).map(option => option.value);

    // Validate user input
    if (!birthdate || !birthtime || !birthplace || interests.length === 0) {
        alert("Please fill out all fields.");
        return;
    }

    // Send a request to the server
    fetch('/astrology', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            birthdate: birthdate,
            birthtime: birthtime,
            birthplace: birthplace,
            interests: interests
        })
    })
    .then(response => response.json())
    .then(recommendedLocations => {
        // Display recommended locations
        displayRecommendedLocations(recommendedLocations);
    })
    .catch(error => console.error('Error:', error));
});

function displayRecommendedLocations(recommendedLocations) {
    const resultsContainer = document.getElementById("results");
    if (!resultsContainer) {
        const newResultsContainer = document.createElement("div");
        newResultsContainer.id = "results";
        document.body.appendChild(newResultsContainer);
    }

    let resultsHtml = "<h2>Recommended Locations:</h2>";
    recommendedLocations.forEach(location => {
        resultsHtml += `<p><strong>${location.location}</strong>: ${location.reason}</p>`;
    });

    document.getElementById("results").innerHTML = resultsHtml;
}
