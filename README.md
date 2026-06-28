# ⭐ Star Sort

自动分类 GitHub Star 项目，基于 Claude 大模型分析，x.ai 暗色风格静态站点展示。

## Features

- **智能分类** — 使用 Claude 大模型自动分析每个 Star 项目的用途，动态生成中文分类
- **多分类支持** — 同一个项目可同时属于多个分类
- **中文描述** — 自动将项目描述翻译为简体中文
- **动态同步** — 新增 Star 自动归类，取消 Star 自动移除
- **手动覆盖** — 通过 `overrides.yml` 自定义分类或排除项目
- **高交互站点** — 搜索、分类筛选、语言筛选，x.ai 暗色风格 UI

## Quick Start

```bash
# 1. 确保本地 CLI 已认证
gh auth status       # GitHub CLI
claude --version     # Claude CLI

# 2. 安装依赖
pip install pyyaml

# 3. 首次全量分类
python3 sync.py

# 4. 本地预览
npm --prefix web install
npm --prefix web run dev
```

## 定时更新

```bash
# 每日凌晨 3:00 自动同步
crontab -e
0 3 * * * cd /path/to/starSort && python3 sync.py
```

## 手动覆盖

编辑 `overrides.yml`：

```yaml
overrides:
  "owner/repo":
    categories: ["自定义分类"]
    exclude: true   # 排除不展示
```

## 技术栈

| 层 | 技术 |
|----|------|
| 数据抓取 | `gh` CLI + GitHub REST API |
| 分类分析 | `claude` CLI (Haiku) |
| 前端 | Vue 3 + Vite |
| 设计 | x.ai 暗色风格 |
| 托管 | GitHub Pages |
| 部署 | GitHub Actions |

## 项目结构

```
starSort/
├── sync.py                 # 数据同步脚本
├── overrides.yml           # 手动分类覆盖
├── stars.json              # 分类结果数据
├── web/                    # Vue 前端
│   └── src/components/
│       ├── NavBar.vue
│       ├── CategoryFilter.vue
│       ├── StarCard.vue
│       └── ...
└── .github/workflows/      # CI/CD
```
