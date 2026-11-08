# Python-WP

Script en Python para monitorear sitios WordPress y detectar cuáles no responden o llevan más de 24 horas sin publicar una nota.

## Descripción

`revisar_wp.py` recibe una lista de URLs, consulta la API REST de WordPress (`/wp-json/wp/v2/posts`) y verifica dos cosas por cada sitio:

1. Que el sitio responda.
2. Que su última entrada publicada tenga menos de 24 horas de antigüedad (según `date_gmt`).

Al final imprime **solo los sitios que fallan**, junto con el motivo. El código de salida es `1` si hay fallos, lo que permite usarlo en cron, CI o tareas de monitoreo.

## Requisitos

- Python 3.8 o superior (usa el operador walrus en `main`).
- Sin dependencias externas: solo la librería estándar.
- La API REST del sitio debe estar accesible. Algunos WordPress la deshabilitan o la protegen.

## Estructura del proyecto

```
.
├── revisar_wp.py   # script principal
├── sitios.txt      # lista de sitios (la creas tú)
├── .gitignore
└── README.md
```

## Uso

1. Crea un archivo `sitios.txt` con una URL por línea. Se aceptan URLs con o sin `https://`; las líneas vacías y las que empiezan con `#` se ignoran.

   ```text
   https://wordpress.org/news/
   mi-sitio.com
   # https://sitio-deshabilitado.com
   ```

2. Ejecuta el script:

   ```bash
   python3 revisar_wp.py sitios.txt
   ```

3. Ejemplo de salida:

   ```text
   1/3 OK; 2 con fallas

   Fallan:
   - https://example.com: HTTP 404
   - https://otro-sitio.com: ultima nota hace 30.2 h
   ```

### Códigos de salida

| Código | Significado |
| ------ | ----------- |
| `0`    | Todos los sitios pasaron la revisión. |
| `1`    | Hay al menos un sitio con fallas, o faltó el argumento `sitios.txt`. |

## Criterios de fallo

Un sitio se reporta como fallido cuando:

- No responde: error de DNS, conexión rechazada, timeout (10 s) u otro error de red.
- Devuelve un código HTTP de error (404, 403, 500, etc.).
- La respuesta de la API no es JSON válido o no tiene los campos esperados.
- No tiene entradas publicadas.
- Su última entrada tiene 24 horas o más de antigüedad.

## Configuración

Los parámetros principales están al inicio de `revisar_wp.py`:

```python
MAX_HORAS, TIMEOUT = 24, 10
UA = "Mozilla/5.0 (compatible; WP-check/1.0)"
```

- `MAX_HORAS`: antigüedad máxima permitida para la última nota.
- `TIMEOUT`: tiempo máximo de espera por sitio, en segundos.
- `UA`: User-Agent enviado en las peticiones (algunos sitios bloquean el de Python por defecto).

## Cómo funciona

1. Normaliza la URL y arma `{sitio}/wp-json/wp/v2/posts?per_page=1&_fields=date_gmt`.
2. Hace una petición GET siguiendo redirecciones y con timeout.
3. Toma la fecha `date_gmt` de la entrada más reciente (la API devuelve por defecto la más nueva primero).
4. Calcula la diferencia contra la hora actual en UTC y la compara con `MAX_HORAS`.

## Limitaciones

- Los sitios con la API REST deshabilitada, protegida o modificada se reportan como fallo.
- Depende de que la API exponga `date_gmt`; si un plugin o tema la altera, el sitio puede aparecer como "API inválida".
- No verifica que el sitio sea WordPress más allá de que el endpoint responda.
- Las peticiones son secuenciales. Para listas muy grandes conviene paralelizar con `concurrent.futures`.

## Notas sobre `.gitignore`

El directorio de caché de Python se llama `__pycache__` (no `__pychache__`). El `.gitignore` incluido lo excluye junto con `*.pyc`, entornos virtuales, archivos `.env` y configuraciones de editores. Si tu lista de sitios es privada, descomenta la línea `sitios.txt` para no versionarla.
