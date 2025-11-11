# 🔧 Configuración Manual en Streamlit Cloud

Si los dashboards aún no aparecen después de actualizar, sigue estos pasos en Streamlit Cloud:

## Opción 1: Re-desplegar la Aplicación (Recomendado)

1. Ve a: https://share.streamlit.io
2. Accede con tu cuenta GitHub
3. Busca tu aplicación "observatorio"
4. Haz clic en los **3 puntos (⋮)** en la esquina superior derecha
5. Selecciona **"Reboot app"** o **"Delete & redeploy"**
6. Espera a que se redepliegue (2-3 minutos)

## Opción 2: Verificar la Configuración de Despliegue

1. En Streamlit Cloud, ve a tu aplicación
2. Haz clic en **"Settings"** (engranaje)
3. Verifica que esté correctamente configurado:
   - **Repository**: Alejandrobr1/Observatorio
   - **Branch**: codigo_prueba
   - **Main file path**: app.py (IMPORTANTE)

Si dice `Dashboards/main_dashboard.py`, cambia a `app.py`

## Opción 3: Forzar actualización en el navegador

1. Abre la app en Streamlit Cloud
2. Presiona **Ctrl+Shift+R** (fuerza actualización del cache)
3. Si aún no funciona, intenta en incógnito (Ctrl+Shift+N)

## Verificación

Una vez desplegado, deberías ver:

✅ Página principal con 3 pestañas:
- 🏠 Inicio
- 📈 Dashboards
- 📥 Descargas

✅ En la pestaña "Dashboards" deberías ver los links organizados:
- Formación Sábados (2 opciones)
- Formación Docentes (1 opción)
- Formación Intensificación (2 opciones)

✅ En el sidebar izquierdo deberías ver todos los dashboards listados:
- 1_📊_Estudiantes_Sabados
- 2_👥_Sexo_Grado_Sabados
- 3_👥_Sexo_Grado_Docentes
- 4_⚡_Estudiantes_Intensificacion
- 5_📈_Sexo_Grado_Intensificacion

## Archivos Importantes

Los cambios realizados:

```
✅ app.py - Punto de entrada principal (NUEVO)
✅ streamlit.app - Archivo de configuración (NUEVO)
✅ .streamlit/config.toml - Configuración actualizada
✅ pages/ - Todos los dashboards multipage
```

## Si Aún No Funciona

Si después de hacer todo esto aún no ves los dashboards:

1. Verifica en GitHub que los archivos estén en `codigo_prueba` branch
2. Verifica que `app.py` esté en la raíz (no en carpeta)
3. Verifica que `pages/` esté en la raíz
4. Intenta eliminar y volver a crear el despliegue en Streamlit Cloud

## Contacto

Si necesitas más ayuda, verifica:
- Los logs en Streamlit Cloud (ícono de "info" en la esquina)
- Que todas las variables de entorno estén configuradas en Secrets
