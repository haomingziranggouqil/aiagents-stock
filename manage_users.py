#!/usr/bin/env python3
"""
用户账号管理工具

用法（在项目目录下，已激活venv）:
  python manage_users.py list                      列出所有用户
  python manage_users.py add <用户名> [密码]        新增用户（不带密码则交互式输入）
  python manage_users.py passwd <用户名> [密码]     修改密码
  python manage_users.py del <用户名>               删除用户

密码以 pbkdf2 加盐哈希存储于 data_db/users.db。
"""

import sys
import getpass

from core.user_store import user_store


def _prompt_password():
    pwd = getpass.getpass("请输入密码: ")
    pwd2 = getpass.getpass("请再次输入密码: ")
    if pwd != pwd2:
        print("❌ 两次输入的密码不一致")
        sys.exit(1)
    if not pwd:
        print("❌ 密码不能为空")
        sys.exit(1)
    return pwd


def cmd_list():
    users = user_store.list_users()
    if not users:
        print("（暂无用户，未启用登录）")
    else:
        print(f"共 {len(users)} 个用户:")
        for u in users:
            print(f"  - {u}")


def cmd_add(args):
    if not args:
        print("用法: python manage_users.py add <用户名> [密码]")
        sys.exit(1)
    username = args[0]
    password = args[1] if len(args) > 1 else _prompt_password()
    try:
        user_store.add_user(username, password)
        print(f"✅ 已新增用户: {username}")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)


def cmd_passwd(args):
    if not args:
        print("用法: python manage_users.py passwd <用户名> [密码]")
        sys.exit(1)
    username = args[0]
    password = args[1] if len(args) > 1 else _prompt_password()
    try:
        user_store.set_password(username, password)
        print(f"✅ 已修改密码: {username}")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)


def cmd_del(args):
    if not args:
        print("用法: python manage_users.py del <用户名>")
        sys.exit(1)
    username = args[0]
    if user_store.delete_user(username):
        print(f"✅ 已删除用户: {username}")
    else:
        print(f"⚠️ 用户不存在: {username}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "list":
        cmd_list()
    elif command == "add":
        cmd_add(args)
    elif command == "passwd":
        cmd_passwd(args)
    elif command in ("del", "delete", "rm"):
        cmd_del(args)
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
