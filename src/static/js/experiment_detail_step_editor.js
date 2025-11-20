// Step Editor Functions for Experiment Detail Page
// Survey question management and step editing

function getInputValueOrFallback(elementId, fallback = '') {
    const el = document.getElementById(elementId);
    if (!el) {
        console.warn(`[StepEditor] Element #${elementId} not found, using fallback.`);
        return fallback;
    }
    const value = el.value != null ? el.value : '';
    return typeof value === 'string' ? value.trim() : value;
}

function getCheckboxValueOrFallback(elementId, fallback = false) {
    const el = document.getElementById(elementId);
    if (!el) {
        console.warn(`[StepEditor] Checkbox #${elementId} not found, using fallback.`);
        return fallback;
    }
    return !!el.checked;
}

function getNumberValueOrFallback(elementId, fallback = null) {
    const el = document.getElementById(elementId);
    if (!el) {
        console.warn(`[StepEditor] Numeric input #${elementId} not found, using fallback.`);
        return fallback;
    }
    const value = parseInt(el.value, 10);
    return Number.isNaN(value) ? fallback : value;
}

function editStep(index) {
    currentEditingStepIndex = index;
    const step = experimentFlowSteps[index];
    
    const modalTitle = document.getElementById('stepEditModalTitle');
    const stepEditForm = document.getElementById('stepEditForm');
    const stepEditModal = document.getElementById('stepEditModal');
    
    if (!modalTitle || !stepEditForm || !stepEditModal) {
        console.error('Step edit modal elements not found:', {
            modalTitle: !!modalTitle,
            stepEditForm: !!stepEditForm,
            stepEditModal: !!stepEditModal
        });
        alert('Error: Modal elements not found. Please refresh the page.');
        return;
    }
    
    modalTitle.textContent = `✏️ Edit ${getStepTypeLabel(step.step_type)} Step`;
    
    const formHtml = generateStepEditForm(step);
    stepEditForm.innerHTML = formHtml;
    
    stepEditModal.style.display = 'block';
}

function closeStepEditModal() {
    document.getElementById('stepEditModal').style.display = 'none';
    currentEditingStepIndex = null;
}

function generateStepEditForm(step) {
    const stepType = step.step_type;
    
    switch(stepType) {
        case 'consent':
            return `
                <div class="form-group">
                    <label>Title</label>
                    <input type="text" id="edit_title" class="form-control" value="${escapeHtml(step.title || '')}" placeholder="e.g., Research Consent">
                </div>
                <div class="form-group">
                    <label>Content (Plain Text)</label>
                    <textarea id="edit_content" class="form-control" rows="10" placeholder="Enter consent text here...">${escapeHtml(step.content || '')}</textarea>
                    <div class="form-hint">Plain text only. Line breaks will be preserved.</div>
                </div>
                <div class="form-group">
                    <label>Button Text</label>
                    <input type="text" id="edit_button_text" class="form-control" value="${escapeHtml(step.button_text || 'I Agree')}" placeholder="I Agree">
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="edit_required" ${step.required ? 'checked' : ''}>
                        Required (participant must complete this step)
                    </label>
                </div>
            `;
            
        case 'instruction':
            return `
                <div class="form-group">
                    <label>Title</label>
                    <input type="text" id="edit_title" class="form-control" value="${escapeHtml(step.title || '')}" placeholder="e.g., Instructions">
                </div>
                <div class="form-group">
                    <label>Content (Plain Text)</label>
                    <textarea id="edit_content" class="form-control" rows="10" placeholder="Enter instructions here...">${escapeHtml(step.content || '')}</textarea>
                    <div class="form-hint">Plain text only. Line breaks will be preserved.</div>
                </div>
                <div class="form-group">
                    <label>Button Text</label>
                    <input type="text" id="edit_button_text" class="form-control" value="${escapeHtml(step.button_text || 'Next')}" placeholder="Next">
                </div>
                <div class="form-group">
                    <label>Minimum Display Time (seconds)</label>
                    <input type="number" id="edit_min_display_seconds" class="form-control" value="${step.min_display_seconds || ''}" placeholder="Leave empty for no time limit" min="0">
                    <div class="form-hint">Optional: Number of seconds to wait before showing the button (e.g., 40)</div>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="edit_show_timer" ${step.show_timer ? 'checked' : ''}>
                        Show countdown timer
                    </label>
                    <div class="form-hint">If unchecked, the button will appear silently after the time limit without showing a countdown</div>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="edit_required" ${step.required ? 'checked' : ''}>
                        Required
                    </label>
                </div>
            `;
            
        case 'debriefing':
            return `
                <div class="form-group">
                    <label>Title</label>
                    <input type="text" id="edit_title" class="form-control" value="${escapeHtml(step.title || '')}" placeholder="e.g., Thank you for participating">
                </div>
                <div class="form-group">
                    <label>Content (Plain Text)</label>
                    <textarea id="edit_content" class="form-control" rows="10" placeholder="Enter debriefing text here...">${escapeHtml(step.content || '')}</textarea>
                    <div class="form-hint">Plain text only. Line breaks will be preserved.</div>
                </div>
                <div class="form-group">
                    <label>Button Text</label>
                    <input type="text" id="edit_button_text" class="form-control" value="${escapeHtml(step.button_text || 'Finish')}" placeholder="Finish">
                </div>
            `;
            
        case 'chat':
            // Load models asynchronously
            setTimeout(() => loadModelsForChatStep(step.bot_model || ''), 0);
            
            return `
                <div class="form-group">
                    <label>Chat Title</label>
                    <input type="text" id="edit_chat_title" class="form-control" value="${escapeHtml(step.title || 'Chat Session')}" placeholder="e.g., Chat with AI">
                </div>
                <div class="form-group">
                    <label>Instruction Text (Optional)</label>
                    <textarea id="edit_instruction_text" class="form-control" rows="3" placeholder="e.g., 相談を始めてください。">${escapeHtml(step.instruction_text || '')}</textarea>
                    <div class="form-hint">Optional: Instruction message displayed when chat starts (e.g., "Please start your consultation.")</div>
                </div>
                <div class="form-group">
                    <label>Bot Name</label>
                    <input type="text" id="edit_bot_name" class="form-control" value="${escapeHtml(step.bot_name || 'AI Assistant')}" placeholder="e.g., Counselor AI">
                    <div class="form-hint">The name displayed for the AI in the chat interface</div>
                </div>
                <div class="form-group">
                    <label>Bot Model</label>
                    <select id="edit_bot_model" class="form-control">
                        <option value="">Loading models...</option>
                    </select>
                    <div class="form-hint">Ollama model to use for this chat session</div>
                </div>
                <div class="form-group">
                    <label>System Prompt</label>
                    <textarea id="edit_system_prompt" class="form-control" rows="8" placeholder="You are a helpful assistant...">${escapeHtml(step.system_prompt || '')}</textarea>
                    <div class="form-hint">Defines the AI's behavior and personality</div>
                </div>
                <div class="form-group">
                    <label>Temperature</label>
                    <input type="number" id="edit_temperature" class="form-control" value="${step.temperature !== undefined ? step.temperature : 0.7}" placeholder="0.7" min="0" max="2" step="0.1">
                    <div class="form-hint">Controls randomness (0.0 = deterministic, 1.0 = creative, default: 0.7)</div>
                </div>
                <div class="form-group">
                    <label>Top P (Nucleus Sampling)</label>
                    <input type="number" id="edit_top_p" class="form-control" value="${step.top_p !== undefined ? step.top_p : 0.9}" placeholder="0.9" min="0" max="1" step="0.05">
                    <div class="form-hint">Cumulative probability threshold (default: 0.9)</div>
                </div>
                <div class="form-group">
                    <label>Top K</label>
                    <input type="number" id="edit_top_k" class="form-control" value="${step.top_k !== undefined ? step.top_k : 40}" placeholder="40" min="1" max="100" step="1">
                    <div class="form-hint">Number of top tokens to consider (default: 40)</div>
                </div>
                <div class="form-group">
                    <label>Repeat Penalty</label>
                    <input type="number" id="edit_repeat_penalty" class="form-control" value="${step.repeat_penalty !== undefined ? step.repeat_penalty : 1.1}" placeholder="1.1" min="1" max="2" step="0.1">
                    <div class="form-hint">Prevents repetition (1.0 = no penalty, 2.0 = strong penalty, default: 1.1)</div>
                </div>
                <div class="form-group">
                    <label>Max Tokens (num_predict)</label>
                    <input type="number" id="edit_num_predict" class="form-control" value="${step.num_predict || ''}" placeholder="Leave empty for no limit" min="10" step="10">
                    <div class="form-hint">Maximum number of tokens to generate (optional, may truncate responses)</div>
                </div>
                <div class="form-group">
                    <label>CPU Threads (num_thread)</label>
                    <input type="number" id="edit_num_thread" class="form-control" value="${step.num_thread || ''}" placeholder="Default: 8 (M4 optimized)" min="1" max="16" step="1">
                    <div class="form-hint">Number of CPU threads (default: 8 for M4, leave empty for auto)</div>
                </div>
                <div class="form-group">
                    <label>Context Length (num_ctx)</label>
                    <input type="number" id="edit_num_ctx" class="form-control" value="${step.num_ctx || ''}" placeholder="Default: 8192" min="512" max="32768" step="512">
                    <div class="form-hint">Context window size (default: 8192, leave empty for auto)</div>
                </div>
                <div class="form-group">
                    <label>GPU Layers (num_gpu)</label>
                    <input type="number" id="edit_num_gpu" class="form-control" value="${step.num_gpu !== undefined ? step.num_gpu : ''}" placeholder="Default: -1 (all layers)" min="-1" max="100" step="1">
                    <div class="form-hint">Number of GPU layers (-1 = all, default: -1 for M4 Neural Engine, leave empty for auto)</div>
                </div>
                <div class="form-group">
                    <label>Batch Size (num_batch)</label>
                    <input type="number" id="edit_num_batch" class="form-control" value="${step.num_batch || ''}" placeholder="Default: 512" min="1" max="2048" step="32">
                    <div class="form-hint">Batch processing size (default: 512, leave empty for auto)</div>
                </div>
                <div class="form-group">
                    <label>Time Limit (minutes)</label>
                    <input type="number" id="edit_time_limit" class="form-control" value="${step.time_limit_minutes || ''}" placeholder="Leave empty for no time limit" min="1">
                    <div class="form-hint">Optional: Time limit for the chat session</div>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="edit_required" ${step.required ? 'checked' : ''}>
                        Required
                    </label>
                </div>
            `;
        
        case 'branch':
            return `
                <div class="form-group">
                    <label>Branch Block Title</label>
                    <input type="text" id="edit_title" class="form-control" value="${escapeHtml(step.title || 'Conditional Branch')}" placeholder="e.g., Condition Assignment">
                </div>
                <div class="form-group" style="background: #e8f4fd; padding: 15px; border-radius: 6px; border-left: 4px solid #2684FF;">
                    <strong>ℹ️ Branch Structure:</strong>
                    <div style="margin-top: 10px; font-size: 13px; color: #555;">
                        This branch block contains ${step.branches ? step.branches.length : 0} branch path(s).
                        Each branch can have its own steps that will be executed based on the participant's condition.
                        <br><br>
                        Use the "+ Add Branch" button in the flow editor to add more branch paths.
                    </div>
                </div>
            `;
            
        case 'survey':
            return generateSurveyEditForm(step);
            
        case 'survey_randomizer':
            return generateSurveyRandomizerEditForm(step);
            
        case 'ai_evaluation':
            return generateAIEvaluationEditForm(step);
            
        default:
            return '<p>Unknown step type</p>';
    }
}

