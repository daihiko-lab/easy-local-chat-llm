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
    'system': 'hsl(0, 0%, 50%)',        // システムメッセージ用のグレー
    'bot': 'hsl(150, 70%, 50%)'         // ボット用の緑
};

// クライアントIDから色を取得（プリセットがある場合はそちらを優先）
function getClientColor(clientId) {
    return COLOR_PRESETS[clientId] || getColorFromClientId(clientId);
}

let clientId;
let currentSessionId;

async function checkSession() {
    // 現在のセッションIDを取得
    try {
        const response = await fetch('/api/sessions/current/info');
        if (response.ok) {
            const data = await response.json();
            const currentSessionId = data.session.session_id;
            const savedSessionId = localStorage.getItem('session_id');
            
            // 保存されたセッションIDと現在のセッションIDが異なる場合
            if (savedSessionId && savedSessionId !== currentSessionId) {
                // Session changed, logout
                console.log('Session has been updated. Re-login required.');
                localStorage.removeItem('client_id');
                localStorage.removeItem('session_id');
                alert('A new session has been started. Please log in again.');
                window.location.href = '/';
                return false;
            }
            
            // 現在のセッションIDを保存
            localStorage.setItem('session_id', currentSessionId);
            return true;
        }
    } catch (error) {
        console.error('Session check error:', error);
    }
    return true;
}

async function connect() {
    // セッションチェック
    const sessionValid = await checkSession();
    if (!sessionValid) {
        return;
    }

    // クエリパラメータからclient_id、session_id、パスワード類を取得
    const urlParams = new URLSearchParams(window.location.search);
    clientId = urlParams.get('client_id');
    let sessionId = urlParams.get('session_id');
    const sessionPassword = urlParams.get('session_password');
    const userPassword = urlParams.get('user_password');

    // クエリパラメータにない場合はwindow.CHAT_CONFIGから取得
    if (!clientId && window.CHAT_CONFIG) {
        clientId = window.CHAT_CONFIG.client_id;
    }
    
    if (!sessionId && window.CHAT_CONFIG) {
        sessionId = window.CHAT_CONFIG.session_id;
    }

    // それでもない場合はlocalStorageから取得
    if (!clientId) {
        clientId = localStorage.getItem('client_id');
    }
    
    if (!sessionId) {
        sessionId = localStorage.getItem('session_id');
    }

    if (!clientId) {
        alert('Client ID is required.');
        window.location.href = '/'; // ログインページに戻す
        return;
    }

    // クライアントIDとセッションIDをlocalStorageに保存（念のため）
    localStorage.setItem('client_id', clientId);
    if (sessionId) {
        localStorage.setItem('session_id', sessionId);
    }
    // パスワードも保存
    if (sessionPassword && sessionId) {
        localStorage.setItem('session_password_' + sessionId, sessionPassword);
    }
    if (userPassword && sessionId && clientId) {
        localStorage.setItem('user_password_' + sessionId + '_' + clientId, userPassword);
    }

    // グローバル変数に保存
    currentSessionId = sessionId;

    // WebSocket接続にsession_idを含める
    const wsUrl = sessionId 
        ? `ws://${window.location.host}/ws?session_id=${sessionId}`
        : `ws://${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = async function() {
        document.getElementById('status-text').textContent = 'Online';
        document.getElementById('status-icon').className = 'online';
        document.getElementById('client-id').textContent = `Client ID: ${clientId}`;
        
        // 過去のメッセージを読み込む
        await loadPastMessages();
        
        // 参加メッセージを送信
        sendSystemMessage('join');
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // セッション終了メッセージの処理
        if (data.type === 'session_end') {
            displayMessage(data);
            // 3秒後にログイン画面へリダイレクト
            setTimeout(() => {
                alert('Session has been ended. Please login again.');
                // localStorageのクリーンアップ
                const sessionId = localStorage.getItem('session_id');
                const clientId = localStorage.getItem('client_id');
                localStorage.removeItem('client_id');
                localStorage.removeItem('session_id');
                if (sessionId) {
                    localStorage.removeItem('session_password_' + sessionId);
                }
                if (sessionId && clientId) {
                    localStorage.removeItem('user_password_' + sessionId + '_' + clientId);
                }
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
            console.log('WebSocket closed:', event);
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
    if (data.type === 'system' || data.type === 'session_end') {
        messageDiv.className = `message system`;
        if (data.type === 'session_end') {
            messageDiv.style.backgroundColor = '#fff3cd';
            messageDiv.style.color = '#856404';
            messageDiv.style.fontWeight = 'bold';
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
        if (isBot) {
            iconDiv.className = 'message-icon bot-icon';
            iconDiv.style.backgroundColor = COLOR_PRESETS['bot'];
        } else {
            iconDiv.style.backgroundColor = data.client_id === clientId ? getColorFromClientId(clientId) : getColorFromClientId(data.client_id);
        }
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
        if (isBot) {
            clientIdSpan.textContent = 'AI Assistant';
            clientIdSpan.style.color = COLOR_PRESETS['bot'];
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
            console.log('[loadPastMessages] No session ID available');
            return;
        }
        
        console.log(`[loadPastMessages] Loading messages for session: ${currentSessionId}, clientId: ${clientId}`);
        
        // セッションのメッセージを取得
        const messagesResponse = await fetch(`/api/sessions/${currentSessionId}/messages`);
        if (!messagesResponse.ok) {
            console.log('[loadPastMessages] Failed to fetch messages, status:', messagesResponse.status);
            return;
        }
        
        const data = await messagesResponse.json();
        const messages = data.messages;
        
        console.log(`[loadPastMessages] Total messages in session: ${messages.length}`);
        
        // 自分が最初に参加した時刻を探す
        let myJoinTime = null;
        for (const msg of messages) {
            if (msg.message_type === 'system' && 
                msg.client_id === clientId && 
                msg.content.includes('joined')) {
                myJoinTime = new Date(msg.timestamp);
                console.log(`[loadPastMessages] Found join message at: ${myJoinTime.toISOString()}`);
                break;
            }
        }
        
        // 自分が参加した記録がない場合は、履歴を表示しない（初回参加）
        if (!myJoinTime) {
            console.log('[loadPastMessages] First time joining this session - no past messages to load');
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
        
        console.log(`[loadPastMessages] Loaded ${loadedCount} past messages (since you joined)`);
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
    console.log(`Unique colors: ${colors.size} / ${numUsers}`);
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
        // localStorageから全てのデータを削除
        const sessionId = localStorage.getItem('session_id');
        const savedClientId = localStorage.getItem('client_id');
        
        localStorage.removeItem('client_id');
        localStorage.removeItem('session_id');
        
        // セッションパスワード削除
        if (sessionId) {
            localStorage.removeItem('session_password_' + sessionId);
        }
        
        // ユーザーパスワード削除
        if (sessionId && savedClientId) {
            localStorage.removeItem('user_password_' + sessionId + '_' + savedClientId);
        }
        
        // ログインページへリダイレクト
        window.location.href = '/';
    }
} 