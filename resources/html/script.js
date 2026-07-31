// script.js
document.addEventListener('DOMContentLoaded', function() {
    // --- THEME MANAGER ---
    initThemeManager();

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

// --- CACHE ---
let lastReceivedData = null;

// --- THEME MANAGER ---
const THEME_VARS = [
    '--bg-body', '--text-main', '--text-sub', '--border-color',
    '--row-bg', '--row-border', '--row-hover',
    '--input-bg', '--input-border', '--input-text',
    '--btn-sec-bg', '--btn-sec-text', '--btn-sec-hover',
    '--active-border', '--active-text', '--active-bg',
    '--toggle-bg', '--header-hover'
];
const builtInThemeIds = new Set(['light', 'dark', 'sepia']);
let customThemes = JSON.parse(localStorage.getItem('ll_config_custom_themes') || '{}');
let _importedThemesLoaded = false;
let themeSelector, themeRemoveBtn;

function initThemeManager() {
    themeSelector = document.getElementById('themeSelector');
    themeRemoveBtn = document.getElementById('themeRemoveBtn');

    document.getElementById('themeImportBtn').addEventListener('click', requestImportTheme);
    document.getElementById('themeExportBtn').addEventListener('click', requestExportTheme);
    themeRemoveBtn.addEventListener('click', removeSelectedTheme);
    document.getElementById('themeResetLink').addEventListener('click', resetThemeCache);
    themeSelector.addEventListener('change', changeTheme);

    for (const id in customThemes) addCustomOption(id);
    applyCustomThemeVars();

    const savedTheme = localStorage.getItem('ll_config_theme') || 'dark';
    themeSelector.value = builtInThemeIds.has(savedTheme) || (savedTheme in customThemes) ? savedTheme : 'dark';
    changeTheme();
}

function applyCustomThemeVars() {
    let styleTag = document.getElementById('dynamic-theme-overrides');
    if (!styleTag) {
        styleTag = document.createElement('style');
        styleTag.id = 'dynamic-theme-overrides';
        document.head.appendChild(styleTag);
    }
    let out = '';
    for (const [themeId, themeVars] of Object.entries(customThemes)) {
        const decls = Object.entries(themeVars).map(([k, v]) => `${k}: ${v};`).join(' ');
        out += `[data-theme="${themeId}"] { ${decls} }\n`;
    }
    styleTag.textContent = out;
}

function addCustomOption(id) {
    if (!themeSelector.querySelector(`option[value="${id}"]`)) {
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = `${id} (custom)`;
        themeSelector.appendChild(opt);
    }
}

function mergeImportedThemes(hostThemes) {
    if (_importedThemesLoaded || !hostThemes || Object.keys(hostThemes).length === 0) return;
    _importedThemesLoaded = true;
    for (const id in hostThemes) {
        customThemes[id] = hostThemes[id];
        addCustomOption(id);
    }
    localStorage.setItem('ll_config_custom_themes', JSON.stringify(customThemes));
    applyCustomThemeVars();
}

function updateRemoveButtonState() {
    const id = themeSelector.value;
    const removable = !builtInThemeIds.has(id) && (id in customThemes);
    themeRemoveBtn.disabled = !removable;
    themeRemoveBtn.title = removable ? `Remove the "${id}" theme` : 'Select a custom (imported) theme to enable';
}

function changeTheme() {
    const id = themeSelector.value;
    document.documentElement.setAttribute('data-theme', id);
    localStorage.setItem('ll_config_theme', id);
    updateRemoveButtonState();
}

function removeSelectedTheme() {
    const id = themeSelector.value;
    if (builtInThemeIds.has(id) || !(id in customThemes)) return;
    if (!confirm(`Permanently remove the "${id}" theme? Re-import its .theme.json to bring it back.`)) return;
    delete customThemes[id];
    localStorage.setItem('ll_config_custom_themes', JSON.stringify(customThemes));
    sendToFusion('remove_imported_theme', { id: id });
    const opt = themeSelector.querySelector(`option[value="${id}"]`);
    if (opt) opt.remove();
    applyCustomThemeVars();
    themeSelector.value = 'dark';
    changeTheme();
}

function requestImportTheme() { sendToFusion('import_theme'); }

function requestExportTheme() {
    const id = themeSelector.value;
    const computed = getComputedStyle(document.documentElement);
    const vars = {};
    THEME_VARS.forEach(v => { vars[v] = computed.getPropertyValue(v).trim(); });
    const content = JSON.stringify({ id: id, vars: vars }, null, 2);
    sendToFusion('export_theme', { content: content, default_name: `${id}.theme.json` });
}

function resetThemeCache() {
    if (!confirm('This will permanently delete all custom imported themes. Continue?')) return;
    localStorage.removeItem('ll_config_custom_themes');
    localStorage.removeItem('ll_config_theme');
    customThemes = {};
    _importedThemesLoaded = false;
    sendToFusion('reset_imported_themes');
    themeSelector.querySelectorAll('option').forEach(opt => {
        if (!builtInThemeIds.has(opt.value)) opt.remove();
    });
    const styleTag = document.getElementById('dynamic-theme-overrides');
    if (styleTag) styleTag.textContent = '';
    themeSelector.value = 'dark';
    changeTheme();
}

function handleThemeImported(parsed) {
    try {
        const themeData = JSON.parse(parsed.content);
        if (themeData.vars && themeData.id !== undefined) {
            customThemes[themeData.id] = themeData.vars;
            localStorage.setItem('ll_config_custom_themes', JSON.stringify(customThemes));
            sendToFusion('save_imported_theme', { id: themeData.id, vars: themeData.vars });
            addCustomOption(themeData.id);
            applyCustomThemeVars();
            themeSelector.value = themeData.id;
            changeTheme();
        }
    } catch (e) { console.log('Invalid theme JSON', e); }
}

// --- HELPERS ---
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) section.classList.toggle('collapsed');
}

