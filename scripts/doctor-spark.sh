#!/usr/bin/env bash
set -u

failed=0

check_command() {
  if command -v "$1" >/dev/null 2>&1; then
    printf '[OK] %s: %s\n' "$1" "$(command -v "$1")"
  else
    printf '[缺失] %s\n' "$1"
    failed=1
  fi
}

check_url() {
  if curl --fail --silent --show-error --max-time 5 "$2" >/dev/null 2>&1; then
    printf '[OK] %s: %s\n' "$1" "$2"
  else
    printf '[未就绪] %s: %s\n' "$1" "$2"
    failed=1
  fi
}

printf '架构：%s\n' "$(uname -m)"
if [[ "$(uname -m)" != 'aarch64' ]]; then
  printf '[注意] 当前设备不是 DGX Spark 的 ARM64 环境\n'
fi
if command -v python3.11 >/dev/null 2>&1; then
  check_command python3.11
else
  check_command python3.12
fi
check_command nvidia-smi
check_command "${BLENDER_BIN:-blender}"
check_command curl

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,driver_version --format=csv,noheader || true
fi
if command -v "${BLENDER_BIN:-blender}" >/dev/null 2>&1; then
  "${BLENDER_BIN:-blender}" --version | head -n 1
fi
if command -v curl >/dev/null 2>&1; then
  check_url Ollama http://127.0.0.1:11434/api/tags
  check_url Hunyuan3D http://127.0.0.1:8081/health
fi
printf '可用磁盘：\n'
df -h . | tail -n 1

exit "$failed"
