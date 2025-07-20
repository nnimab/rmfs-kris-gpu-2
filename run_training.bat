@echo off
chcp 65001 > nul
SETLOCAL

REM =================================================
REM        ROBUST INTERACTIVE LAUNCHER
REM =================================================

REM --- Step 1: Check for Virtual Environment ---
IF EXIST ".venv\Scripts\activate.bat" GOTO VENV_OK

echo [ERROR] Virtual environment (.venv) not found.
echo Please run 'py -3.11 -m venv .venv' first to create it.
pause
GOTO :EOF

:VENV_OK
REM --- Step 2: Display Menu ---
:MENU
cls
echo ============================================================================
echo                RMFS INTERACTIVE EXPERIMENT LAUNCHER
echo ============================================================================
echo.
echo   [1] dqn_step      (DQN, Step Reward, 1.6M Ticks)
echo   [2] dqn_global    (DQN, Global Reward, 1.6M Ticks)
echo   [3] nerl_step_a   (NERL, Step Reward, Variant A, 20 workers)
echo   [4] nerl_global_a (NERL, Global Reward, Variant A, 20 workers)
echo   [5] nerl_step_b   (NERL, Step Reward, Variant B, 20 workers)
echo   [6] nerl_global_b (NERL, Global Reward, Variant B, 20 workers)
echo.
echo   [7] Exit
echo.
echo ============================================================================

CHOICE /C 1234567 /N /M "Enter your choice [1-7]:"

REM --- Step 3: Process Choice ---
IF ERRORLEVEL 7 GOTO QUIT
IF ERRORLEVEL 6 GOTO RUN_NERL_GLOBAL_B
IF ERRORLEVEL 5 GOTO RUN_NERL_STEP_B
IF ERRORLEVEL 4 GOTO RUN_NERL_GLOBAL_A
IF ERRORLEVEL 3 GOTO RUN_NERL_STEP_A
IF ERRORLEVEL 2 GOTO RUN_DQN_GLOBAL
IF ERRORLEVEL 1 GOTO RUN_DQN_STEP
GOTO MENU


REM --- Step 4: Define Tasks ---
:RUN_DQN_STEP
CALL :RUN_TASK "dqn_step" "python train.py --agent dqn --reward_mode step --log_level DEBUG --training_ticks 1600000"
GOTO END_TASK

:RUN_DQN_GLOBAL
CALL :RUN_TASK "dqn_global" "python train.py --agent dqn --reward_mode global --log_level DEBUG --training_ticks 1600000"
GOTO END_TASK

:RUN_NERL_STEP_A
CALL :RUN_TASK "nerl_step_a" "python train.py --agent nerl --reward_mode step --log_level DEBUG --variant a --generations 20 --population 20 --eval_ticks 4000 --parallel_workers 20"
GOTO END_TASK

:RUN_NERL_GLOBAL_A
CALL :RUN_TASK "nerl_global_a" "python train.py --agent nerl --reward_mode global --log_level DEBUG --variant a --generations 20 --population 20 --eval_ticks 4000 --parallel_workers 20"
GOTO END_TASK

:RUN_NERL_STEP_B
CALL :RUN_TASK "nerl_step_b" "python train.py --agent nerl --reward_mode step --log_level DEBUG --variant b --generations 20 --population 20 --eval_ticks 4000 --parallel_workers 20"
GOTO END_TASK

:RUN_NERL_GLOBAL_B
CALL :RUN_TASK "nerl_global_b" "python train.py --agent nerl --reward_mode global --log_level DEBUG --variant b --generations 20 --population 20 --eval_ticks 4000 --parallel_workers 20"
GOTO END_TASK


REM --- Subroutine for running the actual command ---
:RUN_TASK
cls
echo [INFO] Activating virtual environment...
CALL ".venv\Scripts\activate.bat"
echo.
echo ============================================================================
echo  Starting Task: %~1
echo ============================================================================
echo.
%~2
echo.
echo ============================================================================
echo  Task Finished: %~1
echo ============================================================================
GOTO :EOF

:END_TASK
GOTO MENU

:QUIT
cls
echo [INFO] Exiting script.

:END
ENDLOCAL
echo.
pause 