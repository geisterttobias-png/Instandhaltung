from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# 1. ERWEITERTER USER (Wegen der Rollen)
class User(AbstractUser):
    class Role(models.TextChoices):
        OPERATOR = 'OP', 'Maschinenführer'
        COORDINATOR = 'CO', 'IH-Koordinator'
        TECHNICIAN = 'TE', 'Instandhalter'
        MANAGER = 'MG', 'Manager'

    role = models.CharField(
        max_length=2, 
        choices=Role.choices, 
        default=Role.OPERATOR
     )

# Hierarchie für Maschine

class Department(models.Model):
    name = models.CharField(max_length=5)


class SubArea(models.Model):
    name = models.CharField(max_length=50)
    department = models.ForeignKey('Department', on_delete=models.CASCADE, null=True, blank=True,  related_name='subareas')

    def __str__(self):
        return f"{self.department.name} - {self.name}"
# 2. MASCHINE
class Machine(models.Model):
    name = models.CharField(max_length=100)
    inventory_number = models.CharField(max_length=50, unique=True)
    subarea = models.ForeignKey('SubArea', on_delete=models.CASCADE, null=True, blank=True,related_name='machines') # Verknopfung zur SubArea

    def __str__(self):
        return f"{self.name} ({self.inventory_number})"

# 3. AUFTRAG (Das Ticket)
class Order(models.Model):
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Niedrig'
        MEDIUM = 'MED', 'Mittel'
        HIGH = 'HI', 'Hoch'
        EMERGENCY = 'EM', 'Notfall'

    class Status(models.TextChoices):
        NEW = 'NEW', 'Neu'
        PLANNED = 'PLN', 'Disponiert'
        IN_PROGRESS = 'INP', 'In Arbeit'
        PAUSED = 'PAU', 'Pausiert'
        TRIAL = 'TRI', 'Probelauf'
        REVIEW = 'REV', 'Abnahme'
        CLOSED = 'CLO', 'Geschlossen'

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='orders')
    creator = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_orders')
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=3, choices=Priority.choices, default=Priority.LOW)
    status = models.CharField(max_length=3, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.id} {self.title} ({self.get_status_display()})"

# 4. ZUWEISUNG (Für die Timeline/Planung)
class OrderAssignment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='assignments')
    technician = models.ForeignKey('User', on_delete=models.CASCADE, related_name='assignments')
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()

# 5. ZEITERFASSUNG (Für Start/Stop Logik)
class WorkLog(models.Model):
    class ActivityType(models.TextChoices):
        WORK = 'WORK', 'Arbeit'
        PAUSE = 'PAUSE', 'Pause'
        TRIAL = 'TRIAL', 'Probelauf'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='work_logs')
    technician = models.ForeignKey('User', on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    activity_type = models.CharField(max_length=10, choices=ActivityType.choices)
    comment = models.CharField(max_length=255, blank=True)

    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return timezone.now() - self.start_time

# 6. LOGBUCH (Historie & Manuelle Einträge)
class LogbookEntry(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='log_entries')
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
