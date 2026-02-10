"""
Quick admin creation script
Usage: python create_admin.py <username> <password>
"""
import sys
from app import create_app, db
from app.models import User


def create_admin(username, password):
    """Create an admin user"""
    app = create_app()
    with app.app_context():
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f'错误: 用户名 "{username}" 已存在')
            return False

        if len(password) < 6:
            print('错误: 密码至少需要6个字符')
            return False

        # Create admin user
        admin = User(username=username, real_name=username, organization='系统管理', role='admin')
        admin.set_password(password)

        try:
            db.session.add(admin)
            db.session.commit()
            print(f'\n✓ 管理员账号创建成功！')
            print(f'  用户名: {username}')
            print(f'  角色: 管理员')
            return True
        except Exception as e:
            db.session.rollback()
            print(f'\n✗ 创建失败: {str(e)}')
            return False


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('用法: python create_admin.py <用户名> <密码>')
        print('示例: python create_admin.py admin admin123')
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    success = create_admin(username, password)
    sys.exit(0 if success else 1)
