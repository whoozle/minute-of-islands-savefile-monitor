from datetime import datetime
import argparse
import ctypes
import os
import shutil

def get_mtime(src_file):
  return os.stat(src_file).st_mtime

def backup(game_dir, src_filename, backup_dir, old_mtime):
  fname, ext = os.path.splitext(src_filename)
  src_file = os.path.join(game_dir, src_filename)
  mtime = get_mtime(src_file)
  if mtime == old_mtime:
    return old_mtime
  date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
  dst_filename = f"{src_filename}-{date}{ext}"
  dst_file = os.path.join(game_dir, backup_dir, dst_filename)
  print(f"backing up {fname} to {dst_file}")
  shutil.copyfile(src_file, dst_file)
  return mtime

arg_p = argparse.ArgumentParser()
arg_p.add_argument("--pretty", "-p", help="Prettify JSON on backup")
arg_p.add_argument("--directory", "-d", default=os.path.join("Studio Fizbin", "Minute of Islands"), help="Path to save inside Local/LocalLow profile")
arg_p.add_argument("--file", "-f", default="savegame.moi", help="File to monitor")
arg_p.add_argument("--backup", "-b", default="backup", help="Backup directory")
args = arg_p.parse_args()

game_dir = None
for local in ["LocalLow", "Local"]:
  dir = os.path.expanduser(os.sep.join(["~", "AppData", local, args.directory]))
  if os.path.exists(dir):
    game_dir = dir
    break

if not game_dir:
    raise RuntimeError(f"No game found in either Local or LocalLow for {args.directory}")

print(f"Found savefile directory at {game_dir}")
backup_dir = os.path.join(game_dir, args.backup)
os.makedirs(backup_dir, exist_ok=True)
print(f"Backups at {backup_dir}")

k32 = ctypes.windll.kernel32
h = k32.FindFirstChangeNotificationW(game_dir, False, 0x0010)
if h == -1:
  raise RuntimeError("FindFirstChangeNotificationW")

WAIT_TIMEOUT = 0x102
mtime = 0
while True:
  r = k32.WaitForSingleObject(h, 100)
  if r == -1:
    raise RuntimeError("WaitForSingleObject failed")
  if r & WAIT_TIMEOUT:
    continue
  r = k32.FindNextChangeNotification(h)
  if not r:
    raise RuntimeError("FindNextChangeNotification failed")
  mtime = backup(game_dir, args.file, args.backup, mtime)
