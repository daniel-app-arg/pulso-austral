# Desplegar Pulso Austral — guía paso a paso

Stack: **Vercel** (frontend) + **Render** (backend) + **Neon** (base, ya
configurada) + **Cloudflare** (DNS del dominio `pulsoaustral.com.ar`).
Los tres primeros tienen plan gratis sin pedir tarjeta.

El código ya está listo (settings de producción, `render.yaml`, git
inicializado con el primer commit). Lo que sigue son pasos que solo vos
podés hacer — crear cuentas, conectar repos, cargar el dominio — no algo
que yo pueda ejecutar por vos.

## 1. Subir el código a GitHub

1. Andá a **https://github.com/new** y creá un repositorio (nombre
   sugerido: `pulso-austral`). Dejalo **privado** si no querés que el
   código sea público, o público si no te importa — no cambia nada del
   despliegue. **No** marques "Initialize with README" (ya tenemos commits).
2. GitHub te va a mostrar los comandos para un repo existente. Van a ser
   algo así (reemplazá `TU-USUARIO`):
   ```bash
   git remote add origin https://github.com/TU-USUARIO/pulso-austral.git
   git push -u origin main
   ```
   Pegámelos (o el link del repo vacío) y los corro yo — o corrélos vos
   mismo desde una terminal en `C:\Users\danie\Pulso Austral`.

## 2. Backend en Render

1. Creá cuenta en **https://render.com** (podés entrar con GitHub directamente).
2. **New +** → **Blueprint** → conectá tu cuenta de GitHub → elegí el
   repo `pulso-austral`. Render va a leer `render.yaml` solo y proponer
   el servicio `pulso-austral-api`.
3. Antes de confirmar (o justo después, en **Environment**), completá
   estas 4 variables — son las únicas que Render no puede adivinar:

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | El mismo connection string de Neon que ya tenés en `backend/.env` (`postgresql://...neon.tech/...`) |
   | `ALLOWED_HOSTS` | `pulso-austral-api.onrender.com,api.pulsoaustral.com.ar` |
   | `CORS_ALLOWED_ORIGINS` | `https://pulsoaustral.com.ar,https://www.pulsoaustral.com.ar` |
   | `CSRF_TRUSTED_ORIGINS` | `https://pulso-austral-api.onrender.com,https://api.pulsoaustral.com.ar` |

   `SECRET_KEY` se genera sola (`generateValue: true` en el blueprint) — no
   toques esa.
4. **Apply** / **Create Web Service**. El primer deploy tarda unos
   minutos (instala dependencias, corre `collectstatic` y `migrate`).
5. Cuando termine, en **Shell** (pestaña del servicio en Render) corré
   una vez, en este orden:
   ```bash
   python manage.py seed_pulso_austral
   python manage.py seed_editorial
   python manage.py seed_noticias_reales
   python manage.py fetch_datos_reales
   python manage.py compute_pulso_index
   python manage.py createsuperuser
   ```
   (Los mismos comandos que ya corrimos contra Neon en local — como usan
   la misma base, en rigor los datos ya están ahí. Solo hace falta
   `createsuperuser` si querés un usuario de admin propio para producción
   en vez de reusar `admin`/`pulsoaustral2026`, que te recomiendo cambiar.)
6. Anotá la URL que te da Render (`https://pulso-austral-api.onrender.com`)
   — la necesitás en el paso 3.

**Sobre el plan free**: el servicio "duerme" después de 15 minutos sin
tráfico. La primera visita después de estar dormido tarda ~30-50 segundos
en responder (Render tiene que arrancar el contenedor de nuevo). Es
normal, no es un error.

## 3. Frontend en Vercel

1. Creá cuenta en **https://vercel.com** (con GitHub).
2. **Add New** → **Project** → importá el repo `pulso-austral`.
3. En la configuración del proyecto (antes de deployar):
   - **Root Directory**: `frontend` (el repo es un monorepo, Vercel tiene
     que saber que el Next.js está en esa subcarpeta).
   - **Environment Variables** → agregá:
     | Variable | Valor |
     |---|---|
     | `API_BASE_URL` | `https://pulso-austral-api.onrender.com/api` (la URL de Render + `/api`) |
4. **Deploy**. Vercel te da una URL tipo `pulso-austral.vercel.app` — ya
   andando, sin dominio propio todavía.

## 4. Dominio: Cloudflare + pulsoaustral.com.ar

1. Creá cuenta en **https://cloudflare.com** (gratis).
2. **Add a site** → escribí `pulsoaustral.com.ar` → elegí el plan **Free**.
3. Cloudflare te va a dar 2 nameservers (algo como `xxx.ns.cloudflare.com`).
   Andá a donde registraste el dominio (NIC Argentina,
   **https://nic.ar**, u otro registrador) y cambiá los nameservers del
   dominio a esos dos. Este cambio puede tardar unas horas en propagarse.
4. Ya en Cloudflare, sección **DNS**, agregá estos registros:

   | Tipo | Nombre | Destino | Proxy |
   |---|---|---|---|
   | CNAME | `@` (o `pulsoaustral.com.ar`) | `cname.vercel-dns.com` | 🔘 **DNS only** (nube gris) |
   | CNAME | `www` | `cname.vercel-dns.com` | 🔘 **DNS only** (nube gris) |
   | CNAME | `api` | `pulso-austral-api.onrender.com` | 🟠 Proxied (nube naranja) está bien acá |

   Importante: los dos registros que apuntan a Vercel van con el **proxy
   apagado** (nube gris, "DNS only") — Vercel necesita ser el origen
   directo, no funciona bien detrás de otro proxy/CDN delante. El de
   Render sí puede ir proxiado por Cloudflare sin problema.

   (Si Cloudflare no te deja un CNAME en `@`/la raíz por ser el apex del
   dominio, usá el registro tipo **CNAME flattening** que Cloudflare hace
   automático, o seguí las instrucciones que da Vercel mismo al agregar
   el dominio en el paso siguiente — a veces piden un registro `A` a una
   IP fija de Vercel en vez de CNAME en el apex.)

5. Volvé a **Vercel** → tu proyecto → **Settings → Domains** → agregá
   `pulsoaustral.com.ar` y `www.pulsoaustral.com.ar`. Vercel verifica el
   DNS solo (puede tardar un rato) y emite el certificado HTTPS.
6. Volvé a **Render** → tu servicio → **Settings → Custom Domains** →
   agregá `api.pulsoaustral.com.ar`. Render también verifica solo.

## 5. Últimos ajustes, una vez que el dominio esté andando

1. En **Vercel**, actualizá la variable `API_BASE_URL` a
   `https://api.pulsoaustral.com.ar/api` (en vez de la URL `.onrender.com`)
   y hacé un **Redeploy**.
2. Probá `https://pulsoaustral.com.ar` — tiene que verse el dashboard con
   datos reales, favicon y logo incluidos.
3. Cambiá la contraseña del admin (`https://api.pulsoaustral.com.ar/admin/`)
   si seguís usando `admin`/`pulsoaustral2026`.

## Checklist rápido

- [ ] Repo en GitHub, código pusheado
- [ ] Render: blueprint aplicado, 4 env vars cargadas, seeds corridos
- [ ] Vercel: proyecto importado, Root Directory = `frontend`, `API_BASE_URL` cargada
- [ ] Cloudflare: nameservers cambiados en el registrador, 3 registros DNS cargados
- [ ] Dominio agregado en Vercel y en Render
- [ ] `API_BASE_URL` actualizada al dominio propio + redeploy
- [ ] Contraseña de admin cambiada
