"""
Modelos de Pulso Austral — equivalente en Django de pulso-austral-schema.sql.

Seis tablas: Fuente, Categoria, Indicador, IndicadorValor (serie de tiempo),
EventoTimeline, Noticia. Se mantienen los mismos nombres de slug/id que en el
SQL original y en el mock del artifact (pulso-austral.jsx) para que la
migración de datos y el mapeo del frontend sean directos.
"""

from django.db import models


class Fuente(models.Model):
    """Un organismo/medio (INDEC, BCRA, ...), reutilizado por varios indicadores,
    eventos y noticias."""

    nombre = models.CharField(max_length=200)
    url = models.URLField(max_length=500)

    class Meta:
        verbose_name = 'fuente'
        verbose_name_plural = 'fuentes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    """Las 9 secciones del dashboard."""

    id = models.SlugField(primary_key=True, max_length=50)  # ej: 'macro', 'empleo'
    nombre = models.CharField(max_length=100)
    color = models.CharField(max_length=7)  # hex, identidad visual
    icono = models.CharField(max_length=50, blank=True)  # nombre de ícono lucide-react
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['orden']

    def __str__(self):
        return self.nombre


class Indicador(models.Model):
    """Catálogo/metadata de cada indicador (no los valores en sí)."""

    TIPO_CHOICES = [
        ('numerico', 'Numérico'),
        ('cualitativo', 'Cualitativo'),
    ]

    POLARIDAD_CHOICES = [
        ('positivo', 'Subir es mejorar'),
        ('negativo', 'Subir es empeorar'),
        ('neutral', 'Sin dirección de consenso — excluido del índice general'),
    ]

    id = models.SlugField(primary_key=True, max_length=100)  # ej: 'inflacion_interanual'
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='indicadores')
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    unidad = models.CharField(max_length=20, blank=True)  # '%', 'pb', 'US$ B', '$'...
    destacado = models.BooleanField(default=False)  # va en el header (dólar, Merval)
    fuente = models.ForeignKey(Fuente, on_delete=models.SET_NULL, null=True, blank=True, related_name='indicadores')
    metodologia = models.TextField(
        blank=True,
        help_text='Cómo se mide/calcula este indicador — para la sección de glosario del sitio.',
    )
    actualizacion_automatica = models.BooleanField(
        default=False,
        help_text=(
            'True si el comando fetch_datos_reales trae este indicador de una fuente '
            'externa real (BCRA, datos.gob.ar, dolarapi.com). False si el valor es '
            'ilustrativo o se carga a mano desde el admin. No es solo informativo: '
            'antes esta distinción vivía únicamente como una lista de IDs hardcodeada '
            'dentro de fetch_datos_reales.py — este campo la hace explícita y '
            'consultable (acá, en el admin, y en la API) en vez de tener que leer el '
            'código para saber qué indicador es "de verdad".'
        ),
    )
    polaridad = models.CharField(
        max_length=10, choices=POLARIDAD_CHOICES, default='neutral',
        help_text=(
            'Si subir este indicador es una mejora o un empeoramiento del país — la '
            'base del índice general (ver services/pulso_index.py). "neutral" para '
            'todo lo ideológicamente contestado (dólar, gasto militar, aprobación de '
            'gobierno, etc.): esos quedan afuera del índice a propósito, no por '
            'descuido. Se fija en seed_pulso_austral.py (POLARIDADES), igual que '
            'actualizacion_automatica.'
        ),
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'indicador'
        verbose_name_plural = 'indicadores'
        ordering = ['categoria', 'orden']

    def __str__(self):
        return self.nombre


class IndicadorValor(models.Model):
    """La serie de tiempo: un renglón por indicador+fecha+granularidad. Alimenta
    tarjetas, sparklines y gráficos expandidos."""

    GRANULARIDAD_CHOICES = [
        ('dia', 'Día'),
        ('semana', 'Semana'),
        ('mes', 'Mes'),
        ('anio', 'Año'),
    ]
    TREND_CHOICES = [
        ('up', 'Sube'),
        ('down', 'Baja'),
        ('flat', 'Sin cambios'),
    ]

    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE, related_name='valores')
    fecha = models.DateField()
    granularidad = models.CharField(max_length=10, choices=GRANULARIDAD_CHOICES)
    valor_numerico = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    valor_texto = models.CharField(max_length=200, blank=True)  # para cualitativos
    delta_texto = models.CharField(max_length=100, blank=True)  # ya formateado
    trend = models.CharField(max_length=10, choices=TREND_CHOICES, blank=True)

    class Meta:
        verbose_name = 'valor de indicador'
        verbose_name_plural = 'valores de indicadores'
        constraints = [
            models.UniqueConstraint(fields=['indicador', 'fecha', 'granularidad'], name='uq_indicador_fecha_gran'),
        ]
        indexes = [
            models.Index(fields=['indicador', 'granularidad', '-fecha'], name='idx_valores_ind_gran_fecha'),
        ]
        ordering = ['indicador', 'granularidad', 'fecha']

    def __str__(self):
        valor = self.valor_numerico if self.valor_numerico is not None else self.valor_texto
        return f'{self.indicador_id} · {self.fecha} ({self.granularidad}) = {valor}'


