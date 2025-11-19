/**
 * 多段階実験フロー管理
 * 汎用的な実験フローシステム
 */

class ExperimentFlow {
    constructor(sessionId, clientId) {
        this.sessionId = sessionId;
        this.clientId = clientId;
        this.currentStep = null;
        this.totalSteps = 0;
        this.currentStepIndex = 0;
        this.hasFlow = false;
        
        // DOM要素のキャッシュ
        this.flowContainer = null;
        this.chatContainer = null;
    }
    
    /**
     * 初期化：フロー情報を取得
     */
    async initialize() {
        try {
            // DOM要素を取得（早期取得）
            this.chatContainer = document.getElementById('chatContainer');
            
            // デバッグ情報を画面に表示
            this.showDebugInfo('Initializing flow...');
            
            const response = await fetch(`/api/sessions/${this.sessionId}/flow/current?client_id=${this.clientId}`);
            const data = await response.json();
            
            this.showDebugInfo(`Flow response: has_flow=${data.has_flow}`);
            
            // 🆕 完了済み参加者チェック
            if (data.already_completed) {
                this.hasFlow = true;
                this.showAlreadyCompletedMessage();
                return true;
            }
            
            if (!data.has_flow) {
                // フローが設定されていない場合は旧形式として処理
                this.hasFlow = false;
                console.log('[Flow] No experiment flow configured, using legacy mode');
                return false;
            }
            
            this.hasFlow = true;
            
            // フローが存在することが確定したので、すぐにチャットを非表示
            if (this.chatContainer) {
                this.chatContainer.style.display = 'none';
                console.log('[Flow] Flow exists, hiding chat container immediately');
            }
            
            if (data.completed) {
                // すべてのステップが完了
                this.showCompletionMessage();
                return true;
            }
            
            // フロー情報を保存
            this.currentStep = data.current_step;
            this.currentStepIndex = data.current_step_index;
            this.totalSteps = data.total_steps;
            
            // フロー用コンテナを作成（存在しなければ）
            if (!document.getElementById('flowContainer')) {
                this.createFlowContainer();
            }
            this.flowContainer = document.getElementById('flowContainer');
            
            // 実験フローが存在する場合、チャット以外は確実にチャットを非表示＆フローを表示
            if (this.currentStep.step_type !== 'chat') {
                this.chatContainer.style.display = 'none';
                this.flowContainer.style.display = 'flex';
                this.showDebugInfo(`Hiding chat, showing flow (type: ${this.currentStep.step_type})`);
                console.log('[Flow] Hiding chat, showing flow container');
            } else {
                this.chatContainer.style.display = 'flex';
                this.flowContainer.style.display = 'none';
                this.showDebugInfo('Showing chat, hiding flow');
                console.log('[Flow] Showing chat, hiding flow container');
            }
            
            // 最初のステップを表示
            this.showDebugInfo(`Showing step: ${this.currentStep.step_type}`);
            await this.showCurrentStep();
            
            return true;
            
        } catch (error) {
            console.error('[Flow] Error initializing:', error);
            this.showDebugInfo(`ERROR: ${error.message}`);
            this.hasFlow = false;
            return false;
        }
    }
    
    /**
     * フロー用コンテナを作成
     */
    createFlowContainer() {
        const container = document.querySelector('.container');
        const flowDiv = document.createElement('div');
        flowDiv.id = 'flowContainer';
        flowDiv.className = 'flow-container';
        flowDiv.style.display = 'none';
        container.appendChild(flowDiv);
    }
    
    /**
     * 現在のステップを表示
     */
    async showCurrentStep() {
        if (!this.currentStep) {
            console.error('[Flow] No current step to show');
            return;
        }
        
        // チャットコンテナを非表示
        if (this.currentStep.step_type !== 'chat') {
            this.chatContainer.style.display = 'none';
            this.flowContainer.style.display = 'flex';
        }
        
        // ステップタイプに応じた表示
        switch (this.currentStep.step_type) {
            case 'consent':
                this.showConsentStep();
                break;
            case 'instruction':
                this.showInstructionStep();
                break;
            case 'survey':
                this.showSurveyStep();
                break;
            case 'survey_randomizer':
                this.showSurveyRandomizerStep();
                break;
            case 'chat':
                this.showChatStep();
                break;
            case 'ai_evaluation':
                await this.processAIEvaluationStep();
                break;
            case 'branch':
                await this.processBranchStep();
                break;
            case 'debriefing':
                this.showDebriefingStep();
                break;
            default:
                console.error('[Flow] Unknown step type:', this.currentStep.step_type);
        }
        
        console.log(`[Flow] Showing step ${this.currentStepIndex + 1}/${this.totalSteps}: ${this.currentStep.step_type}`);
    }
    
    /**
     * 同意書ステップ
     */
    showConsentStep() {
        const title = this.currentStep.title || '研究参加への同意';
        const content = this.currentStep.content || '';
        const buttonText = this.currentStep.button_text || '同意する';
        
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <div class="flow-progress">ステップ ${this.currentStepIndex + 1} / ${this.totalSteps}</div>
                <h2 class="flow-title">${this.escapeHtml(title)}</h2>
                <div class="flow-text">${this.formatContent(content)}</div>
                <div class="flow-actions">
                    <button class="flow-button" onclick="experimentFlow.advanceToNextStep()">${this.escapeHtml(buttonText)}</button>
                </div>
            </div>
        `;
    }
    
    /**
     * 教示文ステップ
     */
    showInstructionStep() {
        const title = this.currentStep.title || '実験の説明';
        const content = this.currentStep.content || '';
        const buttonText = this.currentStep.button_text || '次へ';
        const minDisplaySeconds = this.currentStep.min_display_seconds;
        // show_timerが明示的にtrueの場合のみ表示、それ以外（false/null/undefined）は非表示
        const showTimer = this.currentStep.show_timer === true;
        
        console.log('[Flow] Instruction step:', {
            step_id: this.currentStep.step_id,
            minDisplaySeconds: minDisplaySeconds,
            show_timer: this.currentStep.show_timer,
            showTimer: showTimer
        });
        
        // Show button by default or hide it if there's a time limit
        const buttonVisibility = minDisplaySeconds ? 'display: none;' : '';
        
        // Show timer only if both minDisplaySeconds is set AND showTimer is explicitly true
        const showTimerDiv = minDisplaySeconds && showTimer;
        
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <div class="flow-progress">ステップ ${this.currentStepIndex + 1} / ${this.totalSteps}</div>
                <h2 class="flow-title">${this.escapeHtml(title)}</h2>
                <div class="flow-text">${this.formatContent(content)}</div>
                ${showTimerDiv ? `<div id="instructionTimer" style="text-align: center; color: #666; margin: 20px 0; font-size: 14px;">ボタンは ${minDisplaySeconds} 秒後に表示されます...</div>` : ''}
                <div class="flow-actions" id="instructionActions" style="${buttonVisibility}">
                    <button class="flow-button" onclick="experimentFlow.advanceToNextStep()">${this.escapeHtml(buttonText)}</button>
                </div>
            </div>
        `;
        
        // Start timer if min_display_seconds is set
        if (minDisplaySeconds && minDisplaySeconds > 0) {
            console.log(`[Flow] Starting ${minDisplaySeconds}s timer for instruction`);
            let remainingSeconds = minDisplaySeconds;
            const timerElement = document.getElementById('instructionTimer');
            const actionsElement = document.getElementById('instructionActions');
            
            // Update countdown every second
            const countdownInterval = setInterval(() => {
                remainingSeconds--;
                
                // Update timer text only if showTimer is true and element exists
                if (showTimer && timerElement) {
                    if (remainingSeconds > 0) {
                        timerElement.textContent = `ボタンは ${remainingSeconds} 秒後に表示されます...`;
                    } else {
                        timerElement.textContent = '';
                    }
                }
                
                if (remainingSeconds <= 0) {
                    clearInterval(countdownInterval);
                    console.log('[Flow] Timer completed, showing button');
                    if (actionsElement) {
                        actionsElement.style.display = '';
                        console.log('[Flow] Button display set to visible');
                    }
                    if (timerElement) {
                        timerElement.remove();
                    }
                }
            }, 1000);
        } else {
            console.log('[Flow] No timer set, button visible immediately');
        }
    }
    
    /**
     * アンケートステップ
     */
    showSurveyStep() {
        const title = this.currentStep.title || 'アンケート';
        const description = this.currentStep.survey_description || '';
        let questions = this.currentStep.survey_questions || [];
        const buttonText = this.currentStep.button_text || '送信';
        const randomizeQuestions = this.currentStep.randomize_questions || false;
        
        // 質問をランダム化（フラグが立っている場合）
        if (randomizeQuestions && questions.length > 0) {
            questions = this.shuffleArray([...questions]); // コピーしてシャッフル
            // ランダマイズされた順序を保存
            this.currentStep._shuffled_questions = questions.map(q => q.question_id);
            console.log('[Flow] Survey questions randomized');
        } else {
            // ランダマイズされていない場合も順序を保存
            this.currentStep._shuffled_questions = questions.map(q => q.question_id);
        }
        
        let questionsHtml = '';
        questions.forEach((question, index) => {
            questionsHtml += this.renderQuestion(question, index);
        });
        
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <div class="flow-progress">ステップ ${this.currentStepIndex + 1} / ${this.totalSteps}</div>
                <h2 class="flow-title">${this.escapeHtml(title)}</h2>
                ${description ? `<p class="flow-description">${this.escapeHtml(description)}</p>` : ''}
                <form id="surveyForm" class="survey-form" onsubmit="experimentFlow.handleSurveySubmit(event); return false;">
                    ${questionsHtml}
                    <div class="flow-actions">
                        <button type="submit" class="flow-button">${this.escapeHtml(buttonText)}</button>
                    </div>
                </form>
            </div>
        `;
        
        console.log('[Flow] Survey form rendered with inline onsubmit handler');
    }
    
    /**
     * 質問をレンダリング
     */
    renderQuestion(question, index) {
        const requiredMark = question.required ? '<span class="required-mark"> *</span>' : '';
        let inputHtml = '';
        
        switch (question.question_type) {
            case 'likert':
            case 'scale':  // 旧形式との互換性
                inputHtml = this.renderLikertScale(question);
                break;
            case 'radio':
            case 'single_choice':
            case 'choice':  // Alias for single_choice
                inputHtml = this.renderRadioChoice(question);
                break;
            case 'checkbox':
            case 'multiple_choice':
                inputHtml = this.renderCheckboxChoice(question);
                break;
            case 'text':
                inputHtml = this.renderShortTextInput(question);
                break;
            case 'textarea':
                inputHtml = this.renderTextInput(question);
                break;
            default:
                inputHtml = this.renderTextInput(question);
        }
        
        return `
            <div class="survey-question">
                <label class="survey-question-label">
                    ${index + 1}. ${this.escapeHtml(question.question_text)}${requiredMark}
                </label>
                ${inputHtml}
            </div>
        `;
    }
    
    /**
     * リッカート尺度をレンダリング
     */
    renderLikertScale(question) {
        let html = '<div class="likert-scale">';
        
        // スケール範囲を決定（新形式と旧形式の両方に対応）
        const scalePoints = question.scale || 5; // デフォルト5段階（変更: 7→5）
        const scaleMin = question.scale_min || 1;
        const scaleMax = question.scale_max || scalePoints;
        
        // デバッグ: scaleが正しく読み込まれているか確認
        if (question.scale !== undefined && question.scale !== scalePoints) {
            console.warn(`[Likert] Question ${question.question_id}: scale mismatch. Expected ${question.scale}, using ${scalePoints}`);
        }
        
        // ラベル設定を取得
        const scaleLabels = question.scale_labels || [];
        const minLabel = question.min_label || question.scale_min_label || '';
        const maxLabel = question.max_label || question.scale_max_label || '';
        
        // 個別ラベルがあるか、min/max ラベルのみか
        const hasIndividualLabels = scaleLabels.length > 0 && scaleLabels.some(l => l);
        
        if (hasIndividualLabels) {
            // 個別ラベルモード：各段階にラベルを表示
            html += '<div class="likert-options-with-labels">';
            for (let i = scaleMin; i <= scaleMax; i++) {
                const label = scaleLabels[i - 1] || '';
                html += `
                    <label class="likert-option-labeled">
                        <input type="radio" name="${question.question_id}" value="${i}" ${question.required ? 'required' : ''}>
                        <span class="likert-value">${i}</span>
                        ${label ? `<span class="likert-label-text">${this.escapeHtml(label)}</span>` : ''}
                    </label>
                `;
            }
            html += '</div>';
        } else {
            // min/max ラベルモード
            if (minLabel || maxLabel) {
                html += `
                    <div class="likert-labels">
                        <span class="likert-label-min">${this.escapeHtml(minLabel)}</span>
                        <span class="likert-label-max">${this.escapeHtml(maxLabel)}</span>
                    </div>
                `;
            }
            
            // 選択肢（横並び）
            html += '<div class="likert-options">';
            for (let i = scaleMin; i <= scaleMax; i++) {
                html += `
                    <label class="likert-option">
                        <input type="radio" name="${question.question_id}" value="${i}" ${question.required ? 'required' : ''}>
                        <span>${i}</span>
                    </label>
                `;
            }
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * ラジオボタン選択をレンダリング (radio)
     */
    renderRadioChoice(question) {
        const options = question.options || question.choices || [];
        
        // デバッグログ
        console.log(`[Flow] Rendering radio choice for ${question.question_id}:`, {
            question_text: question.question_text,
            options_count: options.length,
            options: options
        });
        
        if (options.length === 0) {
            console.warn(`[Flow] ⚠️ No options found for radio question: ${question.question_id}`);
            return '<div class="choice-options"><p style="color: #999; font-style: italic;">選択肢が設定されていません。</p></div>';
        }
        
        let html = '<div class="choice-options">';
        options.forEach((option) => {
            html += `
                <label class="choice-option">
                    <input type="radio" name="${question.question_id}" value="${this.escapeHtml(option)}" ${question.required ? 'required' : ''}>
                    <span>${this.escapeHtml(option)}</span>
                </label>
            `;
        });
        html += '</div>';
        return html;
    }
    
    /**
     * 単一選択をレンダリング (旧形式)
     */
    renderSingleChoice(question) {
        return this.renderRadioChoice(question);
    }
    
    /**
     * チェックボックス選択をレンダリング (checkbox)
     */
    renderCheckboxChoice(question) {
        const options = question.options || question.choices || [];
        let html = '<div class="choice-options">';
        options.forEach((option) => {
            html += `
                <label class="choice-option">
                    <input type="checkbox" name="${question.question_id}" value="${this.escapeHtml(option)}">
                    <span>${this.escapeHtml(option)}</span>
                </label>
            `;
        });
        html += '</div>';
        return html;
    }
    
    /**
     * 複数選択をレンダリング (旧形式)
     */
    renderMultipleChoice(question) {
        return this.renderCheckboxChoice(question);
    }
    
    /**
     * 短文テキスト入力をレンダリング (text)
     */
    renderShortTextInput(question) {
        const inputType = question.input_type || 'text';
        // 数値入力の場合、max属性を削除（年齢などで制限をかけない）
        const extraAttrs = inputType === 'number' 
            ? 'min="0" step="1" pattern="[0-9]*"' 
            : (question.max_length ? `maxlength="${question.max_length}"` : '');
        
        return `
            <input 
                type="${inputType}" 
                name="${question.question_id}" 
                class="survey-text-input" 
                ${question.required ? 'required' : ''}
                ${extraAttrs}
                placeholder="${question.placeholder || ''}"
            >
        `;
    }
    
    /**
     * 長文テキスト入力をレンダリング (textarea)
     */
    renderTextInput(question) {
        return `
            <textarea 
                name="${question.question_id}" 
                class="survey-textarea" 
                rows="4"
                ${question.required ? 'required' : ''}
                ${question.max_length ? `maxlength="${question.max_length}"` : ''}
                placeholder="${question.placeholder || ''}"
            ></textarea>
        `;
    }
    
    /**
     * サーベイフォーム送信ハンドラ（inline onsubmit用）
     */
    handleSurveySubmit(event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        console.log('[Flow] ✅ Survey submit intercepted via inline handler');
        
        // 必須項目のバリデーション
        const questions = this.currentStep.survey_questions || [];
        for (const question of questions) {
            if (question.required) {
                const qType = question.question_type;
                let hasAnswer = false;
                
                if (qType === 'likert' || qType === 'scale' || qType === 'radio' || qType === 'single_choice' || qType === 'choice') {
                    const selected = document.querySelector(`input[name="${question.question_id}"]:checked`);
                    hasAnswer = !!selected;
                } else if (qType === 'checkbox' || qType === 'multiple_choice') {
                    const checked = document.querySelectorAll(`input[name="${question.question_id}"]:checked`);
                    hasAnswer = checked.length > 0;
                } else if (qType === 'text') {
                    const input = document.querySelector(`input[name="${question.question_id}"]`);
                    hasAnswer = input && input.value.trim() !== '';
                } else if (qType === 'textarea') {
                    const textarea = document.querySelector(`textarea[name="${question.question_id}"]`);
                    hasAnswer = textarea && textarea.value.trim() !== '';
                }
                
                if (!hasAnswer) {
                    alert(`必須項目に回答してください: ${question.question_text}`);
                    return;
                }
            }
        }
        
        // バリデーションOK、送信処理へ
        this.submitSurvey();
    }
    
    /**
     * アンケートを送信
     */
    async submitSurvey() {
        const questions = this.currentStep.survey_questions || [];
        const responses = [];
        
        // 各質問の回答を収集
        for (const question of questions) {
            let answer = null;
            const qType = question.question_type;
            
            if (qType === 'likert' || qType === 'scale') {
                // リッカート尺度：整数値
                const selected = document.querySelector(`input[name="${question.question_id}"]:checked`);
                answer = selected ? parseInt(selected.value) : null;
            } else if (qType === 'radio' || qType === 'single_choice' || qType === 'choice') {
                // ラジオボタン：選択された値
                const selected = document.querySelector(`input[name="${question.question_id}"]:checked`);
                answer = selected ? selected.value : null;
            } else if (qType === 'checkbox' || qType === 'multiple_choice') {
                // チェックボックス：配列
                const checked = document.querySelectorAll(`input[name="${question.question_id}"]:checked`);
                answer = Array.from(checked).map(cb => cb.value);
            } else if (qType === 'text') {
                // 短文テキスト
                const input = document.querySelector(`input[name="${question.question_id}"]`);
                answer = input ? input.value : null;
                
                // 数値入力の場合、数値かどうかをバリデーション
                if (question.input_type === 'number' && answer !== null && answer !== '') {
                    const numValue = Number(answer);
                    if (isNaN(numValue) || !isFinite(numValue) || numValue < 0) {
                        alert(`${question.question_text}には、0以上の数値を入力してください。`);
                        return;
                    }
                    // 数値として保存（文字列ではなく）
                    answer = numValue;
                }
            } else if (qType === 'textarea') {
                // 長文テキスト
                const textarea = document.querySelector(`textarea[name="${question.question_id}"]`);
                answer = textarea ? textarea.value : null;
            }
            
            responses.push({
                question_id: question.question_id,
                question_text: question.question_text,
                question_type: qType,
                answer: answer
            });
        }
        
        // ランダマイズされた順序情報を含める
        const responseData = {
            survey_responses: responses
        };
        if (this.currentStep._shuffled_questions) {
            responseData.question_order = this.currentStep._shuffled_questions;
        }
        
        // 次のステップへ進む（回答を含む）
        await this.advanceToNextStep(responseData);
    }
    
    /**
     * チャットステップ
     */
    async showChatStep() {
        // チャットコンテナを表示
        this.flowContainer.style.display = 'none';
        this.chatContainer.style.display = 'flex';
        
        // チャットステップのbot設定をサーバーに適用
        try {
            await fetch(`/api/sessions/${this.sessionId}/chat/configure`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    bot_model: this.currentStep.bot_model || 'gemma3:4b',
                    system_prompt: this.currentStep.system_prompt || '',
                    temperature: this.currentStep.temperature !== undefined ? this.currentStep.temperature : 0.7,
                    top_p: this.currentStep.top_p !== undefined ? this.currentStep.top_p : 0.9,
                    top_k: this.currentStep.top_k !== undefined ? this.currentStep.top_k : 40,
                    repeat_penalty: this.currentStep.repeat_penalty !== undefined ? this.currentStep.repeat_penalty : 1.1,
                    num_predict: this.currentStep.num_predict || null,
                    num_thread: this.currentStep.num_thread || null,
                    num_ctx: this.currentStep.num_ctx || null,
                    num_gpu: this.currentStep.num_gpu !== undefined ? this.currentStep.num_gpu : null,
                    num_batch: this.currentStep.num_batch || null
                })
            });
            console.log('[Flow] Chat configuration applied:', {
                model: this.currentStep.bot_model,
                temperature: this.currentStep.temperature,
                top_p: this.currentStep.top_p,
                top_k: this.currentStep.top_k,
                repeat_penalty: this.currentStep.repeat_penalty,
                num_predict: this.currentStep.num_predict,
                num_thread: this.currentStep.num_thread,
                num_ctx: this.currentStep.num_ctx,
                num_gpu: this.currentStep.num_gpu,
                num_batch: this.currentStep.num_batch
            });
        } catch (error) {
            console.error('[Flow] Failed to configure chat:', error);
        }
        
        // 教示文がある場合は表示
        if (this.currentStep.instruction_text && this.currentStep.instruction_text.trim() !== '') {
            const instructionMessage = {
                type: 'instruction',
                message: this.currentStep.instruction_text,
                timestamp: new Date().toISOString()
            };
            
            // displayMessage関数を使用してメッセージを表示
            if (typeof displayMessage === 'function') {
                displayMessage(instructionMessage);
                console.log('[Flow] Instruction message displayed:', this.currentStep.instruction_text);
            }
        }
        
        // タイムリミットを設定（必要なら）
        if (this.currentStep.time_limit_minutes && this.currentStep.time_limit_minutes > 0) {
            this.startChatTimer(this.currentStep.time_limit_minutes);
        }
    }
    
    /**
     * チャットタイマーを開始
     */
    startChatTimer(minutes) {
        const milliseconds = minutes * 60 * 1000;
        
        setTimeout(async () => {
            // チャットセッションを終了してアンケートへ
            const endMessage = {
                type: 'system',
                message: `⏱️ Time limit reached (${minutes} minutes). Moving to next step...`,
                timestamp: new Date().toISOString()
            };
            
            // メッセージを表示（chat.jsのdisplayMessage関数を使用）
            if (typeof displayMessage === 'function') {
                displayMessage(endMessage);
            }
            
            // WebSocketを閉じる
            if (typeof ws !== 'undefined' && ws) {
                ws.close();
            }
            
            // 次のステップに進む
            await this.advanceToNextStep();
        }, milliseconds);
    }
    
    /**
     * デブリーフィングステップ
     */
    showDebriefingStep() {
        const title = this.currentStep.title || '実験へのご協力ありがとうございました';
        const content = this.currentStep.content || '';
        const buttonText = this.currentStep.button_text || '終了';
        
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <div class="flow-progress">ステップ ${this.currentStepIndex + 1} / ${this.totalSteps}</div>
                <h2 class="flow-title">${this.escapeHtml(title)}</h2>
                <div class="flow-text">${this.formatContent(content)}</div>
                <div class="flow-actions">
                    <button class="flow-button" onclick="experimentFlow.finishExperiment()">${this.escapeHtml(buttonText)}</button>
                </div>
            </div>
        `;
    }
    
