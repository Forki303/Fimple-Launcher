import os
import json
import subprocess
import customtkinter as ctk
from tkinter import Listbox, simpledialog, messagebox
import minecraft_launcher_lib as mll
from PIL import Image
import uuid
import hashlib
import requests




# ================= НАСТРОЙКИ =================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MC_DIR = os.path.join(os.getcwd(), "Minecraft")
os.makedirs(MC_DIR, exist_ok=True)
INSTANCES_DIR = os.path.join(MC_DIR, "instances")
os.makedirs(INSTANCES_DIR, exist_ok=True)


VERSIONS_FILE = os.path.join(MC_DIR, "versions.json")
SETTINGS_FILE = os.path.join(MC_DIR, "settings.json")

current_language = "ru"

# ================= ПЕРЕВОДЫ =================
translations = {
    "ru": {
        "title": "Fimple Launcher",
        "installed_versions": "Установленные версии",
        "enter_version": "Введите версию Minecraft (например 1.20.1):",
        "install_button": "Установить версию",
        "install_forge": "Установить Forge",
        "enter_forge_version": "Введите версию Minecraft для Forge (например 1.12.2):",
        "forge_installed": "Forge для версии {} установлен!",
        "version_installed": "Версия уже установлена",
        "select_version": "Выберите версию!",
        "enter_nickname": "Введите ник!",
        "launch_button": "Запустить",
        "enter_nickname_label": "Введите ник:",
        "language_button": "English",
        "launch_error": "Ошибка запуска: {}",
        "ram_label": "Выделенная RAM: {} МБ",
        "install_fabric": "Установить Fabric",
        "enter_fabric_version": "Введите версию Minecraft для Fabric (например 1.20.1):",
        "fabric_installed": "Fabric для версии {} установлен!"

    },
    "en": {
        "title": "Fimple Launcher",
        "installed_versions": "Installed Versions",
        "enter_version": "Enter Minecraft version (e.g. 1.20.1):",
        "install_button": "Install Version",
        "install_forge": "Install Forge",
        "enter_forge_version": "Enter Minecraft version for Forge (e.g. 1.12.2):",
        "forge_installed": "Forge for version {} installed!",
        "version_installed": "Version already installed",
        "select_version": "Select a version!",
        "enter_nickname": "Enter nickname!",
        "launch_button": "Launch",
        "enter_nickname_label": "Enter nickname:",
        "language_button": "Русский",
        "launch_error": "Launch error: {}",
        "ram_label": "Allocated RAM: {} MB",
        "install_fabric": "Install Fabric",
        "enter_fabric_version": "Enter Minecraft version for Fabric (e.g. 1.20.1):",
        "fabric_installed": "Fabric for version {} installed!"

    }
}

# ================= НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ =================
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "nickname": "Player",
        "ram": 2048,
        "ely": None

    }

def save_settings():
    data = {
        "nickname": nickname_entry.get(),
        "ram": int(ram_slider.get())
    }

    data = {
        "nickname": nickname_entry.get(),
        "ram": int(ram_slider.get()),
        "ely": settings.get("ely")
    }


    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

settings = load_settings()

# ================= ЯЗЫК =================
def switch_language():
    global current_language
    current_language = "en" if current_language == "ru" else "ru"
    update_ui()

def update_ui():
    root.title(translations[current_language]["title"])
    title_label.configure(text=translations[current_language]["title"])
    versions_label.configure(text=translations[current_language]["installed_versions"])
    nickname_label.configure(text=translations[current_language]["enter_nickname_label"])
    btn_install.configure(text=translations[current_language]["install_button"])
    btn_forge.configure(text=translations[current_language]["install_forge"])
    btn_launch.configure(text=translations[current_language]["launch_button"])
    btn_language.configure(text=translations[current_language]["language_button"])
    btn_fabric.configure(text=translations[current_language]["install_fabric"])

    ram_display.configure(
        text=translations[current_language]["ram_label"].format(int(ram_slider.get()))
    )

# ================= INSTANCES =================
def create_instance(instance_id, mc_version, loader="vanilla"):
    path = os.path.join(INSTANCES_DIR, instance_id)
    os.makedirs(path, exist_ok=True)

    for folder in ["mods", "saves", "config"]:
        os.makedirs(os.path.join(path, folder), exist_ok=True)

    with open(os.path.join(path, "instance.json"), "w", encoding="utf-8") as f:
        json.dump({
            "id": instance_id,
            "mc_version": mc_version,
            "loader": loader
        }, f, indent=2)


