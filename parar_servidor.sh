#!/bin/bash
kill -9 $(lsof -ti :8000) 2>/dev/null && echo "Servidor detenido en puerto 8000" || echo "No hay servidor corriendo en puerto 8000"
