# GitHub Star 项目归类工具

## Goal

构建个人 GitHub starred repository 分类工具，以 x.ai 风格静态站点展示（GitHub Pages），每日通过本地 cron 调用本地 claude CLI 自动分析新增 star，手动覆盖通过 `overrides.yml`。

## Requirements

### R1: 数据抓取
- 使用本地 `gh api` CLI 获取用户所有 starred repos（无需额外 Token）
- 提取字段：full_name, description, language, topics, stargazers_count, html_url, created_at, updated_at

### R2: LLM 自动分类
- 使用本地 `claude` CLI（`-p` 单次调用）分析每个 repo（基于 description + topics + language + README excerpt）
- 类别由 LLM 动态生成，无预定义分类词表
- 增量分析：每日仅处理新增 star（对比已有 stars.json）
- 全量刷新：每周一次重新分析所有项目

### R3: 手动覆盖
- `overrides.yml` 存于仓库根目录，格式：
  ```yaml
  overrides:
    "owner/repo":
      categories: ["自定义分类"]
      exclude: true
  ```

### R4: 数据持久化
- `stars.json` 存于仓库根目录和 `web/public/`：
  ```json
  {
    "last_updated": "ISO timestamp",
    "categories": [{ "id", "name", "description", "count", "tint" }],
    "stars": [{ "full_name", "description", "language", "topics", "html_url", "stargazers_count", "categories", "analyzed_at", "override" }]
  }
  ```

### R5: 前端站点（x.ai 风格）
- Vue 3 + Vite 构建单页应用
- UI 风格遵循 DESIGN.md（x.ai）：近黑暗色画布 `#0a0a0a`、Inter 400-weight 字体、GeistMono uppercase 标签、pill 按钮 `9999px` 圆角、卡片 `8px` 圆角、hairline 边框
- 组件：NavBar（sticky）+ CategoryFilter（pill 筛选器）+ ContentArea（card grid）+ StarCard（card-content）+ FooterBand
- 搜索框（项目名/描述模糊搜索）+ 多维度筛选（分类 pill、语言下拉）
- 响应式：自适应 card grid（auto-fill minmax 340px）

### R6: 托管部署
- GitHub Pages 部署
- GitHub Actions：push main → npm --prefix web install → vite build → deploy-pages@v4

### R7: 定时更新
- 本地 Linux cron job 每日定时运行 `python sync.py`
- 使用本地工具链：`gh` CLI → `claude` CLI → `git`，零环境变量

## Acceptance Criteria

- [ ] AC1: `python sync.py` 通过 gh CLI 抓取 starred repos 并写入 stars.json
- [ ] AC2: 新增 star 通过 claude CLI 分析归类，类别名称合理
- [ ] AC3: overrides.yml 覆盖项正确合并，override=true 标记存在
- [ ] AC4: 全量刷新模式重新分析所有项目
- [ ] AC5: Vue 站点渲染 x.ai 风格页面（暗色画布、pill 筛选器、card grid）
- [ ] AC6: 搜索模糊匹配、分类 pill 筛选、语言筛选组合生效
- [ ] AC7: GitHub Actions 自动构建部署到 GitHub Pages
- [ ] AC8: 本地 cron job 每日自动运行 sync.py 并 push

## Out of Scope

- 前端 UI 编辑分类后回写仓库
- 多用户 / OAuth 认证
- 数据库存储
