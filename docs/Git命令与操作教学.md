# Git 命令与操作教学

## Step 1 标准收尾流程

```powershell
git status
git add .
git status
git commit -m "chore: step 1 - 项目初始化与工程化配置"
git tag step-1-init
git push
git push origin step-1-init
```

普通 `git push` 不会自动推送标签，所以每个步骤的 tag 都要单独推送。提交前必须确认 `.env`、`.venv`、数据库和日志没有进入暂存区。

## Windows 中文显示配置

```powershell
git config --global core.quotepath false
git config --global i18n.commit.encoding utf-8
git config --global i18n.logoutputencoding utf-8
```

老师的 Step1 文档要求代码和标签推送到 Gitee；若同时使用 GitHub，可为同一个本地仓库配置第二个远程地址。
