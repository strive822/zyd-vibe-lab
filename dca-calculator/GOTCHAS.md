# GOTCHAS — 踩坑记录

### 东财 WAF 按 TLS/请求头指纹拦截脚本客户端（2026-09-02）
- 问题现象：python-requests 请求东财接口间歇性 `RemoteDisconnected`，同一 URL curl 却正常
- 根本原因：东财 WAF 识别非浏览器请求指纹（默认 keep-alive + 头集合）
- 解决方案：携带浏览器级请求头（UA/Accept/Accept-Language/Referer）+ `Connection: close`
- 未来避免方式：访问东财 push2 系列接口一律带浏览器头；出现秒级瞬断先怀疑指纹拦截而非网络

### Windows 系统代理被 requests 自动读取导致 ProxyError（2026-09-02）
- 问题现象：requests 全部请求报 ProxyError（代理 127.0.0.1:xxxx），curl 正常
- 根本原因：requests 经 urllib 读取 Windows 注册表 Internet Settings 的系统代理；
  环境变量里看不到，排查时容易漏
- 解决方案：国内数据源用 `session.trust_env = False` 直连优先，失败再走系统代理兜底
- 未来避免方式：凡访问国内接口，默认直连优先；排查 ProxyError 先查注册表代理

### 东财 HTTPS 主域断连但 HTTP/镜像子域可用（2026-09-02）
- 问题现象：`https://push2his.eastmoney.com` 断连或返回空体；HTTP(80) 与
  `92.push2his.eastmoney.com` 正常
- 解决方案：多端点按序回退（HTTP 主域 → HTTPS 数字子域镜像）
- 未来避免方式：东财端点配置成列表而非单 URL

### 腾讯美股指数无深历史（2026-09-02）
- 问题现象：`fqkline/get?param=usNDX,day,,,800,qfq` 只返回 1 根日线
- 解决方案：NDX 回退源改用新浪 `US_MinKService.getDailyK?symbol=.NDX`（3153 根）；
  fetch 层加"历史≥800 才算可用"守卫，浅历史源自动跳过
- 未来避免方式：回退源必须实测历史深度，不能只看实时价可用

### 测试间 60 秒缓存串扰（2026-09-02）
- 问题现象：mock 回退链的三个测试互相"DID NOT RAISE"
- 根本原因：`fetch_asset_data` 的模块级 TTL 缓存在前一个测试写入了同 key 数据
- 解决方案：测试内 `monkeypatch.setattr(md, "_CACHE", {})` 清空
- 未来避免方式：给带缓存的函数写单测时，先清缓存或注入缓存

### Next.js 15.4.6 有已知漏洞 CVE-2025-66478（2026-09-02）
- 解决方案：`npm install next@15` 升级到 15.5.25 修补版
- 未来避免方式：npm install 的 deprecation/security warning 不要忽略
