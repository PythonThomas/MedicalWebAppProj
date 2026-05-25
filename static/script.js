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

// Landing page hero CTA and footer CTA — both navigate to the certificate request form
const heroCta = document.getElementById('heroCta');
const ctaBtn = document.getElementById('ctaBtn');

if (heroCta) {
    heroCta.addEventListener('click', () => {
        window.location.href = '/request-certificate';
    });
}

if (ctaBtn) {
    ctaBtn.addEventListener('click', () => {
        window.location.href = '/request-certificate';
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
    const form = document.getElementById('certificateForm');

    if (!reasonInput || !surName || !givenName || !dateOfBirth || !certEmail || !absenceStartDate || !absenceEndDate) return null;

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
        paypalOrderId: form ? (form.dataset.paypalOrderId || '') : '',
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

/**
 * validateStep - Checks that all required fields in the current step are filled.
 * Shows an inline .step-error message inside the step if validation fails.
 * @param {HTMLElement} form - The form element containing the steps
 * @param {number} stepIndex - Zero-based index of the step to validate
 * @returns {boolean} true if the step is valid, false otherwise
 *
 * Step 0: certificateReasonFor must have a non-empty value; if "other", otherReason must be filled.
 * Step 1: surName, givenName, dateOfBirth, and email must all be non-empty.
 * Step 2: absenceStartDate and absenceEndDate must both be set, and end >= start.
 * Step 3 (payment): no required-field validation; always returns true.
 */
function validateStep(form, stepIndex) {
    const steps = Array.from(form.querySelectorAll('.form-step'));
    const step = steps[stepIndex];
    if (!step) return true;

    const existingError = step.querySelector('.step-error');
    if (existingError) existingError.remove();

    let errorMessage = null;

    if (stepIndex === 0) {
        const reason = form.querySelector('#certificateReasonFor');
        if (!reason || !reason.value) {
            errorMessage = 'Please select a reason for absence before continuing.';
        } else if (reason.value === 'other') {
            const otherReason = form.querySelector('#otherReason');
            if (!otherReason || !otherReason.value.trim()) {
                errorMessage = 'Please specify your reason for absence.';
            }
        }
    } else if (stepIndex === 1) {
        const surName = form.querySelector('#surName');
        const givenName = form.querySelector('#givenName');
        const dateOfBirth = form.querySelector('#dateOfBirth');
        const email = form.querySelector('#email');
        if (!surName?.value.trim()) {
            errorMessage = 'Please enter your surname.';
        } else if (!givenName?.value.trim()) {
            errorMessage = 'Please enter your given name.';
        } else if (!dateOfBirth?.value) {
            errorMessage = 'Please enter your date of birth.';
        } else if (!email?.value.trim()) {
            errorMessage = 'Please enter your email address.';
        }
    } else if (stepIndex === 2) {
        const startDate = form.querySelector('#absenceStartDate');
        const endDate = form.querySelector('#absenceEndDate');
        if (!startDate?.value) {
            errorMessage = 'Please enter the start date of your absence.';
        } else if (!endDate?.value) {
            errorMessage = 'Please enter the end date of your absence.';
        } else if (endDate.value < startDate.value) {
            errorMessage = 'The end date must be on or after the start date.';
        }
    }

    if (errorMessage) {
        const errorEl = document.createElement('p');
        errorEl.className = 'step-error';
        errorEl.textContent = errorMessage;
        const stepButtons = step.querySelector('.step-buttons');
        step.insertBefore(errorEl, stepButtons);
        return false;
    }

    return true;
}

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
        if (formId === 'certificateForm' && index === steps.length - 1) {
            initPayPalStep(form);
        }
    };

    form.querySelectorAll('.next-step').forEach((button) => {
        button.addEventListener('click', () => {
            if (validateStep(form, currentStep)) {
                showStep(Math.min(currentStep + 1, steps.length - 1));
            }
        });
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

    // Reset PayPal state so buttons re-render cleanly on the next visit to step 4
    const paypalContainer = document.getElementById('paypal-button-container');
    if (paypalContainer) {
        paypalContainer.innerHTML = '';
        delete paypalContainer.dataset.initialized;
    }
    const paymentStatus = document.getElementById('payment-status');
    if (paymentStatus) {
        paymentStatus.style.display = 'none';
        paymentStatus.textContent = '';
    }
    delete form.dataset.paypalOrderId;
}

// ============================================
// PAYPAL INTEGRATION
// ============================================

/**
 * initPayPalStep - Lazy-loads the PayPal JS SDK when the user reaches the
 * payment step, then calls renderPayPalButtons once the SDK is ready.
 * Reads the PayPal client ID from data-client-id on #paypal-button-container,
 * which is populated by Jinja2 from the PAYPAL_CLIENT_ID environment variable.
 * @param {HTMLElement} form - The certificate request form element
 */
function initPayPalStep(form) {
    const container = document.getElementById('paypal-button-container');
    if (!container || container.dataset.initialized) return;

    const clientId = container.dataset.clientId;
    if (!clientId) {
        container.textContent = 'PayPal is not configured. Please contact support.';
        return;
    }

    if (window.paypal) {
        renderPayPalButtons(form);
        return;
    }

    const script = document.createElement('script');
    script.src = `https://www.paypal.com/sdk/js?client-id=${encodeURIComponent(clientId)}&currency=AUD`;
    script.onload = () => renderPayPalButtons(form);
    script.onerror = () => {
        container.textContent = 'Failed to load PayPal. Please check your connection and try again.';
    };
    document.head.appendChild(script);
}

/**
 * renderPayPalButtons - Renders the PayPal Smart Payment Buttons into
 * #paypal-button-container. On createOrder, calls the backend to create a
 * PayPal order for 12.99 AUD. On onApprove, calls the backend to capture
 * the payment, then stores the order ID on the form and triggers submission.
 * @param {HTMLElement} form - The certificate request form element
 */
function renderPayPalButtons(form) {
    const container = document.getElementById('paypal-button-container');
    if (!container || container.dataset.initialized) return;
    container.dataset.initialized = 'true';

    paypal.Buttons({
        style: { layout: 'vertical', color: 'blue', shape: 'rect', label: 'pay' },

        createOrder: async () => {
            const res = await fetch('/api/paypal/create-order', { method: 'POST' });
            const data = await res.json();
            if (!data.id) throw new Error(data.message || 'Could not create PayPal order.');
            return data.id;
        },

        onApprove: async (approvalData) => {
            showPaymentStatus('Processing payment…', 'pending');
            try {
                const res = await fetch('/api/paypal/capture-order', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ orderID: approvalData.orderID }),
                });
                const result = await res.json();
                if (result.status === 'success') {
                    showPaymentStatus('Payment successful — submitting your request…', 'success');
                    form.dataset.paypalOrderId = approvalData.orderID;
                    form.requestSubmit();
                } else {
                    showPaymentStatus(result.message || 'Payment capture failed. Please try again.', 'error');
                }
            } catch (err) {
                showPaymentStatus('Payment error: ' + err.message, 'error');
            }
        },

        onCancel: () => {
            showPaymentStatus('Payment cancelled. You can try again when ready.', 'info');
        },

        onError: () => {
            showPaymentStatus('PayPal encountered an error. Please try again.', 'error');
        },
    }).render('#paypal-button-container');
}

/**
 * showPaymentStatus - Updates #payment-status with a message and applies a
 * type-specific CSS modifier class for visual feedback.
 * @param {string} message - The status message to display
 * @param {string} type - One of 'pending', 'success', 'error', 'info'
 */
function showPaymentStatus(message, type) {
    const el = document.getElementById('payment-status');
    if (!el) return;
    el.textContent = message;
    el.className = `payment-status payment-status--${type}`;
    el.style.display = 'block';
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
