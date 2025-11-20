# 多段階実験フローシステム - 使用ガイド

## 概要

このシステムは、汎用的な多段階実験フロー機能を提供します。任意の実験デザインに対応できるよう柔軟に設計されています。

**🔄 重要: 実験レベルと条件レベルのフロー**

フローは **2つのレベル** で定義できます：

1. **実験レベル (Experiment-level)** - 推奨 ✅
   - **全条件で共通のフロー** を定義
   - 管理画面の実験詳細で「🔄 Edit Experiment Flow」から編集
   - 例：同じPANAS測定を全条件で実施

2. **条件レベル (Condition-level)** - 特殊な場合のみ
   - **特定の条件だけ異なるフロー** を定義
   - 各条件カードの「⚙️ 条件固有フロー」から編集
   - 例：条件Aだけ追加のアンケートがある

**優先順位**: Condition → Experiment → 旧形式

**🔄 旧形式の自動変換**

`experiment_flow` を明示的に設定しない場合でも、旧形式のフィールド (`instruction_text`, `time_limit_minutes`, `survey_questions`) は自動的にフローシステムに変換されます。

## 実験フローの構成

### ステップタイプ

以下の5種類のステップタイプを組み合わせて、実験フローを構成できます：

1. **consent** - 同意書
2. **instruction** - 教示文
3. **survey** - 質問紙 (事前・事後どちらでも)
4. **chat** - チャットセッション
5. **debriefing** - デブリーフィング

### 質問タイプ

アンケート (survey) では以下の質問タイプが使用できます：

- **likert** - リッカート尺度 (例: 1-7段階評価)
- **single_choice** - 単一選択
- **multiple_choice** - 複数選択
- **text** - 自由記述

## 実装例

### 例1: 基本的な実験フロー

```json
{
  "condition_id": "empathic_condition",
  "name": "共感的条件",
  "bot_model": "gemma3:4b",
  "system_prompt": "あなたは共感的なカウンセラーです...",
  "is_experiment": true,
  "experiment_group": "共感条件",
  "experiment_flow": [
    {
      "step_id": "consent",
      "step_type": "consent",
      "title": "研究参加への同意",
      "content": "この研究は...\n\n上記に同意いただける場合は、下のボタンを押してください。",
      "button_text": "同意する",
      "required": true
    },
    {
      "step_id": "instruction",
      "step_type": "instruction",
      "title": "実験の説明",
      "content": "これから10分間、AIとチャットをしていただきます。\n悩みについて自由にお話しください。",
      "button_text": "開始する",
      "required": true
    },
    {
      "step_id": "chat_session",
      "step_type": "chat",
      "time_limit_minutes": 10,
      "required": true
    },
    {
      "step_id": "post_survey",
      "step_type": "survey",
      "title": "アンケート",
      "survey_description": "チャット体験についてお答えください。",
      "button_text": "送信",
      "survey_questions": [
        {
          "question_id": "satisfaction",
          "question_text": "チャット体験に満足しましたか？",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 7,
          "scale_min_label": "全く満足していない",
          "scale_max_label": "非常に満足している",
          "required": true
        }
      ],
      "required": true
    },
    {
      "step_id": "debriefing",
      "step_type": "debriefing",
      "title": "実験へのご協力ありがとうございました",
      "content": "本研究の目的は...\n\nご協力ありがとうございました。",
      "button_text": "終了",
      "required": true
    }
  ]
}
```

### 例2: PANAS尺度を含む実験 (あなたの実験例)

