// Experiment Detail Page JavaScript
// Manages experiment conditions, sessions, and flow editor

const experimentId = document.body.dataset.experimentId;
let currentEditingStepIndex = null;
let currentEditingFlowConditionId = null;
let isEditingExperimentFlow = false;
let experimentFlowSteps = [];

// ========== Initialization ==========

document.addEventListener('DOMContentLoaded', function() {
    console.log('=== Experiment Detail Page Initialization ===');
    console.log('Experiment ID:', experimentId);
    loadExperimentFlow();
    loadParticipantCodes();
    loadSessions();
    loadAvailableModels();
});

// Load experiment flow and render preview
async function loadExperimentFlow() {
    console.log('📊 Loading experiment flow...');
    try {
        const response = await fetch(`/api/experiments`, {
            credentials: 'include'
        });
        const data = await response.json();
        const experiment = data.experiments.find(exp => exp.experiment_id === experimentId);
        
        if (experiment && experiment.experiment_flow) {
            experimentFlowSteps = experiment.experiment_flow;
            console.log('✅ Experiment flow loaded:', experimentFlowSteps.length, 'steps');
            renderFlowPreview();
        } else {
            console.log('⚠️ No experiment flow found');
        }
    } catch (error) {
        console.error('❌ Failed to load experiment flow:', error);
    }
}

// ========== Model Management ==========

async function loadAvailableModels() {
    const select = document.getElementById('botModel');
    
    // 要素が存在しない場合は何もしない
    if (!select) {
        console.log('botModel element not found, skipping model loading');
        return;
    }
    
    try {
        console.log('Fetching available models from Ollama...');
        const response = await fetch('/api/ollama/models', {
            credentials: 'include'
        });
        
        console.log('Models API response status:', response.status);
        
        if (!response.ok) {
            if (response.status === 401) {
                console.error('Unauthorized: Admin login required');
                select.innerHTML = '<option value="">❌ Not logged in as admin</option>';
                alert('Session expired. Please log in again.');
                window.location.href = '/admin/login';
                return;
            }
            
            const errorText = await response.text();
            console.error('Failed to fetch models:', response.status, errorText);
            select.innerHTML = `<option value="">❌ Error ${response.status}</option>`;
            return;
        }
        
        const data = await response.json();
        const models = data.models || [];
        
        console.log('Available models:', models);
        
        if (models.length === 0) {
            select.innerHTML = '<option value="">⚠️ No Ollama models installed</option>';
            console.warn('No Ollama models found. Please run: ollama pull gemma3:4b');
            alert('No Ollama models found.\n\nPlease install at least one model:\n\nollama pull gemma3:4b');
            return;
        }
        
        // モデルリストを表示
        select.innerHTML = '<option value="">-- Select a model --</option>' + 
            models.map(model => `<option value="${model}">${model}</option>`).join('');
        
        // selectを有効化
        select.disabled = false;
        
        // デフォルト選択 (推奨モデルがあれば)
        const preferredModels = ['gemma3:4b', 'gemma3:2b', 'llama3.2:3b'];
        const availablePreferred = preferredModels.find(m => models.includes(m));
        if (availablePreferred) {
            select.value = availablePreferred;
            console.log('Auto-selected preferred model:', availablePreferred);
        }
        
        console.log(`✅ Successfully loaded ${models.length} Ollama models`);
    } catch (error) {
        console.error('Exception while loading models:', error);
        if (select) {
            select.innerHTML = '<option value="">❌ Network error</option>';
        }
        alert('Failed to load models: ' + error.message + '\n\nIs Ollama running?');
    }
}

// ========== Session Management ==========

// ========== Participant Codes Display ==========

async function loadParticipantCodes() {
    try {
        const response = await fetch(`/api/experiments`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            console.error('Failed to load experiment data');
            return;
        }
        
        const data = await response.json();
        const experiment = data.experiments.find(exp => exp.experiment_id === experimentId);
        
        if (!experiment) {
            console.error('Experiment not found');
            return;
        }
        
        if (!experiment.participant_codes || Object.keys(experiment.participant_codes).length === 0) {
            document.getElementById('participantCodesDisplay').innerHTML = `
                <p style="color: #999; text-align: center;">No participant codes generated yet.</p>
            `;
            return;
        }
        
        displayParticipantCodes(experiment.participant_codes);
        
    } catch (error) {
        console.error('Error loading participant codes:', error);
    }
}

