// ========== Block-based Flow Editor (Finder-style Hierarchy) ==========
// Last updated: 2024-11-16 (Full-page editor support)

// Global state for collapsed branches
let collapsedBranches = new Set();

// Helper function: Get step type label
function getStepTypeLabel(stepType) {
    const labels = {
        'consent': 'Consent',
        'instruction': 'Instruction',
        'survey': 'Survey',
        'survey_randomizer': 'Randomizer',
        'chat': 'Chat',
        'ai_evaluation': 'AI Evaluation',
        'branch': 'Branch',
        'debriefing': 'Debriefing'
    };
    return labels[stepType] || stepType;
}

// Render flow as blocks
function renderFlowBlocks(steps = null, container = null) {
    // Allow passing custom steps and container (for full-page editor)
    const flowSteps = steps || experimentFlowSteps;
    const targetContainer = container || document.getElementById('flowBlocksContainer');
    
    if (!targetContainer) {
        console.error('[Flow Blocks] Container not found!');
        return;
    }
    
    if (!flowSteps || flowSteps.length === 0) {
        targetContainer.innerHTML = '<p style="color: #999; text-align: center; padding: 30px;">Click "+ Add Block" below to start building your flow</p>';
        return;
    }
    
    // Update global state if custom steps provided
    if (steps) {
        window.experimentFlowSteps = steps;
        window.currentFlow = steps;
    }
    
    targetContainer.innerHTML = flowSteps.map((step, index) => {
        if (step.step_type === 'branch') {
            return renderBranchBlock(step, index);
        } else {
            return renderNormalBlock(step, index);
        }
    }).join('');
    
    // Add drag and drop listeners
    addDragAndDropListeners();
}

// Render normal block
function renderNormalBlock(step, index) {
    const blockType = getBlockTypeDisplay(step.step_type);
    const blockIcon = getBlockIcon(step.step_type);
    const blockSummary = getBlockSummary(step);
    
    return `
        <div class="flow-block" draggable="true" data-index="${index}">
            <div class="flow-block-header">
                <span class="flow-block-type">
                    <span style="font-size: 16px;">${blockIcon}</span>
                    <span>${step.title || blockType}</span>
                </span>
                <span style="flex: 1;"></span>
                <div style="display: flex; gap: 6px; opacity: 0.6;">
                    ${index > 0 ? `<button onclick="moveStepUp(${index}); event.stopPropagation();" style="padding: 4px 10px; font-size: 11px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">↑</button>` : ''}
                    ${index < experimentFlowSteps.length - 1 ? `<button onclick="moveStepDown(${index}); event.stopPropagation();" style="padding: 4px 10px; font-size: 11px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">↓</button>` : ''}
                    <button onclick="editStep(${index}); event.stopPropagation();" style="padding: 4px 10px; font-size: 11px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">Edit</button>
                    <button onclick="deleteStep(${index}); event.stopPropagation();" style="padding: 4px 10px; font-size: 11px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #ef4444; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">×</button>
                </div>
            </div>
            ${blockSummary ? `<div class="flow-block-body">${blockSummary}</div>` : ''}
        </div>
    `;
}

