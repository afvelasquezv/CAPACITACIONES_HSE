import db
import pandas as pd

# Obtener todos los cursos
cursos_df = db.obtener_cursos_por_cliente()
# Obtener todas las asignaciones
asignaciones = db.obtener_asignaciones()

# Contar asignaciones por curso
cursos_con_asignaciones = asignaciones['curso'].value_counts().reset_index()
cursos_con_asignaciones.columns = ['curso', 'num_asignaciones']

# Hacer merge para identificar cursos sin asignaciones
cursos_sin_asignaciones = cursos_df.merge(
    cursos_con_asignaciones,
    left_on='nombre',
    right_on='curso',
    how='left'
)

# Filtrar los que tienen 0 asignaciones (o NaN)
cursos_sin = cursos_sin_asignaciones[cursos_sin_asignaciones['num_asignaciones'].isna()]
print("Cursos sin asignaciones:")
print(cursos_sin[['nombre', 'cliente']])