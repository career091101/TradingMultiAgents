#!/usr/bin/env python3
"""WebUI問題診断スクリプト"""

import subprocess
import sys
import platform
import os
import socket
import time

def check_process():
    """プロセス確認"""
    print("=== WebUIプロセス確認 ===")
    try:
        result = subprocess.run(
            ['ps', 'aux'], 
            capture_output=True, 
            text=True
        )
        for line in result.stdout.split('\n'):
            if 'streamlit' in line or 'run_webui' in line:
                if 'grep' not in line:
                    print(f"✅ 発見: {line[:120]}...")
                    return True
        print("❌ WebUIプロセスが見つかりません")
        return False
    except Exception as e:
        print(f"エラー: {e}")
        return False

def check_port():
    """ポート確認"""
    print("\n=== ポート8501の確認 ===")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex(('localhost', 8501))
        if result == 0:
            print("✅ ポート8501は開いています")
            return True
        else:
            print("❌ ポート8501は閉じています")
            return False
    except Exception as e:
        print(f"エラー: {e}")
        return False
    finally:
        sock.close()

def check_architecture():
    """アーキテクチャ確認"""
    print("\n=== アーキテクチャ確認 ===")
    print(f"Python: {sys.executable}")
    print(f"Platform: {platform.machine()}")
    print(f"Architecture: {platform.architecture()}")
    
    # Rosetta確認
    try:
        result = subprocess.run(
            ['sysctl', '-n', 'sysctl.proc_translated'],
            capture_output=True,
            text=True
        )
        translated = result.stdout.strip()
        if translated == '1':
            print("⚠️  Rosetta 2で実行中")
        else:
            print("✅ ネイティブARM64で実行中")
    except:
        pass

def check_streamlit_logs():
    """Streamlitログ確認"""
    print("\n=== Streamlitログ確認 ===")
    log_paths = [
        '.streamlit/logs/streamlit.log',
        'streamlit.log',
        os.path.expanduser('~/.streamlit/logs/streamlit.log')
    ]
    
    for log_path in log_paths:
        if os.path.exists(log_path):
            print(f"\nログファイル: {log_path}")
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    print("最後の10行:")
                    for line in lines[-10:]:
                        print(f"  {line.strip()}")
            except Exception as e:
                print(f"  読み込みエラー: {e}")

def start_webui_with_debug():
    """デバッグモードでWebUI起動"""
    print("\n=== WebUIをデバッグモードで再起動 ===")
    print("現在のプロセスを確認中...")
    
    # 既存プロセスの停止
    subprocess.run(['pkill', '-f', 'streamlit'], capture_output=True)
    time.sleep(2)
    
    print("ARM64環境でWebUIを起動中...")
    cmd = [
        'arch', '-arm64',
        sys.executable,
        'TradingMultiAgents/run_webui.py'
    ]
    
    print(f"コマンド: {' '.join(cmd)}")
    print("\n起動ログ:")
    
    # 起動
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # 最初の数行を表示
    for i in range(20):
        line = process.stdout.readline()
        if not line:
            break
        print(f"  {line.strip()}")
        if 'You can now view your Streamlit app' in line:
            print("\n✅ WebUIが正常に起動しました！")
            print("🌐 ブラウザで http://localhost:8501 にアクセスしてください")
            break
    
    return process

def main():
    """メイン処理"""
    print("WebUI問題診断を開始します...\n")
    
    # 各種チェック
    process_ok = check_process()
    port_ok = check_port()
    check_architecture()
    check_streamlit_logs()
    
    # 問題がある場合は再起動を提案
    if not process_ok or not port_ok:
        print("\n💡 推奨アクション:")
        print("1. 現在のWebUIプロセスを停止: pkill -f streamlit")
        print("2. ARM64モードで再起動: ./run_webui_arm64.sh")
        print("\nまたは、このスクリプトで自動的に再起動しますか？ (y/n): ", end='')
        
        response = input().strip().lower()
        if response == 'y':
            start_webui_with_debug()
    else:
        print("\n✅ WebUIは正常に動作しているようです")
        print("ブラウザの問題の可能性があります:")
        print("1. ブラウザのキャッシュをクリア")
        print("2. 別のブラウザで試す")
        print("3. http://localhost:8501 を直接入力")

if __name__ == '__main__':
    main()