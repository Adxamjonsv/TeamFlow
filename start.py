import subprocess
import sys
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def check_and_install_dependencies():
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if not os.path.exists(req_file):
        print("[-] requirements.txt fayli topilmadi!")
        return

    print("[*] Kutubxonalar tekshirilmoqda va o'rnatilmoqda...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", req_file
        ])
        print("[+] Barcha kutubxonalar muvaffaqiyatli o'rnatildi!")
    except subprocess.CalledProcessError as e:
        print(f"[-] Kutubxonalarni o'rnatishda xatolik yuz berdi: {e}")
        sys.exit(1)

def ensure_env_file():
    env_file = os.path.join(BASE_DIR, ".env")
    env_example = os.path.join(BASE_DIR, ".env.example")
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            print("[*] .env fayli topilmadi, .env.example dan nusxalanmoqda...")
            shutil.copyfile(env_example, env_file)
            print("[!] Iltimos, yangi yaratilgan .env fayliga BOT_TOKEN va ADMIN_IDS ni kiriting!")
        else:
            print("[-] .env fayli mavjud emas!")

def run_main():
    main_file = os.path.join(BASE_DIR, "main.py")
    if not os.path.exists(main_file):
        print("[-] main.py fayli topilmadi!")
        return

    print("[*] Bot ishga tushirilmoqda...\n")
    try:
        subprocess.run([sys.executable, main_file])
    except KeyboardInterrupt:
        print("\n[+] Bot to'xtatildi.")

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 TELEGRAM VAZIFA BOTI — ISHGA TUSHIRISH")
    print("=" * 50)
    ensure_env_file()
    check_and_install_dependencies()
    run_main()

