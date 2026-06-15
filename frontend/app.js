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
// --- Copier Logic ---
const btnFetchOdds = document.getElementById('btn-fetch-odds');
const spinnerOdds = document.getElementById('spinner-odds');
const btnCopyOdds = document.getElementById('btn-copy-odds');
const oddsOutput = document.getElementById('odds-output');

// 競馬場コード変換用
const courseMap = {
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟", "05": "東京",
    "06": "中山", "07": "中京", "08": "京都", "09": "阪神", "10": "小倉"
};

function formatRaceName(raceId) {
    const courseCode = raceId.substring(4, 6);
    const raceNum = parseInt(raceId.substring(10, 12), 10);
    const courseName = courseMap[courseCode] || courseCode;
    return `${courseName}${raceNum}R`;
}

async function loadRacesForCopier() {
    // If races are already loaded for the current date, skip.
    // Otherwise fetch from /api/races
    
    // Instead of forcing Sunday, get the exact date from the input
    const val = targetDateInput.value;
    if (!val) return;
    
    const d = new Date(val);
    if (isNaN(d.getTime())) return;
    
    const targetDate = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;

    // We can fetch races
    const data = await fetchAPI(`/races?target_date=${targetDate}`);
    if (data && data.races) {
        const races = data.races; // List of race IDs
        
        // Populate 5 dropdowns
        for (let i = 1; i <= 5; i++) {
            const select = document.getElementById(`win5-race-${i}`);
            // Keep the selected value if it exists and is in the new list, otherwise reset
            const currentVal = select.value;
            select.innerHTML = '';
            
            // Add an empty default option
            const defaultOpt = document.createElement('option');
            defaultOpt.value = "";
            defaultOpt.innerText = "選択してください";
            select.appendChild(defaultOpt);

            races.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r;
                opt.innerText = formatRaceName(r);
                select.appendChild(opt);
            });

            // Try to auto-select if empty
            if (currentVal && races.includes(currentVal)) {
                select.value = currentVal;
            }
        }
        
        // Basic Auto-select logic using the backend's predicted WIN5 races
        if (data.win5_races && data.win5_races.length === 5) {
            for (let i = 0; i < 5; i++) {
                const sel = document.getElementById(`win5-race-${i+1}`);
                if (!sel.value) { // Only auto-select if empty
                    sel.value = data.win5_races[i];
                }
            }
        } else {
            // Fallback: naive auto-select
            if (!document.getElementById('win5-race-1').value) {
                const r10 = races.filter(r => r.endsWith('10'));
                const r11 = races.filter(r => r.endsWith('11'));
                const autoSelects = [...r10, ...r11].sort();
                for (let i = 0; i < Math.min(5, autoSelects.length); i++) {
                    document.getElementById(`win5-race-${i+1}`).value = autoSelects[i];
                }
            }
        }
    }
}

targetDateInput.addEventListener('change', () => {
    // Reload races
    loadRacesForCopier();
});

btnFetchOdds.addEventListener('click', async () => {
    btnFetchOdds.classList.add('hidden');
    spinnerOdds.classList.remove('hidden');
    
    // Collect selected race IDs
    const raceIds = [];
    for (let i = 1; i <= 5; i++) {
        const val = document.getElementById(`win5-race-${i}`).value;
        if (val) raceIds.push(val);
    }
    
    if (raceIds.length === 0) {
        oddsOutput.value = "レースが選択されていません。";
        spinnerOdds.classList.add('hidden');
        btnFetchOdds.classList.remove('hidden');
        return;
    }

    // Build Query
    const qParams = raceIds.map(id => `race_ids=${id}`).join('&');
    const data = await fetchAPI(`/win5-live-odds?${qParams}`);
    
    if (data && data.races) {
        let outText = "";
        for (const r_id of raceIds) {
            outText += `【${formatRaceName(r_id)}】\n`;
            outText += "馬番\t馬名\t単勝オッズ\t人気順\n"; // Excel用ヘッダー
            const horses = data.races[r_id] || [];
            if (horses.length === 0) {
                outText += "データがありません\n\n";
                continue;
            }
            horses.forEach(h => {
                outText += `${h.umaban}\t${h.horse_name}\t${h.odds}\t${h.popularity}\n`;
            });
            outText += "\n";
        }
        oddsOutput.value = outText.trim();
    } else {
        oddsOutput.value = "取得に失敗しました。";
    }

    spinnerOdds.classList.add('hidden');
    btnFetchOdds.classList.remove('hidden');
});

btnCopyOdds.addEventListener('click', () => {
    oddsOutput.focus();
    oddsOutput.setSelectionRange(0, oddsOutput.value.length);
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(oddsOutput.value);
    } else {
        document.execCommand('copy');
    }
    const originalText = btnCopyOdds.innerText;
    btnCopyOdds.innerText = "コピー完了！";
    btnCopyOdds.style.backgroundColor = "var(--accent-success)";
    setTimeout(() => {
        btnCopyOdds.innerText = originalText;
        btnCopyOdds.style.backgroundColor = "var(--accent-secondary)";
    }, 2000);
});

// Initialize init logic
document.addEventListener('DOMContentLoaded', () => {
    // set default input to today
    const now = new Date();
    targetDateInput.value = now.toISOString().split('T')[0];
    loadRacesForCopier();
});
