# AITestAgent 本地开发一键启动脚本
# 用法：双击运行，或执行 .\start-dev.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 工具链：系统环境缺少 node/pnpm 时回退到 Codex 内置运行时
$nodeBin = "C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin"
$pnpmFallback = "C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { $env:Path = "$nodeBin;$env:Path" }

$python = Join-Path $root "backend\.venv\Scripts\python.exe"
$pnpm = (Get-Command pnpm -ErrorAction SilentlyContinue).Source
if (-not $pnpm) { $pnpm = $pnpmFallback }

# 启动后端（8000）
$beUp = (Test-NetConnection 127.0.0.1 -Port 8000 -WarningAction SilentlyContinue).TcpTestSucceeded
if (-not $beUp) {
    Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
        -WorkingDirectory (Join-Path $root "backend") -WindowStyle Hidden
    Write-Host "后端已启动 (8000)"
} else {
    Write-Host "后端已在运行 (8000)"
}

# 启动前端（5173）
$feUp = (Test-NetConnection 127.0.0.1 -Port 5173 -WarningAction SilentlyContinue).TcpTestSucceeded
if (-not $feUp) {
    Start-Process -FilePath $pnpm -ArgumentList "dev" `
        -WorkingDirectory (Join-Path $root "frontend") -WindowStyle Hidden
    Write-Host "前端已启动 (5173)"
} else {
    Write-Host "前端已在运行 (5173)"
}

Write-Host ""
Write-Host "前端页面：http://localhost:5173"
Write-Host "后端文档：http://localhost:8000/docs"
Start-Sleep -Seconds 2
