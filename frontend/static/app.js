const form = document.getElementById("test-form");
const button = document.getElementById("run-test");
const statusElement = document.getElementById("status");
const resultElement = document.getElementById("result");


form.addEventListener("submit", async function (event) {

    event.preventDefault();

    const applicationUrl =
        document.getElementById("application-url").value;

    const instructions =
        document.getElementById("instructions").value;

    button.disabled = true;

    statusElement.textContent = "Running test...";
    resultElement.textContent = "InfraGuardian is testing the application...";

    try {

        const response = await fetch(
            `${API_URL}/api/test`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    application_url: applicationUrl,
                    instructions: instructions
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Test request failed."
            );
        }

        statusElement.textContent = "Test completed.";

        resultElement.textContent =
            JSON.stringify(data, null, 2);

    } catch (error) {

        statusElement.textContent = "Test failed.";

        resultElement.textContent =
            error.message;

    } finally {

        button.disabled = false;
    }
});