

# 自用节点
类型 Trojan
别名 user w2-zfmgeu9z
地址 kk.323424.xyz
端口 3023
传输协议 tcp
tls TLS
延迟(ms) 233 

# github代理（开启节点下）

代码上传  git push TkVoiceJourney  
代码下载 https://github.com/Wu-ChengLiang/TkVoiceJourney

## 若连接卡顿
git remote -v  
### 检查代理运行
Get-Process | Where-Object {$_.ProcessName -match "clash|v2ray|trojan|shadowsocks|sing-box"} | Select-Object ProcessName,Id