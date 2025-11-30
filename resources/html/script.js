// script.js
// Handles communication between the HTML Sidecar and Fusion 360

document.addEventListener('DOMContentLoaded', function() {
    // --- THEME LOGIC ---
    const toggleSwitch = document.getElementById('theme-checkbox');
    const savedTheme = localStorage.getItem('ll_config_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    toggleSwitch.checked = (savedTheme === 'dark');

    toggleSwitch.addEventListener('change', function(e) {
        const newTheme = e.target.checked ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('ll_config_theme', newTheme);
    });

    // --- FAV FILTER LOGIC ---
    const favCheck = document.getElementById('favFilterCheck');
    const savedFavState = localStorage.getItem('ll_fav_only');
    favCheck.checked = (savedFavState !== 'false');

    favCheck.addEventListener('change', function(e) {
        localStorage.setItem('ll_fav_only', e.target.checked);
        if (lastReceivedData) {
            renderUI(lastReceivedData);
        }
    });

    // --- BUTTON INITIALIZATION ---
    const scanBtn = document.getElementById('scanBtn');
    const saveBtn = document.getElementById('saveConfigBtn');
    if (scanBtn) scanBtn.disabled = true;
    if (saveBtn) saveBtn.disabled = true;

    waitForFusion();

    if (scanBtn) {
        scanBtn.addEventListener('click', function(e) {
            e.stopPropagation(); 
            refreshData();
        });
    }
    if (saveBtn) saveBtn.addEventListener('click', saveSnapshot);
});

// --- CACHE FOR FILTERING ---
let lastReceivedData = null;

// --- UI HELPERS ---

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.toggle('collapsed');
    }
}

// --- STATE VERIFICATION ---
function isConfigMatch(data, configName) {
    if (!configName || !data.configs || !data.configs[configName]) return false;
    const saved = data.configs[configName];

    if (saved.params) {
        for (const [name, savedExpr] of Object.entries(saved.params)) {
            const currentParam = data.parameters.find(p => p.name === name);
            if (!currentParam || currentParam.expression !== savedExpr) return false;
        }
    }

    if (saved.features) {
        for (const [name, savedSuppressed] of Object.entries(saved.features)) {
            const currentFeat = data.features.find(f => f.name === name);
            if (!currentFeat || currentFeat.isSuppressed !== savedSuppressed) return false;
        }
    }
    return true;
}

function markAsDirty() {
    const activeBtns = document.querySelectorAll('.active-config');
    activeBtns.forEach(btn => btn.classList.remove('active-config'));
    const nameInput = document.getElementById('newConfigName');
    if (nameInput) nameInput.style.borderColor = '#ff9e3b';
}

// --- CONNECTION MANAGER ---

let connectionAttempts = 0;
const MAX_ATTEMPTS = 20;

function waitForFusion() {
    if (window.adsk) {
        console.log("Fusion API Bridge Found!");
        
        const scanBtn = document.getElementById('scanBtn');
        const saveBtn = document.getElementById('saveConfigBtn');
        if (scanBtn) scanBtn.disabled = false;
        if (saveBtn) saveBtn.disabled = false;

        if (window.adsk.fusion && window.adsk.fusion.on) {
            window.adsk.fusion.on('update_ui', function(jsonString) {
                var data = JSON.parse(jsonString);
                renderUI(data);
            });
        }
        
        window.fusionJavaScriptHandler = {
            handle: function(action, data) {
                if (action === 'update_ui') {
                    try {
                        var parsed = typeof data === 'string' ? JSON.parse(data) : data;
                        renderUI(parsed);
                    } catch (e) {
                        console.error("Legacy Parse Error", e);
                    }
                    return "OK";
                }
            }
        };

        refreshData();
    } else {
        connectionAttempts++;
        if (connectionAttempts > MAX_ATTEMPTS) {
            console.error("Connection Timeout: No adsk object found.");
            document.body.innerHTML = `
                <div style="padding: 20px; color: #ff8888; text-align: center;">
                    <h3>Connection Failed</h3>
                    <p>Fusion 360 API bridge not found.</p>
                </div>
            `;
            return;
        }
        setTimeout(waitForFusion, 500);
    }
}

// --- COMMUNICATION ---

function sendToFusion(action, data = {}) {
    const dataStr = JSON.stringify(data);
    if (window.adsk && window.adsk.fusion && window.adsk.fusion.sendCommand) {
        data.action = action; 
        window.adsk.fusion.sendCommand(JSON.stringify(data));
    } 
    else if (window.adsk && window.adsk.fusionSendData) {
        data.action = action; 
        window.adsk.fusionSendData('send', JSON.stringify(data));
    }
}

function refreshData() {
    sendToFusion('refresh_data');
}

// --- RENDERING ---

