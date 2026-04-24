@echo off
echo ==========================================
echo 🎓 Starting Smart Classroom & Timetable AI
echo ==========================================
echo Installing library dependencies...
pip install -r requirements.txt
echo.
echo Launching Streamlit Portal...
streamlit run app.py
pause
