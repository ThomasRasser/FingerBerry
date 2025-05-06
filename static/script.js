/**
 * Main JavaScript for the Fingerprint Sensor Web Interface
 */

// Global variables
let webSocket = null;
const apiBase = window.location.origin + '/api';
const wsBase = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;

// DOM elements - we will populate this when the page loads
let elements = {};

/**
 * Initialize the application
 */
function initialize() {
    // Get DOM elements
    elements = {
        sensorStatus: document.getElementById('sensorStatus'),
        fingerprintVisual: document.getElementById('fingerprintVisual'),
        log: document.getElementById('log'),
        enrollBtn: document.getElementById('enrollBtn'),
        verifyBtn: document.getElementById('verifyBtn'),
        deleteBtn: document.getElementById('deleteBtn'),
        countBtn: document.getElementById('countBtn'),
        clearBtn: document.getElementById('clearBtn'),
        statusBtn: document.getElementById('statusBtn'),
        clearLogBtn: document.getElementById('clearLogBtn')
    };

    // Connect to WebSocket
    connectWebSocket();

    // Check initial sensor status
    checkStatus();

    // Set up button event listeners
    setupEventListeners();
}

/**
 * Set up event listeners for buttons
 */
function setupEventListeners() {
    // Status button
    elements.statusBtn.addEventListener('click', checkStatus);

    // Operation buttons
    elements.enrollBtn.addEventListener('click', enrollFinger);
    elements.verifyBtn.addEventListener('click', verifyFinger);
    elements.deleteBtn.addEventListener('click', function() {
        const position = prompt("Enter fingerprint position to delete, or leave blank to scan:", "");
        if (position === null) return; // User cancelled

        if (position === "" || isNaN(parseInt(position))) {
            deleteFinger();
        } else {
            deleteFingerByPosition(parseInt(position));
        }
    });
    elements.countBtn.addEventListener('click', getCount);
    elements.clearBtn.addEventListener('click', confirmClear);

    // Clear log button
    elements.clearLogBtn.addEventListener('click', clearLog);
}

/**
 * Connect to the WebSocket server
 */
function connectWebSocket() {
    if (webSocket && webSocket.readyState !== WebSocket.CLOSED) {
        return; // Already connected or connecting
    }

    webSocket = new WebSocket(`${wsBase}/ws`);

    webSocket.onopen = function() {
        log('WebSocket connected', 'success');
        elements.fingerprintVisual.classList.remove('scanning');
    };

    webSocket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            // If not JSON, just log as plain text
            log(event.data);
        }
    };

    webSocket.onclose = function() {
        log('WebSocket disconnected, trying to reconnect in 5s...', 'error');
        setTimeout(connectWebSocket, 5000);
    };

    webSocket.onerror = function(error) {
        log('WebSocket error: ' + error.message, 'error');
    };
}

/**
 * Handle messages from the WebSocket
 * @param {Object} data - The message data
 */
function handleWebSocketMessage(data) {
    // Handle different message types
    switch (data.type) {
        case 'status':
            updateSensorState(data.status, data.message);
            log(data.message, data.status === 'success' ? 'success' :
                             data.status === 'failed' ? 'error' : 'warning');
            break;

        case 'error':
            log(data.message, 'error');
            elements.fingerprintVisual.classList.remove('scanning');
            break;

        case 'connection':
            log('WebSocket: ' + data.message, 'success');
            break;

        default:
            // For unknown types, just log the message
            log(JSON.stringify(data));
    }
}

/**
 * Update the visual sensor state
 * @param {string} status - The sensor status
 * @param {string} message - The status message
 */
function updateSensorState(status, message) {
    // Update the fingerprint visual
    if (['enrolling', 'verifying', 'deleting', 'clearing'].includes(status)) {
        elements.fingerprintVisual.classList.add('scanning');
    } else {
        elements.fingerprintVisual.classList.remove('scanning');
    }

    // Update the sensor status text and class
    if (elements.sensorStatus) {
        elements.sensorStatus.textContent = message;

        // Remove existing status classes
        elements.sensorStatus.classList.remove('status-connected', 'status-disconnected', 'status-waiting');

        // Add appropriate class
        if (status === 'success') {
            elements.sensorStatus.classList.add('status-connected');
        } else if (status === 'failed' || status === 'error') {
            elements.sensorStatus.classList.add('status-disconnected');
        } else {
            elements.sensorStatus.classList.add('status-waiting');
        }
    }
}

