from concurrent.futures import ThreadPoolExecutor
from datetime import date
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from students.models import Student
from students.services import create_student

User = get_user_model()

# 创建一个尚未绑定任何业务身份的用户
user = User.objects.create_user(
    username="test_student_concurrent",
    password="testpass123",
)

operator = User.objects.get(username="test_superuser")


def create_concurrently(index):
    close_old_connections()

    try:
        student = create_student(
            validated_data={
                "name": f"并发测试学生{index}",
                "student_no": f"CONCURRENT{index}",
                "birth_date": date(2005, 1, 1),
                "user_id": user.id,
            },
            operator_id=operator.id,
        )
        return f"成功：Student ID={student.id}"

    except Exception as exc:
        return f"失败：{type(exc).__name__}，{exc}"

    finally:
        close_old_connections()


with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(create_concurrently, [1, 2]))

print(results)

print(
    "最终绑定数量：",
    Student.objects.filter(user_id=user.id).count()
)