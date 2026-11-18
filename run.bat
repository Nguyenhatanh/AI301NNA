@echo off
chcp 65001 >nul
cd /d %~dp0
REM Dung Python cua may (da co san Streamlit tu lan cai truoc), khong dung .venv bi loi
python -c "import streamlit, plotly, sklearn, docx, reportlab, google.genai, imblearn, pypdf, pptx" 2>nul
if errorlevel 1 (
  echo [1/2] Cai bo sung thu vien con thieu, mang cham co the mat vai phut ...
  python -m pip install --default-timeout=180 --retries 10 -r requirements.txt
  if errorlevel 1 (
    echo.
    echo Mang bi ngat khi tai thu vien. Hay chay lai run.bat - cac goi da tai se khong tai lai.
    pause & exit /b 1
  )
) else (
  echo [1/2] Thu vien da du, bo qua buoc cai dat.
)
if not exist .env copy .env.example .env >nul
echo [2/2] Khoi dong tai http://localhost:8501
python -m streamlit run app.py
