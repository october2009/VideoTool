import os
import glob
import subprocess
import shutil
from datetime import datetime

def run_cmd(cmd):
    print(f"\n▶ 正在执行：{cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ 错误信息：", result.stderr)
        raise RuntimeError("命令执行失败")
    return result.stdout

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def find_latest_video(folder, ext=".mp4"):
    files = glob.glob(os.path.join(folder, f"*{ext}"))
    if not files:
        raise FileNotFoundError(f"在 {folder} 中找不到视频文件")
    return max(files, key=os.path.getctime)

def ask_subtitle_type():
    print("\n字幕类型选项：")
    print("1. 烧录硬字幕（burn-in）")
    print("2. 添加软字幕轨（soft subtitle）")
    choice = input("请输入 1 或 2（默认 1）：").strip()
    return "burn-in" if choice != "2" else "soft"

def archive_old_files(output_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = os.path.join("archive", f"backup_{timestamp}")
    ensure_dir(archive_dir)
    for f in os.listdir(output_dir):
        shutil.move(os.path.join(output_dir, f), os.path.join(archive_dir, f))
    print(f"✅ 旧文件已归档到：{archive_dir}")

def merge_subtitles(video_path, subtitle_path, output_path, subtitle_type):
    if subtitle_type == "burn-in":
        cmd = f'ffmpeg -i "{video_path}" -vf subtitles="{subtitle_path}" -c:a copy "{output_path}"'
    else:
        cmd = (f'ffmpeg -i "{video_path}" -i "{subtitle_path}" -c copy '
               f'-c:s mov_text -metadata:s:s:0 language=chi "{output_path}"')
    run_cmd(cmd)

def main():
    input_folder = input("📁 请输入视频文件夹路径（例如 raw_videos）：").strip()
    if not os.path.exists(input_folder):
        print("❌ 文件夹不存在，请重新运行")
        return

    ensure_dir("output")
    ensure_dir("archive")
    archive_old_files("output")

    latest_video = find_latest_video(input_folder)
    print(f"✅ 找到视频：{latest_video}")

    # Step 1: Auto-Editor 剪辑
    trimmed = os.path.join("output", "trimmed.mp4")
    run_cmd(f'auto-editor "{latest_video}" --edit audio --export "{trimmed}"')

    # Step 2: Whisper 自动生成字幕（translate + 低随机性）
    run_cmd(f'whisper "{trimmed}" --model medium --language Chinese '
            f'--task translate --temperature 0 --output_dir output --output_format srt')

    base = os.path.splitext(os.path.basename(trimmed))[0]
    subtitle_path = os.path.join("output", f"{base}.srt")

    # Step 3: 字幕选择
    sub_type = ask_subtitle_type()
    outname = f"{base}_{sub_type}.mp4"
    output_path = os.path.join("output", outname)

    # Step 4: 合并字幕
    merge_subtitles(trimmed, subtitle_path, output_path, sub_type)

    print(f"\n🎉 完成！输出文件位于：{output_path}")

if __name__ == "__main__":
    main()
