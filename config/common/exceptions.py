from rest_framework.views import exception_handler
from rest_framework.settings import api_settings

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    status_code = response.status_code
    data = response.data

    if isinstance(data, dict) and "detail" not in data:
        # 字段级校验错误
        errors = data
        message = "请求参数错误"

    elif isinstance(data, list):
        # 非字段级校验错误
        errors = {
            api_settings.NON_FIELD_ERRORS_KEY: data
        }
        message = "请求参数错误"

    else:
        # 认证、权限、404 等 HTTP 异常
        errors = None

        if isinstance(data, dict):
            message = str(data.get("detail", "请求失败"))
        else:
            message = str(data)

    response.data = {
        "code": status_code,
        "message": message,
        "errors": errors,
    }

    return response