function isConfigMatch(data, configName) {
    if (!configName || !data.configs || !data.configs[configName]) return false;
    const saved = data.configs[configName];

    // Check Params
    if (saved.params) {
        for (const [name, savedExpr] of Object.entries(saved.params)) {
            const currentParam = data.parameters.find(p => p.name === name);
            if (!currentParam || currentParam.expression !== savedExpr) return false;
        }
    }
    // Check Features
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

// ... (Connection Manager) ...
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
                if (action === 'theme_imported') {
                    try {
                        var parsed = typeof data === 'string' ? JSON.parse(data) : data;
                        handleThemeImported(parsed);
                    } catch (e) {
                        console.error("Theme Import Parse Error", e);
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
    if (data.addin_version) document.getElementById('versionTag').textContent = 'v' + data.addin_version;
    if (data.imported_themes) mergeImportedThemes(data.imported_themes);
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
                 pContainer.innerHTML = '<div class="empty-state">No Favorites marked. Uncheck ★ Favs to view all.</div>';
            } else {
                 pContainer.innerHTML = '<div class="empty-state">No User Parameters found.</div>';
            }
        } else {
            paramsToShow.forEach(param => {
                const row = document.createElement('div');
                row.className = 'param-row';
                const starColor = param.isFavorite ? '#ff9e3b' : '#555';
                const star = `<span class="fav-star" style="color:${starColor}; margin-right:6px; cursor:pointer;" onclick="toggleFavorite('${param.name}')">★</span>`;
                
                row.innerHTML = `
                    <div class="param-label" title="${param.name}">${star}${param.name}</div>
                    <div class="param-input">
                        <input type="text" value="${param.expression}" onchange="updateParam('${param.name}', this.value)" onkeydown="handleEnter(event, this)">
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
                updateBtn.onclick = () => updateSnapshot(name);

                const delBtn = document.createElement('button');
                delBtn.className = 'action-btn delete-btn';
                delBtn.innerHTML = '🗑️';
                delBtn.onclick = () => deleteSnapshot(name);

                row.appendChild(btn);
                row.appendChild(updateBtn);
                row.appendChild(delBtn);
                cContainer.appendChild(row);
            });
        }
    }

    // 3. Render Timeline Features
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
    sendToFusion('update_param', { name: name, value: value });
    if (lastReceivedData && lastReceivedData.parameters) {
        const param = lastReceivedData.parameters.find(p => p.name === name);
        if (param) param.expression = value;
    }
    markAsDirty(); 
}
function toggleFavorite(name) {
    sendToFusion('toggle_favorite', { name: name });
}
function toggleFeature(name, isChecked) {
    const shouldSuppress = !isChecked; // Toggle: On = Not Suppressed
    sendToFusion('toggle_feature', { name: name, is_suppressed: shouldSuppress });
}
function handleEnter(e, input) {
    if (e.key === 'Enter') input.blur(); 
}
function saveSnapshot() {
    const nameInput = document.getElementById('newConfigName');
    const name = nameInput.value.trim();
    if (!name) return;
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