#!/usr/bin/env python3
import os
import re
import pandas as pd

def load_mapping(file_path):
    """
    ExcelまたはCSVファイルから、idと稼ぎの対応表を作成する。
    ファイルには「id」と「稼ぎ」というヘッダーがあると仮定する。
    Excelの場合は .xlsx、CSVの場合は .csv に対応。
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".xlsx":
        df = pd.read_excel(file_path)
    elif ext == ".csv":
        df = pd.read_csv(file_path, encoding="utf-8")
    else:
        print(f"Unsupported file type: {file_path}")
        return {}

    mapping = {}
    for _, row in df.iterrows():
        # id を文字列として扱い、前後の空白を除去
        id_value = str(row["id"]).strip()
        # 稼ぎ（新しい名前）も文字列として扱い、前後の空白を除去
        new_name = str(row["稼ぎ"]).strip()
        mapping[id_value] = new_name
    return mapping

def rename_video_files(video_folder, mapping):
    """
    動画フォルダ内の動画ファイル名に含まれる数字（id）を抽出し、
    対応する mapping の値（稼ぎの名前）に置換してファイル名を変更する。
    動画ファイルは、拡張子 .mp4, .mov, .avi, .mkv などを対象とする。
    """
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv')
    for filename in os.listdir(video_folder):
        if filename.lower().endswith(video_extensions):
            # 正規表現でファイル名中の数字を抽出（例: "video_1.mp4" → "1"）
            match = re.search(r'(\d+)', filename)
            if match:
                id_in_filename = match.group(1)
                if id_in_filename in mapping:
                    new_name = mapping[id_in_filename]
                    ext = os.path.splitext(filename)[1]
                    new_filename = f"{new_name}{ext}"
                    old_path = os.path.join(video_folder, filename)
                    new_path = os.path.join(video_folder, new_filename)
                    try:
                        os.rename(old_path, new_path)
                        print(f"Renamed: {filename} -> {new_filename}")
                    except Exception as e:
                        print(f"Error renaming {filename}: {e}")
                else:
                    print(f"Mapping に ID {id_in_filename} が見つかりませんでした（ファイル: {filename}）。")
            else:
                print(f"ファイル名に数字(ID)が見つかりませんでした: {filename}")

def main():
    # 置換対象の Excel または CSV ファイルの絶対パス
    mapping_file = "/Users/yusaku/kakeru/toukou_kakeru.xlsx"  # CSVの場合は .csv に変更
    # 動画ファイルが保存されているフォルダの絶対パス
    video_folder = "/Users/yusaku/kakeru/動画"
    
    # 対応表を読み込む
    mapping = load_mapping(mapping_file)
    if not mapping:
        print("対応表が作成できませんでした。")
        return
    print("Mapping:", mapping)
    
    # 動画フォルダ内のファイル名を置換
    rename_video_files(video_folder, mapping)

if __name__ == "__main__":
    main()