def load_instances():
    instances = []
    for name in os.listdir(INSTANCES_DIR):
        meta = os.path.join(INSTANCES_DIR, name, "instance.json")
        if os.path.exists(meta):
            with open(meta, "r", encoding="utf-8") as f:
                instances.append(json.load(f))
    return instances


def refresh_instances():
    version_list.delete(0, "end")
    for inst in load_instances():
        version_list.insert("end", inst["id"])

# ================= УСТАНОВКА VANILLA =================
def install_version():
    version = simpledialog.askstring(
        translations[current_language]["install_button"],
        translations[current_language]["enter_version"]
    )
    if not version:
        return

    try:
        mll.install.install_minecraft_version(version, MC_DIR)

        create_instance(
            instance_id=version,
            mc_version=version,
            loader="vanilla"
        )

        refresh_instances()

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ================= УСТАНОВКА FORGE =================
def install_forge():
    mc_version = simpledialog.askstring(
        translations[current_language]["install_forge"],
        translations[current_language]["enter_forge_version"]
    )
    if not mc_version:
        return

    try:
        forge_version = mll.forge.find_forge_version(mc_version)
        mll.forge.install_forge_version(forge_version, MC_DIR, callback={})


        versions_dir = os.path.join(MC_DIR, "versions")
        forge_ids = [
            v for v in os.listdir(versions_dir)
            if v.startswith(mc_version) and "forge" in v.lower()
        ]

        if not forge_ids:
            raise Exception("Forge установлен, но версия не найдена")

        forge_ids.sort(reverse=True)
        version_id = forge_ids[0]

        instance_id = f"forge-{mc_version}"
        create_instance(instance_id, version_id, "forge")

        refresh_instances()

        messagebox.showinfo(
            "Forge",
            translations[current_language]["forge_installed"].format(mc_version)
        )

    except Exception as e:
        messagebox.showerror("Forge", str(e))

def install_fabric():
    mc_version = simpledialog.askstring(
        translations[current_language]["install_fabric"],
        translations[current_language]["enter_fabric_version"]
    )
    if not mc_version:
        return

    try:
        loader_version = mll.fabric.get_latest_loader_version()
        mll.fabric.install_fabric(mc_version, MC_DIR, loader_version)

        # ВАЖНО: правильный version_id для Fabric
        version_id = f"fabric-loader-{loader_version}-{mc_version}"

        instance_id = f"fabric-{mc_version}"
        create_instance(instance_id, version_id, "fabric")

        refresh_instances()

        messagebox.showinfo(
            "Fabric",
            translations[current_language]["fabric_installed"].format(mc_version)
        )

    except Exception as e:
        messagebox.showerror("Fabric", str(e))


def ely_login():
    email = simpledialog.askstring("Ely.by", "Email:", parent=root)
    if not email:
        return

    password = simpledialog.askstring(
        "Ely.by",
        "Password:",
        parent=root,
        show="*"
    )
    if not password:
        return

    try:
        payload = {
            "username": email,
            "password": password,
            "requestUser": True
        }

        r = requests.post(
            "https://authserver.ely.by/auth/authenticate",
            json=payload,
            timeout=10
        )
        r.raise_for_status()
        data = r.json()

        profile = data["selectedProfile"]

        settings["ely"] = {
            "accessToken": data["accessToken"],
            "uuid": profile["id"],
            "username": profile["name"]
        }

        nickname_entry.delete(0, "end")
        nickname_entry.insert(0, profile["name"])

        save_settings()

        messagebox.showinfo(
            "Ely.by",
            f"Вход выполнен как {profile['name']}"
        )

    except Exception as e:
        messagebox.showerror("Ely.by", f"Ошибка входа:\n{e}")



# ================= UUID (OFFLINE / ELY.BY) =================
def offline_uuid(username: str) -> str:
    md5_hash = hashlib.md5(f"OfflinePlayer:{username}".encode("utf-8")).digest()
    return str(uuid.UUID(bytes=md5_hash))