```json
{
  "condition_id": "empathic_panas",
  "name": "共感的条件 (PANAS測定)",
  "bot_model": "gemma3:4b",
  "system_prompt": "あなたは共感的で支持的なAIカウンセラーです。ユーザーの感情に寄り添い、理解を示してください。",
  "is_experiment": true,
  "experiment_group": "共感条件",
  "weight": 1,
  "experiment_flow": [
    {
      "step_id": "consent",
      "step_type": "consent",
      "title": "研究参加への同意",
      "content": "本研究は、生成AIを用いた相談体験に関する研究です。\n\n【研究の概要】\n- 所要時間: 約20分\n- 内容: 質問紙回答、AIとの対話、質問紙回答\n- データは匿名化され、研究目的のみに使用されます\n\n参加は任意であり、途中で中断することも可能です。\n同意いただける場合は、下のボタンを押してください。",
      "button_text": "同意する",
      "required": true
    },
    {
      "step_id": "concern_type",
      "step_type": "survey",
      "title": "事前質問",
      "survey_description": "本実験で相談する悩みの種類を選択してください。",
      "button_text": "次へ",
      "survey_questions": [
        {
          "question_id": "concern_category",
          "question_text": "今回相談したい悩みの種類を選択してください",
          "question_type": "single_choice",
          "choices": ["人間関係", "学業成績"],
          "required": true
        }
      ],
      "required": true
    },
    {
      "step_id": "recall_instruction",
      "step_type": "instruction",
      "title": "悩みの想起",
      "content": "これから、先ほど選択した種類の悩みについて思い出してください。\n\nできるだけ具体的に、その悩みの状況や感情を思い浮かべてください。\n\n準備ができたら、次へ進んでください。",
      "button_text": "次へ",
      "required": true
    },
    {
      "step_id": "pre_panas",
      "step_type": "survey",
      "title": "現在の気分について",
      "survey_description": "現在のあなたの気分についてお答えください。",
      "button_text": "次へ",
      "survey_questions": [
        {
          "question_id": "panas_pre_1",
          "question_text": "活気のある",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 5,
          "scale_min_label": "全く当てはまらない",
          "scale_max_label": "非常に当てはまる",
          "required": true
        },
        {
          "question_id": "panas_pre_2",
          "question_text": "苦悩した",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 5,
          "scale_min_label": "全く当てはまらない",
          "scale_max_label": "非常に当てはまる",
          "required": true
        },
        {
          "question_id": "panas_pre_3",
          "question_text": "興味のある",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 5,
          "scale_min_label": "全く当てはまらない",
          "scale_max_label": "非常に当てはまる",
          "required": true
        }
      ],
      "required": true
    },
    {
      "step_id": "chat_instruction",
      "step_type": "instruction",
      "title": "AIとの対話",
      "content": "これから10分間、AIに悩みを相談してください。\n\n思い出した悩みについて、自由にお話しください。\nAIはあなたの相談に応答します。\n\n10分経過すると自動的に次の画面に進みます。",
      "button_text": "チャット開始",
      "required": true
    },
    {
      "step_id": "chat_session",
      "step_type": "chat",
      "time_limit_minutes": 10,
      "required": true
    },
    {
      "step_id": "post_panas",
      "step_type": "survey",
      "title": "現在の気分について",
      "survey_description": "チャット後の現在のあなたの気分についてお答えください。",
      "button_text": "次へ",
      "survey_questions": [
        {
          "question_id": "panas_post_1",
          "question_text": "活気のある",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 5,
          "scale_min_label": "全く当てはまらない",
          "scale_max_label": "非常に当てはまる",
          "required": true
        },
        {
          "question_id": "panas_post_2",
          "question_text": "苦悩した",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 5,
          "scale_min_label": "全く当てはまらない",
          "scale_max_label": "非常に当てはまる",
          "required": true
        },
        {
          "question_id": "panas_post_3",
          "question_text": "興味のある",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 5,
          "scale_min_label": "全く当てはまらない",
          "scale_max_label": "非常に当てはまる",
          "required": true
        }
      ],
      "required": true
    },
    {
      "step_id": "manipulation_check_empathy",
      "step_type": "survey",
      "title": "チャット体験について",
      "survey_description": "AIとの対話体験についてお答えください。",
      "button_text": "次へ",
      "survey_questions": [
        {
          "question_id": "empathy_1",
          "question_text": "AIは私の気持ちをよく理解してくれた",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 7,
          "scale_min_label": "全くそう思わない",
          "scale_max_label": "非常にそう思う",
          "required": true
        },
        {
          "question_id": "empathy_2",
          "question_text": "AIは私の話に共感してくれたと感じた",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 7,
          "scale_min_label": "全くそう思わない",
          "scale_max_label": "非常にそう思う",
          "required": true
        },
        {
          "question_id": "empathy_3",
          "question_text": "AIの返答は、私の感情に寄り添っていた",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 7,
          "scale_min_label": "全くそう思わない",
          "scale_max_label": "非常にそう思う",
          "required": true
        },
        {
          "question_id": "solution_1",
          "question_text": "AIは私の問題に対して具体的な助言をくれた",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 7,
          "scale_min_label": "全くそう思わない",
          "scale_max_label": "非常にそう思う",
          "required": true
        },
        {
          "question_id": "solution_2",
          "question_text": "AIの返答は、実行可能な解決策を含んでいた",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 7,
          "scale_min_label": "全くそう思わない",
          "scale_max_label": "非常にそう思う",
          "required": true
        },
        {
          "question_id": "solution_3",
          "question_text": "AIの返答は、問題解決に役立つと感じた",
          "question_type": "likert",
          "scale_min": 1,
          "scale_max": 7,
          "scale_min_label": "全くそう思わない",
          "scale_max_label": "非常にそう思う",
          "required": true
        }
      ],
      "required": true
    },
    {
      "step_id": "environment_check",
      "step_type": "survey",
      "title": "実験環境について",
      "survey_description": "",
      "button_text": "次へ",
      "survey_questions": [
        {
          "question_id": "naturalness",
          "question_text": "実験環境に不自然な点はありましたか？",
          "question_type": "single_choice",
          "choices": ["なかった", "少しあった", "かなりあった"],
          "required": true
        },
        {
          "question_id": "comments",
          "question_text": "実験全体を通しての感想を自由にお書きください",
          "question_type": "text",
          "max_length": 500,
          "required": false
        }
      ],
      "required": true
    },
    {
      "step_id": "demographics",
      "step_type": "survey",
      "title": "基本情報",
      "survey_description": "最後に、あなたの基本情報についてお答えください。",
      "button_text": "送信",
      "survey_questions": [
        {
          "question_id": "age",
          "question_text": "年齢",
          "question_type": "text",
          "required": true
        },
        {
          "question_id": "gender",
          "question_text": "性別",
          "question_type": "single_choice",
          "choices": ["男性", "女性", "その他", "回答しない"],
          "required": true
        },
        {
          "question_id": "grade",
          "question_text": "学年",
          "question_type": "single_choice",
          "choices": ["学部1年", "学部2年", "学部3年", "学部4年", "修士1年", "修士2年", "博士1年", "博士2年", "博士3年以上"],
          "required": true
        },
        {
          "question_id": "ai_experience",
          "question_text": "生成AIに相談をしたことがありますか？",
          "question_type": "single_choice",
          "choices": ["ある", "ない"],
          "required": true
        }
      ],
      "required": true
    },
    {
      "step_id": "debriefing",
      "step_type": "debriefing",
      "title": "実験へのご協力ありがとうございました",
      "content": "【研究の目的】\n本研究は、生成AIによる共感的応答と解決指向的応答が、相談者の感情状態に与える影響を検討することを目的としています。\n\n【データの取り扱い】\n収集されたデータは匿名化され、研究目的のみに使用されます。個人が特定されることはありません。\n\n【お問い合わせ】\n本研究について質問がある場合は、[研究者連絡先]までご連絡ください。\n\nご協力ありがとうございました。",
      "button_text": "終了",
      "required": true
    }
  ]
}
```

