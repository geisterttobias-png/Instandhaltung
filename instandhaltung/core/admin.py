from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (User, 
                     Department, 
                     SubArea,   
                     Machine, 
                     Order, 
                     OrderAssignment, 
                     WorkLog,
                     LogbookEntry )# models importieren
# Register your models here.
# Einfache Registrierung

admin.site.register(Machine)
admin.site.register(OrderAssignment)
admin.site.register(WorkLog)
admin.site.register(LogbookEntry)
admin.site.register(Department)
admin.site.register(SubArea)

# User registrieren

admin.site.register(User, UserAdmin)


# Eine etwas schickere Ansicht für die Aufträge (optional)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'machine', 'priority', 'status')
    list_filter = ('status', 'priority')
