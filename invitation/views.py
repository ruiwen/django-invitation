from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from registration.views import register as registration_register
from registration.forms import RegistrationForm

from invitation.models import InvitationKey
from invitation.forms import InvitationKeyForm

is_key_valid = InvitationKey.objects.is_key_valid
remaining_invitations_for_user = InvitationKey.objects.remaining_invitations_for_user

# TODO: move the authorization control to a dedicated decorator

class InvitationUsedCallback(object):
    """
    Callable to mark InvitationKey as used, by way of profile_callback.
    """
    def __init__(self, invitation_key, profile_callback):
        self.invitation_key = invitation_key
        self.profile_callback = profile_callback
        
    def __call__(self, user):
        """Mark the key used, and then call the real callback (if any)."""
        key = InvitationKey.objects.get_key(self.invitation_key)
        if key:
            key.mark_used(user)

        if self.profile_callback:
            self.profile_callback(user)

            
def invited(request, invitation_key=None, extra_context=None):
    if 'INVITE_MODE' in settings.get_all_members() and settings.INVITE_MODE:
        if invitation_key and is_key_valid(invitation_key):
            template_name = 'invitation/invited.html'
        else:
            template_name = 'invitation/wrong_invitation_key.html'
        extra_context = extra_context is not None and extra_context.copy() or {}
        extra_context.update({'invitation_key': invitation_key})
        return direct_to_template(request, template_name, extra_context)
    else:
        return HttpResponseRedirect(reverse('registration_register'))

def register(request, success_url=None,
            form_class=RegistrationForm, profile_callback=None,
            template_name='registration/registration_form.html',
            extra_context=None):
    extra_context = extra_context is not None and extra_context.copy() or {}
    if 'INVITE_MODE' in settings.get_all_members() and settings.INVITE_MODE:
        if 'invitation_key' in request.REQUEST:
            if is_key_valid(request.REQUEST['invitation_key']):
                invitation_key = request.REQUEST['invitation_key']
                extra_context.update({'invitation_key': invitation_key})
                profile_callback = InvitationUsedCallback(invitation_key, 
                                                          profile_callback)
                return registration_register(request, success_url, form_class, 
                            profile_callback, template_name, extra_context)
            else:
                extra_context.update({'invalid_key': True})
        else:
            extra_context.update({'no_key': True})
        template_name = 'invitation/wrong_invitation_key.html'
        return direct_to_template(request, template_name, extra_context)
    else:
        return registration_register(request, success_url, form_class, 
                            profile_callback, template_name, extra_context)

def invite(request, success_url=None, 
            form_class=InvitationKeyForm,
            template_name='invitation/invitation_form.html', 
            extra_context=None):
    extra_context = extra_context is not None and extra_context.copy() or {}
    remaining_invitations = remaining_invitations_for_user(request.user)
    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if remaining_invitations > 0 and form.is_valid():
            invitation = InvitationKey.objects.create_invitation(request.user)
            invitation.send_to(form.cleaned_data["email"])
            # success_url needs to be dynamically generated here; setting a
            # a default value using reverse() will cause circular-import
            # problems with the default URLConf for this application, which
            # imports this file.
            return HttpResponseRedirect(success_url or reverse('invitation_complete'))
    else:
        form = form_class()
    extra_context.update({
            'form': form,
            'remaining_invitations': remaining_invitations,
        })
    return direct_to_template(request, template_name, extra_context)
invite = login_required(invite)