function generateAIEvaluationEditForm(step) {
    const questions = step.evaluation_questions || [];
    
    // Convert old format to new format if needed
    const normalizedQuestions = questions.map(q => {
        if (!q.question_type) {
            return {
                question_id: q.question_id || `eval_${Date.now()}`,
                question_text: q.text || '',
                question_type: 'likert',
                required: true,
                scale: 7
            };
        }
        return q;
    });
    
    // Load models asynchronously
    setTimeout(() => loadModelsForEvaluationStep(step.evaluation_model || ''), 0);
    
    return `
        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <h4 style="margin: 0 0 10px 0; font-size: 1em; color: #856404;">⚠️ プレイスホルダー</h4>
            <div style="font-size: 0.9em; color: #856404; line-height: 1.6;">
                <p style="margin: 0;">AI評価機能は現在プレイスホルダーです。実際のAI評価は行われず、参加者は「次へ」ボタンを押して次のステップに進みます。</p>
                <p style="margin: 10px 0 0 0;">設定は保存されますが、実行時には使用されません。</p>
            </div>
        </div>
        
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="edit_title" class="form-control" value="${escapeHtml(step.title || 'AI Evaluation')}" placeholder="e.g., AI Evaluation">
        </div>
        <div class="form-group" style="opacity: 0.6; pointer-events: none;">
            <label>Evaluation Model</label>
            <select id="edit_evaluation_model" class="form-control">
                <option value="">Loading models...</option>
            </select>
            <div class="form-hint" style="color: #999;">（プレイスホルダー: 使用されません）</div>
        </div>
        <div class="form-group" style="opacity: 0.6; pointer-events: none;">
            <label>Context Prompt</label>
            <textarea id="edit_context_prompt" class="form-control" rows="4" placeholder="Context for the AI evaluator...">${escapeHtml(step.context_prompt || 'Please evaluate the following conversation objectively.')}</textarea>
            <div class="form-hint" style="color: #999;">（プレイスホルダー: 使用されません）</div>
        </div>
        <div class="form-group">
            <label>
                <input type="checkbox" id="edit_required" ${step.required ? 'checked' : ''}>
                Required Step
            </label>
        </div>
        
        <hr style="margin: 20px 0;">
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h4 style="margin: 0;">Evaluation Questions</h4>
            <button type="button" class="btn btn-small btn-success" onclick="addEvaluationQuestion()" style="opacity: 0.6; pointer-events: none; cursor: not-allowed;">+ Add Question</button>
        </div>
        
        <div id="evaluationQuestionsContainer" style="opacity: 0.6;">
            ${normalizedQuestions.length === 0 ? '<p style="color: #999; text-align: center; padding: 20px;">No questions yet. Click "Add Question" to create one.</p>' : ''}
            ${normalizedQuestions.map((q, idx) => generateEvaluationQuestionEditHtml(q, idx)).join('')}
        </div>
    `;
}

