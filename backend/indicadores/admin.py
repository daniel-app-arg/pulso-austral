from django.contrib import admin

from .models import Categoria, EventoTimeline, Fuente, Gobierno, Indicador, IndicadorValor, Medio, Noticia, PulsoIndexSnapshot


@admin.register(Fuente)
class FuenteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'url']
    search_fields = ['nombre']


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'color', 'icono', 'orden']
    ordering = ['orden']


class IndicadorValorInline(admin.TabularInline):
    model = IndicadorValor
    extra = 0
    ordering = ['-fecha']


@admin.register(Indicador)
class IndicadorAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'categoria', 'tipo', 'unidad', 'destacado', 'actualizacion_automatica', 'polaridad', 'fuente', 'orden']
    list_filter = ['categoria', 'tipo', 'destacado', 'actualizacion_automatica', 'polaridad']
    search_fields = ['id', 'nombre']
    inlines = [IndicadorValorInline]


@admin.register(IndicadorValor)
class IndicadorValorAdmin(admin.ModelAdmin):
    list_display = ['indicador', 'fecha', 'granularidad', 'valor_numerico', 'valor_texto', 'trend']
    list_filter = ['granularidad', 'trend', 'indicador__categoria']
    search_fields = ['indicador__id', 'indicador__nombre']
    date_hierarchy = 'fecha'
    autocomplete_fields = ['indicador']


@admin.register(EventoTimeline)
class EventoTimelineAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'titulo', 'categoria', 'sentimiento', 'fuente']
    list_filter = ['sentimiento', 'categoria']
    search_fields = ['titulo']
    date_hierarchy = 'fecha'


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'titulo', 'categoria', 'medio', 'publicado']
    list_filter = ['categoria', 'medio', 'publicado']
    search_fields = ['titulo', 'bajada']
    date_hierarchy = 'fecha'


@admin.register(Medio)
class MedioAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'tipo', 'orientacion', 'orden']
    list_filter = ['tipo', 'orientacion']
    search_fields = ['id', 'nombre']
    ordering = ['orden']


@admin.register(Gobierno)
class GobiernoAdmin(admin.ModelAdmin):
    list_display = ['id', 'presidente', 'partido', 'fecha_inicio', 'fecha_fin', 'orden']
    ordering = ['orden']


@admin.register(PulsoIndexSnapshot)
class PulsoIndexSnapshotAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'score', 'mejorando', 'empeorando', 'sin_cambio', 'total']
    date_hierarchy = 'fecha'
    ordering = ['-fecha']
