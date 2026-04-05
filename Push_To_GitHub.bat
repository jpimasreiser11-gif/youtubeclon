@echo off
echo =======================================================
echo        PUSHEANDO CODIGO A GITHUB (ACTUALIZACION)       
echo =======================================================
echo.

cd /d "%~dp0"

echo [1] Verificando estado git...
git status

echo.
echo [2] Añadiendo archivos modificados...
git add .

echo.
echo [3] Creando commit...
git commit -m "fix(engine): Reparado ETA display y dependencias de procesamiento de clips"

echo.
echo [4] Subiendo a GitHub...
git push origin main

echo.
echo =======================================================
echo                 PROCESO COMPLETADO                     
echo =======================================================
pause