async function displayParticipantCodes(codes) {
    const codesArray = Object.entries(codes).map(([code, data]) => ({
        code,
        ...data
    }));
    
    // 状態別に分類
    const unused = codesArray.filter(c => c.status === 'unused');
    const used = codesArray.filter(c => c.status === 'used');
    const completed = codesArray.filter(c => c.status === 'completed');
    
    const total = codesArray.length;
    
    // Get participant URL
    let participantUrl = `${window.location.origin}/`;
    try {
        const response = await fetch('/api/server/ip');
        if (response.ok) {
            const data = await response.json();
            participantUrl = `http://${data.local_ip}:${data.port}/`;
        }
    } catch (error) {
        console.error('Failed to get server IP:', error);
    }
    
    let html = `
        <div style="margin-bottom: 15px;">
            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                <div style="flex: 1; padding: 10px; background: #e3f2fd; border-radius: 6px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 600; color: #1976d2;">${unused.length}</div>
                    <div style="font-size: 12px; color: #666;">Unused</div>
                </div>
                <div style="flex: 1; padding: 10px; background: #fff3e0; border-radius: 6px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 600; color: #f57c00;">${used.length}</div>
                    <div style="font-size: 12px; color: #666;">In Progress</div>
                </div>
                <div style="flex: 1; padding: 10px; background: #e8f5e9; border-radius: 6px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 600; color: #388e3c;">${completed.length}</div>
                    <div style="font-size: 12px; color: #666;">Completed</div>
                </div>
            </div>
            
            <!-- Participant URL Section -->
            <div style="margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-radius: 6px; border: 1px solid #dee2e6;">
                <div style="font-size: 12px; color: #666; margin-bottom: 6px; font-weight: 600;">Participant URL</div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <input type="text" id="participantUrlInput" value="${participantUrl}" readonly 
                           style="flex: 1; padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; font-size: 12px; background: white;">
                    <button onclick="copyToClipboard('participantUrlInput')" 
                            style="padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px; white-space: nowrap;">
                        📋 Copy
                    </button>
                </div>
                ${participantUrl.includes('localhost') || participantUrl.includes('127.0.0.1') ? 
                    '<div style="margin-top: 8px; padding: 8px; background: #fff3cd; border-radius: 4px; font-size: 11px; color: #856404;">⚠️ This URL may not be accessible from other computers.</div>' : 
                    '<div style="margin-top: 8px; padding: 8px; background: #d4edda; border-radius: 4px; font-size: 11px; color: #155724;">✓ Network accessible URL</div>'}
            </div>
            
            <!-- Codes List with Export and Management -->
            <div style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 12px; color: #666; font-weight: 600;">Codes & PINs (${total})</div>
                <div style="display: flex; gap: 6px;">
                    <button onclick="copyAllParticipantCodes()" 
                            style="padding: 4px 10px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
                        📋 Copy All
                    </button>
                    <button onclick="showCodeManagementMenu()" 
                            style="padding: 4px 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
                        ⚙️ Manage
                    </button>
                </div>
            </div>
            
            <div style="max-height: 350px; overflow-y: auto; border: 1px solid #ddd; border-radius: 6px; padding: 10px; background: #f8f9fa;">
    `;
    
    // Sort by status priority and then by code
    const sortedCodes = [
        ...unused.sort((a, b) => a.code.localeCompare(b.code)),
        ...used.sort((a, b) => a.code.localeCompare(b.code)),
        ...completed.sort((a, b) => a.code.localeCompare(b.code))
    ];
    
    sortedCodes.forEach(item => {
        let bgColor, textColor, statusText, icon;
        
        if (item.status === 'unused') {
            bgColor = '#e3f2fd';
            textColor = '#1976d2';
            statusText = 'Unused';
            icon = '⚪';
        } else if (item.status === 'used') {
            bgColor = '#fff3e0';
            textColor = '#f57c00';
            statusText = 'In Progress';
            icon = '🟡';
        } else if (item.status === 'completed') {
            bgColor = '#e8f5e9';
            textColor = '#388e3c';
            statusText = 'Completed';
            icon = '🟢';
        }
        
        const password = item.password || 'N/A';
        
        // Show delete button only for unused codes
        const deleteBtn = item.status === 'unused' ? 
            `<button onclick="deleteParticipantCode('${item.code}')" 
                     style="padding: 2px 6px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 10px; margin-left: 8px;"
                     title="Delete this code">
                ✕
            </button>` : '';
        
        html += `
            <div style="display: flex; align-items: center; padding: 8px; margin-bottom: 5px; background: ${bgColor}; border-radius: 4px; font-size: 12px;">
                <span style="margin-right: 8px;">${icon}</span>
                <div style="flex: 1; display: flex; gap: 10px; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <span style="font-size: 10px; color: #666; font-weight: 600;">CODE:</span>
                        <span style="font-family: 'Courier New', monospace; font-weight: 700; color: ${textColor}; background: white; padding: 2px 8px; border-radius: 3px; border: 1px solid ${textColor}; letter-spacing: 0.5px;">${item.code}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <span style="font-size: 10px; color: #666; font-weight: 600;">PIN:</span>
                        <span style="font-family: 'Courier New', monospace; font-weight: 700; color: #333; background: #fffacd; padding: 2px 8px; border-radius: 3px; border: 1px solid #ffd700; letter-spacing: 1px; font-size: 13px;">${password}</span>
                    </div>
                </div>
                <span style="font-size: 10px; color: #666;">${statusText}</span>
                ${deleteBtn}
            </div>
        `;
    });
    
    html += `
            </div>
            
            <!-- Instructions -->
            <div style="margin-top: 12px; padding: 10px; background: #e7f3ff; border-radius: 6px; font-size: 11px; line-height: 1.5; color: #0c5460;">
                <strong>Instructions for participants:</strong><br>
                1. Go to the URL above<br>
                2. Enter the <strong>CODE</strong> (6 characters: letters & numbers)<br>
                3. Enter the <strong>PIN</strong> (4 digits: numbers only)<br>
                4. Click "Start Experiment"
            </div>
        </div>
    `;
    
    document.getElementById('participantCodesDisplay').innerHTML = html;
    
    // Store codes globally for CSV export
    window.currentDisplayedCodes = codesArray;
}

// ========== Session List ==========

