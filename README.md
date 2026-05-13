# 🥗 Fitness Food - Aplicación Web

Una aplicación web moderna desarrollada con Flask para ayudar a mantener una alimentación saludable y equilibrada.

## Evidencias en ejecución
<img width="1920" height="965" alt="image" src="https://github.com/user-attachments/assets/bef80b8d-c871-4aed-a007-49f330be64cb" />
<img width="1920" height="983" alt="image" src="https://github.com/user-attachments/assets/adf11802-9f46-4243-afde-68044781e1cc" />
<img width="1920" height="969" alt="image" src="https://github.com/user-attachments/assets/15735179-dca8-45bf-934a-4f940174b055" />


## 📋 Características

- **Base de Datos SQLite**: gestión de usuarios, alimentos y registros de consumo
- **Carga de Datos desde JSON**: alimentos se importan desde `alimentos.json`
- **Gestión de Usuarios**: crear usuarios, cambiar objetivo fitness y eliminar usuarios
- **Base de Alimentos**: catálogo nutricional con datos desde MongoDB y SQLite
- **Registros de Consumo**: crear, editar y eliminar consumos de alimentos
- **Interfaz en Español**: toda la app está en español
- **Diseño Responsivo**: compatible con móviles, tablets y desktop
- **Bootstrap 5**: UI moderna y accesible
- **Interactividad**: botones y formularios con JavaScript para mejor experiencia

## 🚀 Estructura del Proyecto

```
Fitness Food/
│
├── app.py                 # Archivo principal de Flask con lógica de rutas y acceso a BD
├── alimentos.json         # Datos de alimentos en formato JSON
├── requirements.txt       # Dependencias de Python
├── README.md              # Este archivo
├── fitness_food.db        # Base de datos SQLite (se crea automáticamente)
│
├── templates/             # Plantillas HTML
│   ├── base.html          # Plantilla base con navegación
│   ├── index.html         # Página de inicio con estadísticas
│   ├── acerca.html        # Página "Acerca de"
│   ├── usuarios.html      # Gestión de usuarios
│   ├── alimentos.html     # Vista de alimentos y catalogación
│   └── registros.html     # Historial de consumo por usuario
│
└── static/                # Archivos estáticos
    ├── css/
    │   └── styles.css    # Estilos personalizados
    └── js/
        └── main.js       # JavaScript principal
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.8+**
- **Flask** - Framework web
- **SQLite3** - Base de datos local
- **Jinja2** - Motor de plantillas
- **PyMongo** - Conexión a MongoDB para datos de alimentos

### Frontend
- **HTML5** - Estructura
- **CSS3** - Estilos personalizados
- **JavaScript ES6+** - Interactividad
- **Bootstrap 5** - Framework CSS

## 📦 Instalación y Configuración

### Prerrequisitos
- Python 3.8 o superior
- pip
- MongoDB (para la carga de alimentos desde la colección si está configurado)

### Pasos para ejecutar la aplicación

1. **Clonar o descargar el proyecto**
   ```bash
   git clone <url-del-repositorio>
   cd "Fitness Food"
   ```

2. **Crear un entorno virtual (recomendado)**
   ```bash
   python -m venv venv

   # Activar el entorno virtual
   # En Windows:
   venv\Scripts\activate

   # En macOS/Linux:
   source venv/bin/activate
   ```

3. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

5. **Abrir en el navegador**
   - `http://127.0.0.1:5000`
   - O `http://localhost:5000`

## 🌐 Rutas Disponibles

