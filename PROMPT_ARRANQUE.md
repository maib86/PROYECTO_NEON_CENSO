# Prompt de arranque para Claude Code

Pegar en Claude Code, abierto en `C:\PROYECTO_NEON_CENSO`, después de crear `.env`.

---

Estás arrancando en el repositorio PROYECTO_NEON_CENSO. Antes de hacer nada:

1. Leé `CLAUDE.md`, `ESPECIFICACION.md`, `docs/DECISIONES.md` y la sesión más reciente
   en `docs/sesiones/`. Confirmame en 5 líneas en qué fase estamos y cuál es el
   siguiente paso exacto según la bitácora.

2. Verificá el entorno sin exponer credenciales: existe `.env`; `psql --version`;
   `py --version`; `git status`. Si `git` no está inicializado, inicializalo y hacé
   el commit inicial con todo lo que hay (respetando `.gitignore`).

3. Con el agente `ingeniero-bd`, comprobá la conexión a Neon:
   `psql "$DATABASE_URL" -c "SELECT count(*) FROM mgn.deteccion_cambio;"` → esperado 1432.
   Si no da 1432, parás y me decís qué devolvió.

4. Proponeme el plan para ejecutar `sql/06_centroides_visita.sql`: qué bloques, qué
   verificaciones, y si vas a usar una rama de Neon o un `pg_dump --schema-only` previo.
   **No lo ejecutes todavía.** Esperá mi confirmación.

Reglas de esta sesión: nada destructivo sin mi "sí" explícito; cada cambio en la base con
su consulta de verificación y resultado literal; al cerrar, `documentador` escribe
`docs/sesiones/2026-10-13_sesion-01.md` y me da el resumen de 10 líneas para Claude web.
