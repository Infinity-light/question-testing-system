"""
Admin management commands
Run with: python manage_admin.py
"""
from app import create_app, db
from app.models import User


def create_admin():
    """Create an admin user"""
    app = create_app()
    with app.app_context():
        print("=== 创建管理员账号 ===")
        username = input("请输入管理员用户名: ").strip()

        if not username:
            print("错误: 用户名不能为空")
            return

        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"错误: 用户名 '{username}' 已存在")
            return

        password = input("请输入管理员密码: ").strip()
        if not password:
            print("错误: 密码不能为空")
            return

        if len(password) < 6:
            print("错误: 密码至少需要6个字符")
            return

        confirm_password = input("请再次输入密码: ").strip()
        if password != confirm_password:
            print("错误: 两次输入的密码不一致")
            return

        # Create admin user
        admin = User(username=username, role='admin')
        admin.set_password(password)

        try:
            db.session.add(admin)
            db.session.commit()
            print(f"\n✓ 管理员账号创建成功！")
            print(f"  用户名: {username}")
            print(f"  角色: 管理员")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ 创建失败: {str(e)}")


def list_users():
    """List all users"""
    app = create_app()
    with app.app_context():
        users = User.query.all()

        if not users:
            print("没有找到用户")
            return

        print("\n=== 用户列表 ===")
        print(f"{'ID':<5} {'用户名':<20} {'角色':<10} {'创建时间':<20}")
        print("-" * 60)

        for user in users:
            role_map = {'admin': '管理员', 'reviewer': '审核员', 'user': '普通用户'}
            role = role_map.get(user.role, user.role)
            created = user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            print(f"{user.id:<5} {user.username:<20} {role:<10} {created:<20}")


def change_user_role():
    """Change user role"""
    app = create_app()
    with app.app_context():
        print("\n=== 修改用户角色 ===")
        username = input("请输入用户名: ").strip()

        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"错误: 用户 '{username}' 不存在")
            return

        print(f"\n当前用户: {user.username}")
        print(f"当前角色: {user.role}")
        print("\n可选角色:")
        print("1. admin (管理员)")
        print("2. reviewer (审核员)")
        print("3. user (普通用户)")

        choice = input("\n请选择新角色 (1-3): ").strip()

        role_map = {'1': 'admin', '2': 'reviewer', '3': 'user'}
        new_role = role_map.get(choice)

        if not new_role:
            print("错误: 无效的选择")
            return

        user.role = new_role

        try:
            db.session.commit()
            print(f"\n✓ 角色修改成功！")
            print(f"  用户名: {user.username}")
            print(f"  新角色: {new_role}")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ 修改失败: {str(e)}")


def main():
    """Main menu"""
    while True:
        print("\n" + "=" * 50)
        print("管理员管理工具")
        print("=" * 50)
        print("1. 创建管理员账号")
        print("2. 查看所有用户")
        print("3. 修改用户角色")
        print("0. 退出")
        print("=" * 50)

        choice = input("\n请选择操作 (0-3): ").strip()

        if choice == '1':
            create_admin()
        elif choice == '2':
            list_users()
        elif choice == '3':
            change_user_role()
        elif choice == '0':
            print("\n再见！")
            break
        else:
            print("\n错误: 无效的选择")


if __name__ == '__main__':
    main()
