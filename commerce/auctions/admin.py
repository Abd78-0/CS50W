from django.contrib import admin

from auctions.models import Bid, Listing, User, Comment

# Register your models here.
admin.site.register(User)
admin.site.register(Listing)
admin.site.register(Bid)
admin.site.register(Comment)