/**
 * Check sensor connection status
 */
function checkStatus() {
    fetch(`${apiBase}/status`)
        .then(response => response.json())
        .then(data => {
            const statusClass = data.connected ? 'status-connected' : 'status-disconnected';
            elements.sensorStatus.textContent = data.message;
            elements.sensorStatus.className = `status ${statusClass}`;
            log(data.message, data.connected ? 'success' : 'error');
        })
        .catch(error => {
            log(`Error checking status: ${error}`, 'error');
            elements.sensorStatus.textContent = 'Error checking sensor status';
            elements.sensorStatus.className = 'status status-disconnected';
        });
}

/**
 * Add message to the log
 * @param {string} message - The message to log
 * @param {string} type - The message type (success, error, warning, or empty for info)
 */
function log(message, type = '') {
    const logElement = elements.log;
    const timestamp = new Date().toLocaleTimeString();

    const entry = document.createElement('div');
    entry.className = 'log-entry';

    const timeSpan = document.createElement('span');
    timeSpan.className = 'log-time';
    timeSpan.textContent = timestamp;

    const messageSpan = document.createElement('span');
    if (type) {
        messageSpan.className = `log-${type}`;
    }
    messageSpan.textContent = message;

    entry.appendChild(timeSpan);
    entry.appendChild(document.createTextNode(' '));
    entry.appendChild(messageSpan);

    logElement.appendChild(entry);
    logElement.scrollTop = logElement.scrollHeight;
}

/**
 * Clear the log panel
 */
function clearLog() {
    elements.log.innerHTML = '';
    log('Log cleared', 'info');
}

/**
 * Enroll a new fingerprint
 */
function enrollFinger() {
    log('Starting fingerprint enrollment...', 'warning');
    elements.fingerprintVisual.classList.add('scanning');

    fetch(`${apiBase}/enroll`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        log(data.message, data.success ? 'success' : 'warning');
    })
    .catch(error => {
        log(`Error during enrollment: ${error}`, 'error');
        elements.fingerprintVisual.classList.remove('scanning');
    });
}

/**
 * Verify a fingerprint
 */
function verifyFinger() {
    log('Starting fingerprint verification...', 'warning');
    elements.fingerprintVisual.classList.add('scanning');

    fetch(`${apiBase}/verify`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        log(data.message, data.success ? 'success' : 'warning');
    })
    .catch(error => {
        log(`Error during verification: ${error}`, 'error');
        elements.fingerprintVisual.classList.remove('scanning');
    });
}

/**
 * Delete a fingerprint by position
 * @param {number} position - The position to delete
 */
function deleteFingerByPosition(position) {
    log(`Deleting fingerprint at position ${position}...`, 'warning');

    fetch(`${apiBase}/delete/${position}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        log(data.message, data.success ? 'success' : 'error');
    })
    .catch(error => {
        log(`Error during deletion: ${error}`, 'error');
    });
}

/**
 * Delete a fingerprint by scanning
 */
function deleteFinger() {
    log('Place finger to delete from database...', 'warning');
    elements.fingerprintVisual.classList.add('scanning');

    fetch(`${apiBase}/delete`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        log(data.message, data.success ? 'success' : 'warning');
    })
    .catch(error => {
        log(`Error during deletion: ${error}`, 'error');
        elements.fingerprintVisual.classList.remove('scanning');
    });
}

/**
 * Get stored fingerprint count
 */
function getCount() {
    fetch(`${apiBase}/count`)
        .then(response => response.json())
        .then(data => {
            log(data.message, 'success');
        })
        .catch(error => {
            log(`Error getting count: ${error}`, 'error');
        });
}

/**
 * Confirm before clearing database
 */
function confirmClear() {
    if (confirm("WARNING: This will delete ALL stored fingerprints! Continue?")) {
        clearDatabase();
    }
}

/**
 * Clear fingerprint database
 */
function clearDatabase() {
    log('Clearing fingerprint database...', 'warning');
    elements.fingerprintVisual.classList.add('scanning');

    fetch(`${apiBase}/clear`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        log(data.message, data.success ? 'success' : 'error');
        elements.fingerprintVisual.classList.remove('scanning');
    })
    .catch(error => {
        log(`Error clearing database: ${error}`, 'error');
        elements.fingerprintVisual.classList.remove('scanning');
    });
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initialize);
