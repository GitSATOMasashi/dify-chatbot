const BASE_URL = 'http://localhost:8000';  // APIのベースURL

// グローバル変数としてapiKeyを定義
let apiKey;

let currentConversationId = null;  // 現在の会話IDを保持

// ドロップダウンの状態管理
let openDropdown = null;

async function sendToDify(message) {
    try {
        console.log('Sending message to Dify:', { message, currentConversationId });
        
        const requestBody = {
            message: message,
            user: 'test_user'
        };

        if (currentConversationId) {
            requestBody.conversation_id = currentConversationId;
        }

        const response = await fetch(`${BASE_URL}/proxy/dify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to send message to Dify');
        }

        // 会話IDを保存
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
        }

        return data;  // addMessageは呼び出さない
        
    } catch (error) {
        console.error('Error in sendToDify:', error);
        throw error;
    }
}

// 設定を取得する関数
async function getConfig() {
    try {
        const response = await fetch(`${BASE_URL}/config`);
        if (!response.ok) {
            throw new Error('Failed to get config');
        }
        const data = await response.json();
        return data.api_key;
    } catch (error) {
        console.error('Error getting config:', error);
        throw error;
    }
}

// ページ読み込み時の初期化
window.onload = async function() {
    try {
        await loadConversations();
        apiKey = await getConfig();  // apiKeyを設定
        await updateTokenCount();
    } catch (error) {
        console.error('Initialization error:', error);
    }
};

// メッセージ送信処理
async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (message) {
        try {
            // 1. 入力欄をクリアし、即座にユーザーメッセージを表示
            input.value = '';
            addMessage(message, 'user');

            // 2. Difyへの送信とボットの応答取得
            const response = await sendToDify(message);
            
            if (!response || !response.conversation_id) {
                throw new Error('Failed to get conversation ID from Dify');
            }

            // 3. 新しい会話を保存（既存の会話の場合はスキップ）
            if (!currentConversationId) {
                const convResponse = await fetch(`${BASE_URL}/conversations`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: 'test_user',
                        title: message.substring(0, 30) + (message.length > 30 ? '...' : ''),
                        id: response.conversation_id
                    })
                });

                if (!convResponse.ok) {
                    throw new Error('Failed to save conversation');
                }
            }

            // 4. メッセージを保存
            await saveMessage(message, 'user', response.conversation_id);
            
            if (response.answer) {
                // 5. ボットの応答を保存
                await saveMessage(response.answer, 'bot', response.conversation_id);
                
                // 6. UIにボットの応答を表示
                addMessage(response.answer, 'bot');
            }
            
            // 7. 会話リストを更新
            await loadConversations();
            
        } catch (error) {
            console.error('Error sending message:', error);
            addMessage('メッセージの送信に失敗しました', 'system');
        }
    }
}

async function loadChatHistory(conversationId) {
    try {
        console.log('Loading messages for conversation:', conversationId);
        const response = await fetch(`${BASE_URL}/messages?conversation_id=${conversationId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load messages: ${response.status}`);
        }
        
        const messages = await response.json();
        
        // チャット画面をクリア
        const messagesDiv = document.getElementById('chat-messages');
        messagesDiv.innerHTML = '';
        
        // メッセージを表示（サーバー側でソート済み）
        if (Array.isArray(messages)) {
            messages.forEach(message => {
                addMessage(message.content, message.role);
            });
            console.log('Messages loaded:', messages);
        } else {
            console.error('Invalid messages format:', messages);
        }
        
        return messages;
    } catch (error) {
        console.error('Error loading messages:', error);
        return [];
    }
}

// トークンリセット処理
async function resetTokens() {
    try {
        const response = await fetch(`${BASE_URL}/tokens/reset/test_user`, {
            method: 'POST'
        });
        const data = await response.json();
        document.getElementById('token-count').textContent = data.remaining_tokens;
        
        // 入力欄と送信ボタンを有効化
        const input = document.getElementById('message-input');
        const sendButton = document.querySelector('.input-container button');
        input.disabled = false;
        sendButton.disabled = false;
    } catch (error) {
        console.error('Error resetting tokens:', error);
        addMessage('トークンのリセットに失敗しました。', 'system');
    }
}

// メッセージ履歴を読み込む関数
async function loadMessages(conversationId) {
    try {
        console.log('\n=== Loading Messages ===');
        console.log('Conversation ID:', conversationId);
        
        currentConversationId = conversationId;
        console.log('Loading messages for conversation:', conversationId);
        
        const response = await fetch(`${BASE_URL}/messages/${conversationId}`);
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error loading messages:', errorData);
            throw new Error(errorData.detail || 'Failed to load messages');
        }
        
        const messages = await response.json();
        console.log('Messages loaded:', messages);
        
        // チャット画面をクリア
        const messagesDiv = document.getElementById('chat-messages');
        messagesDiv.innerHTML = '';
        
        // メッセージを表示
        messages.forEach(msg => {
            addMessage(msg.content, msg.role);
        });
        
        // 会話リストの選択状態を更新
        const items = document.querySelectorAll('.conversation-item');
        items.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.id === conversationId) {
                item.classList.add('active');
            }
        });
        
    } catch (error) {
        console.error('Error in loadMessages:', error);
        console.error('Error stack:', error.stack);
        throw error;
    }
}

// ドロップダウンを切り替える関数
function toggleDropdown(dropdown) {
    // 他のドロップダウンを閉じる
    closeAllDropdowns();
    
    const content = dropdown.querySelector('.dropdown-content');
    if (content) {
        content.style.display = content.style.display === 'block' ? 'none' : 'block';
        if (content.style.display === 'block') {
            openDropdown = dropdown;
        } else {
            openDropdown = null;
        }
    }
}

// 全てのドロップダウンを閉じる関数
function closeAllDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown-content');
    dropdowns.forEach(dropdown => {
        dropdown.style.display = 'none';
    });
    openDropdown = null;
}

// ドロップダウン以外をクリックした時に閉じる
document.addEventListener('click', function(event) {
    if (openDropdown && !openDropdown.contains(event.target)) {
        closeAllDropdowns();
    }
});

// 会話リストを読み込む関数の修正
async function loadConversations() {
    try {
        const response = await fetch(`${BASE_URL}/conversations/test_user`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const conversations = await response.json();
        
        const list = document.getElementById('conversation-list');
        list.innerHTML = '';
        
        conversations.forEach(conv => {
            const li = document.createElement('li');
            li.className = 'conversation-item';
            li.dataset.id = conv.id;  // 会話IDをデータ属性として保存
            if (conv.id === currentConversationId) {
                li.classList.add('active');
            }
            
            const titleDiv = document.createElement('div');
            titleDiv.className = 'conversation-title';
            titleDiv.textContent = conv.title;
            
            const lastMessageDiv = document.createElement('div');
            lastMessageDiv.className = 'conversation-preview';
            lastMessageDiv.textContent = conv.last_message || '新しい会話';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'conversation-content';
            contentDiv.appendChild(titleDiv);
            contentDiv.appendChild(lastMessageDiv);
            
            contentDiv.onclick = () => loadMessages(conv.id);
            
            const dropdown = document.createElement('div');
            dropdown.className = 'dropdown';
            
            const dropdownBtn = document.createElement('button');
            dropdownBtn.className = 'dropdown-btn';
            dropdownBtn.innerHTML = '&#8230;'; // 三点リーダー
            dropdownBtn.onclick = (e) => {
                e.stopPropagation();
                toggleDropdown(dropdown);
            };
            
            const dropdownContent = document.createElement('div');
            dropdownContent.className = 'dropdown-content';
            
            const editBtn = document.createElement('button');
            editBtn.textContent = '編集';
            editBtn.className = 'edit';
            editBtn.onclick = (e) => {
                e.stopPropagation();
                openEditModal(conv.id, conv.title);
                closeAllDropdowns();
            };
            
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = '削除';
            deleteBtn.className = 'delete';
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                deleteConversation(conv.id);
                closeAllDropdowns();
            };
            
            dropdownContent.appendChild(editBtn);
            dropdownContent.appendChild(deleteBtn);
            dropdown.appendChild(dropdownBtn);
            dropdown.appendChild(dropdownContent);
            
            li.appendChild(contentDiv);
            li.appendChild(dropdown);
            list.appendChild(li);
        });
    } catch (error) {
        console.error('Error loading conversations:', error);
    }

    // 会話リストの表示後にオプションをセットアップ
    setupConversationOptions();
}

// トークン数を更新
async function updateTokenCount() {
    try {
        const response = await fetch(`${BASE_URL}/tokens/test_user`);
        if (!response.ok) {
            throw new Error('Failed to get token count');
        }
        const data = await response.json();
        document.getElementById('token-count').textContent = data.remaining_tokens;
    } catch (error) {
        console.error('Error updating token count:', error);
    }
}

// メッセージを画面に追加する関数
function addMessage(content, role) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    // メッージの内容を設定
    const contentP = document.createElement('p');
    contentP.textContent = content;
    messageDiv.appendChild(contentP);
    
    // メッセージを追加
    messagesDiv.appendChild(messageDiv);
    
    // 最新のメッセージが見えるように自動スクロール
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// トークンを消費する関数
async function consumeTokens(message) {
    try {
        const response = await fetch(`${BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: 'test_user'
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'トークンの消費に失敗しました');
        }

        const data = await response.json();
        document.getElementById('token-count').textContent = data.remaining_tokens;
        return data;
    } catch (error) {
        console.error('Error consuming tokens:', error);
        throw error;
    }
}

// メッセージを保存す関数
async function saveMessage(content, role, conversationId) {
    try {
        console.log('=== Saving Message ===');
        console.log('Content:', content);
        console.log('Role:', role);
        console.log('Conversation ID:', conversationId);

        if (!conversationId) {
            console.error('No conversation ID provided');
            return;
        }

        const messageData = {
            content: content,
            role: role,
            user_id: 'test_user',
            conversation_id: conversationId
        };

        console.log('Sending message data:', messageData);

        const response = await fetch(`${BASE_URL}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(messageData)
        });

        const responseData = await response.json();
        
        if (!response.ok) {
            console.error('Error response:', responseData);
            throw new Error(responseData.detail || 'Failed to save message');
        }

        console.log('Message saved successfully:', responseData);
        return responseData;
    } catch (error) {
        console.error('Error saving message:', error);
        throw error;
    }
}

// 会話を削除する関数
async function deleteConversation(conversationId) {
    try {
        // 確認ダイアログを表示
        if (!confirm('の会話を削除してよろしいですか？')) {
            return;
        }

        console.log('Deleting conversation:', conversationId);
        
        const response = await fetch(`${BASE_URL}/conversations/${conversationId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 会話リストを再読み込み
        await loadConversations();
        
        // 削除した会話が現在表示中の会話だった場合、チャット画面をクリア
        if (currentConversationId === conversationId) {
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML = '';
            currentConversationId = null;
        }

    } catch (error) {
        console.error('Error deleting conversation:', error);
        alert('会話の削除に失敗ました');
    }
}

// 新しいチャットを開始する関数
async function startNewChat() {
    try {
        // チャット画面をクリア
        const messagesDiv = document.getElementById('chat-messages');
        messagesDiv.innerHTML = '';
        
        // 現在の会話IDをリセット
        currentConversationId = null;
        
        // 入力欄を有効化
        const input = document.getElementById('message-input');
        const sendButton = document.querySelector('.input-container button');
        input.disabled = false;
        sendButton.disabled = false;
        
        // 会話リストの選択状態をクリア
        const items = document.querySelectorAll('.conversation-item');
        items.forEach(item => {
            item.classList.remove('active');
        });
        
        console.log('Started new chat');
        
    } catch (error) {
        console.error('Error starting new chat:', error);
        addMessage('新しいトークの作成に失敗しました', 'system');
    }
}

function setupConversationOptions() {
    document.querySelectorAll('.more-options-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const menu = btn.nextElementSibling;
            menu.classList.toggle('hidden');
        });
    });

    // タイトル編集のイベントリスナー
    document.querySelectorAll('.edit-title').forEach(item => {
        item.addEventListener('click', async (e) => {
            e.stopPropagation();
            const convItem = e.target.closest('.conversation-item');
            const convId = convItem.dataset.id;
            const currentTitle = convItem.querySelector('.conversation-title').textContent;
            
            const newTitle = prompt('新しいタイトルを入力してください:', currentTitle);
            if (newTitle && newTitle !== currentTitle) {
                try {
                    const response = await fetch(`${BASE_URL}/conversations/${convId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ title: newTitle })
                    });

                    if (response.ok) {
                        convItem.querySelector('.conversation-title').textContent = newTitle;
                    } else {
                        alert('タイトルの更新に失敗しました');
                    }
                } catch (error) {
                    console.error('Error updating title:', error);
                    alert('タイトルの更新に失敗しました');
                }
            }
        });
    });

    // 削除のイベントリスナー
    document.querySelectorAll('.delete-conv').forEach(item => {
        item.addEventListener('click', async (e) => {
            e.stopPropagation();
            const convItem = e.target.closest('.conversation-item');
            const convId = convItem.dataset.id;
            
            if (confirm('この会話を削除してもよろしいですか？')) {
                try {
                    const response = await fetch(`${BASE_URL}/conversations/${convId}`, {
                        method: 'DELETE'
                    });

                    if (response.ok) {
                        convItem.remove();
                    } else {
                        alert('会話の削除に失敗しました');
                    }
                } catch (error) {
                    console.error('Error deleting conversation:', error);
                    alert('会話の削除に失敗しました');
                }
            }
        });
    });
}