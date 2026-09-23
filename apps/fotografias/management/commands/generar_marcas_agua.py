from django.core.management.base import BaseCommand
from apps.fotografias.models import Fotografia
from apps.fotografias.marcas_agua import generar_derivado_web


class Command(BaseCommand):
    help = "Genera las copias derivadas con marca de agua institucional para todas las fotografías existentes sin alterar los originales maestros."

    def add_arguments(self, parser):
        parser.add_argument(
            "--forzar",
            action="store_true",
            help="Fuerza la regeneración de la marca de agua incluso si el derivado ya existe en disco.",
        )

    def handle(self, *args, **options):
        forzar = options.get("forzar", False)
        fotografias = Fotografia.objects.filter(archivo_imagen__isnull=False).exclude(archivo_imagen="")
        total = fotografias.count()

        self.stdout.write(self.style.NOTICE(f"Iniciando procesamiento de {total} fotografías..."))
        procesadas = 0
        existentes = 0
        errores = 0

        for foto in fotografias:
            try:
                url = generar_derivado_web(foto, forzar=forzar)
                if url:
                    procesadas += 1
                else:
                    errores += 1
            except Exception as e:
                errores += 1
                self.stderr.write(f"Error procesando Fotografía {foto.id}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"[COMPLETADO] Derivados web generados exitosamente: {procesadas}/{total}. "
                f"Errores/omitidas: {errores}."
            )
        )
