#!/bin/bash

# AI設定テストスクリプト
# 実験のAI設定が正しく読み込まれているかを確認する

EXPERIMENT_SLUG="ai"
EXPERIMENT_FILE="data/experiments/${EXPERIMENT_SLUG}/experiment.json"

echo "=========================================="
echo "AI設定テスト"
echo "=========================================="
echo ""

# 実験設定を確認
echo "【1】実験設定の確認"

if [ ! -f "$EXPERIMENT_FILE" ]; then
    echo "  ✗ 実験ファイルが見つかりません: $EXPERIMENT_FILE"
    exit 1
fi

echo "  ✓ 実験ファイル: $EXPERIMENT_FILE"
echo ""

# チャット設定を抽出
python3 - "$EXPERIMENT_FILE" <<'EOF'
import json
import sys

with open(sys.argv[1], 'r') as f:
    data = json.load(f)

configs = []
for step in data.get('experiment_flow', []):
    if step.get('step_type') == 'branch':
        for branch in step.get('branches', []):
            for sub_step in branch.get('steps', []):
                if sub_step.get('step_type') == 'chat':
                    config = {
                        'condition': branch.get('condition_label'),
                        'step_id': sub_step.get('step_id'),
                        'bot_model': sub_step.get('bot_model'),
                        'system_prompt': sub_step.get('system_prompt', '')[:50] + '...',
                        'temperature': sub_step.get('temperature'),
                        'top_p': sub_step.get('top_p'),
                        'top_k': sub_step.get('top_k'),
                        'repeat_penalty': sub_step.get('repeat_penalty'),
                        'num_thread': sub_step.get('num_thread'),
                        'num_ctx': sub_step.get('num_ctx'),
                        'num_gpu': sub_step.get('num_gpu'),
                        'num_batch': sub_step.get('num_batch'),
                    }
                    configs.append(config)

print("AI設定:")
print()
for i, cfg in enumerate(configs, 1):
    print(f"  【条件 {i}: {cfg['condition']}】")
    print(f"    step_id        : {cfg['step_id']}")
    print(f"    bot_model      : {cfg['bot_model']}")
    print(f"    system_prompt  : {cfg['system_prompt']}")
    print(f"    temperature    : {cfg['temperature']}")
    print(f"    top_p          : {cfg['top_p']}")
    print(f"    top_k          : {cfg['top_k']}")
    print(f"    repeat_penalty : {cfg['repeat_penalty']}")
    print(f"    num_thread     : {cfg['num_thread']}")
    print(f"    num_ctx        : {cfg['num_ctx']}")
    print(f"    num_gpu        : {cfg['num_gpu']}")
    print(f"    num_batch      : {cfg['num_batch']}")
    print()
EOF

echo ""
echo "【2】実際の動作確認方法"
echo ""
echo "  実験を開始して、AIとチャットすると、サーバーログに"
echo "  以下のような詳細情報が表示されます:"
echo ""
echo "  =================================="
echo "  🤖 OLLAMA MODEL INVOCATION"
echo "  =================================="
echo "  Session ID    : sess_..."
echo "  Model         : qwen3:14b"
echo "  System Prompt : You are an empathetic counselor..."
echo ""
echo "  Parameters:"
echo "    temperature      : 0.6"
echo "    top_p            : 0.95"
echo "    top_k            : 20"
echo "    repeat_penalty   : 1.0"
echo "    num_predict      : Default (unlimited)"
echo "    num_thread       : Default (8)"
echo "    num_ctx          : Default (8192)"
echo "    num_gpu          : Default (-1, all)"
echo "    num_batch        : Default (512)"
echo "  =================================="
echo ""
echo "  ✓ この出力が実験設定と一致していれば、正しく動作しています"
echo ""
echo ""
echo "【3】テスト手順"
echo ""
echo "  1. ブラウザで http://localhost:8000/ を開く"
echo "  2. 参加者コードでログイン"
echo "  3. チャットステップまで進む"
echo "  4. メッセージを送信"
echo "  5. サーバーのコンソール出力を確認"
echo ""
echo "=========================================="

