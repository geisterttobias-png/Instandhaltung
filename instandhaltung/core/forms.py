from django import forms
from .models import Order, LogbookEntry, Machine,SubArea



class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['title', 'description']
        
        # Damit die Felder hübsch aussehen (Bootstrap-Klassen)
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Kurzer Titel, z.B. "Pumpe leckt"'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Details zur Störung...'
            }),
        }

class LogbookEntryForm(forms.ModelForm):
    class Meta:
        model = LogbookEntry
        fields = ['content']  # Wir fragen nur den Text ab
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Neuer Eintrag...'}),
        }

class OrderFilterForm(forms.Form):
    # Dropdown für den Bereich
    subarea = forms.ModelChoiceField(
        queryset=SubArea.objects.all(), 
        required=False, 
        label="Bereich",
        empty_label="Alle Bereiche"
    )
    
    # Dropdown für die Maschine
    machine = forms.ModelChoiceField(
        queryset=Machine.objects.all(), 
        required=False, 
        label="Maschine",
        empty_label="Alle Maschinen"
    )
    
    # Datum von...
    date_from = forms.DateField(
        required=False, 
        label="Von Datum",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # ...Datum bis
    date_to = forms.DateField(
        required=False, 
        label="Bis Datum",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )