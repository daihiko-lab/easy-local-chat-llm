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
            const response = await fetch(`/api/sessions/${this.sessionId}/flow/current?client_id=${this.clientId}`);
            const data = await response.json();
            
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
            
            if (data.completed) {
                // すべてのステップが完了
                this.showCompletionMessage();
                return true;
            }
            
            // フロー情報を保存
            this.currentStep = data.current_step;
            this.currentStepIndex = data.current_step_index;
            this.totalSteps = data.total_steps;
            
            // DOM要素を取得
            this.chatContainer = document.getElementById('chatContainer');
            
            // フロー用コンテナを作成（存在しなければ）
            if (!document.getElementById('flowContainer')) {
                this.createFlowContainer();
            }
            this.flowContainer = document.getElementById('flowContainer');
            
            // 最初のステップを表示
            await this.showCurrentStep();
            
            return true;
            
        } catch (error) {
            console.error('[Flow] Error initializing:', error);
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
     * アンケートステップ
     */
    showSurveyStep() {
        const title = this.currentStep.title || 'アンケート';
        const description = this.currentStep.survey_description || '';
        const questions = this.currentStep.survey_questions || [];
        const buttonText = this.currentStep.button_text || '送信';
        
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
        const scalePoints = question.scale || 7; // デフォルト7段階
        const scaleMin = question.scale_min || 1;
        const scaleMax = question.scale_max || scalePoints;
        
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
        const extraAttrs = inputType === 'number' 
            ? 'min="0" max="150" step="1"' 
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
        
        // 次のステップへ進む（回答を含む）
        await this.advanceToNextStep({ survey_responses: responses });
    }
    
    /**
     * チャットステップ
     */
    showChatStep() {
        // チャットコンテナを表示
        this.flowContainer.style.display = 'none';
        this.chatContainer.style.display = 'flex';
        
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
     * Automatically evaluates the previous chat session
     */
    async processAIEvaluationStep() {
        console.log('[Flow] 🤖 Processing AI evaluation step:', this.currentStep.step_id);
        
        // ローディング表示
        this.flowContainer.style.display = 'flex';
        this.chatContainer.style.display = 'none';
        this.flowContainer.innerHTML = `
            <div class="flow-content">
                <div class="flow-progress">ステップ ${this.currentStepIndex + 1} / ${this.totalSteps}</div>
                <h2 class="flow-title">🤖 AIによる評価中...</h2>
                <div class="flow-text">
                    <p>AIがチャット内容を分析しています。</p>
                    <p>しばらくお待ちください...</p>
                    <div style="text-align: center; margin-top: 30px;">
                        <div class="spinner"></div>
                    </div>
                </div>
            </div>
        `;
        
        try {
            // AI評価APIを呼び出し
            const response = await fetch(`/api/sessions/${this.sessionId}/ai_evaluate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: this.clientId,
                    step_id: this.currentStep.step_id,
                    evaluation_config: {
                        target_session: this.sessionId,
                        questions: this.currentStep.evaluation_questions || [],
                        evaluation_model: this.currentStep.evaluation_model || 'gemma2:9b',
                        context_prompt: this.currentStep.context_prompt || ''
                    }
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                console.log('[Flow] AI evaluation completed:', data);
                // 評価完了後、次のステップに進む
                await this.advanceToNextStep({ ai_evaluation: data.results });
            } else {
                console.error('[Flow] AI evaluation failed:', data);
                alert('AI評価でエラーが発生しました。次のステップに進みます。');
                await this.advanceToNextStep();
            }
        } catch (error) {
            console.error('[Flow] Error during AI evaluation:', error);
            alert('AI評価でエラーが発生しました。次のステップに進みます。');
            await this.advanceToNextStep();
        }
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
}

// グローバル変数として定義（chat.jsから参照できるように）
let experimentFlow = null;