## 条件の設定方法

### 方法1: 管理画面から設定 (推奨) ✅

#### 実験レベルのフロー（全条件共通）

1. 管理画面 (`/admin`) → 実験の「🔧 Manage」をクリック
2. 「🔄 Edit Experiment Flow (共通フロー)」ボタンをクリック
3. ステップを追加・編集・並び替え
4. 「💾 Save Flow」で保存

#### 条件レベルのフロー（特定条件のみ）

1. 実験詳細画面で条件カードの「⚙️ 条件固有フロー」をクリック
2. その条件だけのフローを定義
3. 「💾 Save Flow」で保存

### 方法2: JSONファイル直接編集

#### 実験レベル

`data/experiments/[実験ID]/experiment.json` を開き、`experiment_flow` を追加：

```json
{
  "experiment_id": "...",
  "name": "...",
  "experiment_flow": [
    {
      "step_id": "consent",
      "step_type": "consent",
      "title": "研究参加への同意",
      "content": "...",
      "button_text": "同意する",
      "required": true
    },
    ...
  ]
}
```

#### 条件レベル

`data/experiments/[実験ID]/conditions.json` を開き、特定の条件に `experiment_flow` を追加。

## データのエクスポート

各ステップの回答データは `Session` オブジェクトの `step_responses` フィールドに保存されます。

```python
# 構造
{
  "step_id": {
    "client_id": {
      "survey_responses": [...],  # アンケート回答
      "timestamp": "...",          # 回答時刻
      ...
    }
  }
}
```

管理画面から通常通りCSVまたはJSONでエクスポートできます。

## 旧形式との互換性

### 自動変換

`experiment_flow` を設定していない条件でも、以下のフィールドが自動的にフローに変換されます：

```json
{
  "instruction_text": "...",      // → instructionステップ
  "time_limit_minutes": 10,        // → chatステップ
  "survey_questions": [...],       // → surveyステップ
  "survey_title": "...",
  "survey_description": "..."
}
```

**変換例:**

旧形式:
```json
{
  "condition_id": "simple",
  "instruction_text": "10分間チャットしてください",
  "time_limit_minutes": 10,
  "survey_questions": [...]
}
```

↓ 自動的に以下のフローに変換される:

```json
{
  "experiment_flow": [
    {
      "step_id": "instruction",
      "step_type": "instruction",
      "content": "10分間チャットしてください",
      ...
    },
    {
      "step_id": "chat",
      "step_type": "chat",
      "time_limit_minutes": 10
    },
    {
      "step_id": "survey",
      "step_type": "survey",
      "survey_questions": [...]
    }
  ]
}
```

### メリット

- **統一されたシステム**: すべての実験が同じフローシステムで動作
- **後方互換性**: 既存の条件設定をそのまま使用可能
- **段階的移行**: 必要に応じて `experiment_flow` を明示的に設定可能

## トラブルシューティング

### フローが表示されない

- `experiment_flow` が正しく設定されているか確認
- サーバーを再起動したか確認
- ブラウザのキャッシュをクリア

### ステップ間で進めない

- 必須項目が入力されているか確認
- ブラウザのコンソールでエラーを確認

### データが保存されない

- セッションが正しく作成されているか確認
- サーバーログでエラーを確認

