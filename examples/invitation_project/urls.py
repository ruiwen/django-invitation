from django.conf.urls.defaults import *
from django.contrib import admin

from registration.forms import RegistrationFormTermsOfService
from invitation.views import register

admin.autodiscover()

urlpatterns = patterns('',
    # Registration/invitation
    url(r'^accounts/register/$',    register,
                                        {'form_class': RegistrationFormTermsOfService},
                                        name='registration_register'),
    url(r'^accounts/',              include('invitation.urls')),
    url(r'^accounts/',              include('registration.urls')),
    url(r'^admin/',                 include(admin.site.urls)),
    
)
