// Get hello message from backend
document.getElementById('backendBtn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/hello');
        const data = await response.json();
        displayResponse(data.message, 'response');
    } catch (error) {
        displayResponse('Error: ' + error.message, 'response');
    }
});

// Submit form data to backend
document.getElementById('dataForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('nameInput').value;
    
    try {
        const response = await fetch('/api/data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: name })
        });
        const data = await response.json();
        displayResponse(JSON.stringify(data, null, 2), 'formResponse');
        document.getElementById('nameInput').value = '';
    } catch (error) {
        displayResponse('Error: ' + error.message, 'formResponse');
    }
});

function displayResponse(message, elementId) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.classList.add('show');
}
