/**
 * Main JavaScript for the Fingerprint Sensor Web Interface
 */

// Global variables
let webSocket = null;
const apiBase = window.location.origin + '/api';
const wsBase = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;

// Store fingerprint data
let fingerprints = [];

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
        countBtn: document.getElementById('countBtn'),
        clearBtn: document.getElementById('clearBtn'),
        statusBtn: document.getElementById('statusBtn'),
        clearLogBtn: document.getElementById('clearLogBtn'),
        fingerprintTable: document.getElementById('fingerprintTable'),
        fingerprintTableBody: document.getElementById('fingerprintTableBody'),
        refreshFingerprintsBtn: document.getElementById('refreshFingerprintsBtn')
    };

    // Connect to WebSocket
    connectWebSocket();

    // Check initial sensor status
    checkStatus();

    // Load fingerprints
    loadFingerprints();

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
    elements.countBtn.addEventListener('click', getCount);
    elements.clearBtn.addEventListener('click', confirmClear);

    // Fingerprint table buttons
    elements.refreshFingerprintsBtn.addEventListener('click', loadFingerprints);

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

            // If enrollment was successful, refresh fingerprint list
            if (data.status === 'success' && data.message.includes('enrolled successfully')) {
                setTimeout(loadFingerprints, 1000); // Delay slightly to ensure data is saved
            }
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
 * Load fingerprints from the API and populate the table
 */
function loadFingerprints() {
    fetch(`${apiBase}/fingerprints`)
        .then(response => response.json())
        .then(data => {
            fingerprints = data.fingerprints;
            renderFingerprintTable();
            log(`Loaded ${fingerprints.length} fingerprints`, 'success');
        })
        .catch(error => {
            log(`Error loading fingerprints: ${error}`, 'error');
            elements.fingerprintTableBody.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center">Error loading fingerprints</td>
                </tr>
            `;
        });
}

/**
 * Render the fingerprint table with current data
 */
function renderFingerprintTable() {
    if (!elements.fingerprintTableBody) return;

    if (fingerprints.length === 0) {
        elements.fingerprintTableBody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center">No fingerprints stored</td>
            </tr>
        `;
        return;
    }

    let html = '';
    fingerprints.forEach(fingerprint => {
        html += `
            <tr>
                <td>${fingerprint.position}</td>
                <td>
                    <input type="text"
                           class="fingerprint-name-input"
                           value="${fingerprint.name || ''}"
                           placeholder="Unnamed"
                           data-position="${fingerprint.position}"
                           onchange="updateFingerprintName(${fingerprint.position}, this.value)">
                </td>
                <td class="actions">
                    <select onchange="updateFingerprintAction(${fingerprint.position}, this.value)">
                        <option value="na" ${fingerprint.action === "none" ? "selected" : ""}>No Action</option>
                        <option value="on" ${fingerprint.action === "on" ? "selected" : ""}>Smart Plug ON</option>
                        <option value="off" ${fingerprint.action === "off" ? "selected" : ""}>Smart Plug OFF</option>
                        <option value="toggle" ${fingerprint.action === "toggle" ? "selected" : ""}>Toggle Plug</option>
                    </select>
                </td>
                <td class="delete">
                    <button class="btn btn-small btn-danger" onclick="deleteFingerByPosition(${fingerprint.position})">Delete</button>
                </td>
            </tr>
        `;
    });

    elements.fingerprintTableBody.innerHTML = html;
}

/**
 * Update the name of a fingerprint
 * @param {number} position - The fingerprint position
 * @param {string} name - The new name
 */
function updateFingerprintName(position, name) {
    fetch(`${apiBase}/fingerprints/${position}/name`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: name })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            log(`Updated name for fingerprint at position ${position}`, 'success');

            // Update local data
            const index = fingerprints.findIndex(f => f.position === position);
            if (index !== -1) {
                fingerprints[index].name = name;
            }
        } else {
            log(`Failed to update name: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        log(`Error updating name: ${error}`, 'error');
    });
}

/**
 * Update the action of a fingerprint
 * @param {number} position - The fingerprint position
 * @param {string} action - The action
 */
function updateFingerprintAction(position, action) {
    fetch(`${apiBase}/fingerprints/${position}/action`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
    })
    .then(res => res.json())
    .then(data => log(data.message, data.success ? 'success' : 'error'))
    .catch(error => log(`Error updating action: ${error}`, 'error'));
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
    const name = prompt("Enter a name for this fingerprint (optional):", "");
    // If user cancels the prompt, name will be null
    if (name === null) return;

    log('Starting fingerprint enrollment...', 'warning');
    elements.fingerprintVisual.classList.add('scanning');

    fetch(`${apiBase}/enroll`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: name })
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
        if (data.success && data.position !== null) {
            // Find the fingerprint with this position
            const fingerprint = fingerprints.find(f => f.position === data.position);
            if (fingerprint && fingerprint.name) {
                log(`Fingerprint verified: ${fingerprint.name} (Position ${data.position}, Accuracy ${data.accuracy})`, 'success');
            } else {
                log(`Fingerprint verified at position ${data.position} with accuracy ${data.accuracy}`, 'success');
            }
        } else {
            log(data.message, 'warning');
        }
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
    if (!confirm(`Are you sure you want to delete the fingerprint at position ${position}?`)) {
        return;
    }

    log(`Deleting fingerprint at position ${position}...`, 'warning');

    fetch(`${apiBase}/delete/${position}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        log(data.message, data.success ? 'success' : 'error');
        if (data.success) {
            // Remove from local array and re-render table
            fingerprints = fingerprints.filter(f => f.position !== position);
            renderFingerprintTable();
        }
    })
    .catch(error => {
        log(`Error during deletion: ${error}`, 'error');
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
        if (data.success) {
            // Clear local data and re-render table
            fingerprints = [];
            renderFingerprintTable();
        }
        elements.fingerprintVisual.classList.remove('scanning');
    })
    .catch(error => {
        log(`Error clearing database: ${error}`, 'error');
        elements.fingerprintVisual.classList.remove('scanning');
    });
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initialize);