# ================= ЗАПУСК =================
def launch_version():
    try:
        sel = version_list.curselection()
        if not sel:
            messagebox.showwarning("Warning", translations[current_language]["select_version"])
            return

        inst = load_instances()[sel[0]]
        instance_dir = os.path.join(INSTANCES_DIR, inst["id"])
        version = inst["mc_version"]

        nickname = nickname_entry.get().strip()

        if not nickname:
            messagebox.showwarning("Warning", translations[current_language]["enter_nickname"])
            return

        save_settings()

        ram_amount = int(ram_slider.get())

        authlib_path = os.path.join(MC_DIR, "authlib-injector-1.2.7.jar")
        if not os.path.exists(authlib_path):
            messagebox.showerror("Error", "authlib-injector-1.2.7.jar не найден!")
            return

        ely = settings.get("ely")

        if isinstance(ely, dict):
            options = {
                "username": ely["username"],
                "uuid": ely["uuid"],
                "token": ely["accessToken"],
                "executablePath": "java",
                "jvmArguments": [
                    f"-Xmx{ram_amount}M",
                    f"-Xms{ram_amount}M",
                    f"-javaagent:{authlib_path}=ely.by"
                ],
                "gameDirectory": instance_dir
            }
        else:
            user_uuid = offline_uuid(nickname)
            options = {
                "username": nickname,
                "uuid": user_uuid,
                "token": user_uuid,
                "executablePath": "java",
                "jvmArguments": [
                    f"-Xmx{ram_amount}M",
                    f"-Xms{ram_amount}M",
                    f"-javaagent:{authlib_path}=ely.by"
                ],
                "gameDirectory": instance_dir
            }

        cmd = mll.command.get_minecraft_command(version, MC_DIR, options)
        subprocess.Popen(cmd, cwd=MC_DIR)

    except Exception as e:
        messagebox.showerror(
            "Error",
            translations[current_language]["launch_error"].format(e)
        )

# ================= ОТКРЫТЬ ПАПКУ =================
def open_mc_folder():
    if os.path.exists(MC_DIR):
        if os.name == "nt":
            os.startfile(MC_DIR)
        else:
            subprocess.Popen(["xdg-open", MC_DIR])

# ================= MODRINTH =================

def open_modrinth():
    win = ctk.CTkToplevel(root)
    win.geometry("600x600")
    win.title("Modrinth")

    search_entry = ctk.CTkEntry(win, placeholder_text="Поиск модов...")
    search_entry.pack(padx=10, pady=10, fill="x")

    mods_list = Listbox(win, height=20)
    mods_list.pack(padx=10, pady=5, fill="both", expand=True)

    mods_cache = {}

    def search():
        mods_list.delete(0, "end")
        mods_cache.clear()

        query = search_entry.get().strip()
        if not query:
            return

        r = requests.get(
            "https://api.modrinth.com/v2/search",
            params={
                "query": query,
                "facets": '[["project_type:mod"]]',
                "limit": 30
            },
            timeout=10
        )
        r.raise_for_status()

        for mod in r.json()["hits"]:
            name = mod["title"]
            mods_cache[name] = mod
            mods_list.insert("end", name)

    ctk.CTkButton(win, text="Поиск", command=search).pack(pady=5)

    def open_selected_mod():
        sel = mods_list.curselection()
        if not sel:
            return
        mod = mods_cache[mods_list.get(sel)]
        open_mod_versions(mod)

    mods_list.bind("<Double-Button-1>", lambda e: open_selected_mod())


def open_mod_versions(mod):
    win = ctk.CTkToplevel(root)
    win.geometry("450x500")
    win.title(mod["title"])

    versions_box = Listbox(win)
    versions_box.pack(padx=10, pady=10, fill="both", expand=True)

    r = requests.get(
        f"https://api.modrinth.com/v2/project/{mod['project_id']}/version",
        timeout=10
    )
    r.raise_for_status()

    versions = r.json()

    for v in versions:
        loaders = ", ".join(v["loaders"])
        mc_versions = ", ".join(v["game_versions"])
        versions_box.insert("end", f"{v['name']} | {mc_versions} | {loaders}")

    def install():
        sel = versions_box.curselection()
        if not sel:
            return

        version = versions[sel[0]]
        file = version["files"][0]
        install_mod_file(file["url"], file["filename"])

    ctk.CTkButton(win, text="Установить", command=install).pack(pady=5)

def choose_instance():
    instances = load_instances()

    if not instances:
        messagebox.showwarning("Instance", "Нет инстансов")
        return None

    names = [i["id"] for i in instances]

    choice = simpledialog.askstring(
        "Instance",
        "Куда установить мод?\n\n" + "\n".join(names)
    )

    for i in instances:
        if i["id"] == choice:
            return i
    return None


