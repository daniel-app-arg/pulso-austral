from rest_framework import serializers

from .models import Categoria, EventoTimeline, Fuente, Gobierno, Indicador, IndicadorValor, Medio, Noticia


class FuenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fuente
        fields = ['id', 'nombre', 'url']


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'color', 'icono', 'orden']


class IndicadorSerializer(serializers.ModelSerializer):
    fuente = FuenteSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(source='categoria', read_only=True)

    class Meta:
        model = Indicador
        fields = [
            'id', 'categoria_id', 'nombre', 'tipo', 'unidad', 'destacado',
            'actualizacion_automatica', 'polaridad', 'metodologia', 'fuente', 'orden',
        ]


class IndicadorValorSerializer(serializers.ModelSerializer):
    indicador_id = serializers.PrimaryKeyRelatedField(source='indicador', read_only=True)

    class Meta:
        model = IndicadorValor
        fields = ['id', 'indicador_id', 'fecha', 'granularidad', 'valor_numerico', 'valor_texto', 'delta_texto', 'trend']


class EventoTimelineSerializer(serializers.ModelSerializer):
    fuente = FuenteSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(source='categoria', read_only=True)

    class Meta:
        model = EventoTimeline
        fields = ['id', 'fecha', 'titulo', 'categoria_id', 'sentimiento', 'fuente']


class MedioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medio
        fields = ['id', 'nombre', 'url', 'tipo', 'orientacion', 'descripcion', 'orden']


class NoticiaSerializer(serializers.ModelSerializer):
    medio = MedioSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(source='categoria', read_only=True)

    class Meta:
        model = Noticia
        fields = ['id', 'categoria_id', 'kicker', 'fecha', 'titulo', 'bajada', 'cuerpo', 'url', 'medio', 'publicado']


class GobiernoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gobierno
        fields = ['id', 'presidente', 'partido', 'fecha_inicio', 'fecha_fin', 'color', 'orden']
