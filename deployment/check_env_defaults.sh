#!/bin/bash

# 環境デフォルト値チェックスクリプト

MODEL="${1:-qwen3:14b}"

echo "=== システム情報 ==="
system_profiler SPHardwareDataType | grep -E "Chip|Memory" | sed 's/^/  /'
echo "  CPU: $(sysctl -n hw.physicalcpu 2>/dev/null)コア"

# メモリ使用状況
MEM_USED=$(vm_stat 2>/dev/null | perl -ne '
  /page size of (\d+)/ and $size=$1;
  /Pages (wired down):\s+(\d+)/ and $wired=$2;
  /Pages (active):\s+(\d+)/ and $active=$2;
  /occupied by compressor:\s+(\d+)/ and $comp=$2;
  END { 
    $used = ($wired + $active + $comp) * $size / 1073741824;
    printf("%.1f GB", $used);
  }
')
echo "  使用中: ${MEM_USED}"

echo ""
echo "=== Ollama ==="
echo "  Version: $(curl -s http://localhost:11434/api/version 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4)"
echo "  Models:"
ollama list 2>/dev/null | tail -n +2 | awk '{print "    " $1}'

echo ""
echo "=== Ollamaデフォルト ==="
echo "  num_ctx: 2048, num_thread: CPU依存, num_gpu: -1, num_batch: 512"

echo ""
echo "=== ${MODEL} ==="
ollama show "${MODEL}" --modelfile 2>/dev/null | grep "^PARAMETER" | awk '{printf "  %s: %s\n", $2, $3}'

echo ""
echo "使い方: $0 [model]"

