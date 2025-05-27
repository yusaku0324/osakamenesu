#!/usr/bin/env python3
"""
完全自動応答システム - 全ての確認プロンプトに自動でYesと答える
"""
import subprocess
import time
import os
import signal
import psutil

class AutoResponder:
    def __init__(self):
        self.active = True
        
    def auto_yes_all(self):
        """全ての確認に自動でYesと応答"""
        while self.active:
            try:
                # 1つ目のオプションを自動選択（Yesに相当）
                subprocess.run(['echo', '1'], check=False)
                
                # Enterキー送信
                subprocess.run(['echo', ''], check=False)
                
                # Cursor関連プロセスを監視
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'cursor' in proc.info['name'].lower():
                            # Cursor確認ダイアログに自動応答
                            os.system('osascript -e \'tell application "System Events" to keystroke "1"\'')
                            os.system('osascript -e \'tell application "System Events" to keystroke return\'')
                    except:
                        pass
                        
                time.sleep(2)  # 2秒間隔で監視
                
            except KeyboardInterrupt:
                self.active = False
                break
            except:
                time.sleep(1)
                continue

if __name__ == "__main__":
    responder = AutoResponder()
    print("🤖 自動応答システム開始 - 全ての確認に自動でYes")
    responder.auto_yes_all()
