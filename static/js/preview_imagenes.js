document.addEventListener("DOMContentLoaded", function() {
    // 1. Mostrar badges de errores en tabs + Auto-foco en error + Cambiar a tab con error
    const tabPanes = document.querySelectorAll('.tab-pane');
    let primerTabConError = null;
    let primerCampoConError = null;
    
    tabPanes.forEach(pane => {
        const invalidFields = pane.querySelectorAll('.is-invalid');
        if (invalidFields.length > 0) {
            const tabId = pane.getAttribute('id');
            const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);
            
            if (tabButton) {
                // Limpiar badge previo
                const existingBadge = tabButton.querySelector('.badge');
                if (existingBadge) {
                    existingBadge.remove();
                }
                
                // Añadir badge rojo (accesibilidad: aria-label)
                tabButton.innerHTML += ` <span class="badge bg-danger rounded-pill ms-2" aria-label="${invalidFields.length} errores">${invalidFields.length}</span>`;
                tabButton.classList.add('text-danger', 'fw-bold');

                // Guardar primer tab y campo para auto-foco
                if (!primerTabConError) {
                    primerTabConError = tabButton;
                    primerCampoConError = invalidFields[0];
                }
            }
        }
    });

    // Auto-navegar al primer error encontrado
    if (primerTabConError) {
        // Cambiar pestaña activa
        const tab = new bootstrap.Tab(primerTabConError);
        tab.show();
        
        // Auto-foco y scroll suave al campo problemático
        setTimeout(() => {
            primerCampoConError.focus();
            primerCampoConError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300); // Pequeño delay para dejar que la pestaña se abra
    }

    // 2. Previsualización de imágenes con estado vacío y transición
    const setupPreview = (inputId, imgId) => {
        const input = document.getElementById(inputId);
        const img = document.getElementById(imgId);
        
        if(input && img) {
            // Estilos iniciales para transición suave
            img.style.transition = "opacity 0.3s ease-in-out";
            
            // Crear contenedor de estado vacío si no tiene imagen
            if (img.getAttribute('src') === '#' || img.getAttribute('src') === '') {
                img.style.opacity = "0";
                img.style.display = "none";
                
                // Contenedor placeholder (estado vacío)
                const placeholder = document.createElement('div');
                placeholder.className = "d-flex align-items-center justify-content-center bg-light border rounded text-muted mb-2";
                placeholder.style.height = "200px";
                placeholder.style.width = "100%";
                placeholder.innerHTML = "<span><i class='bi bi-image fs-1'></i><br>Sin imagen</span>";
                placeholder.id = `${imgId}_placeholder`;
                img.parentNode.insertBefore(placeholder, img);
            } else {
                img.style.opacity = "1";
            }

            input.addEventListener('change', function() {
                const file = this.files[0];
                const placeholder = document.getElementById(`${imgId}_placeholder`);
                
                if (file) {
                    img.src = URL.createObjectURL(file);
                    img.style.display = 'block';
                    
                    // Crossfade
                    setTimeout(() => img.style.opacity = "1", 50);
                    if(placeholder) placeholder.style.display = 'none';
                } else {
                    // Reset si cancela selección
                    img.src = '';
                    img.style.opacity = "0";
                    setTimeout(() => img.style.display = 'none', 300);
                    if(placeholder) placeholder.style.display = 'flex';
                }
            });
        }
    };
    
    setupPreview('id_archivo_imagen', 'preview_principal');
    setupPreview('id_imagen_mapa', 'preview_mapa');
    setupPreview('id_imagen_aerea', 'preview_aerea');

    // 3. Prevenir doble submit y mostrar spinner (UI/UX Loading Button)
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                if (submitBtn.dataset.isSubmitting) {
                    event.preventDefault(); // Prevenir envíos adicionales
                    return;
                }
                
                // Marcar como enviando
                submitBtn.dataset.isSubmitting = 'true';
                
                // Mostrar spinner sin deshabilitar inmediatamente para no romper el POST nativo
                submitBtn.style.pointerEvents = 'none';
                submitBtn.style.opacity = '0.7';
                submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...`;
            }
        });
    });
});