// Render branch block (Finder-style hierarchy)
function renderBranchBlock(step, stepIndex) {
    const branches = step.branches || [];
    const isCollapsed = collapsedBranches.has(step.step_id);
    const flowSteps = window.currentFlow || window.experimentFlowSteps || [];
    
    let html = `
        <div class="flow-block branch-block" draggable="true" data-index="${stepIndex}">
            <div class="flow-block-header">
                <button onclick="toggleBranchCollapse('${step.step_id}'); event.stopPropagation();" style="background: none; border: none; cursor: pointer; padding: 0; font-size: 12px; color: #9ca3af; width: 20px; text-align: left; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
                    ${isCollapsed ? '▶' : '▼'}
                </button>
                <span class="flow-block-type">
                    <span style="font-size: 16px;">🔀</span>
                    <span>${step.title || 'Branch'}</span>
                </span>
                <span style="flex: 1;"></span>
                <div style="display: flex; gap: 6px; opacity: 0.6;">
                    ${stepIndex > 0 ? `<button onclick="moveStepUp(${stepIndex}); event.stopPropagation();" style="padding: 4px 10px; font-size: 11px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">↑</button>` : ''}
                    ${stepIndex < flowSteps.length - 1 ? `<button onclick="moveStepDown(${stepIndex}); event.stopPropagation();" style="padding: 4px 10px; font-size: 11px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">↓</button>` : ''}
                    <button onclick="addBranchPath(${stepIndex}); event.stopPropagation();" style="padding: 4px 10px; font-size: 11px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">+ Add</button>
                    <button onclick="editStep(${stepIndex}); event.stopPropagation();" style="padding: 4px 10px; font-size: 11px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">Edit</button>
                    <button onclick="deleteStep(${stepIndex}); event.stopPropagation();" style="padding: 4px 10px; font-size: 11px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #ef4444; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">×</button>
                </div>
            </div>
            ${!isCollapsed ? `
                <div class="branch-content">
                    ${branches.map((branch, branchIndex) => renderBranchPath(branch, stepIndex, branchIndex)).join('')}
                </div>
            ` : ''}
        </div>
    `;
    
    return html;
}

// Render a single branch path
function renderBranchPath(branch, stepIndex, branchIndex) {
    const isCollapsed = collapsedBranches.has(branch.branch_id);
    const steps = branch.steps || [];
    
    return `
        <div class="branch-path" style="margin-left: 20px; padding-left: 0; border-left: 1px solid #e5e7eb; margin-top: 0;">
            <div class="branch-path-header" style="display: flex; align-items: center; gap: 6px; padding: 8px 12px; background: transparent; border-bottom: 1px solid #e5e7eb; transition: background 0.12s ease;" onmouseover="this.style.background='#f9fafb'" onmouseout="this.style.background='transparent'">
                <button onclick="toggleBranchCollapse('${branch.branch_id}'); event.stopPropagation();" style="background: none; border: none; cursor: pointer; padding: 0; font-size: 11px; color: #9ca3af; width: 16px; text-align: left; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
                    ${isCollapsed ? '▶' : '▼'}
                </button>
                <span style="font-size: 13px; font-weight: 400; color: #374151; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">${branch.condition_label || 'Branch ' + (branchIndex + 1)}</span>
                <span style="font-size: 11px; color: #9ca3af; font-family: 'SF Mono', Monaco, monospace;">${getBranchConditionDisplay(branch)}</span>
                <div style="margin-left: auto; display: flex; gap: 4px; opacity: 0.6;">
                    <button onclick="addStepToBranch(${stepIndex}, ${branchIndex}); event.stopPropagation();" style="padding: 3px 8px; font-size: 10px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">+ Step</button>
                    <button onclick="editBranchPath(${stepIndex}, ${branchIndex}); event.stopPropagation();" style="padding: 3px 8px; font-size: 10px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">Edit</button>
                    <button onclick="deleteBranchPath(${stepIndex}, ${branchIndex}); event.stopPropagation();" style="padding: 3px 8px; font-size: 10px; background: transparent; border: 1px solid #d1d5db; border-radius: 4px; color: #ef4444; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;">×</button>
                </div>
            </div>
            ${!isCollapsed ? `
                <div class="branch-steps" style="margin-left: 0;">
                    ${steps.length > 0 ? steps.map((step, stepIdx) => renderBranchStep(step, stepIndex, branchIndex, stepIdx)).join('') : '<div style="color: #9ca3af; font-size: 11px; padding: 8px 12px 8px 32px; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">No steps</div>'}
                </div>
            ` : ''}
        </div>
    `;
}

// Render a step within a branch
function renderBranchStep(step, stepIndex, branchIndex, stepIdx) {
    const blockIcon = getBlockIcon(step.step_type);
    const blockType = getBlockTypeDisplay(step.step_type);
    
    return `
        <div class="branch-step" style="display: flex; align-items: center; gap: 8px; padding: 6px; background: white; border: 1px solid #e0e0e0; border-radius: 4px; margin-bottom: 4px; font-size: 13px;">
            <span>${blockIcon} ${blockType}</span>
            <span style="flex: 1; color: #555;">${step.title || 'Untitled'}</span>
            <button class="btn btn-small" onclick="editBranchStep(${stepIndex}, ${branchIndex}, ${stepIdx})" style="padding: 2px 8px; font-size: 11px;">Edit</button>
            <button class="btn btn-small btn-danger" onclick="deleteBranchStep(${stepIndex}, ${branchIndex}, ${stepIdx})" style="padding: 2px 8px; font-size: 11px;">×</button>
        </div>
    `;
}

