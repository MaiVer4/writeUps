# Portafolio de Writeups (Estilo v1nl4nd)

Plantilla automatizada para documentar y publicar writeups de máquinas CTF (DockerLabs, HackTheBox, TryHackMe, etc.) con la estética *editorial dark hacking*, terminales interactivas, línea de tiempo por fases y despliegue automático en GitHub Pages.

---

## 🚀 Flujo de trabajo para agregar una nueva máquina

Cada vez que resuelvas una máquina nueva, solo tienes que seguir estos 3 pasos:

### 1. Duplica la plantilla en `content/`
```bash
cp content/_plantilla.md content/nombre-maquina.md
```

### 2. Escribe tu writeup en Markdown
Abre `content/nombre-maquina.md` en tu editor favorito (Neovim, VS Code, Obsidian, etc.) y rellena:
- La cabecera (título, plataforma, dificultad, servicios, descripción, etc.).
- Las fases con sus comandos.

### 3. Sube a GitHub
```bash
git add .
git commit -m "Añadir writeup: NombreMaquina"
git push origin main
```
¡Y listo! Una acción de GitHub (`GitHub Actions`) compilará el sitio y actualizará tu GitHub Pages en segundos:
- Se genera el writeup con la línea de tiempo y terminales.
- Se actualiza el árbol lateral de navegación en todas las páginas.
- Se crea la tarjeta en el catálogo de inicio con sus filtros por plataforma y dificultad.

---

## 🛠️ Probar localmente

Si quieres ver cómo queda en tu navegador antes de subirlo:

```bash
python3 build.py
python3 -m http.server 8000 -d dist
```
Abre en tu navegador: `http://localhost:8000`

---

## 📝 Chuleta de sintaxis en Markdown

| Elemento | Sintaxis en Markdown |
|---|---|
| **Ventana de terminal** | ```` ```terminal [nmap] ````<br>`$ nmap -sCV 10.10.10.1`<br>`PORT 22 open`<br>```` ``` ```` |
| **Resaltar en terminal** | Usa doble igual `==texto a resaltar==` |
| **Comentario en terminal** | Agrega `<- comentario` al final de la línea |
| **Fase normal** | `## Fase 1: Reconocimiento`<br>`nmap · escaneo de puertos` |
| **Fase de Root (acento rojo)** | `## Fase Final: Escalada de Privilegios {root}`<br>`usuario → root` |
| **Callout / Nota técnica** | `> [!NOTE] GTFOBins`<br>`> Explicación o truco.` |
| **Callout de aviso** | `> [!WARNING] Cuidado`<br>`> Payload potencialmente destructivo.` |
| **Bandera / Root final** | `:::flag`<br>`¡Máquina completada!`<br>`uid=0(root)`<br>`:::` |

---

## ⚙️ Configuración personal

Edita [config.yaml](file:///home/snicker/Proyectos/writeups/config.yaml) para cambiar tu nombre, bio, usuario de GitHub o LinkedIn.

---

## 🌐 Despliegue en GitHub Pages

1. Crea un repositorio en tu cuenta de GitHub (ejemplo: `writeups` o `<usuario>.github.io`).
2. En GitHub ve a **Settings** → **Pages** → **Build and deployment** → selecciona **GitHub Actions**.
3. Inicializa el repositorio local y conéctalo:
   ```bash
   cd ~/Proyectos/writeups
   git init
   git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git push -u origin main
   ```
El workflow `.github/workflows/deploy.yml` se encargará de todo automáticamente.
