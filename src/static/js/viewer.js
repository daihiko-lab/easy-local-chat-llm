let ws = null;
let sessionId = null;

// 黄金比を使用してより均一な分布を得る
const GOLDEN_RATIO = 0.618033988749895;

// シード値から擬似乱数を生成するジェネレータ
function createRandomGenerator(seed) {
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
        const char = seed.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    
    return function() {
        hash = (hash * 1103515245 + 12345) & 0x7fffffff;
        return hash / 0x7fffffff;
    };
}

// クライアントIDから色相を計算
function getColorFromClientId(clientId) {
    const rng = createRandomGenerator(clientId);
    const hue = (rng() * 360);
    const saturation = 65 + (rng() * 20);
    const lightness = 45 + (rng() * 15);
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

const COLOR_PRESETS = {
    'Alice': '#E74C3C',
    'Bob': '#3498DB',
    'Charlie': '#2ECC71',
    'David': '#F39C12',
    'Eve': '#9B59B6'
};

function getClientColor(clientId) {
    return COLOR_PRESETS[clientId] || getColorFromClientId(clientId);
}

async function connect() {
    // URLパラメータからsession_idを取得
    const urlParams = new URLSearchParams(window.location.search);
    sessionId = urlParams.get('session_id');

    if (!sessionId) {
        alert('Session ID is required.');
        window.close();
        return;
    }

    // セッション情報を表示
    document.getElementById('session-id').textContent = sessionId;

    // WebSocket接続
    const wsUrl = `ws://${window.location.host}/ws/viewer?session_id=${sessionId}`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = async function() {
        document.getElementById('status-text').textContent = 'Online';
        document.getElementById('status-icon').className = 'online';
        
        // 過去のメッセージを読み込む
        await loadPastMessages();
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // セッション終了メッセージの処理
        if (data.type === 'session_end') {
            displayMessage(data);
            setTimeout(() => {
                alert('Session has been ended.');
                window.close();
            }, 3000);
        } else {
            displayMessage(data);
        }
    };

    ws.onclose = function(event) {
        document.getElementById('status-text').textContent = 'Offline';
        document.getElementById('status-icon').className = 'offline';
    };

    ws.onerror = function(error) {
        console.error('[Viewer] WebSocket error:', error);
    };
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
        messageDiv.textContent = data.message;
    } else {
        // ユーザーメッセージの場合（通常のチャットと同じ構造）
        messageDiv.className = `message other`;

        // メッセージコンテナを作成
        const messageContainer = document.createElement('div');
        messageContainer.className = 'message-container';

        // アイコンを表示
        const iconDiv = document.createElement('div');
        iconDiv.className = 'message-icon';
        iconDiv.style.backgroundColor = getClientColor(data.client_id);
        const img = document.createElement('img');
        img.src = `/static/images/default_icon.png`;
        iconDiv.appendChild(img);
        messageContainer.appendChild(iconDiv);

        // メッセージテキストを表示
        const messageTextDiv = document.createElement('div');
        messageTextDiv.className = 'message-text';
        
        // クライアントIDを表示
        const clientIdSpan = document.createElement('span');
        clientIdSpan.className = 'client-id';
        clientIdSpan.textContent = `Client ID: ${data.client_id}`;
        messageTextDiv.appendChild(clientIdSpan);
        messageTextDiv.appendChild(document.createElement('br'));
        messageTextDiv.appendChild(document.createTextNode(data.message));

        messageContainer.appendChild(messageTextDiv);
        messageDiv.appendChild(messageContainer);
    }

    // タイムスタンプを追加
    if (data.timestamp) {
        const timestampSpan = document.createElement('span');
        timestampSpan.className = 'message-timestamp';
        const date = new Date(data.timestamp);
        timestampSpan.textContent = date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        messageDiv.appendChild(timestampSpan);
    }

    messageArea.appendChild(messageDiv);
    
    // 自動スクロール
    messageArea.scrollTop = messageArea.scrollHeight;
}

// 過去のメッセージを読み込む関数
async function loadPastMessages() {
    try {
        const messagesResponse = await fetch(`/api/sessions/${sessionId}/messages`);
        if (!messagesResponse.ok) {
            return;
        }
        
        const data = await messagesResponse.json();
        const messages = data.messages;
        
        // すべてのメッセージを表示（管理者なので全て見える）
        messages.forEach(msg => {
            displayMessage({
                type: msg.message_type,
                client_id: msg.client_id,
                message: msg.content,
                timestamp: msg.timestamp
            });
        });
    } catch (error) {
        console.error('[Viewer] Error loading past messages:', error);
    }
}

// 初期接続
connect();

