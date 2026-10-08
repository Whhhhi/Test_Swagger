#!/usr/bin/env bash
# ============================================================
# Petstore API 自动化测试 — 运行脚本
# ============================================================
# 用法:
#   bash run_tests.sh              # 运行全部用例
#   bash run_tests.sh -m smoke     # 仅冒烟测试
#   bash run_tests.sh -m negative  # 仅反向测试
#   bash run_tests.sh --allure     # 运行并生成 Allure 报告
# ============================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# 颜色
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Petstore API 自动化测试${NC}"
echo -e "${CYAN}============================================${NC}"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[INFO] 未找到虚拟环境，创建中...${NC}"
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 创建日志目录
mkdir -p logs

# 解析参数
ALLURE_FLAG=0
PYTEST_ARGS=""

for arg in "$@"; do
    case "$arg" in
        --allure)
            ALLURE_FLAG=1
            ;;
        *)
            PYTEST_ARGS="$PYTEST_ARGS $arg"
            ;;
    esac
done

# 默认参数
if [ -z "$PYTEST_ARGS" ]; then
    PYTEST_ARGS="-v --tb=short"
fi

echo -e "${GREEN}[INFO] 运行测试: pytest $PYTEST_ARGS${NC}"

# 运行 pytest
if [ "$ALLURE_FLAG" -eq 1 ]; then
    ALLURE_DIR="./allure-results"
    rm -rf "$ALLURE_DIR"
    python -m pytest $PYTEST_ARGS --alluredir="$ALLURE_DIR"
    EXIT_CODE=$?

    echo ""
    echo -e "${CYAN}[INFO] 生成 Allure 报告...${NC}"
    allure generate "$ALLURE_DIR" -o "./allure-report" --clean
    echo -e "${GREEN}[INFO] Allure 报告已生成: allure-report/index.html${NC}"
    echo -e "${CYAN}[INFO] 运行 'allure open allure-report' 查看报告${NC}"
else
    python -m pytest $PYTEST_ARGS
    EXIT_CODE=$?
fi

echo ""
if [ "$EXIT_CODE" -eq 0 ]; then
    echo -e "${GREEN}✅ 全部测试通过${NC}"
else
    echo -e "${RED}❌ 部分测试失败 (exit code: $EXIT_CODE)${NC}"
fi

exit "$EXIT_CODE"
