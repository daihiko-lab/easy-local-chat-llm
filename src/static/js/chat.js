let ws = null;
// const clientId = "client-" + Math.random().toString(36).substr(2, 5);

// 黄金比を使用してより均一な分布を得る
const GOLDEN_RATIO = 0.618033988749895;

// シード値から擬似乱数を生成するジェネレータ
function createRandomGenerator(seed) {
    // シード値からハッシュ値を生成
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
        hash = seed.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // 擬似乱数生成関数を返す
    return function() {
        // xorshiftアルゴリズムを使用
        hash ^= hash << 13;
        hash ^= hash >> 17;
        hash ^= hash << 5;
        return (hash >>> 0) / 4294967296; // 0から1の範囲に正規化
    };
}

// より多様な色を生成するバージョン
function getColorFromClientId(clientId) {
    const random = createRandomGenerator(clientId);
    
    // 複数の要素から色を生成
    const baseHue = (random() + GOLDEN_RATIO) % 1;
    const hueOffset = random() * 30 - 15;  // ±15度のばらつき
    
    const h = Math.floor((baseHue * 360 + hueOffset + 360) % 360);
    const s = 65 + random() * 25;  // 彩度: 65-90%
    const l = 50 + random() * 15;  // 明度: 50-65%
    
    return `hsl(${h}, ${s}%, ${l}%)`;
}

// 色のプリセットを定義（必要に応じて）
const COLOR_PRESETS = {
    'admin': 'hsl(210, 80%, 60%)',      // 管理者用の青
    'moderator': 'hsl(280, 75%, 60%)',  // モデレーター用の紫
    'system': 'hsl(0, 0%, 50%)'         // システムメッセージ用のグレー
};

// クライアントIDから色を取得（プリセットがある場合はそちらを優先）
function getClientColor(clientId) {
    return COLOR_PRESETS[clientId] || getColorFromClientId(clientId);
}

let clientId;
let currentSessionId;