async function loadSessions() {
    console.log('📅 Loading sessions...');
    try {
        const response = await fetch(`/api/experiments/${experimentId}/sessions`, {
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Failed to load sessions');
        
        const data = await response.json();
        const sessions = data.sessions || [];
        
        console.log('✅ Sessions loaded:', sessions.length);
        
        const container = document.getElementById('sessionsList');
        const countSpan = document.getElementById('sessions-count');
        
        const activeSessions = sessions.filter(s => s.status === 'active');
        const endedSessions = sessions.filter(s => s.status === 'ended');
        countSpan.textContent = `(${sessions.length}) - Active: ${activeSessions.length} | Ended: ${endedSessions.length}`;
        
        if (sessions.length === 0) {
            container.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">No sessions yet</p>';
            return;
        }
        
        container.innerHTML = `
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f5f5f5; border-bottom: 2px solid #ddd;">
                        <th style="padding: 10px; text-align: left;">Participant Code</th>
                        <th style="padding: 10px; text-align: left;">Session ID</th>
                        <th style="padding: 10px; text-align: left;">Condition</th>
                        <th style="padding: 10px; text-align: center;">Participants</th>
                        <th style="padding: 10px; text-align: center;">Messages</th>
                        <th style="padding: 10px; text-align: center;">Status</th>
                        <th style="padding: 10px; text-align: center;">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${sessions.map(s => {
                        const participantCode = s.participant_code || 'N/A';
                        const codeStyle = participantCode !== 'N/A' 
                            ? 'font-family: monospace; font-weight: 600; color: #2c3e50;' 
                            : 'color: #999;';
                        return `
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 10px; ${codeStyle}">${participantCode}</td>
                            <td style="padding: 10px; font-family: monospace; font-size: 0.9em;">${s.session_id.substring(0, 16)}...</td>
                            <td style="padding: 10px;">${s.experiment_group || 'N/A'}</td>
                            <td style="padding: 10px; text-align: center;">${s.participants ? s.participants.length : 0}</td>
                            <td style="padding: 10px; text-align: center;">${s.total_messages || 0}</td>
                            <td style="padding: 10px; text-align: center;">
                                <span style="padding: 3px 8px; border-radius: 3px; font-size: 0.85em; background: ${s.status === 'active' ? '#d4edda' : '#f8d7da'}; color: ${s.status === 'active' ? '#155724' : '#721c24'};">
                                    ${s.status}
                                </span>
                            </td>
                            <td style="padding: 10px; text-align: center;">
                                <button class="btn btn-small btn-primary" onclick="viewSession('${s.session_id}')" style="margin-right: 4px;">View</button>
                                ${s.status === 'ended' ? `
                                    <button class="btn btn-small" onclick="exportSessionData('${s.session_id}', 'json')" style="margin-right: 4px;">JSON</button>
                                    <button class="btn btn-small" onclick="exportSessionData('${s.session_id}', 'csv')">CSV</button>
                                ` : ''}
                            </td>
                        </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

function toggleSessions() {
    const list = document.getElementById('sessionsList');
    const toggle = document.getElementById('sessions-toggle');
    
    if (list.style.display === 'none') {
        list.style.display = 'block';
        toggle.textContent = '▼';
    } else {
        list.style.display = 'none';
        toggle.textContent = '▶';
    }
}

function toggleConditions() {
    const list = document.getElementById('conditionsList');
    const toggle = document.getElementById('conditions-toggle');
    
    if (list.style.display === 'none') {
        list.style.display = 'block';
        toggle.textContent = '▼';
    } else {
        list.style.display = 'none';
        toggle.textContent = '▶';
    }
}

// Open flow modal for experiment-level editing
function openFlowModal() {
    isEditingExperimentFlow = true;
    currentEditingFlowConditionId = null;
    const modal = document.getElementById('flowModal');
    modal.style.display = 'flex';
    console.log('[Flow] Modal opened, calling renderSteps()');
    // renderSteps() will be overridden by experiment_flow_blocks.js to call renderFlowBlocks()
    setTimeout(() => {
        if (window.renderSteps) {
            window.renderSteps();
        } else {
            renderSteps();
        }
    }, 100);
}

// Render flow preview in main UI
function renderFlowPreview() {
    const preview = document.getElementById('flowPreview');
    if (!experimentFlowSteps || experimentFlowSteps.length === 0) {
        preview.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">Edit flow to build your experiment</p>';
        return;
    }
    
    // Render simplified view
    let html = '<div style="padding: 12px;">';
    experimentFlowSteps.forEach((step, index) => {
        if (step.step_type === 'branch') {
            const branches = step.branches || [];
            html += `
                <div style="padding: 8px 12px; background: #fafafa; border-left: 3px solid #e74c3c; margin-bottom: 8px; border-radius: 4px;">
                    <div style="font-weight: 500; color: #374151; font-size: 13px; margin-bottom: 6px;">
                        🔀 ${step.title || 'Branch'} <span style="color: #9ca3af; font-size: 11px;">(${branches.length} paths)</span>
                    </div>
                    ${branches.map((branch, idx) => `
                        <div style="margin-left: 16px; padding: 6px; background: white; border: 1px solid #e5e7eb; border-radius: 4px; margin-bottom: 4px; font-size: 12px; color: #6b7280;">
                            └─ ${branch.condition_label || 'Branch ' + (idx+1)}
                            ${branch.steps && branch.steps.length > 0 ? ` <span style="color: #9ca3af;">(${branch.steps.length} steps)</span>` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            const icon = getBlockIcon(step.step_type);
            html += `
                <div style="padding: 8px 12px; background: white; border-left: 3px solid #3b82f6; margin-bottom: 8px; border-radius: 4px; font-size: 13px; color: #374151; font-weight: 400;">
                    ${icon} ${step.title || getBlockTypeDisplay(step.step_type)}
                </div>
            `;
        }
    });
    html += '</div>';
    preview.innerHTML = html;
}

function viewSession(sessionId) {
    window.open(`/viewer?session_id=${sessionId}`, '_blank', 'width=800,height=600');
}

async function exportSessionData(sessionId, format) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}/export?format=${format}`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `messages_${sessionId}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Export failed');
        }
    } catch (error) {
        alert('Export failed: ' + error.message);
    }
}

// ========== Experiment Control ==========

let preparedPassword = null; // Store prepared password
let participantCodes = null; // Store generated participant codes

async function prepareParticipantInfo() {
    // Ask for number of participants
    const count = prompt('Number of participants (e.g., 20):');
    if (!count || isNaN(count) || count < 1) {
        alert('Please enter a valid number');
        return;
    }
    
    try {
        console.log(`Generating ${count} participant codes...`);
        console.log('Cookies:', document.cookie);
        
        // Generate participant codes
        const response = await fetch(`/api/experiments/${experimentId}/generate_codes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ count: parseInt(count) })
        });
        
        console.log(`Response status: ${response.status}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            console.error('Failed to generate codes:', errorData);
            
            if (response.status === 401) {
                alert('Session expired. Please log in again as administrator.');
                window.location.href = '/admin/login';
                return;
            }
            
            alert(`Failed to generate participant codes: ${errorData.detail || 'Unknown error'}`);
            return;
        }
        
        const data = await response.json();
        console.log(`Generated ${data.count} codes:`, data.codes);
        participantCodes = data.codes;
        
        // Reload participant codes display (no modal)
        await loadParticipantCodes();
        
        // Scroll to participant codes section
        document.getElementById('participantCodesDisplay').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (error) {
        console.error('Error generating codes:', error);
        alert('Error: ' + error.message);
    }
}

async function startExperiment() {
    // Use prepared password or generate new one
    const password = preparedPassword || generateRandomPassword();
    
    if (!confirm('Start this experiment now? Participants will be able to join with the access code.')) return;
    
    try {
        const response = await fetch(`/api/experiments/${experimentId}/start`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ password: password })
        });
        if (response.ok) {
            // Show success message
            showPasswordModal(password, true);
        } else {
            alert('Failed to start experiment');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function generateRandomPassword() {
    // Generate 6-character alphanumeric password
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // Exclude confusing characters
    let password = '';
    for (let i = 0; i < 6; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return password;
}

function showPasswordModal(password, experimentStarted = false) {
    const participantUrl = `${window.location.origin}/`;
    
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 10000;';
    
    const title = experimentStarted ? '✅ Experiment Started!' : '📋 Participant Information';
    const buttonText = experimentStarted ? 'Got it!' : 'Close';
    const statusMessage = experimentStarted 
        ? '<div style="padding: 10px; background: #d4edda; border-radius: 6px; margin-bottom: 15px; color: #155724; font-weight: 600;">✓ Experiment is now running</div>'
        : '<div style="padding: 10px; background: #fff3cd; border-radius: 6px; margin-bottom: 15px; color: #856404;">⚠️ Experiment not started yet. Share this info and click "Start Experiment" when ready.</div>';
    
    modal.innerHTML = `
        <div style="background: white; border-radius: 12px; padding: 30px; max-width: 500px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
            <h2 style="margin: 0 0 20px 0; color: #2c3e50;">${title}</h2>
            ${statusMessage}
            <div style="margin-bottom: 20px;">
                <p style="margin: 0 0 10px 0; color: #666;">Share this information with participants:</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
                    <div style="font-size: 12px; color: #999; margin-bottom: 5px;">Participant URL</div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="text" id="urlInput" value="${participantUrl}" readonly style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; font-size: 14px;">
                        <button onclick="copyToClipboard('urlInput')" style="padding: 8px 12px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">Copy</button>
                    </div>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 6px; border: 2px solid #f39c12;">
                    <div style="font-size: 12px; color: #856404; margin-bottom: 5px;">🔑 Session Password</div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="text" id="passwordInput" value="${password}" readonly style="flex: 1; padding: 8px; border: 1px solid #f39c12; border-radius: 4px; font-family: monospace; font-size: 20px; font-weight: bold; letter-spacing: 2px; text-align: center; background: white;">
                        <button onclick="copyToClipboard('passwordInput')" style="padding: 8px 12px; background: #f39c12; color: white; border: none; border-radius: 4px; cursor: pointer;">Copy</button>
                    </div>
                </div>
                
                <div style="margin-top: 15px; padding: 12px; background: #e8f5e9; border-left: 4px solid #4caf50; border-radius: 4px; font-size: 13px; color: #2e7d32;">
                    <strong>Instructions:</strong><br>
                    1. Give participants the URL<br>
                    2. Share the password with them<br>
                    3. They can enter the password when they join
                </div>
            </div>
            
            <button onclick="closePasswordModal(${experimentStarted})" style="width: 100%; padding: 12px; background: #2c3e50; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600;">${buttonText}</button>
        </div>
    `;
    
    document.body.appendChild(modal);
    window.currentPasswordModal = modal;
}

function copyToClipboard(inputId) {
    const input = document.getElementById(inputId);
    input.select();
    document.execCommand('copy');
    
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '✓ Copied!';
    button.style.background = '#27ae60';
    
    setTimeout(() => {
        button.textContent = originalText;
        button.style.background = '';
    }, 2000);
}

function closePasswordModal(shouldReload = false) {
    if (window.currentPasswordModal) {
        document.body.removeChild(window.currentPasswordModal);
        window.currentPasswordModal = null;
    }
    if (shouldReload) {
        location.reload();
    }
}

async function showParticipantCodesModal(codes) {
    // サーバーのローカルIPを取得
    let participantUrl = `${window.location.origin}/`;
    try {
        const response = await fetch('/api/server/ip');
        if (response.ok) {
            const data = await response.json();
            participantUrl = `http://${data.local_ip}:${data.port}/`;
        }
    } catch (error) {
        console.error('Failed to get server IP:', error);
    }
    
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 10000; overflow: auto;';
    
    // コードとパスワードのテーブル形式
    const codesTable = codes.map(item => `
        <tr style="border-bottom: 1px solid #dee2e6;">
            <td style="padding: 8px; font-family: monospace; font-weight: 600; font-size: 14px;">${item.code}</td>
            <td style="padding: 8px; font-family: monospace; font-weight: 600; font-size: 14px;">${item.password}</td>
        </tr>
    `).join('');
    
    modal.innerHTML = `
        <div style="background: white; border-radius: 12px; padding: 30px; max-width: 700px; max-height: 80vh; overflow-y: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.2); margin: 20px;">
            <h2 style="margin: 0 0 20px 0; color: #2c3e50;">📋 Participant Codes Generated</h2>
            <div style="padding: 10px; background: #fff3cd; border-radius: 6px; margin-bottom: 20px; color: #856404;">
                ⚠️ Save these codes! Distribute one code to each participant. Each code can only be used once.
            </div>
            
            <div style="margin-bottom: 25px;">
                <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #666;">Participant Codes & PINs (${codes.length} total)</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border: 2px solid #dee2e6; max-height: 300px; overflow-y: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #e9ecef; border-bottom: 2px solid #dee2e6;">
                                <th style="padding: 8px; text-align: left; font-size: 12px; color: #666;">Code</th>
                                <th style="padding: 8px; text-align: left; font-size: 12px; color: #666;">PIN</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${codesTable}
                        </tbody>
                    </table>
                </div>
                <button onclick="copyParticipantCodes()" style="margin-top: 10px; padding: 8px 16px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">📋 Copy All (CSV format)</button>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #666;">Participant URL</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px;">
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="text" id="codesUrlInput" value="${participantUrl}" readonly style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; font-size: 14px;">
                        <button onclick="copyToClipboard('codesUrlInput')" style="padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; white-space: nowrap;">📋 Copy</button>
                    </div>
                    ${participantUrl.includes('localhost') || participantUrl.includes('127.0.0.1') ? 
                        '<div style="margin-top: 10px; padding: 10px; background: #fff3cd; border-radius: 4px; font-size: 12px; color: #856404;">⚠️ Warning: This URL uses localhost and may not be accessible from other computers. Make sure participants access from the same computer or use the server\'s IP address.</div>' : 
                        '<div style="margin-top: 10px; padding: 10px; background: #d4edda; border-radius: 4px; font-size: 12px; color: #155724;">✓ This URL should be accessible from other computers on the same network.</div>'}
                </div>
            </div>
            
            <div style="background: #e7f3ff; padding: 15px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; line-height: 1.6;">
                <strong>Instructions for participants:</strong><br>
                1. Go to the URL above<br>
                2. Enter their assigned participant code (e.g., a3k9r2)<br>
                3. Enter their assigned password (e.g., x7m4p1)<br>
                4. Start the experiment
            </div>
            
            <button onclick="closeCodesModal()" style="width: 100%; padding: 12px; background: #2c3e50; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600;">Close</button>
        </div>
    `;
    
    document.body.appendChild(modal);
    window.currentCodesModal = modal;
    window.currentParticipantCodes = codes;
}

function copyParticipantCodes() {
    // CSV format: Code,Password
    const csv = 'Code,Password\n' + window.currentParticipantCodes.map(item => `${item.code},${item.password}`).join('\n');
    navigator.clipboard.writeText(csv).then(() => {
        alert('All participant codes and passwords copied to clipboard (CSV format)!');
    });
}

function closeCodesModal() {
    if (window.currentCodesModal) {
        document.body.removeChild(window.currentCodesModal);
        window.currentCodesModal = null;
    }
}

async function pauseExperiment() {
    if (!confirm('Pause this experiment? New participants will not be able to join until resumed.')) return;
    
    try {
        const response = await fetch(`/api/experiments/${experimentId}/pause`, { 
            method: 'POST',
            credentials: 'include'
        });
        if (response.ok) {
            alert('Experiment paused!');
            location.reload();
        } else {
            alert('Failed to pause experiment');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function resumeExperiment() {
    if (!confirm('Resume this experiment?')) return;
    
    try {
        const response = await fetch(`/api/experiments/${experimentId}/resume`, { 
            method: 'POST',
            credentials: 'include'
        });
        if (response.ok) {
            alert('Experiment resumed!');
            location.reload();
        } else {
            alert('Failed to resume experiment');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function endExperiment() {
    if (!confirm('End this experiment? This will stop accepting new participants and cannot be undone.')) return;
    
    try {
        const response = await fetch(`/api/experiments/${experimentId}/end`, { 
            method: 'POST',
            credentials: 'include'
        });
        if (response.ok) {
            alert('Experiment ended!');
            location.reload();
        } else {
            alert('Failed to end experiment');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function deleteExperiment() {
    const confirmMessage = `⚠️ WARNING: This action cannot be undone!\n\nDelete this experiment?\n\nThis will permanently remove:\n- Experiment configuration\n- All conditions\n- All associated sessions and data\n\nType "DELETE" to confirm:`;
    
    const userInput = prompt(confirmMessage);
    
    if (userInput !== 'DELETE') {
        if (userInput !== null) {
            alert('Deletion cancelled. You must type "DELETE" exactly to confirm.');
        }
        return;
    }
    
    try {
        const response = await fetch(`/api/experiments/${experimentId}/delete`, { 
            method: 'DELETE',
            credentials: 'include'
        });
        if (response.ok) {
            alert('✅ Experiment deleted successfully');
            window.location.href = '/admin';
        } else {
            alert('Failed to delete experiment');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// ========== Modal Management ==========

window.onclick = function(event) {
    const modal = document.getElementById('conditionModal');
    if (event.target === modal) {
        closeConditionModal();
    }
    const flowModal = document.getElementById('flowModal');
    if (event.target === flowModal) {
        closeFlowModal();
    }
}

// ========== Flow Editor ==========

async function editExperimentFlow() {
    currentEditingFlowConditionId = null;
    isEditingExperimentFlow = true;
    
    try {
        const response = await fetch(`/api/experiments`, {
            credentials: 'include'
        });
        const data = await response.json();
        const experiment = data.experiments.find(exp => exp.experiment_id === experimentId);
        
        if (experiment && experiment.experiment_flow && experiment.experiment_flow.length > 0) {
            experimentFlowSteps = experiment.experiment_flow.map(step => {
                if (step.survey_questions) {
                    return {
                        ...step,
                        survey_questions: step.survey_questions.map(q => typeof q === 'string' ? JSON.parse(q) : q)
                    };
                }
                return step;
            });
        } else {
            experimentFlowSteps = [];
        }
        
        renderSteps();
        document.getElementById('flowModal').querySelector('h2').textContent = '🔄 Experiment Flow Editor';
        document.getElementById('copyFlowSection').style.display = 'none'; // Hide copy button for experiment-level flow
        document.getElementById('flowModal').style.display = 'block';
        
    } catch (error) {
        alert('Failed to load experiment flow: ' + error.message);
    }
}

async function editConditionFlow(conditionId) {
    currentEditingFlowConditionId = conditionId;
    isEditingExperimentFlow = false;
    
    try {
        const response = await fetch(`/api/conditions/${conditionId}`, {
            credentials: 'include'
        });
        const condition = await response.json();
        
        if (condition.experiment_flow && condition.experiment_flow.length > 0) {
            experimentFlowSteps = condition.experiment_flow;
        } else {
            experimentFlowSteps = generateFlowFromLegacy(condition);
        }
        
        renderSteps();
        document.getElementById('flowModal').querySelector('h2').textContent = '🔄 Condition Flow Editor';
        document.getElementById('copyFlowSection').style.display = 'block'; // Show copy button for conditions
        document.getElementById('flowModal').style.display = 'block';
        
    } catch (error) {
        alert('Failed to load condition: ' + error.message);
    }
}

function generateFlowFromLegacy(condition) {
    const steps = [];
    
    if (condition.instruction_text) {
        steps.push({
            step_id: 'instruction',
            step_type: 'instruction',
            title: 'Experiment Instructions',
            content: condition.instruction_text,
            button_text: '開始する',
            required: true
        });
    }
    
    steps.push({
        step_id: 'chat',
        step_type: 'chat',
        time_limit_minutes: condition.time_limit_minutes || null,
        required: true
    });
    
    if (condition.survey_questions && condition.survey_questions.length > 0) {
        steps.push({
            step_id: 'survey',
            step_type: 'survey',
            title: condition.survey_title || 'アンケート',
            survey_description: condition.survey_description || '',
            survey_questions: condition.survey_questions,
            button_text: '送信',
            required: true
        });
    }
    
    return steps;
}

function closeFlowModal() {
    if (currentEditingStepIndex !== null) {
        if (!confirm('A step is currently being edited. Close without saving? (Unsaved step changes will be lost)')) {
            return;
        }
        closeStepEditModal();
    }
    
    document.getElementById('flowModal').style.display = 'none';
}

function renderSteps() {
    const container = document.getElementById('flowBlocksContainer');
    
    if (!container) {
        console.error('flowBlocksContainer not found');
        return;
    }
    
    if (experimentFlowSteps.length === 0) {
        container.innerHTML = '<p style="color: #999; text-align: center; padding: 30px;">No steps defined. Click "+ Add Block" below to add your first step.</p>';
        return;
    }
    
    container.innerHTML = experimentFlowSteps.map((step, index) => {
        const isRecallStep = step.step_id && step.step_id.startsWith('instruction_recall');
        const cardStyle = isRecallStep 
            ? 'background: #fff9e6; border: 2px solid #f39c12; border-radius: 6px; padding: 15px; margin-bottom: 10px; position: relative;'
            : 'background: white; border: 2px solid #ddd; border-radius: 6px; padding: 15px; margin-bottom: 10px; position: relative;';
        
        return `
        <div class="step-card" style="${cardStyle}">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span style="background: #3498db; color: white; padding: 4px 10px; border-radius: 4px; font-size: 0.85em; font-weight: 600;">
                            ${index + 1}
                        </span>
                        <span style="background: #9b59b6; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.85em;">
                            ${getStepTypeLabel(step.step_type)}
                        </span>
                        ${isRecallStep ? '<span style="background: #f39c12; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75em;">📌 Condition-Specific</span>' : ''}
                        ${step.title ? `<strong>${step.title}</strong>` : ''}
                    </div>
                    <div style="color: #666; font-size: 0.9em; margin-left: 45px;">
                        ${getStepPreview(step)}
                    </div>
                </div>
                <div style="display: flex; gap: 5px;">
                    ${index > 0 ? `<button class="btn btn-small" onclick="moveStepUp(${index})" style="padding: 4px 8px;">↑</button>` : ''}
                    ${index < experimentFlowSteps.length - 1 ? `<button class="btn btn-small" onclick="moveStepDown(${index})" style="padding: 4px 8px;">↓</button>` : ''}
                    <button class="btn btn-small btn-primary" onclick="editStep(${index})">Edit</button>
                    <button class="btn btn-small btn-danger" onclick="deleteStep(${index})">×</button>
                </div>
            </div>
        </div>
    `;
    }).join('');
}

function getStepTypeLabel(stepType) {
    const labels = {
        'consent': 'Consent',
        'instruction': 'Instruction',
        'survey': 'Survey',
        'chat': 'Chat',
        'ai_evaluation': 'AI Evaluation',
        'branch': 'Branch',
        'debriefing': 'Debriefing'
    };
    return labels[stepType] || stepType;
}

function getStepPreview(step) {
    switch(step.step_type) {
        case 'consent':
        case 'instruction':
        case 'debriefing':
            return step.content ? (step.content.substring(0, 100) + (step.content.length > 100 ? '...' : '')) : '(No content)';
        case 'survey':
            const qCount = step.survey_questions ? step.survey_questions.length : 0;
            return `${qCount} questions`;
        case 'chat':
            return step.time_limit_minutes ? `Time limit: ${step.time_limit_minutes} minutes` : 'No time limit';
        case 'ai_evaluation':
            const evalQCount = step.evaluation_questions ? step.evaluation_questions.length : 0;
            return `${evalQCount} questions • Model: ${step.evaluation_model || 'gemma2:9b'}`;
        default:
            return '';
    }
}

function addStep(stepType) {
    addStepAt(stepType, null);
}

function addStepAt(stepType, insertAtIndex) {
    const newStep = {
        step_id: `${stepType}_${Date.now()}`,
        step_type: stepType,
        required: true
    };
    
    switch(stepType) {
        case 'consent':
            newStep.title = 'Research Consent';
            newStep.content = '';
            newStep.button_text = 'I Agree';
            break;
        case 'instruction':
            newStep.title = 'Instructions';
            newStep.content = '';
            newStep.button_text = 'Next';
            break;
        case 'survey':
            newStep.title = 'Survey';
            newStep.survey_description = '';
            newStep.survey_questions = [];
            newStep.button_text = 'Submit';
            break;
        case 'chat':
            newStep.title = 'Chat Session';
            newStep.bot_name = 'AI Assistant';
            newStep.bot_model = '';
            newStep.system_prompt = '';
            newStep.time_limit_minutes = null;
            break;
        case 'ai_evaluation':
            newStep.title = 'AI Evaluation';
            newStep.evaluation_model = 'gemma2:9b';
            newStep.context_prompt = 'Please evaluate the following conversation objectively.';
            newStep.evaluation_questions = [
                {
                    question_id: 'sincerity',
                    text: 'Did the user engage sincerely in the conversation?'
                },
                {
                    question_id: 'richness',
                    text: 'Was the conversation content rich and meaningful?'
                }
            ];
            break;
        case 'branch':
            newStep.title = 'Conditional Branch';
            newStep.branches = [
                {
                    branch_id: `branch_${Date.now()}_1`,
                    condition_label: 'Branch A',
                    condition_type: 'random',  // デフォルトはランダム割り当て
                    condition_value: '',
                    weight: 1,  // ランダム割り当ての重み
                    steps: []
                }
            ];
            break;
        case 'debriefing':
            newStep.title = 'Thank you for participating';
            newStep.content = '';
            newStep.button_text = 'Finish';
            break;
    }
    
    // Insert at specific position or append to end
    if (insertAtIndex !== null && insertAtIndex >= 0 && insertAtIndex <= experimentFlowSteps.length) {
        experimentFlowSteps.splice(insertAtIndex, 0, newStep);
    } else {
        experimentFlowSteps.push(newStep);
    }
    
    renderSteps();
}

function deleteStep(index) {
    if (!confirm('Delete this step?')) return;
    
    if (currentEditingStepIndex !== null) {
        if (currentEditingStepIndex === index) {
            closeStepEditModal();
        } else if (currentEditingStepIndex > index) {
            currentEditingStepIndex--;
        }
    }
    
    experimentFlowSteps.splice(index, 1);
    renderSteps();
}

function moveStepUp(index) {
    if (index === 0) return;
    
    if (currentEditingStepIndex !== null) {
        if (currentEditingStepIndex === index) {
            currentEditingStepIndex = index - 1;
        } else if (currentEditingStepIndex === index - 1) {
            currentEditingStepIndex = index;
        }
    }
    
    const temp = experimentFlowSteps[index];
    experimentFlowSteps[index] = experimentFlowSteps[index - 1];
    experimentFlowSteps[index - 1] = temp;
    renderSteps();
}

function moveStepDown(index) {
    if (index === experimentFlowSteps.length - 1) return;
    
    if (currentEditingStepIndex !== null) {
        if (currentEditingStepIndex === index) {
            currentEditingStepIndex = index + 1;
        } else if (currentEditingStepIndex === index + 1) {
            currentEditingStepIndex = index;
        }
    }
    
    const temp = experimentFlowSteps[index];
    experimentFlowSteps[index] = experimentFlowSteps[index + 1];
    experimentFlowSteps[index + 1] = temp;
    renderSteps();
}

async function showCopyFlowDialog() {
    try {
        // 全条件を取得
        const response = await fetch(`/api/experiments/${experimentId}/conditions`, {
            credentials: 'include'
        });
        const data = await response.json();
        const conditions = data.conditions || [];
        
        // 現在編集中の条件を除外
        const otherConditions = conditions.filter(c => c.condition_id !== currentEditingFlowConditionId);
        
        if (otherConditions.length === 0) {
            alert('No other conditions to copy from. Create another condition first.');
            return;
        }
        
        // 条件選択ダイアログを表示
        let message = 'Select a condition to copy flow from:\n\n';
        otherConditions.forEach((c, idx) => {
            message += `${idx + 1}. ${c.name}\n`;
        });
        message += '\nEnter number (or cancel):';
        
        const input = prompt(message);
        if (!input) return;
        
        const index = parseInt(input) - 1;
        if (index < 0 || index >= otherConditions.length || isNaN(index)) {
            alert('Invalid selection');
            return;
        }
        
        const selectedCondition = otherConditions[index];
        
        // 確認
        if (!confirm(`Copy flow from "${selectedCondition.name}"?\n\nThis will replace your current flow.`)) {
            return;
        }
        
        // フローをコピー
        await copyFlowFromCondition(selectedCondition.condition_id);
        
    } catch (error) {
        alert('Failed to load conditions: ' + error.message);
    }
}

async function copyFlowFromCondition(sourceConditionId) {
    try {
        // ソース条件を取得
        const response = await fetch(`/api/conditions/${sourceConditionId}`, {
            credentials: 'include'
        });
        const sourceCondition = await response.json();
        
        // フローをコピー
        if (sourceCondition.experiment_flow && sourceCondition.experiment_flow.length > 0) {
            // ディープコピー
            experimentFlowSteps = JSON.parse(JSON.stringify(sourceCondition.experiment_flow));
        } else {
            // 旧形式から生成
            experimentFlowSteps = generateFlowFromLegacy(sourceCondition);
        }
        
        // 表示を更新
        renderSteps();
        
        alert(`✅ Flow copied from "${sourceCondition.name}"!\n\nYou can now customize the flow for this condition.`);
        
    } catch (error) {
        alert('Failed to copy flow: ' + error.message);
    }
}

async function saveFlow() {
    try {
        if (currentEditingStepIndex !== null) {
            if (!confirm('A step is currently being edited. Do you want to save the step and continue?')) {
                return;
            }
            await saveStepEdit();
        }
        
        if (isEditingExperimentFlow) {
            const response = await fetch(`/api/experiments`, {
                credentials: 'include'
            });
            const data = await response.json();
            const experiment = data.experiments.find(exp => exp.experiment_id === experimentId);
            
            if (!experiment) {
                alert('Experiment not found');
                return;
            }
            
            experiment.experiment_flow = experimentFlowSteps;
            
            const saveResponse = await fetch(`/api/experiments/${experimentId}/flow`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ experiment_flow: experimentFlowSteps })
            });
            
            if (saveResponse.ok) {
                alert('✅ Experiment flow saved successfully!');
                closeFlowModal();
                renderFlowPreview();
            } else {
                alert('Failed to save experiment flow');
            }
            
        } else if (currentEditingFlowConditionId) {
            const response = await fetch(`/api/conditions/${currentEditingFlowConditionId}`, {
                credentials: 'include'
            });
            const condition = await response.json();
            
            condition.experiment_flow = experimentFlowSteps;
            
            const saveResponse = await fetch(`/api/experiments/${experimentId}/conditions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(condition)
            });
            
            if (saveResponse.ok) {
                alert('✅ Condition flow saved successfully!');
                closeFlowModal();
                loadConditions();
            } else {
                alert('Failed to save condition flow');
            }
            
        } else {
            alert('No target selected for saving');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// ========== Global function exports ==========

// Copy all participant codes from the display
function copyAllParticipantCodes() {
    if (!window.currentDisplayedCodes || window.currentDisplayedCodes.length === 0) {
        alert('No participant codes to copy');
        return;
    }
    
    // Create CSV format: code,pin
    const csv = 'code,pin\n' + 
                window.currentDisplayedCodes
                    .map(item => `${item.code},${item.password || 'N/A'}`)
                    .join('\n');
    
    // Copy to clipboard
    navigator.clipboard.writeText(csv).then(() => {
        // Show temporary success message
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        btn.style.background = '#28a745';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '#6c757d';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
}

window.copyAllParticipantCodes = copyAllParticipantCodes;
window.showCodeManagementMenu = showCodeManagementMenu;
window.deleteParticipantCode = deleteParticipantCode;
window.deleteUnusedCodes = deleteUnusedCodes;
window.deleteAllCodes = deleteAllCodes;
window.closeManagementMenu = closeManagementMenu;

// Show code management menu
function showCodeManagementMenu() {
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 10000;';
    
    modal.innerHTML = `
        <div style="background: white; border-radius: 12px; padding: 25px; max-width: 400px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
            <h2 style="margin: 0 0 20px 0; color: #2c3e50;">⚙️ Manage Participant Codes</h2>
            
            <div style="margin-bottom: 20px;">
                <button onclick="deleteUnusedCodes()" 
                        style="width: 100%; padding: 12px; margin-bottom: 10px; background: #ff9800; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; text-align: left;">
                    🗑️ Delete Unused Codes
                    <div style="font-size: 11px; margin-top: 4px; opacity: 0.9;">Remove all codes that haven't been used yet</div>
                </button>
                
                <button onclick="deleteAllCodes()" 
                        style="width: 100%; padding: 12px; background: #dc3545; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; text-align: left;">
                    ⚠️ Delete All Codes
                    <div style="font-size: 11px; margin-top: 4px; opacity: 0.9;">Remove all codes (cannot be undone)</div>
                </button>
            </div>
            
            <div style="padding: 12px; background: #e7f3ff; border-radius: 6px; font-size: 12px; color: #0c5460; margin-bottom: 15px;">
                💡 <strong>Tip:</strong> You can delete individual unused codes by clicking the ✕ button next to each code.
            </div>
            
            <button onclick="closeManagementMenu()" 
                    style="width: 100%; padding: 10px; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                Close
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    window.currentManagementModal = modal;
}

function closeManagementMenu() {
    if (window.currentManagementModal) {
        document.body.removeChild(window.currentManagementModal);
        window.currentManagementModal = null;
    }
}

// Delete a single participant code
async function deleteParticipantCode(code) {
    if (!confirm(`Delete participant code "${code}"?\n\nThis cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/experiments/${experimentId}/codes/${code}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            await loadParticipantCodes();
            alert(`Code "${code}" deleted successfully!`);
        } else {
            const error = await response.json();
            alert(`Failed to delete code: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error deleting code:', error);
        alert('Error: ' + error.message);
    }
}

// Delete all unused codes
async function deleteUnusedCodes() {
    closeManagementMenu();
    
    console.log('[Delete] Starting deleteUnusedCodes...');
    console.log('[Delete] Experiment ID:', experimentId);
    
    if (!confirm('Delete ALL UNUSED participant codes?\n\nCodes that are in progress or completed will NOT be deleted.\n\nThis cannot be undone.')) {
        console.log('[Delete] User cancelled');
        return;
    }
    
    try {
        const url = `/api/experiments/${experimentId}/codes/unused`;
        console.log('[Delete] Calling:', url);
        
        const response = await fetch(url, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        console.log('[Delete] Response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('[Delete] Success! Deleted:', data.deleted_count, 'codes');
            await loadParticipantCodes();
            alert(`Deleted ${data.deleted_count} unused code(s) successfully!`);
        } else {
            const errorText = await response.text();
            console.error('[Delete] Error response:', errorText);
            try {
                const error = JSON.parse(errorText);
                alert(`Failed to delete codes: ${error.detail || 'Unknown error'}`);
            } catch {
                alert(`Failed to delete codes: ${errorText}`);
            }
        }
    } catch (error) {
        console.error('[Delete] Exception:', error);
        alert('Error: ' + error.message);
    }
}

// Delete all codes
async function deleteAllCodes() {
    closeManagementMenu();
    
    if (!confirm('⚠️ DELETE ALL PARTICIPANT CODES?\n\nThis will remove ALL codes including those in progress or completed.\n\nTHIS CANNOT BE UNDONE!\n\nType "DELETE" in the next prompt to confirm.')) {
        return;
    }
    
    const confirmation = prompt('Type "DELETE" to confirm:');
    if (confirmation !== 'DELETE') {
        alert('Deletion cancelled.');
        return;
    }
    
    try {
        const response = await fetch(`/api/experiments/${experimentId}/codes`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            await loadParticipantCodes();
            alert(`Deleted ${data.deleted_count} code(s) successfully!`);
        } else {
            const error = await response.json();
            alert(`Failed to delete codes: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error deleting codes:', error);
        alert('Error: ' + error.message);
    }
}

// ==================== Export Wide Format ====================
async function exportWideFormat() {
    console.log('[Export] Exporting wide format CSV...');
    
    try {
        const response = await fetch(`/api/experiments/${experimentId}/export/wide`, {
            method: 'POST',
            credentials: 'include'  // cookieを送信
        });
        
        if (response.status === 401) {
            alert('Session expired. Please login again.');
            window.location.href = '/admin/login';
            return;
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Export failed');
        }
        
        // CSVファイルをダウンロード
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // ファイル名をContent-Dispositionヘッダーから取得
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `wide_format_${experimentId}.csv`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename=(.+)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        console.log('[Export] Wide format CSV downloaded:', filename);
        
    } catch (error) {
        console.error('[Export] Error exporting wide format:', error);
        alert(`Failed to export wide format CSV: ${error.message}`);
    }
}

// Export functions to global scope for onclick handlers
window.addStep = addStep;
window.addStepAt = addStepAt;
window.deleteStep = deleteStep;
window.moveStepUp = moveStepUp;
window.moveStepDown = moveStepDown;
window.viewSession = viewSession;
window.exportSessionData = exportSessionData;
window.prepareParticipantInfo = prepareParticipantInfo;
window.copyAllParticipantCodes = copyAllParticipantCodes;
window.showCodeManagementMenu = showCodeManagementMenu;
window.closeManagementMenu = closeManagementMenu;
window.deleteParticipantCode = deleteParticipantCode;
window.deleteUnusedCodes = deleteUnusedCodes;
window.deleteAllCodes = deleteAllCodes;
window.openFlowModal = openFlowModal;
window.closeFlowModal = closeFlowModal;
window.saveFlow = saveFlow;
window.exportWideFormat = exportWideFormat;

console.log('✅ experiment_detail.js loaded (2024-11-16 - Wide Format Export)');

