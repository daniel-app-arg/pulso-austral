"""
Calcula el índice general de hoy (ver indicadores/services/pulso_index.py)
y guarda una foto en PulsoIndexSnapshot — así queda una serie histórica
real, no solo un número recalculado en cada request.

Pensado para correrse una vez por día, después de `fetch_datos_reales`
(que es lo que mueve el `trend` de los indicadores reales; los
ilustrativos no cambian de un día para el otro, así que recalcular todos
los días solo tiene sentido una vez que haya un scheduler — hasta
entonces, correrlo a mano cuando se quiera una foto nueva).

Uso:
    python manage.py compute_pulso_index
"""

from datetime import date

from django.core.management.base import BaseCommand

from indicadores.models import PulsoIndexSnapshot
from indicadores.services import pulso_index


class Command(BaseCommand):
    help = 'Calcula el índice general de hoy y guarda una foto en PulsoIndexSnapshot.'

    def handle(self, *args, **options):
        resultado = pulso_index.calcular()

        if resultado['total'] == 0:
            self.stdout.write(self.style.WARNING(
                'No hay indicadores con polaridad definida y datos cargados — nada para calcular '
                '(¿corriste seed_pulso_austral después de agregar el campo polaridad?).'
            ))
            return

        snapshot, creado = PulsoIndexSnapshot.objects.update_or_create(
            fecha=date.today(),
            defaults={
                'score': resultado['score'],
                'mejorando': resultado['mejorando'],
                'empeorando': resultado['empeorando'],
                'sin_cambio': resultado['sin_cambio'],
                'total': resultado['total'],
            },
        )
        verbo = 'creada' if creado else 'actualizada'
        self.stdout.write(self.style.SUCCESS(
            f'Foto {verbo} para {snapshot.fecha}: score {snapshot.score} '
            f'({snapshot.mejorando} mejorando, {snapshot.empeorando} empeorando, '
            f'{snapshot.sin_cambio} sin cambio, de {snapshot.total} indicadores considerados).'
        ))
