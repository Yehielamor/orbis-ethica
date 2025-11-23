@echo off
REM Orbis Ethica - Setup Script for Windows

echo ================================
echo Orbis Ethica - Setup Script
echo ================================

REM Check Python version
echo Checking Python version...
python --version | findstr "3.11" >nul
if errorlevel 1 (
    echo Python 3.11 not found. Please install Python 3.11+
    exit /b 1
)
echo [OK] Python 3.11+ found

REM Create virtual environment
echo Creating virtual environment...
cd backend
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
echo [OK] Python dependencies installed

REM Create .env file
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo [OK] .env file created (please update with your keys)
) else (
    echo .env file already exists
)

REM Setup frontend
cd ..\frontend
if exist "package.json" (
    echo Installing frontend dependencies...
    call npm install
    echo [OK] Frontend dependencies installed
)

REM Setup blockchain
cd ..\blockchain
if exist "package.json" (
    echo Installing blockchain dependencies...
    call npm install
    echo [OK] Blockchain dependencies installed
)

cd ..

echo.
echo ================================
echo Setup complete!
echo ================================
echo.
echo Next steps:
echo 1. Update backend\.env with your API keys
echo 2. Activate virtual environment: cd backend ^&^& venv\Scripts\activate
echo 3. Run tests: pytest tests\
echo 4. Start CLI: python -m cli.main --help
echo.

pause
