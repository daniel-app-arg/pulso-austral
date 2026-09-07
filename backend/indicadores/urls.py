from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import (
    CategoriaViewSet,
    DestacadosView,
    EventoTimelineViewSet,
    FuenteViewSet,
    GobiernoResumenView,
    GobiernoViewSet,
    IndicadorValorViewSet,
    IndicadorViewSet,
    MedioViewSet,
    NoticiaViewSet,
    PulsoIndexView,
    TimelineResumenMensualView,
    UltimosValoresView,
)

router = DefaultRouter()
router.register('categorias', CategoriaViewSet, basename='categoria')
router.register('fuentes', FuenteViewSet, basename='fuente')
router.register('indicadores', IndicadorViewSet, basename='indicador')
router.register('indicador-valores', IndicadorValorViewSet, basename='indicador-valor')
router.register('eventos-timeline', EventoTimelineViewSet, basename='evento-timeline')
router.register('noticias', NoticiaViewSet, basename='noticia')
router.register('medios', MedioViewSet, basename='medio')
router.register('gobiernos', GobiernoViewSet, basename='gobierno')

urlpatterns = router.urls + [
    path('destacados/', DestacadosView.as_view(), name='destacados'),
    path('ultimos-valores/', UltimosValoresView.as_view(), name='ultimos-valores'),
    path('timeline-resumen-mensual/', TimelineResumenMensualView.as_view(), name='timeline-resumen-mensual'),
    path('gobiernos/<slug:gobierno_id>/resumen/', GobiernoResumenView.as_view(), name='gobierno-resumen'),
    path('pulso-index/', PulsoIndexView.as_view(), name='pulso-index'),
]