function renderUI(data) {
    lastReceivedData = data;

    const docNameEl = document.getElementById('docName');
    if (docNameEl) docNameEl.innerText = data.doc_name || "Unknown Design";

    // 1. Render Parameters
    const pContainer = document.getElementById('paramList');
    const favOnly = document.getElementById('favFilterCheck').checked;

    if (pContainer) {
        pContainer.innerHTML = '';
        let paramsToShow = data.parameters || [];
        if (favOnly) {
            paramsToShow = paramsToShow.filter(p => p.isFavorite);
        }

        if (paramsToShow.length === 0) {
            if (favOnly && data.parameters.length > 0) {
                 pContainer.innerHTML = '<div class="empty-state">No Favorites marked. Uncheck "Favs" to see all.</div>';
            } else {
                 pContainer.innerHTML = '<div class="empty-state">No User Parameters found.</div>';
            }
        } else {
            paramsToShow.forEach(param => {
                const row = document.createElement('div');
                row.className = 'param-row';
                
                const starColor = param.isFavorite ? '#ff9e3b' : '#555';
                const starTitle = param.isFavorite ? 'Unfavorite' : 'Favorite';
                
                const star = `<span class="fav-star" 
                                    title="${starTitle}" 
                                    style="color:${starColor}; margin-right:6px; cursor:pointer;"
                                    onclick="toggleFavorite('${param.name}')">★</span>`;
                
                row.innerHTML = `
                    <div class="param-label" title="${param.name}">${star}${param.name}</div>
                    <div class="param-input">
                        <input type="text" 
                               value="${param.expression}" 
                               onchange="updateParam('${param.name}', this.value)"
                               onkeydown="handleEnter(event, this)">
                    </div>
                `;
                pContainer.appendChild(row);
            });
        }
    }

    // 2. Render Configs
    const cContainer = document.getElementById('configList');
    if (cContainer) {
        cContainer.innerHTML = '';
        const configNames = data.configs ? Object.keys(data.configs) : [];
        if (configNames.length === 0) {
            cContainer.innerHTML = '<div class="empty-state">No configs saved.</div>';
        } else {
            let effectiveActive = data.active_config;
            if (effectiveActive && !isConfigMatch(data, effectiveActive)) {
                effectiveActive = null;
                setTimeout(markAsDirty, 0);
            } else {
                const nameInput = document.getElementById('newConfigName');
                if (nameInput) nameInput.style.borderColor = '';
            }

            configNames.forEach(name => {
                const row = document.createElement('div');
                row.className = 'config-row';
                
                const btn = document.createElement('button');
                btn.className = 'config-btn';
                if (effectiveActive === name) btn.classList.add('active-config');
                btn.innerText = name;
                btn.onclick = () => loadSnapshot(name);
                
                const updateBtn = document.createElement('button');
                updateBtn.className = 'action-btn update-btn';
                updateBtn.innerHTML = '💾';
                updateBtn.title = 'Update';
                updateBtn.onclick = () => updateSnapshot(name);

                const delBtn = document.createElement('button');
                delBtn.className = 'action-btn delete-btn';
                delBtn.innerHTML = '🗑️';
                delBtn.title = 'Delete';
                delBtn.onclick = () => deleteSnapshot(name);

                row.appendChild(btn);
                row.appendChild(updateBtn);
                row.appendChild(delBtn);
                cContainer.appendChild(row);
            });
        }
    }

    // 3. Render Features
    const fContainer = document.getElementById('featureList');
    if (fContainer) {
        fContainer.innerHTML = '';
        if (data.features) {
            data.features.forEach(feat => {
                const row = document.createElement('div');
                row.className = 'feature-row';
                const isChecked = !feat.isSuppressed ? 'checked' : '';
                row.innerHTML = `
                    <span>${feat.name}</span>
                    <label class="switch">
                        <input type="checkbox" ${isChecked} onchange="toggleFeature('${feat.name}', this.checked)">
                        <span class="slider"></span>
                    </label>
                `;
                fContainer.appendChild(row);
            });
        }
    }
}

// --- LOGIC ---
function updateParam(name, value) {
    // 1. Send command to Fusion (The Source of Truth)
    sendToFusion('update_param', { name: name, value: value });
    // 2. Update Local Cache (The UI Memory)
    // This prevents the value from reverting if we re-render (e.g. toggling favorites)
    if (lastReceivedData && lastReceivedData.parameters) {
        const param = lastReceivedData.parameters.find(p => p.name === name);
        if (param) {
            param.expression = value;
        }
    }
    // 3. Update Visuals
    markAsDirty(); 
}function toggleFavorite(name) {
    sendToFusion('toggle_favorite', { name: name });
}
function toggleFeature(name, isChecked) {
    const shouldSuppress = !isChecked;
    sendToFusion('toggle_feature', { name: name, is_suppressed: shouldSuppress });
}
function handleEnter(e, input) {
    if (e.key === 'Enter') input.blur(); 
}
function saveSnapshot() {
    const nameInput = document.getElementById('newConfigName');
    const name = nameInput.value.trim();
    if (!name) return;
    
    // Removed includeApps logic
    sendToFusion('save_snapshot', { config_name: name });
    nameInput.value = ''; 
}
function updateSnapshot(name) {
    if(confirm(`Update '${name}'?`)) {
        sendToFusion('save_snapshot', { config_name: name });
    }
}
function deleteSnapshot(name) {
    if(confirm(`Delete '${name}'?`)) {
        sendToFusion('delete_snapshot', { config_name: name });
    }
}
function loadSnapshot(name) {
    sendToFusion('load_snapshot', { config_name: name });
}