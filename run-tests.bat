@echo off
REM Test runner script for Lexi Law Agent (Windows)

echo ================================
echo Lexi Law Agent - Test Runner
echo ================================
echo.

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pytest is not installed.
    echo Installing pytest...
    pip install pytest pytest-cov
)

echo.
echo Select test option:
echo 1. Run all tests
echo 2. Run quick tests only (skip integration/performance)
echo 3. Run with coverage report
echo 4. Run specific test file
echo 5. Run tests matching pattern
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto all_tests
if "%choice%"=="2" goto quick_tests
if "%choice%"=="3" goto coverage
if "%choice%"=="4" goto specific
if "%choice%"=="5" goto pattern
goto invalid

:all_tests
echo.
echo Running all tests...
python -m pytest test_file.py -v
goto end

:quick_tests
echo.
echo Running quick tests (excluding integration and performance)...
python -m pytest test_file.py -v -m "not integration and not performance"
goto end

:coverage
echo.
echo Running tests with coverage report...
python -m pytest test_file.py -v --cov=src --cov-report=html --cov-report=term
echo.
echo Coverage report generated in htmlcov/index.html
goto end

:specific
echo.
set /p testfile="Enter test file name (default: test_file.py): "
if "%testfile%"=="" set testfile=test_file.py
echo Running %testfile%...
python -m pytest %testfile% -v
goto end

:pattern
echo.
set /p pattern="Enter test name pattern (e.g., test_auth): "
echo Running tests matching '%pattern%'...
python -m pytest test_file.py -v -k "%pattern%"
goto end

:invalid
echo.
echo Invalid choice. Please run the script again.
exit /b 1

:end
echo.
pause
