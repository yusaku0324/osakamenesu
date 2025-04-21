#!/usr/bin/env python3
import os
import sys
import csv
import openpyxl

def process_text_file(filepath, old, new):
    """CSV, JSON, PYなどテキストファイル内の旧文字列を新文字列に置換"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[Error reading] {filepath}: {e}")
        return

    new_content = content.replace(old, new)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[Updated Content] {filepath}")
    except Exception as e:
        print(f"[Error writing] {filepath}: {e}")

def process_excel_file(filepath, old, new):
    """Excelファイル内の各セル（文字列）の旧文字列を新文字列に置換"""
    try:
        wb = openpyxl.load_workbook(filepath)
    except Exception as e:
        print(f"[Error loading Excel] {filepath}: {e}")
        return

    updated = False
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and old in cell.value:
                    cell.value = cell.value.replace(old, new)
                    updated = True
    if updated:
        try:
            wb.save(filepath)
            print(f"[Updated Excel] {filepath}")
        except Exception as e:
            print(f"[Error saving Excel] {filepath}: {e}")
    else:
        print(f"[No changes] {filepath}")

def process_file(filepath, old, new):
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ['.csv', '.json', '.py']:
        process_text_file(filepath, old, new)
    elif ext == '.xlsx':
        process_excel_file(filepath, old, new)
    else:
        print(f"[Skipped] {filepath} (unsupported file type)")

def rename_file(filepath, old, new):
    """ファイル名に旧文字列が含まれている場合、旧文字列を新文字列に置換してリネームする"""
    dirname, filename = os.path.split(filepath)
    new_filename = filename.replace(old, new)
    if new_filename != filename:
        new_filepath = os.path.join(dirname, new_filename)
        try:
            os.rename(filepath, new_filepath)
            print(f"[Renamed] {filepath} -> {new_filepath}")
            return new_filepath
        except Exception as e:
            print(f"[Error renaming] {filepath}: {e}")
            return filepath
    return filepath

def main(root_dir, old, new):
    # 指定ディレクトリ以下を再帰的に探索し、対象ファイルの内容とファイル名を置換
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(('.csv', '.json', '.xlsx', '.py')):
                full_path = os.path.join(dirpath, filename)
                # コンテンツの置換処理
                process_file(full_path, old, new)
                # ファイル名の置換処理
                rename_file(full_path, old, new)

if __name__ == "__main__":
    # ユーザーから置換対象のディレクトリのパスを入力してもらう
    root_directory = input("置換対象のディレクトリのパスを入力してください: ").strip()
    if not root_directory or not os.path.exists(root_directory):
        print("有効なディレクトリパスを入力してください。")
        sys.exit(1)

    # ユーザーから旧文字列と新文字列を入力してもらう
    old_string = input("置換前の文字列を入力してください: ").strip()
    new_string = input("置換後の文字列を入力してください: ").strip()

    # 置換対象とする文字列が入力されているか確認
    if not old_string or not new_string:
        print("両方の文字列を入力してください。")
        sys.exit(1)

    main(root_directory, old_string, new_string)
