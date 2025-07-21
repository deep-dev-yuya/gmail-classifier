# Claude Desktop DXT 移行計画

## 🎯 移行目的
現在のDocker MCP構成からDXT（Desktop Extensions）への移行により、以下の改善を実現：
- 設定の簡素化
- 性能向上（Docker オーバーヘッドなし）
- 保守性の向上
- ワンクリック インストール・更新

## 📋 現在の構成分析

### 既存のDocker MCP設定
```json
{
  "mcp": {
    "server": {
      "host": "127.0.0.1",
      "port": 5003
    }
  },
  "mcpServers": {
    "MCP_DOCKER": {
      "command": "docker",
      "args": [
        "run", "-l", "mcp.client=claude-desktop", "--rm", "-i",
        "alpine/socat", "STDIO", "TCP:host.docker.internal:8811"
      ]
    }
  }
}
```

### 現在の機能
- ファイルシステム アクセス（mcp/filesystem）
- Docker コンテナ管理
- TCP トンネル経由の通信

## 🚀 DXT移行手順

### Step 1: 準備作業
```bash
# 1. 現在の設定をバックアップ
cp "~/Library/Application Support/Claude/claude_desktop_config.json" ./claude_desktop_config.json.backup

# 2. DXT CLI の確認（既にインストール済み）
dxt --version
```

### Step 2: 推奨DXT拡張のダウンロード
```bash
# File Manager DXT（ファイルシステム機能）
curl -o file-manager.dxt https://www.desktopextensions.com/downloads/file-manager.dxt

# Database Connector DXT（データベース機能）
curl -o database.dxt https://www.desktopextensions.com/downloads/database.dxt

# Git Integration DXT（Git機能）
curl -o git-integration.dxt https://www.desktopextensions.com/downloads/git-integration.dxt
```

### Step 3: DXT拡張のインストール
```bash
# 方法1: ファイルをダブルクリック
open file-manager.dxt

# 方法2: Claude Desktop UI経由
# Settings → Extensions → Install from file
```

### Step 4: 設定ファイルの更新
新しい設定ファイル（claude_desktop_config.json）:
```json
{
  "mcp": {
    "server": {
      "host": "127.0.0.1",
      "port": 5003
    }
  },
  "extensions": {
    "file-manager": {
      "enabled": true,
      "permissions": ["read", "write", "execute"],
      "paths": [
        "/Users/hasegawayuya/Projects",
        "/Users/hasegawayuya/Documents"
      ]
    },
    "database": {
      "enabled": true,
      "connections": {
        "local": {
          "type": "sqlite",
          "path": "/Users/hasegawayuya/Documents/databases/"
        }
      }
    },
    "git": {
      "enabled": true,
      "repositories": [
        "/Users/hasegawayuya/Projects"
      ]
    }
  }
}
```

### Step 5: 動作確認
```bash
# 1. Claude Desktop を再起動
pkill -f "Claude Desktop"
open -a "Claude Desktop"

# 2. 拡張機能の動作確認
# Claude Desktop で以下をテスト：
# - ファイル読み書き
# - データベース接続
# - Git操作
```

### Step 6: 旧設定の削除
```bash
# Docker MCP設定の削除（動作確認後）
# claude_desktop_config.json から mcpServers セクションを削除

# 不要なDockerコンテナの削除
docker stop $(docker ps -q --filter "label=mcp.client=claude-desktop")
docker rm $(docker ps -aq --filter "label=mcp.client=claude-desktop")
```

## 🔍 移行後の期待効果

### 1. 性能向上
- Docker オーバーヘッドなし
- 直接実行による高速化
- メモリ使用量削減

### 2. 保守性向上
- 設定の一元管理
- 自動更新機能
- エラーハンドリング改善

### 3. 機能拡張
- 50+ 拡張から選択可能
- 公式サポート
- コミュニティ開発

## 🚨 注意点・リスク

### 1. 互換性確認
- 既存のスクリプトとの互換性確認
- API仕様の変更がないか確認

### 2. データ安全性
- 設定変更前にバックアップ
- 重要なデータの保護

### 3. 段階的移行
- 一度に全て移行せず、段階的に実施
- 問題発生時の復旧計画

## 📊 移行スケジュール

### Phase 1: 準備・検証（今日）
- [x] DXT CLI インストール
- [x] 現在の設定分析
- [ ] File Manager DXT ダウンロード・テスト

### Phase 2: 部分移行（1-2日後）
- [ ] File Manager DXT 本格導入
- [ ] ファイルシステム機能の動作確認
- [ ] 既存機能との比較

### Phase 3: 完全移行（3-5日後）
- [ ] 全DXT拡張の導入
- [ ] Docker MCP設定の削除
- [ ] 動作確認・最適化

## 🎯 成功指標

### 1. 機能維持
- 既存の全機能が正常動作
- 性能劣化なし

### 2. 保守性向上
- 設定変更の簡素化
- エラー頻度の削減

### 3. 拡張性確保
- 新機能の追加容易性
- 将来的な拡張可能性

## 📝 まとめ

DXT移行により、Claude Desktop の機能を維持しながら、設定の簡素化と性能向上を実現できます。段階的な移行により、リスクを最小化しつつ、最新の拡張システムの恩恵を受けることができます。