function generateSurveyRandomizerEditForm(step) {
    // Support both 'surveys' (legacy) and 'steps' (new)
    const items = step.steps || step.surveys || [];
    
    // Initialize global state for randomizer editing
    window.currentEditingRandomizerItems = items;
    window.currentEditingRandomizerItemIndex = null;
    
    return `
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="edit_title" class="form-control" value="${escapeHtml(step.title || '')}" placeholder="e.g., Randomizer">
        </div>
        <div class="form-group">
            <label>
                <input type="checkbox" id="edit_required" ${step.required ? 'checked' : ''}>
                Required
            </label>
        </div>
        
        <hr style="margin: 20px 0;">
        
        <div style="background: #e8f4fd; padding: 15px; border-radius: 6px; border-left: 4px solid #2684FF; margin-bottom: 20px;">
            <strong>ℹ️ Randomizer:</strong>
            <div style="margin-top: 10px; font-size: 13px; color: #555;">
                This step will display multiple items (surveys, instructions, etc.) in a random order. All items will be shown to the participant.
            </div>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h4 style="margin: 0;">Items (${items.length})</h4>
            <div style="display: flex; gap: 10px;">
                <button type="button" class="btn btn-small btn-success" onclick="addItemToRandomizer('survey')">+ Survey</button>
                <button type="button" class="btn btn-small btn-success" onclick="addItemToRandomizer('instruction')">+ Instruction</button>
            </div>
        </div>
        
        <div id="randomizerItemsListContainer">
            ${items.length === 0 ? '<p style="color: #999; text-align: center; padding: 20px;">No items yet. Click a button above to add one.</p>' : ''}
            ${items.map((item, idx) => generateRandomizerItemCardHtml(item, idx)).join('')}
        </div>
    `;
}

function generateRandomizerItemCardHtml(item, index) {
    // Determine item type
    const itemType = item.step_type || (item.survey_questions ? 'survey' : 'unknown');
    
    // Get type icon and color
    const typeIcons = {
        'survey': '📊',
        'instruction': '📝',
        'consent': '📋',
        'chat': '💬',
        'debriefing': '🎓'
    };
    const typeColors = {
        'survey': '#3b82f6',
        'instruction': '#10b981',
        'consent': '#f59e0b',
        'chat': '#8b5cf6',
        'debriefing': '#06b6d4'
    };
    
    const icon = typeIcons[itemType] || '📄';
    const color = typeColors[itemType] || '#6b7280';
    
    // Get item details based on type
    let details = '';
    if (itemType === 'survey') {
        const numQuestions = item.survey_questions ? item.survey_questions.length : 0;
        details = `${numQuestions} question${numQuestions !== 1 ? 's' : ''}`;
    } else if (itemType === 'instruction') {
        const contentLength = item.content ? item.content.length : 0;
        details = `${contentLength} characters`;
    }
    
    const title = item.title || 'Untitled';
    const description = item.survey_description || item.content ? (item.content ? item.content.substring(0, 50) + '...' : '') : '';
    
    return `
        <div class="randomizer-item-card" style="border: 2px solid ${color}; padding: 15px; margin-bottom: 15px; border-radius: 8px; background: #f8fafc;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 20px;">${icon}</span>
                        <strong style="font-size: 16px; color: ${color};">${escapeHtml(title)}</strong>
                    </div>
                    <div style="font-size: 13px; color: #64748b; margin-top: 5px;">
                        Type: ${itemType} ${details ? `• ${details}` : ''}
                    </div>
                    ${description ? `<div style="font-size: 13px; color: #475569; margin-top: 8px; font-style: italic;">"${escapeHtml(description)}"</div>` : ''}
                </div>
                <div style="display: flex; gap: 6px;">
                    <button type="button" class="btn btn-small" onclick="editItemInRandomizer(${index})" style="background: ${color}; color: white;">Edit</button>
                    <button type="button" class="btn btn-small btn-danger" onclick="removeItemFromRandomizer(${index})">Delete</button>
                </div>
            </div>
        </div>
    `;
}

// Legacy function for backward compatibility
function generateSurveyCardHtml(survey, index) {
    survey.step_type = 'survey';
    return generateRandomizerItemCardHtml(survey, index);
}

function generateSurveyEditForm(step) {
    const questions = step.survey_questions || [];
    
    return `
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="edit_title" class="form-control" value="${escapeHtml(step.title || '')}" placeholder="e.g., Survey">
        </div>
        <div class="form-group">
            <label>Description (Optional)</label>
            <textarea id="edit_survey_description" class="form-control" rows="3" placeholder="Brief description of the survey...">${escapeHtml(step.survey_description || '')}</textarea>
        </div>
        <div class="form-group">
            <label>Button Text</label>
            <input type="text" id="edit_button_text" class="form-control" value="${escapeHtml(step.button_text || 'Submit')}" placeholder="Submit">
        </div>
        <div class="form-group">
            <label>
                <input type="checkbox" id="edit_required" ${step.required ? 'checked' : ''}>
                Required
            </label>
        </div>
        <div class="form-group">
            <label>
                <input type="checkbox" id="edit_randomize_questions" ${step.randomize_questions ? 'checked' : ''}>
                Randomize question order
            </label>
            <div class="form-hint">If checked, questions will be displayed in a random order for each participant</div>
        </div>
        
        <hr style="margin: 20px 0;">
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h4 style="margin: 0;">Survey Questions</h4>
            <button type="button" class="btn btn-small btn-success" onclick="addSurveyQuestion()">+ Add Question</button>
        </div>
        
        <div id="surveyQuestionsContainer">
            ${questions.length === 0 ? '<p style="color: #999; text-align: center; padding: 20px;">No questions yet. Click "Add Question" to create one.</p>' : ''}
            ${questions.map((q, idx) => generateQuestionEditHtml(q, idx)).join('')}
        </div>
    `;
}

function generateEvaluationQuestionEditHtml(question, index) {
    // AI evaluation questions are always Likert scale
    const scale = question.scale || 7;
    
    return `
        <div class="question-edit-card" style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 6px; background: #f9f9f9;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong>Question ${index + 1}</strong>
                <button type="button" class="btn btn-small btn-danger" onclick="removeEvaluationQuestion(${index})">🗑 Delete</button>
            </div>
            <div class="form-group">
                <label>Question ID <span style="color: #999; font-size: 0.85em;">(for data analysis)</span></label>
                <input type="text" id="eval_q_id_${index}" class="form-control" value="${escapeHtml(question.question_id || '')}" placeholder="e.g., sincerity" required>
            </div>
            <div class="form-group">
                <label>Question Text</label>
                <input type="text" id="eval_q_text_${index}" class="form-control" value="${escapeHtml(question.question_text || question.text || '')}" required>
            </div>
            <div class="form-group">
                <label>Scale Points</label>
                <select id="eval_q_scale_${index}" class="form-control">
                    <option value="3" ${scale === 3 ? 'selected' : ''}>3-point scale</option>
                    <option value="4" ${scale === 4 ? 'selected' : ''}>4-point scale</option>
                    <option value="5" ${scale === 5 ? 'selected' : ''}>5-point scale</option>
                    <option value="6" ${scale === 6 ? 'selected' : ''}>6-point scale</option>
                    <option value="7" ${scale === 7 ? 'selected' : ''}>7-point scale</option>
                    <option value="9" ${scale === 9 ? 'selected' : ''}>9-point scale</option>
                    <option value="10" ${scale === 10 ? 'selected' : ''}>10-point scale</option>
                </select>
                <div class="form-hint">ラベルは説明文に記載してください。</div>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="eval_q_required_${index}" ${question.required !== false ? 'checked' : ''}>
                    Required
                </label>
            </div>
        </div>
    `;
}