// Get branch condition display
function getBranchConditionDisplay(branch) {
    if (branch.condition_type === 'random') {
        if (branch.weight) {
            return `Random (weight: ${branch.weight})`;
        }
        return 'Random assignment';
    } else if (branch.condition_value) {
        return branch.condition_value;
    } else {
        return 'Not configured';
    }
}

// Get block type display name
function getBlockTypeDisplay(type) {
    const types = {
        'consent': 'Consent Form',
        'instruction': 'Instructions',
        'survey': 'Survey',
        'chat': 'Chat Session',
        'branch': 'Conditional Branch',
        'debriefing': 'Debriefing'
    };
    return types[type] || type;
}

// Get block icon
function getBlockIcon(type) {
    const icons = {
        'consent': '📋',
        'instruction': '📝',
        'survey': '📊',
        'survey_randomizer': '🎲',
        'chat': '💬',
        'ai_evaluation': '🤖',
        'branch': '🔀',
        'debriefing': '🎓'
    };
    return icons[type] || '📄';
}

// Get block summary
function getBlockSummary(step) {
    switch (step.step_type) {
        case 'survey':
            const qCount = step.survey_questions ? step.survey_questions.length : 0;
            return `${qCount} question${qCount !== 1 ? 's' : ''}`;
        case 'chat':
            let summary = [];
            if (step.bot_name) summary.push(`Bot: ${step.bot_name}`);
            if (step.time_limit_minutes) summary.push(`${step.time_limit_minutes}分`);
            if (step.system_prompt) {
                const preview = step.system_prompt.substring(0, 50);
                summary.push(preview + (step.system_prompt.length > 50 ? '...' : ''));
            }
            return summary.length > 0 ? summary.join(' • ') : 'No settings';
        case 'ai_evaluation':
            const evalQCount = step.evaluation_questions ? step.evaluation_questions.length : 0;
            const evalModel = step.evaluation_model || 'gemma2:9b';
            return `${evalQCount} question${evalQCount !== 1 ? 's' : ''} • ${evalModel}`;
        case 'branch':
            const condType = step.condition_type || 'Not configured';
            return `Condition: ${condType}`;
        case 'instruction':
        case 'consent':
        case 'debriefing':
            if (step.content) {
                const preview = step.content.substring(0, 100);
                return preview + (step.content.length > 100 ? '...' : '');
            }
            return null;
        default:
            return null;
    }
}

