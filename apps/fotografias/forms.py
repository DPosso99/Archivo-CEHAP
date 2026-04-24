from django import forms
from .models import Fotografia
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from crispy_forms.bootstrap import TabHolder, Tab


class FotografiaForm(forms.ModelForm):
    relaciones = forms.MultipleChoiceField(
        choices=Fotografia.RELACIONES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Relaciones"
    )
    uso_imagen = forms.MultipleChoiceField(
        choices=Fotografia.USO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Uso imagen"
    )

    class Meta:
        model = Fotografia
        fields = "__all__"
        exclude = (
            "registrado_por",
            "fecha_registro",
            "fecha_actualizacion",
        )  # Campos automáticos

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    "Imagen",
                    Row(
                        Column("titulo", css_class="col-md-6"),
                        Column("codigo", css_class="col-md-6"),
                    ),
                    Row(
                        Column("idioma_original", css_class="col-md-4"),
                        Column("coleccion", css_class="col-md-4"),
                        Column("estado", css_class="col-md-4"),
                    ),
                    "archivo_imagen",
                    HTML('<img id="preview_principal" class="img-fluid mt-2 mb-4" style="max-height: 300px; display: none;" />'),
                    "funcion_imagen",
                    "explicacion_funcion",
                    HTML("<p><strong>Consideraciones del usuario y Aplicación imagen</strong></p>"),
                    Row(
                        Column("acuerdo_contexto", css_class="col-md-3"),
                        Column("adapta_lenguaje", css_class="col-md-3"),
                        Column("respeta_esquemas_culturales", css_class="col-md-3"),
                        Column("rigor_cientifico", css_class="col-md-3"),
                    ),
                    Row(
                        Column("simplicidad_imagen", css_class="col-md-4"),
                        Column("legibilidad", css_class="col-md-4"),
                        Column("elementos_distraccion", css_class="col-md-4"),
                    ),
                    HTML("<p><strong>Clasificación académica</strong></p>"),
                    Row(
                        Column("disciplina", css_class="col-md-6"),
                        Column("subdisciplina", css_class="col-md-6"),
                    ),
                    "conceptos_imagen",
                    "relacion_documental",
                    css_id="tab-imagen",
                ),
                Tab(
                    "Descripción Técnica y Origen",
                    "descripcion_general",
                    HTML("<p><strong>Formato</strong></p>"),
                    Row(
                        Column("formato_original", css_class="col-md-6"),
                        Column("formato_actual", css_class="col-md-6"),
                    ),
                    HTML("<p><strong>Autoría y derechos</strong></p>"),
                    Row(
                        Column("autor", css_class="col-md-6"),
                        Column("entidad_responsable", css_class="col-md-6"),
                    ),
                    "derechos_propiedad_intelectual",
                    "condiciones_uso",
                    HTML("<p><strong>Dimensiones físicas</strong></p>"),
                    Row(
                        Column("ancho_fisico_px", css_class="col-md-6"),
                        Column("alto_fisico_px", css_class="col-md-6"),
                    ),
                    HTML("<p><strong>Dimensiones digitales y Color</strong></p>"),
                    Row(
                        Column("ancho_pixeles", css_class="col-md-6"),
                        Column("alto_pixeles", css_class="col-md-6"),
                    ),
                    Row(
                        Column("resolucion_horizontal", css_class="col-md-4"),
                        Column("resolucion_vertical", css_class="col-md-4"),
                        Column("unidad_resolucion", css_class="col-md-4"),
                    ),
                    Row(
                        Column("profundidad_bits", css_class="col-md-6"),
                        Column("modelo_color", css_class="col-md-6"),
                    ),
                    HTML("<p><strong>Producción y publicación</strong></p>"),
                    Row(
                        Column("fecha_produccion", css_class="col-md-6"),
                        Column("lugar_produccion", css_class="col-md-6"),
                    ),
                    "publicacion_imagen",
                    Row(
                        Column("fecha_publicacion", css_class="col-md-6"),
                        Column("lugar_publicacion", css_class="col-md-6"),
                    ),
                    HTML("<p><strong>Versiones y características</strong></p>"),
                    Row(
                        Column("primera_version_imagen", css_class="col-md-6"),
                        Column("ultima_modificacion_imagen", css_class="col-md-6"),
                    ),
                    "caracteristicas",
                    "adaptacion_formato",
                    "posibilidad_adaptacion",
                    "anotaciones",
                    css_id="tab-tecnico-origen",
                ),
                Tab(
                    "Descripción Perceptual",
                    "tipo_imagen",
                    HTML("<p><strong>Contexto de la imagen</strong></p>"),
                    "contexto_fondo",
                    "contexto_figura",
                    "elementos_visuales_importantes",
                    "percepcion_sin_descripcion",
                    "percepcion_con_descripcion",
                    "objetivo_imagen",
                    HTML("<p><strong>Relaciones e Imagen de una imagen</strong></p>"),
                    "relaciones",
                    Row(
                        Column("porcentaje_distorsion", css_class="col-md-6"),
                        Column("porcentaje_pixelacion", css_class="col-md-6"),
                    ),
                    "uso_imagen",
                    css_id="tab-perceptual",
                ),
                Tab(
                    "Ubicación",
                    "ubicacion_web",
                    "ubicacion_archivo",
                    "imagen_mapa",
                    HTML('<img id="preview_mapa" class="img-fluid mt-2 mb-4" style="max-height: 300px; display: none;" />'),
                    "imagen_propia",
                    HTML('<img id="preview_propia" class="img-fluid mt-2 mb-4" style="max-height: 300px; display: none;" />'),
                    "descripcion_imagen_propia",
                    css_id="tab-ubicacion",
                ),
            ),
            Submit("submit", "Guardar Ficha", css_class="btn btn-success mt-4 w-100"),
        )