function generateQuestionEditHtml(question, index) {
    const questionTypeOptions = `
        <option value="text" ${question.question_type === 'text' ? 'selected' : ''}>Text (Short Answer)</option>
        <option value="textarea" ${question.question_type === 'textarea' ? 'selected' : ''}>Textarea (Long Answer)</option>
        <option value="radio" ${question.question_type === 'radio' ? 'selected' : ''}>Radio (Single Choice)</option>
        <option value="checkbox" ${question.question_type === 'checkbox' ? 'selected' : ''}>Checkbox (Multiple Choice)</option>
        <option value="likert" ${question.question_type === 'likert' || question.question_type === 'scale' ? 'selected' : ''}>Likert Scale</option>
    `;
    
    const needsOptions = ['radio', 'checkbox'].includes(question.question_type);
    const isLikert = question.question_type === 'likert' || question.question_type === 'scale';
    const isText = question.question_type === 'text';
    
    let optionsHtml = '';
    
    if (isText) {
        const inputType = question.input_type || 'text';
        optionsHtml = `
            <div class="form-group">
                <label>Input Type</label>
                <select id="q_input_type_${index}" class="form-control">
                    <option value="text" ${inputType === 'text' ? 'selected' : ''}>Text (any characters)</option>
                    <option value="number" ${inputType === 'number' ? 'selected' : ''}>Number (digits only)</option>
                    <option value="email" ${inputType === 'email' ? 'selected' : ''}>Email</option>
                    <option value="tel" ${inputType === 'tel' ? 'selected' : ''}>Phone</option>
                    <option value="url" ${inputType === 'url' ? 'selected' : ''}>URL</option>
                </select>
                <div class="form-hint">HTML5 input type for validation</div>
            </div>
        `;
    } else if (needsOptions) {
        optionsHtml = `
            <div class="form-group">
                <label>Options (comma-separated)</label>
                <input type="text" id="q_options_${index}" class="form-control" value="${escapeHtml((question.options || []).join(', '))}" placeholder="Option 1, Option 2, Option 3">
            </div>
        `;
    } else if (isLikert) {
        const scale = question.scale || question.likert_scale || 5;
        
        optionsHtml = `
            <div class="form-group">
                <label>Scale Points</label>
                <select id="q_scale_${index}" class="form-control">
                    <option value="3" ${scale === 3 ? 'selected' : ''}>3-point scale</option>
                    <option value="4" ${scale === 4 ? 'selected' : ''}>4-point scale</option>
                    <option value="5" ${scale === 5 ? 'selected' : ''}>5-point scale</option>
                    <option value="6" ${scale === 6 ? 'selected' : ''}>6-point scale</option>
                    <option value="7" ${scale === 7 ? 'selected' : ''}>7-point scale</option>
                    <option value="9" ${scale === 9 ? 'selected' : ''}>9-point scale</option>
                    <option value="10" ${scale === 10 ? 'selected' : ''}>10-point scale</option>
                </select>
                <div class="form-hint">ラベルは説明文（survey_description）に記載してください。</div>
            </div>
        `;
    }
    
    return `
        <div class="question-edit-card" style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 6px; background: #f9f9f9;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong>Question ${index + 1}</strong>
                <button type="button" class="btn btn-small btn-danger" onclick="removeSurveyQuestion(${index})">🗑 Delete</button>
            </div>
            <div class="form-group">
                <label>Question ID <span style="color: #999; font-size: 0.85em;">(for data analysis)</span></label>
                <input type="text" id="q_id_${index}" class="form-control" value="${escapeHtml(question.question_id || '')}" placeholder="e.g., panas_pre_1" required>
            </div>
            <div class="form-group">
                <label>Question Text</label>
                <input type="text" id="q_text_${index}" class="form-control" value="${escapeHtml(question.question_text)}" required>
            </div>
            <div class="form-group">
                <label>Question Type</label>
                <select id="q_type_${index}" class="form-control" onchange="updateQuestionOptions(${index})">
                    ${questionTypeOptions}
                </select>
            </div>
            <div id="q_options_container_${index}">
                ${optionsHtml}
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="q_required_${index}" ${question.required ? 'checked' : ''}>
                    Required
                </label>
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function loadModelsForChatStep(currentModel) {
    const select = document.getElementById('edit_bot_model');
    if (!select) return;
    
    try {
        const response = await fetch('/api/ollama/models', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            select.innerHTML = '<option value="">❌ Failed to load models</option>';
            return;
        }
        
        const data = await response.json();
        const models = data.models || [];
        
        if (models.length === 0) {
            select.innerHTML = '<option value="">⚠️ No Ollama models installed</option>';
            return;
        }
        
        // Build options
        select.innerHTML = '<option value="">-- Select a model --</option>' + 
            models.map(model => `<option value="${model}" ${model === currentModel ? 'selected' : ''}>${model}</option>`).join('');
        
        // If current model is not in the list, add it
        if (currentModel && !models.includes(currentModel)) {
            const option = document.createElement('option');
            option.value = currentModel;
            option.textContent = `${currentModel} (not available)`;
            option.selected = true;
            select.appendChild(option);
        }
        
    } catch (error) {
        console.error('Failed to load models:', error);
        select.innerHTML = '<option value="">❌ Network error</option>';
    }
}

async function loadModelsForEvaluationStep(currentModel) {
    const select = document.getElementById('edit_evaluation_model');
    if (!select) return;
    
    try {
        const response = await fetch('/api/ollama/models', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            select.innerHTML = '<option value="">❌ Failed to load models</option>';
            return;
        }
        
        const data = await response.json();
        const models = data.models || [];
        
        if (models.length === 0) {
            select.innerHTML = '<option value="">⚠️ No Ollama models installed</option>';
            return;
        }
        
        // Build options
        select.innerHTML = '<option value="">-- Select a model --</option>' + 
            models.map(model => `<option value="${model}" ${model === currentModel ? 'selected' : ''}>${model}</option>`).join('');
        
        // If current model is not in the list, add it
        if (currentModel && !models.includes(currentModel)) {
            const option = document.createElement('option');
            option.value = currentModel;
            option.textContent = `${currentModel} (not available)`;
            option.selected = true;
            select.appendChild(option);
        }
        
    } catch (error) {
        console.error('Failed to load models:', error);
        select.innerHTML = '<option value="">❌ Network error</option>';
    }
}

function saveSurveyFormData() {
    const step = experimentFlowSteps[currentEditingStepIndex];
    if (!step.survey_questions) return;
    
    const questions = step.survey_questions;
    for (let i = 0; i < questions.length; i++) {
        const idEl = document.getElementById(`q_id_${i}`);
        const textEl = document.getElementById(`q_text_${i}`);
        const typeEl = document.getElementById(`q_type_${i}`);
        const requiredEl = document.getElementById(`q_required_${i}`);
        
        if (!textEl || !typeEl) continue;
        
        questions[i].question_id = idEl ? idEl.value.trim() : (questions[i].question_id || `q_${Date.now()}_${i+1}`);
        questions[i].question_text = textEl.value.trim();
        questions[i].question_type = typeEl.value;
        questions[i].required = requiredEl ? requiredEl.checked : true;
        
        // Save input_type for text questions
        if (questions[i].question_type === 'text') {
            const inputTypeEl = document.getElementById(`q_input_type_${i}`);
            if (inputTypeEl) {
                questions[i].input_type = inputTypeEl.value;
            }
        }
        
        const optionsEl = document.getElementById(`q_options_${i}`);
        if (optionsEl) {
            questions[i].options = optionsEl.value.split(',').map(o => o.trim()).filter(o => o);
        }
        
        if (questions[i].question_type === 'likert') {
            const scaleEl = document.getElementById(`q_scale_${i}`);
            const scale = scaleEl ? parseInt(scaleEl.value) : 5;
            questions[i].scale = scale;
            // scale_labels, min_label, max_label は削除（説明文に記載する方式に変更）
        }
    }
}

function addSurveyQuestion() {
    saveSurveyFormData();
    
    const step = experimentFlowSteps[currentEditingStepIndex];
    if (!step.survey_questions) {
        step.survey_questions = [];
    }
    
    // Generate unique question_id
    const questionId = `q_${Date.now()}_${step.survey_questions.length + 1}`;
    
    step.survey_questions.push({
        question_id: questionId,
        question_text: '',
        question_type: 'likert',
        required: true,
        scale: 5,
        options: []
    });
    
    document.getElementById('stepEditForm').innerHTML = generateStepEditForm(step);
}

function removeSurveyQuestion(index) {
    if (!confirm('Delete this question?')) return;
    
    saveSurveyFormData();
    
    const step = experimentFlowSteps[currentEditingStepIndex];
    step.survey_questions.splice(index, 1);
    document.getElementById('stepEditForm').innerHTML = generateStepEditForm(step);
}

function updateQuestionOptions(index) {
    const step = experimentFlowSteps[currentEditingStepIndex];
    const question = step.survey_questions[index];
    
    const textEl = document.getElementById(`q_text_${index}`);
    const requiredEl = document.getElementById(`q_required_${index}`);
    
    if (textEl) {
        question.question_text = textEl.value.trim();
    }
    if (requiredEl) {
        question.required = requiredEl.checked;
    }
    
    const questionType = document.getElementById(`q_type_${index}`).value;
    question.question_type = questionType;
    
    const needsOptions = ['radio', 'checkbox'].includes(questionType);
    const isLikert = questionType === 'likert';
    const isText = questionType === 'text';
    
    const container = document.getElementById(`q_options_container_${index}`);
    
    if (isText) {
        container.innerHTML = `
            <div class="form-group">
                <label>Input Type</label>
                <select id="q_input_type_${index}" class="form-control">
                    <option value="text">Text (any characters)</option>
                    <option value="number">Number (digits only)</option>
                    <option value="email">Email</option>
                    <option value="tel">Phone</option>
                    <option value="url">URL</option>
                </select>
                <div class="form-hint">HTML5 input type for validation</div>
            </div>
        `;
    } else if (needsOptions) {
        container.innerHTML = `
            <div class="form-group">
                <label>Options (comma-separated)</label>
                <input type="text" id="q_options_${index}" class="form-control" placeholder="Option 1, Option 2, Option 3">
            </div>
        `;
    } else if (isLikert) {
        container.innerHTML = `
            <div class="form-group">
                <label>Scale Points</label>
                <select id="q_scale_${index}" class="form-control">
                    <option value="3">3-point scale</option>
                    <option value="4">4-point scale</option>
                    <option value="5" selected>5-point scale</option>
                    <option value="6">6-point scale</option>
                    <option value="7">7-point scale</option>
                    <option value="9">9-point scale</option>
                    <option value="10">10-point scale</option>
                </select>
                <div class="form-hint">ラベルは説明文（survey_description）に記載してください。</div>
            </div>
        `;
    } else {
        container.innerHTML = '';
    }
}

// toggleLikertLabelMode と updateLikertScaleLabels は削除（ラベルは説明文に記載する方式に変更）

async function saveStepEdit() {
    // Check if editing a step within a branch
    let step;
    if (window.currentEditingBranchContext) {
        const { stepIndex, branchIndex, stepIdx } = window.currentEditingBranchContext;
        step = experimentFlowSteps[stepIndex].branches[branchIndex].steps[stepIdx];
    } else {
        step = experimentFlowSteps[currentEditingStepIndex];
    }
    
    const stepType = step.step_type;
    
    try {
        switch(stepType) {
            case 'consent':
                step.title = getInputValueOrFallback('edit_title', step.title || '');
                step.content = getInputValueOrFallback('edit_content', step.content || '');
                step.button_text = getInputValueOrFallback('edit_button_text', step.button_text || 'I Agree');
                step.required = getCheckboxValueOrFallback('edit_required', step.required ?? true);
                break;
                
            case 'instruction':
                step.title = getInputValueOrFallback('edit_title', step.title || '');
                step.content = getInputValueOrFallback('edit_content', step.content || '');
                step.button_text = getInputValueOrFallback('edit_button_text', step.button_text || 'Next');
                step.required = getCheckboxValueOrFallback('edit_required', step.required ?? true);
                const minDisplaySeconds = getNumberValueOrFallback('edit_min_display_seconds', null);
                step.min_display_seconds = minDisplaySeconds;
                step.show_timer = getCheckboxValueOrFallback('edit_show_timer', !!step.show_timer);
                break;
                
            case 'debriefing':
                step.title = getInputValueOrFallback('edit_title', step.title || '');
                step.content = getInputValueOrFallback('edit_content', step.content || '');
                step.button_text = getInputValueOrFallback('edit_button_text', step.button_text || 'Finish');
                // Debriefing is always required, no checkbox
                step.required = true;
                break;
                
            case 'chat':
                step.title = getInputValueOrFallback('edit_chat_title', step.title || '');
                step.instruction_text = getInputValueOrFallback('edit_instruction_text', step.instruction_text || '');
                step.bot_name = getInputValueOrFallback('edit_bot_name', step.bot_name || '');
                const botModelSelect = document.getElementById('edit_bot_model');
                step.bot_model = botModelSelect ? botModelSelect.value.trim() : '';
                step.system_prompt = getInputValueOrFallback('edit_system_prompt', step.system_prompt || '');
                const temperature = getNumberValueOrFallback('edit_temperature', step.temperature !== undefined ? step.temperature : 0.7);
                step.temperature = temperature !== null ? temperature : 0.7;
                const top_p = getNumberValueOrFallback('edit_top_p', step.top_p !== undefined ? step.top_p : 0.9);
                step.top_p = top_p !== null ? top_p : 0.9;
                const top_k = getNumberValueOrFallback('edit_top_k', step.top_k !== undefined ? step.top_k : 40);
                step.top_k = top_k !== null ? top_k : 40;
                const repeat_penalty = getNumberValueOrFallback('edit_repeat_penalty', step.repeat_penalty !== undefined ? step.repeat_penalty : 1.1);
                step.repeat_penalty = repeat_penalty !== null ? repeat_penalty : 1.1;
                const num_predict = getNumberValueOrFallback('edit_num_predict', null);
                step.num_predict = num_predict;
                const num_thread = getNumberValueOrFallback('edit_num_thread', null);
                step.num_thread = num_thread;
                const num_ctx = getNumberValueOrFallback('edit_num_ctx', null);
                step.num_ctx = num_ctx;
                const num_gpu = getNumberValueOrFallback('edit_num_gpu', null);
                step.num_gpu = num_gpu;
                const num_batch = getNumberValueOrFallback('edit_num_batch', null);
                step.num_batch = num_batch;
                const timeLimit = getNumberValueOrFallback('edit_time_limit', null);
                step.time_limit_minutes = timeLimit;
                step.required = getCheckboxValueOrFallback('edit_required', step.required ?? true);
                console.log('Saving chat step with bot_model:', step.bot_model, 'params:', {
                    temperature: step.temperature,
                    top_p: step.top_p,
                    top_k: step.top_k,
                    repeat_penalty: step.repeat_penalty,
                    num_predict: step.num_predict,
                    num_thread: step.num_thread,
                    num_ctx: step.num_ctx,
                    num_gpu: step.num_gpu,
                    num_batch: step.num_batch
                });
                break;
            
            case 'ai_evaluation':
                step.title = getInputValueOrFallback('edit_title', step.title || 'AI Evaluation');
                step.evaluation_model = getInputValueOrFallback('edit_evaluation_model', step.evaluation_model || '');
                step.context_prompt = getInputValueOrFallback('edit_context_prompt', step.context_prompt || '');
                step.required = getCheckboxValueOrFallback('edit_required', step.required ?? true);
                
                // Collect evaluation questions with Likert scale details
                step.evaluation_questions = saveEvaluationQuestionsData();
                break;
            
            case 'branch':
                step.title = document.getElementById('edit_title').value.trim();
                step.required = true; // Always required
                // Branch paths are managed separately through the flow editor
                break;
                
            case 'survey_randomizer':
                step.title = document.getElementById('edit_title').value.trim();
                step.required = document.getElementById('edit_required').checked;
                
                // Get items from global state (supports both surveys and steps)
                const items = window.currentEditingRandomizerItems || window.currentEditingSurveys || step.steps || step.surveys || [];
                
                // Save as 'steps' for new format, keep 'surveys' for backward compatibility
                step.steps = items;
                if (items.length > 0 && items.every(item => item.step_type === 'survey' || item.survey_questions)) {
                    // All items are surveys, also save to surveys property for compatibility
                    step.surveys = items;
                }
                
                console.log('Saved randomizer with items:', step.steps);
                break;
            
            case 'survey':
                step.title = document.getElementById('edit_title').value.trim();
                step.survey_description = document.getElementById('edit_survey_description').value.trim();
                step.button_text = document.getElementById('edit_button_text').value.trim();
                step.required = document.getElementById('edit_required').checked;
                step.randomize_questions = document.getElementById('edit_randomize_questions').checked;
                
                const questions = step.survey_questions || [];
                for (let i = 0; i < questions.length; i++) {
                    const idEl = document.getElementById(`q_id_${i}`);
                    const textEl = document.getElementById(`q_text_${i}`);
                    const typeEl = document.getElementById(`q_type_${i}`);
                    const requiredEl = document.getElementById(`q_required_${i}`);
                    
                    if (!textEl || !typeEl) continue;
                    
                    questions[i].question_id = idEl ? idEl.value.trim() : (questions[i].question_id || `q_${Date.now()}_${i+1}`);
                    questions[i].question_text = textEl.value.trim();
                    questions[i].question_type = typeEl.value;
                    questions[i].required = requiredEl ? requiredEl.checked : true;
                    
                    const optionsEl = document.getElementById(`q_options_${i}`);
                    if (optionsEl) {
                        questions[i].options = optionsEl.value.split(',').map(o => o.trim()).filter(o => o);
                    } else {
                        questions[i].options = [];
                    }
                    
                    if (questions[i].question_type === 'likert') {
                        const scaleEl = document.getElementById(`q_scale_${i}`);
                        const scale = scaleEl ? parseInt(scaleEl.value) : 5;
                        questions[i].scale = scale;
                        // scale_labels, min_label, max_label は削除（説明文に記載する方式に変更）
                    } else {
                        delete questions[i].scale;
                    }
                }
                break;
        }
        
        renderSteps();
        
        console.log('Step updated:', step);
        
        await autoSaveFlow();
        
        closeStepEditModal();
        
    } catch (error) {
        console.error('Save error:', error);
        alert('Failed to save step: ' + error.message);
    }
}

async function autoSaveFlow() {
    try {
        if (isEditingExperimentFlow) {
            const saveResponse = await fetch(`/api/experiments/${experimentId}/flow`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ experiment_flow: experimentFlowSteps })
            });
            
            if (saveResponse.ok) {
                console.log('✅ Flow auto-saved successfully');
            } else {
                throw new Error('Server returned error: ' + saveResponse.status);
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
                console.log('✅ Flow auto-saved successfully');
            } else {
                throw new Error('Server returned error: ' + saveResponse.status);
            }
        }
    } catch (error) {
        console.error('Auto-save failed:', error);
        alert('⚠️ Failed to save to server: ' + error.message + '\nYour changes are saved locally. Please try "Save Flow" manually.');
    }
}

// Save evaluation questions data from form
function saveEvaluationQuestionsData() {
    const questions = [];
    const questionCards = document.querySelectorAll('.question-edit-card');
    
    questionCards.forEach((card, idx) => {
        const qId = document.getElementById(`eval_q_id_${idx}`);
        const qText = document.getElementById(`eval_q_text_${idx}`);
        const qScale = document.getElementById(`eval_q_scale_${idx}`);
        const qRequired = document.getElementById(`eval_q_required_${idx}`);
        const useMinMaxOnly = document.getElementById(`eval_q_use_minmax_only_${idx}`);
        
        if (!qId || !qText || !qId.value.trim()) return;
        
        const scale = qScale ? parseInt(qScale.value) : 7;
        const question = {
            question_id: qId.value.trim(),
            question_text: qText.value.trim(),
            question_type: 'likert',
            required: qRequired ? qRequired.checked : true,
            scale: scale
            // scale_labels, min_label, max_label は削除（説明文に記載する方式に変更）
        };
        
        questions.push(question);
    });
    
    return questions;
}

// Add evaluation question
function addEvaluationQuestion() {
    saveEvaluationQuestionsData();
    
    const step = experimentFlowSteps[currentEditingStepIndex];
    if (!step.evaluation_questions) {
        step.evaluation_questions = [];
    }
    
    // Generate unique question_id
    const questionId = `eval_${Date.now()}_${step.evaluation_questions.length + 1}`;
    
    step.evaluation_questions.push({
        question_id: questionId,
        question_text: '',
        question_type: 'likert',
        required: true,
        scale: 7
    });
    
    document.getElementById('stepEditForm').innerHTML = generateAIEvaluationEditForm(step);
}

// Remove evaluation question
function removeEvaluationQuestion(index) {
    if (!confirm('Delete this question?')) return;
    
    // Save current data first
    const currentQuestions = saveEvaluationQuestionsData();
    
    const step = experimentFlowSteps[currentEditingStepIndex];
    step.evaluation_questions = currentQuestions;
    step.evaluation_questions.splice(index, 1);
    
    document.getElementById('stepEditForm').innerHTML = generateAIEvaluationEditForm(step);
}

// Update evaluation Likert scale labels when scale changes
// updateEvaluationLikertScaleLabels と toggleEvaluationLikertLabelMode は削除（ラベルは説明文に記載する方式に変更）

// Randomizer Management Functions
function addItemToRandomizer(itemType) {
    let newItem;
    
    if (itemType === 'survey') {
        newItem = {
            step_type: 'survey',
            survey_id: `survey_${Date.now()}`,
            title: 'New Survey',
            survey_description: '',
            survey_questions: [],
            button_text: 'Next'
        };
    } else if (itemType === 'instruction') {
        newItem = {
            step_type: 'instruction',
            title: 'New Instruction',
            content: '',
            button_text: 'Next',
            min_display_seconds: null,
            show_timer: true
        };
    } else {
        newItem = {
            step_type: itemType,
            title: `New ${itemType}`,
            content: ''
        };
    }
    
    window.currentEditingRandomizerItems.push(newItem);
    refreshRandomizerItemsListContainer();
}

function removeItemFromRandomizer(index) {
    if (confirm(`Delete Item ${index + 1}?`)) {
        window.currentEditingRandomizerItems.splice(index, 1);
        refreshRandomizerItemsListContainer();
    }
}

function editItemInRandomizer(index) {
    window.currentEditingRandomizerItemIndex = index;
    const item = window.currentEditingRandomizerItems[index];
    const itemType = item.step_type || 'survey';
    
    // Generate form based on item type
    const formHtml = generateSingleItemEditForm(item, index);
    
    // Show item editor modal
    const modalTitle = itemType.charAt(0).toUpperCase() + itemType.slice(1);
    const modalHtml = `
        <div id="itemEditModal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 8px; width: 90%; max-width: 900px; max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <div style="padding: 20px; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; background: white; z-index: 1;">
                    <h3 style="margin: 0;">Edit ${modalTitle} ${index + 1}</h3>
                    <button onclick="closeItemEditModal()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #999;">&times;</button>
                </div>
                <div style="padding: 20px;">
                    <form id="itemEditFormInner" onsubmit="saveItemInRandomizer(); return false;">
                        ${formHtml}
                        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                            <button type="button" class="btn" onclick="closeItemEditModal()">Cancel</button>
                            <button type="submit" class="btn btn-success">Save</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function generateSingleItemEditForm(item, index) {
    const itemType = item.step_type || 'survey';
    
    if (itemType === 'survey') {
        return generateSingleSurveyEditForm(item, index);
    } else if (itemType === 'instruction') {
        return `
            <div class="form-group">
                <label>Title</label>
                <input type="text" id="edit_item_title" class="form-control" value="${escapeHtml(item.title || '')}" placeholder="e.g., Instructions">
            </div>
            <div class="form-group">
                <label>Content (Plain Text)</label>
                <textarea id="edit_item_content" class="form-control" rows="10" placeholder="Enter instructions here...">${escapeHtml(item.content || '')}</textarea>
                <div class="form-hint">Plain text only. Line breaks will be preserved.</div>
            </div>
            <div class="form-group">
                <label>Button Text</label>
                <input type="text" id="edit_item_button_text" class="form-control" value="${escapeHtml(item.button_text || 'Next')}" placeholder="Next">
            </div>
            <div class="form-group">
                <label>Minimum Display Time (seconds)</label>
                <input type="number" id="edit_item_min_display_seconds" class="form-control" value="${item.min_display_seconds || ''}" placeholder="Leave empty for no time limit" min="0">
                <div class="form-hint">Optional: Number of seconds to wait before showing the button</div>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="edit_item_show_timer" ${item.show_timer !== false ? 'checked' : ''}>
                    Show countdown timer
                </label>
            </div>
        `;
    } else {
        return `<p>Editing for type "${itemType}" is not yet implemented.</p>`;
    }
}

function generateSingleSurveyEditForm(survey, index) {
    const questions = survey.survey_questions || [];
    
    // Store current survey questions in global state
    window.currentEditingSurveyQuestions = questions;
    
    return `
        <div class="form-group">
            <label>Survey ID</label>
            <input type="text" id="edit_survey_id" class="form-control" value="${escapeHtml(survey.survey_id || '')}" placeholder="e.g., survey_1">
            <div class="form-hint">Unique identifier for this survey</div>
        </div>
        <div class="form-group">
            <label>Survey Title</label>
            <input type="text" id="edit_survey_title" class="form-control" value="${escapeHtml(survey.title || '')}" placeholder="e.g., Empathy Check">
        </div>
        <div class="form-group">
            <label>Description (Optional)</label>
            <textarea id="edit_survey_desc" class="form-control" rows="3" placeholder="Brief description...">${escapeHtml(survey.survey_description || '')}</textarea>
        </div>
        <div class="form-group">
            <label>Button Text</label>
            <input type="text" id="edit_survey_button" class="form-control" value="${escapeHtml(survey.button_text || 'Next')}" placeholder="Next">
        </div>
        
        <hr style="margin: 20px 0;">
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h4 style="margin: 0;">Survey Questions</h4>
            <button type="button" class="btn btn-small btn-success" onclick="addQuestionToCurrentSurvey()">+ Add Question</button>
        </div>
        
        <div id="surveyQuestionsContainerInner">
            ${questions.length === 0 ? '<p style="color: #999; text-align: center; padding: 20px;">No questions yet. Click "Add Question" to create one.</p>' : ''}
            ${questions.map((q, idx) => generateQuestionEditHtml(q, idx)).join('')}
        </div>
    `;
}

function addQuestionToCurrentSurvey() {
    const newQuestion = {
        question_id: `q_${Date.now()}`,
        question_text: '',
        question_type: 'likert',
        required: true,
        scale: 5,
        options: []
    };
    
    window.currentEditingSurveyQuestions.push(newQuestion);
    refreshSurveyQuestionsContainerInner();
}

function refreshSurveyQuestionsContainerInner() {
    const container = document.getElementById('surveyQuestionsContainerInner');
    if (!container) return;
    
    const questions = window.currentEditingSurveyQuestions;
    container.innerHTML = questions.length === 0 
        ? '<p style="color: #999; text-align: center; padding: 20px;">No questions yet. Click "Add Question" to create one.</p>'
        : questions.map((q, idx) => generateQuestionEditHtml(q, idx)).join('');
}

function saveSurveyInRandomizer() {
    const index = window.currentEditingSurveyIndex;
    const survey = window.currentEditingSurveys[index];
    
    // Update survey metadata
    survey.survey_id = document.getElementById('edit_survey_id').value.trim();
    survey.title = document.getElementById('edit_survey_title').value.trim();
    survey.survey_description = document.getElementById('edit_survey_desc').value.trim();
    survey.button_text = document.getElementById('edit_survey_button').value.trim();
    
    // Save questions (similar to regular survey)
    const questions = window.currentEditingSurveyQuestions;
    for (let i = 0; i < questions.length; i++) {
        const idEl = document.getElementById(`q_id_${i}`);
        const textEl = document.getElementById(`q_text_${i}`);
        const typeEl = document.getElementById(`q_type_${i}`);
        const requiredEl = document.getElementById(`q_required_${i}`);
        
        if (!textEl || !typeEl) continue;
        
        questions[i].question_id = idEl ? idEl.value.trim() : (questions[i].question_id || `q_${Date.now()}_${i+1}`);
        questions[i].question_text = textEl.value.trim();
        questions[i].question_type = typeEl.value;
        questions[i].required = requiredEl ? requiredEl.checked : true;
        
        const optionsEl = document.getElementById(`q_options_${i}`);
        if (optionsEl) {
            questions[i].options = optionsEl.value.split(',').map(o => o.trim()).filter(o => o);
        } else {
            questions[i].options = [];
        }
        
        if (questions[i].question_type === 'likert') {
            const scaleEl = document.getElementById(`q_scale_${i}`);
            const scale = scaleEl ? parseInt(scaleEl.value) : 7;
            questions[i].scale = scale;
            
            const useMinMaxOnly = document.getElementById(`q_use_minmax_only_${i}`);
            
            if (useMinMaxOnly && useMinMaxOnly.checked) {
                const minLabelEl = document.getElementById(`q_min_label_${i}`);
                const maxLabelEl = document.getElementById(`q_max_label_${i}`);
                
                questions[i].min_label = minLabelEl ? minLabelEl.value.trim() : '';
                questions[i].max_label = maxLabelEl ? maxLabelEl.value.trim() : '';
                questions[i].scale_labels = [];
            } else {
                const scaleLabels = [];
                for (let j = 1; j <= scale; j++) {
                    const labelEl = document.getElementById(`q_scale_label_${i}_${j}`);
                    scaleLabels.push(labelEl ? labelEl.value.trim() : '');
                }
                questions[i].scale_labels = scaleLabels;
                questions[i].min_label = '';
                questions[i].max_label = '';
            }
        }
    }
    
    survey.survey_questions = questions;
    
    closeSurveyEditModal();
    refreshSurveysListContainer();
}

function saveItemInRandomizer() {
    const index = window.currentEditingRandomizerItemIndex;
    const item = window.currentEditingRandomizerItems[index];
    const itemType = item.step_type || 'survey';
    
    if (itemType === 'survey') {
        // Update survey metadata
        item.survey_id = document.getElementById('edit_survey_id').value.trim();
        item.title = document.getElementById('edit_survey_title').value.trim();
        item.survey_description = document.getElementById('edit_survey_desc').value.trim();
        item.button_text = document.getElementById('edit_survey_button').value.trim();
        
        // Save questions (from global state set by generateSingleSurveyEditForm)
        const questions = window.currentEditingSurveyQuestions;
        for (let i = 0; i < questions.length; i++) {
            const idEl = document.getElementById(`q_id_${i}`);
            const textEl = document.getElementById(`q_text_${i}`);
            const typeEl = document.getElementById(`q_type_${i}`);
            const requiredEl = document.getElementById(`q_required_${i}`);
            
            if (!textEl || !typeEl) continue;
            
            questions[i].question_id = idEl ? idEl.value.trim() : (questions[i].question_id || `q_${Date.now()}_${i+1}`);
            questions[i].question_text = textEl.value.trim();
            questions[i].question_type = typeEl.value;
            questions[i].required = requiredEl ? requiredEl.checked : true;
            
            const optionsEl = document.getElementById(`q_options_${i}`);
            if (optionsEl) {
                questions[i].options = optionsEl.value.split(',').map(o => o.trim()).filter(o => o);
            } else {
                questions[i].options = [];
            }
            
            if (questions[i].question_type === 'likert') {
                const scaleEl = document.getElementById(`q_scale_${i}`);
                const scale = scaleEl ? parseInt(scaleEl.value) : 5;
                questions[i].scale = scale;
                
                const useMinMaxOnly = document.getElementById(`q_use_minmax_only_${i}`);
                
                if (useMinMaxOnly && useMinMaxOnly.checked) {
                    const minLabelEl = document.getElementById(`q_min_label_${i}`);
                    const maxLabelEl = document.getElementById(`q_max_label_${i}`);
                    
                    questions[i].min_label = minLabelEl ? minLabelEl.value.trim() : '';
                    questions[i].max_label = maxLabelEl ? maxLabelEl.value.trim() : '';
                    questions[i].scale_labels = [];
                } else {
                    const scaleLabels = [];
                    for (let j = 1; j <= scale; j++) {
                        const labelEl = document.getElementById(`q_scale_label_${i}_${j}`);
                        scaleLabels.push(labelEl ? labelEl.value.trim() : '');
                    }
                    questions[i].scale_labels = scaleLabels;
                    questions[i].min_label = '';
                    questions[i].max_label = '';
                }
            }
        }
        
        item.survey_questions = questions;
    } else if (itemType === 'instruction') {
        // Update instruction metadata
        item.title = document.getElementById('edit_item_title').value.trim();
        item.content = document.getElementById('edit_item_content').value.trim();
        item.button_text = document.getElementById('edit_item_button_text').value.trim();
        const minDisplaySeconds = document.getElementById('edit_item_min_display_seconds').value;
        item.min_display_seconds = minDisplaySeconds ? parseInt(minDisplaySeconds) : null;
        item.show_timer = document.getElementById('edit_item_show_timer').checked;
    }
    
    closeItemEditModal();
    refreshRandomizerItemsListContainer();
}

function closeItemEditModal() {
    const modal = document.getElementById('itemEditModal');
    if (modal) {
        modal.remove();
    }
    window.currentEditingRandomizerItemIndex = null;
    window.currentEditingSurveyQuestions = null;
}

function refreshRandomizerItemsListContainer() {
    const container = document.getElementById('randomizerItemsListContainer');
    if (!container) return;
    
    const items = window.currentEditingRandomizerItems;
    container.innerHTML = items.length === 0
        ? '<p style="color: #999; text-align: center; padding: 20px;">No items yet. Click a button above to add one.</p>'
        : items.map((item, idx) => generateRandomizerItemCardHtml(item, idx)).join('');
}

// Legacy functions for backward compatibility
function saveSurveyInRandomizer() {
    saveItemInRandomizer();
}

function closeSurveyEditModal() {
    closeItemEditModal();
}

function refreshSurveysListContainer() {
    refreshRandomizerItemsListContainer();
}

// Export functions to global scope for onclick handlers
window.editStep = editStep;
// New randomizer functions
window.addItemToRandomizer = addItemToRandomizer;
window.removeItemFromRandomizer = removeItemFromRandomizer;
window.editItemInRandomizer = editItemInRandomizer;
window.saveItemInRandomizer = saveItemInRandomizer;
window.closeItemEditModal = closeItemEditModal;
// Legacy survey randomizer functions (for backward compatibility)
window.addSurveyToRandomizer = addItemToRandomizer.bind(null, 'survey');
window.removeSurveyFromRandomizer = removeItemFromRandomizer;
window.editSurveyInRandomizer = editItemInRandomizer;
window.saveSurveyInRandomizer = saveSurveyInRandomizer;
window.closeSurveyEditModal = closeSurveyEditModal;
window.addQuestionToCurrentSurvey = addQuestionToCurrentSurvey;
window.closeStepEditModal = closeStepEditModal;
window.saveStepEdit = saveStepEdit;
window.addSurveyQuestion = addSurveyQuestion;
window.removeSurveyQuestion = removeSurveyQuestion;
window.addEvaluationQuestion = addEvaluationQuestion;
window.removeEvaluationQuestion = removeEvaluationQuestion;
// updateEvaluationLikertScaleLabels と toggleEvaluationLikertLabelMode は削除済み

console.log('✅ experiment_detail_step_editor.js loaded (2024-11-16 - Global Scope Export)');