def install_mod_file(url, filename):
    inst = choose_instance()
    if not inst:
        return

    mods_dir = os.path.join(
        INSTANCES_DIR,
        inst["id"],
        "mods"
    )
    os.makedirs(mods_dir, exist_ok=True)

    path = os.path.join(mods_dir, filename)

    r = requests.get(url, stream=True)
    with open(path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    messagebox.showinfo(
        "Modrinth",
        f"Мод установлен в {inst['id']}"
    )

# ================= GUI =================
root = ctk.CTk()

root.update_idletasks()
screen_h = root.winfo_screenheight()
root.geometry(f"550x{min(800, screen_h - 60)}")
root.resizable(True, True)

main_frame = ctk.CTkScrollableFrame(root, width=520)
main_frame.pack(fill="both", expand=True)


title_label = ctk.CTkLabel(main_frame, text="", font=("Arial", 26, "bold"))
title_label.pack(pady=15)


versions_label = ctk.CTkLabel(root, text="", font=("Arial", 16))
versions_label.pack()

version_list = Listbox(main_frame, width=55, height=15, font=("Arial", 12))
version_list.pack(pady=10)


nick_frame = ctk.CTkFrame(root)
nick_frame.pack(pady=5)

btn_ely = ctk.CTkButton(
    nick_frame,
    width=40,
    height=40,
    text="👤",
    font=("Arial", 20),
    command=lambda: ely_login()
)
btn_ely.pack(side="left", padx=5)

nickname_label = ctk.CTkLabel(nick_frame, text="", font=("Arial", 14))
nickname_label.pack(side="left", padx=5)

nickname_entry = ctk.CTkEntry(nick_frame, width=200)
nickname_entry.pack(side="left", padx=5)
nickname_entry.insert(0, settings["nickname"])

btn_open_folder = ctk.CTkButton(
    nick_frame, width=40, height=40, text="📁", font=("Arial", 20), command=open_mc_folder
)
btn_open_folder.pack(side="left", padx=5)

btn_install = ctk.CTkButton(main_frame, text="", command=install_version, width=250)
btn_install.pack(pady=5)


btn_forge = ctk.CTkButton(root, text="", command=install_forge, width=250)
btn_forge.pack(pady=5)

btn_fabric = ctk.CTkButton(root, text="", command=install_fabric, width=250)
btn_fabric.pack(pady=5)

btn_mods = ctk.CTkButton(
    root,
    text="📚 Библиотека модов (Modrinth)",
    width=250,
    command=open_modrinth
)
btn_mods.pack(pady=5)


ram_frame = ctk.CTkFrame(root)
ram_frame.pack(pady=5)

ram_slider = ctk.CTkSlider(
    ram_frame,
    from_=512,
    to=8192,
    command=lambda v: (
        ram_display.configure(
            text=translations[current_language]["ram_label"].format(int(float(v)))
        ),
        save_settings()
    )
)
ram_slider.set(settings["ram"])
ram_slider.pack(pady=5)

ram_display = ctk.CTkLabel(
    ram_frame,
    text=translations[current_language]["ram_label"].format(settings["ram"]),
    font=("Arial", 12)
)
ram_display.pack(pady=5)

def set_ram(value):
    ram_slider.set(value)
    ram_display.configure(
        text=translations[current_language]["ram_label"].format(value)
    )
    save_settings()

ram_buttons_frame = ctk.CTkFrame(ram_frame)
ram_buttons_frame.pack(pady=5)

ctk.CTkButton(ram_buttons_frame, text="512 MB", width=80, command=lambda: set_ram(512)).pack(side="left", padx=2)
ctk.CTkButton(ram_buttons_frame, text="2 GB", width=80, command=lambda: set_ram(2048)).pack(side="left", padx=2)
ctk.CTkButton(ram_buttons_frame, text="4 GB", width=80, command=lambda: set_ram(4096)).pack(side="left", padx=2)
ctk.CTkButton(ram_buttons_frame, text="8 GB", width=80, command=lambda: set_ram(8192)).pack(side="left", padx=2)

btn_launch = ctk.CTkButton(root, text="", command=launch_version, width=250)
btn_launch.pack(pady=10)

btn_language = ctk.CTkButton(root, text="", command=switch_language, width=250)
btn_language.pack(pady=5)

refresh_instances()
update_ui()
root.mainloop()
