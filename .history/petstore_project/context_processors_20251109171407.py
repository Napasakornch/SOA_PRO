def user_context(request):
    """
    Context processor ที่ส่งข้อมูลผู้ใช้ไปยังทุก template
    """
    return {
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
        'is_admin': request.user.is_authenticated and request.user.is_admin(),
        'is_seller': request.user.is_authenticated and request.user.is_seller(),
        'is_customer': request.user.is_authenticated and request.user.is_customer(),
    }