#!/bin/bash
cd '/home/dposso/code/Plataforma_Unidad_Documentación'
nohup python3 manage.py runserver 0.0.0.0:8000 > django_server.log 2>&1 &
echo "Servidor de Django iniciado exitosamente!"