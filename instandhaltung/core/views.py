from django.shortcuts import render
from .models import Machine, Department, SubArea
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404 # update imports
from .forms import OrderForm, LogbookEntryForm, OrderFilterForm
from .models import Machine, Order, LogbookEntry


@login_required

# View für das Maschinenverzeichnis

def machine_list(request):
   # 1. Immer alle Abteilungen laden (für die Auswahl oben)
    departments = Department.objects.all()
    
    # 2. Prüfen: Hat der User eine Abteilung ausgewählt? (Lese aus URL)
    dept_id = request.GET.get('department')
    sub_id = request.GET.get('subarea')
    
    # Standard: Erstmal keine Maschinen anzeigen (oder alle, je nach Geschmack)
    # Da du sagtest "erst Bereich klicken", fangen wir leer an:
    machines = Machine.objects.all() 
    subareas = all

    # 3. Wenn eine Abteilung gewählt wurde:
    if dept_id:
        # Filtere Maschinen, die zu SubAreas dieser Abteilung gehören
        machines = Machine.objects.filter(subarea__department_id=dept_id)
        # Lade die passenden Unterbereiche für den zweiten Filter
        subareas = SubArea.objects.filter(department_id=dept_id)
        
    # 4. Wenn ZUSÄTZLICH ein Unterbereich gewählt wurde:
    if sub_id:
        machines = machines.filter(subarea_id=sub_id)

    context = {
        'departments': departments,
        'subareas': subareas,
        'machines': machines,
        # Wir geben die Auswahl zurück, damit wir den aktiven Button markieren können
        'selected_dept': int(dept_id) if dept_id else None,
        'selected_sub': int(sub_id) if sub_id else None,
        'order_form': OrderForm()
    }
    return render(request, 'core/machine_list.html', context)

def order_create(request, machine_id):
    # 1. Wir holen uns die Maschine, zu der die Störung gehört
    machine = get_object_or_404(Machine, pk=machine_id)
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # 2. Speichern vorbereiten (commit=False), um Daten zu ergänzen
            order = form.save(commit=False)
            order.machine = machine
            order.creator = request.user # Der aktuelle User
            order.save()

            # Logbucheintrag erstellen
            LogbookEntry.objects.create(
                machine=machine,
                user=request.user,
                order=order,  # Wir verknüpfen es direkt
                content=f"Störung gemeldet: {order.title}"
                )
            
            # 3. Zurück zur Liste
            return redirect('machine_list')

    # Falls jemand versucht, die Seite direkt aufzurufen, schicken wir ihn einfach zurück
    return redirect('machine_list')

def machine_detail(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    
    # 1. Formular-Logik (Verarbeiten, wenn gesendet)
    if request.method == 'POST':
        form = LogbookEntryForm(request.POST)
        if form.is_valid():
            # Hier ist der Trick: commit=False 🛑
            log_entry = form.save(commit=False)
            
            # Jetzt füllen wir die Lücken manuell
            log_entry.machine = machine
            log_entry.user = request.user
            
            # Und ab in die Datenbank damit! 💾
            log_entry.save()
            
            # Seite neu laden, um Post-Resubmit-Probleme zu vermeiden
            return redirect('machine_detail', machine_id=machine.id)
    else:
        # Wenn wir die Seite nur ansehen, brauchen wir ein leeres Formular
        form = LogbookEntryForm()

    # 2. Daten laden
    orders = machine.orders.exclude(status='CLO').order_by('-priority')
    logs = machine.log_entries.all().order_by('-created_at')

    context = {
        'machine': machine,
        'orders': orders,
        'logs': logs,
        'log_form': form,  # <-- WICHTIG: Das Formular muss ins Template!
    }
    return render(request, 'core/machine_detail.html', context)


def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    
    # 1. Neuer Eintrag: Wenn das Formular abgeschickt wurde
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            LogbookEntry.objects.create(
                machine=order.machine, # Gehört immer zur Maschine
                order=order,           # Aber hier speziell auch zum Auftrag
                user=request.user,
                content=content
            )
            return redirect('order_detail', order_id=order.id)

    # 2. Anzeigen: Wir holen alle Logs, die zu diesem Auftrag gehören
    # (Dank related_name='comments' im Model geht das so einfach)
    logs = order.comments.all().order_by('-created_at')

    return render(request, 'core/order_detail.html', {
        'order': order,
        'logs': logs
    })

def log_update(request, log_id, machine_id):
    # 1. Den existierenden Eintrag holen (oder 404 Fehler, wenn nicht gefunden)
    log_entry = get_object_or_404(LogbookEntry, pk=log_id)

    # Optional: Sicherstellen, dass nur der Ersteller ändern darf
    # if log_entry.user != request.user:
    #     return redirect('machine_detail', machine_id=machine_id)

    if request.method == 'POST':
        # WICHTIG: 'instance=log_entry' sorgt für das UPDATE statt CREATE
        form = LogbookEntryForm(request.POST, instance=log_entry)
        if form.is_valid():
            form.save()
            return redirect('machine_detail', machine_id=machine_id)
    else:
        # Formular mit den alten Daten vorbefüllen
        form = LogbookEntryForm(instance=log_entry)

    return render(request, 'core/log_update.html', {
        'form': form,
        'machine_id': machine_id
    })



def order_list(request):
    # 1. Erstmal ALLE Aufträge holen (am besten die neuesten zuerst)
    orders = Order.objects.all().order_by('-priority', '-created_at')
    
    # 2. Formular mit den GET-Daten (aus der URL) füllen
    form = OrderFilterForm(request.GET)

    # 3. Wenn die Daten gültig sind (was bei required=False meistens so ist)
    if form.is_valid():
        subarea = form.cleaned_data.get('subarea')
        machine = form.cleaned_data.get('machine')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

        # 1. Nach Bereich filtern
        # Wir müssen über 'machine' auf 'subarea' zugreifen -> deshalb der doppelte Unterstrich __
        if subarea:
            orders = orders.filter(machine__subarea=subarea)

        # 2. Nach Maschine filtern
        if machine:
            orders = orders.filter(machine=machine)

        # 3. Startdatum (gte = greater than or equal / größer oder gleich)
        if date_from:
            orders = orders.filter(created_at__date__gte=date_from)

        # 4. Enddatum (lte = less than or equal / kleiner oder gleich)
        if date_to:
            orders = orders.filter(created_at__date__lte=date_to)
        
    context = {
        'orders': orders,
        'form': form,
    }
    return render(request, 'core/order_list.html', context)