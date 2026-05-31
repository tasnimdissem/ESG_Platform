@echo off
chcp 65001 >nul
echo ==========================================
echo 🔄 ESG Platform - Mise à jour de l'IA (RAG)
echo ==========================================
echo.
echo Ce script demande au serveur RAG d'indexer les nouveaux documents 
echo presents dans le dossier RAG_SYSTEM\data\raw
echo.
echo ATTENTION : L'application doit etre en cours d'execution (run.bat - Local).
echo.
echo Veuillez patienter, le traitement des PDF peut prendre quelques minutes...
echo.
curl.exe -X POST http://127.0.0.1:8000/api/v1/ingest
echo.
echo.
echo Si vous voyez "Ingestion complete" ci-dessus, l'IA est prete !
pause
