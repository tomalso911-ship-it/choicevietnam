# AGI-PM Node 后端

`node-backend` 是 AGI-PM 的 Node 运行壳：`server.mjs` 托管前端，并把每个请求转成 Web `Request` 交给后端业务代码处理，再把 `Response` 回写。

## 当前状态
- 原后端业务代码（认证、CRM/签约/失败/审批、用户权限、附件、备注补翻、价格快照、私密空间等）
  此前位于 `cloudflare/src/` 并由本目录复用，**现已移除**。
- 本目录当前**不含可运行的后端业务逻辑**。如需运行，请把后端业务代码放入
  `node-backend/src/` 并修改 `server.mjs` 的 import 路径指向本地 `src`。
- 数据层 / 文件层通过 `d1shim.mjs` / `filesshim.mjs` 适配，可对接本地 SQLite 与本地磁盘。

## 最简启动（业务代码就绪后）
```bash
cd node-backend
npm install
cp .env.example .env   # 按需修改 VAULT_PIN
node server.mjs
# 或：npm i -g pm2 && pm2 start server.mjs --name agi-pm
```
放通端口 3000；如需 HTTPS，套 nginx + certbot 反代到 127.0.0.1:3000。

## 验证
`npm install && node server.mjs` 后访问 `http://<服务器IP>:3000/api/health` 应返回各表行数。
