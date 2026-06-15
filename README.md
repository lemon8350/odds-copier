# WIN5 Meter

このプロジェクトは、週末のWIN5難易度をリアルタイムで算出するためのPWAアプリケーションです。

## 【クラウド（Render）へのデプロイ手順】

このアプリは、無料のクラウドサービス「Render (https://render.com/)」へ簡単にデプロイできるように設計されています。

### 手順
1. **GitHubリポジトリの作成**
   - ご自身のGitHubアカウントで新しいリポジトリ（例：`win5-meter`）を作成します。
   - この `WIN5_Meter` フォルダ内のファイル一式を、作成したリポジトリにプッシュ（アップロード）します。

2. **Renderでの設定**
   - [Render](https://dashboard.render.com/) にログインします。
   - ダッシュボードの「New +」ボタンから **「Blueprint」** を選択します。
   - GitHubを連携し、先ほど作成した `win5-meter` リポジトリを選択します。
   - Renderが自動的にリポジトリ内の `render.yaml` を読み込み、Webサービスとしてデプロイを開始します。

3. **ScraperAPIキーの登録（Netkeibaのブロック回避用）**
   - デプロイ設定画面、もしくはデプロイ後のダッシュボードの「Environment」タブを開きます。
   - 「Add Environment Variable」をクリックし、以下の変数を追加します。
     - Key: `SCRAPER_API_KEY`
     - Value: （ScraperAPIで取得したあなたのAPIキー）
   - 設定後、「Save Changes」を押すとアプリが自動的に再起動します。

4. **アクセス**
   - デプロイが完了すると、Renderから専用のURL（例: `https://win5-meter-xxxx.onrender.com`）が発行されます。
   - iPhoneのSafariからそのURLにアクセスし、画面下部の共有ボタンから「ホーム画面に追加」をタップすることで、アプリとしてご利用いただけます。

## 【ローカル（Mac）での起動方法】

クラウドにデプロイする前や、テストをしたい場合は、以下のコマンドで起動できます。

1. ターミナルで `WIN5_Meter/backend` ディレクトリに移動します。
2. 以下のコマンドを実行します：
   ```bash
   python3 -m uvicorn main:app --port 8090
   ```
3. 起動後、ブラウザで `http://localhost:8090` にアクセスしてください。