// Show add block menu (at the end or at a specific position)
function showAddBlockMenu(insertAtIndex = null) {
    const isBranchContext = insertAtIndex === 'branch';
    const menuTitle = isBranchContext ? 'Add Step to Branch' : (insertAtIndex !== null && insertAtIndex !== 'branch' ? 'Insert Block' : 'Add Block');
    const onClickHandler = isBranchContext ? 'addStepToBranchAt' : 'addStepAt';
    
    const menu = `
        <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 10000;" onclick="this.remove()">
            <div style="background: white; border-radius: 12px; padding: 24px; max-width: 500px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);" onclick="event.stopPropagation()">
                <h3 style="margin: 0 0 20px 0; font-size: 18px; color: #2c3e50;">${menuTitle}</h3>
                <div style="display: grid; gap: 10px;">
                    <button onclick="${onClickHandler}('consent'${!isBranchContext ? ', ' + insertAtIndex : ''}); this.closest('[style*=\\'fixed\\']').remove();" style="padding: 14px; border: 2px solid #e0e0e0; background: white; border-radius: 8px; cursor: pointer; text-align: left; display: flex; align-items: center; gap: 12px; transition: all 0.2s;" onmouseover="this.style.borderColor='#2684FF'; this.style.background='#f0f7ff'" onmouseout="this.style.borderColor='#e0e0e0'; this.style.background='white'">
                        <span style="font-size: 24px;">📋</span>
                        <div>
                            <div style="font-weight: 600; color: #2c3e50;">Consent Form</div>
                            <div style="font-size: 12px; color: #666;">Informed consent document</div>
                        </div>
                    </button>
                    <button onclick="${onClickHandler}('instruction'${!isBranchContext ? ', ' + insertAtIndex : ''}); this.closest('[style*=\\'fixed\\']').remove();" style="padding: 14px; border: 2px solid #e0e0e0; background: white; border-radius: 8px; cursor: pointer; text-align: left; display: flex; align-items: center; gap: 12px; transition: all 0.2s;" onmouseover="this.style.borderColor='#2684FF'; this.style.background='#f0f7ff'" onmouseout="this.style.borderColor='#e0e0e0'; this.style.background='white'">
                        <span style="font-size: 24px;">📝</span>
                        <div>
                            <div style="font-weight: 600; color: #2c3e50;">Instructions</div>
                            <div style="font-size: 12px; color: #666;">Display instructions or prompts</div>
                        </div>
                    </button>
                    <button onclick="${onClickHandler}('survey'${!isBranchContext ? ', ' + insertAtIndex : ''}); this.closest('[style*=\\'fixed\\']').remove();" style="padding: 14px; border: 2px solid #e0e0e0; background: white; border-radius: 8px; cursor: pointer; text-align: left; display: flex; align-items: center; gap: 12px; transition: all 0.2s;" onmouseover="this.style.borderColor='#2684FF'; this.style.background='#f0f7ff'" onmouseout="this.style.borderColor='#e0e0e0'; this.style.background='white'">
                        <span style="font-size: 24px;">📊</span>
                        <div>
                            <div style="font-weight: 600; color: #2c3e50;">Survey</div>
                            <div style="font-size: 12px; color: #666;">Questionnaire or assessment</div>
                        </div>
                    </button>
                    <button onclick="${onClickHandler}('chat'${!isBranchContext ? ', ' + insertAtIndex : ''}); this.closest('[style*=\\'fixed\\']').remove();" style="padding: 14px; border: 2px solid #e0e0e0; background: white; border-radius: 8px; cursor: pointer; text-align: left; display: flex; align-items: center; gap: 12px; transition: all 0.2s;" onmouseover="this.style.borderColor='#2684FF'; this.style.background='#f0f7ff'" onmouseout="this.style.borderColor='#e0e0e0'; this.style.background='white'">
                        <span style="font-size: 24px;">💬</span>
                        <div>
                            <div style="font-weight: 600; color: #2c3e50;">Chat Session</div>
                            <div style="font-size: 12px; color: #666;">Interactive conversation with AI</div>
                        </div>
                    </button>
                    <button onclick="${onClickHandler}('ai_evaluation'${!isBranchContext ? ', ' + insertAtIndex : ''}); this.closest('[style*=\\'fixed\\']').remove();" style="padding: 14px; border: 2px solid #e0e0e0; background: white; border-radius: 8px; cursor: pointer; text-align: left; display: flex; align-items: center; gap: 12px; transition: all 0.2s;" onmouseover="this.style.borderColor='#2684FF'; this.style.background='#f0f7ff'" onmouseout="this.style.borderColor='#e0e0e0'; this.style.background='white'">
                        <span style="font-size: 24px;">🤖</span>
                        <div>
                            <div style="font-weight: 600; color: #2c3e50;">AI Evaluation</div>
                            <div style="font-size: 12px; color: #666;">Automatic chat quality analysis</div>
                        </div>
                    </button>
                    ${!isBranchContext ? `
                    <button onclick="${onClickHandler}('branch', ${insertAtIndex}); this.closest('[style*=\\'fixed\\']').remove();" style="padding: 14px; border: 2px solid #e74c3c; background: #fff5f5; border-radius: 8px; cursor: pointer; text-align: left; display: flex; align-items: center; gap: 12px; transition: all 0.2s;" onmouseover="this.style.borderColor='#e74c3c'; this.style.background='#ffe5e5'" onmouseout="this.style.borderColor='#e74c3c'; this.style.background='#fff5f5'">
                        <span style="font-size: 24px;">🔀</span>
                        <div>
                            <div style="font-weight: 600; color: #e74c3c;">Conditional Branch</div>
                            <div style="font-size: 12px; color: #c0392b;">Split flow based on conditions (Advanced)</div>
                        </div>
                    </button>
                    ` : ''}
                    <button onclick="${onClickHandler}('debriefing'${!isBranchContext ? ', ' + insertAtIndex : ''}); this.closest('[style*=\\'fixed\\']').remove();" style="padding: 14px; border: 2px solid #e0e0e0; background: white; border-radius: 8px; cursor: pointer; text-align: left; display: flex; align-items: center; gap: 12px; transition: all 0.2s;" onmouseover="this.style.borderColor='#2684FF'; this.style.background='#f0f7ff'" onmouseout="this.style.borderColor='#e0e0e0'; this.style.background='white'">
                        <span style="font-size: 24px;">🎓</span>
                        <div>
                            <div style="font-weight: 600; color: #2c3e50;">Debriefing</div>
                            <div style="font-size: 12px; color: #666;">Post-experiment information</div>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', menu);
}

// Show add block menu at a specific position
function showAddBlockMenuAt(index) {
    showAddBlockMenu(index);
}

// Drag and drop functionality
let draggedIndex = null;

function addDragAndDropListeners() {
    const blocks = document.querySelectorAll('.flow-block');
    
    blocks.forEach((block, index) => {
        block.addEventListener('dragstart', (e) => {
            draggedIndex = parseInt(block.dataset.index);
            block.style.opacity = '0.5';
        });
        
        block.addEventListener('dragend', (e) => {
            block.style.opacity = '1';
            draggedIndex = null;
        });
        
        block.addEventListener('dragover', (e) => {
            e.preventDefault();
            const targetIndex = parseInt(block.dataset.index);
            if (draggedIndex !== null && draggedIndex !== targetIndex) {
                block.style.borderTop = '3px solid #2684FF';
            }
        });
        
        block.addEventListener('dragleave', (e) => {
            block.style.borderTop = '';
        });
        
        block.addEventListener('drop', (e) => {
            e.preventDefault();
            block.style.borderTop = '';
            
            const targetIndex = parseInt(block.dataset.index);
            if (draggedIndex !== null && draggedIndex !== targetIndex) {
                // Reorder steps
                const flowSteps = window.currentFlow || window.experimentFlowSteps || [];
                const [removed] = flowSteps.splice(draggedIndex, 1);
                flowSteps.splice(targetIndex, 0, removed);
                
                // Update global state
                window.currentFlow = flowSteps;
                window.experimentFlowSteps = flowSteps;
                
                renderFlowBlocks(flowSteps);
                // Note: Auto-save happens on step edit, manual save on "Save Flow" button
            }
        });
    });
}

// Toggle branch collapse
function toggleBranchCollapse(branchId) {
    if (collapsedBranches.has(branchId)) {
        collapsedBranches.delete(branchId);
    } else {
        collapsedBranches.add(branchId);
    }
    renderFlowBlocks();
}

// Add a new branch path to a branch block
function addBranchPath(stepIndex) {
    const step = experimentFlowSteps[stepIndex];
    if (!step.branches) {
        step.branches = [];
    }
    
    const newBranch = {
        branch_id: `branch_${Date.now()}_${step.branches.length + 1}`,
        condition_label: `Branch ${String.fromCharCode(65 + step.branches.length)}`,
        condition_type: 'random',  // デフォルトはランダム割り当て
        condition_value: '',
        weight: 1,  // ランダム割り当ての重み
        steps: []
    };
    
    step.branches.push(newBranch);
    renderFlowBlocks();
}

// Delete a branch path
function deleteBranchPath(stepIndex, branchIndex) {
    if (!confirm('Delete this branch path and all its steps?')) return;
    
    const step = experimentFlowSteps[stepIndex];
    step.branches.splice(branchIndex, 1);
    renderFlowBlocks();
}

// Edit a branch path (label and condition)
function editBranchPath(stepIndex, branchIndex) {
    const step = experimentFlowSteps[stepIndex];
    const branch = step.branches[branchIndex];
    
    // Edit label
    const label = prompt('Branch label:', branch.condition_label);
    if (label !== null) {
        branch.condition_label = label;
    }
    
    // Select condition type
    const condTypeOptions = 'Condition type: "random" for random assignment, "condition_id" to branch by specific condition ID:';
    const condType = prompt(condTypeOptions, branch.condition_type || 'random');
    if (condType !== null) {
        branch.condition_type = condType;
    }
    
    // Different settings based on condition type
    if (branch.condition_type === 'random') {
        // For random assignment, set weight
        const weight = prompt('Assignment weight (number, default: 1):', branch.weight || 1);
        if (weight !== null) {
            branch.weight = parseInt(weight) || 1;
        }
        branch.condition_value = ''; // condition_value not needed for random
    } else if (branch.condition_type === 'condition_id') {
        // For condition_id branching
        const condValue = prompt('Condition ID (condition_id):', branch.condition_value);
        if (condValue !== null) {
            branch.condition_value = condValue;
        }
    }
    
    renderFlowBlocks();
}

// Add a step to a branch
function addStepToBranch(stepIndex, branchIndex) {
    window.currentBranchContext = { stepIndex, branchIndex };
    showAddBlockMenu('branch');
}

// Add step to branch (called from menu)
function addStepToBranchAt(stepType) {
    if (!window.currentBranchContext) return;
    
    const { stepIndex, branchIndex } = window.currentBranchContext;
    const step = experimentFlowSteps[stepIndex];
    const branch = step.branches[branchIndex];
    
    const newStep = createNewStep(stepType);
    branch.steps.push(newStep);
    
    window.currentBranchContext = null;
    renderFlowBlocks();
}

// Create a new step object
function createNewStep(stepType) {
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
        case 'survey_randomizer':
            newStep.title = 'Survey Randomizer';
            newStep.surveys = [
                {
                    survey_id: 'survey_1',
                    title: 'Survey 1',
                    survey_description: '',
                    survey_questions: [],
                    button_text: 'Next'
                },
                {
                    survey_id: 'survey_2',
                    title: 'Survey 2',
                    survey_description: '',
                    survey_questions: [],
                    button_text: 'Next'
                }
            ];
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
                    question_text: 'Did the user engage sincerely in the conversation?',
                    question_type: 'likert',
                    required: true,
                    scale: 7,
                    scale_labels: [],
                    min_label: '',
                    max_label: ''
                },
                {
                    question_id: 'richness',
                    question_text: 'Was the conversation content rich and meaningful?',
                    question_type: 'likert',
                    required: true,
                    scale: 7,
                    scale_labels: [],
                    min_label: '',
                    max_label: ''
                }
            ];
            break;
        case 'branch':
            newStep.title = 'Conditional Branch';
            newStep.branches = [
                {
                    branch_id: `branch_${Date.now()}_1`,
                    condition_label: 'Branch A',
                    condition_type: 'random',
                    condition_value: '',
                    weight: 1,
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
    
    return newStep;
}

// Edit a step within a branch
function editBranchStep(stepIndex, branchIndex, stepIdx) {
    const step = experimentFlowSteps[stepIndex];
    const branch = step.branches[branchIndex];
    const branchStep = branch.steps[stepIdx];
    
    window.currentEditingBranchContext = { stepIndex, branchIndex, stepIdx };
    currentEditingStepIndex = null; // Clear normal editing context
    
    // Use existing modal elements
    const modalTitle = document.getElementById('stepEditModalTitle');
    const stepEditForm = document.getElementById('stepEditForm');
    const stepEditModal = document.getElementById('stepEditModal');
    
    if (!modalTitle || !stepEditForm || !stepEditModal) {
        console.error('Step edit modal elements not found');
        alert('Error: Modal elements not found. Please refresh the page.');
        return;
    }
    
    modalTitle.textContent = `✏️ Edit ${getStepTypeLabel(branchStep.step_type)} Step (in Branch)`;
    stepEditForm.innerHTML = generateStepEditForm(branchStep);
    stepEditModal.style.display = 'block';
}

// Close branch step edit modal
function closeBranchStepEdit() {
    window.currentEditingBranchContext = null;
    closeStepEditModal(); // Use the standard close function
}

// Save branch step edit
async function saveBranchStepEdit() {
    await saveStepEdit();
    closeBranchStepEdit();
    renderFlowBlocks();
}

// Delete a step within a branch
function deleteBranchStep(stepIndex, branchIndex, stepIdx) {
    if (!confirm('Delete this step?')) return;
    
    const step = experimentFlowSteps[stepIndex];
    const branch = step.branches[branchIndex];
    branch.steps.splice(stepIdx, 1);
    renderFlowBlocks();
}

// Add step at specific position (for main flow)
function addStepAt(stepType, insertAtIndex) {
    const newStep = createNewStep(stepType);
    
    // For flow editor, get the current flow from window.currentFlow
    const flowSteps = window.currentFlow || window.experimentFlowSteps || [];
    
    // Insert at specific position or append to end
    if (insertAtIndex !== null && insertAtIndex >= 0 && insertAtIndex <= flowSteps.length) {
        flowSteps.splice(insertAtIndex, 0, newStep);
    } else {
        flowSteps.push(newStep);
    }
    
    // Update global state
    window.currentFlow = flowSteps;
    window.experimentFlowSteps = flowSteps;
    
    renderFlowBlocks(flowSteps);
}

// Delete step
function deleteStep(index) {
    if (!confirm('Delete this step?')) return;
    
    const flowSteps = window.currentFlow || window.experimentFlowSteps || [];
    flowSteps.splice(index, 1);
    
    // Update global state
    window.currentFlow = flowSteps;
    window.experimentFlowSteps = flowSteps;
    
    renderFlowBlocks(flowSteps);
}

// Move step up
function moveStepUp(index) {
    if (index === 0) return;
    
    const flowSteps = window.currentFlow || window.experimentFlowSteps || [];
    const [removed] = flowSteps.splice(index, 1);
    flowSteps.splice(index - 1, 0, removed);
    
    // Update global state
    window.currentFlow = flowSteps;
    window.experimentFlowSteps = flowSteps;
    
    renderFlowBlocks(flowSteps);
}

// Move step down
function moveStepDown(index) {
    const flowSteps = window.currentFlow || window.experimentFlowSteps || [];
    if (index === flowSteps.length - 1) return;
    
    const [removed] = flowSteps.splice(index, 1);
    flowSteps.splice(index + 1, 0, removed);
    
    // Update global state
    window.currentFlow = flowSteps;
    window.experimentFlowSteps = flowSteps;
    
    renderFlowBlocks(flowSteps);
}

// Override renderSteps to use block view
const originalRenderSteps = window.renderSteps;
window.renderSteps = function() {
    renderFlowBlocks();
};

// Export functions to global scope for onclick handlers
window.getStepTypeLabel = getStepTypeLabel;
window.renderFlowBlocks = renderFlowBlocks;
window.showAddBlockMenu = showAddBlockMenu;
window.showAddBlockMenuAt = showAddBlockMenuAt;
window.toggleBranchCollapse = toggleBranchCollapse;
window.addBranchPath = addBranchPath;
window.deleteBranchPath = deleteBranchPath;
window.editBranchPath = editBranchPath;
window.addStepToBranch = addStepToBranch;
window.addStepToBranchAt = addStepToBranchAt;
window.editBranchStep = editBranchStep;
window.saveBranchStepEdit = saveBranchStepEdit;
window.closeBranchStepEdit = closeBranchStepEdit;
window.deleteBranchStep = deleteBranchStep;
window.addStepAt = addStepAt;
window.deleteStep = deleteStep;
window.moveStepUp = moveStepUp;
window.moveStepDown = moveStepDown;
// Note: editStep is exported by experiment_detail_step_editor.js

console.log('✅ Finder-style hierarchy flow editor loaded');
console.log('✅ experiment_flow_blocks.js loaded (2024-11-16 - AI Evaluation + Global Scope)');
