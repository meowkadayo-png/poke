# 寶可夢資訊網（Pokédex Web App）

使用 Python 3.12、Flask 與 requests 製作的繁體中文寶可夢圖鑑，資料來自公開的 PokéAPI v2。

## 本機安裝與啟動

請先安裝 Python 3.12，然後在專案根目錄執行：

```powershell
py -3.12 -m venv .venv
& ./.venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

開啟 http://127.0.0.1:5000。首頁預設每頁 20 筆，可用 `?limit=20&offset=20` 分頁。搜尋支援英文名稱或全國圖鑑編號；詳情頁會顯示屬性、尺寸、能力值、特性及招式摘要，並嘗試顯示繁體中文名稱。

## 專案結構

```text
app.py                 Flask 路由、PokéAPI 呼叫與短期快取
api/index.py           Vercel Python Function 入口
templates/             Jinja2 頁面模板
static/style.css       響應式樣式
requirements.txt       Python 套件需求
vercel.json            Vercel 建置與路由設定
.gitignore             排除虛擬環境、快取及本機設定
```

PokéAPI 僅使用 GET。清單使用回應中的名稱與編號組成圖片網址，不會逐隻呼叫詳細 API；API 回應會在執行個體記憶體中快取五分鐘。Serverless 執行環境可能在不同執行個體間重設快取。

## 推送到 GitHub

在 GitHub 建立空白儲存庫，然後從專案目錄執行：

```bash
git init
git add .
git commit -m "Build Pokédex web app"
git branch -M main
git remote add origin https://github.com/<YOUR-ACCOUNT>/<YOUR-REPOSITORY>.git
git push -u origin main
```

請將網址中的佔位文字換成儲存庫資訊。若已有 Git 設定，先查看 `git status` 與 `git remote -v`，不要重複初始化或覆寫現有遠端。

## 部署到 Vercel

1. 登入 Vercel，選擇 **Add New → Project**，匯入此 GitHub 儲存庫。
2. 專案根目錄保持為儲存庫根目錄，使用預設 Python 設定。
3. 選擇 **Deploy**；`vercel.json` 會將網站路由交給 `api/index.py`。
4. 部署完成後，用 Vercel 提供的網址開啟網站。

部署需要你自己的 GitHub/Vercel 帳號授權。請勿將密碼或存取權杖提交到儲存庫。
