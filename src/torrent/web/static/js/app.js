// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0.0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDate(timestamp) {
    if (!timestamp) return 'Never';
    return new Date(timestamp * 1000).toLocaleString();
}

function formatProgress(progress) {
    return Math.round(progress * 100) + '%';
}

// Error handling
function showErrorMessage(message) {
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function hideErrorMessage() {
    const errorMessage = document.getElementById('error-message');
    errorMessage.style.display = 'none';
}

function handleApiError(error, context) {
    console.error(`Error in ${context}:`, error);
    showErrorMessage(`Error in ${context}: ${error}`);
}

// DOM updates
function updateProgressBar(progress) {
    return `<div class="progress-bar" style="width: ${progress}%"></div>`;
}

function updateStatusBadge(status) {
    return `<span class="status-badge ${status}">${status}</span>`;
}

function updateRateDisplay(rate) {
    return formatBytes(rate) + '/s';
}

function updateStats(stats) {
    document.getElementById('total-torrents').textContent = stats.total;
    document.getElementById('seeding-torrents').textContent = stats.seeding;
    document.getElementById('downloading-torrents').textContent = stats.downloading;
    document.getElementById('error-torrents').textContent = stats.errors;
}

function updateErrors(errors) {
    const errorItems = document.getElementById('errorItems');
    errorItems.innerHTML = errors.map(error => `
        <div class="error-item">${error}</div>
    `).join('');
}

function updateTorrentList(torrents) {
    const torrentList = document.getElementById('torrent-list');
    torrentList.innerHTML = torrents.map(torrent => `
        <div class="torrent-item">
            <div class="torrent-info">
                <div class="torrent-name">${torrent.name}</div>
                <div class="torrent-status">
                    ${updateStatusBadge(torrent.status)}
                    ${updateProgressBar(torrent.progress)}
                </div>
                <div class="torrent-stats">
                    <span>↓ ${updateRateDisplay(torrent.download_rate)}</span>
                    <span>↑ ${updateRateDisplay(torrent.upload_rate)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function updateBatchStatus(data) {
    const batchStatus = document.getElementById('batch-status');
    const status = data.is_running ? 'Running' : 'Stopped';
    const lastRun = formatDate(data.last_run);
    const nextCheck = formatDate(data.next_check);

    batchStatus.innerHTML = `
        <div class="batch-status">
            <h3>Batch Process Status</h3>
            <p>Status: ${status}</p>
            <p>Last Run: ${lastRun}</p>
            <p>Next Check: ${nextCheck}</p>
            ${data.message ? `<p>Message: ${data.message}</p>` : ''}
        </div>
    `;
}

function updateBatchControls(isRunning) {
    const startButton = document.getElementById('start-batch');
    const stopButton = document.getElementById('stop-batch');

    startButton.disabled = isRunning;
    stopButton.disabled = !isRunning;
}

// API calls
async function startBatch() {
    try {
        const response = await fetch('/batch/start', { method: 'POST' });
        const data = await response.json();
        handleBatchResponse(data);
    } catch (error) {
        handleApiError(error, 'starting batch');
    }
}

async function stopBatch() {
    try {
        const response = await fetch('/batch/stop', { method: 'POST' });
        const data = await response.json();
        handleBatchResponse(data);
    } catch (error) {
        handleApiError(error, 'stopping batch');
    }
}

function handleBatchResponse(response) {
    if (response.success) {
        updateBatchStatus(response.batch_status);
        updateBatchControls(response.batch_status.is_running);
    } else {
        handleApiError(response.error, 'batch operation');
    }
}

// Real-time updates
let updateInterval;

function startUpdates() {
    updateStatus();
    updateInterval = setInterval(updateStatus, 5000);
}

function stopUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

async function updateStatus() {
    try {
        const response = await fetch('/status');
        const data = await response.json();

        updateTorrentList(data.torrents);
        updateStats(data.stats);
        updateErrors(data.errors);
        updateBatchStatus(data.batch_status);
        updateBatchControls(data.batch_status.is_running);
    } catch (error) {
        handleApiError(error, 'updating status');
    }
}

// Dark mode
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    document.getElementById('start-batch').addEventListener('click', startBatch);
    document.getElementById('stop-batch').addEventListener('click', stopBatch);

    // Set up dark mode
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }

    // Start real-time updates
    startUpdates();
});
