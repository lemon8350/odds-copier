// DOM Elements
const elCeiling = document.getElementById('ceiling-value');
const elCurrent = document.getElementById('current-value');
const elRemaining = document.getElementById('remaining-value');
const elGaugeVal = document.getElementById('gauge-value');
const elMessage = document.getElementById('gauge-message');
const btnSat = document.getElementById('btn-fetch-sat');
const btnSun = document.getElementById('btn-fetch-sun');
const spinnerSat = document.getElementById('spinner-sat');
const spinnerSun = document.getElementById('spinner-sun');
const raceSelect = document.getElementById('race-select');
const statusIndicator = document.getElementById('status-indicator');
const targetDateInput = document.getElementById('target-date');

// State
let ceiling = null;
let current = null;

// API URL
const API_BASE = window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://127.0.0.1:8000/api' 
    : '/api';

// --- Functions ---
async function fetchAPI(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        if (!res.ok) throw new Error('API Error');
        statusIndicator.style.backgroundColor = 'var(--accent-success)';
        statusIndicator.style.boxShadow = '0 0 10px var(--accent-success)';
        return await res.json();
    } catch (e) {
        statusIndicator.style.backgroundColor = 'var(--accent-secondary)';
        statusIndicator.style.boxShadow = '0 0 10px var(--accent-secondary)';
        console.error(e);
        return null;
    }
}

function updateGauge() {
    if (ceiling === null || current === null) return;
    
    const remaining = ceiling - current;
    elRemaining.innerText = remaining > 0 ? remaining : 0;
    
    // Gauge max is ceiling.
    let ratio = 1 - (current / ceiling);
    if (ratio < 0) ratio = 0;
    if (ratio > 1) ratio = 1;
    
    // The SVG path has length ~125.6
    // offset 125.6 is empty (0%)
    // offset 0 is full (100%)
    const offset = 125.6 - (125.6 * ratio);
    elGaugeVal.style.strokeDashoffset = offset;
    
    // Color and message logic
    elMessage.className = 'gauge-message'; // reset
    if (remaining >= 20) {
        elGaugeVal.style.stroke = 'var(--accent-success)'; // Green
        elMessage.innerText = `和${remaining} 以内。大荒れまで許容される大波乱推奨！`;
        elMessage.classList.add('msg-safe');
    } else if (remaining >= 10) {
        elGaugeVal.style.stroke = 'var(--accent-warning)'; // Yellow
        elMessage.innerText = `和${remaining} 以内。中穴狙いが面白そう。`;
        elMessage.classList.add('msg-warn');
    } else if (remaining > 0) {
        elGaugeVal.style.stroke = 'var(--accent-secondary)'; // Red
        elMessage.innerText = `和${remaining} 以内。超ガチガチ決着濃厚！本命狙い！`;
        elMessage.classList.add('msg-danger');
    } else {
        elGaugeVal.style.stroke = 'var(--accent-secondary)';
        elMessage.innerText = `すでに上限突破！波乱の連続です。`;
        elMessage.classList.add('msg-danger');
    }
}

// --- Helpers ---
function getWeekendDatesFromInput() {
    const val = targetDateInput.value;
    if (!val) return { sat: '', sun: '' }; // Fallback to backend auto
    
    // Parse selected date (e.g. "2026-06-07")
    const d = new Date(val);
    if (isNaN(d.getTime())) return { sat: '', sun: '' };
    
    // Find closest weekend (assuming the picked date is roughly around the target weekend)
    // If the picked date is a Sunday(0), Saturday is d - 1 day.
    // If the picked date is a Saturday(6), Sunday is d + 1 day.
    const day = d.getDay();
    let satDate = new Date(d);
    let sunDate = new Date(d);
    
    if (day === 6) {
        sunDate.setDate(d.getDate() + 1);
    } else if (day === 0) {
        satDate.setDate(d.getDate() - 1);
    } else {
        // If a weekday is picked, default to the upcoming weekend
        const daysToSat = 6 - day;
        satDate.setDate(d.getDate() + daysToSat);
        sunDate.setDate(d.getDate() + daysToSat + 1);
    }
    
    const fmt = (dt) => {
        const y = dt.getFullYear();
        const m = String(dt.getMonth() + 1).padStart(2, '0');
        const dNum = String(dt.getDate()).padStart(2, '0');
        return `${y}${m}${dNum}`;
    };
    
    return { sat: fmt(satDate), sun: fmt(sunDate) };
}

// --- Event Listeners ---
btnSat.addEventListener('click', async () => {
    btnSat.classList.add('hidden');
    spinnerSat.classList.remove('hidden');
    
    const dates = getWeekendDatesFromInput();
    const q = dates.sat ? `?target_date=${dates.sat}` : '';
    
    const data = await fetchAPI(`/saturday-ceiling${q}`);
    if (data && data.ceiling !== undefined) {
        ceiling = data.ceiling;
        elCeiling.innerText = ceiling;
        updateGauge();
    }
    
    spinnerSat.classList.add('hidden');
    btnSat.classList.remove('hidden');
});

btnSun.addEventListener('click', async () => {
    btnSun.classList.add('hidden');
    spinnerSun.classList.remove('hidden');
    
    const upTo = raceSelect.value;
    const dates = getWeekendDatesFromInput();
    const qTarget = dates.sun ? `&target_date=${dates.sun}` : '';
    
    const data = await fetchAPI(`/sunday-current?up_to_race=${upTo}${qTarget}`);
    if (data && data.current_sum !== undefined) {
        current = data.current_sum;
        elCurrent.innerText = current;
        updateGauge();
    }
    
    spinnerSun.classList.add('hidden');
    btnSun.classList.remove('hidden');
});

// Initial Ping
fetchAPI('/status');

// Initialize init logic
document.addEventListener('DOMContentLoaded', () => {
    // set default input to today
    const now = new Date();
    targetDateInput.value = now.toISOString().split('T')[0];
});
