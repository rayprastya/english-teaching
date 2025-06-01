# Mixins for expandable view action

from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseForbidden
class RoleRequiredMixin(AccessMixin):
    """limit user access based on role."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
                
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        user_roles = request.user.groups.values_list('name', flat=True)
        if not set(user_roles).intersection(self.allowed_roles):
            return HttpResponseForbidden("You do not have permission for this action")
        
        return super().dispatch(request, *args, **kwargs)