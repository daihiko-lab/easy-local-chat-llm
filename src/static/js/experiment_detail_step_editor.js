// Step Editor Functions for Experiment Detail Page
// Survey question management and step editing

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
                scale: 7,
                scale_labels: [],
                min_label: '',
                max_label: ''
            };
        }
        return q;
    });
    
    return `
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="edit_title" class="form-control" value="${escapeHtml(step.title || 'AI Evaluation')}" placeholder="e.g., AI Evaluation">
        </div>
        <div class="form-group">
            <label>Evaluation Model</label>
            <input type="text" id="edit_evaluation_model" class="form-control" value="${escapeHtml(step.evaluation_model || 'gemma2:9b')}" placeholder="gemma2:9b">
            <div class="form-hint">Ollama model to use for evaluation (e.g., gemma2:9b, llama2)</div>
        </div>
        <div class="form-group">
            <label>Context Prompt</label>
            <textarea id="edit_context_prompt" class="form-control" rows="4" placeholder="Context for the AI evaluator...">${escapeHtml(step.context_prompt || 'Please evaluate the following conversation objectively.')}</textarea>
            <div class="form-hint">Instructions for the AI to set context for evaluation</div>
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
            <button type="button" class="btn btn-small btn-success" onclick="addEvaluationQuestion()">+ Add Question</button>
        </div>
        
        <div id="evaluationQuestionsContainer">
            ${normalizedQuestions.length === 0 ? '<p style="color: #999; text-align: center; padding: 20px;">No questions yet. Click "Add Question" to create one.</p>' : ''}
            ${normalizedQuestions.map((q, idx) => generateEvaluationQuestionEditHtml(q, idx)).join('')}
        </div>
    `;
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
    const minLabel = question.min_label || '';
    const maxLabel = question.max_label || '';
    const scaleLabels = question.scale_labels || [];
    
    const hasMinMaxLabels = (minLabel || maxLabel) && scaleLabels.length === 0;
    const effectiveScaleLabels = scaleLabels.length > 0 ? scaleLabels : (hasMinMaxLabels ? [] : Array(scale).fill(''));
    
    let scaleLabelsHtml = '';
    for (let i = 1; i <= scale; i++) {
        const labelValue = effectiveScaleLabels[i - 1] || '';
        scaleLabelsHtml += `
            <div style="margin-bottom: 8px;">
                <label style="font-weight: normal; font-size: 0.9em;">${i}:</label>
                <input type="text" id="eval_q_scale_label_${index}_${i}" class="form-control" value="${escapeHtml(labelValue)}" placeholder="Label for ${i}" style="margin-top: 3px;">
            </div>
        `;
    }
    
    const useMinMaxMode = hasMinMaxLabels;
    
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
                <select id="eval_q_scale_${index}" class="form-control" onchange="updateEvaluationLikertScaleLabels(${index})">
                    <option value="3" ${scale === 3 ? 'selected' : ''}>3-point scale</option>
                    <option value="4" ${scale === 4 ? 'selected' : ''}>4-point scale</option>
                    <option value="5" ${scale === 5 ? 'selected' : ''}>5-point scale</option>
                    <option value="6" ${scale === 6 ? 'selected' : ''}>6-point scale</option>
                    <option value="7" ${scale === 7 ? 'selected' : ''}>7-point scale</option>
                    <option value="9" ${scale === 9 ? 'selected' : ''}>9-point scale</option>
                    <option value="10" ${scale === 10 ? 'selected' : ''}>10-point scale</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="eval_q_use_minmax_only_${index}" ${useMinMaxMode ? 'checked' : ''} onchange="toggleEvaluationLikertLabelMode(${index})">
                    Use min/max labels only (両端のみ)
                </label>
            </div>
            <div id="eval_q_minmax_container_${index}" style="${useMinMaxMode ? '' : 'display: none;'}">
                <div class="form-group">
                    <label>Minimum Label (e.g., "Not at all")</label>
                    <input type="text" id="eval_q_min_label_${index}" class="form-control" value="${escapeHtml(minLabel)}" placeholder="Optional: Label for lowest value">
                </div>
                <div class="form-group">
                    <label>Maximum Label (e.g., "Very much")</label>
                    <input type="text" id="eval_q_max_label_${index}" class="form-control" value="${escapeHtml(maxLabel)}" placeholder="Optional: Label for highest value">
                </div>
            </div>
            <div id="eval_q_scale_labels_container_${index}" style="${useMinMaxMode ? 'display: none;' : ''}">
                <div class="form-group">
                    <label>Labels for each point</label>
                    <div style="background: #f9f9f9; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0;">
                        ${scaleLabelsHtml}
                    </div>
                </div>
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
        const minLabel = question.min_label || question.scale_min_label || '';
        const maxLabel = question.max_label || question.scale_max_label || '';
        const scaleLabels = question.scale_labels || [];
        
        const hasMinMaxLabels = (minLabel || maxLabel) && scaleLabels.length === 0;
        const effectiveScaleLabels = scaleLabels.length > 0 ? scaleLabels : (hasMinMaxLabels ? [] : Array(scale).fill(''));
        
        let scaleLabelsHtml = '';
        for (let i = 1; i <= scale; i++) {
            const labelValue = effectiveScaleLabels[i - 1] || '';
            scaleLabelsHtml += `
                <div style="margin-bottom: 8px;">
                    <label style="font-weight: normal; font-size: 0.9em;">${i}:</label>
                    <input type="text" id="q_scale_label_${index}_${i}" class="form-control" value="${escapeHtml(labelValue)}" placeholder="Label for ${i}" style="margin-top: 3px;">
                </div>
            `;
        }
        
        const useMinMaxMode = hasMinMaxLabels;
        
        optionsHtml = `
            <div class="form-group">
                <label>Scale Points</label>
                <select id="q_scale_${index}" class="form-control" onchange="updateLikertScaleLabels(${index})">
                    <option value="3" ${scale === 3 ? 'selected' : ''}>3-point scale</option>
                    <option value="4" ${scale === 4 ? 'selected' : ''}>4-point scale</option>
                    <option value="5" ${scale === 5 ? 'selected' : ''}>5-point scale</option>
                    <option value="6" ${scale === 6 ? 'selected' : ''}>6-point scale</option>
                    <option value="7" ${scale === 7 ? 'selected' : ''}>7-point scale</option>
                    <option value="9" ${scale === 9 ? 'selected' : ''}>9-point scale</option>
                    <option value="10" ${scale === 10 ? 'selected' : ''}>10-point scale</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="q_use_minmax_only_${index}" ${useMinMaxMode ? 'checked' : ''} onchange="toggleLikertLabelMode(${index})">
                    Use min/max labels only (両端のみ)
                </label>
            </div>
            <div id="q_minmax_container_${index}" style="${useMinMaxMode ? '' : 'display: none;'}">
                <div class="form-group">
                    <label>Minimum Label (e.g., "全くそう思わない")</label>
                    <input type="text" id="q_min_label_${index}" class="form-control" value="${escapeHtml(minLabel)}" placeholder="Optional: Label for lowest value">
                </div>
                <div class="form-group">
                    <label>Maximum Label (e.g., "非常にそう思う")</label>
                    <input type="text" id="q_max_label_${index}" class="form-control" value="${escapeHtml(maxLabel)}" placeholder="Optional: Label for highest value">
                </div>
            </div>
            <div id="q_scale_labels_container_${index}" style="${useMinMaxMode ? 'display: none;' : ''}">
                <div class="form-group">
                    <label>Labels for each point</label>
                    <div style="background: #f9f9f9; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0;">
                        ${scaleLabelsHtml}
                    </div>
                </div>
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
        scale_labels: ['', '', '', '', ''],
        min_label: '',
        max_label: '',
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
        let scaleLabelsHtml = '';
        for (let i = 1; i <= 5; i++) {
            scaleLabelsHtml += `
                <div style="margin-bottom: 8px;">
                    <label style="font-weight: normal; font-size: 0.9em;">${i}:</label>
                    <input type="text" id="q_scale_label_${index}_${i}" class="form-control" placeholder="Label for ${i}" style="margin-top: 3px;">
                </div>
            `;
        }
        
        container.innerHTML = `
            <div class="form-group">
                <label>Scale Points</label>
                <select id="q_scale_${index}" class="form-control" onchange="updateLikertScaleLabels(${index})">
                    <option value="3">3-point scale</option>
                    <option value="4">4-point scale</option>
                    <option value="5" selected>5-point scale</option>
                    <option value="6">6-point scale</option>
                    <option value="7">7-point scale</option>
                    <option value="9">9-point scale</option>
                    <option value="10">10-point scale</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="q_use_minmax_only_${index}" onchange="toggleLikertLabelMode(${index})">
                    Use min/max labels only (両端のみ)
                </label>
            </div>
            <div id="q_minmax_container_${index}" style="display: none;">
                <div class="form-group">
                    <label>Minimum Label (e.g., "全くそう思わない")</label>
                    <input type="text" id="q_min_label_${index}" class="form-control" placeholder="Optional: Label for lowest value">
                </div>
                <div class="form-group">
                    <label>Maximum Label (e.g., "非常にそう思う")</label>
                    <input type="text" id="q_max_label_${index}" class="form-control" placeholder="Optional: Label for highest value">
                </div>
            </div>
            <div id="q_scale_labels_container_${index}">
                <div class="form-group">
                    <label>Labels for each point</label>
                    <div style="background: #f9f9f9; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0;">
                        ${scaleLabelsHtml}
                    </div>
                </div>
            </div>
        `;
    } else {
        container.innerHTML = '';
    }
}

function toggleLikertLabelMode(index) {
    const useMinMaxOnly = document.getElementById(`q_use_minmax_only_${index}`).checked;
    const minMaxContainer = document.getElementById(`q_minmax_container_${index}`);
    const scaleLabelsContainer = document.getElementById(`q_scale_labels_container_${index}`);
    
    if (useMinMaxOnly) {
        minMaxContainer.style.display = '';
        scaleLabelsContainer.style.display = 'none';
    } else {
        minMaxContainer.style.display = 'none';
        scaleLabelsContainer.style.display = '';
    }
}

function updateLikertScaleLabels(index) {
    const scale = parseInt(document.getElementById(`q_scale_${index}`).value);
    const container = document.getElementById(`q_scale_labels_container_${index}`);
    
    let scaleLabelsHtml = '';
    for (let i = 1; i <= scale; i++) {
        const existingInput = document.getElementById(`q_scale_label_${index}_${i}`);
        const existingValue = existingInput ? existingInput.value : '';
        
        scaleLabelsHtml += `
            <div style="margin-bottom: 8px;">
                <label style="font-weight: normal; font-size: 0.9em;">${i}:</label>
                <input type="text" id="q_scale_label_${index}_${i}" class="form-control" value="${escapeHtml(existingValue)}" placeholder="Label for ${i}" style="margin-top: 3px;">
            </div>
        `;
    }
    
    const formGroup = container.querySelector('.form-group > div');
    if (formGroup) {
        formGroup.innerHTML = scaleLabelsHtml;
    }
}

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
            case 'instruction':
            case 'debriefing':
                step.title = document.getElementById('edit_title').value.trim();
                step.content = document.getElementById('edit_content').value.trim();
                step.button_text = document.getElementById('edit_button_text').value.trim();
                step.required = document.getElementById('edit_required').checked;
                break;
                
            case 'chat':
                step.title = document.getElementById('edit_chat_title').value.trim();
                step.bot_name = document.getElementById('edit_bot_name').value.trim();
                const botModelSelect = document.getElementById('edit_bot_model');
                step.bot_model = botModelSelect ? botModelSelect.value.trim() : '';
                step.system_prompt = document.getElementById('edit_system_prompt').value.trim();
                const timeLimit = document.getElementById('edit_time_limit').value;
                step.time_limit_minutes = timeLimit ? parseInt(timeLimit) : null;
                step.required = document.getElementById('edit_required').checked;
                console.log('Saving chat step with bot_model:', step.bot_model);
                break;
            
            case 'ai_evaluation':
                step.title = document.getElementById('edit_title').value.trim();
                step.evaluation_model = document.getElementById('edit_evaluation_model').value.trim();
                step.context_prompt = document.getElementById('edit_context_prompt').value.trim();
                step.required = document.getElementById('edit_required').checked;
                
                // Collect evaluation questions with Likert scale details
                step.evaluation_questions = saveEvaluationQuestionsData();
                break;
            
            case 'branch':
                step.title = document.getElementById('edit_title').value.trim();
                step.required = true; // Always required
                // Branch paths are managed separately through the flow editor
                break;
                
            case 'survey':
                step.title = document.getElementById('edit_title').value.trim();
                step.survey_description = document.getElementById('edit_survey_description').value.trim();
                step.button_text = document.getElementById('edit_button_text').value.trim();
                step.required = document.getElementById('edit_required').checked;
                
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
                    } else {
                        delete questions[i].scale;
                        delete questions[i].min_label;
                        delete questions[i].max_label;
                        delete questions[i].scale_labels;
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
        };
        
        // Collect labels based on mode
        if (useMinMaxOnly && useMinMaxOnly.checked) {
            const minLabel = document.getElementById(`eval_q_min_label_${idx}`);
            const maxLabel = document.getElementById(`eval_q_max_label_${idx}`);
            question.min_label = minLabel ? minLabel.value.trim() : '';
            question.max_label = maxLabel ? maxLabel.value.trim() : '';
            question.scale_labels = [];
        } else {
            const scaleLabels = [];
            for (let i = 1; i <= scale; i++) {
                const labelInput = document.getElementById(`eval_q_scale_label_${idx}_${i}`);
                scaleLabels.push(labelInput ? labelInput.value.trim() : '');
            }
            question.scale_labels = scaleLabels;
            question.min_label = '';
            question.max_label = '';
        }
        
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
        scale: 7,
        scale_labels: [],
        min_label: '',
        max_label: ''
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
function updateEvaluationLikertScaleLabels(index) {
    const step = experimentFlowSteps[currentEditingStepIndex];
    const question = step.evaluation_questions[index];
    
    // Save current values
    const qId = document.getElementById(`eval_q_id_${index}`);
    const qText = document.getElementById(`eval_q_text_${index}`);
    const qRequired = document.getElementById(`eval_q_required_${index}`);
    
    if (qId) question.question_id = qId.value.trim();
    if (qText) question.question_text = qText.value.trim();
    if (qRequired) question.required = qRequired.checked;
    
    const newScale = parseInt(document.getElementById(`eval_q_scale_${index}`).value);
    question.scale = newScale;
    question.scale_labels = Array(newScale).fill('');
    
    document.getElementById('stepEditForm').innerHTML = generateAIEvaluationEditForm(step);
}

// Toggle evaluation Likert label mode
function toggleEvaluationLikertLabelMode(index) {
    const useMinMaxOnly = document.getElementById(`eval_q_use_minmax_only_${index}`).checked;
    const minMaxContainer = document.getElementById(`eval_q_minmax_container_${index}`);
    const scaleLabelsContainer = document.getElementById(`eval_q_scale_labels_container_${index}`);
    
    if (useMinMaxOnly) {
        minMaxContainer.style.display = '';
        scaleLabelsContainer.style.display = 'none';
    } else {
        minMaxContainer.style.display = 'none';
        scaleLabelsContainer.style.display = '';
    }
}

// Export functions to global scope for onclick handlers
window.editStep = editStep;
window.closeStepEditModal = closeStepEditModal;
window.saveStepEdit = saveStepEdit;
window.addSurveyQuestion = addSurveyQuestion;
window.removeSurveyQuestion = removeSurveyQuestion;
window.addEvaluationQuestion = addEvaluationQuestion;
window.removeEvaluationQuestion = removeEvaluationQuestion;
window.updateEvaluationLikertScaleLabels = updateEvaluationLikertScaleLabels;
window.toggleEvaluationLikertLabelMode = toggleEvaluationLikertLabelMode;

console.log('✅ experiment_detail_step_editor.js loaded (2024-11-16 - Global Scope Export)');

