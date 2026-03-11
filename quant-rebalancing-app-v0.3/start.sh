#!/bin/bash
# 启动量化配权软件

echo "正在启动量化配权软件..."
echo ""

# 检查依赖是否安装
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "检测到依赖未安装，正在安装..."
    pip3 install -r requirements.txt --quiet
    echo "依赖安装完成"
    echo ""
fi

# 启动Streamlit
echo "启动Web界面..."
echo "请在浏览器中打开: http://localhost:8501"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

streamlit run app.py
