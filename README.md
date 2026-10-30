# BoletaYa SAS: proyecto final (DynamoDB en AWS)

Repositorio del grupo. Cada integrante trabaja en su propia carpeta.

| Carpeta | Responsable | Contenido |
|---|---|---|
| `jacobo/` | Jacobo | Modelo de datos, capacidad, arquitectura |
| `david/` | David | Concurrencia, anexo, alta disponibilidad, estadio |
| `miguel/` | Miguel | Recuperación, licenciamiento, carta de evento |
| `juanpablo/` | Juan Pablo | Costos |
| `samuel/` | Samuel | Seguridad y cumplimiento |

## Reglas para no pisarnos

1. **Cada quien edita solo su carpeta.** Si algo de otra carpeta está mal, se lo dices a su dueño (en el chat o en un *issue* de GitHub), no lo cambias tú.
2. **Antes de empezar a trabajar:** `git pull`.
3. **Al terminar:** `git add .`, `git commit -m "qué cambió"`, `git push`.
4. Los mensajes del commit dicen qué cambió, por ejemplo: `david: escenario 3 del anexo`.
5. Los pendientes entre personas van como *issues* con el nombre de a quién le toca (por ejemplo "Jacobo: activar Streams en bya_tickets").

## Comandos que más se usan

```
git pull                      # traer lo que subieron los demás
git status                    # ver qué cambié yo
git add .                     # preparar mis cambios
git commit -m "mensaje"       # guardarlos con un mensaje
git push                      # subirlos
git log --oneline -- david/   # historial de una carpeta
```

Si `git push` dice que hay cambios nuevos en el servidor, se hace `git pull` primero y luego `git push` otra vez.