    /**
     * 次のステップに進む
     */
    async advanceToNextStep(responseData = null) {
        try {
            const response = await fetch(`/api/sessions/${this.sessionId}/flow/advance`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: this.clientId,
                    response: responseData
                })
            });
            
            const data = await response.json();
            
            if (data.completed) {
                // すべてのステップが完了
                this.showCompletionMessage();
                return;
            }
            
            // 次のステップを表示
            this.currentStep = data.next_step;
            this.currentStepIndex = data.current_step_index;
            await this.showCurrentStep();
            
        } catch (error) {
            console.error('[Flow] Error advancing to next step:', error);
            alert('エラーが発生しました。もう一度お試しください。');
        }
    }
    
    /**
     * 実験を終了
     */
    async finishExperiment() {
        // 最後のステップを完了としてマーク
        await this.advanceToNextStep();
        
        // ストレージをクリア
        localStorage.clear();
        sessionStorage.clear();
        
        // ログイン画面へリダイレクト
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    }
    
    /**
     * 完了メッセージを表示
     */
    showCompletionMessage() {
        this.flowContainer.style.display = 'flex';
        this.chatContainer.style.display = 'none';
        
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <h2 class="flow-title">実験完了</h2>
                <div class="flow-text">
                    <p>すべてのステップが完了しました。</p>
                    <p>ご協力ありがとうございました。</p>
                </div>
                <div class="flow-actions">
                    <button class="flow-button" onclick="experimentFlow.finishExperiment()">終了</button>
                </div>
            </div>
        `;
    }
    
    /**
     * 🆕 既に完了済みのメッセージを表示
     */
    showAlreadyCompletedMessage() {
        // コンテナを作成（存在しなければ）
        if (!document.getElementById('flowContainer')) {
            this.createFlowContainer();
        }
        this.flowContainer = document.getElementById('flowContainer');
        this.chatContainer = document.getElementById('chatContainer');
        
        this.flowContainer.style.display = 'flex';
        this.chatContainer.style.display = 'none';
        
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <h2 class="flow-title">実験完了済み</h2>
                <div class="flow-text">
                    <p>あなたは既にこの実験を完了しています。</p>
                    <p>再度参加することはできません。</p>
                    <p>ご協力ありがとうございました。</p>
                </div>
                <div class="flow-actions">
                    <button class="flow-button" onclick="window.location.href='/'">ホームに戻る</button>
                </div>
            </div>
        `;
    }
    
    /**
     * コンテンツをフォーマット（改行を保持）
     */
    formatContent(content) {
        return this.escapeHtml(content).replace(/\n/g, '<br>');
    }
    
    /**
     * HTMLエスケープ
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * AI Evaluation step processing
     * プレイスホルダー: 実際のAI評価は行わず、すぐに次のステップに進む
     */
    async processAIEvaluationStep() {
        console.log('[Flow] 🤖 AI evaluation step (placeholder):', this.currentStep.step_id);
        
        // プレイスホルダー表示
        this.flowContainer.style.display = 'flex';
        this.chatContainer.style.display = 'none';
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <div class="flow-progress">ステップ ${this.currentStepIndex + 1} / ${this.totalSteps}</div>
                <h2 class="flow-title">🤖 AI評価（プレイスホルダー）</h2>
                <div class="flow-text">
                    <p>このステップは現在プレイスホルダーです。</p>
                    <p>実際のAI評価機能は実装中です。</p>
                </div>
                <div class="flow-actions">
                    <button class="flow-button" onclick="experimentFlow.advanceToNextStep()">次へ</button>
                </div>
            </div>
        `;
        
        // 実際のAI評価は行わず、ユーザーが「次へ」ボタンを押すまで待つ
    }
    
    /**
     * Survey Randomizer step - displays multiple surveys in random order
     */
    showSurveyRandomizerStep() {
        // Support both 'steps' (new) and 'surveys' (legacy)
        const items = this.currentStep.steps || this.currentStep.surveys || [];
        
        // 初回実行時にアイテムをシャッフル
        if (!this.currentStep._shuffled_items) {
            this.currentStep._shuffled_items = this.shuffleArray([...items]);
            // ランダマイズされたアイテムの順序を保存
            this.currentStep._item_order = this.currentStep._shuffled_items.map(item => 
                item.survey_id || item.step_id || `item_${this.currentStep._shuffled_items.indexOf(item)}`
            );
            this.currentStep._current_item_index = 0;
            this.currentStep._all_responses = [];
            this.currentStep._temp_step = null;
            console.log(`[Flow] Randomizer: ${items.length} items shuffled`);
        }
        
        const currentIndex = this.currentStep._current_item_index;
        const shuffledItems = this.currentStep._shuffled_items;
        
        if (currentIndex >= shuffledItems.length) {
            // すべてのアイテムが完了 - 次のステップへ
            console.log('[Flow] Randomizer: All items completed');
            const responseData = {
                randomizer_responses: this.currentStep._all_responses
            };
            // アイテムの順序情報を含める
            if (this.currentStep._item_order) {
                responseData.item_order = this.currentStep._item_order;
            }
            this.advanceToNextStep(responseData);
            return;
        }
        
        // 現在のアイテムを表示
        const currentItem = shuffledItems[currentIndex];
        const itemType = currentItem.step_type || (currentItem.survey_questions ? 'survey' : 'unknown');
        
        // Store current item as temporary step
        this.currentStep._temp_step = currentItem;
        
        // Display based on item type
        if (itemType === 'survey') {
            this.showRandomizerSurveyItem(currentItem, currentIndex, shuffledItems.length);
        } else if (itemType === 'instruction') {
            this.showRandomizerInstructionItem(currentItem, currentIndex, shuffledItems.length);
        } else {
            console.error(`[Flow] Unknown randomizer item type: ${itemType}`);
            alert('Unknown item type. Skipping...');
            this.currentStep._current_item_index++;
            this.showSurveyRandomizerStep();
        }
    }
    
    showRandomizerSurveyItem(item, currentIndex, totalItems) {
        const title = item.title || `アンケート (${currentIndex + 1}/${totalItems})`;
        const description = item.survey_description || '';
        let questions = item.survey_questions || [];
        const buttonText = item.button_text || '次へ';
        const randomizeQuestions = item.randomize_questions || false;
        
        // 質問をランダム化（フラグが立っている場合）
        if (randomizeQuestions && questions.length > 0) {
            questions = this.shuffleArray([...questions]); // コピーしてシャッフル
            // ランダマイズされた質問の順序を保存
            item._shuffled_questions = questions.map(q => q.question_id);
            console.log('[Flow] Randomizer survey questions randomized');
        } else {
            // ランダマイズされていない場合も順序を保存
            item._shuffled_questions = questions.map(q => q.question_id);
        }
        
        let questionsHtml = '';
        questions.forEach((question, index) => {
            questionsHtml += this.renderQuestion(question, index);
        });
        
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <div class="flow-progress">ステップ ${this.currentStepIndex + 1} / ${this.totalSteps} (${currentIndex + 1}/${totalItems})</div>
                <h2 class="flow-title">${this.escapeHtml(title)}</h2>
                ${description ? `<p class="flow-description">${this.escapeHtml(description)}</p>` : ''}
                <form id="surveyForm" class="survey-form" onsubmit="experimentFlow.handleSurveyRandomizerSubmit(event); return false;">
                    ${questionsHtml}
                    <div class="flow-actions">
                        <button type="submit" class="flow-button">${this.escapeHtml(buttonText)}</button>
                    </div>
                </form>
            </div>
        `;
    }
    
    showRandomizerInstructionItem(item, currentIndex, totalItems) {
        const title = item.title || `教示 (${currentIndex + 1}/${totalItems})`;
        const content = item.content || '';
        const buttonText = item.button_text || '次へ';
        const minDisplaySeconds = item.min_display_seconds;
        // show_timerが明示的にtrueの場合のみ表示、それ以外（false/null/undefined）は非表示
        const showTimer = item.show_timer === true;
        
        const buttonVisibility = minDisplaySeconds ? 'display: none;' : '';
        const showTimerDiv = minDisplaySeconds && showTimer;
        
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <div class="flow-progress">ステップ ${this.currentStepIndex + 1} / ${this.totalSteps} (${currentIndex + 1}/${totalItems})</div>
                <h2 class="flow-title">${this.escapeHtml(title)}</h2>
                <div class="flow-text">${this.formatContent(content)}</div>
                ${showTimerDiv ? `<div id="randomizerTimer" style="text-align: center; color: #666; margin: 20px 0; font-size: 14px;">ボタンは ${minDisplaySeconds} 秒後に表示されます...</div>` : ''}
                <div class="flow-actions" id="randomizerActions" style="${buttonVisibility}">
                    <button class="flow-button" onclick="experimentFlow.handleRandomizerInstructionNext()">${this.escapeHtml(buttonText)}</button>
                </div>
            </div>
        `;
        
        // Start timer if needed
        if (minDisplaySeconds && minDisplaySeconds > 0) {
            let remainingSeconds = minDisplaySeconds;
            const timerElement = document.getElementById('randomizerTimer');
            const actionsElement = document.getElementById('randomizerActions');
            
            const countdownInterval = setInterval(() => {
                remainingSeconds--;
                
                if (showTimer && timerElement) {
                    if (remainingSeconds > 0) {
                        timerElement.textContent = `ボタンは ${remainingSeconds} 秒後に表示されます...`;
                    } else {
                        timerElement.textContent = '';
                    }
                }
                
                if (remainingSeconds <= 0) {
                    clearInterval(countdownInterval);
                    if (actionsElement) {
                        actionsElement.style.display = '';
                    }
                    if (timerElement) {
                        timerElement.remove();
                    }
                }
            }, 1000);
        }
    }
    
    handleRandomizerInstructionNext() {
        // Move to next item in randomizer
        this.currentStep._current_item_index++;
        this.showSurveyRandomizerStep();
    }
    
    /**
     * Handle survey randomizer submit
     */
    handleSurveyRandomizerSubmit(event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        console.log('[Flow] Randomizer submit intercepted');
        
        const currentIndex = this.currentStep._current_item_index;
        const currentItem = this.currentStep._shuffled_items[currentIndex];
        const questions = currentItem.survey_questions || [];
        
        // バリデーション
        for (const question of questions) {
            if (question.required) {
                const qType = question.question_type;
                let hasAnswer = false;
                
                if (qType === 'likert' || qType === 'scale' || qType === 'radio' || qType === 'single_choice' || qType === 'choice') {
                    const selected = document.querySelector(`input[name="${question.question_id}"]:checked`);
                    hasAnswer = !!selected;
                } else if (qType === 'checkbox' || qType === 'multiple_choice') {
                    const checked = document.querySelectorAll(`input[name="${question.question_id}"]:checked`);
                    hasAnswer = checked.length > 0;
                } else if (qType === 'text') {
                    const input = document.querySelector(`input[name="${question.question_id}"]`);
                    hasAnswer = input && input.value.trim() !== '';
                } else if (qType === 'textarea') {
                    const textarea = document.querySelector(`textarea[name="${question.question_id}"]`);
                    hasAnswer = textarea && textarea.value.trim() !== '';
                }
                
                if (!hasAnswer) {
                    alert(`必須項目に回答してください: ${question.question_text}`);
                    return;
                }
            }
        }
        
        // 回答を収集
        const responses = [];
        for (const question of questions) {
            let answer = null;
            const qType = question.question_type;
            
            if (qType === 'likert' || qType === 'scale') {
                const selected = document.querySelector(`input[name="${question.question_id}"]:checked`);
                answer = selected ? parseInt(selected.value) : null;
            } else if (qType === 'radio' || qType === 'single_choice' || qType === 'choice') {
                const selected = document.querySelector(`input[name="${question.question_id}"]:checked`);
                answer = selected ? selected.value : null;
            } else if (qType === 'checkbox' || qType === 'multiple_choice') {
                const checked = document.querySelectorAll(`input[name="${question.question_id}"]:checked`);
                answer = Array.from(checked).map(cb => cb.value);
            } else if (qType === 'text') {
                const input = document.querySelector(`input[name="${question.question_id}"]`);
                answer = input ? input.value : null;
                
                // 数値入力の場合、数値かどうかをバリデーション
                if (question.input_type === 'number' && answer !== null && answer !== '') {
                    const numValue = Number(answer);
                    if (isNaN(numValue) || !isFinite(numValue) || numValue < 0) {
                        alert(`${question.question_text}には、0以上の数値を入力してください。`);
                        return;
                    }
                    // 数値として保存（文字列ではなく）
                    answer = numValue;
                }
            } else if (qType === 'textarea') {
                const textarea = document.querySelector(`textarea[name="${question.question_id}"]`);
                answer = textarea ? textarea.value : null;
            }
            
            responses.push({
                question_id: question.question_id,
                question_text: question.question_text,
                question_type: qType,
                answer: answer,
                item_id: currentItem.survey_id || currentItem.step_id || `item_${currentIndex}`,
                item_type: currentItem.step_type || 'survey',
                item_order: currentIndex + 1  // アイテム内での順序
            });
        }
        
        // ランダマイズされた質問の順序情報を追加
        if (currentItem._shuffled_questions) {
            responses.forEach((resp, idx) => {
                resp.question_order = currentItem._shuffled_questions;
                resp.question_index = currentItem._shuffled_questions.indexOf(resp.question_id) + 1;
            });
        }
        
        // 回答を保存
        this.currentStep._all_responses.push(...responses);
        
        // 次のアイテムへ
        this.currentStep._current_item_index++;
        this.showSurveyRandomizerStep();
    }
    
    /**
     * Array shuffle utility (Fisher-Yates algorithm)
     */
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
    
    /**
     * Branch step processing
     * Simply record that this branch point was passed
     */
    async processBranchStep() {
        console.log('[Flow] 🔀 Processing branch step:', this.currentStep.step_id);
        
        // ブランチステップは自動的に次のステップに進む
        // サーバー側でランダム割り当てや条件分岐が処理される
        await this.advanceToNextStep();
    }
    
    /**
     * デバッグ情報を画面に表示（スマホ用）
     * グローバル関数があればそれを使用
     */
    showDebugInfo(message) {
        if (typeof window.showDebugInfo === 'function') {
            window.showDebugInfo(message);
        } else {
            console.log('[Debug]', message);
        }
    }
}

// グローバル変数として定義（chat.jsから参照できるように）
let experimentFlow = null;

