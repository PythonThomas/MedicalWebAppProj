/**
 * JeffCare Frontend Script
 * Handles navigation between pages and API communication with the backend
 */

// ============================================
// NAVIGATION BUTTON HANDLERS
// ============================================
// These buttons navigate users between different pages of the application

const homeBtn = document.getElementById('homeBtn');
const reqcrtBtn = document.getElementById('reqcrtBtn');
const contactBtn = document.getElementById('contactBtn');

// Home button - returns to the main index page
if (homeBtn) {
    homeBtn.addEventListener('click', () => {
        window.location.href = '/';
    });
}

// Request Certificate button - navigates to the certificate request form
if (reqcrtBtn) {
    reqcrtBtn.addEventListener('click', () => {
        window.location.href = '/request-certificate';
    });
}

// Contact Us button - navigates to the contact form
if (contactBtn) {
    contactBtn.addEventListener('click', () => {
        window.location.href = '/contact';
    });
}

// ============================================
// BACKEND API COMMUNICATION
// ============================================
// These handlers manage communication with the Flask backend

/**
 * Backend Message Button Handler
 * Fetches a greeting message from the backend API when clicked
 * Displays the response in the response box on the page
 */
document.getElementById('backendBtn').addEventListener('click', async () => {
    try {
        // Make a GET request to /api/hello endpoint
        const response = await fetch('/api/hello');
        const data = await response.json();
        // Display the message returned from the backend
        displayResponse(data.message, 'response');
    } catch (error) {
        // Display error message if the request fails
        displayResponse('Error: ' + error.message, 'response');
    }
});

/**
 * Form Submission Handler
 * Captures form data and sends it to the backend as JSON
 * Displays the server's response to confirm data was received
 */
document.getElementById('dataForm').addEventListener('submit', async (e) => {
    // Prevent the default form submission behavior
    e.preventDefault();
    // Get the user's name from the input field
    const name = document.getElementById('nameInput').value;
    
    try {
        // Send POST request with the user's name
        const response = await fetch('/api/data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: name })
        });
        // Parse the JSON response from the backend
        const data = await response.json();
        // Format and display the response
        displayResponse(JSON.stringify(data, null, 2), 'formResponse');
        // Clear the input field after successful submission
        document.getElementById('nameInput').value = '';
    } catch (error) {
        // Display error message if the request fails
        displayResponse('Error: ' + error.message, 'formResponse');
    }
});

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * displayResponse - Shows API response messages to the user
 * @param {string} message - The message or data to display
 * @param {string} elementId - The HTML element ID where the message should appear
 * Displays the message in a styled response box and makes it visible
 */
function displayResponse(message, elementId) {
    // Get the element where the response should be displayed
    const element = document.getElementById(elementId);
    // Set the message text
    element.textContent = message;
    // Add the 'show' class to make the response box visible
    element.classList.add('show');
}