- `/` - Página de inicio con estadísticas generales
- `/acerca` - Información sobre la aplicación
- `/usuarios` - Gestión de usuarios registrados
- `/alimentos` - Endpoint JSON con alimentos desde MongoDB
- `/alimentos/vista` - Interfaz web de la base de datos de alimentos
- `/registros/<usuario_id>` - Historial de registros por usuario
- `/api/alimentos-bd` - API JSON de alimentos para la UI
- `/api/usuarios` - API JSON de usuarios
- `/api/estadisticas` - API JSON con estadísticas avanzadas
- `/api/cargar-alimentos-json` - Recarga alimentos desde `alimentos.json`
- `/registro` (POST) - Crear un nuevo registro de consumo
- `/registro/<registro_id>` (PATCH) - Actualizar un registro existente
- `/registro/<registro_id>` (DELETE) - Eliminar un registro existente
- `/nuevo-usuario` (POST) - Crear un nuevo usuario
- `/editar-usuario/<usuario_id>` (POST) - Actualizar el objetivo fitness de un usuario
- `/eliminar-usuario` (POST) - Eliminar un usuario y sus registros asociados
- `/consumo` (GET) - Obtener calorías consumidas hoy por usuario
- `/recomendaciones` (GET) - Obtener recomendaciones según el objetivo y consumo

## 🗄️ Esquema de Base de Datos

### Tabla `usuarios`
- `id` (INTEGER, PRIMARY KEY)
- `nombre` (TEXT, UNIQUE, NOT NULL)
- `objetivo` (TEXT, CHECK: 'perder_peso', 'mantener', 'ganar_masa')
- `fecha_creacion` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### Tabla `alimentos`
- `id` (INTEGER, PRIMARY KEY)
- `nombre` (TEXT, UNIQUE, NOT NULL)
- `calorias_por_100g` (REAL, NOT NULL)
- `fecha_creacion` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### Tabla `registros`
- `id` (INTEGER, PRIMARY KEY)
- `usuario_id` (INTEGER, FOREIGN KEY → usuarios.id)
- `alimento_id` (INTEGER, FOREIGN KEY → alimentos.id)
- `gramos` (REAL, NOT NULL)
- `calorias` (REAL, NOT NULL)
- `fecha` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### Características de la Base de Datos
- ✅ Claves foráneas para integridad referencial
- ✅ Índices para consultas más rápidas
- ✅ Restricciones CHECK para validar datos
- ✅ Eliminación en cascada para mantener consistencia

## 📄 Gestión de Datos con JSON

### Archivo `alimentos.json`
Contiene la lista de alimentos en formato JSON con esta estructura:
```json
{
  "alimentos": [
    {
      "id": 1,
      "nombre": "Nombre del alimento",
      "calorias_por_100g": 123.0
    }
  ]
}
```

### Carga Automática
- En la primera ejecución, se inicializa la colección de MongoDB y se sincroniza con SQLite
- Si los datos ya existen, no se duplican
- Para recargar manualmente, usa `POST /api/cargar-alimentos-json`

### Personalizar Alimentos
1. Edita `alimentos.json`
2. Reinicia la aplicación
3. Si ya había datos, recarga con `/api/cargar-alimentos-json`

## 🎨 Personalización

### Colores principales
- Verde principal: `#198754`
- Verde claro: `#d1e7dd`
- Verde oscuro: `#146c43`

### Agregar nuevas páginas
1. Crea la plantilla en `templates/`
2. Define la ruta en `app.py`
3. Actualiza la navegación en `templates/base.html`

## 📱 Responsive

La app está diseñada para adaptarse a pantallas de:
- Desktop
- Tablet
- Móvil

## 🤝 Contribuir

1. Haz fork del proyecto
2. Crea una rama (`git checkout -b nueva-funcion`)
3. Haz commit (`git commit -am 'Agregar nueva función'`)
4. Haz push (`git push origin nueva-funcion`)
5. Abre un Pull Request

## 📝 Notas de Desarrollo

- El modo debug puede estar habilitado en `app.py`
- Los archivos estáticos se sirven desde `/static`
- Las plantillas usan herencia Jinja2

## 🔧 Solución de Problemas

### No module named flask
```bash
pip install flask
```

### Puerto en uso
```python
app.run(debug=True, host='127.0.0.1', port=5001)
```

### Problemas con archivos estáticos
Asegúrate de que la carpeta `static` esté en la raíz del proyecto.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 👥 Autor

Desarrollado con ❤️ para la comunidad fitness y de alimentación saludable.

---

¡Disfruta creando tu aplicación de alimentación saludable! 🥗✨
