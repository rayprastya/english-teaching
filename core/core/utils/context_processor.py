def user_role(request):
    if request.user.is_authenticated:
        groups = request.user.groups.values_list('name', flat=True)
        return {'user_role': list(groups)}
    return {'user_role': ["public"]}