class EventoTimeline(models.Model):
    """La línea de tiempo con sentimiento positivo/negativo/neutral."""

    SENTIMIENTO_CHOICES = [
        ('positivo', 'Positivo'),
        ('negativo', 'Negativo'),
        ('neutral', 'Neutral'),
    ]

    fecha = models.DateField()
    titulo = models.CharField(max_length=300)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='eventos_timeline')
    sentimiento = models.CharField(max_length=10, choices=SENTIMIENTO_CHOICES)
    fuente = models.ForeignKey(Fuente, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos_timeline')

    class Meta:
        verbose_name = 'evento de línea de tiempo'
        verbose_name_plural = 'eventos de línea de tiempo'
        indexes = [
            models.Index(fields=['-fecha'], name='idx_eventos_fecha'),
        ]
        ordering = ['-fecha']

    def __str__(self):
        return self.titulo


class Noticia(models.Model):
    """El blog, filtrable por categoría igual que en el artifact.

    Diseñada para sobrevivir a que el link se rompa: `titulo` y `bajada`
    son la fuente de verdad persistida acá mismo, no un espejo de lo que
    dice `url` en este momento — si el diario borra o muda la nota, esos
    dos campos siguen intactos y `url` simplemente deja de resolver (se
    puede dejar así, o limpiar a mano desde el admin, pero no hace falta
    borrar la noticia)."""

    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='noticias')
    kicker = models.CharField(max_length=100, blank=True)
    fecha = models.DateField()
    titulo = models.CharField(max_length=300)
    bajada = models.TextField(blank=True, help_text='Resumen breve y persistente — no depende de que `url` siga viva.')
    cuerpo = models.TextField(blank=True)  # nota completa, si el blog crece más allá de la bajada
    url = models.URLField(max_length=1000, blank=True, help_text='Link a la nota original. Puede quedar roto con el tiempo — titulo/bajada no dependen de esto.')
    medio = models.ForeignKey('Medio', on_delete=models.SET_NULL, null=True, blank=True, related_name='noticias')
    publicado = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'noticia'
        verbose_name_plural = 'noticias'
        indexes = [
            models.Index(fields=['categoria', '-fecha'], name='idx_noticias_cat_fecha'),
        ]
        ordering = ['-fecha']

    def __str__(self):
        return self.titulo


class Medio(models.Model):
    """Directorio editorial de medios de comunicación, con una
    caracterización de referencia de su orientación. Es contenido curado
    por el sitio (editable desde el admin), no una medición objetiva —
    pensado como el equivalente a los "media bias charts" que usan sitios
    como AllSides o Ad Fontes Media, adaptado a medios argentinos."""

    ORIENTACION_CHOICES = [
        ('izquierda', 'Izquierda'),
        ('centro_izquierda', 'Centro-izquierda'),
        ('centro', 'Centro'),
        ('centro_derecha', 'Centro-derecha'),
        ('derecha', 'Derecha'),
    ]
    TIPO_CHOICES = [
        ('diario', 'Diario / digital de noticias'),
        ('agencia', 'Agencia de noticias'),
        ('tv', 'Televisión'),
        ('radio', 'Radio'),
        ('revista', 'Revista'),
        ('factchecking', 'Verificación de datos'),
    ]

    id = models.SlugField(primary_key=True, max_length=50)
    nombre = models.CharField(max_length=150)
    url = models.URLField(max_length=500)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    orientacion = models.CharField(max_length=20, choices=ORIENTACION_CHOICES)
    descripcion = models.TextField(
        help_text='Breve justificación de la caracterización — de dónde viene, no solo la etiqueta.'
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'medio de comunicación'
        verbose_name_plural = 'medios de comunicación'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class Gobierno(models.Model):
    """Un período presidencial (4 años, salvo excepciones), para poder
    resumir todos los indicadores dentro de esa ventana de tiempo."""

    id = models.SlugField(primary_key=True, max_length=50)  # ej: 'milei-2023'
    presidente = models.CharField(max_length=150)
    partido = models.CharField(max_length=150, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)  # null = en curso
    color = models.CharField(max_length=7, blank=True)  # hex, para la UI
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'gobierno'
        verbose_name_plural = 'gobiernos'
        ordering = ['orden']

    def __str__(self):
        return f'{self.presidente} ({self.fecha_inicio.year}-{self.fecha_fin.year if self.fecha_fin else "actualidad"})'


class PulsoIndexSnapshot(models.Model):
    """Una foto del índice general del país en una fecha: qué porcentaje de
    los indicadores con polaridad definida mejoró/empeoró/quedó igual desde
    su punto anterior, resumido en un score 0-100 (50 = neutro, tantos
    mejorando como empeorando). Se calcula con
    `indicadores.services.pulso_index.calcular()` y se guarda con el
    comando `compute_pulso_index` — no se recalcula en cada request a la
    API, así que esta tabla es la serie histórica real del índice (una fila
    por día que se corrió el comando), útil para mostrar su propia
    tendencia con el mismo componente de gráfico que ya tienen los
    indicadores comunes."""

    fecha = models.DateField(unique=True)
    score = models.DecimalField(max_digits=5, decimal_places=1)  # 0-100
    mejorando = models.PositiveIntegerField()
    empeorando = models.PositiveIntegerField()
    sin_cambio = models.PositiveIntegerField()
    total = models.PositiveIntegerField()  # mejorando + empeorando + sin_cambio

    class Meta:
        verbose_name = 'foto del índice general'
        verbose_name_plural = 'fotos del índice general'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.fecha}: {self.score} ({self.mejorando}↑ {self.empeorando}↓ {self.sin_cambio}=)'
