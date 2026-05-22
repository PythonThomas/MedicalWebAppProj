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
if (document.getElementById('backendBtn')) {
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
}

/**
 * Form Submission Handler
 * Captures form input values and sends them to the backend as JSON
 * Displays the backend response in the matching response box
 *
 * This reusable helper is used by multiple forms:
 * - dataForm on index.html
 * - certificateForm on reqcrt.html
 * - contactForm on contact.html
 */
async function submitForm(formId, responseId, buildPayload) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = buildPayload();
        if (!payload) {
            displayResponse('Unable to read form values. Please refresh the page and try again.', responseId);
            return;
        }

        try {
            const response = await fetch('/api/data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            displayResponse(JSON.stringify(data, null, 2), responseId);
            form.reset();
            if (formId === 'certificateForm') {
                resetFormSteps(formId);
            }
        } catch (error) {
            displayResponse('Error: ' + error.message, responseId);
        }
    });
}

// Set up the index page form: sends a simple name payload to /api/data
submitForm('dataForm', 'formResponse', () => {
    const nameInput = document.getElementById('nameInput');
    return nameInput ? {
        formType: 'general',
        name: nameInput.value
    } : null;
});

// Set up the certificate request page form: sends multi-step certificate fields to the backend
submitForm('certificateForm', 'certResponse', () => {
    const reasonInput = document.getElementById('certificateReasonFor');
    const otherReasonInput = document.getElementById('otherReason');
    const surName = document.getElementById('surName');
    const givenName = document.getElementById('givenName');
    const dateOfBirth = document.getElementById('dateOfBirth');
    const certEmail = document.getElementById('email');
    const absenceStartDate = document.getElementById('absenceStartDate');
    const absenceEndDate = document.getElementById('absenceEndDate');
    const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked');

    if (!reasonInput || !surName || !givenName || !dateOfBirth || !certEmail || !absenceStartDate || !absenceEndDate || !paymentMethod) return null;

    return {
        formType: 'certificateRequest',
        reasonFor: reasonInput.value,
        otherReason: reasonInput.value === 'other' ? otherReasonInput?.value.trim() || '' : '',
        surname: surName.value.trim(),
        givenName: givenName.value.trim(),
        dateOfBirth: dateOfBirth.value,
        email: certEmail.value.trim(),
        absenceStartDate: absenceStartDate.value,
        absenceEndDate: absenceEndDate.value,
        paymentMethod: paymentMethod.value
    };
});

// Set up the contact page form: sends name, email, and message to the backend
submitForm('contactForm', 'contactResponse', () => {
    const contactName = document.getElementById('contactName');
    const contactEmail = document.getElementById('contactEmail');
    const contactMessage = document.getElementById('contactMessage');
    if (!contactName || !contactEmail || !contactMessage) return null;
    return {
        formType: 'contactMessage',
        name: contactName.value,
        email: contactEmail.value,
        message: contactMessage.value
    };
});

function setupMultiStepForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    const steps = Array.from(form.querySelectorAll('.form-step'));
    if (!steps.length) return;

    let currentStep = 0;

    const stepCounter = form.querySelector('#stepCounter');

    const showStep = (index) => {
        if (index < 0 || index >= steps.length) return;
        steps.forEach((step, stepIndex) => {
            step.classList.toggle('active', stepIndex === index);
        });
        currentStep = index;
        if (stepCounter) {
            stepCounter.textContent = `Step ${currentStep + 1} / ${steps.length}`;
        }
    };

    form.querySelectorAll('.next-step').forEach((button) => {
        button.addEventListener('click', () => showStep(Math.min(currentStep + 1, steps.length - 1)));
    });

    form.querySelectorAll('.previous-step').forEach((button) => {
        button.addEventListener('click', () => showStep(Math.max(currentStep - 1, 0)));
    });

    const reasonSelect = form.querySelector('#certificateReasonFor');
    const otherReasonField = form.querySelector('.other-reason-field');

    if (reasonSelect && otherReasonField) {
        const toggleOtherReason = () => {
            const displayed = reasonSelect.value === 'other';
            otherReasonField.style.display = displayed ? 'block' : 'none';
            const otherInput = otherReasonField.querySelector('#otherReason');
            if (otherInput) {
                otherInput.required = displayed;
            }
        };

        reasonSelect.addEventListener('change', toggleOtherReason);
        toggleOtherReason();
    }

    showStep(0);
}

function resetFormSteps(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    const steps = Array.from(form.querySelectorAll('.form-step'));
    const stepCounter = form.querySelector('#stepCounter');
    steps.forEach((step, index) => {
        step.classList.toggle('active', index === 0);
    });

    if (stepCounter) {
        stepCounter.textContent = `Step 1 / ${steps.length}`;
    }

    const reasonSelect = form.querySelector('#certificateReasonFor');
    if (reasonSelect) {
        reasonSelect.dispatchEvent(new Event('change'));
    }
}

// Initialize certificate request multi-step behavior
setupMultiStepForm('certificateForm');

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
    if (!element) return;
    // Set the message text
    element.textContent = message;
    // Add the 'show' class to make the response box visible
    element.classList.add('show');
}
