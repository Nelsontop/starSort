# Design: GitHub Star 项目归类工具

## Architecture Overview

```
┌───────────────── 本地环境 ─────────────────────┐
│                                                  │
│  cron job ──→ sync.py                            │
│                ├── gh api ──→ 抓取 stars          │
│                ├── stars.json ──→ 增量比对        │
│                ├── claude CLI ──→ LLM 分类分析    │
│                ├── overrides.yml ──→ 合合覆盖      │
│                └── git commit & push ──→ main     │
│                                                  │
│  零环境变量：全部使用本地已认证 CLI 工具           │
└──────────────────────────────────────────────────┘
                      │ push
                      ▼
┌──────────── GitHub ────────────────────────────┐
│                                                  │
│  main branch                                     │
│    ├── stars.json      (数据)                    │
│    ├── overrides.yml   (手动覆盖配置)            │
│    ├── web/            (Vue 3 + Vite 前端)       │
│    ├── sync.py         (Python 数据脚本)         │
│    └── .github/workflows/deploy.yml             │
│                                                  │
│  GitHub Actions ──→ vite build ──→ GitHub Pages  │
│                                                  │
└──────────────────────────────────────────────────┘
```

## Module Boundaries

### Python 数据层（sync.py）

1. **抓取**：`gh api /user/starred --paginate` 获取所有 starred repos
2. **增量判定**：读取已有 `stars.json`，比对 full_name 集合
3. **LLM 分析**：`claude -p "prompt" --max-turns 1 --output-format text` 批量分类（每批 20 个）
4. **合并覆盖**：读取 `overrides.yml` 合并到 LLM 结果
5. **输出**：写 `stars.json` + 复制到 `web/public/stars.json`
6. **提交**：`git add && git commit && git push`

### Vue 前端（web/）

**x.ai 设计语言（DESIGN.md）**：
- 近黑暗色画布 `#0a0a0a`
- Inter 400-weight 显示字体（universalSans 替代）
- GeistMono uppercase 标签（letter-spacing 1.4px）
- 所有按钮 pill 形状 `9999px` 圆角
- 卡片 `8px` 圆角 + `#191919` 背景 + `#212327` hairline 边框
- 点缀色：sunset `#ff7a17` / breeze `#a0c3ec` / twilight `#c4b5fd`

**组件树**：

```
App.vue
  ├── NavBar.vue           sticky 顶栏：mono eyebrow + 标题 + 搜索框 + 语言选择 + CLEAR pill
  ├── CategoryFilter.vue   分类筛选：mono eyebrow "Categories" + pill 按钮组（tint 色标记）
  ├── ContentArea.vue      内容区
  │   └── CategorySection.vue  每个分类：mono eyebrow + card grid
  │       └── StarCard.vue     card-content：项目名 + 描述（2行截断） + meta（语言/star/topics）
  └── FooterBand.vue       底部：mono 品牌 + 更新时间
```

**数据获取**：`stars.json` 放在 `web/public/`，Vue 通过 `fetch('/stars.json')` 加载。

**Class 共享**：`.eyebrow-mono` 和 `.card-content` 定义在全局 `design.css`，跨 scoped 组件复用。

### GitHub Actions

仅前端构建部署。workflow_dispatch + push main 自动触发。

## Data Flow

### CLI 调用链

```
gh api /user/starred --paginate        → JSON (all stars)
gh api /repos/{owner}/{repo}/readme    → base64 README, 截取前 500 字符
claude -p "<prompt>" --max-turns 1 --output-format text  → JSON text, 解析 classifications
git add stars.json && git commit && git push
```

### 色调分配

8 色调循环分配给分类（originally from Dell 1996，现用作 pill 点缀色）：

| 色调 | 颜色 |
|------|------|
| olive | `#8e8a25` |
| sage | `#b3bd95` |
| salmon | `#d77a7a` |
| peach | `#e6915d` |
| lime | `#c0d4a7` |
| sky | `#9ab6c8` |
| steel | `#a5b8c0` |
| periwinkle | `#8c9ae0` |

## Operational

- **成本**：claude CLI 调用走本地 API key，批量 20 个/次减少调用次数
- **Cron**：`0 3 * * * cd /path/to/starSort && python3 sync.py`
- **README**：部分 repo 无 README 优雅跳过
- **Vite dev server**：vite.config.js 中 `server.host: '0.0.0.0'` 默认暴露局域网