async function connect() {
    // リロード検出：既にチャットセッションが開始されている場合、ログイン画面に戻す
    if (sessionStorage.getItem('chat_session_active') === 'true') {
        alert('Page reload is not allowed during the experiment. Please log in again.');
        sessionStorage.removeItem('chat_session_active');
        window.location.href = '/';
        return;
    }
    
    // 初回訪問フラグを設定
    sessionStorage.setItem('chat_session_active', 'true');

    // トークンとクライアントIDを取得
    let token = null;
    const urlParams = new URLSearchParams(window.location.search);
    token = urlParams.get('token');

    // window.CHAT_CONFIGから取得（常に新規セッション）
    if (!token && window.CHAT_CONFIG) {
        token = window.CHAT_CONFIG.token;
    }
    
    if (!token) {
        alert('Invalid access. Please log in again.');
        window.location.href = '/';
        return;
    }
    
    // クライアントIDと条件IDを取得
    clientId = window.CHAT_CONFIG ? window.CHAT_CONFIG.client_id : null;
    let conditionId = window.CHAT_CONFIG ? window.CHAT_CONFIG.condition_id : null;
    
    if (!clientId) {
        alert('Client ID is required.');
        window.location.href = '/';
        return;
    }
    
    // 実験では常に新規セッション作成（念のためストレージをクリア）
    sessionId = null;  // 常にnull
    localStorage.clear();  // すべてクリア（ログイン画面でも既にクリア済み）

    // グローバル変数に保存
    currentSessionId = null;  // 常に新規セッション

    // WebSocket接続URL（常に新規セッション）
    const wsUrl = `ws://${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = async function() {
        document.getElementById('status-text').textContent = 'Online';
        document.getElementById('status-icon').className = 'online';
        document.getElementById('client-id').textContent = `Client ID: ${clientId}`;
        
        // 参加メッセージを送信（tokenとcondition_idを含む）
        const joinMessage = {
            type: 'join',
            token: token,
            client_id: clientId,
            condition_id: conditionId,  // 常に新規セッション
            timestamp: new Date().toISOString()
        };
        ws.send(JSON.stringify(joinMessage));
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // セッション作成メッセージの処理
        if (data.type === 'session_created') {
            currentSessionId = data.session_id;
            // 実験ではlocalStorageを使用しない（リロード検出のため）
            // セッション表示を更新
            const sessionElement = document.getElementById('session-id');
            if (sessionElement) {
                sessionElement.textContent = data.session_id;
            }
            
            // タイムリミットを設定（セッション作成時に開始）
            startTimeLimitIfNeeded();
        } else if (data.type === 'instruction') {
            // 教示文メッセージの処理（joinメッセージの後にサーバーから送信される）
            displayMessage(data);
        } else if (data.type === 'session_end') {
            displayMessage(data);
            // すべてのストレージをクリア
            localStorage.clear();
            sessionStorage.clear();
            // 3秒後にログイン画面へリダイレクト
            setTimeout(() => {
                alert('Session has been ended. Please login again.');
                window.location.href = '/';
            }, 3000);
        } else if (data.type === 'bot') {
            // ボットメッセージの処理
            displayMessage(data);
        } else {
            displayMessage(data);
        }
    };

    ws.onclose = function(event) {
        if (event.reason === "Client ID already in use") {
            alert("This ID is already in use. Please log in with a different ID.");
            window.location.href = '/'; // ログインページに戻す
        } else if (event.reason === "Only one user allowed") {
            alert("Another user is currently connected. Please try again later.");
            window.location.href = '/'; // Return to login page
        } else {
            document.getElementById('status-text').textContent = 'Offline';
            document.getElementById('status-icon').className = 'offline';
        }
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (message && ws && ws.readyState === WebSocket.OPEN) {
        const messageData = {
            type: 'message',
            client_id: clientId,
            message: message,
            timestamp: new Date().toISOString()
        };
        
        ws.send(JSON.stringify(messageData));
        input.value = '';
    }
}

function sendSystemMessage(type) {
    if (ws) {
        const messageData = {
            type: type,
            client_id: clientId,
            timestamp: new Date().toISOString()
        };
        ws.send(JSON.stringify(messageData));
    }
}

function displayMessage(data) {
    const messageArea = document.getElementById('messageArea');
    const messageDiv = document.createElement('div');

    // システムメッセージの場合、特別なクラスを追加
    if (data.type === 'system' || data.type === 'session_end' || data.type === 'instruction') {
        messageDiv.className = `message system`;
        if (data.type === 'session_end') {
            messageDiv.style.backgroundColor = '#fff3cd';
            messageDiv.style.color = '#856404';
            messageDiv.style.fontWeight = 'bold';
        } else if (data.type === 'instruction') {
            // 教示文は目立つスタイルで表示
            messageDiv.style.backgroundColor = '#e3f2fd';
            messageDiv.style.color = '#1565c0';
            messageDiv.style.fontWeight = 'bold';
            messageDiv.style.fontStyle = 'normal';
            messageDiv.style.borderLeft = '4px solid #1976d2';
            messageDiv.style.padding = '12px 15px';
        }
        messageDiv.textContent = data.message; // メッセージ内容を直接設定
    } else {
        // ボットメッセージか判定
        const isBot = data.type === 'bot' || data.client_id === 'bot';
        
        messageDiv.className = `message ${data.client_id === clientId ? 'self' : 'other'}`;
        if (isBot) {
            messageDiv.className = 'message other bot-message';
        }

        // メッセージコンテナを作成
        const messageContainer = document.createElement('div');
        messageContainer.className = 'message-container';

        // アイコンを表示
        const iconDiv = document.createElement('div');
        iconDiv.className = 'message-icon';
        // 内部ID（internal_id）を使って色を生成（ランダム性を確保）
        const colorId = data.internal_id || data.client_id;
        iconDiv.style.backgroundColor = getColorFromClientId(colorId);
        const img = document.createElement('img');
        img.src = `/static/images/default_icon.png`; // アイコンのパス
        iconDiv.appendChild(img);
        messageContainer.appendChild(iconDiv);

        // メッセージテキストを表示
        const messageTextDiv = document.createElement('div');
        messageTextDiv.className = 'message-text';
        
        // クライアントIDを表示
        const clientIdSpan = document.createElement('span');
        clientIdSpan.className = 'client-id';
        // 既に上で定義されたcolorIdを使用
        if (isBot) {
            clientIdSpan.textContent = 'AI Assistant';
            clientIdSpan.style.color = getColorFromClientId(colorId);
            clientIdSpan.style.fontWeight = 'bold';
        } else {
            clientIdSpan.textContent = `Client ID: ${data.client_id}`;
        }
        messageTextDiv.appendChild(clientIdSpan);
        messageTextDiv.appendChild(document.createElement('br')); // 改行を追加
        
        // メッセージ内容を改行を保持して表示
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // ボットメッセージの場合はMarkdownをレンダリング
        if (isBot) {
            // Markdownをパース
            const renderer = new marked.Renderer();
            
            // コードブロックのカスタムレンダラー
            renderer.code = function(code, language) {
                const validLanguage = hljs.getLanguage(language) ? language : 'plaintext';
                const highlighted = hljs.highlight(code, { language: validLanguage }).value;
                return `<pre><code class="hljs language-${validLanguage}">${highlighted}</code></pre>`;
            };
            
            // インラインコードのカスタムレンダラー
            renderer.codespan = function(code) {
                return `<code class="inline-code">${code}</code>`;
            };
            
            marked.setOptions({
                renderer: renderer,
                breaks: true,  // 改行を<br>に変換
                gfm: true,     // GitHub Flavored Markdown
            });
            
            messageContent.innerHTML = marked.parse(data.message);
        } else {
            // ユーザーメッセージは通常通りテキストで表示
            messageContent.style.whiteSpace = 'pre-wrap'; // 改行を保持
            messageContent.textContent = data.message;
        }
        
        messageTextDiv.appendChild(messageContent);

        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = new Date(data.timestamp).toLocaleString();
        messageTextDiv.appendChild(timestamp);

        messageContainer.appendChild(messageTextDiv);
        messageDiv.appendChild(messageContainer);
    }

    messageArea.appendChild(messageDiv);
    messageArea.scrollTop = messageArea.scrollHeight;
}

// エンターキーでメッセージを送信
document.getElementById('messageInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// 過去のメッセージを読み込む関数
async function loadPastMessages() {
    try {
        // セッションIDが設定されていない場合は何もしない
        if (!currentSessionId) {
            return;
        }
        
        // セッションのメッセージを取得
        const messagesResponse = await fetch(`/api/sessions/${currentSessionId}/messages`);
        if (!messagesResponse.ok) {
            return;
        }
        
        const data = await messagesResponse.json();
        const messages = data.messages;
        
        // 自分が最初に参加した時刻を探す
        let myJoinTime = null;
        for (const msg of messages) {
            if (msg.message_type === 'system' && 
                msg.client_id === clientId && 
                msg.content.includes('joined')) {
                myJoinTime = new Date(msg.timestamp);
                break;
            }
        }
        
        // 自分が参加した記録がない場合は、履歴を表示しない（初回参加）
        if (!myJoinTime) {
            return;
        }
        
        // 自分が参加した時刻以降のメッセージのみを表示
        let loadedCount = 0;
        messages.forEach(msg => {
            const msgTime = new Date(msg.timestamp);
            
            // 自分の参加時刻より前のメッセージはスキップ
            if (msgTime < myJoinTime) {
                return;
            }
            
            // 自分の最初の参加メッセージはスキップ（新しく送信されるため）
            if (msg.message_type === 'system' && 
                msg.client_id === clientId && 
                msg.content.includes('joined') &&
                Math.abs(msgTime - myJoinTime) < 1000) {  // 1秒以内なら同じメッセージ
                return;
            }
            
            // メッセージを画面に表示
            displayMessage({
                type: msg.message_type,
                client_id: msg.client_id,
                message: msg.content,
                timestamp: msg.timestamp
            });
            
            loadedCount++;
        });
    } catch (error) {
        console.error('[loadPastMessages] Error:', error);
    }
}

// 初期接続
connect();

// 色の衝突を検証するテスト関数
function testColorDistribution(numUsers) {
    const colors = new Set();
    for (let i = 0; i < numUsers; i++) {
        const userId = `user${i}`;
        colors.add(getClientColor(userId));
    }
}

// テスト実行
// testColorDistribution(100);

// ログアウト機能
function logout() {
    if (confirm('ログアウトしますか？')) {
        // WebSocket接続を閉じる
        if (ws) {
            ws.close();
        }
        
        // すべてのストレージをクリア（実験の完全性を保つ）
        localStorage.clear();
        sessionStorage.clear();
        
        // ログインページへリダイレクト
        window.location.href = '/';
    }
}

// 教示文を表示（条件に設定されている場合）
function showInstructionIfNeeded() {
    const instructionText = window.CHAT_CONFIG.instruction_text;
    
    if (!instructionText || instructionText.trim() === '') {
        return;  // 教示文がない場合は何もしない
    }
    
    // 教示文メッセージとして表示
    const instructionMessage = {
        type: 'instruction',
        message: instructionText,
        timestamp: new Date().toISOString()
    };
    
    displayMessage(instructionMessage);
}

// タイムリミットを設定（条件に設定されている場合）
function startTimeLimitIfNeeded() {
    const timeLimitMinutes = window.CHAT_CONFIG.time_limit_minutes;
    
    if (!timeLimitMinutes || timeLimitMinutes <= 0) {
        return;  // タイムリミットが設定されていない場合は何もしない
    }
    
    const timeLimitMs = timeLimitMinutes * 60 * 1000;  // 分をミリ秒に変換
    
    // 指定時間後にセッションを終了
    setTimeout(() => {
        
        // 終了メッセージを表示
        const endMessage = {
            type: 'system',
            message: `⏱️ Time limit reached (${timeLimitMinutes} minutes). Thank you for participating!`,
            timestamp: new Date().toISOString()
        };
        displayMessage(endMessage);
        
        // WebSocketを閉じる
        if (ws) {
            ws.close();
        }
        
        // アンケートがある場合は表示、ない場合はログイン画面へ
        const surveyQuestions = window.CHAT_CONFIG.survey_questions;
        if (surveyQuestions && surveyQuestions.length > 0) {
            // アンケートを表示
            showSurvey();
        } else {
            // すべてのストレージをクリア
            localStorage.clear();
            sessionStorage.clear();
            
            // 3秒後にログイン画面へリダイレクト
            setTimeout(() => {
                alert(`Session ended. Time limit: ${timeLimitMinutes} minutes.`);
                window.location.href = '/';
            }, 3000);
        }
    }, timeLimitMs);
}

// アンケートを表示
function showSurvey() {
    const surveyQuestions = window.CHAT_CONFIG.survey_questions;
    
    if (!surveyQuestions || surveyQuestions.length === 0) {
        // アンケートがない場合は何もしない
        return;
    }
    
    // チャット画面を非表示
    document.getElementById('chatContainer').style.display = 'none';
    
    // アンケート画面を表示
    const surveyContainer = document.getElementById('surveyContainer');
    surveyContainer.style.display = 'flex';
    
    // タイトルと説明を設定
    document.getElementById('surveyTitle').textContent = window.CHAT_CONFIG.survey_title || 'アンケート';
    const descElement = document.getElementById('surveyDescription');
    if (window.CHAT_CONFIG.survey_description) {
        descElement.textContent = window.CHAT_CONFIG.survey_description;
        descElement.style.display = 'block';
    } else {
        descElement.style.display = 'none';
    }
    
    // 質問を生成
    const questionsContainer = document.getElementById('surveyQuestions');
    questionsContainer.innerHTML = '';
    
    surveyQuestions.forEach((question, index) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'survey-question';
        
        // 質問テキスト
        const questionLabel = document.createElement('label');
        questionLabel.className = 'survey-question-label';
        questionLabel.textContent = `${index + 1}. ${question.question_text}`;
        if (question.required) {
            const requiredSpan = document.createElement('span');
            requiredSpan.className = 'required-mark';
            requiredSpan.textContent = ' *';
            questionLabel.appendChild(requiredSpan);
        }
        questionDiv.appendChild(questionLabel);
        
        // 質問タイプに応じた入力要素を生成
        if (question.question_type === 'likert') {
            // リッカート尺度
            const scaleContainer = document.createElement('div');
            scaleContainer.className = 'likert-scale';
            
            // ラベル行
            if (question.scale_min_label || question.scale_max_label) {
                const labelsDiv = document.createElement('div');
                labelsDiv.className = 'likert-labels';
                
                const minLabel = document.createElement('span');
                minLabel.className = 'likert-label-min';
                minLabel.textContent = question.scale_min_label || '';
                labelsDiv.appendChild(minLabel);
                
                const maxLabel = document.createElement('span');
                maxLabel.className = 'likert-label-max';
                maxLabel.textContent = question.scale_max_label || '';
                labelsDiv.appendChild(maxLabel);
                
                scaleContainer.appendChild(labelsDiv);
            }
            
            // スケール選択肢
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'likert-options';
            
            for (let i = question.scale_min; i <= question.scale_max; i++) {
                const optionLabel = document.createElement('label');
                optionLabel.className = 'likert-option';
                
                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.name = question.question_id;
                radio.value = i;
                radio.required = question.required;
                
                const span = document.createElement('span');
                span.textContent = i;
                
                optionLabel.appendChild(radio);
                optionLabel.appendChild(span);
                optionsDiv.appendChild(optionLabel);
            }
            
            scaleContainer.appendChild(optionsDiv);
            questionDiv.appendChild(scaleContainer);
            
        } else if (question.question_type === 'single_choice') {
            // 単一選択
            const choicesContainer = document.createElement('div');
            choicesContainer.className = 'choice-options';
            
            question.choices.forEach((choice, choiceIndex) => {
                const choiceLabel = document.createElement('label');
                choiceLabel.className = 'choice-option';
                
                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.name = question.question_id;
                radio.value = choice;
                radio.required = question.required;
                
                const span = document.createElement('span');
                span.textContent = choice;
                
                choiceLabel.appendChild(radio);
                choiceLabel.appendChild(span);
                choicesContainer.appendChild(choiceLabel);
            });
            
            questionDiv.appendChild(choicesContainer);
            
        } else if (question.question_type === 'multiple_choice') {
            // 複数選択
            const choicesContainer = document.createElement('div');
            choicesContainer.className = 'choice-options';
            
            question.choices.forEach((choice, choiceIndex) => {
                const choiceLabel = document.createElement('label');
                choiceLabel.className = 'choice-option';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.name = question.question_id;
                checkbox.value = choice;
                if (question.required && choiceIndex === 0) {
                    checkbox.required = true;  // 少なくとも1つ必須
                }
                
                const span = document.createElement('span');
                span.textContent = choice;
                
                choiceLabel.appendChild(checkbox);
                choiceLabel.appendChild(span);
                choicesContainer.appendChild(choiceLabel);
            });
            
            questionDiv.appendChild(choicesContainer);
            
        } else if (question.question_type === 'text') {
            // 自由記述
            const textarea = document.createElement('textarea');
            textarea.name = question.question_id;
            textarea.className = 'survey-textarea';
            textarea.required = question.required;
            if (question.max_length) {
                textarea.maxLength = question.max_length;
            }
            textarea.rows = 4;
            questionDiv.appendChild(textarea);
        }
        
        questionsContainer.appendChild(questionDiv);
    });
    
    // フォーム送信イベント
    document.getElementById('surveyForm').onsubmit = async (e) => {
        e.preventDefault();
        await submitSurvey();
    };
}

// アンケート回答を送信
async function submitSurvey() {
    const surveyQuestions = window.CHAT_CONFIG.survey_questions;
    const responses = [];
    
    // 各質問の回答を収集
    for (const question of surveyQuestions) {
        let answer = null;
        
        if (question.question_type === 'likert' || question.question_type === 'single_choice') {
            // ラジオボタン
            const selected = document.querySelector(`input[name="${question.question_id}"]:checked`);
            if (selected) {
                answer = question.question_type === 'likert' ? parseInt(selected.value) : selected.value;
            }
        } else if (question.question_type === 'multiple_choice') {
            // チェックボックス（複数選択）
            const checked = document.querySelectorAll(`input[name="${question.question_id}"]:checked`);
            answer = Array.from(checked).map(cb => cb.value);
        } else if (question.question_type === 'text') {
            // テキストエリア
            const textarea = document.querySelector(`textarea[name="${question.question_id}"]`);
            answer = textarea ? textarea.value : null;
        }
        
        responses.push({
            question_id: question.question_id,
            answer: answer
        });
    }
    
    // サーバーに送信
    try {
        const response = await fetch(`/api/sessions/${currentSessionId}/survey`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_id: clientId,
                responses: responses
            })
        });
        
        if (response.ok) {
            // 送信成功
            document.getElementById('surveyForm').style.display = 'none';
            document.getElementById('surveyThankYou').style.display = 'block';
            
            // すべてのストレージをクリア
            localStorage.clear();
            sessionStorage.clear();
            
            // 3秒後にログイン画面へリダイレクト
            setTimeout(() => {
                window.location.href = '/';
            }, 3000);
        } else {
            alert('アンケートの送信に失敗しました。もう一度お試しください。');
        }
    } catch (error) {
        console.error('Survey submission error:', error);
        alert('アンケートの送信中にエラーが発生しました。');
    }
} 