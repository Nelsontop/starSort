# Implement: GitHub Star 项目归类工具

## Execution Checklist

### Phase A: Python 数据层

- [x] A1: 创建 `sync.py` — 使用 `gh api --paginate` 抓取 starred repos
- [x] A2: 实现增量比对逻辑
- [x] A3: 实现 `claude -p` CLI 分类分析（批量 20/批）
- [x] A4: 实现 overrides.yml 合并逻辑
- [x] A5: 实现 stars.json 写入 + tint 色调分配
- [x] A6: 实现 git commit & push
- [ ] A7: 首次真实数据初始化运行

### Phase B: Vue 前端（x.ai 风格）

- [x] B1: 初始化 Vue 3 + Vite 项目（`web/`）
- [x] B2: 实现 x.ai DESIGN.md CSS（暗色画布、Inter + GeistMono、pill/card 样式）
- [x] B3: 实现 NavBar.vue（sticky、mono eyebrow、搜索、语言筛选、CLEAR pill）
- [x] B4: 实现 CategoryFilter.vue（pill 按钮组、tint 点缀色）
- [x] B5: 实现 CategorySection.vue + StarCard.vue（card grid + card-content）
- [x] B6: 实现 FooterBand.vue
- [x] B7: 响应式布局（自适应 card grid）
- [x] B8: web/vite.config.js 默认 `host: 0.0.0.0` 暴露局域网

### Phase C: CI/CD + Cron

- [x] C1: `.github/workflows/deploy.yml`（npm --prefix web install/build + deploy-pages@v4）
- [ ] C2: push 代码到 GitHub 仓库，配置 Pages source = Actions
- [ ] C3: 配置本地 Linux cron job（`0 3 * * *`）

## Validation Commands

```bash
# Python 数据层
python3 sync.py --fetch-only          # 仅抓取
python3 sync.py                       # 增量分析
python3 sync.py --full-refresh        # 全量刷新

# Vue 前端
npm --prefix web run dev              # 开发服务器（自动暴露 0.0.0.0）
npm --prefix web run build            # 生产构建

# 站点验证
curl http://localhost:5176/            # 本地
curl http://192.168.0.105:5176/       # 局域网
```

## Current Project Files

```
starSort/
├── sync.py                    # Python 数据脚本（gh + claude CLI）
├── overrides.yml              # 手动分类覆盖
├── requirements.txt           # pyyaml
├── DESIGN.md                  # x.ai 设计语言
├── .gitignore
├── .github/workflows/deploy.yml
└── web/                       # Vue 3 + Vite
    ├── vite.config.js         # host: 0.0.0.0
    ├── public/stars.json      # mock 数据
    └── src/
        ├── main.js
        ├── App.vue
        ├── assets/design.css  # x.ai design tokens
        └── components/
            ├── NavBar.vue
            ├── CategoryFilter.vue
            ├── ContentArea.vue
            ├── CategorySection.vue
            ├── StarCard.vue
            └── FooterBand.vue
```
