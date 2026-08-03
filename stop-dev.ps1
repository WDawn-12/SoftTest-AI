# AITestAgent 本地开发一键停止脚本
# 用法：执行 .\stop-dev.ps1
$ports = 8000, 5173
foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        try {
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop
            Write-Host "已停止端口 $port 的进程 (PID $($c.OwningProcess))"
        } catch {
            Write-Host "停止端口 $port 失败: $($_.Exception.Message)"
        }
    }
}
